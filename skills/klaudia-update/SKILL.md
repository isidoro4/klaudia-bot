---
name: klaudia-update
description: Use when the person says update, or a KLAUDIA script fails because a file is missing. Pulls the newest KLAUDIA kit.
---

# Update
No .git in /workspace/klaudia-bot (an old zip install): run skill klaudia-setup step 1 first. Then run `git -C /workspace/klaudia-bot pull -q && python3 -m pip install -q --user pillow imageio-ffmpeg numpy "opencv-python-headless<5" && echo UPDATED` (no clone yet: skill klaudia-setup, step 1).
Then read /workspace/klaudia-bot/CHANGELOG.md and tell the person, in one or two lines, what is new since last time.
If the template's own skills changed (the changelog says so), tell them: "Re-add the KLAUDIA BOT from its link to get the new steps."
If a skill named in the changelog is missing from this bot (0.7 added klaudia-style, klaudia-feat, klaudia-resume), save each missing skills/<name>/SKILL.md as a skill with that exact name and text.
