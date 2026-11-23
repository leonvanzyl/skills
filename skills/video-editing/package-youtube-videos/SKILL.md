---
name: package-youtube-videos
description: Package a YouTube video for Leon van Zyl's channel the way a packaging strategist would - the idea, the titles, finished thumbnails with variants, and the plan for testing them - and deliver it as a review page. Starts from the viewer and the video's own hook rather than from a design, researches what separates hits from flops on the same channels (never winners only), has one designer agent per concept art-direct Codex image generation to render each whole thumbnail from Leon's reference portraits, corrects his likeness through Codex, then tries to knock the results down with a promise check against the transcript, a blind read test and an independent inspection of the final files at native size. Use this whenever the user wants a thumbnail, thumbnail concepts or variants, a title or title options, "packaging" for a video, A/B or Test & Compare variants, or a better thumbnail or title for an existing video - even if they only mention one of those and never name a skill.
---

# package-youtube-videos

Package a video for Leon van Zyl's channel: decide what the video is selling and to whom, write the titles, make
thumbnails that each give a different reason to click, check them hard, and hand him a page with three to test and a
plan for testing them.

## How this differs from designing a thumbnail, and why
An earlier skill produced 60 to 70 drafts a video for three barely usable ones, and click-through fell well below
what had been normal. It started from the picture: it measured winning thumbnails and reproduced their look. Five
things were learned replacing it (2026-11-22, on a sponsored product video), and the workflow below is built on them:

1. **Start from the viewer, not the picture.** Title and thumbnail are one package, and the package is an idea: who
   this is for, what they already want or fear, and the change the video delivers. Decide that first, in words.
2. **Topic beats format, so never claim a format wins.** A control study of six large channels found the thumbnail
   formats credited to winners (verdict text, minimal layouts, popular title shapes) just as common on the same
   channels' flops. Studying winners only is the easiest mistake to make here, and VidIQ helps you make it: its
   breakout score was missing for 77 of 88 flops.
3. **A thumbnail's job is narrower and still worth doing well:** be instantly clear to the people the topic is for,
   keep the promise the first 30 seconds make, carry the topic marker, and look like a professional made it.
4. **Let the image model render the whole thumbnail.** One designer per concept writes art direction and Codex image
   generation produces the complete image, type included, from Leon's two reference portraits, in about a minute a
   take. No HTML collage, no pasted cut-out.
5. **Try to knock the work down before he sees it, and believe him over the checks.** Separate agents that never saw
   the strategy test the promise against the transcript, the read in a feed, and the finish at native size. They
   caught real faults. They also passed faces he called terrible. His eye is the standard.

`references/leon.md` holds what he has said, in his words, with where each line comes from. Read it at the start of
every run.

## Rules that are not negotiable
- **Every subagent runs on Opus 5.5 at extra-high effort:** pass `model: "opus"` and `effort: "xhigh"` on every Agent
  call (designers, likeness, checkers, the control analyst). Leon's instruction.
