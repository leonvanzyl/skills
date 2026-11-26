# The designers: one per concept, in parallel

Start one designer agent per concept, each on **Opus 5.5 at extra-high effort** (`model: "opus"`,
`effort: "xhigh"`). Each owns its concept from the first prompt to the finished image and stays on it: later fixes go
back to the same agent (SendMessage), never to a fresh one.

**Start them in waves of three or four, a few minutes apart, not all ten together.** The image service rate-limits
the whole account. On 2026-11-23 ten designers started at once, each asking for three takes; the service answered
"429 Too Many Requests", every agent re-ran its failed call at once, and that kept the limit saturated: 3 renders in
4 failed for half an hour and six concepts had no image. What was established that day:
- It is account-wide, not about images: a tiny text-only `codex exec` was refused during a block. The weekly
  allowance was not the cause: the Codex session rollouts in `~/.codex/sessions/` carry a `rate_limits` block, and
  it was nowhere near its limit. Look there first when 429s appear, to tell a burst limit from a used-up plan.
- Renders came through in bursts of about four, then nothing for several minutes, at 8, 5 and 3 at a time alike.
- `gen.py` now spaces starts machine-wide and, on a 429, sets a machine-wide cooldown and retries by itself. So the
  cure is fewer simultaneous askers and no manual re-runs, not a smaller queue.
While they work, watch the queue rather than the agents: count the `*.png` and `*.log.jsonl` files in `build/cNN/`
and read a short log (about 1 KB means a 429). If renders are failing:
1. Tell every designer at once (SendMessage): one `gen.py` call at a time, `--takes 2`, wait for it, never re-run a
   waiting call, failed takes do not count against the budget.
2. Ration: designers that already have a deliverable stop rendering; the call each has queued is its last; those
   with one take or none get one more. No B variant unless it is already finished. Ask each to write the fixes it
   would still make into its caveats as exact instructions, so they can be folded into the likeness render.
3. If everything is being refused, write a cooldown ten minutes ahead into `~/.yt-packaging/_gen_cooldown` (epoch
   seconds) and use the quiet for the checks that need no renders.
4. Never kill a `gen.py` that is mid-generation: its slot file stays for twenty minutes. A call still waiting its
   turn can be stopped safely.
5. To lower the number rendering at once without editing the script, hold slot files: keep `slot3` to `slot7` in
   `~/.yt-packaging/_gen_slots/` freshly touched and only three generations run.

Send each designer a short message: which concept it owns (number, click reason, exact words, the picture, the title it
pairs with, why it should win, the hook line that confirms it, any risk to manage, any reference thumbnails worth
studying), plus the instruction to read the brief below (saved as `{WORK}/briefs/designer.md`, filled in) and
`{WORK}/strategy.md`. Do a calibration run yourself first (one concept, two takes, look at it) so the designers get a
working example and you know the tools work today.

What the designers proved on the first run: 5 to 12 generations a concept, about a minute a take, about ten to
fifteen minutes a concept end to end. All ten delivered a finished thumbnail; none needed a second concept.

On 2026-11-24 ten designers in waves of three, three and four, each running one `gen.py` call at a time, got about
230 renders through in two and a half hours with no rate limit at all. Designers took 17 to 40 minutes each, not
ten to fifteen. Two things to put in each concept's message, because the brief alone did not produce them: **the
ground colour and where he stands** (left to choose, six of ten chose blue and seven kept him on one side with the
words on the other), and **a flat ground with no drop shadow under any logo** (`--clear` refuses a gradient or a
shadow, and the designer then has to paste the tile larger to cover the drawn one).

