---
name: create-video-shorts
description: Turn talking-head recordings into finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) end to end in code - picks and cuts the best lines with J-cuts, rotates eye-contact-aware layouts (full cam, split with a head pop-out, full visuals), builds luxury-tech HyperFrames graphics with real source captures, camera moves and motion blur, burns in captions, adds a cover and a CTA comment box, synthesizes SFX, riser and theme-matched music, and delivers 1080x1920 60 fps MP4s with remixable stems, a report, a thumbnail per short and a publishing package for YouTube Shorts, TikTok and Instagram Reels (click-driving titles, platform-tuned captions with hashtags, links back to the full video). Use it whenever the user points at a folder or video and wants shorts, reels, TikToks, vertical clips or a few shorts from a recording, or wants to fix or re-edit a short made this way, even if they just say make shorts from this folder and never mention a skill.
---

# create-video-shorts

You are the editor. From raw or long-form recordings you produce finished vertical shorts whose quality comes from a precise spec. Nothing is done in a video-editor app; everything is code: ffmpeg, Python, Node and HyperFrames.

**The quality contract is `references/editing-spec.md`. Read all of it before planning anything.** Every rule in it was tuned on real output, so follow it exactly. It covers:
- take selection and the cut
- the J-cut and join rules
- eye contact and the three layouts with their exact geometry
- the graphics style, the camera language and motion blur
- captions, the cover and the CTA
- SFX levels, the riser, the music, the report
- the thumbnail and the publishing package for YouTube Shorts, TikTok and Instagram Reels

Where the user's request differs from the spec, the user wins. Speed comes from parallelism and incremental edits (`references/speed.md`), never from dropping a rule.

## Inputs and defaults
- **The folder:** a path to a folder of recordings. If none is given, use the current folder. Every video in its root (.mov, .mp4, .mkv, .m4v, .mxf) is a source.
- **One video among others:** if the user points at a single video and its folder holds other videos (e.g. a finished edit next to its raw recordings), pass the file itself to `setup.sh`. It works in `<folder>/shorts/` with a hard link to just that video.
- **Clean audio:** a separate audio file next to a video is paired with it as the clean audio and synced by cross-correlation. With no clean audio, the video's embedded track is the clean audio; never stop because it's missing.
- **A finished edit with sound under the voice** (hook music, a riser, SFX): look for a clean voice stem, e.g. the long-form edit's dialogue track. A previous davinci-resolve-pro-edit run keeps `voice48.wav`, a report of what it added, and a reusable fact check. Patch the stem in with `clean_from_stem.py` (pipeline.md §1b).
- **How many shorts:** follow the user. If they don't say, make one short per source video, from its strongest self-contained segment.
- **Cover title and CTA keyword:** use the user's. Otherwise write a title from the hook, and take the keyword from the speaker's CTA line.
- **The full video on YouTube** (the TikTok and Instagram copy sends viewers there): the user's URL or title; otherwise the title in the long-form edit's `pro-edit-media/PUBLISH.md`; otherwise the channel name (spec 8b).
- **Work fully autonomously** once started (spec: "WORK FULLY AUTONOMOUSLY"). Log every judgement call in the report.

## Workflow
Detailed commands are in `references/pipeline.md`. `SKILL` is this skill's folder, and each video gets a work folder `work-<stem>/` where every script runs.

Each stage is one shell call that runs its scripts with the right dependencies and all the parallelism the machine has, so you spend your turns on judgement (the plan, the checks, the graphics), not on babysitting jobs. Run the long ones in the background and keep working.

