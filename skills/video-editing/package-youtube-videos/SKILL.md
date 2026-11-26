---
name: package-youtube-videos
description: Package a YouTube video for Leon van Zyl's channel the way a packaging strategist would - the idea, the titles, finished thumbnails with variants, and the plan for testing them - and deliver it as a review page. Starts from the viewer and the video's own hook rather than from a design, researches what separates hits from flops on the same channels (never winners only), has one designer agent per concept art-direct Codex image generation to render each whole thumbnail as a photo edit of Leon's reference portrait on a dark ground, then tries to knock the results down with a promise check against the transcript, a blind read test and an independent inspection of the final files at native size. Use this whenever the user wants a thumbnail, thumbnail concepts or variants, a title or title options, "packaging" for a video, A/B or Test & Compare variants, or a better thumbnail or title for an existing video - even if they only mention one of those and never name a skill.
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
4. **Let the image model render the whole thumbnail, as a photo edit of his portrait.** One designer per concept
   writes art direction and Codex image generation produces the complete image, type included, in about a minute a
   take. No HTML collage, no pasted cut-out. Since 2026-11-24 his portrait is the BASE image of every generation
   and the thumbnail is built around it, with him left where he sits in the photograph: the earlier way (attach
   both portraits as references, let the model draw him into a scene, then "correct" the face) produced a similar
   man ten times out of ten, and he rejected all ten (`references/likeness.md`).
5. **Try to knock the work down before he sees it, and believe him over the checks.** Separate agents that never saw
   the strategy test the promise against the transcript, the read in a feed, and the finish at native size. They
   caught real faults. They also passed faces he called terrible. His eye is the standard.

`references/leon.md` holds what he has said, in his words, with where each line comes from. Read it at the start of
every run.

## Rules that are not negotiable
- **Every subagent runs on Opus 5.5 at extra-high effort:** pass `model: "opus"` and `effort: "xhigh"` on every Agent
  call (designers, likeness, checkers, the control analyst). Leon's instruction.
