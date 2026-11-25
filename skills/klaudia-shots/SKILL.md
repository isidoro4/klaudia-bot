---
name: klaudia-shots
description: Use when a KLAUDIA video needs Klaudia's photos (stills) or clips, or the person asks for a photo or a clip of her. Stills with her numbered references and an automatic review; clips with this bot's Grok Imagine from those stills.
---

# Stills and clips — always HER

**The rule:** every still of Klaudia goes with her face sheet as image 1 (the script does it). Never a still of her "from text only", never a picture edited to get past a filter. Refused → another shot or another model, never without her reference.

## Stills (OpenRouter, about $0.14 each + $0.003 review; one yes for the batch)
`python3 /workspace/klaudia-bot/bin/klaudia_photo.py still --shot "<framing + what she does>" --place "<one line>" [--role <id> | --look <id> | --outfit-ref refs/outfit.jpg] [--body <id>] [--style-ref photos/01.png] [--sing] [--guest guests/<name>.json] --format vertical --ai --out photos/NN.png --yes`
- The prompt is built the same way every time: "image 1 = who she is · image 2 = her clothes · image 3 = the style", her identity text word for word, body, clothes, shot, place. Without --yes it shows the prompt and price (free).
- It saves photos/NN.png at exactly 720×1280 (1280×720 for 16:9) for Grok Imagine, and NN.full.png for the thumbnail.
- `--sing` for every shot where she sings: face to camera, mouth visible, lips closed.
- **Consistency**: after the first approved full-body or medium still, crop her clothes: `klaudia_photo.py outfit photos/NN.full.png --out refs/outfit.jpg`, and pass `--outfit-ref refs/outfit.jpg --style-ref photos/NN.png` to every next still.
- **Review** (automatic): photos/NN.review.json says pass or the reasons; photos/NN.compare.jpg puts her face sheet beside it. Look at it. A fail: once more inside the same yes; fails again → show it with the reason, the person decides.
- Several stills: make them one after the other in the background, show them together in ONE numbered sheet (`klaudia_sheet.py pick --images … --title "THE SHOTS" --out shots.png`).
- Stills WITHOUT her (a place, the robots, an object): `--no-klaudia`, or this bot's own Grok Imagine (free).

## Clips (Grok Imagine of this bot, 6 s, 720p, from a still)
First frame: the shot's still (already 720×1280). Prompt, 60–120 words: what she does second by second (one action), the camera in one line ("static camera" unless the shot needs a move), "keep her face, hair and clothes exactly as in the first frame", "no text on screen". Dances: the dance's prompt from kit/dances.json and "speed": 1.5 in the board. Never a singing shot here (skill klaudia-lipsync). Check the size with ffprobe; below 720 on the short side → once more. Save clips/NN-name.mp4. Make them in parallel, not one per reply.
