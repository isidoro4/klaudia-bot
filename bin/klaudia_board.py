#!/usr/bin/env python3
"""KLAUDIA BOT · the board: the whole video as numbered shots, before anything is paid.

board.json (one video):
  {"song": "song/song.mp3", "lines": "song/lines.json", "format": "vertical" | "horizontal",
   "title": "FOUR VIEWERS", "tag": "STREAM YOURSELF.",
   "style": {"look": "news" | "clip" | "ad", "lyrics": "classic" | "karaoke" | "giant" | "box", "grade": "film"},
   "shots": [{"n": 1, "t0": 0.0, "t1": 2.4, "kind": "sing" | "dance" | "move",
              "line": "Hi! This is Klaudia's News.", "what": "close-up, she sings the hook to camera",
              "graphic": {"type": "counter", …} | null, "still": "photos/01.png", "clip": "clips/01-sung.mp4" | null}, …]}
  t0/t1 = seconds of the SONG. "clip" empty = the shot shows its photo (free preview).

  plan     python3 klaudia_board.py plan board.json --lines song/lines.json --template news
              news  = Klaudia's News: SEVEN fixed shots (hook sung · fact · dance · fact · chorus sung · dance · punchline sung)
              recipe = one shot per line, the gaps danced in shots of at most --max s on the beat (--beat 60/BPM)
  sheet    python3 klaudia_board.py sheet board.json --out board.png      the picture of the board (send it)
  frames   python3 klaudia_board.py frames board.json --out frames.png    3–6 style frames: the finished look, free
  windows  python3 klaudia_board.py windows board.json --vocals song/vocals.mp3   the vocal window of every sung shot (free)
  takes    python3 klaudia_board.py takes board.json [--yes]   ALL sung takes at once, in parallel: the price first
              (no --yes), then, after the person's yes, every take + its lip-sync check, written into the board
  split    python3 klaudia_board.py split board.json 5 --at 21.3          shot 5 becomes two shots (5 and 6)
  check    python3 klaudia_board.py check board.json                      what is missing, the price left, sync warnings
The edit reads the same file: klaudia_edit.py --board board.json (free preview with photos, or the final with clips).
"""
import argparse
import json
import math
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klaudia_common as kc  # noqa: E402

ICON = {"sing": "SINGS", "dance": "DANCES", "move": "MOVES", "text": "TEXT"}
COL = {"sing": (255, 122, 26), "dance": (90, 200, 255), "move": (180, 180, 180), "text": (255, 230, 120)}
SING_PRICE = 0.05          # HeyGen on OpenRouter, $ per second of window
MAX_SING = 5.0             # longer sung takes drift and HeyGen may refuse them (402 weight_exceeds_budget)


def font(s):
    return kc.font(s)


def load(p):
    return json.loads(Path(p).read_text())


def save(p, b):
    Path(p).write_text(json.dumps(b, indent=1, ensure_ascii=False))


def fmt(t):
    return f"{int(t // 60)}:{t % 60:05.2f}"


def clip_text(d, text, f, maxw):
    """Shorten with … until it fits the cell."""
    if d.textlength(text, font=f) <= maxw:
        return text
    while text and d.textlength(text + "…", font=f) > maxw:
        text = text[:-1]
    return text.rstrip() + "…"


def gdesc(g):
    if not g:
        return ""
    t = g.get("type", "")
    main = g.get("text") or g.get("label") or g.get("title") or g.get("time") or ""
    return f"[{t.upper()}] {main}"


