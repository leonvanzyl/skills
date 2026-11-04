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
- **Hook loud, body visual.** The hook may be as energetic as a short. The body keeps moving too: the viewer is
  constantly SHOWN what is being said - a zoom with a highlight, the real article or page, an explainer graphic, a
  logo, the speaker's own video - so theory never sits on a static slide. No music, no keyword pops and no layout
  gymnastics after the hook: the energy comes from showing, not from decoration.
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

**The body (hook_end -> end): always showing something.** (The standard since the Harness Engineering edit, which
Leon called "energetic... things move... constantly showing examples and B-roll... phenomenal".)
- Every stretch gets the visual that helps most: a zoom with marks on the slide, code or UI being talked about; the
  REAL source (article, docs, X post, pricing page, repo) at every citation, with the cited line highlighted; an
  explainer graphic wherever the speaker explains how something works (a system, a flow, a comparison, a number);
  official logos when products are named; the speaker's own YouTube watch page / thumbnail at every "I have a video on".
- Density, measured on that edit (16 min, mostly slides and theory): 34 zooms + 27 graphics + 4 CTA cards in a
  15-minute body - a new visual beat about every 14 s, and about 80% of the runtime covered by a zoom or a graphic.
  Aim for that on theory and slides: no static slide or plain talking head for more than ~30 s unless the plain
  shot is genuinely the best view (a personal story told to camera, a demo where the full screen is clearer).
- Explainers are the heart of it: the processes the speaker describes in words (here the software-factory swarm,
  task ingestion and allocation to agents, the harness levels, context budgets) become animated diagrams in the
  channel's style, cued word by word. One continuous "world" may span two graphics back to back (an invisible cut);
  otherwise the recording or a zoom sits between graphics.
- No music. No keyword pops. No splits. A whip (with its whoosh) only into or out of a full-visual resource, at
  most one every couple of minutes. Sound design follows the visual events (section 6): pops on every animation,
  a soft whoosh into each graphic, a highlight swish or ding on a zoom's first mark only (accents are rare).
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
  - `box`: an accent outline (azure, `config.MARK`) with a soft accent glow, for a control, button, menu item or
    value. Lands with a small settle.
  - `band`: a marker-pen sweep for a line of text, a row or a number being read. An accent wash on dark UI and a
    soft blue multiply tint on light pages, chosen automatically.
  - `spot`: dims everything else (45%) to isolate a region on a busy screen.
  - `underline`: a sweeping accent bar under a phrase in a paragraph.
- A beat never crosses a V1 title, generator or transition the editor added, and stays inside one scene.
- SFX: nothing on the moves. In the body only a zoom's FIRST mark sounds: a highlight swish when a band or underline
  sweeps, a soft ding when a box lands (dings at least 15 s apart; section 6), a `click` only where the recording
  shows a real press.

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
- `fvc` (camera scenes): the whole frame with the camera in a corner window. With separate webcam + desktop
  recordings the window is the dynamic camera's (384 px square, 40 px margin, top-right unless the beat's
  `"dyncam_corner"` says otherwise): brief the graphic to keep that square clear. `fv` hides the camera.
- Resources: when the speaker cites or mentions something outside the recording (docs, a blog post, a repo, a
  paper, a tweet, a pricing page, an announcement), capture the real page and show it in the capture frame with the
  inner camera moving to the passage and a band on the sentence referenced. When the recording already shows the
  page, prefer a zoom on the recording.
- A named product: its official logo large and centred first, then the real UI doing the action. "Claude Code"
  means the Claude desktop app UI, never a terminal, unless the speaker is talking about the terminal.
- Length: the phrase it illustrates, typically 4-10 s. Frame 0 is the landing state (content visible, camera at
  rest), because it hard-cuts in.

