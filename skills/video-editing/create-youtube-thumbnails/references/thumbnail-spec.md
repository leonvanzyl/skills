# Thumbnail spec (the quality contract)

This is the complete creative and technical spec behind the thumbnails. Every rule here was set by research on real outliers or proven on real renders. Follow all of it; don't skip a step to save time (speed comes from parallel research and parallel renders, never from cutting corners). Where the user's request says something different, the user wins.

You're designing the thumbnails for my YouTube video. Understand exactly what my video is about and what my title promises. Research what wins in my niche and on my own channel. Then, for each variant, take one proven outlier thumbnail and re-make it faithfully for my video: its layout, background, palette, type and treatment, with me, my words and my video's real payoff in it. Prove every render against its reference, the video and the title, and hand me the finished variants to A/B test.

THE THREE THINGS THAT MATTER MOST (every past failure broke one of these)
1. Honour the video. Every thumbnail shows what the video actually shows: its payoff, from the video itself. An invented prop (a phone game, a brain, logo tiles standing in for "coworkers") makes a thumbnail about something else.
2. Honour the title. The title states the claim and the thumbnail shows it. A stranger who sees only the two together must be able to say what the video is about.
3. Honour the reference. The image model follows the brief's words over the attached image, so the brief copies the reference's background, palette, subject treatment (for example a white cut-out outline), type style and composition, measured and written down. Inventing a background colour "to make the variant different" produced blue and red eyesores where the reference was black.

