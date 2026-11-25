---
name: klaudia-lipsync
description: Use when a KLAUDIA video has shots where she sings on camera and OPENROUTER_API_KEY is set. HeyGen Avatar IV animates the shot's still with her own vocal, in short takes, then the lip sync is measured. Never without the person's yes to the price.
---

# Singing shots — HeyGen Avatar IV on OpenRouter, short takes, measured

Why HeyGen: it accepts Klaudia's face (Seedance refuses it as "may be a real person"; dropping her reference to get through is FORBIDDEN: the face stops being hers). $0.05 a second.

1. **Her voice alone** (once per song): Suno's stems tool on the chosen take, mode "two" (about 10 credits: ask, ideally in the song's yes). Download the vocals → song/vocals.mp3. Say once that stems appear in their Suno library and can be deleted there.
2. **Sung shots**: 2–4 per video, each 2–5 s, ONLY her own words (never the choir's lines), her face close or medium, mouth visible, made from a still made with `--sing` (klaudia-shots).
3. **Windows** (free): `klaudia_board.py windows board.json --vocals song/vocals.mp3` → sing/NN.wav + sing/NN.json (song_start). A window over 5 s is refused with where to split.
4. **Price + yes**: inside the board's one yes (klaudia-board step 4). The balance is checked before anything is sent.
5. **Takes**: `klaudia_board.py takes board.json --yes` (all in parallel; each window goes to a temporary link deleted within an hour: say so once). One by one if needed: `klaudia_sing.py sing --still photos/NN.png --audio sing/NN.wav --format vertical --out clips/NN-sung.mp4 --yes`. A refusal is final for that still (offer another still). A timeout: `klaudia_sing.py fetch --out clips/NN-sung.mp4` later — never submit again (it would charge twice). 402 "weight": make the window shorter.
6. **The check** (free, automatic in `takes`): `klaudia_sync.py check clips/NN-sung.mp4` → good · shift (the edit moves it) · drift (cut at good_until) · bad. Look at the first take yourself too. One retake at most per shot, with a new yes.
7. **The edit** places them by the song's clock (.sync.json): never add "@0.7".
