#!/usr/bin/env python3
"""KLAUDIA BOT · stills of Klaudia (Nano Banana Pro on OpenRouter) that always look like her, and their review.

THE RULE: every still of Klaudia goes WITH her face sheet as image 1. Never a still of her "from text only" to get
past a filter: if a model refuses her, change the model (or the shot), never drop her reference.

  still    python3 klaudia_photo.py still --shot "close-up, she sings the hook to camera" --place "a TV studio" \
               [--look news | --role anchor | --outfit-ref refs/outfit.jpg] [--body curvy] [--style-ref photos/01.png] \
               [--sing] [--guest guests/claudia.json] --format vertical --out photos/01.png [--yes]
           The prompt is BUILT here, the same way every time: "References: image 1 is her face sheet (who she is) ·
           image 2 is her outfit (the clothes only) · image 3 is the style (light and colour only)", then her identity
           text word for word (kit/klaudia.json), body, clothes, the shot, the place, the photo ending.
           Saves photos/01.png at exactly 720×1280 (or 1280×720: what Grok Imagine wants as a first frame) and the
           big one as photos/01.full.png. Then reviews it (below). Without --yes: prints the prompt and the price.
  review   python3 klaudia_photo.py review photos/01.png [--sing] [--ai --yes]
           Free checks: the size, ONE face, the face big enough when she sings. With --ai (about $0.003, inside the
           batch's yes): a vision model answers the fixed list in kit/review.json (one woman, her face, her fringe and
           streak, no letters, the framing asked, mouth visible when she sings…). Writes photos/01.review.json and
           photos/01.compare.jpg (her face sheet beside the still): LOOK at it before showing the still.
  outfit   python3 klaudia_photo.py outfit photos/03.full.png --out refs/outfit.jpg
           Crops the clothes WITHOUT the face (from the chin down) from an approved full-body still: image 2 for the
           rest of the video (a full-body photo as a reference made every close-up come out wide).
  sheet    → klaudia_sheet.py (numbered sheets to choose from).
Key: OPENROUTER_API_KEY in the environment. Never printed.
"""
import argparse
import base64
import json
import sys
import urllib.error
from pathlib import Path

from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klaudia_common as kc  # noqa: E402

KIT = HERE.parent
MODEL = "google/gemini-3-pro-image-preview"
REVIEW_MODEL = "google/gemini-3.6-flash"
USUAL, REVIEW_USD = 0.14, 0.003
BASE = {"vertical": (720, 1280), "horizontal": (1280, 720), "square": (1024, 1024)}


def kit(name):
    return json.loads((KIT / "kit" / name).read_text())


def pick(items, key):
    for it in items:
        if it["id"] == key:
            return it
    sys.exit(f"'{key}' is not in the menu ({', '.join(i['id'] for i in items)})")


def build(a):
    """→ (prompt, [ref paths in order])."""
    k = kit("klaudia.json")
    refs, roles = [], []

    def add(path, role):
        refs.append(str(path))
        roles.append(f"image {len(refs)} is {role}")

    if not a.no_klaudia:
        add(KIT / k["face_sheet"], k["ref_roles"]["face_sheet"])
    outfit_text = ""
    if a.outfit_ref:
        add(a.outfit_ref, k["ref_roles"]["outfit"])
    if a.role:
        outfit_text = pick(kit("roles.json")["roles"], a.role)["text"]
    elif a.look:
        look = pick(kit("looks.json")["looks"], a.look)
        outfit_text = look["text"]
        if not a.outfit_ref and look.get("ref") and not a.no_klaudia:
            add(KIT / look["ref"], k["ref_roles"]["outfit"])
    elif a.outfit:
        outfit_text = a.outfit
    if a.style_ref:
        add(a.style_ref, k["ref_roles"]["style"])
    guest_text = ""
    if a.guest:
        g = json.loads(Path(a.guest).read_text())
        gsheet = Path(a.guest).parent / g["face_sheet"] if not str(g["face_sheet"]).startswith("/") else Path(g["face_sheet"])
        add(gsheet, f"{g['name']}'s face sheet (who SHE/HE is: a different person from Klaudia; copy that face and hair exactly)")
        guest_text = (f" With her: {g['name']}, {g['identity']} {g.get('outfit', '')} The two never look alike: "
                      f"Klaudia has the very long black hair with one orange streak; {g['name']} has {g.get('tell', 'her own hair')}.")
    for extra in a.extra or []:
        p, _, role = extra.partition("=")
        add(p, role or "a reference for the place or the props only")
    if not a.no_klaudia:
        add(KIT / k["face_close"], k["ref_roles"]["face_close"])
    body = pick(kit("bodies.json")["bodies"], a.body)["text"] if a.body else ""
    parts = []
    if refs:
        parts.append("References: " + "; ".join(roles) + ".")
    if not a.no_klaudia:
        parts.append(k["identity"])
        if body:
            parts.append(body)
        if outfit_text:
            parts.append(outfit_text)
    parts.append(a.shot.rstrip(".") + ".")
    if guest_text:
        parts.append(guest_text.strip())
    if a.place:
        parts.append(f"The place: {a.place.rstrip('.')}.")
    if a.sing and not a.no_klaudia:
        parts.append(k["sing_still"])
    elif not a.no_klaudia:
        parts.append("Expression: deadpan, eyes open.")
    parts.append(k["photo_end"])
    return " ".join(parts), refs


