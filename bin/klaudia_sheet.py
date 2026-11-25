#!/usr/bin/env python3
"""KLAUDIA BOT · numbered sheets to CHOOSE from (pictures and a number, not paragraphs). Model: "WHICH KLAUDIA?"
(three Klaudias, the same face and streak, big orange numbers, one line underneath).

  pick     python3 klaudia_sheet.py pick --images a.png b.png c.png --labels "Slim" "Curvy" "Full" \
               --title "WHICH KLAUDIA?" --foot "Same face. Same streak. You pick the body." --out sheet.png
           any choice made of pictures (outfits, roles, places, "more options", the person's own…)
  grades   python3 klaudia_sheet.py grades --photo photos/01.png --out grades.png
           the same photo in every colour of kit/grades.json (exactly what the edit will do)
  words    python3 klaudia_sheet.py words --photo photos/01.png --line "Four viewers. Two are robots." --out words.png
           the lyric styles of kit/lyric-styles.json on that photo (exactly what the edit draws)
  looks    python3 klaudia_sheet.py looks --photo photos/01.png --title "FOUR VIEWERS" --out looks.png
           the frame around the picture: news (TV) · clip (clean) · ad (unpaid)
  examples python3 klaudia_sheet.py examples        rebuild the free example sheets in sheets/ (no spend)
The person answers with a number ("2"), or a button: 🔄 more options · ✍️ my own.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klaudia_common as kc  # noqa: E402

KIT = HERE.parent
ORANGE, CREAM, BG = (230, 110, 40), (245, 240, 230), (12, 12, 12)
AI_LINE = "Klaudia is an AI character"


def cover(im, w, h, face=True):
    im = im.convert("RGB")
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    fs = kc.faces(im) if face else None
    cx = fs[0][0] + fs[0][2] / 2 if fs else im.width / 2
    cy = fs[0][1] + fs[0][3] / 2 if fs else im.height * 0.4
    x = int(min(max(cx - w / 2, 0), im.width - w))
    y = int(min(max(cy - h * 0.38, 0), im.height - h))
    return im.crop((x, y, x + w, y + h))


def pick_sheet(images, labels, title, foot, out, cell=(420, 746)):
    n = len(images)
    cols = n if n <= 4 else (3 if n in (5, 6, 9) else 4)
    rows = -(-n // cols)
    cw, ch = cell
    pad, top, bottom = 36, 130, 96 + 54
    W = cols * cw + (cols + 1) * pad
    H = top + rows * (ch + 60) + (rows - 1) * pad + bottom
    sh = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(sh)
    tf = kc.font(88)
    d.text(((W - d.textlength(title, font=tf)) / 2, 22), title, font=tf, fill=(255, 255, 255))
    for i, (img, lab) in enumerate(zip(images, labels)):
        x = pad + (i % cols) * (cw + pad)
        y = top + (i // cols) * (ch + 60 + pad)
        im = img if isinstance(img, Image.Image) else Image.open(img)
        sh.paste(cover(im, cw, ch), (x, y))
        r = 46                                   # the number sits low on the left: the top holds the frame's own marks
        by = y + ch - 2 * r - 18
        d.ellipse((x + 18, by, x + 18 + 2 * r, by + 2 * r), fill=ORANGE)
        nf = kc.font(64)
        num = str(i + 1)
        d.text((x + 18 + r - d.textlength(num, font=nf) / 2, by + 4), num, font=nf, fill=(255, 255, 255))
        lf = kc.font(38)
        lab = str(lab)
        while d.textlength(lab, font=lf) > cw and lf.size > 20:
            lf = kc.font(lf.size - 2)
        d.text((x + (cw - d.textlength(lab, font=lf)) / 2, y + ch + 10), lab, font=lf, fill=CREAM)
    ff = kc.font(34)
    line = f"{foot}   ·   {AI_LINE}" if foot else AI_LINE
    d.text(((W - d.textlength(line, font=ff)) / 2, H - 86), line, font=ff, fill=(200, 200, 200))
    bf = kc.font(30)
    btn = "Answer with a number  ·  🔄 more options  ·  ✍️ my own"
    d.text(((W - d.textlength(btn, font=bf)) / 2, H - 46), btn.replace("🔄 ", "").replace("✍️ ", ""), font=bf, fill=ORANGE)
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    sh.save(out, quality=88)
    return {"ok": True, "out": str(out), "options": [str(x) for x in labels]}


def _vertical(photo):
    return cover(Image.open(photo), 720, 1280)


def grades_sheet(photo, out):
    grades = json.loads((KIT / "kit" / "grades.json").read_text())["grades"]
    base = _vertical(photo)
    tmp = Path(tempfile.mkdtemp())
    src = tmp / "src.png"
    base.save(src)
    imgs = []
    for g in grades:
        o = tmp / f"{g['id']}.png"
        vf = (g["ffmpeg"] + ",") if g["ffmpeg"] else ""
        kc.run_ff(["-i", str(src), "-vf", vf + "format=rgb24", "-frames:v", "1", str(o)])
        imgs.append(Image.open(o).copy())
    return pick_sheet(imgs, [g["label"].split("·", 1)[-1].strip() for g in grades], "THE COLOUR",
                      "One colour for the whole video: every shot matches.", out, cell=(300, 533))


def _edit_frame(photo, layers_fn):
    import klaudia_edit as ke
    ke.W, ke.H, ke.S = 1080, 1920, 1.0
    img = cover(Image.open(photo), 1080, 1920).convert("RGBA")
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    layers_fn(ke, lay)
    img.alpha_composite(lay)
    return img.convert("RGB")


def words_sheet(photo, line, out):
    styles = json.loads((KIT / "kit" / "lyric-styles.json").read_text())["styles"]
    imgs = []
    for st in styles:
        def draw(ke, lay, sid=st["id"]):
            if sid == "karaoke":
                ke.draw_text(lay, line.upper(), 96, ke.CREAM, int(1920 * 0.8), hot=1)
            elif sid == "giant":
                ke.draw_text(lay, line.split()[0].upper(), 260, ke.CREAM, int(1920 * 0.5), stroke=10)
            elif sid == "box":
                ke.draw_text(lay, line, 80, ke.CREAM, int(1920 * 0.79), box=True)
            elif sid == "classic":
                ke.draw_text(lay, line.upper(), 96, ke.CREAM, int(1920 * 0.8))
            ke.draw_text(lay, "ROBOTS!", 140, ke.ORANGE, int(1920 * (0.68 if sid == "giant" else 0.615)), stroke=8)
        imgs.append(_edit_frame(photo, draw))
    return pick_sheet(imgs, [s["label"] for s in styles], "THE WORDS", "How the lyric appears on screen.", out, cell=(330, 587))


def looks_sheet(photo, title, out):
    looks = [("news", "News (TV)"), ("clip", "Music video (clean)"), ("ad", "Ad (unpaid)")]
    imgs = []
    for lid, _ in looks:
        def draw(ke, lay, lid=lid):
            ke.chrome(lay, lid, title, 0)
            if lid == "clip":
                ke.draw_text(lay, title.upper(), 120, ke.CREAM, int(1920 * 0.156), stroke=8)
            ke.draw_text(lay, "TWO OF THEM ARE ROBOTS.", 96, ke.CREAM, int(1920 * (0.76 if lid == "news" else 0.8)))
        imgs.append(_edit_frame(photo, draw))
    return pick_sheet(imgs, [l for _, l in looks], "THE FRAME", "News, music video or ad.", out)


def examples():
    """The free example sheets kept in the repo (made from the public reference images only)."""
    out = KIT / "sheets"
    out.mkdir(exist_ok=True)
    face = KIT / "refs" / "klaudia-face.jpg"
    res = [grades_sheet(face, out / "grades.jpg"),
           words_sheet(face, "Four viewers. Two are robots.", out / "words.jpg"),
           looks_sheet(face, "FOUR VIEWERS", out / "looks.jpg")]
    g = out / "graphics.jpg"
    subprocess.run([sys.executable, str(HERE / "klaudia_graphics.py"), "demo", "--out", str(g)], check=True, capture_output=True)
    res.append({"ok": True, "out": str(g)})
    return res


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pick")
    p.add_argument("--images", nargs="+", required=True); p.add_argument("--labels", nargs="+")
    p.add_argument("--title", default="PICK ONE"); p.add_argument("--foot", default=""); p.add_argument("--out", required=True)
    g = sub.add_parser("grades"); g.add_argument("--photo", required=True); g.add_argument("--out", required=True)
    w = sub.add_parser("words"); w.add_argument("--photo", required=True); w.add_argument("--line", required=True); w.add_argument("--out", required=True)
    lk = sub.add_parser("looks"); lk.add_argument("--photo", required=True); lk.add_argument("--title", default="KLAUDIA'S NEWS"); lk.add_argument("--out", required=True)
    sub.add_parser("examples")
    a = ap.parse_args()
    if a.cmd == "pick":
        labels = a.labels or [""] * len(a.images)
        print(json.dumps(pick_sheet(a.images, labels, a.title, a.foot, a.out)))
    elif a.cmd == "grades":
        print(json.dumps(grades_sheet(a.photo, a.out)))
    elif a.cmd == "words":
        print(json.dumps(words_sheet(a.photo, a.line, a.out)))
    elif a.cmd == "looks":
        print(json.dumps(looks_sheet(a.photo, a.title, a.out)))
    else:
        print(json.dumps(examples()))


if __name__ == "__main__":
    main()
