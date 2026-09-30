# Editing spec (the quality contract)

This is the creative and technical spec for the pro edit. It carries the create-video-shorts spec over to long-form
YouTube: the same taste, style, camera language, sound design and fact checking, re-tuned for a 10-30 minute video
that people watch sitting down. Every number here was either tuned on real shorts output or measured on a real
long-form test edit. Follow all of it. Where the user's request says something different, the user wins.

Contents: [0 Principles](#0-principles) · [1 Foundation cut](#1-the-foundation-cut) · [2 Hook and body](#2-hook-and-body) ·
[3 Beats](#3-the-beats) · [4 Geometry](#4-geometry-169) · [5 Graphics](#5-graphics-style) · [6 Audio](#6-audio) ·
[7 Captions, chapters, publishing](#7-captions-chapters-publishing) · [8 Assembly](#8-assembly-in-resolve) · [9 Report](#9-report)

## 0. Principles
- **The recording carries a long-form video.** The viewer came for the speaker and the screen. Every enhancement must
  help them see what is being talked about, or (in the hook only) pull them in. If a beat only decorates, drop it.
- **Hook loud, body quiet.** The hook may be as energetic as a short. After it, restraint: no music, no keyword pops,
  no layout gymnastics - just the right zoom, highlight, source or card at the right word.
- **Real over invented.** Anything that happened (a release, a number, a quote, pricing, a benchmark, a docs
  statement) is shown as its real source: the real page, the real UI, the real numbers from the recording.
- **Animate the action, never label it.** No pills, chips or text rows restating the narration.
- **Nothing on V1 or A1 changes** except static punch-in transforms on camera items. Every addition is its own clip
  on its own named track, so the user can nudge, disable or delete any of it in Resolve.
- **Work autonomously** from the go-ahead to the assembled timeline. Make every judgement call yourself (which take,
  which beats, a figure that disagrees with its sources, a page behind a login), keep going, and log it in the
  report. Stop only if the timeline or its media can't be read.

## 1. The foundation cut
The pro edit sits on a clean foundation cut: every thought said once, in its best take, without fillers, stumbles
or noises (`references/foundation-cut.md`, `references/editorial-rules.md`).
- If the chosen timeline is already a clean cut (made by this skill, by davinci-resolve-video-edit - its name ends in
  "Clean Cut vN" - or cut by the user), **reuse it as it is**. Never re-cut what the user already approved; they may
  have added transitions, sounds or titles to it.
- Otherwise make the foundation cut first, then continue on the new "Clean Cut" timeline.

## 2. Hook and body
**hook_end** is the first sentence boundary where the content starts ("First, let's...", "So let's jump in",
"Let me show you..."), normally 20-45 s in, never past ~60 s. Snap it to the V1 cut there. If the editor put a
transition on that cut, hook_end is the cut in the middle of the transition.

**The hook (0 -> hook_end): short-form energy.**
- Something changes every 2-4 s. Rotate the tools: screen zooms with highlights, punch-ins on camera shots,
  full-visual graphics, and at most one or two splits (camera card with the head pop-out).
- Two beats in a row never share a layout or a tool. Every sentence of the hook gets a treatment.
- 3-6 keyword pops on the words that carry the promise (numbers, product names, the outcome). Never two in a row,
  never function words, never over a graphic that already shows the word.
- Music under the whole hook (section 6). The riser lands exactly on hook_end.
- Up to three whips (whoosh) in the hook.

**The body (hook_end -> end): restraint.**
- The plain recording is the default. A beat appears when the viewer needs help seeing something: a UI control
  being clicked, a number, a line of code or prompt being read, a setting, a result, a page the speaker cites.
- Density: about one beat per 20-40 s, following the content, not a quota. Tutorial stretches with lots of clicking
  can have more; talk-only stretches may have none. Never two graphics back to back without the recording between
  them.
- No music. No keyword pops. No splits. A whip (with its whoosh) only into or out of a full-visual resource, at
  most one every couple of minutes.
- CTA cards whenever the speaker points to the community, a download or a link (section 3).

## 3. The beats
Every beat is an entry in `edit_plan.json` with a programme time range [t0, t1] snapped to frames. Cues sit on
words: a move starts 0.25 s before the word that names its target; a mark lands on the word.

**zoom - push into the screen recording (hook and body).** The workhorse.
- The camera starts at the V1 framing (k = 1), so the cut into the clip is invisible. It pushes in 0.6-0.9 s
  (power2.inOut), holds while the thing is discussed (a slow glide is fine), steps between targets (0.5-0.7 s), and
  pulls back to k = 1 before the clip ends when the next V1 item continues the same screen. It may end zoomed only
  when V1 cuts to a different shot anyway.
- k is 1.2-1.9 (1.3-1.6 for UI, up to 1.9 for a single small control). Never so far that text goes soft.
- Frame targets so they stay clear of the webcam: in every zoom and every screen-scene graphic the PiP is held still
  exactly where V1 has it. `look.py --zoom k,fx,fy` shows the view (magenta) and what the PiP will cover (red).
- Marks (at most one or two on screen at once, on the word, gone when the talk moves on):
  - `box`: a clay outline for a control, button, menu item or value. Lands with a small settle.
  - `band`: a marker-pen sweep for a line of text, a row or a number being read. A clay wash on dark UI and a
    multiply tint on light pages, chosen automatically.
  - `spot`: dims everything else (45%) to isolate a region on a busy screen.
  - `underline`: a sweeping clay bar under a phrase in a paragraph.
- A beat never crosses a V1 title, generator or transition the editor added, and stays inside one scene.
- SFX: nothing on the moves. A `click` only where the recording shows a real press.

**punch - static punch-in on camera items (hook and body).** Full-frame camera shots only.
- A static zoom (1.10-1.20) on the V1 item itself, with the eyes on ~38% of the frame height and the face's x kept.
  It is a native Resolve transform, so it stays editable and graded with the shot.
- Hook: alternate framings on consecutive camera items (a jump cut becomes a punch-in). Body: only on emphasis
  lines (an opinion, a verdict, a punchline), never on two items in a row.
- No moves on the camera footage and no punch-ins inside an item (the spec's "no zooms on my footage" rule for
  moving pushes still holds; a clean cut to a tighter framing is allowed).

**gfx - full-visual graphics (HyperFrames).** Three layouts:
- `fv`: the whole frame (camera scenes, or when the screen is irrelevant).
- `fvp`: the whole frame except the webcam corner, which stays exactly as in V1 (screen scenes). Default for the
  body, so the speaker never disappears mid-tutorial.
- `split` (hook only): the graphic on the left, a camera card on the right with the speaker's head and shoulders
  popping out above the card's top edge.
- Resources: when the speaker cites or mentions something outside the recording (docs, a blog post, a repo, a
  paper, a tweet, a pricing page, an announcement), capture the real page and show it in the capture frame with the
  inner camera moving to the passage and a band on the sentence referenced. When the recording already shows the
  page, prefer a zoom on the recording.
- A named product: its official logo large and centred first, then the real UI doing the action. "Claude Code"
  means the Claude desktop app UI, never a terminal, unless the speaker is talking about the terminal.
- Length: the phrase it illustrates, typically 4-10 s. Frame 0 is the landing state (content visible, camera at
  rest), because it hard-cuts in.

**words - keyword pops (hook only).** 1-3 words, Poppins Bold 80 white with an 8 px black stroke; a highlight
(the key word) in Instrument Serif italic 96, pure yellow #FFFF00, 9 px black stroke. Centre (960, 905), lower
third, clear of the face and of any graphic text. Pops in over 0.18 s (scale 0.86 -> 1), holds for the phrase,
fades over 0.14 s.

**cta - the community card (body).** The long-form version of the shorts' comment box: a white card at the bottom
left with the spec shadow, an avatar or logo, a one-line label, the URL typed with a clay caret starting on the
word that names the place, then a clay button press. 4-6 s. Pop on landing, key ticks while typing, click on the
press. Use the user's real URLs (skool.com/leonvanzyl for the free community, skool.com/agentic-labs for Agentic
Labs) unless the video names another.

## 4. Geometry (16:9)
Layout px are 1920x1080; renders are made at the timeline's resolution (x2 on UHD).
- **Webcam PiP:** wherever the recording has it (`scenes.py` finds it per source file). Held still in every zoom
  and `fvp` graphic by pasting the same frame's pixels back, so it never jumps on a cut.
- **Capture frame** (radius 32, white, shadowed, on its washed, blurred clone): fv x 160, y 72, 1600x936;
  fvp x 64, y 72, 1440x936; split x 64, y 90, 1112x900. The frame never moves; the footage pans inside it.
- **Split:** squircle card x 1236, y 318, 760x842, radius 120, bleeding off the right and bottom edges. The whole
  face fits inside the card with the hair ~96 px above its top edge; the matte and the card come from the same
  frames. The world keeps its content in x 64-1176 and fades out from x 1180 over 120 px.
- **Content bounds:** fvp content stays left of x 1504 while the PiP is top right. Nothing important within 48 px
  of any edge.
- **Keyword pops** centre (960, 905). **CTA card** x 64, y 836, 900x176.

## 5. Graphics style
Luxury tech: one bright world of floating white cards, and a camera that moves through it (the shorts' engine,
generalised to 16:9 - `references/graphics.md`).
- Ground: radial near-white (#FFFFFF at 50%/36%, #F3F3F0 at the edges). No grid, no orbs, nothing dark except real UI.
- Shadow on every card: 0 60px 120px rgba(24,24,32,.16), 0 24px 48px rgba(24,24,32,.10), 0 4px 10px rgba(24,24,32,.06).
  Radii: media 3% of the width, docs 40, tiles 72, phones 84, captures 32.
- Type: Poppins. Headline 88/700, subhead 52/700, body 30/400; nothing under 30 px. Ink #111111. Clay #D97757 for
  fills, #B25730 for clay text on white, highlight band #FBEEE8, green #34C759 for checks, red #FF3B30 for stamps.
- Camera: glide (sine.inOut, scale change <= 0.04), step (0.5 s power3.inOut, 0.25 s before the word), push
  (1.2-2 s power2.inOut, up to ~1.6x), pull (1-2 s), at most one whip per graphic (0.45 s out power3.in, 0.6 s in
  power3.out). While a product window is the subject only its inner camera moves (1.15-1.4x, 0.4-0.7 s).
- Depth of field: the card being read is sharp; neighbours blur up to 14 px and dim 30% as the camera pushes; an old
  hero drops to a 9 px blur at 40%. Never blur a word the viewer needs to read.
- Motion blur on every move: graphics render at 4x the timeline rate with per-frame directional blur and blend 3 of
  every 4 frames; zooms use a 4-sample 270-degree shutter. A blurred frame at rest is a bug.
- Sparse scenes: one dominant subject, at most one supporting cue, smooth eased motion, never frantic.

## 6. Audio
All synthesized in code (`scripts/audio.py`), clean, modern and premium, never cartoony. Levels are baked into the
files, because Resolve's scripting API cannot set clip volume.
- **Voice:** the timeline's own A1, untouched. Levels below are measured against its robust peak (the 99th
  percentile of 100 ms peaks) and its hook loudness.
- **SFX**, one per meaningful visible event: a soft bubbly click on real presses, a key tick run on typing, a dull
  pop when a card lands, a two-note chime on an answer or confirmation, a low airy whoosh whose loudest moment lands
  exactly on the whip midpoint (whips only; rotate the four variants). Nothing on zooms, punch-ins, steps, pushes,
  glides or cuts. Peaks vs the voice: click, pop, chime -10 dB; whoosh -9 dB; keys and ticks -16 dB.
- **Riser:** a 2.6 s low swell whose audible end lands exactly on hook_end, -12 dB. The one sound allowed to rise
  into a cut.
- **Music - the hook only.** Synthesized for this video (never a repeat: the seed comes from the timeline name).
  Pick the style that fits the topic and energy - lofi (the default for talking-head tech), chillhop (relaxed
  how-tos), ambient (serious or reflective), synthwave (retro, hype), upbeat house (launches and wins) - and a mood
  (warm or moody). A low-passed intro, the beat drops at the end of the hook's first sentence, ~18 LU under the
  hook's voice, sidechain-ducked ~5 dB under speech, and it **fades out over 2-3 s starting at hook_end**. Nothing
  after that: long-form viewers tire of a bed under a tutorial.
- **Final loudness** is set on delivery: the added layers are levelled against the voice, so normalising the whole
  mix to -14 LUFS (YouTube) in Deliver keeps the balance. Say so in the report.

## 7. Captions, chapters, publishing
- **Captions** are not burned in. `publish.py` writes `captions.srt` from the final word timings (fillers and noise
  tags removed, at most two lines of 42 characters, at most 6 s per cue) for YouTube Studio.
- **Chapters:** a blue marker on the timeline and a line in PUBLISH.md for each section. The first is at 0:00, at
  least three, each at least 10 s long. Titles are specific and searchable ("Opus 5.5 results", not "Part 3").
- **PUBLISH.md**, written after the edit is final, from what it actually says:
  - Title: 60 characters or fewer, the main search term first (the tool, model or topic people type into search),
    no claim the video doesn't back up, no emojis or hashtags.
  - Description: two or three natural, keyword-rich lines (about 300 characters) on what the viewer learns, accurate
    against the fact check.
  - Then the chapters, then these two lines exactly as written, each followed by a blank line:
    🎁 Get the resources from this video + my free AI builder course: https://skool.com/leonvanzyl
    🚀 Go deeper inside Agentic Labs: AI coding courses, live Q&A, weekly challenges, and direct access to me: https://skool.com/agentic-labs

## 8. Assembly in Resolve
- The pro edit is a **duplicate of the clean cut** named "<clean cut base name> - Pro Edit vN", so everything the
  editor put on it (transitions, sounds, titles, grades) is kept. The clean cut itself is never modified.
- New tracks go above whatever exists: "PE Graphics" (zoom and graphic clips), "PE Overlays" (alpha: keyword pops,
  CTA cards), "PE SFX", "PE Music", "PE Riser" (stereo).
- Clips are placed at exact frames; punch-ins are transforms on V1 items; chapters and a "Listen: hook -> content"
  marker go on the timeline. Verify the build (`references/resolve-assembly.md`) before reporting.

## 9. Report
`report.md` next to the renders:
- Inputs: the timeline, the clean cut used (or made), sources and scenes (camera vs screen, the PiP window).
- The hook: hook_end and why, every beat in it with its cue words.
- The body: every beat with its time, what it shows, the sources used, and why it earns its place.
- Graphics: one line per composition (what it shows, real sources, camera moves, whips).
- Audio: the music (style, mood, key, tempo, seed, drop, level, fade), the riser, every SFX with its time and level.
- Fact check: each figure the speaker says, with 2+ sources, and any disagreement.
- The Resolve build: timeline name, tracks, clip counts, verification results, anything the user must do (delete
  the archived duplicate, normalise loudness on delivery).
- Every judgement call.