- **No code touches him.** Not his face, hair, neck or body: no paste, blend, warp, scale, move, matte, heal, clone,
  sharpen or retouch by script, by you or by any agent. His likeness comes from the image model, working from his
  portrait as the base image. A scripted face blend was tried and he rejected it outright ("It should
  definitely not be a scripted faceplate. Why on earth would you do that if you've got access to Codex?"). The only
  script allowed to alter pixels of a delivered image is `tools.py logo`, and only on a logo.
- **How he gets into a thumbnail is settled, and is never a question for him.** His reference portrait is passed to
  Codex with every generation and Codex renders the thumbnail with him in it. Leon, 2026-11-26: "The face should not be placed using code. You can pass reference images to Codex, and that will add the image to the thumbnail."
  Never offer to place, paste or composite his photograph, with or without "his OK". Never open or interrupt a run
  by asking him to choose a method, accept faces in advance or send another portrait. When a face falls short the
  remedies are the skill's to apply, in the order `references/likeness.md` gives, and the run goes on.
- **"A similar man" is never delivered.** A face goes to him only when, put beside the portrait at native size, it
  reads as the same photograph of the same man on a new ground. Designers judge every take that way, an inspector
  calibrated on faces he has rejected (`~/.yt-packaging/likeness_rejects/`) gives each final file one of three
  verdicts, and a face blocker from any inspector is acted on, never argued away (`references/checks.md`,
  section 3). What still differs from the portrait is written beside the image on the page, first, in plain words.
  The one floor under this rule: a run never ends with an empty page or a question to him. If the gate would leave
  fewer than three concepts, the three closest go on the page with their verdicts and differences stated first
  (`references/likeness.md`).
- **Nothing with his face reaches a page before that inspection of the final files and your own look at each one at
  native size.** He was shown broken faces once because a page was published first, and ten faces he rejected
  outright a second time because the checks graded them close.
- **Every concept is delivered on a dark ground, and the dark version is the main one.** Leon (2026-11-24): "I
  always need the dark versions as well. I'm personally not a fan of bright backgrounds. I'm okay with them being
  in the mix, as long as they're based on best practises and what's working in the industry." Charcoal or
  near-black, never a grey bland gradient. A bright ground is an alternate, made only where this run's research
  gives a reason, and the page states the reason with its numbers (`references/designer.md`).
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
  with Pillow, numpy and OpenCV; a browser or Playwright for one look at the page. **Check VidIQ is connected before
  planning the research.** It is configured per project, and a session started from a video folder may not have it
  (2026-11-23). `references/research.md` has the yt-dlp fallback and says what it cannot replace; tell him early if
  VidIQ is missing.
- **A video that is already published** (a re-package) is a different job from a launch: look at the old package
  once to know what not to repeat, pull the transcript and frames from the live video, and use the test plan for
  existing videos (`references/test-plan.md`).
- **The work folder:** next to the video (`<video folder>/packaging-<slug>/`), never inside a code or skills repository.
- Ask before starting only for what cannot be found: the sponsor's requirements, and the last video's test result if
  the ledger lacks it. Otherwise work through to the page, then iterate with him. A note an earlier run left about
  his face, his portrait or the method is not something to ask him about: the method is settled (rules above).

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
   and the designers have a working example; then one designer agent per concept, started in waves of three or four
   a few minutes apart, never all ten at once: the image service rate-limits the whole account. Each delivers a
   finished thumbnail as a 1280x720 review file plus its full-size original (the upload file is made from the
   original in step 9) on a dark ground, a bright alternate only where you asked for one, and its own doubts. Tell him where things stand at every stage
   boundary and whenever an obstacle changes the estimate; do not leave him to ask.
5. **Check the designs** (`references/checks.md`), each by a fresh agent that has not read the strategy: the promise
   check against the transcript and the blind read test. Act on them: fix overclaims in the words, drop or flag what
   the hook does not confirm, send each fix to that concept's own designer (image-model edits only). **Every reworded
   thumbnail or title goes back through the promise check** before it can be offered.
6. **Make every fix as a fresh render from his portrait** (`references/likeness.md`, `references/designer.md`): a
   changed word, a moved element or a face fault all go into the prompt, and the image is rendered again with the
   portrait as its base, then the official logos are pasted. There is no separate likeness pass any more: the old
   one ("reproduce this thumbnail, correct only his face") kept the face the model had already drawn, and is
   documented in `likeness.md` only as a last resort.
7. **Inspect the final files** (`references/checks.md`, section 3): fresh agents, calibrated on faces he has
   rejected, every final image at native pixels: a likeness verdict against his portrait, text, logos against the
   official mark, artefacts, the dark ground. Then look yourself: open each `out/<id>_full.png` whole, and its
   native-size face sheet. A face graded "similar man" is re-rendered or withdrawn; one graded "visibly changed"
   gets one more render with the fault named and, if the fault survives, goes on the page with that fault stated
   first. If anything changes after this step, the inspection runs again for that image before it is shown.
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
    `references/leon.md` with the date and his words. And write the run's lessons into this skill before closing it
    (Leon, 2026-11-23: "add the lessons learned, like the rate limit issues, to the global skill as well"): what
    went wrong goes in "Mistakes already made once" and in the reference it belongs to, dated; what a check or a
    study found goes in as one run's finding, not a rule. When he says the thumbnails are uploaded, note in the
    ledger what he uploaded and when, and offer to clean up as "What a run leaves behind" describes. Delete nothing
    until he says yes for this run.

## What to expect
About ten to fifteen minutes per designer, started in waves of three or four; five to twelve generations a concept; each agent uses
roughly 150K to 250K tokens. A full run of ten concepts is around twenty-five agents and takes two to three hours
end to end. That is the cost of not showing him unchecked work.

That is with the image service answering freely. On 2026-11-23 it rate-limited the whole account to about four
images every ten minutes, and the same run took more than four hours. Renders are then the only thing that sets the
pace, so ration them the moment it shows: no alternatives unless one is already finished, one likeness take for
concepts that will not be in the trio, fixes folded into the likeness render, and concepts the promise check has
cut dropped before the likeness pass, not after. Tell him the new estimate when it changes.

## What a run leaves behind (measured 2026-11-23)
- **The work folder:** about 900 MB for ten concepts, a fifth of it the downloaded video. Once he has uploaded he may
  not need it, but it holds the only full-size originals outside YouTube, so tell him the size and ask before
  deleting it; first move out anything you parked there that the skill still needs. Never keep the only
  backup of a skill file in the work folder: put it in `~/.yt-packaging/`.
- **The image tool's own folder, which is easy to miss:** every render attempt, failed ones included, writes a
  session file of about 7 MB into `~/.codex/sessions/` (the request with its reference images inside), and every
  image is also kept in `~/.codex/generated_images/<thread id>/`. A run of 316 attempts for 68 images left 2.2 GB
  of session files and 144 MB of images there, all carrying his likeness. This run's files are the ones whose first
  line names the work folder as `cwd`. It is another tool's data, so tell him the size and ask before clearing it.
  It is also one more reason to avoid retry storms: 248 of those 316 files were failed attempts. When he says yes:
  list the matching session files first (exact `cwd`, the run's date folder), take each one's `session_id` to find
  its folder under `generated_images/`, delete only those, and check the store's counts fell by exactly that many.
  Leave Codex's index and database files alone; its session list may keep dead entries for the deleted runs.
- **The published review page** stays on claude.ai until he deletes it. Ask.
- **Kept on purpose:** the results ledger and its pending note for the test, and the lessons in this skill.

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
- **Ten designers rendering at once** (2026-11-23). All ten started together, the image service answered "429 Too
  Many Requests", and every agent re-ran its failed call straight away, which kept the limit saturated: three
  renders in four failed for half an hour and six concepts had no image at all. It was the whole account (a tiny
  text-only request was refused too), not the weekly allowance, and lowering the concurrency alone did not cure it.
  `gen.py` now spaces starts and waits and retries by itself; designers start in waves, run one call at a time and
  never re-run a call that is waiting (`references/designer.md`).
- **Stopping a render that holds a queue slot.** Killing a `gen.py` process mid-generation leaves its slot file
  behind for twenty minutes. Stop only a call that is still waiting its turn, or let it finish.
- **Assuming VidIQ was there.** The research was planned around it and the session did not have it. Check first.
  yt-dlp gave the same-topic search, the channel pulls, the feed pool and the control study; it cannot give search
  volumes or his saved test history.
- **A tick on something the video never shows.** "ENDING ✓" was true of the game and said in the opening, but the
  video stops in the first act. A tick, an arrow or a picture claims the viewer will SEE the thing. Ask of every
  element: said in the opening, and shown when?
- **A picture whose star arrives at minute 22.** Two concepts made a late-game figure the hero. Their words were
  confirmed in the first 16 seconds; the figure appeared 92% of the way through. Check the thumbnail's picture
  against what the opening SHOWS, not only its words against what the opening says.
- **A promise checker with only the transcript.** It could not tell whether a pictured scene was in the video, and
  said so. The second checker sampled frames from the video file and settled it. Give the checker the frames.
- **Selling a bonus.** A concept built on a download the video offers and never shows working came back a mismatch,
  after a designer had spent renders on it. "Offered" is not "shown": cull it in words.
- **One prompt in, finished thing out.** An arrow from a typed sentence to the result read as "one prompt made
  this" when the video took ten steps. Putting the count on the arrow ("10 STEPS LATER") fixed it.
- **Reading a zero as a verdict on the thumbnails.** For a video outside the channel's usual subject, viewers
  written as the core audience read every thumbnail correctly and tapped none, while tapping the real videos
  beside them 11 to 18% of the time. That is a finding about subject and audience, to be said plainly on the page.
  It does not rank the concepts, and the audience the package is really for was not in the panel.
- **An agent that handed back half done.** Resumed after a server error and asked to "reply in six lines", a
  likeness agent reported and stopped with two images unrendered. When resuming an agent, say what is left and that
  it hands back only when all of it is delivered.
- **Correcting a correction.** Three faces the inspection flagged (a grin, a smirk, an arched brow) went through a
  second likeness round and none moved: the image model keeps most of a face it has already drawn. The one that was
  rendered afresh from its designer's prompt, with the expression written out in words, came back right in one call.
  For an expression fault, skip the second likeness round and re-render (`references/likeness.md`).
- **Replacing a file under an inspector.** An image was swapped for a better version while an inspection of it was
  running, so nobody could say which version that read described, and it had to be discarded. Start an inspection
  only on files that will not change, and inspect a late replacement on its own.
- **Taking an inspector's blocker as fact.** One graded a character's curls a blocker for "looking like letters";
  they were the real character's curls, in every frame of the video. Three inspectors also read versions of one
  face three ways. Give the inspector the real frames so it knows what is faithful, look yourself, and put a
  blocker you are not acting on in front of him with the reason.
- **A published page nobody could open.** The built-in browser was not signed in, so the published page could not
  be looked at. Confirm the publish from the artifact's own file list (the page and every image present), and say
  plainly that the rendered page was not seen.
- **Leaving him to ask for progress.** He asked three times during a run that overran. Say where things stand at
  each stage boundary, and at once when an obstacle changes the estimate.
- **Naming the subject's neighbour to the segment writer** (2026-11-24). The channel line given to the agent that
  writes the viewer profiles named a platform closely tied to the video's subject, so three of four profiles had
  that platform in their week, and those three tapped ours 50 to 90% of the time against 7 to 14% for real videos,
  with one of ours per sheet. The taps were discarded again. Describe the channel in general terms, and expect a
  new product that only our tiles cover to be spotted anyway: plan to use the reads only.
- **A maker's logo, an arrow and a product** (2026-11-24). "[Maker's logo] → [product] MADE AN ..." was read by every
  blind viewer as a tutorial on building the thing with the maker's tool. An arrow says "turns into". Say "by the
  ... team" in words when the point is who made it.
- **Designers left to choose a ground all chose the same one** (2026-11-24). Told only to get away from the field's
  dark look, six of ten independently picked blue, and seven of ten kept him on one side with words on the other.
  Assign each concept its ground and where he stands in its own brief, in words, before anything is rendered.
- **A softer wording that was still an overclaim** (2026-11-24). A concept graded late was reworded to the opening's
  own gist ("NO TECH SKILLS NEEDED" for "not technical at all") and the second promise check graded it moderate:
  the steps on screen still asked for skills. A third wording passed. The re-check rule earned its keep twice.
- **Ten faces he rejected, after every check had run** (2026-11-24). All ten concepts were drawn from both portraits
  as references, corrected by the likeness pass, read by five inspectors and looked at by the orchestrator at
  native size, and the hand-over said "recognisably you". He answered: "those faces do not look good enough at
  all. The critics should have picked that up, and it should have been fixed." Three things went wrong at once.
  The method drew a similar man every time. The inspectors listed real differences (narrower jaw, greyer hair,
  lighter eyes, wider smile) and then summarised them as close, because nothing asked them for a verdict or showed
  them a face he had rejected. And when two inspectors did grade a face a blocker, the orchestrator measured the
  face box, found it within 9% of the portrait and level with faces nobody had flagged, and delivered it: the
  measurement was true and cleared nothing, since every rejected face had the portrait's proportions. The fixes
  are the photograph-as-base method (`references/likeness.md`), the calibrated three-verdict gate
  (`references/checks.md`, section 3), and this rule: a face blocker is acted on, and a measurement may only
  confirm a fault.
- **Moving him to make room for the words** (2026-11-24). Ten takes that slid the serious portrait down under a
  headline all came back with a redrawn face; two that left him exactly where he sits in the photograph and put
  the headline beside him came back as the photograph. Lay the words out round him.
- **Attaching the old thumbnail "for its layout only"** (2026-11-24) brought its wrong face back with it: lighter
  eyes, a narrower jaw. Nothing with a drawn version of him is ever attached; the layout is described in words.
- **Bright grounds by default, and no dark version of three concepts** (2026-11-24). The strategy told designers
  to get away from the dark look of the field; he had to ask for dark versions and said he is "not a fan of bright
  backgrounds". The brief now makes dark the main ground. That day's bright alternates also cost likeness: two of
  three failed their own designer's check with a wider, pinker face.
- **Asking for him bigger than the portrait** (2026-11-24): at 52% of the frame height against the smile portrait's
  47%, the model widened and flattened his head. He stays at the photograph's size.
- **Calling the second attempt fixed before the gate had run** (2026-11-24). After the re-render the orchestrator's
  own read was again that the faces were his, and progress notes said the method "works". Three calibrated
  inspectors then graded the smiling faces "a similar man" or "visibly changed" and none passed. The page went out
  with a banner saying likeness was not signed off, each face beside his portrait, and no upload files. Say
  "closer", never "fixed", until the gate has run; and when it fails, show him the evidence in plain words rather
  than another confident sentence. The remedies are the skill's to apply (`references/likeness.md`), not choices to
  hand him.
- **Asking him how his face should get into the thumbnails** (2026-11-26). The run above had left "three ways
  forward" in this skill and in the ledger as a choice waiting on him, one of them placing his photograph by code.
  The next session read that at the start, stopped, and asked him to choose, recommending the code route "with
  his OK". He said the question itself showed something was wrong: his reference goes to Codex and Codex puts him
  in the thumbnail. Never park an open question about method where the next run will read it, and never present a
  forbidden route as an option.
- **A logo rasterised wrong** (2026-11-24). A product's app tile, rasterised from the official SVG with PyMuPDF, came out
  with its corner arcs flattened into near-chamfers, and that file was pasted on twenty images across two rounds
  before an inspector noticed it against the official PNG. After rasterising a mark, compare it with the source's
  own geometry (corner radius, ring and dot bounds) or with an official raster of the same mark, at 3x. Fixing it
  was a re-paste from each kept pre-paste take, with a pixel comparison proving nothing else moved.
- **A ghost under a pasted logo** (2026-11-24). `--clear` removed the model's drawing of a lattice mark from a
  white chip but left its soft edge 5 to 10 grey levels under the white, which two inspectors saw. Ask the model
  for the chip EMPTY and paste the official mark onto plain ground.
- **Type and cards landing exactly on his shoulder line** (2026-11-24): three of ten had a bar, a card corner or a
  letter touching his shoulder with a 0 to 3 px gap. Say in the prompt whether an element stops short of him (by
  how much) or laps clearly over him; a tangent is neither.
- **Inspectors sharing one scratch folder** overwrote each other's helper scripts (2026-11-24). Give each inspector
  its own folder under `qa/final/`.
- **No rendered final cut** (2026-11-24). The folder held raw recordings and the edit's item list, so frames were
  mapped through the list: the talking-head opening could not be checked visually and frame times drifted by up to
  fifteen seconds late in the video. Ask for the exported file; if there is none, say what could not be seen.
- **A secret on screen.** A checker reading frames of a recording can come across a credential (an access token, an
  API key) that is readable on screen. Verify it yourself, copy its value nowhere (not into a file, a brief or the
  page), delete any crop you made, and put it first in "Still open" and in the hand-over. Never name the video or
  the credential in this skill.
- **A transparent logo and a pre-paste render worth keeping.** A mark with a transparent centre cannot use
  `--clear`: fold "remove the mark, leave that spot plain" into the likeness prompt, check the spot, then paste.
  Keep the chosen take as it was before any logo was pasted: when an inspector found the mark cramped, pasting it
  smaller onto that take fixed it with no render, and a pixel comparison proved nothing else moved (2026-11-24).
- **`--clear` refuses a tile on a gradient or over a drop shadow.** Ask designers for a flat ground and no shadow
  under a mark, or paste the opaque official tile about 4% larger than the drawn one and look at the corners.
- **Windows:** write scripts and JSON with the file tools rather than shell heredocs (quotes and backslashes break
  them); quote paths with spaces; pass Python forward-slash Windows paths. A `cd` inside a Bash call moves the
  session's working directory: use absolute paths. Headless Chrome will not lay a page out narrower than about
  500 px, so a 390 px screenshot is a cropped 500 px page: shoot phone width at 500.

## Files
- `scripts/`: `setup.py` (work folder and ledger); `gen.py` (Codex image generation with a shared queue, starts
  spaced machine-wide, and a wait-and-retry when the service rate-limits; takes, reference images, edits); `tools.py` (`sheet`, `feed`, `face`, `logo`, `export`, `upload`, `finals`); `fetch.py` (research
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
  mark and tile), `prompts/` (`photo_base_smile.txt` and `photo_base_serious.txt`, the paragraph about him that
  goes into every prompt; `example_photo_base.txt` and `example_photo_base_serious.txt`, two prompts that worked;
  the older `example_art_direction.txt` and the two `likeness_*.txt` prompts of the retired correction pass),
  `models/` (the face detector `tools.py face` uses).
- Also outside this folder: `~/.yt-packaging/likeness_rejects/` holds face sheets of faces he has rejected, for
  calibrating the inspectors (`references/checks.md`, section 3). Private: every file carries his likeness.
