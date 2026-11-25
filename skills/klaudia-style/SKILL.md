---
name: klaudia-style
description: Use when the person chooses how the video looks — colour, the words on screen, the frame (news / music video / ad), Klaudia's body or outfit, the graphics — or says "more options" or "my own". Every choice is a numbered picture sheet and a number, never a paragraph.
---

# Style — pick by number

Sheets kept in the kit (free): sheets/bodies.png (WHICH KLAUDIA?) · sheets/grades.jpg (THE COLOUR) · sheets/words.jpg (THE WORDS) · sheets/looks.jpg (THE FRAME) · sheets/graphics.jpg. Send the sheet, ask "Which one? (number)", buttons with the numbers + **🔄 more options** + **✍️ my own**. Write the answer into board.json "style" (look, lyrics, grade) or state.json (body, role, outfit).

- **With her real photo** (better, still free): once the first still exists, remake the sheet on it: `klaudia_sheet.py grades --photo photos/01.png --out grades.png`, `… words --photo photos/01.png --line "<a line of the song>" --out words.png`, `… looks --photo photos/01.png --title "<title>" --out looks.png`.
- **The body**: 1 · 2 · 3 or "as she is" (kit/bodies.json). Same face, same streak. A game of the brand, never a joke about bodies.
- **Viste a Klaudia (outfit)**: a role from kit/roles.json brings its clothes; or kit/looks.json; 🔄 more options = 3 stills of her in 3 new outfits that fit the story (one yes: about $0.45), shown as one sheet `klaudia_sheet.py pick --title "DRESS HER" --foot "Same face. Same streak. You pick the clothes."`; ✍️ my own = they describe it or send a photo of clothes (never a real person's face: crop to the clothes) → 3 stills → pick → `klaudia_photo.py outfit` makes image 2 for the whole video.
- **🔄 more options** on any sheet: 3 new options (free when they are colour/words/frame; stills cost and ask first).
- **✍️ my own style**: they describe it or send a reference picture (never a real person) → 3 style frames in that style (`klaudia_board.py frames` after setting it) → pick → save it as kit-free text in state.json "my_styles" with a name, to reuse.
- **Graphics**: by default the board gives the fact lines an object (kit/graphics.json). "Fewer graphics" / "none" / "2: a clock" change it by number.
