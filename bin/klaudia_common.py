#!/usr/bin/env python3
"""KLAUDIA BOT · shared helpers: ffmpeg, the OpenRouter key and balance, the temporary https host, face finding,
fonts and the video state file. Imported by the other scripts; also a small command line:

  python3 klaudia_common.py balance [--need 1.20]   → {"ok", "remaining_usd", "enough"} (free; never prints the key)
  python3 klaudia_common.py face photo.png          → {"faces": [[x, y, w, h], …]} (free)
  python3 klaudia_common.py upload sing/01.wav      → {"url": "https://…"} temporary public link, deleted within ~1 hour
"""
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
FONTS = KIT / "fonts"
OR = "https://openrouter.ai/api/v1"


# ---------- ffmpeg ----------
def ffmpeg():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("No ffmpeg: run `python3 -m pip install --user imageio-ffmpeg`.")


def run_ff(args):
    r = subprocess.run([ffmpeg(), "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-2000:])


def duration(path):
    r = subprocess.run([ffmpeg(), "-nostdin", "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


def video_size(path):
    r = subprocess.run([ffmpeg(), "-nostdin", "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})", r.stderr)
    return (int(m[1]), int(m[2])) if m else (0, 0)


def read_audio(path, sr=16000, start=None, length=None):
    """Mono float samples of any audio/video file (needs numpy)."""
    import numpy as np
    args = [ffmpeg(), "-nostdin", "-hide_banner", "-loglevel", "error"]
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    if length is not None:
        args += ["-t", f"{length:.3f}"]
    args += ["-i", str(path), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"]
    raw = subprocess.run(args, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype("float32") / 32768.0


# ---------- OpenRouter ----------
def key():
    k = os.environ.get("OPENROUTER_API_KEY")
    if not k:
        sys.exit("OPENROUTER_API_KEY is not set: connect OpenRouter first (skill klaudia-setup).")
    return k


def or_call(method, path, body=None, raw=False, timeout=300):
    url = path if path.startswith("http") else OR + path
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = r.read()
        return d if raw else json.loads(d)


def balance():
    """What can still be spent: the key's own limit (if it has one) and the account's credits, the smaller wins."""
    left = []
    try:
        k = or_call("GET", "/key", timeout=30).get("data", {})
        if k.get("limit_remaining") is not None:
            left.append(float(k["limit_remaining"]))
    except Exception:
        pass
    try:
        c = or_call("GET", "/credits", timeout=30).get("data", {})
        if c.get("total_credits") is not None:
            left.append(float(c["total_credits"]) - float(c.get("total_usage") or 0))
    except Exception:
        pass
    return round(min(left), 3) if left else None


def need(usd):
    """Stop BEFORE spending when the key cannot pay (OpenRouter answers 402 halfway through a batch otherwise)."""
    left = balance()
    if left is not None and left < usd:
        sys.exit(json.dumps({"ok": False, "not_enough_credit": True, "remaining_usd": left, "need_usd": round(usd, 3),
                             "say": f"Your OpenRouter has ${left:.2f} left and this needs about ${usd:.2f}. "
                                    "Add credits at openrouter.ai (Settings → Credits) and tell me when."}))
    return left


def data_url(path, max_side=1920, quality=90):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_side, max_side))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=quality)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


# ---------- temporary https host (the tunnel is blocked on Grok Bot's computer) ----------
def url_ok(url):
    try:
        req = urllib.request.Request(url, headers={"Range": "bytes=0-15", "User-Agent": "klaudia-bot"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status in (200, 206)
    except Exception:
        return False


def upload_temp(path):
    """A temporary public copy, deleted within about an hour (litterbox; tmpfiles.org as a fallback).
    Returns a DIRECT https link (the file itself, not a web page), checked before it is returned."""
    hosts = (
        (["curl", "-s", "-m", "90", "--form-string", "reqtype=fileupload", "--form-string", "time=1h",
          "-F", f"fileToUpload=@{path}", "https://litterbox.catbox.moe/resources/internals/api.php"],
         lambda s: s.strip()),
        (["curl", "-s", "-m", "90", "-F", f"file=@{path}", "https://tmpfiles.org/api/v1/upload"],
         lambda s: re.sub(r"^https?://tmpfiles\.org/", "https://tmpfiles.org/dl/", json.loads(s)["data"]["url"])),
    )
    for cmd, fix in hosts:
        for _ in range(2):
            try:
                url = fix(subprocess.run(cmd, capture_output=True, text=True).stdout)
                if url.startswith("https://") and url_ok(url):
                    return url
            except Exception:
                pass
    return None


# ---------- faces (OpenCV if installed; everything still works without it, with fewer checks) ----------
def faces(path_or_img):
    """Frontal faces as [x, y, w, h], biggest first. [] if none or if OpenCV is missing (then None).
    An extreme close-up (the face fills the frame) is found by trying again on the picture shrunk inside a border."""
    from PIL import Image
    im = path_or_img if hasattr(path_or_img, "size") else Image.open(path_or_img)
    found = _faces(im)
    if found == []:
        big = Image.new("RGB", (im.width * 2, im.height * 2), (128, 128, 128))
        big.paste(im.convert("RGB"), (im.width // 2, im.height // 2))
        found = [[x - im.width // 2, y - im.height // 2, w, h] for x, y, w, h in (_faces(big) or [])]
    return found


def _faces(path_or_img):
    try:
        import cv2
        import numpy as np
    except ImportError:
        return None
    if not hasattr(cv2, "CascadeClassifier"):     # OpenCV 5 dropped it: setup installs "opencv-python-headless<5"
        return None
    from PIL import Image
    im = path_or_img if hasattr(path_or_img, "size") else Image.open(path_or_img)
    rgb = im.convert("RGB")
    scale = 900 / max(im.size)
    small = rgb.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale)))) if scale < 1 else rgb
    scale = min(scale, 1)
    col = np.array(small).astype("float32")
    g = np.array(small.convert("L"))
    casc = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    found = casc.detectMultiScale(g, scaleFactor=1.1, minNeighbors=6, minSize=(40, 40))
    eyes = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_eye.xml")
    out, strong = [], []
    grey = (np.ptp(col.reshape(-1, 3).mean(axis=0)) < 4) and np.abs(col[..., 0] - col[..., 2]).mean() < 3
    for (x, y, w, h) in found:
        # skin, not a TV screen or a chrome robot: the middle of the box is warmer than it is blue
        r, gg, b = col[y + h // 3:y + 2 * h // 3, x + w // 4:x + 3 * w // 4].reshape(-1, 3).mean(axis=0)
        if grey or (r > 70 and r > b * 1.08 and r >= gg * 0.95):
            box = [int(v / scale) for v in (x, y, w, h)]
            out.append(box)
            upper = g[y:y + int(h * 0.6), x:x + w]      # a real face has eyes in its upper half
            if len(eyes.detectMultiScale(upper, scaleFactor=1.1, minNeighbors=4, minSize=(max(6, w // 10),) * 2)):
                strong.append(box)
    return sorted(strong or out, key=lambda f: -f[2] * f[3])


def font(size, name="Anton-Regular.ttf"):
    from PIL import ImageFont
    p = FONTS / name
    if not p.exists():
        p = FONTS / "Anton-Regular.ttf"
    return ImageFont.truetype(str(p), size)


# ---------- the video's state (one chat per video: everything lives in files) ----------
def state_path(folder):
    return Path(folder) / "state.json"


def load_state(folder):
    p = state_path(folder)
    return json.loads(p.read_text()) if p.exists() else {}


def save_state(folder, **changes):
    st = load_state(folder)
    st.update(changes)
    state_path(folder).write_text(json.dumps(st, indent=1, ensure_ascii=False))
    return st


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("balance"); b.add_argument("--need", type=float, default=0)
    f = sub.add_parser("face"); f.add_argument("image")
    u = sub.add_parser("upload"); u.add_argument("file")
    a = ap.parse_args()
    if a.cmd == "balance":
        left = balance()
        print(json.dumps({"ok": left is not None, "remaining_usd": left,
                          "enough": None if left is None else left >= a.need}))
    elif a.cmd == "face":
        print(json.dumps({"faces": faces(a.image)}))
    else:
        url = upload_temp(a.file)
        print(json.dumps({"ok": bool(url), "url": url}))


if __name__ == "__main__":
    main()