**words - keyword pops (hook only). LOCKED DESIGN (user-approved 2026-10-13): the channel's own slide system.**
Leon's slides follow the "Leon YouTube" design system (bundled in `references/design-system/`: graphite stage,
Figtree, Geist Mono labels, azure #2F95FF primary accent, ember #FF8A5B second - the orange dot of the cognaitiv logo on
his shirt). A keyword pop is a small piece of that system:
- a graphite glass chip: fill stage-800 rgb(24,25,28) at ~88% (more opaque than the slides' 62% glass, since an alpha
  overlay can't blur what is under it), radius 28 (the panel radius), a 1.5 px accent hairline (accent at ~33%), a
  1 px white top highlight at ~9%, the long panel shadow (0 50 120 -40, black ~78%) and the highlighted-panel bloom
  (accent at ~60%, blur ~46 px, inset 30 px);
- the words in Figtree 600 white at 62 layout px, tracking -0.025em (the title tracking), kerning kept, padding 40 x 26;
- beneath them the accent line (5 px, radius 3, with a soft glow), below the descenders, drawn left to right 0.10 s
  after the landing over 0.40 s (power3.out); azure by default, `"accent": "ember"` for costs/warnings or variety;
- optional `"label"`: a Geist Mono 500 uppercase eyebrow (18 px, 0.14em tracking, text-muted #7E818A) above the words.
Centre (960, 905), lower third, clear of the face and of any graphic text. Lands over 0.26 s (scale 0.96 -> 1, rising
12 px, power3.out), holds for the phrase, fades over 0.18 s. SFX: a soft pop on the landing and a highlight swish as
the line draws. Fonts ship in `assets/fonts` (Figtree-VF.ttf, GeistMono-VF.ttf, both OFL). Rejected: yellow
Instrument Serif italic with a black stroke ("not professional for a tech channel"), and a white chip with a clay
highlighter ("not sure it matches the channel brand").

**cta - the community card (body).** The long-form version of the shorts' comment box, in the channel's design
system: a graphite glass card (stage-800 at ~96%, white hairline and top highlight, radius 28, the long panel shadow)
at the bottom left, the avatar in a circle, a Geist Mono uppercase label (muted), the URL typed in Figtree 600 white
with an azure caret starting on the word that names the place, then an azure button (with a soft glow) that darkens
to azure-ink on the press. 4-6 s. Pop on landing, key ticks while typing, click on the
press. Use the user's real URLs (skool.com/leonvanzyl for the free community, skool.com/agentic-labs for Agentic
Labs) unless the video names another.

## 4. Geometry (16:9)
Layout px are 1920x1080; renders are made at the timeline's resolution (x2 on UHD).
- **Webcam PiP:** wherever the recording has it (`scenes.py` finds it per source file). Held still in every zoom
  and `fvp` graphic by pasting the same frame's pixels back, so it never jumps on a cut.
- **Separate webcam + desktop recordings: the dynamic camera** (`dynamic-camera.md`). FULL / CARD (756x936 at
  1100,72 beside a 1000x562.5 content panel at 64,258) / SMALL (384 px square, 40 px margin, radius 22) / HIDDEN, eased
  morphs at cuts, top-right by default (YouTube's bottom strip holds the controls, captions and watermark; AI tools keep
  the prompt and newest output at the bottom), another corner only where the content needs it.
- **Capture frame** (radius 32, white, shadowed, on its washed, blurred clone): fv x 160, y 72, 1600x936;
  fvp x 64, y 72, 1440x936; split x 64, y 90, 1112x900. The frame never moves; the footage pans inside it.
- **Split:** squircle card x 1236, y 318, 760x842, radius 120, bleeding off the right and bottom edges. The whole
  face fits inside the card with the hair ~96 px above its top edge; the matte and the card come from the same
  frames. The world keeps its content in x 64-1176 and fades out from x 1180 over 120 px.
- **Content bounds:** fvp content stays left of x 1504 while the PiP is top right. Nothing important within 48 px
  of any edge.
- **Keyword pops** centre (960, 905). **CTA card** x 64, y 836, 900x176.

## 5. Graphics style
**The channel's own design system** ("Leon YouTube", bundled in `references/design-system/` - read its
`readme.md` and tokens before designing anything new): his slides are a product keynote on a graphite stage, and the
B-roll is that deck come alive. The engine's default `theme: 'stage'` paints it (`references/graphics.md`); the old
bright white world (`theme: 'paper'`) was rejected for this channel ("it needs to be done right", 2026-10-13).
- Ground: the stage - stage-800 #18191C fading to stage-950 #0B0C0E under a soft overhead spotlight, two faint light
  beams, the animated horizon WAVE of dots glowing in the accent (Stage.jsx `paintWave`, time-driven), a vignette.
