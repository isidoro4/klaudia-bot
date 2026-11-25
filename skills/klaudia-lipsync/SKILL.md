---
name: klaudia-lipsync
description: Use when a KLAUDIA video has shots where she sings on camera and OPENROUTER_API_KEY is set. Makes those shots with Seedance on OpenRouter from the song's own vocal, so her lips match the song exactly. Never without the person's yes to the price.
---

# Singing shots with real lip sync — Seedance on OpenRouter

Same method as the Claudia bot: reference mode, the still as @Image1, her face as @Image2, the VOCAL STEM of exactly that shot's lines as @Audio1 (https link). Script: /workspace/klaudia-bot/bin/klaudia_sing.py (its header explains every command). From the video's folder:

1. **The vocal stem** (once per song): Suno's stems tool on the chosen take, mode "two" (about 10 Suno credits: ask first, in the same yes as the song if you can). Download the vocals stem (if Suno asks for a download credit, ask) → song/vocals.mp3. Never make extra Suno songs to cut windows: the stems are the only Suno step here. Say once that the stems appear in their Suno library and can be deleted there.
2. **The lines with their times**: `python3 /workspace/klaudia-bot/bin/klaudia_edit.py --song song/song.mp3 --words song/alignment.json --lyrics song/lyrics.txt --clips x --dump-lines song/lines.json`.
3. **Which shots sing**: 3–5 at most per video, 4–8 s each, one or two lyric lines each, her face close or medium, mouth fully visible, nothing in front of it. The rest stay Grok Imagine clips where she moves (no singing to camera in those).
4. **The windows** (free): for each singing shot, `python3 …/klaudia_sing.py window --vocals song/vocals.mp3 --from <first word t0> --to <last word t1> --out sing/<NN>.wav` (times from lines.json).
5. **The price and the yes**: `python3 …/klaudia_sing.py price --seconds <s> --model mini` for each; show the list and the total. Models: **mini** (ALWAYS the default, about $0.38 per 5 s at 720p), **flash** (about $0.76), **full** (Seedance 2.5, about $1.16, the best: only if the person picks it). Show the price per shot and the total with mini, and the other two as options. Buttons: **Go (total $X)** / Change. Nothing is spent without that yes.
6. **The links** (free): `python3 …/klaudia_sing.py host --dir sing` (background). It tries the tunnel (over http2) and, if this computer blocks it, uploads each window to a temporary host that deletes it within an hour. It prints `{"mode", "urls": {"01.wav": "https://…"}}`. If mode is "temp", tell the person in one line: "Your vocal snippets are on a temporary public link for up to an hour (only these few seconds)." With mode "tunnel", keep it running until the last take, then stop it.
7. **The takes**, one by one: `python3 …/klaudia_sing.py sing --still photos/<NN>.png --face /workspace/klaudia-bot/refs/klaudia-face.jpg --audio-url <the url printed for <NN>.wav> --words "<the exact words>" --seconds <s> --model <m> --format <vertical|horizontal> --out clips/<NN>-sung.mp4 --yes`. It prints the real cost. A refusal is final for that still: never edit the picture to get through; offer another still. A timeout: never submit again (it would charge twice); say so.
8. **Check by eye** the first take before the rest: does she sing those words? If her lips drift, keep the part that matches (the edit can cut it shorter) or cut away to another shot. One retake at most per shot, with the person's yes.
9. **The edit**: give each sung take as `clips/<NN>-sung.mp4@0.7` in klaudia-edit's --clips list, in its place in the story (0.7 s = the window's lead before the first word).
