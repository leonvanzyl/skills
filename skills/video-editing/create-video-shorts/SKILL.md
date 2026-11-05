---
name: create-video-shorts
description: Turn talking-head recordings into finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) end to end in code - picks and cuts the best lines with J-cuts, rotates eye-contact-aware layouts (full cam, split with a head pop-out matted with Robust Video Matting, full visuals), builds HyperFrames graphics in the channel's design system (graphite stage, glass, Figtree, azure) with real source captures, camera moves and motion blur, burns in captions with glass keyword chips, adds a glass cover and a "Watch the full video" CTA card, real library SFX, a riser and music generated locally for each short (ACE-Step), and delivers 1080x1920 60 fps MP4s with remixable stems, a report, a thumbnail per short and a publishing package for YouTube Shorts, TikTok and Instagram Reels (click-driving titles, platform-tuned captions with hashtags, links back to the full video). Use it whenever the user points at a folder or video and wants shorts, reels, TikToks, vertical clips or a few shorts from a recording, or wants to fix or re-edit a short made this way, even if they just say make shorts from this folder and never mention a skill.
---

# create-video-shorts

You are the editor. From raw or long-form recordings you produce finished vertical shorts whose quality comes from a precise spec. Nothing is done in a video-editor app; everything is code: ffmpeg, Python, Node and HyperFrames.