- Surfaces: `glass` panels for explanations and diagrams (stage-800 at 62% + 24 px backdrop blur, white hairline,
  inset top highlight, shadow 0 50 120 -40 black 85%; one `highlight` per scene = accent hairline + bloom); white
  `window`/`paper` for real product UI, chats, files, issues, repos and captures (window radius 22, card 24, the
  dark window/card shadows). No glass inside glass, no paper inside glass.
- Type: Figtree 600 (display 140 -0.035em, headline 96 -0.03em, statements 54 -0.025em), Figtree 500 accent
  subtitle (46), body 30 in text-secondary #A3A6AD, Geist Mono uppercase labels (22, 0.14em, muted #7E818A, parts
  joined by a middle dot), code in Geist Mono with the code token colours. Nothing under 22 px on the stage; pills
  on paper may go to 14. Tabular numerals.
- Colour: one accent per scene - azure #2F95FF (default) or ember #FF8A5B (costs, security, warnings, refusals);
  mint #4FD6A0 for passes and checks; iris only on icon tiles. Winners white or accent, losers text-secondary.
  Status on paper as pills (azure/mint/ember wash + ink). No clay, no pure red, no Poppins.
- Personality: the design system's glossy 3D icon tiles (`tile_html`: azure code, iris bolt, mint eyes/check, ember
  bars) and real product logos on paper chips or glass tiles.
