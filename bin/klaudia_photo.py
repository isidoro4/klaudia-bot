#!/usr/bin/env python3
"""KLAUDIA BOT · a high-quality still of Klaudia with Nano Banana Pro (Google) on OpenRouter, from her reference images.

  python3 klaudia_photo.py --prompt "..." --refs refs/klaudia-face.jpg refs/klaudia-sheet.jpg [more] \
      --format vertical --out photos/01-hook.png --yes
  (without --yes: a dry run that prints what would be sent and the usual price)

One still per call, never in a loop without looking: it prints the real cost. Usually about $0.14; a hard edit can
cost much more (the model makes several images inside). Stop and tell the person if one costs more than $0.20.
To keep her the same Klaudia across a video: when one still is right, make the next ones as EDITS of that still
(pass it first in --refs and ask to change only the pose, the expression or the place).
Key: OPENROUTER_API_KEY in the environment. Never printed.
"""
import argparse
import base64
import io
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

MODEL = "google/gemini-3-pro-image-preview"
USUAL = 0.14


def part(path):
    from PIL import Image
    im = Image.open(path).convert("RGB")
    im.thumbnail((2048, 2048))
    b = io.BytesIO()
    im.save(b, "JPEG", quality=90)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()}}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--refs", nargs="+", required=True)
    ap.add_argument("--format", choices=["vertical", "horizontal", "square"], default="vertical")
    ap.add_argument("--out", required=True)
    ap.add_argument("--yes", action="store_true")
    a = ap.parse_args()
    ratio = {"vertical": "9:16", "horizontal": "16:9", "square": "1:1"}[a.format]
    body = {"model": MODEL, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": [{"type": "text", "text": a.prompt}] + [part(r) for r in a.refs]}],
            "image_config": {"aspect_ratio": ratio, "image_size": "2K"}}
    if not a.yes:
        print(json.dumps({"dry_run": True, "model": MODEL, "usual_usd": USUAL, "refs": a.refs, "ratio": ratio}))
        return
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        sys.exit("OPENROUTER_API_KEY is not set: connect OpenRouter first (skill klaudia-setup).")
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        r = json.load(urllib.request.urlopen(req, timeout=300))
    except urllib.error.HTTPError as e:
        sys.exit(json.dumps({"ok": False, "refused": e.code, "why": e.read().decode(errors="replace")[:400]}))
    if not r.get("choices"):
        sys.exit(json.dumps({"ok": False, "error": r.get("error") or r}, ensure_ascii=False)[:600])
    imgs = r["choices"][0]["message"].get("images") or []
    cost = float((r.get("usage") or {}).get("cost") or USUAL)
    if not imgs:
        sys.exit(json.dumps({"ok": False, "why": "no image came back (often a content refusal)", "cost": cost}))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))
    print(json.dumps({"ok": True, "out": str(out), "cost": cost, "too_expensive": cost > 0.20}))


if __name__ == "__main__":
    main()
