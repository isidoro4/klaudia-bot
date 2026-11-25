#!/usr/bin/env python3
"""KLAUDIA BOT · measure the lip sync of a sung take, and where to cut before it drifts (free, on this computer).

  python3 klaudia_sync.py check clips/04-sung.mp4 [--vocal sing/04.wav]
    → {"ok", "lag_s", "synced_pct", "good_until", "verdict", "say"} and the same into clips/04-sung.sync.json

How: her mouth is found in the take (OpenCV face finder; mouth = lower middle of the face). Frame by frame we
measure how open/moving the mouth is, and compare it with the loudness of the vocal she was given (the window, or
the take's own audio). In every 1.5 s stretch we look for the delay that matches best:
  - lag_s: the delay of her lips against the voice (+ = lips late). Over ±0.12 s the edit shifts the clip by it.
  - synced_pct: share of the sung stretches where lips and voice move together (within ±0.12 s).
  - good_until: seconds into the take where it stops matching for good → cut to another shot there.
It is a measure, not a judge: a "drift" verdict means LOOK at it. Needs numpy and OpenCV (setup installs them).
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import klaudia_common as kc  # noqa: E402

FPS = 25
TOL = 0.12


def frames_gray(path, width=360):
    import numpy as np
    w, h = kc.video_size(path)
    if not w:
        sys.exit("Not a video: " + str(path))
    hh = int(round(h * width / w / 2) * 2)
    raw = subprocess.run([kc.ffmpeg(), "-nostdin", "-loglevel", "error", "-i", str(path), "-vf",
                          f"fps={FPS},scale={width}:{hh},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    n = len(raw) // (width * hh)
    return np.frombuffer(raw[: n * width * hh], dtype=np.uint8).reshape(n, hh, width).astype("float32")


def mouth_box(frames):
    from PIL import Image
    import numpy as np
    boxes = []
    for k in range(0, len(frames), max(1, len(frames) // 12)):
        f = kc.faces(Image.fromarray(frames[k].astype("uint8")))
        if f is None:
            sys.exit("OpenCV is missing: python3 -m pip install --user opencv-python-headless numpy")
        if f:
            boxes.append(f[0])
    if not boxes:
        return None
    x, y, w, h = (int(np.median([b[i] for b in boxes])) for i in range(4))
    return x + int(0.28 * w), y + int(0.66 * h), int(0.44 * w), int(0.30 * h), (x, y, w, h)


def mouth_signal(frames, box):
    """Per frame: how open the mouth is (dark inside of the mouth) plus how much it moves, head motion removed."""
    import numpy as np
    x, y, w, h, (fx, fy, fw, fh) = box
    m = frames[:, y:y + h, x:x + w]
    ref = frames[:, fy + int(0.15 * fh):fy + int(0.35 * fh), fx + int(0.3 * fw):fx + int(0.7 * fw)]  # forehead
    dark = np.array([np.percentile(f, 12) for f in m])
    opening = -(dark - np.median(dark))
    move = np.r_[0, np.abs(np.diff(m, axis=0)).mean(axis=(1, 2))] - np.r_[0, np.abs(np.diff(ref, axis=0)).mean(axis=(1, 2))]
    sig = z(opening) + 0.5 * z(move)
    return smooth(sig, 3)


def z(v):
    import numpy as np
    s = v.std()
    return (v - v.mean()) / s if s > 1e-6 else v * 0


def smooth(v, k):
    import numpy as np
    return np.convolve(v, np.ones(k) / k, mode="same")


def voice_env(path, n):
    import numpy as np
    sr = 16000
    a = kc.read_audio(path, sr)
    hop = sr // FPS
    env = np.array([np.sqrt(np.mean(a[i * hop:(i + 1) * hop] ** 2)) if i * hop < len(a) else 0 for i in range(n)])
    return env


def best_lag(m, v, maxlag):
    import numpy as np
    best, lag = -2, 0
    for L in range(-maxlag, maxlag + 1):
        a, b = (m[L:], v[:len(v) - L]) if L >= 0 else (m[:L], v[-L:])
        if len(a) < 8 or a.std() < 1e-6 or b.std() < 1e-6:
            continue
        c = float(np.corrcoef(a, b)[0, 1])
        if c > best:
            best, lag = c, L
    return lag / FPS, best


def check(clip, vocal=None):
    import numpy as np
    clip = Path(clip)
    side = clip.with_suffix(".sync.json")
    info = json.loads(side.read_text()) if side.exists() else {}
    vocal = vocal or info.get("window")
    if vocal and not Path(vocal).exists():
        vocal = None
    frames = frames_gray(clip)
    n = len(frames)
    box = mouth_box(frames)
    if not box:
        res = {"ok": False, "verdict": "no_face", "say": "I can't find her face in this take: look at it before using it."}
    else:
        mouth = mouth_signal(frames, box)
        env = voice_env(vocal or clip, n)
        voiced = env > max(env.max() * 0.12, 1e-4)
        lag_all, corr_all = best_lag(mouth, z(smooth(env, 3)), int(0.5 * FPS))
        win, step = int(1.5 * FPS), int(0.25 * FPS)
        stretches = []
        for s in range(0, max(1, n - win + 1), step):
            v = voiced[s:s + win]
            if v.mean() < 0.3:          # mostly silence: nothing to match
                continue
            lag, c = best_lag(mouth[s:s + win], z(smooth(env[s:s + win], 3)), int(0.4 * FPS))
            stretches.append({"t": round(s / FPS, 2), "lag": round(lag, 2), "corr": round(c, 2)})
        strong = [x["lag"] for x in stretches if x["corr"] > 0.3]
        lag_ref = float(np.median(strong)) if strong else lag_all
        for x in stretches:
            x["ok"] = x["corr"] > 0.25 and abs(x["lag"] - lag_ref) <= TOL + 1e-9
        good = [x for x in stretches if x["ok"]]
        pct = round(100 * len(good) / len(stretches)) if stretches else 0
        good_until = round(n / FPS, 2)
        bad_run = 0
        for x in stretches[1:]:                   # (the first stretch holds the breath before the voice)
            bad_run = 0 if x["ok"] else bad_run + 1
            if bad_run == 3:                      # three bad stretches in a row = it has come apart
                good_until = round(max(x["t"] - 0.5, 0.0), 2)
                break
        if pct >= 60 and abs(lag_ref) <= TOL:
            verdict = "good"
        elif pct >= 60:
            verdict = "shift"
        elif good_until >= 1.5:
            verdict = "drift"
        else:
            verdict = "bad"
        say = {"good": f"Lip sync looks right ({pct}% of the sung part).",
               "shift": f"Her lips move with the voice but {abs(lag_ref):.2f} s {'late' if lag_ref > 0 else 'early'}: the edit shifts the clip by that.",
               "drift": f"Lips match for the first {good_until:.1f} s, then drift: cut to another shot there.",
               "bad": f"Lips barely match ({pct}%): look at it; use a dance or move shot instead, or one retake with a yes."}[verdict]
        lag_all = lag_ref
        res = {"ok": True, "lag_s": round(lag_all, 2), "overall_corr": round(corr_all, 2), "synced_pct": pct,
               "good_until": good_until, "seconds": round(n / FPS, 2), "verdict": verdict, "say": say,
               "stretches": stretches}
    if side.exists() or info:
        info["check"] = {k: v for k, v in res.items() if k != "stretches"}
        side.write_text(json.dumps(info, indent=1))
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("check")
    c.add_argument("clip")
    c.add_argument("--vocal")
    c.add_argument("--short", action="store_true", help="leave out the per-stretch detail")
    a = ap.parse_args()
    r = check(a.clip, a.vocal)
    if a.short:
        r.pop("stretches", None)
    print(json.dumps(r))


if __name__ == "__main__":
    main()
