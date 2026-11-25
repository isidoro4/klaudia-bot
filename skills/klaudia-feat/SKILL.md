---
name: klaudia-feat
description: Use when the person wants a second character in a KLAUDIA video — "feat. Claudia", "add Claudia", "with my character", "my mascot", "my own character". Brings Claudia from her public canon, or builds a ficha for the person's own character. Never a real person.
---

# ➕ feat. — a second character, with her own ficha

Buttons: **➕ Claudia (by anabology)** / **➕ My own character** / **No guest**.

## Claudia
`python3 /workspace/klaudia-bot/bin/klaudia_guest.py claudia --dir guests` (reads her public canon and face sheet from claudia.gallery: an open character; credit welcome, not required). Her rules travel with her: her canon word for word, always a grown woman, never "young", nothing explicit, never presented as official. In the post: "Claudia is an open character by anabology (claudia.gallery)" (recommended). Never "feat. Claudia" in the song's artist field.

## Their own character
1. Ask: describe it, or send 1–3 pictures. **Never a real person** (not themselves, not a celebrity, not a friend): if the pictures look like a real person, say so and stop; drawings, mascots, robots and invented people are fine.
2. `klaudia_guest.py own --name "<name>" --describe "<2–3 lines>" [--photos …] --tell "<what makes it different from Klaudia>" --dir guests`
3. The test face sheet (about $0.14, ask): `klaudia_guest.py sheet guests/<name>.json --yes` → send it: "Is this <name>?" **Yes, that's them** / **Not quite** (what to change; each new sheet asks again).
4. `klaudia_guest.py approve guests/<name>.json`.

## In the video
- Every still with both: `klaudia_photo.py still … --guest guests/<name>.json` (both described in every prompt, each with her own face sheet; they never look alike).
- Lip sync with two faces in one shot often fails: each sings in her own shots (HeyGen animates the face in the still); a shot with both = a move or dance shot.
- The board shows who is in each shot ("what": "Klaudia and Claudia, wide, …").
