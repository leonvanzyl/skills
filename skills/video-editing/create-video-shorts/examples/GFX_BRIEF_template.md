# Graphics brief (shared by every graphics subagent) — TEMPLATE
<!-- Copy to work-<stem>/GFX_BRIEF.md, fill every <...>, delete what doesn't apply. The filled-in brief of the reference run
     is examples/harness-engineering/GFX_BRIEF.md: match its detail. Then start a FEW LONG-LIVED graphics agents (2-4, one
     per 1-2 shorts, grouped by kind: real sources / footage, concept diagrams, one continuous world), each with a short
     prompt: "read GFX_BRIEF.md and every reference it lists; your tag is <a>; your compositions are <ids>". Never one agent
     per 2-5 compositions: Leon wants few long-lived agents (the reference run: 3 agents, 31 compositions, ~1 h each). -->

You build HyperFrames compositions for <N> vertical shorts (1080x1920, 60 fps) cut from <whose video, its title, and one line
on what it's about, with the names the viewer will see: products, models, the speaker's own apps>. The graphics must match
the reference shorts (`<SKILL>/examples/harness-engineering/`, Leon: "Everything is spot on"): energetic, things move,
constantly showing real examples. Work autonomously; make every judgement call yourself and report it.

## Paths
- Work folder (run every command from here): `<absolute path of work-<stem>>`
  (Git Bash: `<the /c/... form>` - QUOTE IT if it has spaces or parentheses)
- Python: `../.venv/Scripts/python.exe` (`$PY`). Bash is Git Bash on Windows: write longer code with a file tool, not
  heredocs (a `\n` inside a heredoc string becomes a real newline; non-ASCII text gets mangled).
- Skill references (READ FIRST, all of them): `<SKILL>/references/graphics.md` (start with "Theme"),
  `<SKILL>/references/editing-spec.md` sections 4-6, `<SKILL>/references/lessons.md` (HyperFrames, finished-edit and brand
  sections), `<SKILL>/examples/gfx_s1.py`, `<SKILL>/examples/prep_assets.py`, and `scripts/build_gfx_common.py` + `gfx/engine.js` here.
- THE QUALITY BAR, read it: `<SKILL>/examples/harness-engineering/README.md` and its `gfx_a.py` (real sources and footage),
  `gfx_b.py` (concept diagrams at true scale), `gfx_c.py` (one continuous world), plus the pro-edit skill's
  `examples/harness-engineering/` (16:9, same engine and theme). Their helpers (tiles, `chip`, `ring`, `vov`, `view`,
  `stack_blocks`, the keyframe library, `world()`) are yours to copy into your own module.
- `cut.json` (runs, word times) and `shorts.json` (the plan) are READ-ONLY for you.

## The source and what to grab from where
- The short's camera and voice come from `../<video>` (<w>x<h>, <fps> fps, <duration> s). <If it is a finished edit: "It is
  a FINISHED edit: most of its body is covered by the long-form edit's zooms, graphics, keyword pops and CTA cards. Do NOT
  grab UI stills or clips from it.">
- <Finished edit made with davinci-resolve-pro-edit (`import_longform.py` ran): "Clean, unzoomed screen footage: the RAW
  recordings `<folder>\{<files>}`. `$PY scripts/import_longform.py --at <final-video s>` gives the raw file + time (and an
  ffmpeg still command); `--range <a> <b>` lists the raw pieces of a stretch. Key stretches (final-video time -> raw):
  <the article/post ~m:ss, the CLI demo ~m:ss, the app footage ~m:ss>." (The same holds when `build_raw_map.py` rebuilt
  `longform_program.json` from the raw recordings because the work folder was gone.)>
- `$PY scripts/rawsheet.py <name> <final s> [...]` makes a labelled contact sheet of the raw frames at those final-video
  times (`chk/<name>.png`): use it to see what the clean footage shows before choosing a crop. <Paste the sheets you made
  for the brief: chk/raw_s1.png ...>
- The raw recordings show the webcam picture-in-picture at x <..>, y <..>, <w>x<h> (source px): never show it in a graphic.
  Crop UI away from it. LOOK at a frame before choosing a crop: `ffmpeg -ss <t-1> -i <raw> -ss 1 -frames:v 1 x.png`. Keep
  crops even-sized; re-encode clips with dense keyframes (`-g 12`) for HyperFrames.
- <When the video builds something (an app, a game) and its project folder is on this machine: point at it READ-ONLY - its
  real pages, the docs the agent wrote, test or debug captures, review files. It is usually the richest real material.>
- Real pages: `captures/` (`captures/index.json`: file -> url, what it shows; `captures/facts.json`: the fact check). Reuse
  them; don't re-capture. Logos / avatars / thumbnails already cut out: `longform_assets/` <and captures/logos/>. Copy what
  you use into `gfx/assets/` with YOUR tag prefix.
- Fact-check notes that matter here: <each figure the shorts say, with its TRUE value and source>. Draw the TRUE number when
  a number is drawn; the captions say what he says.
- NEVER: <a sponsor of an earlier video, competitors he doesn't name, private details>. No brand or logo the speaker doesn't
  name in THIS video.

## Regions of the source you must never show
- The webcam picture-in-picture: x <..>, y <..> (source px), always. <Stretches where it moves: avoid <t0>-<t1> s.>
- <Baked titles / captions of the long-form edit: text, times, position.>
- <Censored (blurred) regions: never a subject, never filling the frame.>
- <Baked zooms of the long-form edit: times. Prefer stills/clips from UNZOOMED moments (or the raw recordings) and do the
  camera work yourself.>

