---
name: davinci-resolve-pro-edit
description: Professionally edit a long-form YouTube recording (talking head, screencast, tutorial) in DaVinci Resolve end to end, with the create-video-shorts editing intelligence carried over to long form and assembled through the davinci-resolve MCP. Reuses or makes a clean foundation cut; gives the first 30-45 s a short-form hook (screen zooms with highlights, punch-ins, luxury-tech graphics with real source captures and motion blur, a split with a head pop-out, keyword pops, music that fades out after the hook, a riser); keeps the body moving with B-roll wherever the talk explains or cites something (zooms with highlights, real articles and pages with the cited line marked, explainer graphics, logos, the speaker's own videos, community CTA cards, library SFX; no music); for separate webcam + desktop recordings, a moving, morphing webcam (full frame, side card, corner window, hidden) on eased transitions, placed by research-backed rules; builds a new Pro Edit timeline with every addition on its own track, plus chapters, an SRT and publishing copy, and delivers the finished upload-ready 4K file mastered for YouTube (-14 LUFS, true peak under -1 dBTP, mixed against the user's own voice chain and verified on the decoded file). Use it whenever the user wants a long-form video or Resolve timeline professionally edited, polished or finished, or given zooms, graphics, B-roll, highlights, sound design or a hook, even without naming a skill. Not for shorts or a clean cut alone.
---

# DaVinci Resolve Pro Edit

You are the editor of a long-form YouTube video. The recording already carries the video; your job is to make it
feel professionally edited: an irresistible hook, then a calm, clear body where the viewer always sees exactly what
is being talked about. Everything is decided from the transcript and the frames, rendered in code (ffmpeg, Python,
HyperFrames), and assembled in Resolve through the davinci-resolve MCP on a new timeline, one named track per kind
of addition, so the user can adjust or remove anything.

**The quality contract is `references/editing-spec.md`. Read all of it before planning.** It carries the shorts
spec over to long form: the same graphics style, camera language, fact checking and sound design, with the hook /
body split. The rules the user cares most about:
- **Music plays under the hook only** and fades out over 2-3 s right after it. Never under the body.
- **The body keeps showing**: a zoom with highlights, the real article or page, an explainer graphic, a logo or the speaker's own video about every 10-20 s (~80% of the runtime covered on theory), CTA cards and SFX on every visual event - energy from showing, not decoration (no music or keyword pops after the hook).
- **Nothing on the clean cut changes.** The pro edit is a duplicate of it with new tracks on top.
- **The deliverable is one file the user uploads as it is:** `$M/final/<timeline> - FINAL (-14 LUFS).mp4`, the 4K
  picture with a master made outside Resolve's mixer from the user's own voice chain plus the pro edit's layers,
  measured on the decoded file (-14 LUFS, under -1 dBTP, in sync). Never leave loudness to "normalise in Deliver".
- **Every 4K export from Resolve uses its built-in "YouTube - 2160p" render preset** (the user's rule: 3840x2160 at
  the timeline frame rate, MP4, H.264 High, ~11 Mb/s at 4K60 - about 2 GB for 25 minutes). Load it by name
  (`project.LoadRenderPreset('YouTube - 2160p')`) and change only the range, folder and file name - never the codec
  or quality: a 97 Mb/s export (18 GB) took "an incredibly long time to upload".
- **The user's voice chain is part of their timeline.** Their EQ, voice isolation and dynamics live on the base
  timeline's tracks; a rebuilt timeline drops them, and the API can't see or copy them. Check it before any levelling.
- **Separate webcam + desktop recordings get the dynamic camera** (`references/dynamic-camera.md`): the webcam morphs
  between full frame, a side card, a corner window and hidden, on eased moves that start at cuts and sentence breaks,
  top-right by default, the corner following the content. The user approved it as the standard for separate
  recordings (abacus-test, 2026-11-01): "exactly the quality of editing that I expect going forward".
Where the user's request differs from the spec, the user wins.

