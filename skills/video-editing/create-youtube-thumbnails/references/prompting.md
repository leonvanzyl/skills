# Writing the image brief

The image model draws exactly what the brief pins down and invents everything it leaves open. **When the words and an attached image disagree, the words win.** A brief that says "flat cobalt blue background" next to a reference with a black background gets cobalt blue. So the brief does two jobs:
- It re-states the reference's look in words: its REFERENCE DNA, with measured hex values.
- It pins down what is ours: the person, the words, and the hero from the video.

A good brief reads like an art director's spec sheet: positions in percentages, exact strings in quotes, expressions as muscle movements, every reference image named by its label.

`scripts/gen.py` wraps your brief: it tells Codex to call its image tool once and pass the brief through in full, and it lists the attached reference images with their labels. Every ref description in `jobs.json` starts with an UPPERCASE LABEL and a colon (`AVATAR:`, `LOGO: CLAUDE:`, `LAYOUT REFERENCE:`, `HOUSE STYLE:`, `UI:`, `THUMBNAIL:`). In the brief, name each one by its label ("the AVATAR reference image"), never by its position.

Contents: [Reference DNA](#reference-dna) · [Brief template](#brief-template) · [Likeness](#likeness) · [Gaze and expression](#gaze-and-expression) · [Text](#text) · [Logos and UI](#logos-and-ui) · [Edit passes](#edit-passes) · [What fails](#what-fails)

## Reference DNA
Before writing a brief, take its LAYOUT REFERENCE apart:
1. `dna.py measure competitors/<ref>.jpg --sheet qa/dna_<id>.png`. This writes `refs/dna/<videoId>.json`: the background colour and value (dark, mid or light), whether it's a flat field or a scene, and the palette with shares. LOOK at the swatch sheet.
2. LOOK at the reference at full size and write down what the numbers can't see:
   - **Subject treatment:** is the person cut out with a white or coloured outline (a "sticker")? Rim light? A drop shadow? A glow behind them?
   - **Type:** font class (heavy condensed caps, rounded sans, serif, handwriting), case, colours, and what makes it read (stroke, shadow, a highlight box behind one word, an underline, an arrow).
   - **Hero treatment:** what the hero is and how it's presented (two tilted 3D tiles held up in both hands, a giant laptop screen, a scene filling the background, a card pinned beside the face) and how big.
   - **Composition grid:** where the face, the hero and the text sit, as % of the frame, and how big each is.
   - **Lighting and finish:** studio-flat, moody spotlight, glossy 3D, photographic.
3. Put all of it in the concept's `dna` field and in the brief's REFERENCE DNA paragraph.

Example (Eric Tech, "Claude Code + Ollama = Free Unlimited Coding AI", 408k views):
```
REFERENCE DNA (keep exactly): near-black flat background #0D0D0C. The creator is cut out with a thick white sticker outline
(about 1.5% of the frame width), centre, face about 22% of the frame width, head top at 25% of the frame height. The hero is two
big glossy rounded app tiles, tilted about 8 degrees outward, held up in both hands at chest height, left and right of the face,
each about 40% of the frame height. Text: one line across the top, bold rounded sans in sentence case, white, with the last word
in black on a solid yellow #FFE500 highlight box; an orange underline under the first words and a small hand-drawn white arrow
pointing down at the right tile. Clean studio light, no glow.
```

## Brief template
Write every section, in this order. Every section that describes the look must agree with the REFERENCE DNA. `gen.py --check` compares the BACKGROUND hex with the measured reference and checks the TEXT colours' contrast against it.

```
FORMAT: A YouTube thumbnail, 16:9 landscape. A faithful re-make of the LAYOUT REFERENCE for a different video: same layout,
background, palette, type style and treatment; only the person, the words and the hero content change.

REFERENCE DNA (keep exactly): <from the section above: background with hex, subject treatment, type, hero treatment, grid, finish>.

PERSON: The man in the AVATAR reference image. Keep his exact likeness: <3-5 distinctive features>. <Wardrobe>.
  Treatment: <as the reference: e.g. cut out with the same thick white sticker outline>.
  Position: <where the reference's person is>, <same scale>.
  Expression: <subtle, muscle-level description>. Natural, not exaggerated.
  Gaze: his eyes look straight into the camera lens, at the viewer.
  Hands: <as the reference's hero treatment needs, or "arms out of frame">.

HERO: <the payoff from the video, from the UI reference: e.g. "the cartoon 3D office from the UI reference image: little
  low-poly agent-workers at desks with dark terminal monitors">, presented exactly like the reference's hero (<its treatment,
  position and size>).

TEXT: Exactly "<WORDS>" (<n> words), in the reference's type style: <font class, case>, fill <hex>, <stroke/shadow/box as the
  reference>, <position as the reference>, cap height about <n>% of the frame height. No other text anywhere in the image.

LOGOS: (only if the concept shows them) Reproduce the reference image labelled LOGO: <BRAND> exactly as given: same shape, proportions
  and colours. Place it <where>, about <n>% of the frame height.

LAYOUT: {LAYOUT REFERENCE}
HOUSE: {HOUSE STYLE}

BACKGROUND AND LIGHT: <the reference's background, with its measured hex: e.g. "near-black flat #0D0D0C, as the reference">,
  <the reference's lighting>.

KEEP CLEAR: The bottom-right corner (the last 18% of the width x 15% of the height) holds no text, logo or face: YouTube puts the
  duration badge there. Nothing important within 4% of any edge.

AVOID: extra text, watermarks, fake UI with gibberish text, extra fingers or hands, warped letters, busy small detail,
  any background or colour scheme other than the reference's, <concept-specific>.
```

The shared `{LAYOUT REFERENCE}` block in `_common.md`:
```
LAYOUT REFERENCE: The reference image labelled LAYOUT REFERENCE is a top-performing thumbnail in this niche. Re-make it for this video:
keep its layout, background colour and value, palette, lighting, the treatment of the person (outline, rim light, shadow), the type
style and the way the hero is presented, as written in REFERENCE DNA. Replace only its person (with the man in the AVATAR image), its
words (with the TEXT above) and its hero content (with the HERO above). Never copy its person, its words, its logos or its screenshots.
```

## Likeness
- One clear, evenly lit, front-facing photo already gives a strong likeness. Two or three photos (front, three-quarter, a big expression) make it near-certain; attach the ones that match the pose you want.
- Name the distinctive features in words as well (hair colour and style, facial hair, glasses, build). Check every word against the photo; never write them from memory. The model holds onto what you name.
- Always attach the avatar again on an edit pass (`AVATAR: the real person, reference for his exact likeness`), or the face drifts over several edits.
- Never ask for a different age, body or skin. If it comes out different anyway, that's a failed render: regenerate it.

## Gaze and expression
Eyes always go straight into the lens; write it in every brief. Expressions stay subtle. Describe the face, not the feeling: "slightly amazed" came back as a smile with a hand on the chin, and "delighted gasp" came back goofy. Use these:
- **Knowing / "this beats that":** lips closed, one corner of the mouth slightly raised, the brow on that side lifted a few millimetres.
- **Serious / contrarian:** lips closed and relaxed, brows very slightly lowered, a steady direct stare.
- **Skeptical:** one eyebrow raised slightly, lips pressed together in a faint, unimpressed line.
- **Satisfied / payoff:** a calm closed-mouth smile, relaxed brows.
- **Concerned:** brows drawn slightly together, lips pressed, chin a touch down.
Add "Natural, not exaggerated." Never ask for an open mouth, a gasp or wide eyes, even if the reference's creator has one.

Say where his hands are, or say "arms out of frame". Hands left unspecified tend to wander onto the chin.

## Text
- Give the exact string in quotes and the word count. Add "No other text anywhere in the image".
- 1-4 words. Each extra word costs readability at 168 px.
- Set it in the reference's type style and position. Give every colour as a hex value, and write stroke and shadow colours as such ("with a black stroke #000000"). Write text on a box as "<fill hex> on a <box hex> box" (for example "white #FFFFFF on a solid orange #D9480F box"). `gen.py --check` measures each fill colour against the background, and boxed text against its box.
- Text renders reliably at this length. Still check every letter at full resolution; a single wrong letter rejects the image.

## Logos and UI
- Never let the model draw a logo from memory. Attach the official mark from `refs/` and say "reproduce the reference image labelled LOGO: <BRAND> exactly". Then stamp the official file over its version anyway (`scripts/stamp.py`): even with the file attached, the model redraws the mark.
- Transparent PNGs work best. Say where it goes and its size.
- **The video's world is a UI reference too.** Frames of the recording (the product, the scene, the result) attached as `UI:` make the hero look like the real thing. In the CubeFarm run, frames of the real 3D office made every render match the app's actual art style.
- For product UI, say what to keep (the layout and the colours) and what may be simplified (small body text becomes clean grey lines, not fake words).

## Edit passes
Use an edit for every fix after the first render. Don't re-roll a good image to fix one thing.
```
EDIT the reference image labelled THUMBNAIL (a YouTube thumbnail). Keep everything identical (composition, lighting, colours, text, logo, background)
except these changes:
1. <one precise change>
2. <at most one more>
The man must still match the AVATAR reference image exactly.
```
- Attach the thumbnail first (`THUMBNAIL:`), then the avatar (`AVATAR:`), then any logo involved in the change (`LOGO: <BRAND>:`).
- Make one or two changes per pass. More than that and the model starts re-composing the image.
- A fidelity FAIL on the background can be fixed with an edit ("change only the background to near-black #0D0D0C, as the LAYOUT REFERENCE"), attaching the LAYOUT REFERENCE as well.

## What fails
- **Inventing the look:** a background, palette or type style the reference doesn't have. It is the most common failure, and the first thing `gen.py --check` and `dna.py fidelity` catch.
- **Inventing the hero:** a prop the video doesn't show (a phone game, a brain, logo tiles standing in for "coworkers"). The thumbnail ends up about something else.
- **Abstract metaphors drawn small:** they read as texture at 168 px.
- **Fake screens:** UI the model invents fills with gibberish. Use a real frame or capture.
- **Too many logos:** more than two and none of them read.
- **Stacked claims:** a title, a number, an arrow, a logo and a face all fighting. Cut back to the one idea.
