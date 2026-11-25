---
name: klaudia-edit
description: Use when a KLAUDIA video has its song and its clips or photos, or the person asks to edit or re-edit a video. Builds the video (vertical and 16:9) with the lyrics, graphics, colour and frame, on this computer, for free.
---

# The edit — /workspace/klaudia-bot/bin/klaudia_edit.py

From the video's folder, always from the board: `python3 /workspace/klaudia-bot/bin/klaudia_edit.py --board board.json --out <short-name>.mp4 --also`
- `--also` makes the other shape too (<name>-16x9.mp4). `--test 0-12` makes only that stretch, fast: use it first if anything looks off.
- The board's "style" decides the frame (news / clip / ad), the words (classic / karaoke / giant / box) and the colour (kit/grades.json). Flags override it: `--look`, `--lyrics-style`, `--grade`.
- Sung takes are placed by the song's clock (their .sync.json): never "@0.7" by hand.
- Style frames (pictures of the finished look, free): `--frames 3.2,11,20 --out frames.png`.
- It prints {"ok": true, …}; "lines_timed_by_guess" lists lines Suno did not align: watch those seconds.
- Send the file in the chat (big: a Drive link if connected). Before sending, look at the first 5 seconds (her face, the hook words) and the end card ("fan-made with KLAUDIA BOT · made with AI": never removed).
- No board (an old video): `--song song/song.mp3 --words song/alignment.json --lyrics song/lyrics.txt --clips … --title … --tag …` still works (one shot per line).
- "No ffmpeg": run skill klaudia-setup step 1 again.
