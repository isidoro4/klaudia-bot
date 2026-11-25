---
name: klaudia-setup
description: Use when the person says set me up, setup, install, start or start over, or a KLAUDIA skill finds the kit missing. Gets the KLAUDIA kit onto this computer and connects Suno.
---

# Setup — the kit, then Suno (one step per reply)

## 1. The kit (no spend, about 2 minutes)
Run:
```
export GIT_TERMINAL_PROMPT=0
test -d /workspace/klaudia-bot/.git || { test -d /workspace/klaudia-bot && mv /workspace/klaudia-bot /workspace/klaudia-bot.old-$(date +%s); git clone -q https://github.com/isidoro4/klaudia-bot /workspace/klaudia-bot; }
git -C /workspace/klaudia-bot pull -q
python3 -m pip install -q --user pillow imageio-ffmpeg
python3 /workspace/klaudia-bot/bin/klaudia_edit.py --help > /dev/null && echo KIT-OK
```
KIT-OK: say "Kit ready." Any error: show the last line in plain words and try once more next reply. Installed packages can vanish after a computer reset: this step is safe to run again any time.

## 2. Suno (the person signs in; you never see or type a password)
One question with buttons — "Connect your Suno for the songs?": **Yes** / **I have no Suno** / **Later**.
- Yes: add a custom MCP server named suno at https://api.suno.com/mcp (remote HTTPS, no key). The person signs in to Suno on its card. Then call its credit or account tool: it answers → "Suno connected: you have N credits." 
- Suno says no access (its connector is in early access): "Ask for access at suno.com/mcp. Until then, make the song yourself on suno.com with the lyrics and style I give you, and send me the file."
- I have no Suno: "Make a free account at suno.com when you want songs. Meanwhile I can use a song file you send me."

## 3. OpenRouter — the quality key (needed for every SUNG video)
One question with buttons — "Klaudia sings with real lip sync and high-quality photos only with an OpenRouter key. Set it up?": **Yes, show me how** / **Only spoken videos for now**.
Say, in simple words, before the card:
- "OpenRouter is a pay-as-you-go account for AI models. With it I make Klaudia's photos with Nano Banana Pro (about $0.14 each) and her singing shots with Seedance, which hears her voice and sings it exactly (about $0.40 per 5-second shot with the standard model, about $1.20 with the best one). A news video with a song: about $3–6 in all. I always show the price and wait for your yes."
- "1. Make an account at openrouter.ai and add credits (Settings → Credits; $10 is plenty to start). 2. Settings → Keys → Create key, and give it a credit limit (for example $10): that limit is your hard cap, whatever happens here. 3. Paste it in the secure card I show you now — I never see it."
Then ask with the masked secure secret card named OPENROUTER_API_KEY. Check it for free: `curl -s https://openrouter.ai/api/v1/key -H "Authorization: Bearer $OPENROUTER_API_KEY"` must answer with its limit and usage (say "Key OK: limit $X, used $Y"; never print the key). Not set in this shell yet: run it again with `bash -lc`. Rejected: ask for a new key; a key pasted in the chat: ask them to delete it at openrouter.ai and make a new one.
Then install the tunnel the singing shots need (free, about 10 s): `mkdir -p ~/.local/bin && A=$(uname -m | sed 's/x86_64/amd64/;s/aarch64/arm64/') && curl -sL -o ~/.local/bin/cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-$A && chmod +x ~/.local/bin/cloudflared && ~/.local/bin/cloudflared --version`.
Only spoken videos: fine; say once that the sung formats need it and "setup" brings this back.

## 4. Ready
Say once: "Ready. What shall we make?" with buttons: **🗞 Klaudia's News** (skill klaudia-news) / **💸 Unpaid sponsorship** (skill klaudia-sponsorship) / **🎵 My song with Klaudia** (skill klaudia-musicvideo). A message with a news link goes straight to klaudia-news.
No OpenRouter key: the sung versions are not offered; say in one line what is missing and that "setup" adds it.
