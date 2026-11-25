---
name: klaudia-news
description: Use when the person sends a news story (an X link, a web link or a few words) or says Klaudia's News, make a video, news video. The whole KLAUDIA'S NEWS recipe, news to finished video (vertical + 16:9), choices by pictures and numbers.
---

# KLAUDIA'S NEWS — news → 30–40 s video, about 10 short replies

Kit: /workspace/klaudia-bot (missing: skill klaudia-setup). Needs OPENROUTER_API_KEY for her photos and singing (without it: say so in one line, offer setup).
Folder: /workspace/klaudia-videos/<YYYY-MM-DD>-<short-name>/ (photos/ clips/ song/ sing/ social/). After EVERY step write state.json: `python3 -c "import sys;sys.path.insert(0,'/workspace/klaudia-bot/bin');import klaudia_common as k;k.save_state('.', step='<step>', <choice>='<value>')"`. A new chat continues from it (klaudia-resume).
Talk as skill klaudia-welcome says: short, pictures, buttons, never "say continue". Read RULES.md and kit/klaudia.json once.

1. **The news** (free). Read it. 3 lines: what happened · what is confirmed / only a plan · the source. Rules check (RULES.md): politics, a real person as the joke, a coin → say which rule, offer another angle or stop.
2. **Hook + sound — one message.** Three hooks (one line each after "Hi! This is Klaudia's News.", with the opening picture in a few words) as buttons **1 / 2 / 3 / Other ideas**, and under them one line: "Sound: Berlin techno + <world from kit/sounds.json> — tap 🔊 to change". Default = keep.
3. **Who is Klaudia — one message.** sheets/bodies.png → "Which Klaudia? 1 · 2 · 3 · as she is", plus buttons of 6 roles from kit/roles.json (labels) + **Other**. Outfit = the role's clothes; "👗 Dress her" opens kit/looks.json or ✍️ their own (skill klaudia-style, section Outfit).
4. **The lyric** (kit/lyrics-template.md), shown in 8–12 short lines. Buttons: **Make the song (2 takes, ~10 Suno credits)** / Change something. With the yes: skill klaudia-song.
   **While Suno works** (about 1–2 min): send sheets/grades.jpg ("Colour? 1–7") and sheets/words.jpg ("Words? 1–4"); write their answers into board.json "style" (look: news). No reply needed to go on: defaults film + classic.
5. **Pick the take** by ear: Take 1 / Take 2 / Another round (asks again for credits). Then the stems for her voice (skill klaudia-lipsync step 1, inside the same yes if you asked for it).
6. **The board — FIXED for the news** (skill klaudia-board): `klaudia_board.py plan board.json --lines song/lines.json --template news` = 7 shots. Fill each shot's "what" and the graphic that EXPLAINS its fact (kit/graphics.json; placeholders in <> must be replaced). Price of the stills first ("7 photos ≈ $1.00 + review"), one yes, then the stills (skill klaudia-shots), then send in ONE message: board.png + frames.png (style frames) + preview.mp4. Buttons: **Looks good** / **Change a shot** (by number) / **🔄 other photos**.
7. **The clips — one yes for all** (skill klaudia-board step 4): the sung takes in parallel ($ shown) + the dance/move clips with Grok Imagine. **While they are made:** the post and the thumbnail (`klaudia_social.py --board board.json --post "<2–3 lines in her voice>" --out social`), sent as soon as they exist.
8. **The video**: `klaudia_edit.py --board board.json --out <name>.mp4 --also` (vertical + 16:9). Send the vertical (the 16:9 as a file or a Drive link); buttons **Done** / **Change something** (by number or second).
9. **Done**: send social/x-post.jpg + the post text. "Open a new chat for the next one." You never post.
