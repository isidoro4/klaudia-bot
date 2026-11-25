#!/usr/bin/env python3
"""KLAUDIA BOT · graphics that EXPLAIN a line as an object of the world (a ticket, a counter, a meter…), drawn in
code on top of the picture (never generated letters). Used by klaudia_edit.py; kit/graphics.json lists them with
examples. A shot in board.json carries at most one: "graphic": {"type": "ticket", …}.

  python3 klaudia_graphics.py demo --out graphics.png      → every type on one sheet (to look at them)

Types (fields):
  ticket   title, rows [[left, right], …], total [left, right]     a till receipt: "MILK 0.99 / DIGNITY FREE / TOTAL…"
  counter  label, from, to, unit                                   a number that counts up during the shot
  meter    label, from, to, unit                                   a bar / thermometer that fills during the shot
  stamp    text                                                    a rubber stamp, slightly crooked
  tag      label, text                                             a price tag on a string
  clock    time, label                                             a digital clock
  chart    label, values [n, …]                                    a line chart that draws itself
  alert    app, text                                               a phone notification (app name invented, no logo)
  headline text, kicker                                            a newspaper headline strip
Never a real logo, a real person's name as a joke, a coin, a price tip or a call to buy.
"""
import argparse
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
import klaudia_common as kc  # noqa: E402

CREAM, ORANGE, INK, PAPER = (255, 246, 228, 255), (255, 122, 26, 255), (18, 18, 20, 255), (250, 247, 240, 255)
MONO = "SpaceMono-Bold.ttf"


def f(size, mono=False):
    return kc.font(size, MONO if mono else "Anton-Regular.ttf")


def _shadow(img, r=18):
    from PIL import ImageFilter
    a = img.split()[-1].filter(ImageFilter.GaussianBlur(r))
    sh = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * 0.55)))
    out = Image.new("RGBA", img.size, (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 10))
    out.alpha_composite(img)
    return out


def _fit(d, text, font_fn, size, maxw):
    while size > 14 and d.textlength(text, font=font_fn(size)) > maxw:
        size -= 2
    return font_fn(size)


def ticket(g, w, p):
    rows = g.get("rows") or []
    lh = int(w * 0.075)
    h = int(w * 0.28) + lh * (len(rows) + (2 if g.get("total") else 0))
    im = Image.new("RGBA", (w + 40, h + 60), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 20, 20
    # zig-zag bottom edge, like a torn receipt
    pts = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h)]
    teeth = 18
    for k in range(teeth, -1, -1):
        pts.append((x0 + w * k / teeth, y0 + h + (14 if k % 2 else 0)))
    d.polygon(pts, fill=PAPER)
    y = y0 + int(w * 0.06)
    title = (g.get("title") or "RECEIPT").upper()
    ft = _fit(d, title, lambda s: f(s, True), int(w * 0.07), w - 60)
    d.text((x0 + (w - d.textlength(title, font=ft)) / 2, y), title, font=ft, fill=INK)
    y += int(w * 0.11)
    d.line((x0 + 24, y, x0 + w - 24, y), fill=INK, width=3)
    y += int(w * 0.04)
    fr = f(int(w * 0.058), True)
    for left, right in rows:
        d.text((x0 + 28, y), str(left).upper(), font=fr, fill=INK)
        d.text((x0 + w - 28 - d.textlength(str(right).upper(), font=fr), y), str(right).upper(), font=fr, fill=INK)
        y += lh
    if g.get("total"):
        y += int(lh * 0.3)
        d.line((x0 + 24, y, x0 + w - 24, y), fill=INK, width=3)
        y += int(lh * 0.3)
        left, right = g["total"]
        fb = f(int(w * 0.075))
        d.text((x0 + 28, y), str(left).upper(), font=fb, fill=INK)
        d.text((x0 + w - 28 - d.textlength(str(right).upper(), font=fb), y), str(right).upper(), font=fb, fill=ORANGE)
    return _shadow(im)


def _number(v, unit):
    s = f"{v:,.0f}" if abs(v) >= 100 or float(v).is_integer() else f"{v:.1f}"
    return s + (unit or "")


def counter(g, w, p):
    a, b = float(g.get("from", 0)), float(g.get("to", 100))
    e = 1 - (1 - min(p * 1.4, 1)) ** 3
    val = a + (b - a) * e
    if float(a).is_integer() and float(b).is_integer():
        val = round(val)
    h = int(w * 0.42)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=18, fill=(10, 10, 12, 230), outline=ORANGE, width=5)
    lab = (g.get("label") or "").upper()
    fl = _fit(d, lab, lambda s: f(s, True), int(w * 0.06), w - 50)
    d.text((28, 22), lab, font=fl, fill=CREAM)
    num = _number(val, g.get("unit", ""))
    fn = _fit(d, num, f, int(h * 0.55), w - 56)
    d.text(((w - d.textlength(num, font=fn)) / 2, int(h * 0.3)), num, font=fn, fill=ORANGE)
    return _shadow(im)


