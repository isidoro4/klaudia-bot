#!/usr/bin/env python3
"""KLAUDIA BOT · the thumbnail and the post, made while the clips are being made (free, on this computer).

  python3 klaudia_social.py --board board.json [--photo photos/01.full.png] [--post "text"] --out social/
    → social/thumb-youtube.jpg (1280×720) · social/x-post.jpg (1600×900) · social/cover-vertical.jpg (1080×1920)
      · social/post.txt (the post to copy, with "fan-made with KLAUDIA BOT · made with AI")
The photo: the one given, else the board's first sung shot, else the first shot. Her face goes to one side and the
title to the other. Corners kept clear: bottom-left (X writes its card label there) and bottom-right (YouTube's
clock). The bot never posts: the person does.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klaudia_common as kc  # noqa: E402

ORANGE, CREAM = (255, 122, 26), (255, 246, 228)
FOOT = "fan-made with KLAUDIA BOT · made with AI"


def place_face(im, w, h, side):
    """Fill w×h with her face on `side` ('left'/'right'/'center')."""
    im = im.convert("RGB")
    r = max(w / im.width, h / im.height) * (1.15 if w > h else 1.25)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    f = kc.faces(im)
    cx = f[0][0] + f[0][2] / 2 if f else im.width / 2
    cy = f[0][1] + f[0][3] / 2 if f else im.height * 0.4
    want = {"left": 0.3, "right": 0.7, "center": 0.5}[side] * w
    x = int(min(max(cx - want, 0), im.width - w))
    y = int(min(max(cy - h * (0.55 if side == "center" else 0.42), 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def title_block(img, title, tag, box, big):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    words = title.upper().split()
    size = big
    while size > 40:
        f = kc.font(size)
        rows, cur = [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if d.textlength(t, font=f) <= x1 - x0 or not cur:
                cur = t
            else:
                rows.append(cur)
                cur = w_
        rows.append(cur)
        if len(rows) * size * 1.02 <= (y1 - y0) * 0.75 and max(d.textlength(r_, font=f) for r_ in rows) <= x1 - x0:
            break
        size -= 6
    y = y0
    for r_ in rows:
        d.text((x0, y), r_, font=f, fill=CREAM, stroke_width=max(4, size // 18), stroke_fill=(0, 0, 0))
        y += int(size * 1.02)
    if tag:
        tf = kc.font(max(36, size // 2))
        d.rectangle((x0 - 10, y + 10, x0 + d.textlength(tag.upper(), font=tf) + 14, y + 20 + tf.size * 1.15), fill=ORANGE)
        d.text((x0, y + 12), tag.upper(), font=tf, fill=(0, 0, 0))


def shade(img, side):
    w, h = img.size
    g = Image.new("L", (w, 1))
    for x in range(w):
        t = x / w if side == "right" else 1 - x / w
        g.putpixel((x, 0), int(200 * max(0, t - 0.35) / 0.65))
    g = g.resize((w, h))
    black = Image.new("RGB", (w, h), (0, 0, 0))
    return Image.composite(black, img, g)


def make(photo, title, tag, out, post):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    src = Image.open(photo)
    # YouTube 1280×720: face left, title right (top), bottom-right clock stays clear
    yt = shade(place_face(src, 1280, 720, "left"), "right")
    title_block(yt, title, tag, (640, 60, 1240, 560), 150)
    yt.save(out / "thumb-youtube.jpg", quality=90)
    # X 1600×900: face right, title left TOP (bottom-left = X's label)
    xp = shade(place_face(src, 1600, 900, "right"), "left")
    title_block(xp, title, tag, (70, 60, 760, 560), 170)
    ImageDraw.Draw(xp).text((1600 - 40 - ImageDraw.Draw(xp).textlength(FOOT, font=kc.font(30)), 850), FOOT,
                            font=kc.font(30), fill=(220, 220, 220))
    xp.save(out / "x-post.jpg", quality=90)
    # vertical cover 1080×1920 (Reels / TikTok / Shorts): face centre, title top
    vc = place_face(src, 1080, 1920, "center")
    top = Image.new("L", (1, 1920))
    for y in range(1920):
        top.putpixel((0, y), int(190 * max(0, 1 - y / 700)))
    vc = Image.composite(Image.new("RGB", vc.size, (0, 0, 0)), vc, top.resize(vc.size))
    title_block(vc, title, tag, (70, 120, 1010, 760), 190)
    vc.save(out / "cover-vertical.jpg", quality=90)
    text = (post or f"{title}\n\n___ yourself.") + f"\n\n{FOOT}"
    (out / "post.txt").write_text(text)
    return {"ok": True, "out": [str(out / n) for n in ("thumb-youtube.jpg", "x-post.jpg", "cover-vertical.jpg", "post.txt")]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--board")
    ap.add_argument("--photo")
    ap.add_argument("--title")
    ap.add_argument("--tag")
    ap.add_argument("--post", help="the post text in Klaudia's voice (the AI label is added for you)")
    ap.add_argument("--out", default="social")
    a = ap.parse_args()
    title, tag, photo = a.title, a.tag, a.photo
    if a.board:
        b = json.loads(Path(a.board).read_text())
        base = Path(a.board).resolve().parent
        title, tag = title or b.get("title", "KLAUDIA"), tag or b.get("tag", "")
        if not photo:
            shots = [s for s in b["shots"] if s.get("kind") == "sing" and s.get("still")] or [s for s in b["shots"] if s.get("still")]
            if not shots:
                sys.exit("No photo yet.")
            st = base / shots[0]["still"]
            full = st.with_suffix(".full.png")
            photo = full if full.exists() else st
    if not photo:
        sys.exit("Give --board or --photo.")
    print(json.dumps(make(photo, title or "KLAUDIA", tag or "", a.out, a.post)))


if __name__ == "__main__":
    main()
