#!/usr/bin/env python3
"""KLAUDIA BOT · ➕ feat.: a second character in the video, with her/his own ficha (face sheet + fixed words).

  claudia  python3 klaudia_guest.py claudia --dir guests
           Reads Claudia's PUBLIC canon from claudia.gallery (an open character by anabology: anyone may use her,
           credit welcome but not required) and her face sheet → guests/claudia.json + guests/claudia-face-sheet.jpg.
           Nothing of hers is stored in this kit: it is read fresh each time.
  own      python3 klaudia_guest.py own --name "Bolt" --describe "a tall chrome robot with a round TV head…" \
               [--photos me1.jpg me2.jpg] --dir guests
           A character of the person's own (a drawing, a mascot, an invented person — NEVER a real person's face):
           writes guests/bolt.json and prints the prompt of a test face sheet.
  sheet    python3 klaudia_guest.py sheet guests/bolt.json [--yes]      (Nano Banana Pro, about $0.14)
           makes guests/bolt-face-sheet.png (front, 3/4, profile, full body). The person looks at it:
           "yes, that's him/her" → approve; otherwise sheet again (each one asks for the yes again).
  approve  python3 klaudia_guest.py approve guests/bolt.json
Then every still with both: klaudia_photo.py still … --guest guests/<name>.json (both described in every prompt,
each with her own face sheet; the two never look alike). Lip sync with two faces in one shot often fails: the guest
sings in her own shots, or the shot is cut before it drifts (klaudia_sync.py).
"""
import argparse
import base64
import json
import re
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import klaudia_common as kc  # noqa: E402

CLAUDIA_MD = "https://claudia.gallery/claudia.md"
CLAUDIA_SHEET = "https://claudia.gallery/kit/claudia-face-sheet.jpg"
MODEL = "google/gemini-3-pro-image-preview"


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "klaudia-bot"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-") or "guest"


def cmd_claudia(a):
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    md = get(CLAUDIA_MD).decode("utf-8", "replace")
    blocks = re.findall(r"```\s*\n(.*?)\n```", md, re.S)
    close = next((b.strip() for b in blocks if "jaw-length bob" in b), None)
    far = next((b.strip() for b in blocks if "late twenties" in b and b.strip() != close), None)
    if not close:
        sys.exit("Could not read Claudia's identity from claudia.gallery (the page changed): ask the person to try later.")
    (d / "claudia-face-sheet.jpg").write_bytes(get(CLAUDIA_SHEET))
    ficha = {
        "name": "Claudia", "source": "https://claudia.gallery/claudia/ (open character by anabology, read " +
        __import__("datetime").date.today().isoformat() + ")",
        "identity": close.replace(", a thin headset microphone at her cheek", "") + ".",
        "identity_far": (far or close) + ".",
        "face_sheet": "claudia-face-sheet.jpg",
        "tell": "a glossy black JAW-LENGTH bob with one clay-orange streak and a small orange star hair clip (Klaudia's hair is very long, below the waist)",
        "outfit": "",
        "never": ["the word 'young' in a prompt", "a second streak or other orange on her", "an influencer smile",
                  "anything that reads under age, explicit or sexualised", "logos or text on her clothes"],
        "credit": "Claudia is an open character by anabology (claudia.gallery)",
        "credit_required": False,
        "approved": True,
    }
    (d / "claudia.json").write_text(json.dumps(ficha, indent=1))
    print(json.dumps({"ok": True, "out": str(d / "claudia.json"), "face_sheet": str(d / "claudia-face-sheet.jpg"),
                      "say": "Claudia is in (her public canon from claudia.gallery). Credit in the post is welcome, not required."}))


def cmd_own(a):
    d = Path(a.dir)
    d.mkdir(parents=True, exist_ok=True)
    s = slug(a.name)
    photos = []
    for k, p in enumerate(a.photos or []):
        dst = d / f"{s}-ref{k + 1}{Path(p).suffix.lower() or '.jpg'}"
        dst.write_bytes(Path(p).read_bytes())
        photos.append(dst.name)
    ficha = {"name": a.name, "identity": a.describe.rstrip(".") + ".", "identity_far": a.describe.rstrip(".") + ".",
             "face_sheet": f"{s}-face-sheet.png", "refs": photos, "tell": a.tell or "", "outfit": a.outfit or "",
             "never": ["a real person's face", "anything sexual", "anyone who looks under age"], "approved": False}
    p = d / f"{s}.json"
    p.write_text(json.dumps(ficha, indent=1))
    print(json.dumps({"ok": True, "out": str(p), "prompt": sheet_prompt(ficha), "next": f"klaudia_guest.py sheet {p}"}))


def sheet_prompt(f):
    return ("A character reference sheet on a plain warm grey background, the SAME character in five views: "
            "a large face-on portrait, a three-quarter view, a profile, and two full-body views (front and side). "
            f"The character: {f['identity']} {f.get('outfit', '')} Neutral expression, even soft light, a real "
            "photograph (unless the description says drawn or animated). No text, no letters, no logos. "
            + ("Image 1 and the next ones are references for this character: copy their face and look exactly. "
               if f.get("refs") else ""))


def cmd_sheet(a):
    fp = Path(a.ficha)
    f = json.loads(fp.read_text())
    refs = [fp.parent / r for r in f.get("refs", [])]
    prompt = sheet_prompt(f)
    if not a.yes:
        print(json.dumps({"dry_run": True, "usual_usd": 0.14, "prompt": prompt, "refs": [str(r) for r in refs]}))
        return
    kc.need(0.25)
    body = {"model": MODEL, "modalities": ["image", "text"],
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}] +
                          [{"type": "image_url", "image_url": {"url": kc.data_url(r, 2048)}} for r in refs]}],
            "image_config": {"aspect_ratio": "16:9", "image_size": "2K"}}
    r = kc.or_call("POST", "/chat/completions", body)
    imgs = (r.get("choices") or [{}])[0].get("message", {}).get("images") or []
    if not imgs:
        sys.exit(json.dumps({"ok": False, "why": "no image came back (often a refusal)"}))
    out = fp.parent / f["face_sheet"]
    out.write_bytes(base64.b64decode(imgs[0]["image_url"]["url"].split(",", 1)[1]))
    print(json.dumps({"ok": True, "out": str(out), "cost": float((r.get("usage") or {}).get("cost") or 0.14),
                      "say": f"Is this {f['name']}? Yes → approve. No → tell me what is wrong and I make another (asks again)."}))


def cmd_approve(a):
    fp = Path(a.ficha)
    f = json.loads(fp.read_text())
    if not (fp.parent / f["face_sheet"]).exists():
        sys.exit("No face sheet yet: run `sheet` first.")
    f["approved"] = True
    fp.write_text(json.dumps(f, indent=1))
    print(json.dumps({"ok": True, "name": f["name"]}))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("claudia"); c.add_argument("--dir", default="guests")
    o = sub.add_parser("own"); o.add_argument("--name", required=True); o.add_argument("--describe", required=True)
    o.add_argument("--photos", nargs="*"); o.add_argument("--tell"); o.add_argument("--outfit"); o.add_argument("--dir", default="guests")
    s = sub.add_parser("sheet"); s.add_argument("ficha"); s.add_argument("--yes", action="store_true")
    ap_ = sub.add_parser("approve"); ap_.add_argument("ficha")
    a = ap.parse_args()
    {"claudia": cmd_claudia, "own": cmd_own, "sheet": cmd_sheet, "approve": cmd_approve}[a.cmd](a)


if __name__ == "__main__":
    main()