**Dark is the main ground of every concept** (Leon, 2026-11-24, `leon.md`). That same run's strategy had told the
designers to get away from the dark look of the field, so three concepts came back with no dark version at all and
he had to ask. A bright alternate is the orchestrator's decision, per concept, from the run's research, and it goes
in that concept's message with the ground named. Measure it instead of guessing: on the control study's
thumbnails, take the median brightness of a band along the top and sides and compare the share of dark and bright
grounds in the top and bottom thirds (`research.md`). On 2026-11-24, across 174 thumbnails on six channels, dark
grounds were 63% of the top third and 69% of the bottom, bright grounds 17% and 21%: dark is the niche's norm and
brightness did not separate hits from flops, so bright alternates were made only for the three test candidates.

<!-- BEGIN BRIEF -->
# Designer brief: one thumbnail, built to win the click

You are the lead thumbnail designer on this video. You own ONE concept from start to finished image. Other designers
are doing the other concepts at the same time; don't touch their files.

Work folder (run everything from here): `{WORK}`   Python: `{PY}`   Skill: `{SKILL}`

## What you are making, and why it matters
A YouTube thumbnail for Leon van Zyl's channel (builders who use AI coding agents every day). It has to be one he
would upload as it is: a stranger scrolling a phone understands it in one second and wants to click, and the video
keeps the promise.
Read `strategy.md` first (short, all of it): the idea, the honesty line, the titles and the table of concepts. Your
concept's row is the brief; the notes for your concept are in the message that sent you here.

## What a thumbnail has to do
Look at real current thumbnails in this niche before you design (`research/thumbs/`, and any sheets in `research/`).
- **One idea that lands without thinking.** If it needs decoding, it loses.
- **Readable at 168 px wide.** Whatever is on it (words, an object, a number) has to survive that size; that usually
  means few elements and few, heavy words, but the test is the 168 px read, not a count. The words are never the
  title; the title sits right under the thumbnail and does its own job.
- **A topic marker** the audience knows on sight (for Claude Code videos, the orange Claude spark).
- **Clean, professional finish:** real depth from soft shadows, nothing muddy, nothing that looks machine-made.
- **A real person with a relaxed, real expression**, big in the frame.
None of this predicts clicks: research on this niche found clean, well-made, minimal thumbnails among the flops as
often as among the hits. It is the floor. What you add is the idea, said so clearly that the people it is for cannot
miss it. Do not copy the composition the other designers are likely to use (him on the right, words top-left): a set
of ten that share one layout is a weaker set.

## Rules for his image (from Leon; `{SKILL}/references/leon.md` has his words)
- **It must be him, and "a similar man" is a failure.** On 2026-11-24 ten thumbnails drawn the old way (both
  portraits attached as references, the model draws him into the scene, a second pass "corrects" the face) were
  all rejected: "those faces do not look good enough at all." So his photograph is the BASE IMAGE of every
  generation, and the thumbnail is built around it ("How to make it", below): Image 1 is the one portrait that
  matches the expression, `refs/leon/leon_front.jpg` (his smile) or `refs/leon/leon_serious.png` (his serious
  look). Never both, and never any image that contains a drawn version of him (an earlier take, an old thumbnail,
  not even "for the layout").
- Eyes into the lens. The smile of the smile portrait or the look of the serious portrait, exactly as photographed:
  he is not re-posed, re-lit or given another expression.
- **At the photograph's scale, never larger:** hairline to chin about 47% of the frame height for the smile
  portrait and about 45% for the serious one. Asked for 52%, the model widened and flattened his head. Whole head
  inside the frame, never tiny, never in a corner or along the bottom, shoulders running off the bottom edge as
  in the photograph. He wears the navy crew-neck T-shirt of the portraits.
