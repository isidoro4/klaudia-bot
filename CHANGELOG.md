# Changelog

## 0.6.0 (beta)
- The board (skill klaudia-board, bin/klaudia_board.py): every shot numbered with its seconds, line and kind, as one image, plus a free preview with photos; change it by number ("3: she dances") or with buttons (More dancing · Faster cuts · More close-ups); one yes for all the clips, made in parallel.
- The Klaudia recipe by default: sung hook in close-up, dancing on every gap without voice (max 2 s a shot), sung punchline. Klaudia never sings the choir's lines.
- Dance menu (kit/dances.json: stomp, go-go, jumps, spins, Berghain head, robots) and faster dances in the edit ("speed": 1.5).
- The edit reads the board: klaudia_edit.py --board board.json.

## 0.5.0 (beta)
- Singing shots now use HeyGen Avatar IV on OpenRouter by default (same key, $0.05 a second): it animates the shot's own still to sing the vocal. Seedance refused Klaudia's face reference as "may be a real person"; it stays as an option, without the face reference.
- One button for the singing shots and their price; no model menu.

## 0.4.0 (beta)
- Lip sync fixed for Grok Bot's computer: the tunnel now runs over http2, and where it is still blocked each vocal snippet goes to a temporary host that deletes it within an hour (the bot says so first).
- Singing shots default to the cheap Seedance mini, with the price per shot shown first.

## 0.3.0 (beta)
- Pick your Klaudia: choose who she is in your video (news anchor, athlete, architect, astronaut, 1950s singer, CEO, chef, scientist, DJ, detective, or type a job). She is always herself; the role changes her clothes and her world.

## 0.2.0 (draft, not published)
- Sung videos need an OpenRouter key: Klaudia's photos with Nano Banana Pro (bin/klaudia_photo.py) and her singing shots with Seedance from the song's own vocal (skill klaudia-lipsync, bin/klaudia_sing.py), the same method as the Claudia bot. Without the key, no sung videos. The edit takes clip@seconds and "+".
- Rules: news ABOUT prediction markets, crypto, stocks or companies is allowed, told as news; never their ad (no bonuses, codes, links, "bet/buy/trade"), no price tips, never the coin named after Klaudia.

## 0.1.0
- First version: welcome, setup (kit + Suno connector), KLAUDIA'S NEWS recipe with five choices, song on Suno, photos and clips with Grok Imagine, edit with lyrics on screen and the fan-made end card.
- Unpaid sponsorship (vertical) and My song with Klaudia (horizontal music video, 1–3 min). The edit makes 16:9 too, cuts every N lines or every N seconds, and can leave the lyrics off.
