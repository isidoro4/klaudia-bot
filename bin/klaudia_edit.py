#!/usr/bin/env python3
"""KLAUDIA BOT edit: a video from a song, its timed lyrics and clips or stills.
Vertical 9:16 (news, sponsorship) or --format horizontal 16:9 (music video: add --lines-per-shot 2 --cut-sung).

Needs Python 3.9+, Pillow and ffmpeg (ffmpeg on PATH, or `pip install imageio-ffmpeg`).

  python3 klaudia_edit.py --song song.mp3 --words alignment.json --lyrics lyrics.txt \
      --clips c1.mp4 c2.mp4 still3.png ... --title "FOUR VIEWERS" --tag "STREAM YOURSELF." --out news.mp4

Timing, one of:
  --words  the JSON of Suno's lyric alignment (audio-lyrics-alignment): a list of words with start/end seconds,
           or an object holding that list. With --lyrics (the lyrics as sent to Suno) the words are grouped into
           the lyric lines; [section tags] are skipped, lines in (PARENTHESES) count as the choir.
  --lines  a JSON list of {"text", "t0", "t1", "choir"} (already grouped).
One shot per lyric line, cut where the line starts; the clips are used in the order given and repeat if there are
fewer clips than lines. A still gets a slow zoom. Lyrics on screen in big letters (choir in orange), the title for
the first seconds, and an end card with the tag and «fan-made with KLAUDIA BOT · made with AI».
A clip given as path@SECONDS starts there (a sung take: @0.7); "+" in the list keeps playing the previous clip.
Options: --end SECONDS (cut the song there), --test 0-10 (only that stretch, fast), --keep (keep the work folder).
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

W, H, FPS = 1080, 1920, 30
S = 1.0  # text scale
HERE = Path(__file__).resolve().parent
FONT = HERE.parent / "fonts" / "Anton-Regular.ttf"
CREAM, ORANGE, BLACK = (255, 246, 228), (255, 122, 26), (0, 0, 0)
FOOTER = "fan-made with KLAUDIA BOT · made with AI"
STILL = {".png", ".jpg", ".jpeg", ".webp"}


def ffmpeg_bin():
    exe = shutil.which("ffmpeg")
    if exe:
        return exe
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError:
        sys.exit("No ffmpeg: install it, or run `pip install imageio-ffmpeg`.")


FF = None


def run(args):
    r = subprocess.run([FF, "-nostdin", "-hide_banner", "-loglevel", "error", "-y", *args],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg failed:\n" + r.stderr[-2000:])


def duration(path):
    r = subprocess.run([FF, "-nostdin", "-hide_banner", "-i", str(path)], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]) if m else 0.0


# ---------- timing ----------
def norm(w):
    return re.sub(r"[^a-z0-9']", "", w.lower())


def lyric_lines(text):
    out = []
    for raw in text.splitlines():
        s = raw.strip()
        if not s or (s.startswith("[") and s.endswith("]")):
            continue
        choir = s.startswith("(") and s.endswith(")")
        out.append({"text": s.strip("()").strip(), "choir": choir})
    return out


def word_list(data):
    """Suno's alignment: tokens (often pieces of words, with the punctuation, line breaks and the unsung
    choir lines inside them) with start_s/end_s. Returns [(text, start, end)] in order."""
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


def lines_from_words(tokens, lyrics):
    """Find each lyric line in the joined token text. A sung line takes the time of its first and last
    letters; a choir line (not aligned by Suno) fills the gap between the lines around it."""
    text, owner = "", []
    for k, (txt, _, _) in enumerate(tokens):
        text += txt
        owner += [k] * len(txt)
    low = text.lower()
    out, cur = [], 0
    for ln in lyrics:
        target = ln["text"].lower()
        pos = low.find(target, cur)
        if pos < 0:  # tolerate small differences: find the first word
            first = target.split()[0] if target.split() else ""
            pos = low.find(first, cur) if first else -1
            if pos < 0:
                continue
            end = pos + len(first)
        else:
            end = pos + len(target)
        cur = end
        letters = [i for i in range(pos, end) if text[i].isalnum()]
        if not letters:
            continue
        out.append({"text": ln["text"], "choir": ln["choir"],
                    "t0": tokens[owner[letters[0]]][1], "t1": tokens[owner[letters[-1]]][2]})
    # choir lines: between the sung lines around them
    for i, ln in enumerate(out):
        if not ln["choir"]:
            continue
        prev = next((x["t1"] for x in reversed(out[:i]) if not x["choir"]), 0.0)
        nxt = next((x["t0"] for x in out[i + 1:] if not x["choir"]), prev + 1.2)
        ln["t0"], ln["t1"] = prev + 0.05, max(nxt - 0.05, prev + 0.6)
    return out


# ---------- pictures of text ----------
def font(size):
    return ImageFont.truetype(str(FONT), size)


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


def text_png(path, text, size, color, y_center, stroke=6):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = font(size)
    rows = wrap(d, text, f, W - 140)
    lh = int(size * 1.08)
    y = int(y_center - lh * len(rows) / 2)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ds = ImageDraw.Draw(shadow)
    for r in rows:
        x = (W - d.textlength(r, font=f)) / 2
        ds.text((x + 6, y + 8), r, font=f, fill=(0, 0, 0, 170))
        d.text((x, y), r, font=f, fill=color, stroke_width=stroke, stroke_fill=BLACK)
        y += lh
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))
    shadow.alpha_composite(img)
    shadow.save(path)


def card_png(path, title, tag):
    img = Image.new("RGB", (W, H), (12, 12, 14))
    d = ImageDraw.Draw(img)
    y = int(H * 0.36)
    for r in wrap(d, title.upper(), font(150), W - 120):
        d.text(((W - d.textlength(r, font=font(150))) / 2, y), r, font=font(150), fill=CREAM)
        y += 160
    y += 40
    for r in wrap(d, tag.upper(), font(96), W - 120):
        d.text(((W - d.textlength(r, font=font(96))) / 2, y), r, font=font(96), fill=ORANGE)
        y += 104
    f = font(40)
    d.text(((W - d.textlength(FOOTER, font=f)) / 2, H - int(H * 0.1)), FOOTER, font=f, fill=(170, 170, 170))
    img.save(path)


def split_chunks(line, maxwords=4):
    words = line["text"].split()
    if len(words) <= maxwords:
        return [line]
    groups, cur = [], []  # break after . ! ? , first, then every maxwords words
    for w in words:
        cur.append(w)
        if len(cur) >= maxwords or w[-1] in ".!?,":
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    total = sum(len(g) for g in groups)
    out, t = [], line["t0"]
    span = max(line["t1"] - line["t0"], 0.3)
    for g in groups:
        dt = span * len(g) / total
        out.append({**line, "text": " ".join(g), "t0": t, "t1": t + dt})
        t += dt
    return out


# ---------- shots ----------
def make_shot(src, seconds, out):
    """src may end in @SECONDS: start reading the clip there (a sung take opens LEAD seconds before its first word)."""
    skip = 0.067  # skip the first 2 frames: they are the sharper input still
    if "@" in str(src) and str(src).rsplit("@", 1)[1].replace(".", "", 1).isdigit():
        src, at = str(src).rsplit("@", 1)
        skip = max(float(at), skip)
    src = Path(src)
    fill = f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1"
    if src.suffix.lower() in STILL:
        frames = max(int(seconds * FPS), 1)
        z = f"zoompan=z='1+0.08*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s={W}x{H}:fps={FPS}"
        run(["-loop", "1", "-i", str(src), "-vf", f"{fill},{z}", "-t", f"{seconds:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out)])
    else:
        have = duration(src) - skip
        pad = max(seconds - have + 0.1, 0)
        vf = f"{fill},fps={FPS}" + (f",tpad=stop_mode=clone:stop_duration={pad:.3f}" if pad > 0 else "")
        run(["-ss", f"{skip:.3f}", "-i", str(src), "-vf", vf, "-t", f"{seconds:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-an", str(out)])


def main():
    global FF, W, H, S
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--song", required=True)
    ap.add_argument("--words")
    ap.add_argument("--lyrics")
    ap.add_argument("--lines")
    ap.add_argument("--clips", nargs="+", required=True)
    ap.add_argument("--title", default="KLAUDIA'S NEWS")
    ap.add_argument("--tag", default="INVITE YOURSELF.")
    ap.add_argument("--out", default="klaudia-news.mp4")
    ap.add_argument("--end", type=float)
    ap.add_argument("--test")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--format", choices=["vertical", "horizontal"], default="vertical",
                    help="vertical 1080x1920 (news, sponsorship) or horizontal 1920x1080 (music video)")
    ap.add_argument("--lines-per-shot", type=int, default=1, help="cut every N lyric lines (music video: 2)")
    ap.add_argument("--cut-sung", action="store_true", help="cut only on sung lines, not on the choir's answers")
    ap.add_argument("--dump-lines", help="write the timed lyric lines to this JSON and stop (for klaudia_sing.py)")
    ap.add_argument("--every", type=float, help="no lyric timing: cut every N seconds (try the beat: 4 bars)")
    ap.add_argument("--no-lyrics", action="store_true", help="no lyrics on screen (title and end card only)")
    a = ap.parse_args()
    if a.format == "horizontal":
        W, H, S = 1920, 1080, 0.85
    FF = ffmpeg_bin()

    if a.lines:
        lines = [{"text": x.get("text", x.get("texto", "")), "choir": bool(x.get("choir", x.get("coro"))),
                  "t0": float(x["t0"]), "t1": float(x["t1"])} for x in json.loads(Path(a.lines).read_text())
                 if x.get("t0") is not None and x.get("t1") is not None]
    elif a.words and a.lyrics:
        lines = lines_from_words(word_list(json.loads(Path(a.words).read_text())),
                                 lyric_lines(Path(a.lyrics).read_text()))
    elif a.every:
        lines = []
    else:
        sys.exit("Give --lines, or --words with --lyrics, or --every SECONDS (a song with no timing).")
    if not lines and not a.every:
        sys.exit("No timed lyric lines.")
    if a.dump_lines:
        Path(a.dump_lines).write_text(json.dumps(lines, indent=1))
        print(json.dumps({"ok": True, "lines": len(lines), "out": a.dump_lines}))
        return

    song_len = duration(a.song)
    end = min(a.end or song_len, song_len)
    card = 1.2
    t0, t1 = 0.0, end
    if a.test:
        t0, t1 = (float(x) for x in a.test.split("-"))

    # cuts: where each line starts (the first shot from 0); the end card at end - card
    if a.every:
        lines = lines or []
    sung = [ln for ln in lines if not (a.cut_sung and ln["choir"])]
    starts = sorted({0.0, *[round(ln["t0"], 3) for ln in sung[::max(a.lines_per_shot, 1)]
                             if 0.3 < ln["t0"] < end - card - 0.4]}
                    | ({round(k * a.every, 3) for k in range(1, int(end / a.every) + 1)
                        if k * a.every < end - card - 0.4} if a.every and not lines else set()))
    cuts = starts + [end - card]
    work = Path(tempfile.mkdtemp(prefix="klaudia-edit-"))
    try:
        # which clip each shot shows; "+" = keep playing the previous clip (a sung take over two lines)
        plan, prev = [], None
        for i, (s, e) in enumerate(zip(cuts, cuts[1:])):
            c = a.clips[i % len(a.clips)]
            if c == "+" and prev:
                src, at = prev
                c = f"{src}@{at:.3f}"
            src, at = (c.rsplit("@", 1) if "@" in c else (c, "0"))
            at = float(at) if at.replace(".", "", 1).isdigit() else 0.0
            prev = (src, at + (e - s))
            plan.append(c)
        parts, first = [], None
        for i, (s, e) in enumerate(zip(cuts, cuts[1:])):
            if e <= t0 or s >= t1:
                continue
            first = s if first is None else first
            p = work / f"shot{i:03d}.mp4"
            make_shot(plan[i], e - s, p)
            parts.append(p)
        if t1 > end - card:
            cp = work / "card.png"
            card_png(cp, a.title, a.tag)
            p = work / "card.mp4"
            make_shot(cp, card, p)
            parts.append(p)
        lst = work / "list.txt"
        lst.write_text("".join(f"file '{p}'\n" for p in parts))
        base = work / "base.mp4"
        run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(base)])
        if a.test:  # the test starts where its first shot starts
            t0 = first if first is not None else end - card
            t1 = max(t1, t0 + 0.5)
        off = t0

        # overlays: the title, then every lyric chunk
        overlays = []
        tp = work / "title.png"
        text_png(tp, a.title.upper(), int(120 * S), CREAM, int(H * 0.156), stroke=8)
        overlays.append((tp, 0.4, min(4.0, end - card)))
        for k, ln in enumerate(c for line in lines for c in split_chunks(line)):
            if ln["t0"] >= end - card or a.no_lyrics:
                continue
            p = work / f"txt{k:03d}.png"
            if ln["choir"]:
                text_png(p, ln["text"].upper(), int(140 * S), ORANGE, int(H * 0.615), stroke=8)
            else:
                text_png(p, ln["text"].upper(), int(96 * S), CREAM, int(H * 0.8))
            overlays.append((p, ln["t0"] - 0.15, min(ln["t1"] + 0.15, end - card)))
        overlays = [(p, s - off, e - off) for p, s, e in overlays if e > t0 and s < t1]

        inputs = ["-i", str(base)]
        chain, last = [], "0:v"
        for j, (p, s, e) in enumerate(overlays, start=1):
            inputs += ["-i", str(p)]
            chain.append(f"[{last}][{j}:v]overlay=0:0:enable='between(t,{max(s, 0):.3f},{e:.3f})'[v{j}]")
            last = f"v{j}"
        fc = ";".join(chain) if chain else "[0:v]null[v0]"
        last = last if chain else "v0"
        inputs += ["-ss", f"{t0:.3f}", "-t", f"{t1 - t0:.3f}", "-i", a.song]
        out = Path(a.out) if not a.test else Path(a.out).with_name(f"test-{a.test}.mp4")
        run([*inputs, "-filter_complex", fc, "-map", f"[{last}]", "-map", f"{len(overlays) + 1}:a",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
             "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", "-movflags", "+faststart", str(out)])
        print(json.dumps({"ok": True, "out": str(out), "seconds": round(t1 - t0, 2),
                          "shots": len(parts), "lyric_lines": len(lines)}))
    finally:
        if a.keep:
            print("work folder:", work, file=sys.stderr)
        else:
            shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
