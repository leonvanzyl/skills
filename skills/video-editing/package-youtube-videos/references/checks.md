# The checks: separate agents that never saw the strategy

Each check is done by a fresh agent on **Opus 5.5 at extra-high effort** that has not read `strategy.md` or the
designers' notes. An agent that knows the reasoning judges the reasoning; these judge the result.

Two rules sit over all of them, because both were broken on the first run:
- **A check counts only for the files it ran on.** If an image or a word changes afterwards, that check is void for it
  until it runs again. The first run inspected the images, then re-rendered every one in the likeness pass, and still
  told Leon they had all passed. Order the work so the last thing that touches an image is followed by an inspection.
- **A check's verdict is a read, not a fact.** Agents here have passed faces Leon rejected, and graded their own work
  as "clearly him". Print what a check found, in its words, as an agent's read. Never as a green tick.

The order: segments (before any concept) -> designs -> promise check and blind read test -> fixes -> promise check
again on anything reworded -> likeness pass (`likeness.md`) -> final inspection -> your own look. Then the page.

## 0. The viewer segments (before any concept exists)
The blind read test needs three or four viewer profiles. If the strategist writes them, the video's pain leaks into
them and the test is rigged (it happened: viewers written with the video's pain tapped it 89% of the time, viewers
written to be bored by it never did). So a separate agent writes them, from the channel alone:

<!-- BEGIN SEGMENTS -->
Write four short profiles of real people who watch a YouTube channel, for a viewer test. You know only this about the
channel: {CHANNEL} (for example: "about 107K subscribers; teaches building software with AI coding agents such as
Claude Code, Codex and Cursor; viewers build real things with these tools every week"). You do not know what the next
video is about, and you must not try to find out: read no files.
Each profile, about 80 words: who they are, what they build and with which tools, how experienced they are, what
their last two weeks of work looked like, and what kinds of video they have clicked on lately. Describe a person and
their week. Do not give them an opinion about any topic, do not make them bored by or keen on anything in particular,
and do not mention debugging, testing or any specific problem unless it is one of many things in their week.
Make them different from each other in experience and in what they build: include at least one professional
engineer, one self-taught builder who ships with AI agents, one beginner, and one viewer who mostly follows AI news.
Write `{WORK}/panel/segments.md`. Reply with the four names and one line each.
<!-- END SEGMENTS -->

## 1. The promise check (does the opening keep the thumbnail's promise?)
Leon raised this himself: a thumbnail the hook and intro don't support is clickbait. One agent, all concepts.
Give it `panel/ours.tsv` (id, title, image path) and the transcript at `video/transcript.txt`.

<!-- BEGIN PROMISE -->
# Promise check: does the video's opening keep the thumbnail's promise?
A thumbnail that wins the click and is not confirmed by the first 30 seconds of the video is clickbait: viewers leave,
and YouTube stops showing the video. Your job is to catch that before upload. Be strict: a finding against the work is
a good result.
Work folder: `{WORK}`. The thumbnails and the title each pairs with are listed in `{OURS}` (id, title, image). Write
only `{EXPECT}` and `{PROMISE}`. Do not open `strategy.md`, earlier results, or anything in `report/`, `qa/` or
`briefs/`: judge these cold.
STEP 1, BLIND. For every thumbnail + title, BEFORE you open the transcript or any other file, as a viewer who just
clicked: (a) the exact words you read on the thumbnail; (b) what do you expect to see or hear in the first 30 seconds?
(c) what is the one specific thing you are now waiting for the video to show you? (d) anything you could misread.
Write `{EXPECT}` and only then go on.
STEP 2, THE VIDEO. Read `video/transcript.txt`. For each thumbnail:
- `hook_line`: the first line that confirms what the thumbnail promised, quoted, with its time. If nothing in the
  first 75 seconds does, say so.
- `payoff_at`: when the specific thing from (c) is actually shown.
- `verdict`: CONFIRMED (the opening says it back within about 30 seconds), CONFIRMED-LATE-PAYOFF (promised in the
  opening, delivered minutes later), LATE (true, but the opening never acknowledges it), or MISMATCH (the video does
  not deliver what the thumbnail implies).
- `risk`: one sentence on what a viewer who clicked would feel at 0:30.
- `overclaim`: any word, number or implication the video does not back, checked against the whole transcript, graded
  NONE / MINOR / MODERATE / SERIOUS with the evidence quoted. Look hard at counts, strong nouns, absolutes, words that
  imply something is new or just happened ("new", "just", "now", "finally"), "free", "full guide", and anything the
  thumbnail presents as found in the wild that the video in fact stages on purpose.
- `fix`: for LATE, MISMATCH or a MODERATE or SERIOUS overclaim, the smallest change to the words that would make it
  honest, or "none: drop it".
- `pairing`: does the title add something the thumbnail does not say, or repeat it?
Judge every title on its own the same way and add a "titles" object. {DOUBTS}
Write `{PROMISE}`. Reply with one line per verdict.
<!-- END PROMISE -->

Put the designers' own doubts in {DOUBTS} for the checker to weigh. Then act on it: fix overclaims in the words (send
the designer the exact change), mark LATE concepts as out of contention for the test trio, drop a MISMATCH. Only
CONFIRMED concepts (or a late payoff the hook explicitly promises) are eligible for the trio.

