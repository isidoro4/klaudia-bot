# Changelog

## 0.7.0 (beta) — new skills: klaudia-style, klaudia-feat, klaudia-resume (update saves them)
**Fixes from the PROTEIN BY PROMPT video**
- Lip sync on time: a sung take is placed by the song's own clock (clips/NN-sung.sync.json). 0.6 added the 0.7 s lead twice. Checked frame by frame: 0 frames off.
- The lyrics no longer get lost or glued: every line is found by its letters only (broken Suno pieces are fine), lines not found are timed from their neighbours, and all the words go on screen as ONE layer, never two phrases on top of each other.
- Short sung takes: 2–5 s, only her own words (HeyGen answered 402 "weight_exceeds_budget" at 8 s). The vocal window accepts under 4 s.
- The voice goes straight to a temporary link (deleted within an hour): no tunnel to install; the tunnel's address is read correctly if someone still uses it.
- The OpenRouter balance is checked before every paid batch: it stops and says how much to add, instead of a 402 halfway.
- Stills are saved at exactly 720×1280 / 1280×720 for Grok Imagine (plus the big one for the thumbnail).
- New: the lip sync of every take is MEASURED (klaudia_sync.py: good · shift · drift · bad) and the board says where to cut before it drifts.

**Klaudia always looks like Klaudia**
- Stills with NUMBERED references and their job: image 1 = her face sheet (who she is), image 2 = her clothes (cropped without the face), image 3 = the style. Her identity text word for word in every prompt.
- Every still is reviewed before you see it: free checks (size, one face, face big enough to sing) + a fixed list read by a vision model (about $0.003), with her face sheet beside it.
- Rule: never a still of her from text only to get past a filter.

**Choose with pictures, not text**
- Numbered sheets: WHICH KLAUDIA? (body) · THE COLOUR · THE WORDS · THE FRAME · graphics; 🔄 more options · ✍️ my own. Dress her: roles, looks, or your own outfit.

**The board and the look**
- Klaudia's News has a FIXED board of 7 shots (hook sung · fact · dance · fact · chorus sung · dance · punchline sung); long parts split themselves.
- Style frames: the finished look as still pictures, with the words, the graphic and the colour, before anything is paid.
- Graphics that explain a line as an object: ticket, counter, meter, stamp, price tag, clock, chart, notification, headline — placed away from her eyes and mouth.
- A frame per format: TV news (bug, LIVE, BREAKING band), clean music video, "unpaid · not affiliated" ad. Four lyric styles (subtitles, karaoke, giant word, caption). One colour for every shot.
- Every video vertical AND 16:9 (--also); the thumbnail (YouTube, X, vertical cover) and the post are made while the clips are.
- All sung takes in one go, in parallel, after one yes.

**Less Grok usage**
- One chat per video: the state lives in the folder (state.json); "continue" in a new chat picks it up. Short replies, pictures instead of paragraphs, never "say continue".

**➕ feat.**
- Claudia from her public canon at claudia.gallery (read fresh, nothing of hers stored here), or your own character with a test face sheet you approve. Never a real person.

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