- Layout: the webcam lane stays clear (content left of x 1504 in `fvp`); text on the bare stage ends above y≈780
  (the wave's crest glows lower) - anything lower sits on glass or paper.
- Camera: glide (sine.inOut, scale change <= 0.04), step (0.5 s power3.inOut, 0.25 s before the word), push
  (1.2-2 s power2.inOut, up to ~1.6x), pull (1-2 s), at most one whip per graphic (0.45 s out power3.in, 0.6 s in
  power3.out). While a product window is the subject only its inner camera moves (1.15-1.4x, 0.4-0.7 s).
- Depth of field: the card being read is sharp; neighbours blur up to 14 px and dim 30% as the camera pushes; an old
  hero drops to a 9 px blur at 40%. Never blur a word the viewer needs to read.
- Motion blur on every move: graphics render at 4x the timeline rate with per-frame directional blur and blend 3 of
  every 4 frames; zooms use a 4-sample 270-degree shutter. A blurred frame at rest is a bug.
- Sparse scenes: one dominant subject, at most one supporting cue, smooth eased motion, never frantic.

## 6. Audio
Real recorded sounds from the royalty-free SFX library (the skill's `assets/sfx`, built by `sfx_library.py`,
licences in its manifest; `sfxlib.py` rotates the recommended picks and lands each sound on its onset or, for
whooshes and risers, its peak), synthesized stand-ins only when the library is missing. Clean, modern and premium,
never cartoony. Levels are baked into the files, because Resolve's scripting API cannot set clip volume. The user
found synthesized SFX "bland and generic" (2026-10-13).
- **Voice:** the timeline's own A1, untouched, with the user's own voice chain (EQ, voice isolation, de-esser,
  dynamics) on its track - it comes with a duplicated timeline and must be put back on a rebuilt one (section 8).
  Levels below are measured against the RAW voice (`voice48.wav`): its robust peak (the 99th percentile of 100 ms
  peaks), its speaking loudness and its hook loudness. The master sets the processed voice back to that reference.
- **SFX**, one per meaningful visible event: a real click on presses, key ticks on typing (single-key samples, one
  per character), a soft pop when a card lands, a success chime on an answer or confirmation, a marker swish when a
  highlight band or underline sweeps (zoom marks, graphic reveals, the keyword pop's accent line), a soft bell ding
  when a box mark lands, a soft whoosh peaking on the cut into each full-visual graphic (not between two graphics of
  one continuous world), a whoosh on the whip midpoint, and a tasteful hit (sting) on hook_end. A highlight or ding
  never stacks within 0.15 s of another event. Nothing on zooms' camera moves, punch-ins, steps, pushes or glides.
  `auto_sfx: false` in the plan turns the derived events off.
- **No dings, bells or chimes (since 2026-10-20).** After the OpenCode 2.0 edit Leon wrote "The dings / bells / high
  pitches is a bit much. Swooshes, swipes, pops are fine." `LONGFORM_RULES` now has `exclude_types=('ding', 'chime')`:
  box marks land silently, success moments have no chime - hook included. Pops, clicks, key ticks, highlight swishes,
  whooshes, the riser and the hit stay. A plan brings them back with `"sfx_rules": {"exclude_types": []}`. (The rules
  below still describe how dings/chimes are paced when a plan turns them back on.)
- **How often (the body).** Leon's pick in an A/B/C test (2026-10-16), after a viewer wrote "the new sound effects get
  annoying fast - ding, scribble, ding, ding, ding". Texture sounds (pops, clicks, keys, soft whooshes) may be
  frequent; accents (ding, chime, hit) are rare and mean something. `sfxlib.select` with LONGFORM_RULES: only the first
  ding and the first scribble of a zoom or graphic; at most 5 pops per animation, 0.6 s apart (every animation keeps
  its sounds: the variant that cut them to 2-3 "overcorrected"); dings / chimes at least 15 s apart; scribbles 4 s
  apart; never two sounds within 0.35 s; at most 7 sounds in any 15 s. About 10.5 sounds a minute in the body
  (Harness Engineering had 12.6, with 35 dings and 31 scribbles). The hook, CTA cards and keyword pops keep every
  sound. Plan `sfx_rules` overrides any of it.
- **How loud.** By LOUDNESS (the loudest 400 ms, K-weighted) against the voice's speaking loudness, never by peak: at
  the same peak a bell or the marker scribble sounds 6-10 dB louder than a click, which had put chimes almost level
  with the voice. Targets in LU under the voice as heard (`sfxlib.LONGFORM_TARGET`, plan `sfx_levels`): hit and chime
  -10, ding and soft whoosh -11, pop and whoosh -12, scribble -14 (its hiss tamed, about -4 dB above 7 kHz), click and
  keys -16; the hook +3 LU (`sfx_hook_bonus`; the music masks it). The files carry these levels exactly: the master
  (section 6, "Final loudness") never sends the layers through Resolve's bus, so `sfx_bus_lift` stays 0. (It was 4.5
  when the mix went through a bus compressor that lifted the quiet layers; `master.py build` still honours a plan
  that sets it.)
- **Riser:** the library's riser (cut right after its peak) or a 2.6 s synthesized swell, landing exactly on
  hook_end, -12 dB. The one sound allowed to rise
  into a cut.
- **Music - the hook only, generated for this video** (`music_gen.py`, ACE-Step 1.5 XL; a new seed per video, never
  a repeat). Leon's pick (Oct 2026, over indie-electronic, felt-piano-pop and electronic-pop takes): **uplifting
  cinematic** - "uplifting cinematic instrumental, opens with a solo emotional piano ostinato and soft pads with no
  drums, then pulsing staccato strings, warm bass and a steady driving modern drum groove enter, hopeful and inspiring,
  warm, documentary style, not an epic trailer", ~105 bpm, structure "[Intro - solo piano ostinato, quiet, no drums, no
  bass] [Build - strings, bass and drums enter] [Main Theme - full drums, driving, inspiring] ...". Generate 3-4 takes
  (this style first, plus a contrast or two), keep the ones with a soft intro that lifts and no vocals, and let the user
  choose by ear. The synthesized beds (`music.py`: lofi, chillhop, ambient, synthwave, house) are the fallback - Leon
  called the chillhop one "very boring". Soft intro, the lift lands at the end of the hook's first sentence (`drop`),
  15 LU under the hook's voice (`under_voice_lu`), ducked ~5 dB more under speech, and it **fades out over 2-3 s
  starting at hook_end**. Nothing after that: long-form viewers tire of a bed under a tutorial.
- **Final loudness - the master and the final file** (pipeline.md section 9). The deliverable is
  `$M/final/<timeline> - FINAL (-14 LUFS).mp4`, made outside Resolve's mixer:
  - the user's own tracks rendered by Resolve through their chain and bus (the base stem), set back to the raw
    voice's speaking loudness; the pro edit's tracks rebuilt from their files at unity, so the balance is exactly
    the one designed above;
  - a true-peak limiter (4x oversampled, 1.5 ms look-ahead, 80 ms release) driven to **-14.0 LUFS integrated**
    with a -1.5 dBTP ceiling, so the AAC encode still lands **under -1 dBTP**; on last-call it worked more than
    0.5 dB only 6.6% of the time, 5.2 dB at most;
  - the timeline's picture rendered with the user's own export preset, Resolve's "YouTube - 2160p" (4K, H.264 High,
    ~11 Mb/s at 4K60, ~2 GB for 25 minutes), its video stream copied, audio AAC 384 kb/s. Not a higher bitrate: the
    97 Mb/s, 18 GB first delivery took "an incredibly long time to upload";
  - measured on the DECODED final file: -14 +-0.3 LUFS, true peak <= -1 dBTP (any AAC overshoot gets a 0.5 s dip
    and a re-mux), sync 0 samples, every SFX type within +-0.5 LU of its target, hook and body loudness, the
    quietest and loudest 30 s.
  Never hand over loudness as "normalise in Deliver": on last-call Deliver's normalisation left the upload "very
  soft", and Resolve's AI Audio Assistant mangled the game music.

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
  editor put on it (transitions, sounds, titles, grades, and the voice chain, track faders and clip volumes) is
  kept. The clean cut itself is never modified.