First real project (Sonnet 5.5 vs Opus 5.5 vs Fable 5.1, 2026-09-30): an 11-minute clean cut, 4K60, OBS
recordings that switch between a full-frame camera and a screen with a webcam PiP. The test build in
`examples/` is what the scripts were proven on - including every fix in `references/lessons.md`.

## Requirements

| What | Notes |
|---|---|
| DaVinci Resolve Studio + the `davinci-resolve` MCP server | Community server [samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp). Load its tools with ToolSearch query `davinci resolve` (it may still be connecting at session start). Studio is needed for external scripting; see `references/resolve-assembly.md`. |
| CrisperWhisper env (transcription) | The same env as davinci-resolve-video-edit: `~/.venvs/crisperwhisper` or `VEDIT_VENV`, model `nyralabs/CrisperWhisper2.0_large` in the Hugging Face cache. Never modified by this skill. |
| Render env | `~/.venvs/pro-edit` or `PRO_EDIT_VENV` (Python 3.11: numpy, scipy, soundfile, pyloudnorm, opencv, pillow, mediapipe, onnxruntime-gpu for the split matte). `setup.sh` creates it with uv and adds what an older env lacks. |
| ffmpeg, Node 22+, uv | ffmpeg with NVENC is used when present. HyperFrames runs through `npx --yes hyperframes`. |
| NVIDIA GPU | Recommended (transcription, NVENC, the split matte). Everything has a CPU fallback. |

Missing pieces: `references/setup-and-troubleshooting.md` (ask before the ~7 GB CrisperWhisper install).

## Conventions
Shell variables don't persist between Bash calls, so start each command with:
```bash
SKILL="<this skill's folder>"
VENV="${VEDIT_VENV:-$HOME/.venvs/crisperwhisper}"; CW="$VENV/Scripts/python.exe"; [ -e "$CW" ] || CW="$VENV/bin/python"
RV="${PRO_EDIT_VENV:-$HOME/.venvs/pro-edit}"; PY="$RV/Scripts/python.exe"; [ -e "$PY" ] || PY="$RV/bin/python"
W="${PRO_EDIT_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/video-pro-edit}/<project>__<timeline>"   # short, no spaces
M="<folder of the source media>/pro-edit-media"     # renders Resolve links to: next to the sources, never under AppData
```
Every script runs with `W` as the working directory (`cd "$W"`). `W` holds caches and intermediates; `M` holds the
finished media, `captions.srt`, `PUBLISH.md`, `report.md`, `final/` (the file to upload) and `_deliver/` (what Resolve
renders for the master; deletable after delivery).

## Workflow
Commands for every step are in `references/pipeline.md`.

1. **Connect and choose the timeline** (read-only). `project_manager get_current`, `timeline get_current`,
   `timeline list`. Default target = the current timeline. If a "<name> - Clean Cut vN" exists for it, that is the
   base; if the current timeline is raw, make the foundation cut first (`references/foundation-cut.md`).
   If the media bin holds separate DESKTOP and WEBCAM files instead of one composited recording, read
   `references/separate-sources.md` and `references/dynamic-camera.md` first. If `resolve_control get_version` reports an MCP update, mention it once.
2. **Set up and map the programme** (~5-10 min, mostly background). `setup.sh "$W" "$M"`, then on the clean cut:
   `probe_timeline_structure` -> `vedit.py prepare` + `transcribe` (CrisperWhisper, hotwords as in the foundation
   cut) -> `program.py` (every V1 item and word on programme time, the voice as it plays) -> `scenes.py` (camera vs
   screen, the PiP window per file) -> `pip_items.py` (the PiP corner per V1 item: OBS scenes can move the webcam
   inside one file). LOOK at `scenes.png`. Read `transcript.txt` like a paper edit. `patch_flash.py scan` lists
   items that end or start on a flash of another window - cover each with a `fix` beat (`patch_flash.py <id> ...`).
3. **Research, in parallel** (one long-lived subagent): fact-check every figure against 2+ sources; capture the pages the speaker
   cites but the recording doesn't show, official logos, pricing and docs as 2x PNGs into `W/captures/`.
