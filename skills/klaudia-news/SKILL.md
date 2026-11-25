---
name: klaudia-news
description: Use when the person sends a news story (an X link, a web link or a few words) or says Klaudia's News, make a video, news video. The whole KLAUDIA'S NEWS recipe, news to finished vertical video, with five choices for the person.
---

# KLAUDIA'S NEWS — from a news story to a 30–40 s vertical video

**Sung video = OpenRouter key required** (skill klaudia-setup step 3). Without OPENROUTER_API_KEY, don't make it: say in one line that her lips would not match the song without it, and offer setup. With it: her stills with klaudia_photo.py, 3–5 singing shots with skill klaudia-lipsync (price first, the person's yes), every other shot a Grok Imagine clip where she moves, never one where she sings.

Kit: /workspace/klaudia-bot (missing: skill klaudia-setup first). Read RULES.md and kit/klaudia.json once per video.
Folder for this video: /workspace/klaudia-news/<YYYY-MM-DD>-<short-name>/ (photos/, clips/, song/). Keep notes.md there: the news, every choice, every file.
One step per reply. The person only chooses; you never ask them to write a prompt. Each choice is a question with buttons.

## 1. The news (no spend)
Read the link (X search or the browser) or the words. In 3 lines: what happened · what is confirmed and what is only a plan or a rumour · the source.
Rules check (RULES.md): politics, a real person as the joke, or the coin named after Klaudia → say which rule in one line and offer another angle, or stop. News about prediction markets, crypto, stocks or companies is fine as news: tell what happened with her joke; leave out bonus amounts, promo codes, links and anything that tells people to bet, buy or trade.

## 2. The hook — choice 1
Three hooks, each one line after "Hi! This is Klaudia's News.": a surprise, a cheeky fact, or Klaudia's own situation (she is the deadpan one; the joke is the world, she wins). Under each, in a few words, the opening picture.
Buttons: Hook 1 / Hook 2 / Hook 3 / Other ideas.

## 3. Sound and look — choices 2 and 3
- Sound: buttons from kit/sounds.json (labels only). For "berlin", name the world you would use and why, in one line; they can switch.
- **Pick your Klaudia**: who she is in this video — buttons from kit/roles.json (labels only; 'Other' lets them type a job). Then, only if they want, a look from kit/looks.json instead of the role's own clothes. She is always herself: never offer to change her face, hair or body.

## 4. The lyric and the song — choice 4 (skill klaudia-song)
Write the lyric with kit/lyrics-template.md and show it. Buttons: **Make the song (2 takes, about 10 Suno credits)** / Change something.
Only with that yes: skill klaudia-song. Then send both takes to listen. Buttons: Take 1 / Take 2 / Another round (asks again for the credits).

## 5–7. The board, the photos, the clips and the edit: skill klaudia-board (it replaces the steps below; they stay as reference)

## 5. The photos — choice 5 (skill klaudia-shots)
Plan 6–8 shots, one per line or two of the lyric: the hook picture first, the chorus on the beat, the punchline last. Mix close, medium and wide; the robots and the world as cutaways.
Make the stills (skill klaudia-shots) and show them numbered. Buttons: Use all / Redo some (they say which numbers; at most 2 rounds).

## 6. The clips (skill klaudia-shots)
One clip of 5–6 s per chosen photo, from that photo. Show them as they land. A clip with a broken face or hands: make it once more, then use the photo instead.

## 7. The edit (skill klaudia-edit)
Build the video, send it. Buttons: **Done** / Change something (one round of changes: swap a clip, the title, the tag).
At the end, a post they can copy: 2–3 short lines in Klaudia's voice, the "___ yourself." sign-off, and "fan-made with KLAUDIA BOT · made with AI". You never post it.