- When a restructure forces a rebuilt timeline (lessons.md, "Restructuring a cut"), tell the user before building
  that it won't carry their voice effects, track levels or clip volumes, and run the voice-chain check (pipeline.md
  9a) once it exists: if their timeline's voice is PROCESSED and the new one RAW, they copy their chain onto its A1
  before anything is levelled or delivered.
- New tracks go above whatever exists: "PE Graphics" (zoom and graphic clips), "PE Overlays" (alpha: keyword pops,
  CTA cards), "PE Censor" (alpha blur over private details, always topmost, only when the plan has a censor beat),
  "PE SFX", "PE Music", "PE Riser" (stereo).
- Clips are placed at exact frames; punch-ins are transforms on V1 items; chapters and a "Listen: hook -> content"
  marker go on the timeline. Verify the build (`references/resolve-assembly.md`) before reporting.

## 9. Report
`report.md` next to the renders:
- Inputs: the timeline, the clean cut used (or made), sources and scenes (camera vs screen, the PiP window).
- The hook: hook_end and why, every beat in it with its cue words.
- The body: every beat with its time, what it shows, the sources used, and why it earns its place.
- Graphics: one line per composition (what it shows, real sources, camera moves, whips).
- Audio: the music (style, mood, key, tempo, seed, drop, level, fade), the riser, every SFX with its time and level.
- **The final file** first in the audio part: its path, resolution and bitrate, integrated loudness, true peak, LRA,
  sync, the voice-chain verdict, the voice gain, each SFX type's offset from its target, hook / body loudness, the
  quietest and loudest 30 s, any AAC overshoot dipped, and every `fit` flag (what Resolve's own mix does differently
  - so Resolve playback won't match the file). All of it is in `levels/master_report.json`.
- Fact check: each figure the speaker says, with 2+ sources, and any disagreement.
- The Resolve build: timeline name, tracks, clip counts, verification results, anything the user must do (upload
  the final file, not a new export from Resolve; delete the archived duplicate timelines if they like).
- Disk: what the project uses (the cleanup dry run's total) and that the cleanup runs once the user says the video
  is uploaded (pipeline.md section 10) - it removes every render, the final file too.
- Every judgement call.
