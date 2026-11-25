#!/usr/bin/env python3
"""KLAUDIA BOT · the board: the whole video as numbered shots, before anything is paid.

board.json (one video):
  {"song": "song/song.mp3", "format": "vertical" | "horizontal", "title": "FOUR VIEWERS", "tag": "STREAM YOURSELF.",
   "shots": [{"n": 1, "t0": 0.0, "t1": 2.4, "kind": "sing" | "dance" | "move" | "text",
              "line": "Hi! This is Klaudia's News.", "what": "close-up, she sings the hook to camera",
              "still": "photos/01.png", "clip": "clips/01-sung.mp4@0.7" | null, "text": "BIG WORD" | null}, …]}
  t0/t1 = seconds of the SONG. "clip" empty = the shot still shows its photo (free preview).

  python3 klaudia_board.py sheet board.json --out board.png        → one image with every shot numbered (send it in the chat)
  python3 klaudia_board.py plan board.json --lines song/lines.json --beat 0.44 [--max 2.0]
        → fills/refreshes t0/t1 from the song (one shot per lyric line, music gaps split into shots of max 2 s on the beat)
  python3 klaudia_board.py check board.json                         → what is missing (photos, clips) and the price of the clips left
The edit reads the same file: klaudia_edit.py --board board.json (free preview with photos, or the final with clips).
"""
import argparse
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FONT = HERE.parent / "fonts" / "Anton-Regular.ttf"
ICON = {"sing": "SINGS", "dance": "DANCES", "move": "MOVES", "text": "TEXT"}
COL = {"sing": (255, 122, 26), "dance": (90, 200, 255), "move": (180, 180, 180), "text": (255, 230, 120)}
PRICE = {"sing": 0.05, "dance": 0.0, "move": 0.0, "text": 0.0}   # sing = HeyGen $/s on OpenRouter; dance/move = Grok Imagine (in the plan)


def font(s):
    return ImageFont.truetype(str(FONT), s)


