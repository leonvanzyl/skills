# The stranger test

The thumbnail version of re-transcribing a finished cut: someone who knows nothing about the video sees exactly what a viewer sees (the title next to the thumbnail) and says what they think the video is about. If that doesn't match the video's promise, the thumbnail fails, however good it looks. You can't run it on yourself: you know the video. A fresh subagent can.

Run it twice:
- **Before rendering**, on plain descriptions of the concepts. It's cheap, and it kills off-topic concepts before they cost renders.
- **After rendering**, on the actual images at feed size.

## How to run it
- Spawn ONE fresh subagent (general-purpose) per test. Give it only what's below. Never the transcript, the brief, the concepts' reasoning or the research: anything more than a viewer sees spoils the test.
- Each item is labelled with its variant id only (A, B, C…), never with the concept's name or mechanic.
- Record the answers in `qa/stranger_pre.json` and `qa/stranger_post.json` (format below). `report.py` shows them on each variant's card.
- Judge each answer against the promise in `brief.md`:
  - **PASS:** its "about" names the video's real subject and payoff (for example: "his AI coding agents work as little characters in a 3D office game").
  - **FAIL:** it names something else ("a mobile game", "a Claude vs ChatGPT comparison") or can't tell.
  - A PASS with click interest of 2 or less is weak; rework it if a spare is stronger.

## Prompt: before rendering
```
You are a YouTube viewer scrolling your home feed. You know nothing about these videos beyond what's below.
For each item you get a video title and a description of its thumbnail. Judge each item on its own.

<for each concept>
Item <id>
Title: <the title this concept pairs with>
Thumbnail: <one plain paragraph: what is in the picture, where, what the words say. No reasoning, no mechanic names.>
</for each>

For each item answer, in JSON:
{"<id>": {"about": "what you think this video is about, in one sentence",
          "expect": "what you expect to see or get if you click",
          "click": 1-5 (how much you'd want to click),
          "confusing": "anything that doesn't fit, or makes the title and picture point at different things (or empty)"}}
```

## Prompt: after rendering
Make one image per variant first: the thumbnail at 480 px wide with its title typed underneath, the way a feed shows it (`qa.py card <out.png> <thumbnail> --title "<title>"`, or any equivalent). Attach those images. Then:
```
You are a YouTube viewer scrolling your home feed. You know nothing about these videos.
Each attached image is one video as it appears in the feed: the thumbnail and its title.
Look at each one on its own and answer, in JSON:
{"<id>": {"about": "what you think this video is about, in one sentence",
          "expect": "what you expect to see or get if you click",
          "click": 1-5,
          "first_noticed": "the first thing your eye went to",
          "confusing": "anything that doesn't fit (or empty)"}}
```

## qa/stranger_post.json
Key it by the deliverable file stem, so `report.py` can match it to its card:
```json
{"A_boring-split": {"title": "...", "about": "...", "expect": "...", "click": 4, "first_noticed": "...",
                    "confusing": "", "verdict": "PASS", "judged_against": "the promise in brief.md"}}
```
`qa/stranger_pre.json` uses the concept ids (`v1`, `v2`…) as keys, with the same fields.
