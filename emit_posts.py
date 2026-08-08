#!/usr/bin/env python3
"""Generate posts.json (ordered posting queue) from the render caption bank.
Each entry: {"file": "NNN_tone.mp4", "caption": "...with hashtags..."}.
Themes interleaved (same permutation as the render schedule). Run once."""
import json, os, sys

RENDER = "/Users/apple/Desktop/outbed_content/render"
sys.path.insert(0, RENDER)
import render_batch as rb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LINK = "link in bio"
EMOJI = {"rage": "😤", "shock": "😱", "sad": "😭", "facepalm": "🤦",
         "smug": "😎", "win": "🔥", "evil": "😈", "annoyed": "😑"}
CTAS = [
    f"⏰ Outbed — the alarm you literally can't ignore. {LINK}.",
    f"No snooze. No excuses. Get Outbed → {LINK}.",
    f"Pay once, wake up on time forever. Outbed → {LINK}.",
]
HASHTAGS = [
    "#outbed #alarmapp #wakeupchallenge #nomoresnooze #morningroutine #5amclub #earlyriser #productivity #memes #relatable #reels #fyp",
    "#outbed #alarmclock #cantoversleep #wakeupearly #morningmotivation #disciplineovermotivation #selfimprovement #funnyvideos #dankmemes #reelsinstagram #viral #trending",
    "#outbed #snoozebutton #morningperson #riseandgrind #habits #productivitytips #comedy #meme #relatablememes #explorepage #reelitfeelit #fyp",
    "#outbed #oversleeping #alarm #wakeup #grindmode #6amclub #lifehacks #funny #memepage #viralreels #trendingreels #instareels",
]

n = len(rb.BANK)
perm = sorted(range(n), key=lambda i: (i * 37) % n)  # decorrelate themes
posts = []
for order, i in enumerate(perm):
    line, tone = rb.BANK[i]
    caption = f"{EMOJI.get(tone,'⏰')} {line}\n\n{CTAS[order%len(CTAS)]}\n\n{HASHTAGS[order%len(HASHTAGS)]}"
    posts.append({"file": f"{i+1:03d}_{tone}.mp4", "caption": caption})

with open(os.path.join(HERE, "posts.json"), "w") as f:
    json.dump(posts, f, ensure_ascii=False, indent=2)
with open(os.path.join(HERE, "state.json"), "w") as f:
    json.dump({"next": 0}, f, indent=2)
print(f"wrote posts.json ({len(posts)} posts) + state.json")