**Run it again on everything that was reworded.** Any thumbnail or title whose words changed after this check, and any
title added later, goes to a fresh promise checker (new `ours_v2.tsv`, new output files, not shown the first result)
before it can be offered or enter the trio. On the first run "3 APP KILLERS", "MCP SETUP" and four rewritten titles
were offered without this, two of them in the trio. A concept on the page with a verdict from before its rewording
must say so.

## 2. The blind read test (what does a viewer take from it?)
What this test is for: what a viewer expects from each thumbnail before reading the title, which thumbnails need the
title to make sense, and the reasons a viewer gives for tapping or passing. What it is not: a click-through estimate,
or a way to rank the concepts. **Tap counts never appear on the trio cards and are never the reason for the trio.**

It only works if the viewers cannot tell which tiles are being tested. On the first run they could (two of ours on
every sheet, the same man on each, 24 sheets to one agent), and viewers with the problem tapped ours 73 to 90% of the
time against 12 to 15% for real videos on the same sheets. So:
- `scripts/panel.py panel/ours.tsv panel --appear 2 --per 1` builds dark-mode feed sheets in `panel/sheets/`: ONE of
  ours among eleven real current videos from `research/pool.tsv`, numbers under the tiles. The key goes to
  `panel/key.json`, outside the folder the viewers open.
- **Each viewer agent reads at most six sheets** (`{SHEETS}`), so the same face does not come round dozens of times.
  Run several agents per segment rather than giving one agent every sheet.
- Use the profiles in `panel/segments.md` (section 0), unchanged.
- `scripts/tally.py` reports, per viewer, how often ours were tapped against how often real videos on the same sheets
  were tapped. **If ours are tapped at more than about twice the real rate, the viewers probably spotted the test
  items: discard the taps and keep only the reads.** Say so on the page.
- Simulated viewers reward what is easy to read, and they are not his audience. Say that on the page too.

