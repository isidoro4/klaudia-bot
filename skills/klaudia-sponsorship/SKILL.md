---
name: klaudia-sponsorship
description: Use when the person picks Unpaid sponsorship, or asks for an ad, a promo or a sponsorship with Klaudia for a product, app or company. A 20–35 s vertical video where Klaudia makes an ad nobody paid for.
---

# UNPAID SPONSORSHIP — Klaudia's ad that nobody paid for

**Sung video = OpenRouter key required** (skill klaudia-setup step 3). Without it: say so in one line and offer setup. With it: her stills with skill klaudia-shots (always with her references, reviewed), 2–4 short singing shots with skill klaudia-lipsync, every other shot a Grok Imagine clip where she moves. Talk as klaudia-welcome says (short, pictures, buttons, one chat per video, state.json after every step). Choices of colour, words, body and outfit: skill klaudia-style. A guest: skill klaudia-feat.

Same machinery as skill klaudia-news (folder, state.json, choices as pictures and buttons, klaudia-song, klaudia-shots, klaudia-edit). Read RULES.md and kit/sponsorship-template.md.
Folder: /workspace/klaudia-videos/<YYYY-MM-DD>-unpaid-<brand>/.

1. **The brand** (no spend): the person names it (a link helps). Check the rules: no medicine, alcohol, gambling, weapons, adult products, financial products, coins or tokens; nothing that mocks a real person. Find 2–3 TRUE things about it (its own site or the news); show them in 3 lines.
2. **The angle — choice 1**: three ideas, one line each: how Klaudia "uses" it, absurd but harmless (she wins). Buttons.
3. **Sound and Klaudia — choices 2 and 3**: as in klaudia-news (the sound, then Pick your Klaudia from kit/roles.json) (the sound menu; for "berlin", a world that fits the product).
4. **Lyric and song — choice 4**: kit/sponsorship-template.md; show it; the yes for the Suno round (about 10 credits); skill klaudia-song; pick a take.
5–7. **Board, photos, clips, edit: skill klaudia-board** with `--template recipe`, style look "ad" (the frame says "UNPAID · NOT AFFILIATED"). Photos: her with the product as a GENERIC object (no logo, no label text, no app screen), one hero shot of it, the robots reacting, the punchline last. Graphics for an ad (kit/graphics.json by_format.ad): tag ($0.00), ticket, stamp UNPAID. While the clips are made: the thumbnail and the post (`klaudia_social.py`), with "unpaid · not affiliated with <BRAND>". The edit: `klaudia_edit.py --board board.json --out unpaid-<brand>.mp4 --also`. You never post it.