def part(path):
    return {"type": "image_url", "image_url": {"url": kc.data_url(path, 2048)}}


def base_crop(full, fmt, out):
    """The exact size Grok Imagine wants (0.6 sent 2K stills and got 704-px clips back), centred on her face."""
    im = Image.open(full).convert("RGB")
    tw, th = BASE[fmt]
    r = max(tw / im.width, th / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    f = kc.faces(im)
    cx = f[0][0] + f[0][2] / 2 if f else im.width / 2
    cy = f[0][1] + f[0][3] / 2 if f else im.height * 0.42
    x = int(min(max(cx - tw / 2, 0), im.width - tw))
    y = int(min(max(cy - th * 0.4, 0), im.height - th))
    im.crop((x, y, x + tw, y + th)).save(out)


def cmd_still(a):
    prompt, refs = build(a)
    est = USUAL + (REVIEW_USD if a.ai else 0)
    ratio = {"vertical": "9:16", "horizontal": "16:9", "square": "1:1"}[a.format]
    if not a.yes:
        print(json.dumps({"dry_run": True, "model": MODEL, "usual_usd": round(est, 3), "refs": refs, "prompt": prompt}))
        return
    kc.need(est * 1.5)
    body = {"model": MODEL, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] + [part(r) for r in refs]}],
            "image_config": {"aspect_ratio": ratio, "image_size": "2K"}}
    try:
        r = kc.or_call("POST", "/chat/completions", body)
    except urllib.error.HTTPError as e:
        sys.exit(json.dumps({"ok": False, "refused": e.code, "why": e.read().decode(errors="replace")[:400],
                             "say": "Refused. Never drop her reference to get through: change the shot or the place."}))
    if not r.get("choices"):
        sys.exit(json.dumps({"ok": False, "error": r.get("error") or r}, ensure_ascii=False)[:600])
    imgs = r["choices"][0]["message"].get("images") or []
    cost = float((r.get("usage") or {}).get("cost") or USUAL)
    if not imgs:
        sys.exit(json.dumps({"ok": False, "why": "no image came back (often a content refusal)", "cost": cost}))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    full = out.with_suffix(".full.png")
    full.write_bytes(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))
    base_crop(full, a.format, out)
    out.with_suffix(".prompt.json").write_text(json.dumps({"prompt": prompt, "refs": refs, "model": MODEL}, indent=1))
    rev = review(out, a.sing, a.ai, a.no_klaudia, shot=a.shot)
    print(json.dumps({"ok": True, "out": str(out), "full": str(full), "cost": round(cost + rev.get("cost", 0), 3),
                      "too_expensive": cost > 0.20, "review": {k: rev[k] for k in ("pass", "fails", "compare") if k in rev}}))


