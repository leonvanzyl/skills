# Graphics brief (shared by every graphics subagent) — TEMPLATE
<!-- Copy to work-<stem>/GFX_BRIEF.md, fill every <...>, delete what doesn't apply. Then give each graphics subagent a short
     prompt: "read GFX_BRIEF.md and every reference it lists; your tag is <tag>; your compositions are <ids> (words, durations
     and what each shows)". One tag per subagent (s1a, s1b, s2a ...), 2-5 compositions each, up to ~6 subagents at once. -->

You build HyperFrames compositions for vertical shorts (1080x1920, 60 fps) cut from <one line: what the video is about, names
the viewer will see (products, the speaker's agent/app names)>. Work autonomously; make every judgement call yourself and report it.

## Paths
- Work folder (run every command from here): `<absolute path of work-<stem>>`
- Python: `../.venv/Scripts/python.exe` (call it `$PY`). Bash is Git Bash on Windows: write longer code with a file tool, not heredocs.
- The source video: `../<video>` (<w>x<h>, <fps> fps, <duration> s). <If it is a finished edit: "It is the speaker's FINISHED edit, so
  some stretches already contain baked-in zooms, highlight bands and on-screen titles from that edit.">
- Skill references (READ FIRST, all of them): `<SKILL>/references/graphics.md`, `<SKILL>/references/editing-spec.md` sections 4-5,
  `<SKILL>/references/lessons.md` (HyperFrames + finished-edit sections), `<SKILL>/examples/gfx_s1.py`, `<SKILL>/examples/prep_assets.py`,
  and `scripts/build_gfx_common.py` + `gfx/engine.js` here.
- `cut.json` (runs, word times) and `shorts.json` (the plan) are READ-ONLY for you.
- Source-page captures and logos: `captures/` (`captures/index.json` says what each shows; `captures/facts.json` is the fact check).

## Regions of the source you must never show
- The webcam picture-in-picture: x <..>, y <..> (source px), always. <Stretches where it moves: avoid <t0>-<t1> s.>
- <Baked titles / captions of the long-form edit: text, times, position.>
- <Censored (blurred) regions: never a subject, never filling the frame.>
- <Baked zooms of the long-form edit: times. Prefer stills/clips from UNZOOMED moments and do the camera work yourself.>
Grab exact stills with output seeking: `ffmpeg -ss <t-1> -i ../<video> -ss 1 -frames:v 1 ...`. LOOK at a frame before choosing a
crop. Keep crops even-sized.

## Your files (never edit anyone else's)
- `scripts/prep_assets_<tag>.py`: cuts your stills/clips into `gfx/assets/` with file names prefixed `<tag>_`, copies the captures /
  logos you use into `gfx/assets/`, and writes `gfx/asset_dims_<tag>.json` (NOT asset_dims.json; build_gfx_common merges them all).
  Synced footage clips follow the edit map with `synced(sk, ri)` from the example (pieces in cut.json).
- `scripts/gfx_<tag>.py` with a `build()` that writes your compositions with the exact ids given (e.g. `s2_r0`), using
  `build_gfx_common` (`words`, `W`, `page`, `capture_card`, ...). Build with `$PY scripts/build_gfx.py <tag>`.
- Render only with `bash scripts/render_draft.sh <ids...>` (10 fps draft + `chk/<id>_sheet.png`: LOOK at it) and, after fixing,
  `bash scripts/render_full.sh <ids...>` (throttles itself machine-wide; wait for a `done <id>` line each; `FAILED` names a log).
  Never run prep.sh, finish.sh or compose.py.
- Check one full-resolution frame of anything with text (`ffmpeg -ss <t> -i gfx/out60/<id>.mp4 -frames:v 1 chk/<id>_t.png`) and the
  right-edge columns 1072-1079 against 1064-1071.

## Rules that matter most (the spec has the rest)
- Duration = the run exactly (`r['dur']` from `words(sk, ri)`); cue every move with `W(ws, 'word')` (steps 0.25 s before the word).
- Frame 0 is the composed landing state: sharp, camera at rest, the hero ALREADY ON SCREEN (the cut lands on it). A card that
  lands at 0.05 s leaves empty frames after the cut. Supporting cards may land later (pop SFX).
- `split`: content in y 40-900 (main element's bottom edge at 880-900), world fades out from y 900 (built in). The caption band
  (941-1114) and the camera card (from 1200) are drawn later: keep clear.
- `fv`: content above y 1230 (bottom edge at 1200-1230). Real captures in the fixed capture frame (`capture_card`, x 24, y 200,
  1032x1040) on the washed backdrop; the frame never moves, the footage pans/zooms inside it (1.15-1.4x, 0.4-0.7 s power2.inOut).
- **`*_r0` is also the cover frame**: at frame 0 keep everything below y 620 (the title box sits at y 262-603), then step/land so the
  hero's bottom edge ends at 880-900.
- Luxury-tech white world, Poppins, ink #111, Clay #D97757 / #B25730, band #FBEEE8 under a `mix-blend-mode:multiply` screenshot
  (on DARK UI a multiply band vanishes: re-ink the real text dark on #FBEEE8 in an overlay, or a clay outline screen-blended),
  green #34C759, red #FF3B30. Nothing under 30 px, including captured UI text the viewer must read.
- Animate the action, never label it. A product is its REAL UI from the source doing the thing. One dominant subject.
- Camera: glide / step / push (to ~1.6x) / pull, at most ONE whip per composition (whoosh at `t+0.45`). Never blur a word to be read.
- SFX on the CFG (run-relative): `pop` landing, `click` real press, `key` typing start, `chime` answer/message arriving, `whoosh` whip only.

## Report back (short)
Per composition: what it shows, which real sources / frames (times) it uses, camera moves and whips, SFX events (run-relative),
judgement calls, and that `render_full.sh` printed `done` (with the contact sheet you checked).
