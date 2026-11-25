---
name: klaudia-setup
description: Use when the person says set me up, setup, install, start or start over, or a KLAUDIA skill finds the kit missing. Gets the KLAUDIA kit onto this computer and connects Suno and OpenRouter.
---

# Setup — the kit, Suno, OpenRouter (one step per reply)

## 1. The kit (no spend, about 2 minutes)
```
export GIT_TERMINAL_PROMPT=0
test -d /workspace/klaudia-bot/.git || { test -d /workspace/klaudia-bot && mv /workspace/klaudia-bot /workspace/klaudia-bot.old-$(date +%s); git clone -q https://github.com/isidoro4/klaudia-bot /workspace/klaudia-bot; }
git -C /workspace/klaudia-bot pull -q
python3 -m pip install -q --user pillow imageio-ffmpeg numpy "opencv-python-headless<5"
python3 /workspace/klaudia-bot/bin/klaudia_edit.py --help > /dev/null && python3 /workspace/klaudia-bot/bin/klaudia_common.py face /workspace/klaudia-bot/refs/klaudia-face.jpg && echo KIT-OK
```
KIT-OK: "Kit ready." Any error: the last line in plain words, and try once more. Installed packages can vanish after a computer reset: this step is safe to run again any time. (OpenCV only helps: without it, crops and checks are simpler.)

## 2. Suno (the person signs in; you never see or type a password)
"Connect your Suno for the songs?": **Yes** / **I have no Suno** / **Later**.
- Yes: add a custom MCP server named suno at https://api.suno.com/mcp (remote HTTPS, no key). The person signs in on its card. Then its credit tool: "Suno connected: N credits."
- No access yet (early access): "Ask at suno.com/mcp. Until then, make the song on suno.com with the lyric and style I give you and send me the file."
- No Suno: "Make a free account at suno.com when you want songs. Meanwhile, send me a song file."

## 3. OpenRouter — her photos and her singing
"Klaudia's photos and her singing shots need an OpenRouter key. Set it up?": **Yes, show me how** / **Not now**.
Say, simply: "OpenRouter is a pay-as-you-go account for AI models. With it I make her photos (about $0.14 each) and her singing shots with HeyGen, which hears her voice and moves her lips exactly ($0.05 a second, 3–5 s a shot). A news video: about $1–3. I show the price and wait for your yes every time." Then: "1. Account at openrouter.ai, add credits ($5–10 is plenty). 2. Settings → Keys → Create key, with a credit limit (your hard cap). 3. Paste it in the secure card I show you now — I never see it."
Ask with the masked secure secret card named OPENROUTER_API_KEY. Check, free: `python3 /workspace/klaudia-bot/bin/klaudia_common.py balance` → "Key OK: $X left." (not set yet in this shell: `bash -lc`). A key pasted in the chat: ask them to delete it at openrouter.ai and make a new one.
No tunnel to install: the singing shots send their few seconds of voice through a temporary link that deletes itself within an hour (say so once).

## 4. Ready
"Ready. What shall we make?" with buttons **📰 Klaudia's News** / **💸 Unpaid sponsorship** / **🎵 My song with Klaudia** / **➕ feat.**. A message with a news link goes straight to klaudia-news.
