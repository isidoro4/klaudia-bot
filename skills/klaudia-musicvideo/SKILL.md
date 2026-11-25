---
name: klaudia-musicvideo
description: Use when the person picks My song with Klaudia, or asks for a music video, a videoclip or a song with Klaudia (not a news story). A horizontal 16:9 music video of 1–3 minutes with Klaudia as the singer.
---

# A KLAUDIA MUSIC VIDEO — horizontal, 1–3 minutes

**Sung video = OpenRouter key required** (skill klaudia-setup step 3). Without it: say so in one line and offer setup. With it: her stills with skill klaudia-shots (always with her references, reviewed), 2–4 short singing shots with skill klaudia-lipsync, every other shot a Grok Imagine clip where she moves. Talk as klaudia-welcome says (short, pictures, buttons, one chat per video, state.json after every step). Choices of colour, words, body and outfit: skill klaudia-style. A guest: skill klaudia-feat.

Same machinery as skill klaudia-news (folder, state.json, choices as pictures and buttons). Read RULES.md and kit/musicvideo-template.md.
Folder: /workspace/klaudia-videos/<YYYY-MM-DD>-<name>/ (state.json after every step).

1. **The start** — buttons: **I have an idea** / **Pitch me three** / **I have my own lyric** / **I have my own song file**.
2. **The concept — choice 1**: three pitches (the template's shape). Buttons.
3. **Sound and look — choices 2 and 3**: the sound menu (kit/sounds.json; for a music video any world from the past can fit, not only the news ones) or their own song; Pick your Klaudia (kit/roles.json) for the world, or a look from kit/looks.json.
4. **The song — choice 4**:
   - We write it: the lyric (the template), shown; the yes for each Suno round (about 10 credits, 2 takes; ask "about 2:30" as duration); skill klaudia-song; pick by ear.
   - Their own lyric: same, with their words (check the rules).
   - Their own file: save it as song/song.mp3. No timing: the edit cuts on a steady rhythm (`--every`, 4 bars; at 120 BPM that is 8 s).
5–8. **The board, stills, clips and edit: skill klaudia-board** with `format: horizontal`, `--template recipe --max 2.5`, style look "clip". 14–24 shots; before any picture say the cost in plan terms ("about N stills and N clips on your Grok Bot usage; a long video can use a lot of your weekly pool") and the OpenRouter price. Few graphics (2–3 in the whole video). The board, the style frames and the free preview first; then one yes for all the clips. The edit: `klaudia_edit.py --board board.json --out <name>.mp4 --also` (16:9 + vertical). Their own song file with no timing: `--every 8` (4 bars at 120 BPM) instead of a board. While the clips are made: thumbnail + post (`klaudia_social.py`).
