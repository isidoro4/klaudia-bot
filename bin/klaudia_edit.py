#!/usr/bin/env python3
"""KLAUDIA BOT edit: a video from a song, its timed lyrics and clips or stills.
Vertical 9:16 (news, sponsorship) or --format horizontal 16:9 (music video). --also makes the other shape too.

Needs Python 3.9+, Pillow and ffmpeg (ffmpeg on PATH, or `pip install imageio-ffmpeg`). numpy/OpenCV optional
(with OpenCV the crops and the graphics keep clear of her face).

  python3 klaudia_edit.py --board board.json --out news.mp4 [--also]        ← the normal way (klaudia_board.py)
  python3 klaudia_edit.py --song song.mp3 --words alignment.json --lyrics lyrics.txt \
      --clips c1.mp4 c2.mp4 still3.png ... --title "FOUR VIEWERS" --tag "STREAM YOURSELF." --out news.mp4

Timing, one of: --words (Suno's lyric alignment JSON) with --lyrics (the lyric as sent to Suno; [section tags]
give each line its part, lines in (PARENTHESES) are the choir) · --lines (a JSON list of {"text","t0","t1","choir"})
· --every SECONDS (no timing: cut on a steady rhythm) · --board.
Sung takes: a clip with a .sync.json beside it (klaudia_sing.py writes it) is placed by the SONG's clock: every
syllable lands on its own second, whatever the shot's start. No "@0.7" by hand any more (0.6 counted it twice).
A clip given as path@SECONDS starts there; path^1.5 plays it 1.5× faster; "+" keeps playing the previous clip.

Looks (from the board's "style" or the flags):
  --look news | clip | ad         the frame around the picture: TV news bug and lower third · clean · "unpaid" ad
  --lyrics classic | karaoke | giant | box | none     how the words appear (kit/lyric-styles.json)
  --grade <id>                    one colour for every shot (kit/grades.json), so clips and stills match
Shots in the board may carry a "graphic" (klaudia_graphics.py): it is drawn where her face is not.
Other options: --end SECONDS · --test 0-10 (only that stretch, fast) · --frames 3.2,11,20 --out frames.png
(style frames: still pictures of the finished look, with the words, the graphic and the colour) · --keep.
"""
import argparse
import difflib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import klaudia_common as kc  # noqa: E402
import klaudia_graphics as kg  # noqa: E402

W, H, FPS = 1080, 1920, 30
S = 1.0  # text scale
KIT = Path(__file__).resolve().parent.parent
CREAM, ORANGE, BLACK = (255, 246, 228), (255, 122, 26), (0, 0, 0)
FOOTER = "fan-made with KLAUDIA BOT · made with AI"
STILL = {".png", ".jpg", ".jpeg", ".webp"}
FF = None
ANIMATED = {"counter", "meter", "chart", "alert", "stamp", "clock"}


def run(args):
    r = subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-2000:])


def font(size):
    return kc.font(size)


def load_json(p):
    return json.loads(Path(p).read_text())


# ======================= timing =======================
def lyric_lines(text):
    out, part = [], "verse"
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        if s.startswith("[") and s.endswith("]"):
            part = re.split(r"[\s\-:\]]+", s[1:].strip().lower())[0] or part
            continue
        choir = s.startswith("(") and s.endswith(")")
        out.append({"text": s.strip("()").strip(), "choir": choir, "part": part})
    return out


def word_list(data):
    """Suno's alignment: tokens (often pieces of words, with punctuation, line breaks and the unsung choir lines
    inside them) with start_s/end_s. Returns [(text, start, end)] in order."""
    if isinstance(data, dict):
        for k in ("words", "aligned_words", "alignment", "data"):
            if isinstance(data.get(k), list):
                return word_list(data[k])
        sys.exit("--words: no list of words found in the JSON.")
    out = []
    for w in data:
        txt = w.get("word", w.get("text", ""))
        a = w.get("start_s", w.get("start", w.get("startS")))
        b = w.get("end_s", w.get("end", w.get("endS")))
        if a is not None and b is not None:
            out.append((str(txt), float(a), float(b)))
    return out


def _norm_with_words(text):
    """Letters and digits only, lower case, and which word each letter belongs to."""
    chars, wid, words = [], [], text.split()
    for k, w in enumerate(words):
        for c in w.lower():
            if c.isalnum():
                chars.append(c)
                wid.append(k)
    return "".join(chars), wid, words


