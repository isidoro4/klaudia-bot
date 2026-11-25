#!/usr/bin/env python3
"""KLAUDIA BOT · sung shots with real lip sync, on the person's OpenRouter key.

DEFAULT --model heygen (HeyGen Avatar IV, $0.05 per second): animates the shot's own still so she sings the vocal
window. It accepted Klaudia's photoreal face on 25 Nov 2026, where Seedance refused her face reference as "may be a
real person". Seedance (mini / flash / full) stays as an option: reference mode, the still as @Image1, NO face
reference by default (that close-up was what its filter refused), the vocal as @Audio1. Never a first frame.
The vocal goes as an HTTPS link (OpenRouter refuses inline audio): see host.

  1. window   cut the vocal window for one shot (free)
     python3 klaudia_sing.py window --vocals song/vocals.mp3 --from 13.7 --to 17.4 --out sing/S04.wav
       (the window opens 0.7 s before the first word, whole seconds 4–15, silence outside [from, to])
  2. host     give each window an https link (free): a Cloudflare quick tunnel over http2, or, where the tunnel is
     blocked, a temporary upload that deletes itself within an hour (litterbox, tmpfiles.org)
     python3 klaudia_sing.py host --dir sing [--mode auto|tunnel|temp]   → prints {"mode", "urls": {"01.wav": "https://…"}}
  3. price    python3 klaudia_sing.py price --seconds 5            (free; heygen by default)
  4. sing     PAID: needs --yes, and the person's yes in the chat first
     python3 klaudia_sing.py sing --still photos/04.png --audio-url <url printed for that file> \
        --words "X wants to pay the streamers" --seconds 5 --format vertical --out clips/S04-sung.mp4 --yes
     It prints {"ok", "out", "cost", "lead": 0.7}. In the edit, give the clip as clips/S04-sung.mp4@0.7.
Key: OPENROUTER_API_KEY in the environment (the bot's masked secret card). Never printed, never written to a file.
"""
import argparse
import base64
import io
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "https://openrouter.ai/api/v1/videos"
LEAD = 0.7
MODELS = {  # OpenRouter ids and their price per video token (checked 2026-11-25 on /api/v1/videos/models)
    "heygen": ("heygen/avatar-iv", None),     # $0.05 per second: animates the still to sing the vocal (DEFAULT)
    "full": ("bytedance/seedance-2.5", 0.0000107),
    "flash": ("bytedance/seedance-2.5-flash", 0.000007),
    "mini": ("bytedance/seedance-2.0-mini", 0.0000035),
}
SIZES = {("720p", "vertical"): (720, 1280), ("720p", "horizontal"): (1280, 720),
         ("480p", "vertical"): (480, 854), ("480p", "horizontal"): (854, 480)}


def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("No ffmpeg: run `pip install imageio-ffmpeg`.")


def price(seconds, model, res, fmt="vertical"):
    if model == "heygen":
        return round(0.05 * seconds, 3)
    w, h = SIZES[(res, fmt)]
    tokens = w * h * 24 * seconds / 1024
    return round(tokens * MODELS[model][1], 3)


