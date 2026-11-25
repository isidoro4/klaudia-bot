---
name: klaudia-edit
description: Use when klaudia-news has the song and the clips, or the person asks to edit or re-edit a KLAUDIA'S NEWS video. Builds the vertical video with the lyrics on screen, on this computer, for free.
---

# The edit — /workspace/klaudia-bot/bin/klaudia_edit.py

From the video's folder:
```
python3 /workspace/klaudia-bot/bin/klaudia_edit.py \
  --song song/song.mp3 --words song/alignment.json --lyrics song/lyrics.txt \
  --clips clips/01-*.mp4 clips/02-*.mp4 ... (in story order; a photo instead of a clip is fine) \
  --title "<2–4 words: the news>" --tag "<THE ___ YOURSELF. sign-off>" \
  --out <short-name>.mp4
```
- Give one --clips entry per shot (dump the lines first to count them). A sung take: `clips/NN-sung.mp4@0.7`; when it covers the next line too, put `+` for that line so the take keeps playing.
- One shot per lyric line, cut where each line starts; the clips repeat if there are fewer clips than lines, so give them in the order the story needs.
- `--test 0-10` makes only those seconds, fast: use it first if anything looks off.
- `--end 38` cuts the song there if the take runs long after the last line.
- It prints {"ok": true, "out": …}. Send the file in the chat (big file: a link from their Drive if connected).
- Fails with "No ffmpeg": run skill klaudia-setup step 1 again.
Check before sending: watch the first 5 seconds (her face, the hook words on screen) and the end card. The end card always says "fan-made with KLAUDIA BOT · made with AI": never remove it.