## Your files (never edit anyone else's)
- `scripts/prep_assets_<tag>.py`: cuts your stills/clips into `gfx/assets/` with file names prefixed `<tag>_`, copies the
  captures / logos you use into `gfx/assets/`, and writes `gfx/asset_dims_<tag>.json` (NOT asset_dims.json; build_gfx_common
  merges them all). Synced footage clips follow the edit map with `synced(sk, ri)` from the example (pieces in cut.json).
- `scripts/gfx_<tag>.py` with a `build()` that writes your compositions with the exact ids given (e.g. `s2_r0`), using
  `build_gfx_common` (`words`, `W`, `page`, `capture_card`, `tile_html`, ...). Build with `$PY scripts/build_gfx.py <tag>`.
- Render only with `bash scripts/render_draft.sh <ids...>` (10 fps draft + `chk/<id>_sheet.png`: LOOK at it) and, after
  fixing, `bash scripts/render_full.sh <ids...>` (throttles itself machine-wide; wait for a `done <id>` line each; `FAILED`
  names a log). Render the drafts of ALL your compositions first, check them, then the full renders.
  Never run prep.sh, finish.sh or compose.py.
- Two large videos in one page (a full-res clip plus its blurred backdrop clone) can run Chrome out of memory: give the
  backdrop its own 640 px wide copy and render with `NODE_OPTIONS=--max-old-space-size=16384`.
- Check one full-resolution frame of anything with text (`ffmpeg -ss <t> -i gfx/out60/<id>.mp4 -frames:v 1 chk/<id>_t.png`)
  and the right-edge columns 1072-1079 against 1064-1071.

## Rules that matter most (the spec has the rest)
- Duration = the run exactly (`r['dur']` from `words(sk, ri)`); cue every move / landing with `W(ws, 'word')` (steps 0.25 s
  before the word). The times below are run-relative word starts from cut.json.
- Frame 0 is the composed landing state: sharp, camera at rest, the hero ALREADY ON SCREEN (the cut lands on it). A card
  that lands at 0.05 s leaves empty frames after the cut. Supporting cards may land later (pop SFX).
- `split`: content in y 40-900 (main element's bottom edge at 880-900), world fades out from y 900 (built in). The caption
  band (941-1114) and the camera card (from 1200, his head pops out above it) are drawn later: keep clear. Footage in a
  split is masked by hand to the same fade (HyperFrames videos sit above the world viewport).
- `fv`: content above y 1230 (bottom edge at 1200-1230); captions go in 1290-1560 below it. Real captures in the fixed
  capture frame (`capture_card`, x 24, y 200, 1032x1040) on the washed backdrop; the frame never moves, the footage pans /
  zooms inside it (1.15-1.4x, 0.4-0.7 s power2.inOut).
- **`*_r0` is also the cover frame**: at frame 0 keep everything below y 620 (the glass title card sits at y ~262-603), then
  step / land so the hero's bottom edge ends at 880-900.
- The channel's design system (graphics.md "Theme"; the default `theme: 'stage'`): graphite stage, glass panels for
  diagrams (`highlight` on the one that matters), white window / paper for real UI and pages, his glossy icon tiles,
  Figtree 600 + Geist Mono labels, azure accent (ember for limits / costs / "busy", mint for passes). Nothing under 30 px,
  including captured UI text the viewer must read. Highlight bands on real pages: class `band` (azure wash) under a
  `mix-blend-mode:multiply` screenshot, revealed with a `scaleX` reveal ON the word (on DARK UI re-ink the real text dark on
  the wash, or an azure outline with a glow); bands and chips over moving footage ride a root-level layer that copies the
  video's transform every frame (`vov()` in the reference gfx_a.py).
- Real sources everywhere something happened: the actual article / docs / post / repo with the cited line highlighted on
  the word, the speaker's own YouTube watch pages for his videos, official logos for named products, his REAL UI doing the
  thing (from the raw recordings). Concept diagrams at TRUE scale when they show quantities (one cell = 1K tokens).
- A concept that spans several runs of one short (a factory, a pipeline, a loop) is ONE continuous world: a pure function
  of the short's own time, each composition rendering its window of it, so the story carries across the cuts
  (`gfx_c.py` `world()`).
- Animate the action, never label it. One dominant subject per scene, at most one supporting cue.
- Camera: glide / step / push (to ~1.6x) / pull, at most ONE whip per composition (whoosh at `t+0.45`). Never blur a word
  to be read.
- SFX on the CFG (run-relative): `pop` landing, `click` real press, `key` typing (one per keystroke burst), `chime` answer /
  success, `whoosh` whip only. Highlight swishes come automatically from `scaleX` reveals.
- Thumbnail moments on the CFG: `thumb=[[a, b]]` (run-relative), where the composition's most eye-catching state is landed
  and still (the logo large, the real UI doing the thing, the key number, the chart that jumped). One or two per composition
  worth a thumbnail, none on the rest. Every short needs at least one strong candidate: a split with his head under a bold
  real element is best.

## Compositions (run id, layout, duration, the words with run-relative start times, and the idea)
<Paste the output of `$PY scripts/brief_runs.py` here and write one "Idea:" line per composition: what it shows, the real
source or footage (with its time), what lands on which word. One "### Short" heading per short, with its title and cover.>

## Assignment
- Agent A (tag `a`): <shorts and composition ids> - <kind, e.g. real sources and footage>
- Agent B (tag `b`): <...> - <e.g. concept diagrams>
- Agent C (tag `c`): <...> - <e.g. the continuous world>

## Report back (short)
Per composition: what it shows, which real sources / frames (times) it uses, camera moves and whips, SFX events
(run-relative), thumbnail windows (and what is on screen in them), judgement calls, and that `render_full.sh` printed `done`
(with the contact sheet you checked).
