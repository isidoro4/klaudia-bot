---
name: klaudia-sponsorship
description: Use when the person picks Unpaid sponsorship, or asks for an ad, a promo or a sponsorship with Klaudia for a product, app or company. A 20–35 s vertical video where Klaudia makes an ad nobody paid for.
---

# UNPAID SPONSORSHIP — Klaudia's ad that nobody paid for

**Sung video = OpenRouter key required** (skill klaudia-setup step 3). Without OPENROUTER_API_KEY, don't make it: say in one line that her lips would not match the song without it, and offer setup. With it: her stills with klaudia_photo.py, 3–5 singing shots with skill klaudia-lipsync (price first, the person's yes), every other shot a Grok Imagine clip where she moves, never one where she sings.

Same machinery as skill klaudia-news (folder, notes.md, one step per reply, choices as buttons, klaudia-song, klaudia-shots, klaudia-edit). Read RULES.md and kit/sponsorship-template.md.
Folder: /workspace/klaudia-news/<YYYY-MM-DD>-unpaid-<brand>/.

1. **The brand** (no spend): the person names it (a link helps). Check the rules: no medicine, alcohol, gambling, weapons, adult products, financial products, coins or tokens; nothing that mocks a real person. Find 2–3 TRUE things about it (its own site or the news); show them in 3 lines.
2. **The angle — choice 1**: three ideas, one line each: how Klaudia "uses" it, absurd but harmless (she wins). Buttons.
3. **Sound and Klaudia — choices 2 and 3**: as in klaudia-news (the sound, then Pick your Klaudia from kit/roles.json) (the sound menu; for "berlin", a world that fits the product).
4. **Lyric and song — choice 4**: kit/sponsorship-template.md; show it; the yes for the Suno round (about 10 credits); skill klaudia-song; pick a take.
5–7. **Board, photos, clips, edit: skill klaudia-board.** Then, as reference:
5. **Photos — choice 5**: 6–8 shots: her with the product as a GENERIC object (no logo, no label text, no app screen), one big hero shot of it, the robots reacting, the punchline last. Skill klaudia-shots.
6. **Clips**: skill klaudia-shots.
7. **Edit**: skill klaudia-edit, vertical, `--title "UNPAID: <BRAND>"`; then add the line "unpaid · not affiliated with <BRAND>" to the post you write for them. You never post it.