**The quality contract is `references/editing-spec.md`. Read all of it before planning anything.** Every rule in it was tuned on real output, so follow it exactly. It covers:
- take selection and the cut
- the J-cut and join rules
- eye contact and the three layouts with their exact geometry
- the graphics style (the channel's "Leon YouTube" design system), the camera language and motion blur
- captions with glass keyword chips, the cover and the CTA
- SFX from the library, the riser, the generated music, the report
- the thumbnail and the publishing package for YouTube Shorts, TikTok and Instagram Reels

**The quality bar is `examples/harness-engineering/`** (five shorts Leon called "spot on"): read its README before planning. It shows how the moments were chosen, the plan, the graphics brief, the three graphics agents' code, a report, the publishing copy and contact sheets of the finished shorts. Match that level.

Where the user's request differs from the spec, the user wins. Speed comes from parallelism and incremental edits (`references/speed.md`), never from dropping a rule.

## Inputs and defaults
- **The folder:** a path to a folder of recordings. If none is given, use the current folder. Every video in its root (.mov, .mp4, .mkv, .m4v, .mxf) is a source.
- **One video among others:** if the user points at a single video and its folder holds other videos (e.g. a finished edit next to its raw recordings), pass the file itself to `setup.sh`. It works in `<folder>/shorts/` with a hard link to just that video.
- **Clean audio:** a separate audio file next to a video is paired with it as the clean audio and synced by cross-correlation. With no clean audio, the video's embedded track is the clean audio; never stop because it's missing.
- **A long-form edit made with davinci-resolve-pro-edit (optional piggyback):** the shorts usually run in a fresh session that knows nothing about how the long-form was made, so `setup.sh` looks for it by itself (`import_longform.py --auto`, pipeline.md §1c) and prints a `long-form:` line. When the run is on this machine, it brings over its map from the final video to the RAW recordings (graphics then use clean, unzoomed footage, never the finished render), its captures and fact check, its cut-out logos and its clean voice stem (`voice48.wav`). When there's none, everything works standalone as before: the research subagent captures the sources and the graphics grab from the source video. If the work folder is gone but the raw recordings sit next to the export, `build_raw_map.py` (after `analyze.sh`) rebuilds the map and a clean voice stem from them by audio matching (pipeline.md §1c). The look matches either way: both skills use the same design system.
- **A finished edit with sound under the voice** (hook music, a riser, SFX): patch in a clean voice stem with `clean_from_stem.py` (pipeline.md §1b). The stem is the long-form edit's dialogue track (`import_longform.py` sets it).
- **How many shorts:** follow the user. If they don't say: the most critical, most interesting self-contained moments for TikTok, Instagram and YouTube Shorts - usually 3-5, never more than 5 per video (Leon, 2026-10-14). Pick each as one self-contained idea with a concrete hook (a number, a cost, a question, a striking visual), real things to show, and the speaker's own summary line as the outro (README "Choosing the moments").
- **Cover title:** use the user's. Otherwise write a title from the hook.
- **CTA:** every short ends on the "Watch the full video" card pointing down at the full-video link (Leon's rule; spec section 6), whatever the outro line says.
- **The full video on YouTube** (the TikTok and Instagram copy sends viewers there): the user's URL or title; otherwise the title in the long-form edit's `pro-edit-media/PUBLISH.md`; otherwise the channel name (spec 8b). With a URL or video ID, use the title it went live with (YouTube oEmbed); the file name often differs.
- **Work fully autonomously** once started (spec: "WORK FULLY AUTONOMOUSLY"). Log every judgement call in the report.

## Workflow
Detailed commands are in `references/pipeline.md`. `SKILL` is this skill's folder, and each video gets a work folder `work-<stem>/` where every script runs.

Each stage is one shell call that runs its scripts with the right dependencies and all the parallelism the machine has, so you spend your turns on judgement (the plan, the checks, the graphics), not on babysitting jobs. Run the long ones in the background and keep working.

1. **Setup (about 15 s once cached):** `bash SKILL/scripts/setup.sh <folder>` (or `<video file>`, see Inputs). It creates `.venv`, `edit/` and one `work-<stem>/` per video, containing the scripts, graphics engine, fonts, face model and `project.json`, and picks up a matching long-form run if there is one (read its `long-form:` line). It needs ffmpeg, Node 22+ and uv.
2. **Ingest and analyse, all at once:** `bash scripts/analyze.sh` (in the background) runs the one full decode of the master, then transcription, camera detection, gaze and zoom scans, each the moment its input exists (about 1.7 min for a 15 min 4K master). Meanwhile brief the **research subagent** that fact-checks every figure against 2+ sources and captures the source pages (after `import_longform.py`, only the claims the long-form research doesn't cover). When it returns, look at `detect_camera.png` and fix `project.json` if the window is wrong (then re-run `gaze.py`, under a minute). Heed its WARNING about stretches where the webcam sits elsewhere. With several videos, start one `analyze.sh` per work folder at once. For a finished edit with sound under the voice, run `clean_from_stem.py` now (§1b).
3. **Plan once.** Pick the moments (see Inputs) and the lines, and check eye contact with `eyesheet.py`, then with full-resolution eye crops of every candidate camera line (`eyecrop.py`). Calibrate which pose is on-lens on frames of known moments (a to-camera sign-off, a line read off a slide): it depends on the setup (lessons.md), never assume. With the webcam just above the screen, the pose clusters can't tell reading from on-lens at all; only the crops can. Write `shorts.json`, modelled on `examples/harness-engineering/shorts.json` (five shorts; `examples/plan_example_shorts.json` is a smaller one): the lines, layouts, word-level camera switches, cover, caption highlights and a `music` style that fits the topic (`cinematic` by default - Leon's pick; every short gets its own generated takes). Then write the run plan tiling [0, END].
4. **Cut:** `bash scripts/cut.sh s1` runs `align_lines.py`, `cut2.py`, then `verify_voice.py` (the track must read word-perfect with no join over 150 ms) and `eyesheet.py` in parallel, and prints the runs, the proof and the eye sheet to look at. Iterate; it's fast.
5. **Fan out in parallel:**
   - **Graphics:** fill in `examples/GFX_BRIEF_template.md` as `GFX_BRIEF.md` (paths, where to grab footage, the webcam window, what must never be shown, the fact-check numbers) and paste `$PY scripts/brief_runs.py` under its Compositions heading with one idea per composition. Then start a FEW LONG-LIVED graphics agents (2-4, one per 1-2 shorts, grouped by kind: real sources and footage, concept diagrams, one continuous world), each with a tag (`a`, `b`, …). Never one agent per few compositions (Leon); the reference run used 3 agents for 31 compositions. Each follows `references/graphics.md` and `examples/gfx_s1.py`, owns its `prep_assets_<tag>.py` / `asset_dims_<tag>.json` / `gfx_<tag>.py`, builds its compositions, marks each composition's eye-catching still moments as `thumb` windows (the thumbnail candidates, graphics.md), renders a 10 fps draft with `render_draft.sh` (draft + contact sheet in one call), fixes, then renders at 240 fps with motion blur with `render_full.sh`, which throttles itself machine-wide (3 renders x 8 Chrome browsers at a time) so any number of subagents can call it at once.
   - **Music, in the background:** `$PY scripts/music_takes.py s1 [s2 ...]` (2-4 min, GPU): three generated takes per short in one model load, each cut so its lift lands on the hook join, the best one picked automatically (`<sk>/music/pick.json`).
   - **Main agent, meanwhile:** `bash scripts/prep.sh s1 [s2 ...]`: frame-exact camera clips (all runs in parallel, NVDEC), the Robust Video Matting mattes for every split run of every short in one GPU call (u2net if the model is missing), the captions and CTA events, and a full-resolution frame of every split run whose graphic is already rendered (`chk/<sk>_splits.png`; run `prep.sh` again once the rest are).
6. **Finish:** once every `render_full.sh` for the short has printed `done`, `bash scripts/finish.sh s1 NN slug`: a check that no on-screen text is garbled (`check_text.py`), the music take (waits for `music_takes.py`, or generates now), audio (library SFX, riser, music, stems, mix) and every compose segment in parallel, the frame-count check, the concat, `verify_final.py`, and the copy into `edit/short-NN_<slug>/`. Alongside the concat it renders the thumbnail candidates the graphics marked: clean frames, one seek each, a few seconds. Look at `chk/s1_final.png`, the split frames and `chk/s1_thumbs.png`, then pick the thumbnail with `$PY scripts/thumbnail.py s1 --pick <t> NN slug` (instant: the frame is already rendered).
7. **Deliver:**
   - `edit/short-NN_<slug>/`: `final.mp4`, `thumbnail.jpg`, `stems/` (voice, sfx, riser, music), `music_takes/` (every generated take as an MP3, the one in the short marked) and `report.md` (spec section 8; `scripts/report_data.py <sk>` prints its numbers; write the reports by script like `examples/harness-engineering/make_reports.py`: numbers from the data, judgement per short)
   - `edit/PUBLISH.md`: one section per short (spec 8b), with the thumbnail and copy for each platform:
     - YouTube Shorts: a title under 55 characters with a power word and an open loop, the description with the two community links and three hashtags, and the related video to set.
     - TikTok: a search-friendly caption.
     - Instagram Reels: a caption with 5 hashtags at most.
     - TikTok and Instagram both point to the full video on YouTube.
     - `$PY scripts/check_publish.py` must pass before you hand it over (title length, the exact community lines, hashtags, hook lengths, the CTA line, no URLs in captions).
8. **Edits** are incremental: change the smallest thing and re-run its stage; `finish.sh` re-renders only the segments whose inputs changed (see `references/pipeline.md` §7). A caption, framing or audio fix takes under a minute, not a re-render of everything.

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Word edges:** cut on forced-alignment + RMS edges, never raw Whisper times, and prove the cut by re-transcribing it.
- **Camera clips:** extract them frame-exactly from the master, and make the matte from the same clip, so head and card never drift apart.
- **Webcam split card:** show the whole face; never crop the chin.
- **Captions:** keep word spacing wider than the stroke, and position each caption by the current frame's run.
- **Checking:** check drafts, contact sheets and one full-resolution frame per split before any full render.
- **Finished edits:** they bring baked music and SFX under the voice, burned-in text on full-frame shots, transitions that warp the webcam, a webcam that moves, and censored regions. `lessons.md` covers each one.
- **Frame 0:** the hero is already on screen when a run cuts in. Only supporting cards land later.
- **The brand, not a generic look:** graphics, caption chips, cover and CTA follow Leon's design system (graphite glass, Figtree / Geist Mono, azure). He called the old yellow serif highlight "ugly"; never bring it back.
- **No sponsor that isn't this video's sponsor:** brand names and logos in graphics only when the speaker names them in this video.
- **Text encoding on Windows:** every script reads JSON as UTF-8 and the stage scripts run Python in UTF-8 mode; a cp1252 read once burned "BÃ¶lÃ¼k" into a caption. New code does the same; `check_text.py` guards `finish.sh`.
- **Look at the finished frames,** not just the logs: a full-resolution frame of every split and of every caption chip with a name in it.

## Files
- `scripts/`: the pipeline, all run inside `work-<stem>/`. Per-video values live in `project.json` (`config.py`), never in code. The stage scripts `analyze.sh`, `cut.sh`, `prep.sh`, `finish.sh`, `render_draft.sh` and `render_full.sh` chain the Python scripts with their dependencies and parallelism; every Python script still runs on its own for an incremental edit (`references/pipeline.md`).
- `assets/gfx/`: `engine.js` (the world camera, depth of field, motion blur, captures, the `stage` brand theme with glass / window / paper cards and the horizon wave), GSAP and the HyperFrames project files.
- `assets/fonts/`: Figtree and Geist Mono (the brand; OFL), Poppins and Instrument Serif (the old `paper` theme). `assets/models/`: the face landmarker.
- `assets/sfx/`: the royalty-free SFX library (54 sounds, `manifest.json` with every source and licence). Git holds the CC0 half; on a machine without the Mixkit half, `sfx_library.py build` downloads it (setup.sh does it).
- Audio and matting scripts: `sfxlib.py` (loads the library), `sfx_library.py` (builds / checks it), `music_gen.py` (ACE-Step 1.5 XL, its own env `~/.venvs/music-gen`), `music_takes.py` (takes per short + the automatic pick), `matte_rvm.py` (Robust Video Matting; `matte_gpu.py` is the u2net fallback). Shared once per machine (setup.sh): the RVM model in `~/.cache/pro-edit-models/rvm`, the music env and weights.
- `scripts/import_longform.py`: reuse a davinci-resolve-pro-edit run (the raw-footage map, `--at` / `--range` lookups, captures, logos, voice stem). `scripts/brief_runs.py`: the graphics brief's composition list with run-relative word times. `scripts/check_text.py`: garbled on-screen text stops `finish.sh`. `scripts/check_publish.py`: `PUBLISH.md` against spec 8b.
- `scripts/build_raw_map.py`: when a finished edit's pro-edit work folder is gone, rebuild its final -> raw map and a clean voice stem from the raw recordings by audio matching. `scripts/rawsheet.py`: a contact sheet of raw frames at final-video times (for the graphics brief). `scripts/eyecrop.py`: full-resolution eye crops for the eye-contact check.
- `scripts/clean_from_stem.py`: a clean voice for a finished edit (piecewise sync, suspects, matched patches). `scripts/report_data.py`: a short's report numbers. `scripts/thumbnail.py`: the thumbnail candidates the graphics marked (clean frames and a sheet), and the pick.
- `examples/`:
  - `harness-engineering/`: THE reference (five shorts from a finished long-form edit, October 2026): README (choosing the moments, patterns, thumbnails, timings, what went wrong), `shorts.json`, `GFX_BRIEF.md`, the three graphics agents' `gfx_a/b/c.py` + `prep_assets_*.py`, `make_reports.py`, a report, `make_publish.py` + `PUBLISH.md`, and `look/` (contact sheets and thumbnails of the finished shorts)
  - an older worked short in the retired white "paper" theme (the structure still applies), "Half the price of Opus?": the plan, the graphics config, the asset prep, the report and `PUBLISH.md`
  - `GFX_BRIEF_template.md`: the shared brief for the graphics agents
- `references/`:
  - `editing-spec.md`: the contract
  - `pipeline.md`: the commands
  - `graphics.md`: the engine API
  - `speed.md`: parallelism
  - `design-system/`: the channel's design system ("Leon YouTube": readme, tokens, components, guidelines), bundled so the skill is self-contained; the brand theme in the code implements it. Read its `readme.md` and tokens before designing anything new
  - `lessons.md`
