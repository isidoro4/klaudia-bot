---
name: klaudia-board
description: Use for every KLAUDIA video once the song is chosen, and whenever the person wants to see or change the plan ("show me the shots", "3 should dance", "shorter"). The board: every shot numbered with its seconds, line, graphic and photo, style frames and a free preview; changes by number; then all the paid clips with one yes.
---

# The board — the whole video before paying, changed by number

**Waiting videos (free, in the kit):** whenever a step takes more than a minute (Suno singing, a batch of stills, the clips, the edit), send ONE of kit/waiting/*.mp4 with one short line, e.g. "Klaudia is getting ready… clip 3 of 8" (makeup · wardrobe · booth · edit, in turn, never the same twice in a row). They cost nothing: they were made once and live in the kit.

Files in the video's folder: board.json (the plan), board.png, frames.png, preview.mp4. Scripts in /workspace/klaudia-bot/bin (their headers explain every command). Run them from the video's folder.

## 1. The plan (free)
- Lines with times AND parts: `python3 …/klaudia_edit.py --song song/song.mp3 --words song/alignment.json --lyrics song/lyrics.txt --dump-lines song/lines.json` (keeps every line; "guessed" lists lines timed by their neighbours: look at them).
- board.json starts as `{"song": "song/song.mp3", "lines": "song/lines.json", "format": "vertical", "title": "<2–4 words>", "tag": "<___ YOURSELF.>", "style": {"look": "news|clip|ad", "lyrics": "classic", "grade": "film"}}`.
- News: `klaudia_board.py plan board.json --lines song/lines.json --template news` (7 fixed shots). Songs and ads: `--template recipe --beat <60/BPM> --max 2.0` (one shot per line, the gaps danced).
- Fill "what" (one short sentence a person understands) and, where the line has a fact, a "graphic" from kit/graphics.json (the object that explains it; never over her face: the edit places it). Sung shots: close or medium, face to camera, at most 5 s of singing (`split` if longer).

## 2. Show it (free, ONE message)
- Stills: skill klaudia-shots, then each shot's "still".
- `klaudia_board.py sheet board.json --out board.png` · `klaudia_board.py frames board.json --out frames.png` (3–5 style frames: the finished look with the words, the graphic and the colour) · `klaudia_edit.py --board board.json --out preview.mp4` (photos only, free).
- Say: "This is the whole video with photos, nothing paid yet. Change anything by number." Buttons: **Looks good, make the clips** · **More dancing** · **Faster cuts** · **More close-ups** · **Change a shot**.

## 3. Changes (free, as many rounds as they want)
"3: she dances" → kind dance. "5: shorter" → `split` or trim (t0/t1 stay on the song). "7: out" → give its time to the neighbour. "2: no graphic" / "2: a clock" → change "graphic". Colour / words / frame → board "style" (skill klaudia-style). A drawn-on picture from the person (Mark up) = read the arrows and circles with the shot number. New board.png + frames.png + preview each round.

## 4. The clips (paid — ONE yes for all)
- `klaudia_board.py check board.json` → what is missing and the sung price. `klaudia_common.py balance --need <price>` → enough? If not: say how much to add, stop.
- Say once: "N sung takes ≈ $X on your OpenRouter + M clips on your Grok Bot plan. Go?" Button **Make all the clips ($X)** / **Not yet**.
- After the yes, AT THE SAME TIME: `klaudia_board.py windows board.json --vocals song/vocals.mp3` then `klaudia_board.py takes board.json --yes` in the background (all sung takes in parallel, each with its lip-sync check), and the dance/move clips with Grok Imagine (skill klaudia-shots) → each shot's "clip". Meanwhile: the post and the thumbnail (klaudia_social.py).
- Sung takes: put just "clips/NN-sung.mp4" (no @): the .sync.json beside it places every syllable on the song. A take marked drift: `split` at its "cut_at" and give the rest another clip; bad: one retake with a new yes, or a move shot.

## 5. The video
`klaudia_edit.py --board board.json --out <name>.mp4 --also` → vertical + 16:9. `--test 0-12` first if anything looks off. Send it; buttons **Done** / **Change something**. The end card always says "fan-made with KLAUDIA BOT · made with AI": never remove it.
