#!/usr/bin/env python3
"""KLAUDIA BOT · sung shots with real lip sync, on the person's OpenRouter key.

DEFAULT --model heygen (HeyGen Avatar IV, $0.05 per second): animates the shot's own still (Klaudia, made from her
references) so she sings the vocal window. It accepts Klaudia's face; Seedance refused it ("may be a real person").
Seedance (mini / flash / full) stays as an option, only if the person asks.

SHORT TAKES: 2–5 s, only her own words in the window (no choir). Long takes (8 s) made HeyGen answer
402 "weight_exceeds_budget" even with credit left, and the longer the take, the more the lips drift.

  1. window   cut the vocal window for one shot (free)
     python3 klaudia_sing.py window --vocals song/vocals.mp3 --from 13.7 --to 17.4 --out sing/04.wav [--words "…"]
       → sing/04.wav + sing/04.json {"song_start": …}. The window opens up to 0.4 s before the first word and ends
         0.3 s after the last one; silence outside the words. Longer than --max (5 s): it says how to split the shot.
  2. price    python3 klaudia_sing.py price --seconds 3.2           (free)
  3. sing     PAID: needs --yes, and the person's yes in the chat first
     python3 klaudia_sing.py sing --still photos/04.png --audio sing/04.wav --words "X wants to pay the streamers" \
        --format vertical --out clips/04-sung.mp4 --yes
     It checks the OpenRouter balance first, uploads the window to a temporary host (deleted within an hour) and
     writes clips/04-sung.sync.json with the window's song_start. In board.json just put "clip": "clips/04-sung.mp4":
     the edit reads the .sync.json and puts every syllable on its own second of the song (no @ offset by hand).
  4. check    python3 klaudia_sync.py check clips/04-sung.mp4      (free: measures the lip sync, see that script)
  host        python3 klaudia_sing.py host --dir sing [--mode temp|tunnel|auto]  (links for every .wav; temp by default)
Key: OPENROUTER_API_KEY in the environment (the bot's masked secret card). Never printed, never written to a file.
"""
import argparse
import json
import math
import re
import shutil
import subprocess
import sys
import time
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import klaudia_common as kc  # noqa: E402

LEAD = 0.4      # seconds of breath before the first word: her lips close and get ready
TAIL = 0.3
MODELS = {  # OpenRouter ids and their price per video token (checked 2026-11-25 on /api/v1/videos/models)
    "heygen": ("heygen/avatar-iv", None),     # $0.05 per second (DEFAULT)
    "full": ("bytedance/seedance-2.5", 0.0000107),
    "flash": ("bytedance/seedance-2.5-flash", 0.000007),
    "mini": ("bytedance/seedance-2.0-mini", 0.0000035),
}
SIZES = {("720p", "vertical"): (720, 1280), ("720p", "horizontal"): (1280, 720),
         ("480p", "vertical"): (480, 854), ("480p", "horizontal"): (854, 480)}


def billed_seconds(seconds, model):
    return math.ceil(seconds) if model != "heygen" else round(seconds, 2)


def price(seconds, model, res="720p", fmt="vertical"):
    s = billed_seconds(seconds, model)
    if model == "heygen":
        return round(0.05 * s, 3)
    w, h = SIZES[(res, fmt)]
    return round(w * h * 24 * s / 1024 * MODELS[model][1], 3)


