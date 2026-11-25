---
name: klaudia-board
description: Use for every KLAUDIA video once the song is chosen, and whenever the person wants to see or change the plan ("show me the shots", "the 3 should dance", "shorter", "more dancing"). The board: every shot numbered with its seconds, line and kind, as one image; a free preview with photos; changes by number; only then the paid clips.
---

# The board — the person sees the whole video before paying, and changes it by number

Files in the video's folder: `board.json` (the plan), `board.png` (the picture of it), `preview.mp4` (free preview). Scripts: /workspace/klaudia-bot/bin/klaudia_board.py and klaudia_edit.py (their headers explain them).

## 1. Make the plan (free)
- Lines with times: `python3 …/klaudia_edit.py --song song/song.mp3 --words song/alignment.json --lyrics song/lyrics.txt --clips x --dump-lines song/lines.json`.
- Start board.json with `{"song": "song/song.mp3", "lines": "song/lines.json", "format": "vertical", "title": "<2–4 words>", "tag": "<___ YOURSELF.>"}` and run `python3 …/klaudia_board.py plan board.json --lines song/lines.json --beat <60/BPM> --max 2.0`.
- Then fill each shot with THE KLAUDIA RECIPE (always, unless the person asks otherwise):
  - **Shot 1 = the hook, "sing"**: close-up, she sings the first line to camera.
  - **Her other lines**: "sing" for 2–3 of them (close or medium, mouth visible; never a choir line in CAPITALS/parentheses), "move" for the rest (she acts the line: points, shrugs, reads a phone…).
  - **Every gap without voice = "dance"**: one shot per 1–2 beats, a dance from kit/dances.json (stomp by default), "speed": 1.5. Different framings in a row (wide, medium, close, low angle). The choir's shouts land on dance or robot shots.
  - **Last shot = "sing"**: close-up, the punchline.
  - No shot longer than 2 s, except a sung line that needs it. Same place for the whole video unless the story moves (one set, many angles).
  - "what" = one short sentence a person understands ("close-up, she sings the hook", "she stomps techno, wide").

## 2. Show it (free)
- Make the photos (skill klaudia-shots), set each shot's "still".
- `python3 …/klaudia_board.py sheet board.json --out board.png` → send board.png.
- Free preview: `python3 …/klaudia_edit.py --board board.json --out preview.mp4` → send it. Say: "This is the plan with photos only, nothing paid yet. Tell me changes by number."
- Buttons (pick 4): **Looks good, make the clips** · **More dancing** · **Faster cuts** · **More close-ups** · **Change a shot**.

## 3. Changes (free, as many rounds as they want)
- "3: she dances" → that shot's kind "dance" + a dance. "5: shorter" → split or trim it (keep the song times consistent). "7: out" → merge its time into the neighbour. "More dancing" → turn "move" shots in gaps into "dance". "Faster cuts" → `plan` again with --max 1.0 (keeps each shot's kind/what/still by number). "More close-ups" → change framings in "what" and make new stills.
- Every round: new board.png + new preview.mp4, the same buttons.

## 4. The clips (paid — one yes for all)
- `python3 …/klaudia_board.py check board.json` → the list of clips to make and the price of the singing shots. Say the total once: "N singing shots ≈ $X on your OpenRouter + M dance/move clips on your Grok Bot plan. Go?" One button: **Make all the clips ($X)** / **Not yet**.
- Make ALL the clips at once, in parallel, not one by one: singing shots with skill klaudia-lipsync (HeyGen), dance/move clips with skill klaudia-shots (Grok Imagine, 6 s, from each shot's still, the dance prompt from kit/dances.json). Put each one in its shot's "clip" (sung takes: "clips/NN-sung.mp4@0.7").

## 5. The video
- `python3 …/klaudia_edit.py --board board.json --out <name>.mp4` → send it with the same buttons as step 2, plus **Done**.
- After "Done": the post text (Klaudia's voice, "___ yourself.", "fan-made with KLAUDIA BOT · made with AI"). The person posts it, never you.