# ---------------- sheet ----------------
def cmd_sheet(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    shots = b["shots"]
    vertical = b.get("format", "vertical") == "vertical"
    tw, th = (220, 390) if vertical else (360, 203)
    cols = min(6 if vertical else 4, max(1, len(shots)))
    pad, cap = 16, 150
    rows = math.ceil(len(shots) / cols)
    W = max(cols * (tw + pad) + pad, 900)
    H = 150 + rows * (th + cap + pad) + pad
    sheet = Image.new("RGB", (W, H), (14, 14, 16))
    d = ImageDraw.Draw(sheet)
    st = b.get("style", {})
    d.text((pad, 14), f"{b.get('title', 'KLAUDIA')} · {len(shots)} shots · {fmt(shots[-1]['t1'])}", font=font(40), fill=(240, 234, 222))
    d.text((pad, 66), f"look {st.get('look', '-')} · words {st.get('lyrics', 'classic')} · colour {st.get('grade', 'none')}"
           "   ·   tell me: \"3: she dances\" · \"5: shorter\" · \"7: out\"", font=font(26), fill=(150, 150, 150))
    sung_cost = 0
    for i, s in enumerate(shots):
        x = pad + (i % cols) * (tw + pad)
        y = 120 + (i // cols) * (th + cap + pad)
        src = s.get("still")
        if src and (base / src).exists():
            img = Image.open(base / src).convert("RGB")
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
        if k == "sing" and not s.get("clip"):
            win = base / s["window"] if s.get("window") else None
            c = round(SING_PRICE * (kc.duration(win) if win and win.exists() else min(s["t1"] - s["t0"] + 0.7, MAX_SING + 0.3)), 2)
            sung_cost += c
            d.rectangle((x, y + th - 40, x + tw, y + th), fill=(255, 122, 26))
            d.text((x + 10, y + th - 38), f"SUNG TAKE ≈ ${c:.2f}", font=font(26), fill=(0, 0, 0))
        ty = y + th + 6
        d.text((x, ty), f"{fmt(s['t0'])}  {s['t1'] - s['t0']:.1f}s  {ICON.get(k, k).upper()}", font=font(22),
               fill=COL.get(k, (200, 200, 200)))
        line = (s.get("line") or "")
        d.text((x, ty + 30), clip_text(d, f"«{line}»" if line else "(music)", font(22), tw), font=font(22), fill=(235, 230, 220))
        d.text((x, ty + 60), clip_text(d, s.get("what") or "", font(18), tw), font=font(18), fill=(150, 150, 150))
        if s.get("graphic"):
            d.text((x, ty + 88), clip_text(d, gdesc(s["graphic"]), font(20), tw), font=font(20), fill=(255, 190, 120))
        warn = (s.get("sync") or {}).get("say") if (s.get("sync") or {}).get("verdict") not in (None, "good") else None
        if warn:
            d.text((x, ty + 116), "LIPS: " + (s["sync"]["verdict"]).upper(), font=font(20), fill=(255, 90, 90))
    if sung_cost:
        d.text((W - 380, 20), f"sung takes ≈ ${sung_cost:.2f}", font=font(34), fill=(255, 122, 26))
    sheet.save(a.out)
    print(json.dumps({"ok": True, "out": a.out, "shots": len(shots), "sung_takes_usd": round(sung_cost, 2)}))


# ---------------- plan ----------------
def _join(lines, t0, t1, choir=False):
    return " ".join(l["text"] for l in lines if (choir or not l.get("choir")) and l["t0"] < t1 - 0.05 and l["t1"] > t0 + 0.05)


def _cut_near(lines, target, lo, hi):
    """The start of a sung line closest to `target`, strictly inside (lo, hi): shots never cut a word."""
    cands = [l["t0"] for l in lines if not l.get("choir") and lo + 0.8 < l["t0"] < hi - 0.8]
    return min(cands, key=lambda c: abs(c - target)) if cands else round((lo + hi) / 2, 3)


def plan_news(lines, end, template):
    """Klaudia's News, FIXED shape: seven shots on the four parts of the lyric template."""
    parts = {}
    for l in lines:
        p = l.get("part", "verse")
        p = {"hook": "intro", "pre": "verse", "bridge": "verse", "end": "outro"}.get(p, p)
        if p not in ("intro", "verse", "chorus", "outro"):
            p = "verse"
        parts.setdefault(p, []).append(l)
    sung = [l for l in lines if not l.get("choir")]
    if not sung:
        sys.exit("No sung lines with times.")
    start = lambda p, dflt: min(l["t0"] for l in parts[p]) if parts.get(p) else dflt
    v0 = start("verse", sung[0]["t1"] + 0.5)
    c0 = start("chorus", (v0 + end) * 0.6)
    o0 = start("outro", max(c0 + 4, end - 4))
    v0, c0, o0 = sorted((v0, c0, o0))
    v1 = _cut_near(lines, v0 + (c0 - v0) / 3, v0, c0)
    v2 = _cut_near(lines, v0 + 2 * (c0 - v0) / 3, v1, c0)
    c1 = _sung_end(lines, c0, o0)
    spans = [(0.0, v0), (v0, v1), (v1, v2), (v2, c0), (c0, c1), (c1, o0), (o0, end)]
    spans = [(round(s, 3), round(e, 3)) for s, e in spans if e - s > 0.3]
    shots = []
    for i, (s, e) in enumerate(spans):
        t = template[min(i, len(template) - 1)]
        for k, (a, b) in enumerate(_pieces(lines, s, e, t["kind"])):
            kind = t["kind"] if k == 0 else ("move" if t["kind"] in ("sing", "dance") and k % 2 else "dance")
            shots.append({"t0": a, "t1": b, "kind": kind, "line": _join(lines, a, b),
                          "what": t["what"] if k == 0 else ("she acts the line, medium" if kind == "move" else "wide, she dances on the beat"),
                          "graphic": t.get("graphic") if k == 0 else None, "still": None, "clip": None})
    for n, x in enumerate(shots, 1):
        x["n"] = n
    return [{"n": x["n"], **{k: v for k, v in x.items() if k != "n"}} for x in shots]


def _pieces(lines, s, e, kind, longest=6.0):
    """A part longer than 6 s becomes several shots, cut where a line starts. A sung one keeps only what fits in
    MAX_SING seconds of singing; the rest becomes move/dance shots."""
    if e - s <= longest:
        return [(s, e)]
    out = []
    if kind == "sing":
        cut = _sung_end(lines, s, e)
        cut = next((l["t0"] for l in lines if not l.get("choir") and cut - 0.3 <= l["t0"] < e - 0.8), cut)
        out.append((s, round(cut, 3)))
        s = cut
    while e - s > longest:
        target = s + min(4.0, (e - s) / 2)
        c = _cut_near(lines, target, s, e)
        if not (s + 1.0 < c < e - 1.0):
            c = round(target, 3)
        out.append((round(s, 3), round(c, 3)))
        s = c
    out.append((round(s, 3), round(e, 3)))
    return out


def _sung_end(lines, c0, o0):
    """The sung chorus shot ends after the chorus lines that fit in MAX_SING seconds, at a line end."""
    best = None
    for l in lines:
        if not l.get("choir") and c0 <= l["t0"] < o0 and l["t1"] - c0 <= MAX_SING - 0.6:
            best = l["t1"] + 0.15
    return min(best or c0 + MAX_SING - 1, o0 - 0.5)


def plan_recipe(lines, end, beat, mx, old):
    sung = [l for l in lines if not l.get("choir")]
    cuts = [0.0]
    for l in sung:
        if l["t0"] > cuts[-1] + 0.3:
            cuts.append(round(l["t0"], 3))
    cuts.append(end)
    spans = []
    for s0, s1 in zip(cuts, cuts[1:]):
        n = max(1, math.ceil((s1 - s0) / mx))
        step = (s1 - s0) / n
        if beat:
            step = max(beat, round(step / beat) * beat)
        t = s0
        while t < s1 - 0.05:
            spans.append((round(t, 3), round(min(s1, t + step), 3)))
            t += step
    merged = []
    for sp in spans:
        if merged and (sp[1] - sp[0] < 0.5 or merged[-1][1] - merged[-1][0] < 0.5):
            merged[-1] = (merged[-1][0], sp[1])
        else:
            merged.append(sp)
    sung_of = [next((l for l in sung if l["t0"] < t1 and l["t1"] > t0), None) for (t0, t1) in merged]
    with_voice = [i for i, l in enumerate(sung_of) if l]
    hook, last = (with_voice[0], with_voice[-1]) if with_voice else (-1, -1)
    shots = []
    for i, (t0, t1) in enumerate(merged, 1):
        prev = old.get(i, {})
        default = "sing" if (i - 1) in (hook, last) else ("move" if sung_of[i - 1] else "dance")
        shots.append({"n": i, "t0": t0, "t1": t1, "kind": prev.get("kind", default),
                      "line": _join(sung, t0, t1), "what": prev.get("what", ""), "graphic": prev.get("graphic"),
                      "still": prev.get("still"), "clip": prev.get("clip")})
    return shots


def cmd_plan(a):
    b = load(a.board) if Path(a.board).exists() else {}
    lines = load(a.lines)
    b.setdefault("lines", a.lines)
    end = b.get("end") or (max(l["t1"] for l in lines) + 0.4 if lines else 30)
    old = {s["n"]: s for s in b.get("shots", [])}
    if a.template == "news":
        tpl = load(HERE.parent / "kit" / "news-board.json")["shots"]
        shots = plan_news(lines, end, tpl)
        for s in shots:                       # keep what the person already chose, by number
            for k in ("still", "clip", "what", "graphic", "kind"):
                if old.get(s["n"], {}).get(k):
                    s[k] = old[s["n"]][k]
        b.setdefault("style", {"look": "news", "lyrics": "classic", "grade": "film"})
    else:
        shots = plan_recipe(lines, end, a.beat, a.max, old)
    b["shots"] = shots
    save(a.board, b)
    long_sung = [s["n"] for s in shots if s["kind"] == "sing" and s["t1"] - s["t0"] > MAX_SING + 1.5]
    print(json.dumps({"ok": True, "shots": len(shots), "board": a.board,
                      "note": (f"sung shots {long_sung} are long: only the first {MAX_SING:.0f} s will sing "
                               "(split them: klaudia_board.py split)") if long_sung else ""}))


# ---------------- frames (style frames) ----------------
def cmd_frames(a):
    b = load(a.board)
    shots = b["shots"]
    pick = [s for s in shots if s.get("graphic")][:3] + [s for s in shots if s.get("kind") == "sing"][:2]
    pick = sorted({s["n"]: s for s in (pick or shots[: a.n])}.values(), key=lambda s: s["t0"])[: a.n]
    times = []
    for s in pick:
        words = [l for l in load(Path(a.board).resolve().parent / b["lines"]) if l["t0"] >= s["t0"] and l["t1"] <= s["t1"] + 0.3] if b.get("lines") else []
        t = (words[0]["t0"] + min(words[0]["t1"], words[0]["t0"] + 0.6)) / 2 if words else (s["t0"] + s["t1"]) / 2
        times.append(round(max(t, s["t0"] + 0.4), 2))
    cmd = [sys.executable, str(HERE / "klaudia_edit.py"), "--board", a.board, "--frames", ",".join(map(str, times)), "--out", a.out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.returncode == 0 else json.dumps({"ok": False, "why": r.stderr[-600:]}))


# ---------------- windows and takes ----------------
def _sung_words(lines, s):
    ws = [l for l in lines if not l.get("choir") and l["t0"] >= s["t0"] - 0.05 and l["t0"] < s["t1"] - 0.2]
    if not ws:
        return None
    t0 = ws[0]["t0"]
    t1 = min(max(l["t1"] for l in ws), s["t1"] + 0.3)
    keep = [l for l in ws if l["t1"] <= t0 + MAX_SING - 0.6] or ws[:1]
    t1 = min(t1, max(l["t1"] for l in keep))
    return t0, t1, " ".join(l["text"] for l in keep)


def cmd_windows(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    lines = load(base / b["lines"])
    out = []
    for s in b["shots"]:
        if s.get("kind") != "sing" or s.get("clip"):
            continue
        w = _sung_words(lines, s)
        if not w:
            out.append({"n": s["n"], "skip": "no sung words in this shot"})
            continue
        t0, t1, words = w
        dest = base / "sing" / f"{s['n']:02d}.wav"
        r = subprocess.run([sys.executable, str(HERE / "klaudia_sing.py"), "window", "--vocals", str(base / a.vocals),
                            "--from", str(t0), "--to", str(t1), "--words", words, "--out", str(dest)],
                           capture_output=True, text=True)
        info = json.loads(r.stdout or r.stderr.strip().splitlines()[-1] or "{}") if (r.stdout or r.stderr) else {}
        if r.returncode == 0:
            s["window"] = str(dest.relative_to(base))
        out.append({"n": s["n"], **{k: info.get(k) for k in ("seconds", "song_start", "say") if k in info}})
    save(a.board, b)
    print(json.dumps({"ok": True, "windows": out}))


def cmd_takes(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    todo = [s for s in b["shots"] if s.get("kind") == "sing" and not s.get("clip") and s.get("window")]
    if not todo:
        print(json.dumps({"ok": False, "say": "No sung shot waiting: run `windows` first (and every sung shot needs its still)."}))
        return
    missing = [s["n"] for s in todo if not s.get("still")]
    if missing:
        sys.exit(json.dumps({"ok": False, "say": f"Shots {missing} have no still yet."}))
    fmt_ = b.get("format", "vertical")
    price = round(sum(SING_PRICE * kc.duration(base / s["window"]) for s in todo), 2)
    if not a.yes:
        print(json.dumps({"ok": True, "dry_run": True, "takes": [s["n"] for s in todo], "usd": price,
                          "say": f"{len(todo)} sung takes ≈ ${price:.2f} on your OpenRouter. Go?"}))
        return
    kc.need(price * 1.2)

    def one(s):
        out = base / "clips" / f"{s['n']:02d}-sung.mp4"
        r = subprocess.run([sys.executable, str(HERE / "klaudia_sing.py"), "sing", "--still", str(base / s["still"]),
                            "--audio", str(base / s["window"]), "--format", fmt_, "--out", str(out), "--yes"],
                           capture_output=True, text=True)
        last = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["{}"])[-1]
        try:
            res = json.loads(last)
        except ValueError:
            res = {"ok": False, "why": last[-300:]}
        if res.get("ok"):
            chk = subprocess.run([sys.executable, str(HERE / "klaudia_sync.py"), "check", str(out), "--short"],
                                 capture_output=True, text=True)
            try:
                res["sync"] = json.loads(chk.stdout.strip().splitlines()[-1])
            except (ValueError, IndexError):
                res["sync"] = {"verdict": "unknown"}
        return s["n"], out, res

    with ThreadPoolExecutor(max_workers=4) as ex:
        results = list(ex.map(one, todo))
    spent, report = 0.0, []
    for n, out, res in results:
        s = next(x for x in b["shots"] if x["n"] == n)
        if res.get("ok"):
            s["clip"] = str(out.relative_to(base))
            s["sync"] = {k: res["sync"].get(k) for k in ("verdict", "synced_pct", "good_until", "lag_s", "say")}
            spent += float(res.get("cost") or 0)
            if s["sync"].get("verdict") == "drift" and s["sync"].get("good_until"):
                s["sync"]["cut_at"] = round(s["t0"] + float(s["sync"]["good_until"]), 2)
        report.append({"n": n, "ok": bool(res.get("ok")), "cost": res.get("cost"),
                       "lips": (res.get("sync") or {}).get("verdict"), "say": (res.get("sync") or {}).get("say") or res.get("say") or res.get("why")})
    save(a.board, b)
    print(json.dumps({"ok": True, "spent_usd": round(spent, 2), "takes": report}))


# ---------------- split / check ----------------
def cmd_split(a):
    b = load(a.board)
    shots = b["shots"]
    i = next((k for k, s in enumerate(shots) if s["n"] == a.n), None)
    if i is None or not (shots[i]["t0"] + 0.3 < a.at < shots[i]["t1"] - 0.3):
        sys.exit("That shot does not contain that second (keep 0.3 s on each side).")
    s = shots[i]
    new = {**s, "t0": a.at, "kind": a.kind or ("dance" if s.get("kind") == "sing" else s.get("kind")),
           "clip": s.get("clip") if a.keep_clip else None, "graphic": None, "what": a.what or s.get("what", "")}
    new.pop("sync", None)
    new.pop("window", None)
    s["t1"] = a.at
    shots.insert(i + 1, new)
    for k, x in enumerate(shots, 1):
        x["n"] = k
    if b.get("lines"):
        lines = load(Path(a.board).resolve().parent / b["lines"])
        for x in shots:
            x["line"] = _join(lines, x["t0"], x["t1"])
    save(a.board, b)
    print(json.dumps({"ok": True, "shots": len(shots), "new": a.n + 1}))


def cmd_check(a):
    b = load(a.board)
    base = Path(a.board).resolve().parent
    shots = b["shots"]
    miss_photo = [s["n"] for s in shots if not s.get("still") or not (base / s["still"]).exists()]
    to_make = [s for s in shots if not s.get("clip")]
    sing_left = [s for s in to_make if s.get("kind") == "sing"]
    cost = round(sum(SING_PRICE * min(s["t1"] - s["t0"] + 0.7, MAX_SING + 0.3) for s in sing_left), 2)
    warns = []
    for s in shots:
        sy = s.get("sync") or {}
        if sy.get("verdict") in ("drift", "bad"):
            warns.append(f"shot {s['n']}: {sy.get('say')}" + (f" → klaudia_board.py split board.json {s['n']} --at {sy['cut_at']}" if sy.get("cut_at") else ""))
        if s.get("kind") == "sing" and s["t1"] - s["t0"] > MAX_SING + 1.5 and not s.get("clip"):
            warns.append(f"shot {s['n']}: {s['t1'] - s['t0']:.1f} s sung is long; only {MAX_SING:.0f} s will sing")
    gaps = [(x["n"], y["n"]) for x, y in zip(shots, shots[1:]) if abs(x["t1"] - y["t0"]) > 0.02]
    print(json.dumps({"shots": len(shots), "missing_photos": miss_photo, "clips_to_make": [s["n"] for s in to_make],
                      "sung_takes_left": [s["n"] for s in sing_left], "sung_takes_usd": cost, "warnings": warns,
                      "gaps_between": gaps, "note": "dance/move clips are Grok Imagine, inside the person's plan"}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("sheet"); s.add_argument("board"); s.add_argument("--out", default="board.png")
    p = sub.add_parser("plan"); p.add_argument("board"); p.add_argument("--lines", required=True)
    p.add_argument("--template", choices=["news", "recipe"], default="recipe")
    p.add_argument("--beat", type=float, default=0.0); p.add_argument("--max", type=float, default=2.0)
    f = sub.add_parser("frames"); f.add_argument("board"); f.add_argument("--out", default="frames.png"); f.add_argument("--n", type=int, default=4)
    w = sub.add_parser("windows"); w.add_argument("board"); w.add_argument("--vocals", required=True)
    t = sub.add_parser("takes"); t.add_argument("board"); t.add_argument("--yes", action="store_true")
    sp = sub.add_parser("split"); sp.add_argument("board"); sp.add_argument("n", type=int); sp.add_argument("--at", type=float, required=True)
    sp.add_argument("--kind", choices=["sing", "dance", "move"]); sp.add_argument("--what"); sp.add_argument("--keep-clip", action="store_true")
    c = sub.add_parser("check"); c.add_argument("board")
    a = ap.parse_args()
    {"sheet": cmd_sheet, "plan": cmd_plan, "frames": cmd_frames, "windows": cmd_windows, "takes": cmd_takes,
     "split": cmd_split, "check": cmd_check}[a.cmd](a)


if __name__ == "__main__":
    main()
