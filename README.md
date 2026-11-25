# KLAUDIA BOT

Make videos with Klaudia in Grok Bot, three ways:
- 📰 **Klaudia's News** (vertical, 30–40 s): send a news story, she sings it.
- 💸 **Unpaid sponsorship** (vertical, 20–35 s): she makes the ad nobody paid for.
- 🎵 **My song with Klaudia** (horizontal music video, 1–3 min): your idea, lyric or song, with her as the singer.

You pick from buttons (the idea, the sound, her look, the song take, the pictures); you never write a prompt. Only Grok Bot and your Suno: no other accounts.

**Klaudia** (with a K) is an original character by @javif4_ / @KLAUDIAclub — [klaudia.club](https://klaudia.club). This kit lets anyone make **fan-made** videos with her, on their own accounts, following [RULES.md](RULES.md).

## How it works
- **Grok Bot** runs the recipe (the skills in `skills/`), makes her photos and clips with its own Grok Imagine from her reference images (`refs/`), and edits the video on its computer (`bin/klaudia_edit.py`, Python + ffmpeg).
- **Suno** makes the song, on your own Suno account through Suno's official connector (https://api.suno.com/mcp).
- **You** choose five things: the hook, the sound, her look, the song take and the photos. You never write a prompt. Nothing is posted by the bot.

## What it costs you
- Grok Bot: included in an X plan that has Grok Bot. Photos, clips and the edit use that plan's usage.
- Suno: your plan's credits, about 10 credits per song round (2 takes); the bot asks before each round. Free Suno songs are non-commercial.

## Install
Add the KLAUDIA BOT to your Grok Bot from its link, and say **set me up**. Later, say **update** to get the newest version.
Manual: `git clone https://github.com/isidoro4/klaudia-bot /workspace/klaudia-bot && python3 -m pip install --user pillow imageio-ffmpeg`.

## Files
| | |
|---|---|
| `skills/` | the Grok Bot skills: welcome, setup, news, sponsorship, music video, song, shots, edit, update |
| `kit/klaudia.json` | who she is and the text that keeps her face |
| `kit/sounds.json`, `kit/looks.json` | the menus of sounds and outfits |
| `kit/lyrics-template.md`, `sponsorship-template.md`, `musicvideo-template.md` | the moulds for each kind of video |
| `refs/` | her reference images (for this kit only) |
| `bin/klaudia_edit.py` | the edit: song + timed lyrics + clips → 9:16 or 16:9 video |
| `RULES.md` | what you can and can't make |

## Credit
Post with "fan-made with KLAUDIA BOT · made with AI". Klaudia's name, look and images belong to her creator: use them for fan videos made with this kit, never as official content and never to promote a coin or token.
The edit uses the Anton font (SIL Open Font License, see `fonts/`).