<!-- BEGIN VIEWER -->
# Feed test: you are one YouTube viewer
You are simulating one specific person scrolling YouTube. Your persona is in the message that sent you here. Stay in
that person's head: what they know, what they want this week, what they are tired of seeing.
Work folder: `{WORK}`. Open ONLY these files: {SHEETS} (Read each, one at a time, and answer for it before the next).
Do not open anything else.
Each sheet is a YouTube home feed in dark mode: 12 tiles, each a thumbnail with its number and title under it.
For each sheet: (1) which tiles, if any, would you tap, in order, deciding from the thumbnail first and the title
second? Most tiles in a real feed get scrolled past: tap none, one or two, as this person really would. (2) which
THREE would you scroll past without a second look? (3) for EVERY tile, in eight words or fewer, what do you expect
that video to be? (4) any tile whose thumbnail you could not make sense of without the title; (5) one short reason for
each tap, in the persona's voice.
Write `{OUT}`:
`{"sheet_1": {"tap": [n, ...], "tap_why": ["...", ...], "skip": [n, n, n], "reads": {"1": "...", ...}, "unclear": [n, ...]}, ...}`
(use each sheet's own file name as its key). Reply with one line when the file is written.
<!-- END VIEWER -->

## 3. The final inspection (is it fit to upload?)
One fresh agent, every image that will be delivered, **after the likeness pass and after the logos were re-pasted**:
the files he will upload, not an earlier version. Nothing is called inspected before this has run on the final files.
Give it the list of ids with the portrait each follows.

<!-- BEGIN INSPECT -->
You are the senior retoucher who signs off YouTube thumbnails before upload. Find every flaw a viewer, the creator or
a designer would notice. Be hard on them; a clean bill of health that turns out wrong is the worst outcome.
Work folder: `{WORK}`. Python: `{PY}` (Pillow installed). Write only inside `qa/final/`. Change nothing in `out/`.
The images: {IMAGES} (full-size originals `out/<id>_full.png`; upload files `out/<id>.jpg`, 1280x720: confirm they
match). References: the creator's two reference portraits `refs/leon/leon_front.jpg` (his smile) and
`refs/leon/leon_serious.png` (his serious look), and the official marks in `refs/logos/`. The intended words for each
image: {WORDS}.
For EACH image: Read the full-size PNG whole. Then make and Read close-up crops at native pixels or 2x, never shrunk
(keep each crop under 2000 px on its longest side so it is not downscaled when you view it): his face; hairline, ears
and shoulders against the ground; every block of text; every logo beside a same-size crop of the official mark; every
object; the bottom-right 18% x 16% corner. `{PY} {SKILL}/scripts/tools.py face out/<id>_full.png qa/final/face_<id>.jpg
--ref smile|serious` puts his face at native pixels beside the matching portrait. Report only what you can see in a
crop, and say where:
- LIKENESS, as a careful read and not a verdict (the creator is the judge, and an earlier inspector passed faces he
  rejected): feature by feature against the matching portrait: face shape and width, lower-face length, eye shape and
  openness, lids, brows (position, angle, furrow), nose, mouth and smile size, teeth, moustache and goatee, skin tone,
  apparent age. Say which features differ and by how much. Rank the set from closest to furthest and name the ones
  you think he would reject.
- EXPRESSION AND EYE-LINE: eyes into the lens; only the smile or the serious look of the portraits, no stronger.
- SKIN AND EDGES: plastic, waxy, painted, swirled or crackled texture; over-sharpening; a halo, cut-out line, glow, rim
  or colour wash on him; stray specks in the hair.
- TEXT: every letter correct and crisp; apostrophes and punctuation; malformed letterforms.
- LOGOS: shape (number, length and thickness of rays) and colour against the official mark, measured. Say whether each
  is the official mark or the model's drawing.
- OBJECTS: hands, handles, glass, screens: anything malformed, duplicated or impossible; garbled pseudo-text.
- COMPOSITION: anything under the duration badge; anything cramped or jammed against an edge or another element (give
  the gap in pixels); anything cut off.
- MISREADS: any wording or mark that can be read another way.
- FEED SIZE: downscale to 168 px wide: what stops being readable?
Grade each flaw BLOCKER (a viewer or the creator would notice at normal size), MAJOR (a designer would fix it) or MINOR
(only at 2x), and give the exact fix as an instruction for an art director directing an image model. Note anything
that repeats across the set. Never recommend pasting, blending, warping, healing or otherwise changing his face, hair
or body by script: anything on him is fixed by the image model with his portraits. An official logo may be pasted.
Write `qa/final/qa_final.json`: `{"<id>": {"likeness_read": "...", "differs": ["feature: how"], "expression_ok": bool,
"flaws": [{"what", "where", "severity", "fix"}], "worst": "one line", "matches_jpg": bool}, ...,
"_ranking_closest_to_furthest": [...], "_would_reject": [...], "_repeats_across_set": [...]}`. Reply in 20 lines at
most.
<!-- END INSPECT -->

Then act on it and look yourself:
- A BLOCKER or MAJOR on a logo: paste the official mark (`tools.py logo ... --clear`), look at it at 3x with its
  neighbours, and re-export. Then prove the rest of the image is untouched (compare the new file with the inspected
  one: no pixel outside the logo box may differ) and say on the page that the logo was replaced after the inspection.
  That is the one change that does not need the inspection run again.
- A BLOCKER on his face or expression: one more likeness round for that image with the inspector's notes written into
  the prompt, then this inspection again on the new file, by a fresh agent that is not shown the earlier verdict.
- Anything else: an image-model edit by the concept's designer, then the likeness pass and this inspection again.
- The inspector's "would reject" list is a reason to look harder and to tell Leon, not a reason to drop a concept.
- Open every `out/<id>_full.png` whole, and its native face sheet, yourself. Write down what you see that differs from
  the portrait; that sentence goes on the page. If you did not open a file, do not say you looked at it.
- The inspector's likeness read is a filter. Leon is the judge (`leon.md`).