# ---------------- review ----------------
def review(path, sing=False, ai=False, no_klaudia=False, shot=""):
    path = Path(path)
    im = Image.open(path).convert("RGB")
    fails = []
    if im.size not in BASE.values():
        fails.append(f"size {im.size[0]}x{im.size[1]} (needs 720x1280 or 1280x720)")
    fs = kc.faces(im)
    if fs is not None and not no_klaudia:
        big = [f for f in fs if f[2] >= im.width * 0.06]
        if not big:
            fails.append("no face found (or it is turned away)")
        elif len(big) > 1 and not shot.lower().count("with"):
            fails.append(f"{len(big)} faces: only Klaudia should be there")
        if sing and big and big[0][2] < im.width * (0.22 if im.height > im.width else 0.13):
            fails.append("her face is too small for a sung shot (close or medium close)")
    cost = 0.0
    res = {"machine_checks": "opencv" if fs is not None else "size only (no OpenCV)"}
    if ai:
        k = kit("klaudia.json")
        items = kit("review.json")["checks"] + (kit("review.json")["sing_checks"] if sing else [])
        q = ("Image 1 is the reference sheet of a character called Klaudia. Image 2 is a new photo of her. "
             f"The shot asked for: {shot or 'any'}. Check image 2 against this list and answer ONLY JSON "
             '{"fails": ["…short reason…"], "notes": "…"}. List: ' + " | ".join(items))
        body = {"model": REVIEW_MODEL, "messages": [{"role": "user", "content": [
            {"type": "text", "text": q}, part(KIT / k["face_sheet"]), part(path)]}],
            "response_format": {"type": "json_object"}}
        try:
            r = kc.or_call("POST", "/chat/completions", body, timeout=120)
            txt = r["choices"][0]["message"]["content"]
            got = json.loads(txt[txt.find("{"): txt.rfind("}") + 1])
            fails += [f"(look) {x}" for x in got.get("fails", [])]
            res["notes"] = got.get("notes", "")
            cost = float((r.get("usage") or {}).get("cost") or REVIEW_USD)
        except Exception as e:  # the review must never block the work: say it did not run
            res["ai_review"] = f"did not run ({type(e).__name__})"
    # her face sheet beside the still, to look at
    if not no_klaudia:
        sheet = Image.open(KIT / kit("klaudia.json")["face_sheet"]).convert("RGB")
        h = 640
        a1 = sheet.resize((int(sheet.width * h / sheet.height), h))
        a2 = im.resize((int(im.width * h / im.height), h))
        comp = Image.new("RGB", (a1.width + a2.width + 30, h + 60), (20, 20, 22))
        comp.paste(a1, (0, 60))
        comp.paste(a2, (a1.width + 30, 60))
        d = ImageDraw.Draw(comp)
        d.text((10, 10), "her face sheet", font=kc.font(34), fill=(200, 200, 200))
        d.text((a1.width + 40, 10), ("PASS" if not fails else "CHECK: " + "; ".join(fails))[:70], font=kc.font(30),
               fill=(120, 255, 140) if not fails else (255, 110, 90))
        res["compare"] = str(path.with_suffix(".compare.jpg"))
        comp.save(res["compare"], quality=85)
    res.update({"pass": not fails, "fails": fails, "cost": cost})
    path.with_suffix(".review.json").write_text(json.dumps(res, indent=1))
    return res


def cmd_review(a):
    if a.ai and not a.yes:
        sys.exit("--ai spends about $0.003: add --yes (inside the person's yes for the batch).")
    print(json.dumps(review(a.image, a.sing, a.ai, a.no_klaudia, a.shot)))


def cmd_outfit(a):
    im = Image.open(a.image).convert("RGB")
    fs = kc.faces(im)
    if not fs:
        sys.exit("No face found: crop by hand (from the chin down) or pick another still.")
    x, y, w, h = fs[0]
    top = int(y + h * 1.12)
    if top > im.height * 0.7:
        sys.exit("This still shows too little of her clothes: use a full-body or medium-wide still.")
    crop = im.crop((max(0, x - w * 2), top, min(im.width, x + w * 3), im.height))
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    crop.save(a.out, quality=90)
    print(json.dumps({"ok": True, "out": a.out, "size": crop.size}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd")
    s = sub.add_parser("still")
    s.add_argument("--shot", required=True, help="framing + what she does, in one sentence")
    s.add_argument("--place", default="")
    s.add_argument("--look")
    s.add_argument("--role")
    s.add_argument("--outfit", help="the person's own outfit, in words")
    s.add_argument("--outfit-ref", help="image 2: the clothes only (klaudia_photo.py outfit)")
    s.add_argument("--body")
    s.add_argument("--style-ref", help="image 3: the style frame (light and colour only)")
    s.add_argument("--guest", help="a guest's ficha (klaudia_guest.py)")
    s.add_argument("--extra", nargs="*", help="more references: path=what it is for")
    s.add_argument("--sing", action="store_true", help="a sung shot: face to camera, mouth visible, lips closed")
    s.add_argument("--no-klaudia", action="store_true", help="a still WITHOUT her (a place, the robots, an object)")
    s.add_argument("--format", choices=list(BASE), default="vertical")
    s.add_argument("--ai", action="store_true", help="also the vision review (about $0.003)")
    s.add_argument("--out", required=True)
    s.add_argument("--yes", action="store_true")
    r = sub.add_parser("review")
    r.add_argument("image"); r.add_argument("--sing", action="store_true"); r.add_argument("--ai", action="store_true")
    r.add_argument("--no-klaudia", action="store_true"); r.add_argument("--shot", default=""); r.add_argument("--yes", action="store_true")
    o = sub.add_parser("outfit"); o.add_argument("image"); o.add_argument("--out", required=True)
    a = ap.parse_args()
    if not a.cmd:
        ap.print_help()
        return
    {"still": cmd_still, "review": cmd_review, "outfit": cmd_outfit}[a.cmd](a)


if __name__ == "__main__":
    main()