# ---------- 1. the window ----------
def cmd_window(a):
    t0, t1 = float(a.from_), float(a.to)
    start = max(t0 - LEAD, 0.0)
    secs = round(t1 + TAIL - start, 2)
    if secs > a.max:
        # never silently send a long take: say where to split the shot
        mid = round((t0 + t1) / 2, 2)
        sys.exit(json.dumps({"ok": False, "too_long": round(secs, 2), "max": a.max,
                             "say": f"This window is {secs:.1f} s; takes over {a.max:.0f} s drift and HeyGen may refuse them. "
                                    f"Split the shot near {mid} s (between two words) and make two windows."}))
    secs = max(secs, 2.0)
    s0, s1 = t0 - start, t1 - start
    vol = (f"volume=enable='lt(t,{max(s0 - 0.03, 0):.3f})+gt(t,{s1 + 0.05:.3f})':volume=0,"
           f"afade=t=in:st={max(s0 - 0.03, 0):.3f}:d=0.03,afade=t=out:st={s1 + 0.02:.3f}:d=0.03,"
           f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=whole_dur={secs:.3f}")
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    kc.run_ff(["-ss", f"{start:.3f}", "-t", f"{secs:.3f}", "-i", a.vocals, "-af", vol, "-t", f"{secs:.3f}",
               "-ac", "1", "-ar", "44100", str(out)])
    info = {"song_start": round(start, 3), "seconds": secs, "first_word": t0, "last_word": t1,
            "words": a.words or "", "vocals": a.vocals}
    out.with_suffix(".json").write_text(json.dumps(info, indent=1))
    print(json.dumps({"ok": True, "out": str(out), **info}))


# ---------- host (links for every window) ----------
def cloudflared():
    exe = shutil.which("cloudflared") or str(Path.home() / ".local/bin/cloudflared")
    return exe if Path(exe).is_file() else None


TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def try_tunnel(d, port):
    exe = cloudflared()
    if not exe:
        return None, None, None
    web = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", str(d)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tun = subprocess.Popen([exe, "tunnel", "--no-autoupdate", "--protocol", "http2", "--url", f"http://127.0.0.1:{port}"],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    url, t_end = None, time.time() + 30
    while time.time() < t_end and url is None:
        line = tun.stdout.readline()
        if not line and tun.poll() is not None:
            break
        m = TUNNEL_URL.search(line)          # (0.6 crashed on "Requesting new quick Tunnel on trycloudflare.com…")
        if m:
            url = m.group(0)
    return url, web, tun


def cmd_host(a):
    d = Path(a.dir).resolve()
    files = sorted(d.glob("*.wav"))
    if not files:
        sys.exit("No .wav files in " + str(d))
    if a.mode in ("auto", "tunnel"):
        url, web, tun = try_tunnel(d, a.port)
        if url:
            time.sleep(4)
            if kc.url_ok(f"{url}/{files[0].name}"):
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
        u = kc.upload_temp(f)
        if not u:
            sys.exit(json.dumps({"ok": False, "failed": f.name, "urls": urls}))
        urls[f.name] = u
    print(json.dumps({"ok": True, "mode": "temp", "urls": urls,
                      "note": "temporary public links (deleted within about an hour): only these few seconds of the vocal"}))


# ---------- the take ----------
def prompt_for(words, framing):
    return ('@Image1 is the shot. Klaudia, the woman in @Image1, sings @Audio1, copying it '
            f'word for word: "{words}". The soundtrack is @Audio1 exactly: no music, no other voices. '
            f'{framing} Eyes wide open, lips closed until her voice begins. '
            'One continuous shot, no cuts, no head turns. Only she sings. No text, letters or logos.')


def cmd_price(a):
    print(json.dumps({"model": MODELS[a.model][0], "seconds": billed_seconds(a.seconds, a.model), "res": a.res,
                      "usd": price(a.seconds, a.model, a.res, a.format)}))


def cmd_sing(a):
    model_id = MODELS[a.model][0]
    win = {}
    if a.audio:
        side = Path(a.audio).with_suffix(".json")
        win = json.loads(side.read_text()) if side.exists() else {}
        seconds = kc.duration(a.audio) or win.get("seconds", 5)
    else:
        seconds = a.seconds or 5
    if seconds > a.max + 0.5:
        sys.exit(f"This window is {seconds:.1f} s: make it {a.max:.0f} s or shorter (klaudia_sing.py window).")
    est = price(seconds, a.model, a.res, a.format)
    words = a.words or win.get("words", "")
    if a.model == "heygen":
        motion = (f'She sings these words with her whole face: "{words}". Eyes wide open, mouth fully visible, '
                  'a slight head bob on the beat, deadpan and confident.')
        body = {"model": model_id, "prompt": motion, "motion_prompt": motion, "resolution": a.res,
                "aspect_ratio": "9:16" if a.format == "vertical" else "16:9"}
    else:
        body = {"model": model_id, "prompt": prompt_for(words, a.framing), "duration": int(math.ceil(seconds)),
                "resolution": a.res, "aspect_ratio": "9:16" if a.format == "vertical" else "16:9", "generate_audio": True}
    if not a.yes:
        print(json.dumps({"dry_run": True, "model": model_id, "seconds": round(seconds, 2), "estimate_usd": est,
                          "prompt": body["prompt"], "song_start": win.get("song_start")}))
        return
    kc.need(est * 1.2)                                          # the balance, BEFORE anything is sent
    url = a.audio_url
    if not url:
        if not a.audio:
            sys.exit("Give --audio sing/NN.wav (uploaded for you) or --audio-url https://…")
        url = kc.upload_temp(a.audio)
        if not url:
            sys.exit(json.dumps({"ok": False, "say": "The temporary host did not answer. Try again in a minute."}))
    if not url.startswith("https://"):
        sys.exit("--audio-url must be an https link.")
    body["input_references"] = [{"type": "image_url", "image_url": {"url": kc.data_url(a.still)}},
                                {"type": "audio_url", "audio_url": {"url": url}}]
    try:
        job = kc.or_call("POST", "/videos", body)
    except urllib.error.HTTPError as e:
        why = e.read().decode(errors="replace")[:400]
        say = ("HeyGen said the take is too heavy: make the window shorter (3–4 s)." if "weight" in why else
               "Refused; a refusal is final for this still: pick or make another still (never edit it to get through).")
        sys.exit(json.dumps({"ok": False, "refused": e.code, "why": why, "say": say}))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sync = {"song_start": win.get("song_start"), "window": a.audio, "seconds": round(seconds, 3), "words": words,
            "model": model_id, "still": a.still, "job": job.get("id")}
    out.with_suffix(".sync.json").write_text(json.dumps(sync, indent=1))
    poll = job.get("polling_url") or f"/videos/{job['id']}"
    st = {}
    for _ in range(120):  # up to 20 minutes; never resubmit on a timeout (it would charge twice)
        time.sleep(10)
        try:
            st = kc.or_call("GET", poll)
        except (urllib.error.URLError, OSError, TimeoutError):
            continue
        if st.get("status") in ("completed", "failed", "cancelled", "expired"):
            break
    if st.get("status") != "completed":
        sys.exit(json.dumps({"ok": False, "status": st.get("status"), "error": st.get("error"), "job": job.get("id"),
                             "note": "check the job later with: klaudia_sing.py fetch; do not submit it again"}))
    fetch(job["id"], st, out)
    cost = float((st.get("usage") or {}).get("cost") or 0)
    sync["cost"] = cost
    out.with_suffix(".sync.json").write_text(json.dumps(sync, indent=1))
    print(json.dumps({"ok": True, "out": str(out), "cost": cost, "estimate": est, "song_start": sync["song_start"],
                      "next": f"python3 klaudia_sync.py check {out}"}))


def fetch(job_id, st, out):
    try:
        video = kc.or_call("GET", f"/videos/{job_id}/content", raw=True)
    except urllib.error.HTTPError:
        import urllib.request
        video = urllib.request.urlopen(st["unsigned_urls"][0], timeout=300).read()
    Path(out).write_bytes(video)


def cmd_fetch(a):
    """A take that timed out: look at the same job again (never a new one)."""
    side = Path(a.out).with_suffix(".sync.json")
    job = json.loads(side.read_text())["job"]
    st = kc.or_call("GET", f"/videos/{job}")
    if st.get("status") != "completed":
        print(json.dumps({"ok": False, "status": st.get("status")}))
        return
    fetch(job, st, a.out)
    print(json.dumps({"ok": True, "out": a.out, "cost": float((st.get("usage") or {}).get("cost") or 0)}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("window")
    w.add_argument("--vocals", required=True)
    w.add_argument("--from", dest="from_", required=True, type=float)
    w.add_argument("--to", required=True, type=float)
    w.add_argument("--out", required=True)
    w.add_argument("--words", default="")
    w.add_argument("--max", type=float, default=5.0)
    h = sub.add_parser("host")
    h.add_argument("--dir", required=True)
    h.add_argument("--port", type=int, default=8765)
    h.add_argument("--mode", choices=["auto", "tunnel", "temp"], default="temp")
    f = sub.add_parser("fetch")
    f.add_argument("--out", required=True)
    for name in ("price", "sing"):
        s = sub.add_parser(name)
        s.add_argument("--seconds", type=float, default=0)
        s.add_argument("--model", choices=list(MODELS), default="heygen")
        s.add_argument("--res", choices=["480p", "720p"], default="720p")
        s.add_argument("--format", choices=["vertical", "horizontal"], default="vertical")
        s.add_argument("--max", type=float, default=5.0)
        if name == "sing":
            s.add_argument("--still", required=True)
            s.add_argument("--audio", help="the window from `window` (uploaded to a temporary host for you)")
            s.add_argument("--audio-url", help="or an https link you already have")
            s.add_argument("--words", default="")
            s.add_argument("--framing", default="Medium close-up, static camera, her whole mouth visible.")
            s.add_argument("--out", required=True)
            s.add_argument("--yes", action="store_true", help="really spend (only after the person's yes)")
    a = ap.parse_args()
    {"window": cmd_window, "host": cmd_host, "price": cmd_price, "sing": cmd_sing, "fetch": cmd_fetch}[a.cmd](a)


if __name__ == "__main__":
    main()