4. **Plan once** into `W/edit_plan.json` (`examples/edit_plan_example.json`): hook_end, music style and mood,
   the beats (zoom, punch, gfx, words, cta) with word-cued times, chapters, caption fixes, the publishing copy.
   Anything private on screen (a message with fees or contact details, an account number) gets a `censor` beat.
   Use `look.py` to see the programme at any time with a source-pixel grid, and `--zoom k,fx,fy` to frame a zoom
   clear of the webcam. Check the plan against the spec's density rules before rendering anything.
5. **Render, fanning out:**
   - censor beats first: `censor.py track` (zooms inside the beat bake the blur in from it), `scan` the whole
     programme for the same words, check `preview` frames, then `render`;
   - zooms, keyword pops, CTA cards and the audio: preview a few zoom frames first (`zoom.py --preview`, seconds),
     then `bash scripts/render_beats.sh` in the background renders every zoom / words / cta beat of the plan in
     parallel (one process per beat) and runs `audio.py` after them - then listen to the hook in `mix_preview.wav`;
   - graphics: one or two LONG-LIVED subagents (the user's preference - many small agents burn tokens), each owning
     half of the gfx beats with a written brief (beats, cue words with times, assets, PiP rules), following
     `references/graphics.md`, `examples/gfx_example.py` and the reference edit in `examples/harness-engineering/`
     (its README indexes the explainers to copy: the software-factory swarm, concept diagrams built word by word,
     real sources with the cited line highlighted):
     assets -> `build_gfx.py` -> `render_gfx.sh draft` -> `draftsheet.py` (LOOK, fix) -> `render_gfx.sh full`
     (lossless PNG capture, one Chrome per worker, throttled machine-wide so any number of subagents can call it)
     -> `compose.py` (split beats: `--matte` first - Robust Video Matting on the GPU, u2net as the fallback; several
     beats with `--jobs`).
   Check every render: previews and sheets before full renders, one full-resolution frame of every split
   (`compose.py <id> --preview t` seeks straight to it).
6. **Assemble in Resolve** (`references/resolve-assembly.md`): duplicate the clean cut as
   "<base> - Pro Edit vN", count its tracks, `place.py plan`, add and name the PE tracks, import `M` into a bin,
   `place.py ids`, one `append_to_timeline`, punch-ins with `bulk_set_item_properties`, markers, save. Then
   `place.py verify` against a fresh structure probe, and check frames from a 1080p review render (pipeline.md
   section 7; `timeline_frame capture` once hung for 30 minutes). If the pro edit could NOT be a straight duplicate
   (a restructured cut rebuilt from source ranges), run the voice-chain check now (pipeline.md 9a): when the user's
   timeline is PROCESSED and the new one RAW, stop and ask them to copy their voice effects onto its A1 first.
7. **Master and deliver** (pipeline.md section 9, ~15-20 min, mostly Resolve rendering): the voice-chain check;
   in Resolve `rs_items.py`, `rs_stem.py` (the user's own tracks through their chain, then the mix as Resolve plays
   it) and `rs_picture.py` (the 4K picture); `master.py layers` (the PE tracks from their files), `fit` (what
   Resolve's mix really does - flags faders, automation and bus effects the master leaves out), `build` (premix at
   the designed balance -> true-peak limiter -> -14.0 LUFS; every SFX audited against its target) and `deliver`
   (sync check, mux with the picture copied, measure the decoded file, dip any AAC overshoot, re-measure). The
   result is `$M/final/<timeline> - FINAL (-14 LUFS).mp4` - the file the user uploads.
   **Separate recordings: the dynamic camera is the final picture** (pipeline.md section 11, ~40 min, mostly a
   background render): `rs_content.py` (the content layer + the track map) -> `dyncam.py cfg` -> `dyncam_plan.py busy`,
   `targets`, `draft` -> edit the plan with judgment (CARD moments, FULL reactions) -> `check` -> look at `--strip`s
   of the moves -> `dyncam.py --jobs 8` -> `dyncam_qc.py flash` -> `rs_layout.py` ("<Pro Edit> - Dynamic Camera") ->
   `rs_picture.py` -> `master.py deliver` -> `dyncam_qc.py flash` + `sync` on the final. Deliver that file.
8. **Publish and report:** `publish.py` (`captions.srt`, `PUBLISH.md` with chapters and the community links),
   then `report.md` (spec section 9) with the final file's numbers. Tell the user: the final file's path and its
   measured loudness, true peak and resolution; the timeline name, what was added and where; anything `fit`
   flagged; the archived duplicates the MCP made and `$M/_deliver` (safe to delete - never delete them yourself).
9. **Edits are incremental:** change the plan, re-render only the touched beats, re-import those files and replace
   their clips (`references/pipeline.md` section 8); many swaps at once go through one `script_plugin run_inline`.
   A rebuilt audio layer goes on new tracks with `place_audio_swap.py`. After any change, run section 9 again so
   the final file matches the timeline. Fold the user's taste into `references/lessons.md`.
10. **Clean up, only on the user's go-ahead** (pipeline.md section 10): a finished edit leaves tens of GB behind
   (last-call ~63 GB). After delivering, ask the user to tell you when the video is uploaded and it is safe to clean
   up - with the dry run's total (`cleanup.py "$M"`), and saying that the final file goes too and the Pro Edit
   timeline's added clips will show as offline. On their yes, `cleanup.py "$M" --delete` removes every work dir of
   the project and everything in `M` but `report.md`, `PUBLISH.md` and `captions.srt`. Never before they say so.

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Separate webcam + desktop files** (no composited OBS recording): follow `references/separate-sources.md`. Render
  every facecam bubble with `scripts/facecam.py` - a looped PNG layer without `-framerate` made the webcam play 2.4x
  fast and out of sync (abacus-test); the script checks speed and sync on every clip before it says ok.
- **The dynamic camera's traps** (`references/dynamic-camera.md`, "Bugs"): a rounded mask that goes transparent below
  half a pixel of radius (the v2 "flicker"), crop and window interpolated apart (a squashed face), moves that straddle
  a webcam jump cut, blur samples reaching back before a key, key times written to 4 decimals (off the frame grid).
  All fixed in `dyncam.py`; `dyncam_qc.py` proves it on the layer and the final file. And when you check sync on a
  Resolve render, decode from frame 0: ffmpeg's input seek lands one frame early in Resolve's MP4s.
- **The webcam corner is a decision, not a habit:** top-right by default for screen demos (YouTube's controls,
  captions and watermark crowd the bottom; AI tools keep the prompt at the bottom), another corner only where the
  content needs it. Earlier edits defaulted to bottom-right without a reason, and the user asked why.
- **Colour at the cut:** zoom renders work on the source's own YUV planes, so a frame at rest is bit-identical to
  V1. Never route footage through ffmpeg's default RGB conversion (bt601) - the cut into V2 would shift colour.
- **Windows pipes:** raw 4K video through a Python-buffered pipe crawls; `media.py`'s unbuffered 64 MB pipes move
  it at GB/s. Never add `bufsize=` to a frame pipe (the shorts skill lost 48 ms a frame to a 100 MB buffer).
- **The user's timeline is not pristine:** duplicate it, never rebuild it; skip titles/transitions in the
  programme map; never plan a beat across a transition. A rebuild (only when a restructure forces it) drops their
  voice chain, track faders and clip volumes - say so up front and run the voice-chain check (pipeline.md 9a).
- **Resolve's mixer is not the master:** fader automation (green faders that snap back), a bus limiter that never
  reaches the render, the AI Audio Assistant and Deliver's loudness normalisation all broke the last-call mix. The
  master is built and measured outside it (section 9); `master.py fit` shows what Resolve's own mix does.
- **Frame the zoom around the webcam:** the PiP is held still; keep targets out of `look.py`'s red box.
- **Private details on screen:** blur them with a censor beat on the topmost track, scan the whole programme for the
  same words, and keep the words themselves out of the report and the publishing copy.
- **Sound effects that wear thin:** level by loudness, not peak (at the same peak bells and scribbles sound 6-10 dB
  louder than a click); only a zoom's first ding / scribble, accents 15 s apart, but every animation keeps its pops
  (variant C, editing-spec section 6). SFX are levelled against the raw voice and `master.py build` sets the voice
  stem back to that reference, so the files' levels are what the viewer hears (`sfx_bus_lift` 0 by default now).
- **Resolve's API can't set clip volume or keyframes reliably:** levels are baked into the audio files, motion is
  rendered, punch-ins are static transforms.

## Files
- `scripts/`: the pipeline (copied into `W/scripts` by `setup.sh`; per-project values live in `W/project.json`).
  `vedit.py` (vendored from davinci-resolve-video-edit), `program.py`, `scenes.py`, `look.py`, `zoom.py`,
  `overlay.py`, `assets.py`, `build_gfx*.py`, `render_gfx.sh`, `draftsheet.py`, `compose.py`, `matte_rvm.py`
  (split mattes, RVM), `matte_gpu.py` (u2net fallback), `audio.py` + `sfxlib.py` (the royalty-free SFX library),
  `music.py` (synthesized beds, from create-video-shorts), `music_gen.py` (generated hook music), `sfx_library.py`
  (builds the SFX library), `render_beats.sh`, `censor.py`, `pip_items.py`, `patch_flash.py`, `words.py` (word
  times in a window), `place.py`, `place_audio_swap.py` (a rebuilt audio layer onto new tracks), `publish.py`,
  `master.py` (the YouTube master and the final file: chain / layers / fit / build / deliver), `rs_items.py`,
  `rs_stem.py`, `rs_picture.py` (run inside Resolve with `script_plugin run_inline`: the audio item list, stems
  rendered through the user's chain, the delivery picture with the user's "YouTube - 2160p" preset), `cleanup.py`
  (frees the project's disk space after the upload, on the user's go-ahead), `media.py`, `config.py`, `faces.py`,
  `facecam.py` (the rounded facecam bubble for separate webcam recordings, with a speed/sync check per clip),
  `dyncam.py` (the dynamic camera layer: cfg / preview / strip / render / patch), `dyncam_plan.py` (busy / targets /
  draft / check), `dyncam_qc.py` (flash frames; face speed and sync), `rs_content.py` and `rs_layout.py` (run inside
  Resolve: the content layer + track map; the dynamic timeline).
- Shared, per machine (setup.sh): `~/.cache/pro-edit-models/rvm/` (matting), the music-generation env and weights
  (`references/setup-and-troubleshooting.md`).
- `assets/`: the 16:9 graphics engine + GSAP, Poppins, Instrument Serif, Figtree and Geist Mono, the face models, and
  `sfx/` - the royalty-free SFX library (54 sounds + `manifest.json` with sources and licences). Git holds the 27 CC0
  sounds; the 27 Mixkit ones may not be redistributed, so on a machine without them run
  `scripts/sfx_library.py build` (setup.sh does it; `references/setup-and-troubleshooting.md`, "Sound-effects library").
- `examples/`: the real test plan, its graphics config and its report, `harness-engineering/` - the reference
  edit (plan, zoom specs, both graphics modules, the briefs) that set the quality bar - and `dynamic-camera/`: the
  approved abacus v3 camera plan (every key with its reason) and its config.
- `references/`: `editing-spec.md` (the contract), `pipeline.md` (commands), `resolve-assembly.md` (MCP calls and
  gotchas), `graphics.md` (engine API), `foundation-cut.md` + `editorial-rules.md` (the clean cut),
  `separate-sources.md` (separate webcam + desktop recordings: sync, layout, facecam, the traps),
  `dynamic-camera.md` (the moving webcam for separate recordings: the rules, the pipeline, the plan, the bugs) and
  `pip-research.md` (the research behind it, with sources),
  `setup-and-troubleshooting.md`, `lessons.md`, and `design-system/` (the channel's "Leon YouTube" design system:
  readme, tokens, components, guidelines; bundled so the skill is self-contained, and implemented by the stage theme).