ASK ONCE, THEN WORK FULLY AUTONOMOUSLY
- Ask me exactly one thing before you start: how many variants to make (suggest 3, the number YouTube's Test & Compare takes at once). Skip the question if I already said a number.
- After that, don't ask me anything. Run every step, start to finish, and finish with the variants and the report.
- Every judgement call (which concepts, which words, a claim the video doesn't quite back up, a logo you can't find) is yours. Make the best call, keep going, and log it in the report.
- If something fails, try another way (another tool, model or fallback) rather than stopping.
- Only stop early if there is no way to learn what the video is about.

INPUTS (any one of these is enough)
- A YouTube URL: pull the title, description, chapters and full transcript with VidIQ (`vidiq_get_videos_by_ids`, `vidiq_video_transcript`).
- A transcript, script, recording or outline: read it in full. For a recording with no transcript, transcribe it (the create-video-shorts transcriber works).
- Just the idea and the hook: the normal case for a video that isn't recorded yet. Work from the promise and the hook as given, and keep every thumbnail claim inside them.
Also:
- The title, or the title candidates. If there is none, write one (section 9).
- My photos: the avatar folder in the brand folder (see SKILL.md). One clear front-facing photo is enough; more angles and expressions are better.
- My brand file (`brand.md` in the brand folder): my likeness words, my face rules and what has worked on my channel. Read it first. Refresh it after the research, so the next run starts smarter.
- My channel: to read what my audience clicks.

1. UNDERSTAND THE VIDEO AND THE TITLE
- Read the whole transcript. Write down, in the run's `brief.md`:
  - the promise in one sentence (what the viewer gets)
  - the payoff moment: the one thing on screen that proves the promise. Grab real frames of it from the recording, or captures of the real product or result, into `refs/ui/`. These are the heroes the concepts draw from.
  - the villain or old way the video argues against, if any
  - every named product, tool, brand and number
  - every claim a thumbnail could make, each with the transcript line that backs it
- For each title (or title candidate), write THE PICTURE OF THE TITLE: the one image a viewer must see to believe that title in a second. It always comes from the payoff. Example: "I Turned My AI Coding Agents Into a Video Game" is pictured by the cartoon 3D office with the little agent-workers at their desks and live terminals on their screens, not by a phone game or two logos.
- A thumbnail claim the video doesn't back up is never allowed: no invented numbers, timestamps, results, features or brands.

2. RESEARCH (parallel subagents, started at the same time; see research.md)
- Niche: outliers (videos far above their channel's normal views) for the topic's search terms in the last 6-12 months, similar videos and similar thumbnails to mine, and keyword volume and competition. Download every thumbnail, build labelled contact sheets at full and mobile size, and LOOK at them.
- My channel: my top performers and my last 12 uploads, and which of my thumbnails over- and under-performed, and why.
- Assets: the official logo of every product the concept may show (transparent PNG, never redrawn), and real UI captures where a product screen appears. Look at each one.
- The research writes `research/niche.md`: niche winners (one line each), the rules that separate outliers from average videos, what is saturated, keyword data, and concept directions.
- THE REFERENCE RULE: every thumbnail the image model is shown as a reference (the competitor LAYOUT REFERENCE and my own HOUSE STYLE thumbnail) comes from a video with at least 100,000 views. Among those, prefer the highest breakout. A huge breakout on a tiny channel (53k views on 539 subscribers) is interesting research, but it is not a reference. Also drop anything with engagement under 1% (likes / views): that's paid reach, not an outlier. `gen.py` refuses to render a job that breaks this rule.

3. CONCEPTS
A concept is: a title it pairs with, a hero from the video, and an eligible outlier whose whole look it re-makes. Write one per variant I asked for, plus one or two spares, into `concepts.json` (the fields are in pipeline.md).
- THE HERO COMES FROM THE VIDEO. It is the payoff, or a real part of it: a frame of the recording, the real product UI, the real result, a real number or claim from the transcript. If you would have to invent the hero, the concept is rejected. That covers a phone game, a brain, a robot, a generic object, or logo tiles standing in for something the video doesn't show. Logos are the hero only when the video is about those tools; otherwise they are a small supporting cue at most.
- EACH CONCEPT PAIRS WITH ONE TITLE (`title` field) and tells the same story: the title states the claim, the thumbnail shows it, and the text adds the hook the picture can't (a number, a result, a reaction or a short label). Read the two together. If they point at different things, the concept fails.
- VARIANTS DIFFER IN ANGLE, NEVER IN SUBJECT. All of them show my video. They differ in:
  - which part of the payoff they show (for example: the floor of agent-workers, the CEO agent on the phone, the whiteboard of real pull requests)
  - which hook the text adds (a number, a contrast with the old way, a reaction)
  - which reference they re-make
  Palettes differ only because their references differ. Never invent a background or palette to make variants look different.
- PICK A REFERENCE THAT FITS THE HERO. A scene hero (a world, a screen, a product in use) needs a reference built around a scene or a big screen. A logo-tile layout fits only a logo hero. Name the reference file and why its layout fits (`borrows`).
- THE STRANGER TEST, BEFORE RENDERING (review.md): a fresh subagent reads only each concept's title and a plain description of the thumbnail, and says what it thinks the video is about and whether it would click. Drop or rework every concept it gets wrong. Don't fill the variant count with weak or off-topic ideas: if you can find fewer strong angles than I asked for, deliver fewer and tell me why.
- Rank them by how clearly and strongly they sell the title.

4. THE THUMBNAIL RULES
Canvas: 16:9, delivered at 1280x720. Positions are in % of the frame.
- One idea, readable in one second. At most three things: my face, one hero, and the text. One small chip (a check, a number, an X) is allowed on top.
- THE REFERENCE DECIDES THE LOOK. The background (colour and value), the palette, the type style (font class, case, colours, stroke, highlight boxes, underline), the subject treatment (a white cut-out outline, a rim light, a drop shadow), the hero treatment (tilted tiles held in both hands, a giant screen, a scene behind me) and the composition grid all come from the LAYOUT REFERENCE, measured with `dna.py` and written into the brief. Change only: the person (me), the words, the hero content, and the logos. If the reference cuts its creator out with a white outline, I get the same outline. If its background is near-black, mine is near-black.
- My face is in every variant unless I ask otherwise. Prefer references with a person in them. A faceless reference can be used only if its layout has a natural place for me, and the brief must say exactly where.
- My face:
  - placed and sized like the reference's person (on its third, at its scale); eyes in the top 45% of the frame
  - my eyes look straight into the lens in every thumbnail, never at the object and never sideways. Look-away thumbnails under-perform, and nearly every top outlier in the niche holds eye contact.
  - my expression is subtle and matches the angle. Never a gasp, an open-mouthed shock or anything goofy:
    - a confident, knowing half-smirk for "this beats that"
    - serious and calm, or a slight frown, for a contrarian statement
    - one slightly raised eyebrow for skeptical
    - a calm, satisfied closed-mouth smile for a payoff
    - pointing at the hero is fine, with my eyes still on the lens
    Describe it as muscle movements in the brief (prompting.md).
- Text:
  - 1-4 words, 3 or fewer preferred. No text is better than vague text.
  - about the same thing as the title. It never restates the whole title, but it may reuse the title's key noun when that's the hook. It adds what the title doesn't: the number, the result, the reaction.
  - set in the reference's type style and position, with a cap height of at least 12% of the frame height. If the reference's text is smaller than that, pick a reference with bigger type rather than shrinking the text.
  - readable: every text colour has at least 3:1 contrast with what's behind it (4.5:1 without a stroke or shadow). `gen.py --check` measures it from the brief's hex values.
  - never over my face, never in the duration-badge zone
- Logos:
  - official marks from `refs/` only, never drawn from memory
  - at most two
  - at least 7% of the frame height inside a card, 15% standalone
  - The sponsor's logo stays off unless the sponsor deal requires it, or the sponsor is a brand my viewers would recognise.
- Product UI and the video's world: from real frames or captures (`refs/ui/`), simplified and oversized. Big shapes and a few large words only; small text becomes clean grey bars, never gibberish.
- Avoid the niche's saturated concepts (listed in `niche.md`). An abstract metaphor (a brain, a network, a cloud of particles) is never the hero; show the real thing.
- Keep clear:
  - the bottom-right 18% x 15% (the duration badge)
  - the outer 4% on every side

5. RENDER: RE-MAKE THE REFERENCE, WITH THE MODEL SEEING EVERYTHING
- REFERENCE DNA first, for every layout reference (pipeline.md):
  - `dna.py measure` records its background colour and value, whether it's a flat field or a scene, and its palette.
  - Then LOOK at it and write down the rest: the subject treatment (outline, rim light, shadow), the type style (font class, case, colours, stroke, boxes), the hero treatment and the composition grid (where the face, hero and text sit and how big each is). This goes in `concepts.json` (`dna`).
- Every brief has a REFERENCE DNA paragraph that carries all of that, and its own BACKGROUND, TEXT and PERSON sections agree with it, using the measured hex values. `gen.py --check` rejects a brief whose background drifts from the reference or whose text contrast is too low.
- Codex's image tool takes at most 5 attached images per job (more fails silently; `gen.py --check` blocks it). If a concept needs more, merge its logos into one PNG or drop the HOUSE STYLE reference.
- Every job attaches, with labels: my photo (AVATAR), the official logo(s) the concept shows (LOGO), the LAYOUT REFERENCE, one of my own top performers for how I'm photographed (HOUSE STYLE), and the real frame or capture of the hero (UI) when the hero is a scene, a screen or the product.
- Write one brief per concept in `prompts/` following prompting.md. Shared wording lives in `prompts/_common.md`.
- Render every concept at once with `scripts/gen.py`, spares included, two renders each, and keep the better one. Deliver only the number of variants I asked for. The spares stay in `out/`, are named in the report, and step in if a variant fails QA.
- Stamp the official logo over the model's version with `scripts/stamp.py`. The model redraws logos even when it's given the file: ray counts, thickness and proportions drift.
- Fix with edit passes, one or two changes per pass, never by re-rolling a good image.

6. PROVE IT (QA, every candidate, before anything is called done)
LOOK at each of these. One failure means an edit pass or a re-render:
0. Reference fidelity:
   - `dna.py fidelity <render> <reference>` must say PASS or WARN. A FAIL means the background value or colour left the reference's: re-render, or edit the background back.
   - Then LOOK at the two side by side (`qa.py compare`): same composition, same subject treatment (outline, rim light), same type style. It should look like the reference re-made for my video, and still clearly my own video.
1. The stranger test after rendering (review.md): a fresh subagent sees only each thumbnail next to its title and says what the video is about. Its answer must match the promise. A miss means the concept failed, not the render: rework it.
2. Text: every letter is correct at full resolution, the words are exactly the brief's, and they read against the background.
3. Likeness, gaze and expression (`qa.py faces`): side by side with my photo, it's unmistakably me (face shape, hair, beard, eyes, skin and age). My eyes are on the lens, and the expression is subtle.
4. Logos: after `stamp.py`, the official mark sits where the model put its version, at the same size, with no halo or leftover rays.
5. Anatomy: hands have five fingers and the face, teeth and ears look natural. No melted detail.
6. Size ladder (`qa.py ladder`):
   - at 246 px (mobile feed), the idea reads
   - at 168 px (sidebar), my face and the text still read
   - in greyscale, the subject separates from the background
7. Feed test (`qa.py feed`): dropped among real niche thumbnails at real size, it is the first thing the eye lands on.
8. Badge zone and edges are clear.
Write the results as a table in the report. Score each candidate 1-5 on how clearly it sells the title, stop power, clarity at 246 px and honesty.

7. DELIVERABLES (in `thumbnails/`)
- One file per variant I asked for, `A_<slug>.jpg`, `B_<slug>.jpg` and so on (`qa.py norm`): 1280x720 JPEG under 2 MB, plus `*_master.png` at 1920x1080. Rank them; A is your pick. With more than 3, suggest which 3 to test first (Test & Compare takes 3 at a time).
- `report.html` (`scripts/report.py`), every time: a self-contained page I can open in any browser. It shows where every decision came from:
  - each variant next to the competitor outlier it re-made (channel, subscribers, views, breakout and a link) and my own house-style thumbnail
  - the title it pairs with, and what the stranger test said it was about
  - the reference fidelity: the measured background and palette of the reference and the render, and the verdict
  - the reasoning and the claims behind each variant
  - the exact chain that made it: render, edits, logo stamps, delivery
  - the brief sent to the image model
  - the whole research pool, with the 100,000-view eligibility marked
  It is built from the run's records, never typed by hand, so it can't drift from what actually happened.
- `report.md` (section 8).
- `PUBLISH.md`, only if you suggest a title change (section 9).

8. REPORT (`report.md`)
- The video: the promise, the payoff, the picture of each title, the villain, and the claims with their transcript lines.
- Research: the numbers (outliers with breakout scores, saturation, keywords) and the sheets used.
- The concepts: the title each pairs with, the hero and where it came from in the video, the reference and why its layout fits, the stranger test answers, and the brief file.
- QA: the table, the fidelity verdicts, every edit pass and why, and every rejected concept or render and why.
- The variants with the ranking and the reasoning, and what each A/B result will tell me.
- Every judgement call.

9. TITLE
If my title leaves out the search term or doesn't match what the video delivers, suggest up to two titles of 60 characters or fewer, with the main search term first. Use the keyword data, back every claim with the video, and use no emojis. The title and the thumbnail must tell one story.