def lines_from_words(tokens, lyrics):
    """Find every lyric line in Suno's tokens by its LETTERS ONLY (spaces, punctuation and line breaks in the tokens
    do not matter: 0.6 lost every line after a token without spaces and showed "OPEIBUILDS"). A line that is not found
    exactly is matched loosely; a line still not found gets its time from its neighbours: no line is ever dropped."""
    stream, owner = [], []
    for k, (txt, _, _) in enumerate(tokens):
        for c in txt.lower():
            if c.isalnum():
                stream.append(c)
                owner.append(k)
    stream = "".join(stream)
    out, cur = [], 0
    for ln in lyrics:
        target, wid, words = _norm_with_words(ln["text"])
        item = {**ln, "t0": None, "t1": None, "words": []}
        out.append(item)
        if not target or ln["choir"]:   # the choir is not aligned by Suno: searching for it moved the cursor too far
            continue
        lo, hi = cur, min(len(stream), cur + len(target) * 4 + 300)
        pos = stream.find(target, lo, hi)
        idx = None
        if pos >= 0:
            idx = list(range(pos, pos + len(target)))
            cur = pos + len(target)
        else:
            sm = difflib.SequenceMatcher(None, stream[lo:hi], target, autojunk=False)
            blocks = [b for b in sm.get_matching_blocks() if b.size >= 2]
            got = sum(b.size for b in blocks)
            if blocks and got >= 0.6 * len(target):
                idx = [None] * len(target)
                for b in blocks:
                    for j in range(b.size):
                        idx[b.b + j] = lo + b.a + j
                cur = lo + blocks[-1].a + blocks[-1].size
        if not idx:
            continue
        known = [i for i in idx if i is not None]
        item["t0"], item["t1"] = tokens[owner[known[0]]][1], tokens[owner[known[-1]]][2]
        for k, w in enumerate(words):
            ids = [idx[j] for j in range(len(target)) if wid[j] == k and idx[j] is not None]
            if ids:
                item["words"].append({"w": w, "t0": tokens[owner[ids[0]]][1], "t1": tokens[owner[ids[-1]]][2]})
    # sung lines that were not found: between their neighbours
    sung = [x for x in out if not x["choir"]]
    for i, x in enumerate(sung):
        if x["t0"] is None:
            prev = next((y["t1"] for y in reversed(sung[:i]) if y["t0"] is not None), 0.0)
            nxt = next((y["t0"] for y in sung[i + 1:] if y["t0"] is not None), prev + 2.0)
            x["t0"], x["t1"], x["guessed"] = prev + 0.1, max(nxt - 0.1, prev + 0.6), True
    # choir lines (not sung by her, so not aligned well): the gap between the sung lines around them
    for i, x in enumerate(out):
        if x["choir"]:
            prev = next((y["t1"] for y in reversed(out[:i]) if not y["choir"]), 0.0)
            nxt = next((y["t0"] for y in out[i + 1:] if not y["choir"]), prev + 1.2)
            x["t0"], x["t1"] = prev + 0.05, max(nxt - 0.05, prev + 0.6)
    for x in out:   # words without times (loose matches): spread over the line
        if not x["words"] or len(x["words"]) != len(x["text"].split()):
            ws = x["text"].split()
            span = max(x["t1"] - x["t0"], 0.3)
            x["words"] = [{"w": w, "t0": x["t0"] + span * k / len(ws), "t1": x["t0"] + span * (k + 1) / len(ws)}
                          for k, w in enumerate(ws)]
    return out


