---
name: klaudia-shots
description: Use when klaudia-news needs Klaudia's photos or clips, or the person asks for a photo or a clip of Klaudia. Makes them with this bot's own Grok Imagine from her reference images.
---

# Photos and clips — your own Grok Imagine

Klaudia's reference images: /workspace/klaudia-bot/refs/klaudia-face.jpg and klaudia-sheet.jpg (the robots: rb1-robots.jpg). They go with EVERY still that shows her. Text pieces: kit/klaudia.json and the chosen look in kit/looks.json.

## A still (9:16, vertical)
**With OPENROUTER_API_KEY set (always for a sung video):** make the stills of HER with /workspace/klaudia-bot/bin/klaudia_photo.py (Nano Banana Pro, about $0.14 each, one at a time; stop and say so if one costs over $0.20), with the two Klaudia images as --refs; once one is right, make the others as edits of it. Stills without her (the robots, a place) can stay on Grok Imagine. Show the price of the batch first and wait for the yes.
**Without the key:** your own Grok Imagine, as below.
Prompt, in this order, one paragraph: identity (kit/klaudia.json "identity") · the look's text · the shot (framing, what she does, her expression: deadpan, eyes open) · the place in one line · photo_end.
References: the two Klaudia images (plus the robots image when they are in the shot). Never a photo of a real person; never a photo from the internet.
Save as photos/NN-name.png. When one photo of her comes out right, make the next ones as edits of THAT photo when the place is the same (it keeps her face).

## A clip (5–6 s, 720p, from a still)
First frame: the chosen still. Prompt, short prose (60–120 words): what she does second by second in plain words (one action), the camera in one line ("static camera" unless the shot needs a move), "keep her face, hair and clothes exactly as in the first frame", "no text on screen". If she SPEAKS in the shot, write the words in quotes (your video tool gives her a voice and moves her lips with it). Never make a SINGING shot here: her lips would not match the song. Singing shots: skill klaudia-lipsync.
Always ask for 720p. Save as clips/NN-name.mp4. Check its size with ffprobe; below 720 on the short side: once more.

## When it goes wrong
- Not her face: once more with "exactly the face of the close-up reference"; then use the best one and say so.
- Declined by the content filter: never edit the picture or the wording to get through; tell the person and offer another shot.
- A limit or an error: say it plainly; never loop.
After the first still and the first clip that worked, write one memory note: which tool settings worked. Use it next time.