def meter(g, w, p):
    a, b = float(g.get("from", 0)), float(g.get("to", 100))
    e = 1 - (1 - min(p * 1.3, 1)) ** 3
    val = a + (b - a) * e
    lo, hi = min(a, b, 0), max(a, b, 100 if (g.get("unit") == "%") else max(a, b))
    h = int(w * 0.36)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=18, fill=(10, 10, 12, 230))
    lab = (g.get("label") or "").upper()
    fl = _fit(d, lab, lambda s: f(s, True), int(w * 0.055), w - 50)
    d.text((26, 20), lab, font=fl, fill=CREAM)
    bx0, by0, bx1, by1 = 26, int(h * 0.42), w - 26, int(h * 0.68)
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=12, outline=CREAM, width=4)
    frac = 0 if hi == lo else (val - lo) / (hi - lo)
    d.rounded_rectangle((bx0 + 6, by0 + 6, bx0 + 6 + max(0, (bx1 - bx0 - 12) * frac), by1 - 6), radius=8, fill=ORANGE)
    for k in range(1, 10):
        x = bx0 + (bx1 - bx0) * k / 10
        d.line((x, by1 + 6, x, by1 + 18), fill=CREAM, width=2)
    num = _number(val, g.get("unit", ""))
    fn = f(int(h * 0.22))
    d.text((w - 26 - d.textlength(num, font=fn), int(h * 0.72)), num, font=fn, fill=ORANGE)
    return _shadow(im)


def stamp(g, w, p):
    text = (g.get("text") or "APPROVED").upper()
    s = min(1.0, 0.6 + p * 4) if p < 0.1 else 1.0          # it lands
    size = int(w * 0.16)
    tmp = Image.new("RGBA", (w, int(size * 2.2)), (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    ft = _fit(d, text, f, size, w - 80)
    tw = d.textlength(text, font=ft)
    x = (w - tw) / 2
    d.rounded_rectangle((x - 30, 20, x + tw + 30, 40 + ft.size * 1.25), radius=14, outline=ORANGE, width=10)
    d.text((x, 26), text, font=ft, fill=ORANGE)
    tmp = tmp.rotate(-8, expand=True, resample=Image.BICUBIC)
    if s < 1:
        tmp = tmp.resize((max(1, int(tmp.width * (2 - s))), max(1, int(tmp.height * (2 - s)))))
    return tmp


def tag(g, w, p):
    h = int(w * 0.36)
    im = Image.new("RGBA", (w, h + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tw = int(w * 0.8)
    x0, y0 = (w - tw) // 2, 40
    d.polygon([(x0, y0 + h * 0.5), (x0 + h * 0.4, y0), (x0 + tw, y0), (x0 + tw, y0 + h), (x0 + h * 0.4, y0 + h)], fill=CREAM)
    d.ellipse((x0 + h * 0.22, y0 + h * 0.42, x0 + h * 0.34, y0 + h * 0.58), fill=(60, 60, 60, 255))
    d.line((x0 + h * 0.28, y0 + h * 0.5, x0 + h * 0.1, 0), fill=CREAM, width=4)
    lab = (g.get("label") or "").upper()
    fl = f(int(h * 0.16), True)
    d.text((x0 + h * 0.5, y0 + h * 0.1), lab, font=fl, fill=INK)
    txt = str(g.get("text") or "").upper()
    ft = _fit(d, txt, f, int(h * 0.5), tw - h * 0.6)
    d.text((x0 + h * 0.5, y0 + h * 0.36), txt, font=ft, fill=ORANGE)
    return _shadow(im)


def clock(g, w, p):
    h = int(w * 0.34)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=20, fill=(8, 8, 8, 240), outline=(60, 60, 60, 255), width=4)
    t = str(g.get("time") or "23:59")
    if p % 0.5 > 0.25:
        t = t.replace(":", " ")
    ft = _fit(d, t, lambda s: f(s, True), int(h * 0.62), w - 60)
    d.text(((w - d.textlength(t, font=ft)) / 2, int(h * 0.12)), t, font=ft, fill=(255, 60, 40, 255))
    if g.get("label"):
        fl = f(int(h * 0.13), True)
        lab = g["label"].upper()
        d.text(((w - d.textlength(lab, font=fl)) / 2, int(h * 0.8)), lab, font=fl, fill=CREAM)
    return _shadow(im)


def chart(g, w, p):
    vals = [float(v) for v in (g.get("values") or [1, 2, 1.5, 3, 5, 9])]
    h = int(w * 0.6)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=18, fill=(10, 10, 12, 225))
    lab = (g.get("label") or "").upper()
    fl = _fit(d, lab, lambda s: f(s, True), int(w * 0.055), w - 50)
    d.text((26, 18), lab, font=fl, fill=CREAM)
    x0, y0, x1, y1 = 40, int(h * 0.25), w - 40, h - 40
    for k in range(4):
        y = y0 + (y1 - y0) * k / 3
        d.line((x0, y, x1, y), fill=(70, 70, 70, 255), width=2)
    lo, hi = min(vals), max(vals)
    pts = [(x0 + (x1 - x0) * i / (len(vals) - 1), y1 - (y1 - y0) * ((v - lo) / (hi - lo) if hi > lo else 0.5))
           for i, v in enumerate(vals)]
    reach = min(p * 1.5, 1) * (len(pts) - 1)
    k = int(reach)
    drawn = pts[:k + 1]
    if k < len(pts) - 1:
        fr = reach - k
        a, b = pts[k], pts[k + 1]
        drawn.append((a[0] + (b[0] - a[0]) * fr, a[1] + (b[1] - a[1]) * fr))
    if len(drawn) > 1:
        d.line(drawn, fill=ORANGE, width=9, joint="curve")
    ex, ey = drawn[-1]
    d.ellipse((ex - 12, ey - 12, ex + 12, ey + 12), fill=ORANGE)
    return _shadow(im)


def alert(g, w, p):
    h = int(w * 0.3)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, w, h), radius=34, fill=(245, 245, 247, 245))
    d.rounded_rectangle((26, 26, 26 + h * 0.34, 26 + h * 0.34), radius=14, fill=ORANGE)
    fa = f(int(h * 0.13), True)
    d.text((40 + h * 0.36, 30), (g.get("app") or "NEWS").upper() + "  ·  now", font=fa, fill=(110, 110, 110, 255))
    txt = str(g.get("text") or "")
    fs = int(h * 0.2)
    ft = f(fs)
    rows, cur = [], ""
    for word in txt.split():
        t = (cur + " " + word).strip()
        if d.textlength(t, font=ft) <= w - 60 or not cur:
            cur = t
        else:
            rows.append(cur)
            cur = word
    rows.append(cur)
    y = int(h * 0.48)
    for r in rows[:2]:
        d.text((30, y), r, font=ft, fill=INK)
        y += int(fs * 1.1)
    off = int((1 - min(p * 6, 1)) * -h)                # slides down
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.alpha_composite(im, (0, off)) if off > -h else None
    return _shadow(out)


