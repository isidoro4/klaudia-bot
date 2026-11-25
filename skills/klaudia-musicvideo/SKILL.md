---
name: klaudia-musicvideo
description: Use when the person picks My song with Klaudia, or asks for a music video, a videoclip or a song with Klaudia (not a news story). A horizontal 16:9 music video of 1–3 minutes with Klaudia as the singer.
---

# A KLAUDIA MUSIC VIDEO — horizontal, 1–3 minutes

**Sung video = OpenRouter key required** (skill klaudia-setup step 3). Without OPENROUTER_API_KEY, don't make it: say in one line that her lips would not match the song without it, and offer setup. With it: her stills with klaudia_photo.py, 3–5 singing shots with skill klaudia-lipsync (price first, the person's yes), every other shot a Grok Imagine clip where she moves, never one where she sings.

Same machinery as skill klaudia-news (folder, notes.md, one step per reply, choices as buttons). Read RULES.md and kit/musicvideo-template.md.
Folder: /workspace/klaudia-videos/<YYYY-MM-DD>-<name>/.

1. **The start** — buttons: **I have an idea** / **Pitch me three** / **I have my own lyric** / **I have my own song file**.
2. **The concept — choice 1**: three pitches (the template's shape). Buttons.
3. **Sound and look — choices 2 and 3**: the sound menu (kit/sounds.json; for a music video any world from the past can fit, not only the news ones) or their own song; Pick your Klaudia (kit/roles.json) for the world, or a look from kit/looks.json.
4. **The song — choice 4**:
   - We write it: the lyric (the template), shown; the yes for each Suno round (about 10 credits, 2 takes; ask "about 2:30" as duration); skill klaudia-song; pick by ear.
   - Their own lyric: same, with their words (check the rules).
   - Their own file: save it as song/song.mp3. No timing: the edit cuts on a steady rhythm (`--every`, 4 bars; at 120 BPM that is 8 s).
5–8. **The board, stills, clips and edit: skill klaudia-board** (format horizontal, --max 2.5). As reference:
5. **The board — choice 5**: 14–24 shots (the template). Show it as a numbered list, one line per shot. Before any picture, say the cost in their plan's terms: "about N stills and N clips of 6–8 s on your Grok Bot usage; a long video can use a lot of your weekly pool". Buttons: **Go** / Change shots.
6. **Stills**: skill klaudia-shots, 16:9 (horizontal) instead of 9:16. Show them in batches of 6. Buttons: Use / Redo some (at most 2 rounds).
7. **Clips**: skill klaudia-shots, 6–8 s each, 16:9, from each still. In a shot where she sings, the words in quotes and kit/klaudia.json "singing"; elsewhere she moves.
8. **Edit — choice 6**: buttons **With lyrics on screen** / **Clean**. Then skill klaudia-edit with `--format horizontal --lines-per-shot 2 --cut-sung` (Clean: add `--no-lyrics`; no timing: `--every 8` instead of --words/--lyrics). `--test 0-20` first. Send it; one round of changes; a post they can copy with "fan-made with KLAUDIA BOT · made with AI".
