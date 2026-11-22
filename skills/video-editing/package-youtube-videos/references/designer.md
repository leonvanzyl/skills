# The designers: one per concept, in parallel

Start one designer agent per concept, all at once, each on **Opus 5.5 at extra-high effort** (`model: "opus"`,
`effort: "xhigh"`). Each owns its concept from the first prompt to the finished image and stays on it: later fixes go
back to the same agent (SendMessage), never to a fresh one.

Send each designer a short message: which concept it owns (number, click reason, exact words, the picture, the title it
pairs with, why it should win, the hook line that confirms it, any risk to manage, any reference thumbnails worth
studying), plus the instruction to read the brief below (saved as `{WORK}/briefs/designer.md`, filled in) and
`{WORK}/strategy.md`. Do a calibration run yourself first (one concept, two takes, look at it) so the designers get a
working example and you know the tools work today.

What the designers proved on the first run: 5 to 12 generations a concept, about a minute a take, about ten to
fifteen minutes a concept end to end. All ten delivered a finished thumbnail; none needed a second concept.

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
- It must be unmistakably him. Attach both reference portraits to every generation: `refs/leon/leon_front.jpg` (his
  smile) and `refs/leon/leon_serious.png` (his serious look).
- Eyes into the lens. The smile of the smile portrait or the look of the serious portrait, exactly as they are and no
  stronger: no smirk, raised brow, squint, open mouth, shock, glare or scowl.
- Big in the frame, whole head inside it, lit like the scene, never tiny, never in a corner or along the bottom,
  shoulders not cut off inside the frame. He wears the navy crew-neck T-shirt of the portraits.
- Nothing glowing on him: no rim light, halo, outline or colour wash.
- No grey grounds, no orange flood grounds, no blurred blob behind him. Bright, clear, vibrant.
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

## How to make it: direct art direction of the image model
You write the art direction; the image model (ChatGPT image generation through the Codex CLI) renders the complete
thumbnail, type included. `briefs/example_art_direction.txt` is a prompt that produced a strong thumbnail in one shot;
read it for the level of precision.
```
cd "{WORK}"
{PY} {SKILL}/scripts/gen.py --prompt build/cNN/p1.txt --out build/cNN/a.png --takes 3 \
   --ref "PORTRAIT of the man (his smile)=refs/leon/leon_front.jpg" \
   --ref "PORTRAIT 2 of the same man (his serious look)=refs/leon/leon_serious.png" \
   --ref "LOGO: the official mark=refs/logos/claude_spark.png"
```
- `gen.py` exits with an error code and prints `ERROR` when a take fails; check its output before using a file.
- Takes come back as `a_1.png`, `a_2.png`, `a_3.png`, one to four minutes a round (all designers share one queue).
  Give the Bash call a 600000 ms timeout. At most 5 reference images a call.
- **To edit** instead of starting over, attach the image first:
  `--ref "BASE (the image to edit; keep everything identical except what the prompt lists)=build/cNN/a_2.png"` and
  write the prompt as "Keep this image exactly as it is. Change only: 1. ... 2. ...". Attach his portraits whenever
  the edit touches him.
- You may attach ONE real thumbnail from `research/thumbs/` as a structure reference ("take only its structure and
  level of finish; none of its words, people, logos or colours"). Never let another person's face or brand through.
- Describe like an art director: what is where (thirds or percentages), how big, what colour (hex), what the type
  looks like, where the light comes from, the exact text in quotes and "no other text anywhere". Name his features in
  words as well as attaching the portraits (round full face, white swept-up hair, grey-white goatee and moustache,
  fair skin, mid-forties).
- **The image model cannot draw the Claude spark reliably,** and the likeness pass that follows yours re-renders the
  whole image and redraws it again. So design for a mark that can be pasted: keep every logo flat and facing the
  camera (on a flat tile, a card, the ground), not on a curved or tilted surface, not behind glass, not as a 3D
  object. Ask the model for the mark in that place, then paste the official PNG over it:
  `{PY} {SKILL}/scripts/tools.py logo <img> <out.png> --logo refs/logos/claude_spark.png --box x,y,w,h [--rot deg] --clear`
  (`--clear` removes the model's drawing first; it needs open ground round the mark, so leave at least 12 px between a
  logo and the nearest letter or shape). Look at the pasted mark and its neighbours at 3x before you go on.
  Record every pasted logo in your JSON (`logos`, below) so it can be pasted again after the likeness pass. If your
  idea truly needs the mark on a 3D object, say so in your caveats: it will be the model's drawing, not the official
  mark, and Leon should know.
- Budget: about 12 generations.

## Look, judge, fix (this is the job)
After every round, LOOK at each take at full size (Read the PNG), then where it will live:
```
{PY} {SKILL}/scripts/tools.py sheet build/cNN/sheet1.jpg build/cNN/a_1.png build/cNN/a_2.png build/cNN/a_3.png
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
3. **Is it him?** Compare with the matching portrait, feature by feature, at native size: face shape and width, eyes,
   brows, nose, smile size, beard, age. If not, re-roll or edit with both portraits attached. (A separate likeness
   pass follows yours, but start it from a face that is already close.)
4. **Every letter right; the logo right.** Read the text character by character.
5. **Bottom-right clear? Nothing glowing on him? Nothing jammed against an edge or another element? Can anything be
   misread (a struck-through word that changes the sentence, a mark that looks like punctuation)?**
Then fix the single biggest weakness and look again. Stop when you would put your name on it. If the concept as briefed
cannot be made to read in one second, say so and deliver the strongest version of the same click reason, with a line
on what you changed.

## Deliver
- `out/cNN.jpg`: the final, via `{PY} {SKILL}/scripts/tools.py export <best.png> out/cNN.jpg` (1280x720; no sharpening).
- `out/cNN_full.png`: a copy of the full-size original the final came from. Keep one for every delivered image.
- `out/cNN_feed.jpg`: its final feed sheet.
- Optional `out/cNN_b.jpg` (+ `out/cNN_b_full.png`): one alternative. A different ground (a dark version beside a bright
  one) is welcome: Leon likes being offered that choice.
- `out/cNN.json`: `{"id", "words", "title", "one_second": "what a stranger takes from it at a glance", "why",
  "face_pct", "portrait": "smile | serious", "logos": [{"image": "cNN | cNN_b", "logo": "refs/logos/claude_spark.png",
  "box": "x,y,w,h in pixels of the full-size PNG", "rot": 0}], "own_read": {"text_exact", "likeness", "legible_168"},
  "caveats": "anything Leon should know: a claim to double-check, a weakness left, a logo the model drew",
  "generations_used", "alt_b": "what the B version tries"}`. `own_read` is your opinion, not a pass: independent
  checks follow, and nobody will take your word for the likeness.
Keep your prompts in `build/cNN/`. Reply in five lines at most: what you delivered, the words, the one thing you're
least sure about.

**If you are sent a fix later** (after the checks): make it as an image-model edit of the full-size PNG, re-paste the
recorded logos, re-export, update the JSON, and say plainly that the image changed, because the likeness pass and the
final inspection must then run again on it.
<!-- END BRIEF -->