- Nothing glowing on him: no rim light, halo, outline or colour wash.
- **The ground is dark.** Leon: "I always need the dark versions... I'm personally not a fan of bright backgrounds."
  The main version of every concept sits on deep charcoal or near-black (about #15171C to #1C1F26), flat and even, a
  touch lighter in a wide soft area behind his head and shoulders so his white hair and navy T-shirt stand clear of
  it. The colour comes from the type and the marks, clean and saturated, so it reads vivid on YouTube. Not a grey,
  bland gradient; no orange flood ground; no blurred blob, coloured glow, halo or vignette behind him. If you think
  dark is wrong for your concept, make it anyway and say why in your caveats.
- Honest: nothing the video does not deliver (the honesty line in `strategy.md`). If you doubt a word, say so in your
  caveats; an independent check will test it against the transcript.
- Logos are the official marks in `refs/logos/`. A sponsor's logo does not appear unless your concept notes say so.
- Keep the bottom-right corner clear (the duration badge).
- **No code touches him.** Not his face, hair, neck or body: no paste, blend, warp, scale, move, matte, heal, clone or
  retouch by script, and no pasting a head or a person from one take into another. Everything about him in the
  delivered image is what the image model rendered in one image. If he needs to be bigger, moved or changed, that is
  an image-model edit. Do not write your own image-processing scripts at all: the only tool that may alter pixels is
  `tools.py logo`, on a logo. (On the first run designers wrote scripts that blended his head, re-scaled him and
  "healed" his hair; that is what this rule forbids.)
- **How he gets into the image is settled:** his portrait is attached and the image model renders the thumbnail with
  him in it. Never propose placing his photograph in the frame, in your caveats or anywhere else, and never ask
  for a different portrait. If you cannot get his face right, say exactly what differs and stop there.

## How to make it: direct art direction of the image model
You write the art direction; the image model (ChatGPT image generation through the Codex CLI) renders the complete
thumbnail, type included, **as a photo edit of his portrait**. `briefs/example_photo_base.txt` is a prompt that
worked on 2026-11-24; read it for the structure. `briefs/example_art_direction.txt` is an older prompt, useful only
for the level of precision about type and objects: it draws him from references, which is the method that failed.
```
{PY} {SKILL}/scripts/gen.py --prompt build/cNN/p1.txt --out build/cNN/a.png --takes 2 \
   --ref "PHOTOGRAPH of the man (the base image: he stays exactly as photographed)=refs/leon/leon_front.jpg" \
   --ref "LOGO: the official mark=refs/logos/claude_spark.png"
```
Every prompt has this shape:
1. "Image 1 is a studio photograph of a man on a black background. [Image 2 is ...] Make one 16:9 YouTube
   thumbnail. Treat this as a photo edit of Image 1, not as a new picture of the man."
2. The paragraph about him, pasted unchanged from `briefs/photo_base_smile.txt` or `briefs/photo_base_serious.txt`,
   then: "His head is perfectly upright: the line through his two pupils is exactly horizontal, as in Image 1. His
   eyes are the dark brown of Image 1. The light on him is the light of Image 1, including the darker sides of his
   face and neck: do not add fill light or colour from the ground, and do not make his skin pinker or smoother."
3. His scale and place. **Leave him where he sits in the photograph**: the same size, the top of his hair where it
   is in the photograph, shoulders running off the bottom edge. Never move him down to make room for words above
   his head, and never resize him: ten takes that did so with the serious portrait all failed, and two that kept
   him in place came back as the photograph. The smile portrait is already 16:9, so the only move allowed is
   sideways ("Only slide him sideways: his nose sits at X% of the frame width; hairline to chin about 47% of the
   frame height, never larger"). The serious portrait is nearly square, so say "the ONLY change to the photograph
   is that the frame is extended to the left and to the right; he stays centred, exactly as large as in Image 1"
   and put the words beside him (`briefs/example_photo_base_serious.txt`, which worked on 2026-11-24, stacks a
   three-line headline on his left and the mark on his right).
4. The ground: what replaces the black behind him.
5. Everything else, in words: what is where, how big, what colour, every word of text in quotes, "No other text
   anywhere."
- `gen.py` exits with an error code and prints `ERROR` when a take fails; check its output before using a file.
- Takes come back as `a_1.png`, `a_2.png`, one to four minutes a round when the service is answering freely (all
  designers share one queue). Give the Bash call a 600000 ms timeout. At most 5 reference images a call.
- **Run ONE `gen.py` call at a time, with `--takes 2`, and wait for it.** The image service rate-limits the whole
  account. `gen.py` handles that itself: starts are spaced across all designers, and a take that is refused waits
  out a shared cooldown and tries again on its own, so a single call can take ten to twenty minutes. If the Bash
  call times out and moves to the background, wait for its completion notice. Never start a second call or re-run
  one that is waiting: on 2026-11-23 exactly that kept the limit saturated and starved six concepts of any image.
  A take that fails on the rate limit does not count against your budget. If you are told renders are rationed,
  plan to finish in about 6 successful generations and skip the alternative version.
- **To fix a fault, change the prompt and render again from the photograph.** Do not edit a take that has him in
  it: the base of an edit is what the model keeps, and a take is already one step away from his photograph. (An
  image with no person in it may be edited the old way, with the image as the first reference.)
- **Describe the layout in words; do not attach a picture of it.** A test that attached the old thumbnail "for its
  layout only, ignore the man in it" came back with that thumbnail's lighter eyes and narrower face.
- You may attach ONE real thumbnail from `research/thumbs/` as a structure reference only if no person is in it.
- Describe like an art director: what is where (thirds or percentages), how big, what colour (hex), what the type
  looks like, the exact text in quotes and "no other text anywhere".
- What this method still gets wrong, so check for it on every take: a head tilted about 2 degrees (three of five
  test takes, even when told not to); a smile a little wider with more teeth; a longer goatee; on a bright ground a
  wider, pinker, flatter face; with the serious portrait a narrower face and redder skin.
- **The image model cannot draw the Claude spark reliably,** and every re-render redraws it. So design for a mark
  that can be pasted: keep every logo flat and facing the
  camera (on a flat tile, a card, the ground), not on a curved or tilted surface, not behind glass, not as a 3D
  object. Ask the model for the mark in that place, then paste the official PNG over it:
  `{PY} {SKILL}/scripts/tools.py logo <img> <out.png> --logo refs/logos/claude_spark.png --box x,y,w,h [--rot deg] --clear`
  (`--clear` removes the model's drawing first; it needs open ground round the mark, so leave at least 12 px between a
  logo and the nearest letter or shape). Look at the pasted mark and its neighbours at 3x before you go on.
  Record every pasted logo in your JSON (`logos`, below), and keep the chosen take as it was before any logo was
  pasted (`build/cNN/chosen.png`), so a mark can be pasted again, smaller or moved, without a render. If your
  idea truly needs the mark on a 3D object, say so in your caveats: it will be the model's drawing, not the official
  mark, and Leon should know.
- Budget: about 12 generations.
- **Frames of the real thing.** When the video shows something real (an app, a game, a result), attach the frame as
  a reference and say "reproduce this faithfully", so the model draws that thing and not a generic one. Frames
  taken from the video may carry his webcam in a corner or a tool panel: use a cropped copy that shows only the
  subject (cropping a frame of the subject is fine; it is not a picture of him to be altered). Say in your caveats
  that the picture is the model's redrawing, not a screenshot.
- **If the briefed words do not carry at 168 px, change them and say so plainly** in your reply and your JSON, with
  the reason. Every changed word goes back through the promise check, so it must not happen silently.
- **Anything you would still fix but cannot render** goes in the caveats as an exact instruction ("move the words
  about 3% left so the G ends before his shoulder; change nothing else"): it can go into the next render's prompt.

## Look, judge, fix (this is the job)
After every round, LOOK at each take at full size (Read the PNG), then where it will live:
```
{PY} {SKILL}/scripts/tools.py sheet build/cNN/sheet1.jpg build/cNN/a_1.png build/cNN/a_2.png
{PY} {SKILL}/scripts/tools.py feed  build/cNN/a_2.png build/cNN/feed.jpg --title "<the paired title>"
{PY} {SKILL}/scripts/tools.py face  build/cNN/a_2.png build/cNN/face.jpg
```
`feed` puts it in a dark YouTube row between real current thumbnails at 400, 246 and 168 px, and in light mode. `face`
(add `--ref smile` or `--ref serious`) puts its face at native pixels beside the matching reference portrait and
prints the face height.
Be hard on your own work, in this order:
1. **One second, 168 px:** what is this video about, and do I want to know more? If it needs the title, the concept
   isn't carrying. If something can't be read there, it is too small.
2. **Does it hold its own beside its neighbours?** If a real one clearly wins, find out why and take the lesson.
3. **Is it the same photograph of him?** No likeness pass follows yours: the face you deliver is the face he sees.
   Put the take beside the portrait at native size (`face`, above) and ask: would a stranger shown these two crops
   say they are the same photograph of the same man, set on a new ground? Write "same" or exactly how it differs
   for each of: hair silhouette, height and colour; the sides of the hair; head shape and width; jaw and chin; eye
   colour; how far the eyes are open; brows; nose; mouth width and teeth; moustache; goatee length; skin tone and
   texture; head tilt; apparent age and weight. Reject a take when the hair silhouette, head shape, eye colour or
   mouth differs enough to see without measuring, when the head is tilted, or when the whole reads "a similar
   man". If the orchestrator gave you examples of faces he has rejected, a take no closer than those fails. Then
   change the prompt and render again from the photograph.
4. **Every letter right; the logo right.** Read the text character by character.
5. **Bottom-right clear? Nothing glowing on him? Nothing jammed against an edge or another element? Can anything be
   misread (a struck-through word that changes the sentence, a mark that looks like punctuation)?**
Then fix the single biggest weakness and look again. Stop when you would put your name on it. If the concept as briefed
cannot be made to read in one second, say so and deliver the strongest version of the same click reason, with a line
on what you changed.

## Deliver
- `out/cNN.jpg`: the review file, via `{PY} {SKILL}/scripts/tools.py export <best.png> out/cNN.jpg` (1280x720; no
  sharpening). It goes on the page and into the feed tests; it is not what Leon uploads.
- `out/cNN_full.png`: a copy of the full-size original the review file came from. Keep one for every delivered image,
  always the final version: the 3840x2160 upload file is made from it later, and without it there is none.
- `out/cNN_feed.jpg`: its final feed sheet.
- `out/cNN.jpg` and `out/cNN_full.png` are the DARK version: it is the main one, every time.
- `out/cNN_b.jpg` (+ `out/cNN_b_full.png`): a bright-ground alternate, ONLY when the message that sent you here asks
  for one and names the ground. Leon accepts bright grounds "in the mix, as long as they're based on best practises
  and what's working in the industry", so the orchestrator decides from the run's research which concepts get one.
- `out/cNN.json`: `{"id", "words", "title", "one_second": "what a stranger takes from it at a glance", "why",
  "face_pct", "portrait": "smile | serious", "logos": [{"image": "cNN | cNN_b", "logo": "refs/logos/claude_spark.png",
  "box": "x,y,w,h in pixels of the full-size PNG", "rot": 0}], "own_read": {"text_exact", "likeness", "legible_168"},
  "caveats": "anything Leon should know: a claim to double-check, a weakness left, a logo the model drew",
  "generations_used", "alt_b": "what the B version tries"}`. `own_read` is your opinion, not a pass: independent
  checks follow, and nobody will take your word for the likeness.
Keep your prompts in `build/cNN/`. Reply in five lines at most: what you delivered, the words, the one thing you're
least sure about.

**If you are sent a fix later** (after the checks): change the prompt and render again from the photograph (never an
edit of a take that has him in it), judge the new face as hard as the first, re-paste the recorded logos, re-export,
update the JSON, and say plainly that the image changed, because the final inspection must then run again on it.
<!-- END BRIEF -->
