---
name: create-video-shorts
description: Turn talking-head recordings into finished, ready-to-post 9:16 shorts (YouTube Shorts, Instagram Reels, TikTok) end to end in code - picks and cuts the best lines with J-cuts, rotates eye-contact-aware layouts (full cam, split with a head pop-out, full visuals), builds luxury-tech HyperFrames graphics with real source captures, camera moves and motion blur, burns in captions, adds a cover and a CTA comment box, synthesizes SFX, riser and theme-matched music, and delivers 1080x1920 60 fps MP4s with remixable stems, a report and SEO titles and descriptions with community links. Use it whenever the user points at a folder or video and wants shorts, reels, TikToks, vertical clips or a few shorts from a recording, or wants to fix or re-edit a short made this way, even if they just say make shorts from this folder and never mention a skill.
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
- the publishing copy with the community links

Where the user's request differs from the spec, the user wins. Speed comes from parallelism and incremental edits (`references/speed.md`), never from dropping a rule.

## Inputs and defaults
- **The folder:** a path to a folder of recordings. If none is given, use the current folder. Every video in its root (.mov, .mp4, .mkv, .m4v, .mxf) is a source.
- **Clean audio:** a separate audio file next to a video is paired with it as the clean audio and synced by cross-correlation. With no clean audio, the video's embedded track is the clean audio; never stop because it's missing.
- **How many shorts:** follow the user. If they don't say, make one short per source video, from its strongest self-contained segment.
- **Cover title and CTA keyword:** use the user's. Otherwise write a title from the hook, and take the keyword from the speaker's CTA line.
- **Work fully autonomously** once started (spec: "WORK FULLY AUTONOMOUSLY"). Log every judgement call in the report.

## Workflow
Detailed commands are in `references/pipeline.md`. `SKILL` is this skill's folder, and each video gets a work folder `work-<stem>/` where every script runs.

1. **Setup (about 15 s once cached):** `bash SKILL/scripts/setup.sh <folder>`. It creates `.venv`, `edit/` and one `work-<stem>/` per video, containing the scripts, graphics engine, fonts, face model and `project.json`. It needs ffmpeg, Node 22+ and uv.
2. **Ingest and analyse, all at once.** `scripts/ingest.py` is the only full decode of the master. It writes the audio, the RMS map, a 10 fps proxy and thumbnails, and handles clean-audio sync. As soon as each input exists, run these in the background:
   - `transcribe.py` (GPU Whisper)
   - `detect_camera.py`, then look at `detect_camera.png`
   - `gaze.py` and `zoomscan.py`
   - a **research subagent** that fact-checks every figure against 2+ sources and captures the source pages
   With several videos, run their ingests concurrently too.
3. **Plan once.** Pick the lines and check eye contact with `eyesheet.py`. Write `shorts.json`, following `examples/plan_example_shorts.json`: the lines, layouts, word-level camera switches, cover, CTA keyword, caption highlights and a `music` style and mood that fit the topic (lofi by default; never the same track twice). Then write the run plan tiling [0, END].
4. **Cut:** `align_lines.py`, then `cut2.py`, then `verify_voice.py` (the track must read word-perfect with no join over 150 ms) and `eyesheet.py <sk>`. Iterate; it's fast.
5. **Fan out in parallel:**
   - **Graphics:** one subagent per composition, following `references/graphics.md` and `examples/gfx_s1.py`. Each builds its composition, renders a 10 fps draft, checks a contact sheet, fixes, then renders at 240 fps with motion blur.
   - **Main agent, meanwhile:**
     - `cam_prep.py` (frame-exact camera clips)
     - the matte for split runs, all shorts in one GPU call (`scripts/matte_gpu.py s1:0,3 s2:0 --jobs 4`)
     - `compose.py --preview 0` (captions, cover and CTA events)
     - `audio.py` (SFX, riser, music, stems, mix)
6. **Composite:** render one `compose.py --runs i --seg-out …` process per run, in parallel, then `--concat`. Verify with `verify_final.py` and look at the contact sheet and a full-resolution frame of every split.
7. **Deliver:**
   - `edit/short-NN_<slug>/`: `final.mp4`, `stems/` (voice, sfx, riser, music) and `report.md` (spec section 8)
   - `edit/PUBLISH.md`: one section per short, with the SEO title, a one-to-two-line description and the two community links exactly as written in spec section 8b
8. **Edits** are incremental: re-run only the stage a change touches (see `references/pipeline.md` §7). A caption, framing or audio fix takes minutes, not a re-render of everything.

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Word edges:** cut on forced-alignment + RMS edges, never raw Whisper times, and prove the cut by re-transcribing it.
- **Camera clips:** extract them frame-exactly from the master, and make the matte from the same clip, so head and card never drift apart.
- **Webcam split card:** show the whole face; never crop the chin.
- **Captions:** keep word spacing wider than the stroke, and position each caption by the current frame's run.
- **Checking:** check drafts, contact sheets and one full-resolution frame per split before any full render.

## Files
- `scripts/`: the pipeline, all run inside `work-<stem>/`. Per-video values live in `project.json` (`config.py`), never in code.
- `assets/gfx/`: `engine.js` (the world camera, depth of field, motion blur, captures), GSAP and the HyperFrames project files.
- `assets/fonts/`: Poppins and Instrument Serif. `assets/models/`: the face landmarker.
- `examples/`: a complete worked short, "Half the price of Opus?":
  - the plan
  - the graphics config
  - the asset prep
  - the report
  - `PUBLISH.md`
- `references/`:
  - `editing-spec.md`: the contract
  - `pipeline.md`: the commands
  - `graphics.md`: the engine API
  - `speed.md`: parallelism
  - `lessons.md`
