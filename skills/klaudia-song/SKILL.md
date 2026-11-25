---
name: klaudia-song
description: Use when klaudia-news has a lyric approved and the person said yes to a song round, or the person asks for a Klaudia song. Makes the song on the person's Suno with Suno's own connector, saves it and its timing.
---

# The song — Suno, the person's account

Never start a round without the person's yes to that round in this chat (each round: 2 takes, about 10 Suno credits).

1. Build the style from kit/sounds.json (for "berlin", fill WORLD and PERCUSSION). Title: the chorus line or the news in 2–3 words.
2. Suno's create tool, custom mode: title, the lyric exactly as approved, style, and the exclude list as negative style (if the tool refuses negative style on their plan, leave it out). Female vocals if the tool offers it. Duration: about 40 s. Never Max Mode unless they ask for it by name.
3. Wait until the 2 takes stream; send both links to listen. They pick one by ear.
4. The chosen take only: download it as mp3 (if Suno says it needs a download credit, ask first) → song/song.mp3. Then Suno's lyric-alignment tool on that take (free; poll while "processing", at most 5 minutes) → song/alignment.json, and the lyric as sent → song/lyrics.txt.
5. No alignment after 5 minutes: say so; the edit can still run with --lines made by you from the take (listen with Suno's listen tool if you have it) or with even spacing as a last resort.

No Suno connected: give the person the title, style and lyric to paste into suno.com themselves; they send back the mp3. Then step 5.