1. **Setup (about 15 s once cached):** `bash SKILL/scripts/setup.sh <folder>` (or `<video file>`, see Inputs). It creates `.venv`, `edit/` and one `work-<stem>/` per video, containing the scripts, graphics engine, fonts, face model and `project.json`. It needs ffmpeg, Node 22+ and uv.
2. **Ingest and analyse, all at once:** `bash scripts/analyze.sh` (in the background) runs the one full decode of the master, then transcription, camera detection, gaze and zoom scans, each the moment its input exists (about 1.7 min for a 15 min 4K master). Meanwhile brief the **research subagent** that fact-checks every figure against 2+ sources and captures the source pages. When it returns, look at `detect_camera.png` and fix `project.json` if the window is wrong (then re-run `gaze.py`, under a minute). Heed its WARNING about stretches where the webcam sits elsewhere. With several videos, start one `analyze.sh` per work folder at once. For a finished edit with sound under the voice, run `clean_from_stem.py` now (§1b).
3. **Plan once.** Pick the lines and check eye contact with `eyesheet.py`. Calibrate on-lens on the outro: with the webcam beside the screen, the lens is the TURNED pose. Write `shorts.json`, following `examples/plan_example_shorts.json`: the lines, layouts, word-level camera switches, cover, CTA keyword, caption highlights and a `music` style and mood that fit the topic (lofi by default; never the same track twice). Then write the run plan tiling [0, END].
4. **Cut:** `bash scripts/cut.sh s1` runs `align_lines.py`, `cut2.py`, then `verify_voice.py` (the track must read word-perfect with no join over 150 ms) and `eyesheet.py` in parallel, and prints the runs, the proof and the eye sheet to look at. Iterate; it's fast.
5. **Fan out in parallel:**
   - **Graphics:** fill in `examples/GFX_BRIEF_template.md` as `GFX_BRIEF.md` (paths, webcam window, what must never be shown), then give each subagent a tag (`s1a`, `s1b`, …) and 2–5 compositions. Each follows `references/graphics.md` and `examples/gfx_s1.py`, owns its `prep_assets_<tag>.py` / `asset_dims_<tag>.json` / `gfx_<tag>.py`, builds its compositions, marks each composition's eye-catching still moments as `thumb` windows (the thumbnail candidates, graphics.md), renders a 10 fps draft with `render_draft.sh` (draft + contact sheet in one call), fixes, then renders at 240 fps with motion blur with `render_full.sh`, which throttles itself machine-wide (3 renders x 8 Chrome browsers at a time) so any number of subagents can call it at once.
   - **Main agent, meanwhile:** `bash scripts/prep.sh s1 [s2 ...]`: frame-exact camera clips (all runs in parallel, NVDEC), the mattes for every split run of every short in one GPU call, the captions and CTA events, and a full-resolution frame of every split run whose graphic is already rendered (`chk/<sk>_splits.png`; run `prep.sh` again once the rest are).
6. **Finish:** once every `render_full.sh` for the short has printed `done`, `bash scripts/finish.sh s1 NN slug`: audio (SFX, riser, music, stems, mix) and every compose segment in parallel, the frame-count check, the concat, `verify_final.py`, and the copy into `edit/short-NN_<slug>/`. Alongside the concat it renders the thumbnail candidates the graphics marked: clean frames, one seek each, a few seconds. Look at `chk/s1_final.png`, the split frames and `chk/s1_thumbs.png`, then pick the thumbnail with `$PY scripts/thumbnail.py s1 --pick <t> NN slug` (instant: the frame is already rendered).
7. **Deliver:**
   - `edit/short-NN_<slug>/`: `final.mp4`, `thumbnail.jpg`, `stems/` (voice, sfx, riser, music) and `report.md` (spec section 8; `scripts/report_data.py <sk>` prints its numbers)
   - `edit/PUBLISH.md`: one section per short (spec 8b), with the thumbnail and copy for each platform:
     - YouTube Shorts: a title under 55 characters with a power word and an open loop, the description with the two community links and three hashtags, and the related video to set.
     - TikTok: a search-friendly caption.
     - Instagram Reels: a caption with 5 hashtags at most.
     - TikTok and Instagram both point to the full video on YouTube.
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

## Files
- `scripts/`: the pipeline, all run inside `work-<stem>/`. Per-video values live in `project.json` (`config.py`), never in code. The stage scripts `analyze.sh`, `cut.sh`, `prep.sh`, `finish.sh`, `render_draft.sh` and `render_full.sh` chain the Python scripts with their dependencies and parallelism; every Python script still runs on its own for an incremental edit (`references/pipeline.md`).
- `assets/gfx/`: `engine.js` (the world camera, depth of field, motion blur, captures), GSAP and the HyperFrames project files.
- `assets/fonts/`: Poppins and Instrument Serif. `assets/models/`: the face landmarker.
- `scripts/clean_from_stem.py`: a clean voice for a finished edit (piecewise sync, suspects, matched patches). `scripts/report_data.py`: a short's report numbers. `scripts/thumbnail.py`: the thumbnail candidates the graphics marked (clean frames and a sheet), and the pick.
- `examples/`:
  - a complete worked short, "Half the price of Opus?": the plan, the graphics config, the asset prep, the report and `PUBLISH.md`
  - `GFX_BRIEF_template.md`: the shared brief for parallel graphics subagents
- `references/`:
  - `editing-spec.md`: the contract
  - `pipeline.md`: the commands
  - `graphics.md`: the engine API
  - `speed.md`: parallelism
  - `lessons.md`