def headline(g, w, p):
    h = int(w * 0.34)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, h), fill=PAPER)
    kick = (g.get("kicker") or "EXTRA").upper()
    fk = f(int(h * 0.15), True)
    d.rectangle((0, 0, w, int(h * 0.25)), fill=INK)
    d.text((22, int(h * 0.04)), kick, font=fk, fill=PAPER)
    txt = (g.get("text") or "").upper()
    ft = _fit(d, txt, f, int(h * 0.52), w - 44)
    d.text((22, int(h * 0.32)), txt, font=ft, fill=INK)
    return _shadow(im.rotate(2, expand=True, resample=Image.BICUBIC))


DRAW = {"ticket": ticket, "counter": counter, "meter": meter, "stamp": stamp, "tag": tag, "clock": clock,
        "chart": chart, "alert": alert, "headline": headline}
WIDTH = {"ticket": 0.56, "counter": 0.5, "meter": 0.62, "stamp": 0.62, "tag": 0.5, "clock": 0.46, "chart": 0.6,
         "alert": 0.8, "headline": 0.78}


def render(g, W, H, p=1.0):
    """The graphic as an RGBA image sized for a W×H frame (p = 0…1 progress through the shot)."""
    kind = g.get("type")
    if kind not in DRAW:
        return None
    w = int(H * 0.95 * WIDTH[kind]) if W > H else int(W * WIDTH[kind])
    return DRAW[kind](g, w, max(0.0, min(1.0, p)))


def demo(out):
    examples = [
        {"type": "ticket", "title": "PROTEIN BAR · AISLE 4", "rows": [["PROTEIN", "30 G"], ["FLAVOUR", "PROMPT"], ["TASTE", "N/A"]], "total": ["TOTAL", "GAINS"]},
        {"type": "counter", "label": "LIVE VIEWERS", "from": 0, "to": 4},
        {"type": "meter", "label": "CHANCE OF SNOW", "from": 0, "to": 100, "unit": "%"},
        {"type": "stamp", "text": "UNPAID"},
        {"type": "tag", "label": "PRICE", "text": "$0.00"},
        {"type": "clock", "time": "23:59", "label": "DEADLINE"},
        {"type": "chart", "label": "AI GIRLS WITH A BOT", "values": [0, 0, 1, 1, 2, 9]},
        {"type": "alert", "app": "Klaudia's News", "text": "X will pay streamers. You have four viewers."},
        {"type": "headline", "kicker": "KLAUDIA'S NEWS", "text": "NOBODY INVITED HER"},
    ]
    W, H = 1080, 1920
    cell = 520
    sheet = Image.new("RGBA", (cell * 3, cell * 3), (40, 40, 44, 255))
    for i, g in enumerate(examples):
        im = render(g, W, H, 1.0)
        im.thumbnail((cell - 30, cell - 60))
        x, y = (i % 3) * cell, (i // 3) * cell
        sheet.alpha_composite(im, (x + (cell - im.width) // 2, y + 40 + (cell - 60 - im.height) // 2))
        ImageDraw.Draw(sheet).text((x + 14, y + 8), g["type"], font=f(30), fill=CREAM)
    sheet.convert("RGB").save(out)
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cmd", choices=["demo"])
    ap.add_argument("--out", default="graphics.png")
    a = ap.parse_args()
    demo(a.out)