- **No code touches him.** Not his face, hair, neck or body: no paste, blend, warp, scale, move, matte, heal, clone,
  sharpen or retouch by script, by you or by any agent. His likeness is corrected by sending the finished thumbnail
  and his reference portraits to Codex. A scripted face blend was tried and he rejected it outright ("It should
  definitely not be a scripted faceplate. Why on earth would you do that if you've got access to Codex?"). The only
  script allowed to alter pixels of a delivered image is `tools.py logo`, and only on a logo.
- **Nothing with his face reaches a page before the likeness pass, an independent inspection of the final files, and
  your own look at each one at native size.** He was shown broken faces once because a page was published first.
- **The upload files are 3840x2160, every time.** Leon: "We need the 4K versions of the thumbnails every time." It is
  YouTube's recommended thumbnail size. `tools.py finals` makes them from each image's full-size original, so every
  delivered image must have its `out/<id>_full.png`. The image model renders about 1,672 px wide, so the upload file
  is a plain enlargement, not extra detail: say that on the page, and never run an AI upscaler on a thumbnail (it
  redraws his face). The 1280x720 files in `out/` are for the review page and the feed tests, not for upload.
- **Claim only what ran on the final files.** A check that ran on an earlier version of an image is not a check of the
  image he will upload. If an image changes after a check, the check is void for that image until it runs again. Never
  write "I looked at" or "passed" for something done at reduced size or on an earlier file.
- **An agent's pass is a read, not a fact.** Do not print an agent's verdict as a green tick. Likeness is his call.
- **No channel report, no ranking of his own videos, nothing from earlier runs** as evidence or as a source of rules.
  The skill does its own research each time (`references/research.md`). What one run found is a hypothesis for the
  next, not a rule (`references/research.md` keeps them dated and labelled).
- **Honest:** nothing on a thumbnail or in a title that the video does not deliver, and nothing the hook does not
  confirm in the test trio. Any word changed after the promise check goes back through it.
- **Report faithfully,** including what failed and what was not checked. Be as hard on the work as he would be.

## Inputs
- **The video:** the transcript or captions file (required; a link alone works only for a public video, since a private
  or scheduled one cannot be fetched), the video folder if there is one (for real frames), the working title, the
  publish date, and whether it is sponsored and what the sponsor requires.
- **How many:** ten concepts by default. If he asks for three, still write the thirty ideas and cull, render the best
  five (each a different reason to click), run every check, and deliver the three that survive, saying what was cut.
- **Tools:** the VidIQ MCP server (ToolSearch, query `vidiq`); the Codex CLI logged in with image generation; Python
  with Pillow, numpy and OpenCV; a browser or Playwright for one look at the page.
- **The work folder:** next to the video (`<video folder>/packaging-<slug>/`), never inside a code or skills repository.
- Ask before starting only for what cannot be found: the sponsor's requirements, and the last video's test result if
  the ledger lacks it. Otherwise work through to the page, then iterate with him.

## Workflow
`SKILL` is this folder. Run scripts from the work folder with the Python `setup.py` reports.

1. **Set up.** `python SKILL/scripts/setup.py <work>` creates the folders, copies in his reference portraits, the
   official marks and the prompts, and creates the results ledger if it does not exist. Put the transcript in
   `video/transcript.txt`. Read `references/leon.md` and the ledger (`~/.yt-packaging/ledger.md`, see
   `references/test-plan.md`).
2. **Read the video and write the strategy** (`references/strategy.md`): the hook verbatim with times, the honesty
   line, the idea in one sentence, where the search demand is, about thirty ideas in words culled to the number asked
   for, and six to eight titles. Write `strategy.md` yourself. The viewer segments for the blind test are written by a
   separate agent that has not read the transcript (`references/checks.md`), before any concept exists.
3. **Research, in parallel with step 2 and after it** (`references/research.md`): search demand; a pool of 60+ real
   current videos for the feed test; real frames and screens from the video for the designers (`refs/ui/`); and, in the
   background, the control study that tries to falsify whatever your strategy claims about formats.
4. **Calibrate, then design** (`references/designer.md`): run one concept yourself (two takes) so the tools are proven
   and the designers have a working example; then one designer agent per concept, all in parallel. Each delivers a
   finished thumbnail as a 1280x720 review file plus its full-size original (the upload file is made from the
   original in step 9), usually a ground variant, and its own doubts.
5. **Check the designs** (`references/checks.md`), each by a fresh agent that has not read the strategy: the promise
   check against the transcript and the blind read test. Act on them: fix overclaims in the words, drop or flag what
   the hook does not confirm, send each fix to that concept's own designer (image-model edits only). **Every reworded
   thumbnail or title goes back through the promise check** before it can be offered.
6. **Correct likeness through Codex** (`references/likeness.md`) on every image that will be delivered, after all the
   fixes, and re-paste the official logos the designer recorded.
7. **Inspect the final files** (`references/checks.md`, section 3): a fresh agent, every final image, at native
   pixels: likeness against his reference, text, logos against the official mark, artefacts. Then look yourself: open
   each `out/<id>_full.png` whole, and its native-size face sheet. If anything changes after this step, steps 6 and 7
   run again for that image before it is shown.
8. **Choose the three to test and write the test plan** (`references/test-plan.md`): three different reasons to click,
   each confirmed by the hook in its current wording, each with its own title, the one he would keep anyway uploaded
   first. Explain the trade-offs; push back on a plan the evidence does not support, with the numbers.
9. **Build the page and the upload folder, then publish** (`references/report.md`): the angle and who it is for at the
   top, the trio, the test plan, every concept with its reasoning and checks beside it and its variants, what the
   checks found and the reasons to doubt them, what the research did and did not show, the titles, and the decisions
   that are his. `tools.py finals` writes `final/` with only the current files, at 3840x2160, each named by its concept number and
   the title it is paired with (`03-why-claude-code-says-fixed-when-its-still-broken.jpg`), so nothing withdrawn
   can be uploaded by mistake. This is the first time he sees the images. If he asks to see work sooner, show it with
   a plain banner: faces not yet corrected or inspected. Tell him the link, the three, and anything not done or not
   verified.
10. **Afterwards:** when he reports the test result, add it to the ledger. When he gives feedback, record it in
    `references/leon.md` with the date and his words.

## What to expect
About ten to fifteen minutes per designer, all in parallel; five to twelve generations a concept; each agent uses
roughly 150K to 250K tokens. A full run of ten concepts is around twenty-five agents and takes two to three hours
end to end. That is the cost of not showing him unchecked work.

## Mistakes already made once (so they are not made again)
- **A scripted face.** His reference blended into generated heads looked acceptable in small crops and terrible at
  full size, and it was published before anyone had looked. Likeness goes through Codex; nothing that changes his
  face is published unseen.
- **Designers writing code on him.** With only "don't paste his face" in the brief, designers still wrote scripts that
  blended a head, scaled and re-matted him, and "healed" his hair. The brief now bans any code on him.
- **Calling a look "full size" when it was not.** The face tool shrank faces below the size of the delivered
  thumbnail, and contact sheets were viewed at half scale, yet the page said every face had been checked at full size.
  `tools.py face` now shows native pixels, one image per sheet.
- **Claiming checks that had not run on the final files.** The inspection ran before the likeness pass re-rendered
  every image; the page still said all had passed. The likeness pass also redrew logos the inspection had approved.
- **Trusting an agent on likeness.** The inspector passed faces he had flagged and recommended keeping the blend he
  rejected. The likeness agents graded their own output as "clearly him".
- **Showing work before it was checked.** The first page went up as soon as the designs existed, so he saw drifted
  faces. He never asked to see unchecked work.
- **A "blind" test that was not blind.** Two of ours sat on every sheet, the same man on each, and each viewer agent
  read all 24 sheets: viewers with the problem tapped ours 73 to 90% of the time against 12 to 15% for real videos.
  They had almost certainly spotted the test items. Tap counts from that run mean nothing; the reads were still
  useful. The test now puts one of ours on a sheet, gives each agent a few sheets, and reports ours against the real
  baseline so a rigged result is visible.
- **Steering the blind viewers.** Viewers written with the video's pain tapped it 89% of the time; viewers written to
  be bored by it, never. Segments are now written by an agent that has not read the transcript.
- **Rewording after the promise check without re-checking.** "3 APP KILLERS", "MCP SETUP" and four rewritten titles
  were offered, two of them in the test trio, without ever being seen by the checker.
- **Studying winners only.** The first research pass read "winning formats" off the niche's best videos; a control
  study knocked most of them down. Run the control before the strategy leans on any format claim.
- **Turning one run's findings into rules.** The first version of this skill told designers "two or three elements,
  never more" although its own control study found minimal layouts no more common among hits than flops.
- **Reading design rules off his own analytics.** A video's click-through rate is mostly its topic. His channel report
  and CTR rankings were both used and both withdrawn. Controlled tests are the only own-channel evidence.
- **Putting words in his mouth.** A list headed "his words" contained numbers and rules he never gave.
  `references/leon.md` now says where every line comes from.
- **Sharpening on export.** An unsharp mask made his skin look crunchy in every image. `tools.py export` does not
  sharpen; keep it that way.
- **Expecting the image model to draw a logo.** It drew the Claude spark wrong in most takes, and redrew it again in
  the likeness pass. Keep the mark flat and facing the camera, record where it is, and paste the official PNG after
  the last render.
- **A logo cleanup that nibbled its neighbours.** The first version of `logo --clear` also erased the soft edges of the
  letter and the box beside the mark. It was caught only because the result was looked at at 3x before delivery. Any
  script that changes pixels gets that look, every time.
- **Ranking his likeness by agent.** Three independent reads of the same faces disagreed on almost every one. Give him
  what differs, feature by feature, and let him rank.
- **The first ten ideas.** Ten were rendered without writing thirty and culling. Do the culling in words, where it is
  cheap.
- **One layout ten times.** Fine inside one test, a uniform across uploads. Vary the composition between concepts; a
  new pose needs a new reference from him, not a generated one.
- **Words that outrun the video.** "NEW", "3 HIDDEN BUGS" and "Biggest" all went onto thumbnails or titles unbacked
  and were caught only by the promise check. Check every word against the transcript.
- **Delivering 720p.** The first run's upload folder held 1280x720 files while YouTube recommends 3840x2160; he had to
  ask whether they were the highest resolution. `finals` now writes 3840x2160 and stops if an original is missing.
- **A folder full of withdrawn files.** `out/` held superseded versions under the plain concept names. Upload only
  from `final/`.
- **Windows:** write scripts and JSON with the file tools rather than shell heredocs (quotes and backslashes break
  them); quote paths with spaces; pass Python forward-slash Windows paths.

## Files
- `scripts/`: `setup.py` (work folder and ledger); `gen.py` (Codex image generation with a shared queue; takes,
  reference images, edits); `tools.py` (`sheet`, `feed`, `face`, `logo`, `export`, `upload`, `finals`); `fetch.py` (research
  thumbnails); `sheet.py` (captioned contact sheets); `panel.py` and `tally.py` (the blind read test); `report.py`
  (the review page).
- `references/`: `leon.md` (what he has said, with sources), `strategy.md`, `research.md` (evidence rules, VidIQ traps,
  the control study brief, dated hypotheses), `designer.md` (the designer brief), `likeness.md` (the likeness pass),
  `checks.md` (segments, promise check, blind read test, final inspection), `test-plan.md` (YouTube's test rules, his
  test history, the ledger) and `report.md` (the page and its data schema).
- Outside this folder, private to his machine: `~/.yt-packaging/` holds the results ledger (`ledger.md`, with his
  test-history snapshot) and, when present, `report-example.json` (a complete real page from an earlier run). They
  are kept out of the skill because the skill is published and they hold his analytics and unreleased videos. Keep
  it that way: nothing about an unpublished video, a sponsor's terms or his channel's numbers goes in this folder.
- `assets/`: `leon/` (his two reference portraits; see `leon.md` for what they are), `logos/` (the official Claude
  mark and tile), `prompts/` (the two likeness prompts and an example of art direction that worked), `models/` (the
  face detector `tools.py face` uses).