# ======================= pictures of text =======================
def wrap(draw, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= maxw or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def draw_text(img, text, size, color, y_center, stroke=6, hot=None, box=False):
    """Centred words; `hot` = index of the word sung now (karaoke, in orange); box = black on a cream card."""
    d = ImageDraw.Draw(img)
    f = font(size)
    rows = wrap(d, text, f, W - 140)
    lh = int(size * 1.08)
    y = int(y_center - lh * len(rows) / 2)
    if box:
        wmax = max(d.textlength(r, font=f) for r in rows)
        d.rounded_rectangle(((W - wmax) / 2 - 34, y - 22, (W + wmax) / 2 + 34, y + lh * len(rows) + 14),
                            radius=26, fill=CREAM + (240,))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    k = 0
    for r in rows:
        x = (W - d.textlength(r, font=f)) / 2
        if not box:
            ds.text((x + 6, y + 8), r, font=f, fill=(0, 0, 0, 170))
        for w in r.split(" "):
            col = ORANGE if (hot is not None and k == hot) else ((20, 20, 20) if box else color)
            d.text((x, y), w, font=f, fill=col, stroke_width=0 if box else stroke, stroke_fill=BLACK)
            x += d.textlength(w + " ", font=f)
            k += 1
        y += lh
    if not box:
        shadow = shadow.filter(ImageFilter.GaussianBlur(6))
        base = Image.new("RGBA", img.size, (0, 0, 0, 0))
        base.alpha_composite(shadow)
        base.alpha_composite(img)
        img.paste(base)


def card_png(path, title, tag):
    img = Image.new("RGB", (W, H), (12, 12, 14))
    d = ImageDraw.Draw(img)
    big = int(150 * S)
    y = int(H * 0.36)
    for r in wrap(d, title.upper(), font(big), W - 120):
        d.text(((W - d.textlength(r, font=font(big))) / 2, y), r, font=font(big), fill=CREAM)
        y += int(big * 1.07)
    y += 40
    mid = int(96 * S)
    for r in wrap(d, tag.upper(), font(mid), W - 120):
        d.text(((W - d.textlength(r, font=font(mid))) / 2, y), r, font=font(mid), fill=ORANGE)
        y += int(mid * 1.08)
    f = font(40)
    d.text(((W - d.textlength(FOOTER, font=f)) / 2, H - int(H * 0.1)), FOOTER, font=f, fill=(170, 170, 170))
    img.save(path)


def split_chunks(line, maxwords=4):
    """A long line → chunks of at most 4 words, timed by their own words."""
    words = line["words"]
    groups, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= maxwords or w["w"][-1:] in ".!?,":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return [{**line, "text": " ".join(w["w"] for w in g), "t0": g[0]["t0"], "t1": g[-1]["t1"], "words": g}
            for g in groups if g]


# ======================= the frame around the picture (look) =======================
def chrome(img, look, title, t):
    d = ImageDraw.Draw(img)
    if look == "news":
        f = font(int(44 * S))
        lab = "KLAUDIA'S NEWS"
        w = d.textlength(lab, font=f)
        d.rectangle((40, 60, 40 + w + 40, 60 + int(66 * S)), fill=ORANGE + (255,))
        d.text((60, 64), lab, font=f, fill=(255, 255, 255))
        live = font(int(34 * S))
        x = 40 + w + 60
        d.rectangle((x, 66, x + d.textlength("LIVE", font=live) + 64, 66 + int(54 * S)), fill=(12, 12, 12, 230))
        r = int(10 * S)
        d.ellipse((x + 14, 66 + int(27 * S) - r, x + 14 + 2 * r, 66 + int(27 * S) + r), fill=(255, 60, 50))
        d.text((x + 24 + 2 * r, 70), "LIVE", font=live, fill=(255, 60, 50))
        tick = font(int(38 * S))
        band_y = H - int(118 * S)
        d.rectangle((0, band_y, W, band_y + int(64 * S)), fill=(12, 12, 12, 225))
        d.rectangle((0, band_y, int(210 * S), band_y + int(64 * S)), fill=ORANGE + (255,))
        d.text((22, band_y + 8), "BREAKING", font=tick, fill=(255, 255, 255))
        d.text((int(232 * S), band_y + 8), title.upper(), font=tick, fill=CREAM)
    elif look == "ad":
        f = font(int(34 * S))
        lab = "UNPAID · NOT AFFILIATED"
        w = d.textlength(lab, font=f)
        d.rounded_rectangle((W - w - 80, 60, W - 40, 60 + int(58 * S)), radius=10, fill=(255, 255, 255, 235))
        d.text((W - w - 60, 66), lab, font=f, fill=(20, 20, 20))
        sp = font(int(30 * S))
        d.text((44, 66), "Not sponsored", font=sp, fill=(255, 255, 255, 220), stroke_width=3, stroke_fill=BLACK)


# ======================= the layers (everything drawn on top, as ONE overlay) =======================
class Layers:
    def __init__(self, lines, shots, a, end, card):
        self.events = []      # (t0, t1, kind, data)
        self.final = False    # style frames: graphics in their finished state
        self.look, self.title, self.end, self.card = a.look, a.title, end, card
        style = a.lyrics
        if a.look != "news":
            self.events.append((0.4, min(4.0, end - card), "title", a.title.upper()))
        if style != "none":
            chunks = [c for ln in lines for c in (split_chunks(ln) if style != "giant" else
                      [{**ln, "text": w["w"], "t0": w["t0"], "t1": w["t1"], "words": [w]} for w in ln["words"]])]
            for slot in (False, True):                     # sung and choir have their own place: never on top of each other
                seq = sorted([c for c in chunks if c["choir"] == slot and c["t0"] < end - card], key=lambda c: c["t0"])
                for k, c in enumerate(seq):
                    nxt = seq[k + 1]["t0"] - 0.12 if k + 1 < len(seq) else end - card   # = the next one's own start
                    s = max(c["t0"] - 0.12, seq[k - 1]["t0"] - 0.12 + 0.1 if k else 0.0)
                    e = min(c["t1"] + 0.35, nxt, end - card)
                    if e - s < 0.1:
                        e = s + 0.1
                    if style == "karaoke" and not c["choir"] and len(c["words"]) > 1:
                        for j, w in enumerate(c["words"]):
                            ws = s if j == 0 else w["t0"]
                            we = e if j == len(c["words"]) - 1 else c["words"][j + 1]["t0"]
                            if we > ws:
                                self.events.append((ws, we, "lyric", (c["text"], c["choir"], j)))
                    else:
                        self.events.append((s, e, "lyric", (c["text"], c["choir"], None)))
        self.style = style
        for sh in shots:
            if sh.get("graphic"):
                self.events.append((sh["t0"], sh["t1"], "graphic", (sh["graphic"], sh.get("face_out"), sh["t0"], sh["t1"])))

    def boundaries(self, t0, t1):
        b = {t0, t1}
        for s, e, kind, data in self.events:
            for x in (s, e):
                if t0 < x < t1:
                    b.add(x)
            if kind == "graphic" and data[0].get("type") in ANIMATED:
                x = max(s, t0)
                while x < min(e, t1):
                    b.add(x)
                    x += 0.125
        return sorted(round(x * FPS) / FPS for x in b)

    def at(self, t):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if t >= self.end - self.card:
            return img
        if self.look in ("news", "ad"):
            chrome(img, self.look, self.title, t)
        for s, e, kind, data in self.events:
            if not (s <= t < e):
                continue
            if kind == "title":
                draw_text(img, data, int(120 * S), CREAM, int(H * 0.156), stroke=8)
            elif kind == "lyric":
                text, choir, hot = data
                if choir:
                    draw_text(img, text.upper(), int(140 * S), ORANGE, int(H * (0.68 if self.style == "giant" else 0.615)), stroke=8)
                elif self.style == "giant":
                    draw_text(img, text.upper(), int(260 * S), CREAM, int(H * 0.5), stroke=10)
                elif self.style == "box":
                    draw_text(img, text, int(80 * S), CREAM, int(H * 0.79), box=True)
                else:
                    y = int(H * (0.76 if self.look == "news" else 0.8))
                    draw_text(img, text.upper(), int(96 * S), CREAM, y, hot=hot)
            elif kind == "graphic":
                g, zone, g0, g1 = data
                p = 1.0 if self.final else (t - g0) / max(g1 - g0, 0.1)
                gi = kg.render(g, W, H, p)
                if gi is not None:
                    self.place(img, gi, zone)  # zone = her face in the frame
        return img

    def place(self, img, gi, face):
        """Vertical: above or below her face, whichever covers less of her eyes and mouth. 16:9: the side she is not on."""
        maxh = int(H * (0.3 if H > W else 0.6))
        if gi.height > maxh:
            gi = gi.resize((int(gi.width * maxh / gi.height), maxh))
        if H > W:
            x = (W - gi.width) // 2
            top = int(H * (0.12 if self.look == "news" else 0.08))
            low = int(H * 0.7) - gi.height
            y = top
            if face:
                cy, fh = face[1], face[3]
                k0, k1 = (cy - 0.3 * fh) * H, (cy + 0.45 * fh) * H       # eyes to mouth
                cover = lambda y0: max(0, min(y0 + gi.height, k1) - max(y0, k0))
                y = min((top, low), key=cover)
        else:
            free = W * 0.34                          # the third of the frame where she is not
            if face:
                cx, fw = face[0], face[2]
                free = max(W * 0.25, W * ((cx - fw * 0.6) if cx > 0.5 else (1 - cx - fw * 0.6)) - W * 0.06)
            if gi.width > free:
                gi = gi.resize((int(free), max(1, int(gi.height * free / gi.width))))
            y = (H - gi.height) // 2 - int(H * 0.05)
            right = int(W * 0.95) - gi.width
            x = int(W * 0.05) if face and face[0] > 0.5 else right
        img.alpha_composite(gi, (max(0, x), max(0, y)))


# ======================= shots =======================
def face_in(src, at=0.0):
    """Her face in a still or a clip frame, as fractions of the picture: (cx, cy, w, h) or None."""
    try:
        if Path(src).suffix.lower() in STILL:
            im = Image.open(src)
        else:
            tmp = Path(tempfile.mkstemp(suffix=".jpg")[1])
            run(["-ss", f"{max(at, 0):.3f}", "-i", str(src), "-frames:v", "1", str(tmp)])
            im = Image.open(tmp)
            im.load()
            tmp.unlink()
    except (Exception, SystemExit):
        return None
    fs = kc.faces(im)
    if not fs:
        return None
    x, y, w, h = fs[0]
    return ((x + w / 2) / im.width, (y + h / 2) / im.height, w / im.width, h / im.height, im.width / im.height)


def crop_filter(aspect, face):
    """Fill W×H. Close in shape: crop (centred on her face if known). Very different shape: the picture whole on a
    blurred copy of itself (a vertical clip in a 16:9 video, or the other way round)."""
    target = W / H
    # a horizontal picture in a vertical video: crop it on her face; a vertical one in a 16:9 video: whole, on a blur
    if aspect and target / aspect > 1.6:
        return ("split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=40:2,"
                "eq=brightness=-0.12[bg];[b]scale={W}:{H}:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1").format(W=W, H=H)
    if face:
        cx, cy = face[0], face[1]
        return (f"scale={W}:{H}:force_original_aspect_ratio=increase,"
                f"crop={W}:{H}:'max(0,min(iw-{W},iw*{cx:.3f}-{W}/2))':'max(0,min(ih-{H},ih*{cy:.3f}-{H}*0.42))',setsar=1")
    return f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"


def parse_src(c):
    """'clip.mp4@1.2^1.5' → (path, at or None, speed)."""
    speed, at = 1.0, None
    c = str(c)
    if "^" in c:
        c, sp = c.rsplit("^", 1)
        speed = float(sp)
    if "@" in c and c.rsplit("@", 1)[1].replace(".", "", 1).lstrip("-").isdigit():
        c, x = c.rsplit("@", 1)
        at = float(x)
    return c, at, speed


def sync_info(src):
    p = Path(src).with_suffix(".sync.json")
    if not p.exists():
        return None
    s = json.loads(p.read_text())
    return s if s.get("song_start") is not None else None


def make_shot(src, offset, speed, seconds, out, face=None):
    """offset: seconds into the clip where the shot starts (negative = hold its first frame that long first)."""
    src = Path(src)
    aspect = None
    if src.suffix.lower() in STILL:
        with Image.open(src) as im:
            aspect = im.width / im.height
        fill = crop_filter(aspect, face)
        frames = max(int(round(seconds * FPS)), 1)
        z = f"zoompan=z='1+0.08*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
        run(["-loop", "1", "-i", str(src), "-filter_complex", f"[0:v]{fill},{z}[v]", "-map", "[v]", "-t", f"{seconds:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out)])
        return
    vw, vh = kc.video_size(src)
    aspect = vw / vh if vh else None
    fill = crop_filter(aspect, face)
    pre = max(-offset, 0.0)
    skip = max(offset, 0.0)
    have = (kc.duration(src) - skip) / speed
    pad = max(seconds - pre - have + 0.1, 0)
    vf = (f"setpts=PTS/{speed}," if speed != 1.0 else "") + f"{fill},fps={FPS}"
    if pre > 0:
        vf += f",tpad=start_mode=clone:start_duration={pre:.3f}"
    if pad > 0:
        vf += f",tpad=stop_mode=clone:stop_duration={pad:.3f}"
    run(["-ss", f"{skip:.3f}", "-i", str(src), "-filter_complex", f"[0:v]{vf}[v]", "-map", "[v]", "-t", f"{seconds:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out)])


def grade_filter(gid):
    if not gid or gid == "none":
        return None
    grades = {g["id"]: g for g in load_json(KIT / "kit" / "grades.json")["grades"]}
    if gid not in grades:
        sys.exit(f"--grade {gid}: not in kit/grades.json ({', '.join(grades)})")
    return grades[gid]["ffmpeg"] or None


# ======================= main =======================
def build(a, lines, plan_shots, song_len):
    """plan_shots: [{"t0","t1","src","graphic"}] already decided. Returns nothing; writes a.out."""
    card = 1.2
    end = min(a.end or song_len, song_len)
    if a.board_end:
        end = min(song_len, a.board_end + card)
    t0, t1 = 0.0, end
    if a.test:
        t0, t1 = (float(x) for x in a.test.split("-"))
        t1 = min(t1, end)
    work = Path(tempfile.mkdtemp(prefix="klaudia-edit-"))
    try:
        # which picture each shot shows, and from which second of it
        prev = None
        for sh in plan_shots:
            c = sh["src"]
            if c == "+" and prev:
                path, off, speed = prev[0], prev[1] + (sh["t0"] - prev[2]), prev[3]
            else:
                path, at, speed = parse_src(c)
                sy = sync_info(path) if Path(path).suffix.lower() not in STILL else None
                if sy:                       # a sung take: by the SONG's clock
                    off = sh["t0"] - float(sy["song_start"])
                    chk = sy.get("check") or {}
                    if chk.get("verdict") == "shift":
                        off -= float(chk.get("lag_s") or 0)
                elif at is not None:
                    off = at
                else:
                    off = 0.067 if Path(path).suffix.lower() not in STILL else 0.0  # skip 2 frames: the sharper input still
                prev = (path, off, sh["t0"], speed)
                if not Path(path).exists():
                    sys.exit(f"Missing file for the shot at {sh['t0']:.2f} s: {path}")
            sh.update(path=path, off=off, speed=speed)
            sh["face"] = face_in(path, off + 0.5) if kc.faces(Image.new("L", (8, 8))) is not None else None
            sh["face_out"] = face_out(sh["face"])
        layers = Layers(lines, plan_shots, a, end, card)
        grade = grade_filter(a.grade)

        if a.frames:
            return style_frames(a, plan_shots, layers, grade, work)

        parts, first = [], None
        for i, sh in enumerate(plan_shots):
            s, e = sh["t0"], sh["t1"]
            if e <= t0 or s >= t1:
                continue
            first = s if first is None else first
            p = work / f"shot{i:03d}.mp4"
            make_shot(sh["path"], sh["off"], sh["speed"], e - s, p, sh["face"])
            parts.append(p)
        if t1 > end - card:
            cp = work / "card.png"
            card_png(cp, a.title, a.tag)
            p = work / "card.mp4"
            make_shot(cp, 0, 1.0, card, p)
            parts.append(p)
        lst = work / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        base = work / "base.mp4"
        run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(base)])
        if a.test:
            t0 = first if first is not None else end - card
            t1 = max(t1, t0 + 0.5)
        # ONE overlay track for every word, title, graphic and frame (0.6 stacked 100+ overlays and lost them)
        bounds = layers.boundaries(t0, t1)
        cache, rows = {}, []
        blank = work / "blank.png"
        Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(blank)
        for k, (s, e) in enumerate(zip(bounds, bounds[1:])):
            if e - s < 0.5 / FPS:
                continue
            img = layers.at((s + e) / 2)
            key = img.tobytes() if img.getbbox() else None
            if key is None:
                path = blank
            elif key in cache:
                path = cache[key]
            else:
                path = work / f"layer{k:04d}.png"
                img.save(path, compress_level=1)
                cache[key] = path
            rows.append((path, e - s))
        txt = "".join(f"file '{p}'\nduration {d:.4f}\n" for p, d in rows) + f"file '{rows[-1][0]}'\n"
        (work / "layers.txt").write_text(txt)
        out = Path(a.out) if not a.test else Path(a.out).with_name(f"test-{a.test}.mp4")
        g = (grade + ",") if grade else ""
        fc = (f"[0:v]{g}format=yuv420p[b];[1:v]fps={FPS},format=rgba[t];"
              f"[b][t]overlay=0:0:eof_action=pass:format=auto[v]")
        run(["-i", str(base), "-f", "concat", "-safe", "0", "-i", str(work / "layers.txt"),
             "-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", a.song,
             "-filter_complex", fc, "-map", "[v]", "-map", "2:a",
             "-c:v", "libx264", "-preset", "fast", "-crf", "21", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", f"{t1 - t0:.3f}", "-movflags", "+faststart", str(out)])
        res = {"ok": True, "out": str(out), "seconds": round(t1 - t0, 2), "shots": len(parts),
               "lyric_lines": len(lines), "format": "vertical" if H > W else "horizontal"}
        guessed = [x["text"] for x in lines if x.get("guessed")]
        if guessed:
            res["lines_timed_by_guess"] = guessed
        return res
    finally:
        if a.keep:
            print("work folder:", work, file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)


def face_out(face):
    """Where her face lands in the OUTPUT frame (after the crop), as fractions: (cx, cy, w, h)."""
    if not face:
        return None
    cx, cy, fw, fh, aspect = face
    target = W / H
    if target / aspect > 1.6:                       # whole picture on a blur (vertical in 16:9)
        sw = aspect / target
        return (0.5 + (cx - 0.5) * sw, cy, fw * sw, fh)
    if aspect > target:                             # wider than the frame: cropped at the sides around her face
        vis = target / aspect
        x0 = min(max(cx - vis / 2, 0), 1 - vis)
        return ((cx - x0) / vis, cy, fw / vis, fh)
    vis = aspect / target                           # taller: cropped top and bottom
    y0 = min(max(cy - vis * 0.42, 0), 1 - vis)
    return (cx, (cy - y0) / vis, fw, fh / vis)


def style_frames(a, shots, layers, grade, work):
    """Still pictures of the finished look at the given seconds, side by side, numbered."""
    times = [float(x) for x in a.frames.split(",") if x.strip()]
    layers.final = True
    pics = []
    for k, t in enumerate(times):
        sh = next((s for s in shots if s["t0"] <= t < s["t1"]), shots[-1])
        p = work / f"f{k}.mp4"
        make_shot(sh["path"], sh["off"] + (t - sh["t0"]) * sh["speed"], sh["speed"], 0.2, p, sh["face"])
        png = work / f"f{k}.png"
        run(["-i", str(p), "-vf", (grade + "," if grade else "") + "format=rgb24", "-frames:v", "1", str(png)])
        im = Image.open(png).convert("RGBA")
        im.alpha_composite(layers.at(t))
        pics.append((im.convert("RGB"), t))
    th = 900 if H > W else 480
    tw = int(th * W / H)
    pad = 24
    sheet = Image.new("RGB", (pad + len(pics) * (tw + pad), th + 2 * pad + 70), (14, 14, 16))
    d = ImageDraw.Draw(sheet)
    for k, (im, t) in enumerate(pics):
        im = im.resize((tw, th))
        x = pad + k * (tw + pad)
        sheet.paste(im, (x, pad + 60))
        d.ellipse((x, pad - 6, x + 56, pad + 50), fill=(230, 110, 40))
        d.text((x + 28 - d.textlength(str(k + 1), font=font(44)) / 2, pad - 4), str(k + 1), font=font(44), fill=(255, 255, 255))
        d.text((x + 70, pad), f"{t:.1f} s", font=font(36), fill=CREAM)
    sheet.save(a.out)
    return {"ok": True, "out": a.out, "frames": len(pics)}


def main():
    global FF, W, H, S
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--song")
    ap.add_argument("--board", help="board.json (klaudia_board.py): cuts, pictures, song, title, tag and style")
    ap.add_argument("--words")
    ap.add_argument("--lyrics", dest="lyrics_file", help="the lyric as sent to Suno (with [section] tags)")
    ap.add_argument("--lines")
    ap.add_argument("--clips", nargs="+")
    ap.add_argument("--title", default="KLAUDIA'S NEWS")
    ap.add_argument("--tag", default="INVITE YOURSELF.")
    ap.add_argument("--out", default="klaudia-news.mp4")
    ap.add_argument("--end", type=float)
    ap.add_argument("--test")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--format", choices=["vertical", "horizontal"], default="vertical")
    ap.add_argument("--also", action="store_true", help="also make the other shape (…-16x9.mp4 or …-9x16.mp4)")
    ap.add_argument("--look", choices=["news", "clip", "ad"], default=None)
    ap.add_argument("--lyrics-style", dest="lyrics_style", choices=["classic", "karaoke", "giant", "box", "none"], default=None)
    ap.add_argument("--grade", default=None)
    ap.add_argument("--frames", help="style frames at these seconds (comma-separated) → --out is a .png")
    ap.add_argument("--lines-per-shot", type=int, default=1, help="cut every N lyric lines (music video: 2)")
    ap.add_argument("--cut-sung", action="store_true", help="cut only on sung lines, not on the choir's answers")
    ap.add_argument("--dump-lines", help="write the timed lyric lines (with each word's time) to this JSON and stop")
    ap.add_argument("--every", type=float, help="no lyric timing: cut every N seconds (try the beat: 4 bars)")
    ap.add_argument("--no-lyrics", action="store_true", help="no lyrics on screen (title and end card only)")
    a = ap.parse_args()
    FF = kc.ffmpeg()
    board, base = None, Path(".")
    a.board_end = None
    if a.board:
        board = load_json(a.board)
        base = Path(a.board).resolve().parent
        a.song = rel(base, board["song"])
        a.format = board.get("format", a.format) if a.format == "vertical" else a.format
        a.title = board.get("title", a.title)
        a.tag = board.get("tag", a.tag)
        if board.get("lines") and not (a.lines or a.words):
            a.lines = rel(base, board["lines"])
    style = (board or {}).get("style", {})
    a.look = a.look or style.get("look") or ("news" if "NEWS" in a.title.upper() else "clip")
    a.lyrics = "none" if a.no_lyrics else (a.lyrics_style or style.get("lyrics") or "classic")
    a.grade = a.grade or style.get("grade")
    if not a.song:
        sys.exit("Give --board, or --song and --clips.")

    if a.lines:
        lines = [{"text": x.get("text", x.get("texto", "")), "choir": bool(x.get("choir", x.get("coro"))),
                  "t0": float(x["t0"]), "t1": float(x["t1"]), "part": x.get("part", "verse"), "words": x.get("words") or []}
                 for x in load_json(a.lines) if x.get("t0") is not None and x.get("t1") is not None]
        for x in lines:
            if not x["words"]:
                ws = x["text"].split()
                span = max(x["t1"] - x["t0"], 0.3)
                x["words"] = [{"w": w, "t0": x["t0"] + span * k / len(ws), "t1": x["t0"] + span * (k + 1) / len(ws)}
                              for k, w in enumerate(ws)]
    elif a.words and a.lyrics_file:
        lines = lines_from_words(word_list(load_json(a.words)), lyric_lines(Path(a.lyrics_file).read_text()))
    else:
        lines = None
    if lines is None:
        if a.every:
            lines = []
        elif board:
            lines = [{"text": s["line"], "choir": False, "t0": s["t0"], "t1": s["t1"], "part": "verse",
                      "words": [{"w": w, "t0": s["t0"], "t1": s["t1"]} for w in s["line"].split()]}
                     for s in board["shots"] if s.get("line")]
        else:
            sys.exit("Give --lines, or --words with --lyrics, or --every SECONDS (a song with no timing).")
    if a.dump_lines:
        Path(a.dump_lines).write_text(json.dumps(lines, indent=1, ensure_ascii=False))
        print(json.dumps({"ok": True, "lines": len(lines), "out": a.dump_lines,
                          "guessed": [x["text"] for x in lines if x.get("guessed")]}))
        return

    if not (a.clips or board):
        sys.exit("Give --board, or --song and --clips.")
    song_len = kc.duration(a.song)
    shapes = [a.format] + ([("horizontal" if a.format == "vertical" else "vertical")] if a.also else [])
    results = []
    for k, shape in enumerate(shapes):
        W, H, S = (1080, 1920, 1.0) if shape == "vertical" else (1920, 1080, 0.85)
        plan = plan_shots(a, board, base, lines, song_len)
        if k:
            stem = Path(a.out).stem
            a2 = argparse.Namespace(**vars(a))
            a2.out = str(Path(a.out).with_name(stem + ("-16x9" if shape == "horizontal" else "-9x16") + Path(a.out).suffix))
            results.append(build(a2, lines, plan, song_len))
        else:
            results.append(build(a, lines, plan, song_len))
    print(json.dumps(results[0] if len(results) == 1 else {"ok": all(r["ok"] for r in results), "videos": results}))


def rel(base, x):
    return str(base / x) if x and not str(x).startswith("/") else x


def plan_shots(a, board, base, lines, song_len):
    card = 1.2
    end = min(a.end or song_len, song_len)
    if board:
        shots = []
        for s in board["shots"]:
            src = s.get("clip") or s.get("still")
            if not src:
                sys.exit(f"shot {s['n']} has no photo and no clip yet")
            path, at, _ = parse_src(src)
            sp = f"^{s['speed']}" if s.get("speed") and s.get("clip") else ""
            shots.append({"t0": s["t0"], "t1": s["t1"], "graphic": s.get("graphic"),
                          "src": rel(base, path) + (f"@{at}" if at is not None else "") + sp})
        a.board_end = board["shots"][-1]["t1"]
        return shots
    sung = [ln for ln in lines if not (a.cut_sung and ln["choir"])]
    starts = sorted({0.0, *[round(ln["t0"], 3) for ln in sung[::max(a.lines_per_shot, 1)]
                             if 0.3 < ln["t0"] < end - card - 0.4]}
                    | ({round(k * a.every, 3) for k in range(1, int(end / a.every) + 1)
                        if k * a.every < end - card - 0.4} if a.every and not lines else set()))
    cuts = starts + [end - card]
    return [{"t0": s, "t1": e, "src": a.clips[i % len(a.clips)], "graphic": None} for i, (s, e) in enumerate(zip(cuts, cuts[1:]))]


if __name__ == "__main__":
    main()
