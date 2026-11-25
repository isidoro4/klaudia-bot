---
name: klaudia-resume
description: Use when the person says continue, carry on, where were we, my video, or opens a new chat while a KLAUDIA video is unfinished. Picks the video up from its files, without re-reading an old chat.
---

# Continue a video — from its files

1. `ls -t /workspace/klaudia-videos/*/state.json /workspace/klaudia-news/*/state.json 2>/dev/null | head -3` → the newest unfinished (state "step" not "done"). More than one: buttons with their names.
2. Read its state.json and board.json (not the old chat). Say in ONE line where it is ("FOUR VIEWERS: board approved, clips 5 of 7 ready") and show its latest picture (board.png or the video).
3. Jobs that were running: clips with a file are done; a sung take with only clips/NN-sung.sync.json → `klaudia_sing.py fetch --out clips/NN-sung.mp4` (never submit again). Paid steps are never repeated without a new yes.
4. Go on with the step in state.json, following the recipe of its kind (klaudia-news / klaudia-sponsorship / klaudia-musicvideo).