def load(p):
    return json.loads(Path(p).read_text())


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def cmd_sheet(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    shots = b["shots"]
    vertical = b.get("format", "vertical") == "vertical"
    tw, th = (220, 390) if vertical else (360, 203)
    cols = 6 if vertical else 4
    pad, cap = 16, 120
    rows = math.ceil(len(shots) / cols)
    W = cols * (tw + pad) + pad
    H = 110 + rows * (th + cap + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 14, 16))
    d = ImageDraw.Draw(sheet)
    d.text((pad, 20), f"{b.get('title', 'KLAUDIA')} · {len(shots)} shots · tell me: \"3: she dances\" / \"5: shorter\" / \"7: out\"",
           font=font(34), fill=(240, 234, 222))
    for i, s in enumerate(shots):
        x = pad + (i % cols) * (tw + pad)
        y = 110 + (i // cols) * (th + cap + pad)
        img = None
        src = s.get("still")
        if src and (base / src).exists():
            img = Image.open(base / src).convert("RGB")
        if img:
            r = max(tw / img.width, th / img.height)
            img = img.resize((round(img.width * r), round(img.height * r)))
            img = img.crop(((img.width - tw) // 2, (img.height - th) // 2, (img.width - tw) // 2 + tw, (img.height - th) // 2 + th))
            sheet.paste(img, (x, y))
        else:
            d.rectangle((x, y, x + tw, y + th), fill=(40, 40, 44))
            d.text((x + 12, y + th // 2 - 20), "no photo yet", font=font(26), fill=(140, 140, 140))
        k = s.get("kind", "move")
        d.rectangle((x, y, x + tw, y + th), outline=COL.get(k, (200, 200, 200)), width=4)
        d.rectangle((x, y, x + 62, y + 52), fill=(0, 0, 0))
        d.text((x + 10, y + 4), str(s["n"]), font=font(40), fill=(255, 255, 255))
        if s.get("clip"):
            d.text((x + tw - 70, y + 8), "CLIP", font=font(24), fill=(120, 255, 140))
        ty = y + th + 6
        d.text((x, ty), f"{fmt(s['t0'])}–{fmt(s['t1'])}  {s['t1'] - s['t0']:.1f}s  {ICON.get(k, k).upper()}", font=font(22),
               fill=COL.get(k, (200, 200, 200)))
        line = (s.get("text") or s.get("line") or s.get("what") or "")[:44]
        d.text((x, ty + 30), line, font=font(22), fill=(235, 230, 220))
        d.text((x, ty + 60), (s.get("what") or "")[:46], font=font(18), fill=(150, 150, 150))
    sheet.save(a.out)
    print(json.dumps({"ok": True, "out": a.out, "shots": len(shots)}))


def cmd_plan(a):
    """Times from the song: a shot per lyric line; gaps without voice split on the beat into shots of at most --max s."""
    b = load(a.board) if Path(a.board).exists() else {"shots": []}
    lines = [l for l in load(a.lines) if not l.get("choir")]
    end = b.get("end") or (lines[-1]["t1"] + 1.5 if lines else 30)
    cuts = [0.0]
    for l in lines:
        if l["t0"] > cuts[-1] + 0.3:
            cuts.append(round(l["t0"], 3))
    cuts.append(end)
    spans = []
    for s0, s1 in zip(cuts, cuts[1:]):                 # split long spans on the beat
        n = max(1, math.ceil((s1 - s0) / a.max))
        step = (s1 - s0) / n
        if a.beat:
            step = max(a.beat, round(step / a.beat) * a.beat)
        t = s0
        while t < s1 - 0.05:
            spans.append((round(t, 3), round(min(s1, t + step), 3)))
            t += step
    merged = []                                          # no shot shorter than half a second: join it to the one before
    for sp in spans:
        if merged and sp[1] - sp[0] < 0.5:
            merged[-1] = (merged[-1][0], sp[1])
        elif merged and merged[-1][1] - merged[-1][0] < 0.5:
            merged[-1] = (merged[-1][0], sp[1])
        else:
            merged.append(sp)
    spans = merged
    old = {s["n"]: s for s in b.get("shots", [])}
    sung_of = [next((l for l in lines if l["t0"] < t1 and l["t1"] > t0), None) for (t0, t1) in spans]
    with_voice = [i for i, l in enumerate(sung_of) if l]
    hook, last = (with_voice[0], with_voice[-1]) if with_voice else (-1, -1)
    shots = []
    for i, (t0, t1) in enumerate(spans, 1):
        sung = sung_of[i - 1]
        prev = old.get(i, {})
        default = "sing" if (i - 1) in (hook, last) else ("move" if sung else "dance")
        shots.append({"n": i, "t0": t0, "t1": t1, "kind": prev.get("kind", default),
                      "line": sung["text"] if sung else "", "what": prev.get("what", ""), "still": prev.get("still"),
                      "clip": prev.get("clip"), "text": prev.get("text")})
    b["shots"] = shots
    Path(a.board).write_text(json.dumps(b, indent=1, ensure_ascii=False))
    print(json.dumps({"ok": True, "shots": len(shots), "board": a.board}))


def cmd_check(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    miss_photo = [s["n"] for s in b["shots"] if not s.get("still") or not (base / s["still"]).exists()]
    to_make = [s for s in b["shots"] if not s.get("clip")]
    cost = round(sum(PRICE.get(s.get("kind"), 0) * (s["t1"] - s["t0"] + 1.0) for s in to_make), 2)
    print(json.dumps({"shots": len(b["shots"]), "missing_photos": miss_photo, "clips_to_make": [s["n"] for s in to_make],
                      "singing_shots_cost_usd": cost, "note": "dance/move clips are Grok Imagine, inside the person's plan"}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet"); s.add_argument("board"); s.add_argument("--out", default="board.png")
    p = sub.add_parser("plan"); p.add_argument("board"); p.add_argument("--lines", required=True)
    p.add_argument("--beat", type=float, default=0.0); p.add_argument("--max", type=float, default=2.0)
    c = sub.add_parser("check"); c.add_argument("board")
    a = ap.parse_args()
    {"sheet": cmd_sheet, "plan": cmd_plan, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