# ---------- 1. the window ----------
def cmd_window(a):
    t0, t1 = float(a.from_), float(a.to)
    start = max(t0 - LEAD, 0.0)
    secs = int(min(15, max(4, -(-(t1 - start + 0.3) // 1))))
    # silence everything outside [t0, t1] (20 ms fades), relative to the window start
    s0, s1 = t0 - start, t1 - start
    vol = (f"volume=enable='lt(t,{s0 - 0.02:.3f})+gt(t,{s1 + 0.02:.3f})':volume=0,"
           f"afade=t=in:st={max(s0 - 0.02, 0):.3f}:d=0.02,afade=t=out:st={s1:.3f}:d=0.02")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run([ffmpeg(), "-nostdin", "-loglevel", "error", "-y", "-ss", f"{start:.3f}", "-t", str(secs),
                        "-i", a.vocals, "-af", vol, "-ac", "1", "-ar", "44100", str(out)], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed: " + r.stderr[-500:])
    print(json.dumps({"ok": True, "out": str(out), "song_start": round(start, 3), "seconds": secs, "lead": round(t0 - start, 3)}))


# ---------- 2. the temporary https link ----------
def cloudflared():
    exe = shutil.which("cloudflared") or str(Path.home() / ".local/bin/cloudflared")
    return exe if Path(exe).is_file() else None


def url_ok(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET", headers={"Range": "bytes=0-15"}), timeout=20) as r:
            return r.status in (200, 206)
    except Exception:
        return False


def upload_temp(path):
    """A temporary public copy (litterbox: deleted after 1 hour; tmpfiles.org as a fallback). Returns a direct URL."""
    for cmd, fix in (
        (["curl", "-s", "-m", "90", "--form-string", "reqtype=fileupload", "--form-string", "time=1h",
          "-F", f"fileToUpload=@{path}", "https://litterbox.catbox.moe/resources/internals/api.php"], lambda s: s.strip()),
        (["curl", "-s", "-m", "90", "-F", f"file=@{path}", "https://tmpfiles.org/api/v1/upload"],
         lambda s: json.loads(s)["data"]["url"].replace("https://tmpfiles.org/", "https://tmpfiles.org/dl/", 1)),
    ):
        for _ in range(2):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True).stdout
                url = fix(out)
                if url.startswith("https://") and url_ok(url):
                    return url
            except Exception:
                pass
    return None


def try_tunnel(d, port):
    exe = cloudflared()
    if not exe:
        return None, None, None
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(d)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # http2 = plain HTTPS on port 443; the default (QUIC over UDP) is blocked on many cloud computers
    tun = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--protocol", "http2", "--url", f"http://127.0.0.1:{port}"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url, t_end = None, time.time() + 45
    while time.time() < t_end and url is None:
        line = tun.stdout.readline()
        if "trycloudflare.com" in line:
            url = "https://" + line.split("https://", 1)[1].split()[0].strip("|").strip()
    return url, web, tun


def cmd_host(a):
    """Give every .wav in --dir an https link. --mode auto: the tunnel first (nothing leaves except through it), then
    a temporary upload. Prints {"ok", "mode", "urls": {file: url}}; with the tunnel it keeps running until stopped."""
    d = Path(a.dir).resolve()
    files = sorted(d.glob("*.wav"))
    if not files:
        sys.exit("No .wav files in " + str(d))
    if a.mode in ("auto", "tunnel"):
        url, web, tun = try_tunnel(d, a.port)
        if url:
            time.sleep(4)
            if url_ok(f"{url}/{files[0].name}"):
                print(json.dumps({"ok": True, "mode": "tunnel", "urls": {f.name: f"{url}/{f.name}" for f in files},
                                  "note": "keep this running until every take is done"}), flush=True)
                try:
                    tun.wait()
                finally:
                    web.kill()
                return
        for pr in (web, tun):
            if pr:
                pr.kill()
        if a.mode == "tunnel":
            sys.exit("The tunnel did not work on this computer: use --mode temp.")
    urls = {}
    for f in files:
        u = upload_temp(f)
        if not u:
            sys.exit(json.dumps({"ok": False, "failed": f.name, "urls": urls}))
        urls[f.name] = u
    print(json.dumps({"ok": True, "mode": "temp", "urls": urls,
                      "note": "temporary public links (deleted within about an hour): only these few seconds of the vocal"}))


# ---------- 4. the take ----------
def data_url(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((1920, 1920))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def prompt_for(words, framing, face=False):
    who = "@Image1 is the shot; @Image2 is Klaudia's face. " if face else "@Image1 is the shot. "
    return (who + f'Klaudia, the woman in @Image1, sings @Audio1, copying it '
            f'word for word: "{words}". The soundtrack is @Audio1 exactly: no music, no other voices. '
            f'{framing} Eyes wide open, a smile in her eyes, lips closed until her voice begins. '
            'One continuous shot, no cuts, no head turns. Only she sings. No text, letters or logos.')


def call(method, url, key, body=None, raw=False):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        d = r.read()
        return d if raw else json.loads(d)


def cmd_price(a):
    print(json.dumps({"model": MODELS[a.model][0], "seconds": a.seconds, "res": a.res,
                      "usd": price(a.seconds, a.model, a.res, a.format)}))


def cmd_sing(a):
    model_id = MODELS[a.model][0]
    est = price(a.seconds, a.model, a.res, a.format)
    if a.model == "heygen":
        # HeyGen Avatar IV: the shot's still + the vocal. No face reference (photoreal face references trip the
        # Seedance face filter; HeyGen animates the still itself, so Klaudia is whoever is in that still).
        motion = (f'She sings these words with her whole face: "{a.words}". Eyes wide open, a slight head bob on the '
                  'beat, deadpan and confident.')
        body = {"model": model_id, "prompt": motion, "motion_prompt": motion, "resolution": a.res,
                "aspect_ratio": "9:16" if a.format == "vertical" else "16:9",
                "input_references": [{"type": "image_url", "image_url": {"url": data_url(a.still)}},
                                     {"type": "audio_url", "audio_url": {"url": a.audio_url}}]}
    else:
        refs = [{"type": "image_url", "image_url": {"url": data_url(a.still)}}]
        if a.face:   # optional: a photoreal close-up here is the usual cause of "may be a real person" refusals
            refs.append({"type": "image_url", "image_url": {"url": data_url(a.face)}})
        refs.append({"type": "audio_url", "audio_url": {"url": a.audio_url}})
        body = {"model": model_id, "prompt": prompt_for(a.words, a.framing, bool(a.face)), "duration": int(a.seconds),
                "resolution": a.res, "aspect_ratio": "9:16" if a.format == "vertical" else "16:9", "generate_audio": True,
                "input_references": refs}
    if not a.audio_url.startswith("https://"):
        sys.exit("--audio-url must be an https link (klaudia_sing.py host).")
    if not a.yes:
        print(json.dumps({"dry_run": True, "model": model_id, "estimate_usd": est, "prompt": body["prompt"],
                          "refs": [r.get("type") for r in body["input_references"]]}))
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set: connect OpenRouter first (skill klaudia-setup).")
    try:
        job = call("POST", API, key, body)
    except urllib.error.HTTPError as e:
        sys.exit(json.dumps({"ok": False, "refused": e.code, "why": e.read().decode(errors="replace")[:400],
                             "note": "not resubmitted: a refused request is final for this still"}))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.with_suffix(".job.json").write_text(json.dumps({"job": job, "model": model_id, "words": a.words}))
    poll = job.get("polling_url") or f"/api/v1/videos/{job['id']}"
    poll = "https://openrouter.ai" + poll if poll.startswith("/") else poll
    st = {}
    for _ in range(120):  # up to 20 minutes; never resubmit on a timeout (it would charge twice)
        time.sleep(10)
        try:
            st = call("GET", poll, key)
        except (urllib.error.URLError, OSError, TimeoutError):
            continue
        if st.get("status") in ("completed", "failed", "cancelled", "expired"):
            break
    if st.get("status") != "completed":
        sys.exit(json.dumps({"ok": False, "status": st.get("status"), "error": st.get("error"), "job": job.get("id"),
                             "note": "check the job later; do not submit it again"}))
    try:
        video = call("GET", f"https://openrouter.ai/api/v1/videos/{job['id']}/content", key, raw=True)
    except urllib.error.HTTPError:
        video = urllib.request.urlopen(st["unsigned_urls"][0], timeout=300).read()
    out.write_bytes(video)
    cost = float((st.get("usage") or {}).get("cost") or 0)
    print(json.dumps({"ok": True, "out": str(out), "cost": cost, "estimate": est, "lead": LEAD,
                      "edit_as": f"{out}@{LEAD}"}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("window")
    w.add_argument("--vocals", required=True)
    w.add_argument("--from", dest="from_", required=True, type=float)
    w.add_argument("--to", required=True, type=float)
    w.add_argument("--out", required=True)
    h = sub.add_parser("host")
    h.add_argument("--dir", required=True)
    h.add_argument("--port", type=int, default=8765)
    h.add_argument("--mode", choices=["auto", "tunnel", "temp"], default="auto")
    for name in ("price", "sing"):
        s = sub.add_parser(name)
        s.add_argument("--seconds", type=int, default=5)
        s.add_argument("--model", choices=list(MODELS), default="heygen")
        s.add_argument("--res", choices=["480p", "720p"], default="720p")
        s.add_argument("--format", choices=["vertical", "horizontal"], default="vertical")
        if name == "sing":
            s.add_argument("--still", required=True)
            s.add_argument("--face", help="Seedance only, optional (usually leave it out)")
            s.add_argument("--audio-url", required=True)
            s.add_argument("--words", required=True)
            s.add_argument("--framing", default="Medium close-up, static camera, her whole mouth visible.")
            s.add_argument("--out", required=True)
            s.add_argument("--yes", action="store_true", help="really spend (only after the person's yes)")
    a = ap.parse_args()
    {"window": cmd_window, "host": cmd_host, "price": cmd_price, "sing": cmd_sing}[a.cmd](a)


if __name__ == "__main__":
    main()
