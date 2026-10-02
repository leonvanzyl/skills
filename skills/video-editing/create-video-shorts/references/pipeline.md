# Pipeline: exact commands

Conventions:
- `SKILL`: this skill's folder.
- `P`: the user's video folder.
- `W`: `P/work-<video stem>`. Every script runs with `W` as the working directory.
- `PY`: `../.venv/Scripts/python.exe` (Windows), or `../.venv/bin/python` elsewhere.
- Shorts are named `s1`, `s2` and so on. Graphic runs are named `<short>_r<run index>`.

Contents: [0 Setup](#0-setup) · [1 Ingest](#1-ingest-and-analysis-all-in-parallel) · [2 Plan](#2-plan) · [3 Cut](#3-cut) · [4 Fan out](#4-fan-out) · [5 Composite](#5-audio-and-composite) · [6 Deliver](#6-verify-and-deliver) · [7 Edits](#7-edits)

## 0. Setup
```bash
bash "$SKILL/scripts/setup.sh" "$P"
bash "$SKILL/scripts/setup.sh" "$P/<video>.mp4"     # ONE video in a folder that also holds others (e.g. a finished edit next to its raw recordings)
```
The single-file form works in `<its folder>/shorts/` with a hard link to that video only (a copy if the link fails), so the other videos aren't processed. `P` is then that `shorts/` folder.

Setup creates:
- `P/.venv`. It takes about 15 s if the uv cache is warm and a few minutes on a new machine.
- `P/edit/`.
- `W` for every video in the root of `P`, each with `scripts/`, `gfx/` (HyperFrames project and engine), `fonts/`, `face_landmarker.task` and `project.json`.

Check `project.json`:
- `clean_audio`: a separate clean recording, if one was found next to the video.
- `fps`, `source_size` and `duration`.

## 1. Ingest and analysis (all in parallel)
```bash
cd "$W"
bash scripts/analyze.sh              # ingest -> transcribe / detect_camera / gaze / zoomscan, each started the moment its input exists
```
One call, run it in the background while you brief the research subagent. It prints a summary (sync, camera window, pose clusters, framing events, transcript size) and keeps every log in `logs/`. A 15 min 4K master takes about 1.7 min on the reference machine (ingest 60 s, then camera detection, then gaze + zoom scans ~30 s). With several videos, start one `analyze.sh` per work folder at once.

What it runs (the same scripts, which you can still run by hand):
```bash
$PY scripts/ingest.py                 # the ONE decode of the master; writes ingest_audio.done, then ingest.done
$PY scripts/transcribe.py clean16.wav transcript_full.json   # GPU Whisper large-v3, batched, word timestamps (~8 s for 15 min; as soon as ingest_audio.done exists)
$PY scripts/detect_camera.py          # as soon as ingest.done exists -> LOOK at detect_camera.png
$PY scripts/gaze.py &  $PY scripts/zoomscan.py &              # both read the proxy + camera window, 8 parallel slices each
```
`ingest.py` writes:
- `clean48.wav`, `clean16.wav` and `rms10ms.npy`, then the marker `ingest_audio.done`.
- `proxy1080_10.mp4` and `thumbs/`, then the marker `ingest.done`.

If a clean-audio file exists, ingest cross-correlates it against the camera track (16 kHz mono) and saves `sync` to `project.json`: the offset and the peak. It then writes the clean track already shifted onto video time. If not, it records that the embedded channels line up at zero lag.
- **`detect_camera.py`:**
  - Sets `camera.mode`: `full` means the frame is the camera; `pip` means a webcam window inside a screen recording.
  - Sets `camera.window` and `camera.safe`, which is the window inset past its border and rounded corners.
  - Always look at `detect_camera.png`. The red box is the window; the green box is the safe area. Fix `project.json` by hand if it's wrong.
- **`detect_camera.py` WARNING:** it lists sample times whose face sits elsewhere (the webcam moves for a stretch, or a full-frame shot). Keep camera runs out of those stretches.
- **`gaze.py`:**
  - Prints two head-pose clusters: on-lens vs reading. The on-lens one is NOT always the frontal one: with the webcam beside the screen, looking at the lens is the turned cluster. Calibrate on the outro with `eyesheet.py --window`.
  - In `pip` mode, it also lists stretches where a finished edit cuts to a full-frame camera shot. Mark lines taken from those with `"cam": "fullframe"`.
  - It runs `GAZE_WORKERS` (8) slices of the proxy in parallel, each with its own landmarker warmed up on the second before its slice. If `detect_camera.py` got the window wrong, fix `project.json` and re-run `gaze.py` (under a minute).
- **`zoomscan.py`:** lists punch-ins and framing jumps baked into the source. Keep every camera run clear of them. Also sliced (`ZOOM_WORKERS`, 8), with identical rows to a sequential pass.

### 1b. Finished edit with sound under the voice (only if needed)
If the source is a finished edit whose audio has music, a riser or SFX under lines you may keep, rebuild the clean audio from a clean voice stem (e.g. the long-form edit's dialogue track; a davinci-resolve-pro-edit run keeps `voice48.wav`). Do this before `cut.sh`. The transcript doesn't need re-running.
```bash
# project.json -> "clean_stem": {"voice": "<stem.wav>"}
$PY scripts/clean_from_stem.py --scan        # piecewise sync map (trims found automatically) + stretches the stem lacks
$PY scripts/clean_from_stem.py --suspects    # where the export has extra low-band sound: risers, pops, whooshes, music bass
# project.json -> "clean_stem.patches": [[t0, t1, "why"], ...]   kept lines inside music/SFX spans; boundaries in quiet gaps
$PY scripts/clean_from_stem.py --build       # clean48/clean16/rms10ms rebuilt, export audio kept as export48.wav
```
- **What gets patched:** only the patch windows take the stem. It is EQ-, compression- and level-matched to the export, so patched and unpatched lines sound the same. Everything else stays the export's own (processed) voice.
- **Never patch** a stretch the stem lacks, e.g. a call's far-end voice. `--scan` lists it as weak correlation.
- **The hook:** treat it as suspect even when `--suspects` is quiet. A music bed far under the voice doesn't show in the low band.

Meanwhile, spawn a research subagent. It fact-checks every figure the speaker says against 2+ sources. It also captures source pages, logos and pricing tables as 2x PNGs into `W/captures/` using a local Playwright, and writes `captures/facts.json`.

## 2. Plan
1. Read `transcript_full.json`, the gaze runs and the zoom events, then pick the lines for each short.
2. Look at eye crops before committing a line to a camera layout:
   ```bash
   $PY scripts/eyesheet.py --window 122.4,127.0 --step 0.2
   ```
   Use `--step 0.1` around a head turn.
3. Write `shorts.json`, using `SKILL/examples/plan_example_shorts.json` as the model. Per short:
   - `title`, `cover` (one or two lines) and `cta_keyword`
   - `highlights`: meaningful caption words or phrases, longest first
   - `music`: `{"style": "lofi"|"chillhop"|"ambient"|"synthwave"|"upbeat", "mood": "warm"|"moody"}`, chosen to fit this short's topic and energy. Optionally add `seed`, `bpm` and `key` (e.g. `"Ab"`). The seed defaults to a hash of the title, so every short gets its own track. Audition any style in seconds with `python -c "import sys; sys.path.insert(0,'scripts'); import music, soundfile as sf; x,p=music.render('lofi', 7, 30, drop=6); sf.write('m.wav', x, 48000); print(p)"`.
   - `lines`
4. Give each line:
   - `id`
   - `a` and `b`: the source start times of its first and last word, from the transcript
   - `layout`: `split`, `fc` or `fv`
   - optional `cam: "fullframe"`
   - `text`, which is the exact words and is used for alignment
   - `switches`: `[{"t": <source s near a word>, "layout": ...}]`, to hide or show the camera at a word boundary
   - `cta: true` on the outro line
   - optional `echo: true` on a line with a room echo (an AI voice on a call through speakers): align_lines collapses the phrases the ASR hears twice. Never on a stutter.

   Write `text` exactly as it should read on screen: captions take it word for word whenever its word count matches the aligned span (casing, numbers as said, misheard words fixed).

Rules for choosing layouts are in `editing-spec.md` sections 3–4. The hook is a split, the outro is full cam, no run runs past about 8 s, and no two runs in a row share a layout.

## 3. Cut
```bash
bash scripts/cut.sh s1               # align_lines -> cut2 -> verify_voice + eyesheet (in parallel); prints the runs, the proof and the sheet name
```
What it runs:
```bash
$PY scripts/align_lines.py           # silence-bounded re-transcription (4 parallel CUDA workers) + wav2vec2 forced alignment on the GPU -> line_align.json
$PY scripts/cut2.py                  # onsets / true ends / pause compression / J-cuts / loud-to-loud joins -> <sk>/voice.wav, cut.json (runs + words)
$PY scripts/verify_voice.py s1 &     # re-transcribe voice.wav (must read word-perfect) + list quiet stretches (joins must be <= 150 ms)
$PY scripts/eyesheet.py s1 &         # 8 eye crops per line -> s1_eyes.png (LOOK at it); the stills are grabbed by 12 parallel ffmpeg seeks and cached in eyes/
```
- **Switch points:** a switch snaps to the nearest aligned word start. To place one precisely, check `cut.json` → `lines[].words` and the RMS dips.
- **Missing word:** if Whisper drops a word, add it by hand at the end of `align_lines.py`. There's a commented example there.
- **Re-running:** `cut2.py` takes seconds, so iterate freely.

## 4. Fan out
**Graphics (parallel subagents):** copy `SKILL/examples/GFX_BRIEF_template.md` to `GFX_BRIEF.md`, fill it in (paths, webcam window, regions never to show, baked zooms/titles/censor), and give each subagent a tag (`s1a`, `s1b`, `s2a`…) with 2–5 compositions. Each tag owns `scripts/prep_assets_<tag>.py`, `gfx/asset_dims_<tag>.json` (all `asset_dims*.json` are merged) and `scripts/gfx_<tag>.py`, built with `build_gfx.py <tag>` (no tag = every `gfx_*.py`). For one short done by one agent, the single-file form below still works:
1. Write `scripts/prep_assets.py`, modelled on `SKILL/examples/prep_assets.py`. It copies captures into `gfx/assets/`, cuts still crops and synced footage clips (`synced()` follows the edit map), and writes `gfx/asset_dims.json`.
2. Give one subagent per composition, or per 2–3 short ones:
   - the run's brief, from `cut.json` runs plus the plan
   - `references/graphics.md`
   - `SKILL/examples/gfx_s1.py`
3. Each subagent writes its part of `scripts/gfx_<sk>.py`, builds it, renders a 10 fps draft, checks a contact sheet, fixes, then renders at full quality:
   ```bash
   $PY scripts/build_gfx.py s1
   bash scripts/render_draft.sh s1_r0 s1_r3    # 10 fps draft + contact sheet in one call -> gfx/draft/<r>.mp4, chk/<r>_sheet.png (LOOK)
   bash scripts/render_full.sh s1_r0 s1_r3     # 240 fps + motion blur (lossless PNG frames) -> tmix -> gfx/out60/<r>.mp4
   ```
   `render_full.sh` takes any number of compositions and throttles itself machine-wide: at most `RENDER_SLOTS` (3) renders at once, `HF_WORKERS` (8) Chrome browsers each, so every subagent can call it freely. An 8 s composition (1,949 frames at 240 fps) takes about 45 s alone (it was 168 s). It prints `done <r> <duration> (<frames> frames ...)` per composition; a `FAILED` line names the log.
   The old form still works for one-offs: `(cd gfx && npx --yes hyperframes render -c s1_r0.html --fps 10 --quality draft --video-frame-format png --workers 4 --output draft/s1_r0.mp4)` then `$PY scripts/draftsheet.py s1_r0 8`.

**At the same time, in the main agent:**
```bash
bash scripts/prep.sh s1 s2                   # cam clips (all runs at once, NVDEC) -> mattes (one GPU call, all shorts) -> captions/CTA events -> split frame checks
```
What it runs:
```bash
$PY scripts/cam_prep.py s1 s2                # frame-exact camera clips per camera run, 4 runs at a time -> <sk>/cam/r<i>.mkv + plan.json
# matte, split runs only (same frames as the card => frame-locked), ALL shorts in one GPU call:
$PY scripts/matte_gpu.py s1:0,3,5 s2:0,3 --jobs 4   # u2net_human_seg on onnxruntime-gpu CUDA + speaker-only cleanup, 3 frames in flight per run, FFV1 output
# (matte_gpu.py falls back to `hyperframes remove-background` itself if the model isn't cached or CUDA is missing: ~0.8 s/frame on CPU.)
$PY scripts/compose.py s1 --events-only      # captions.json + events_extra.json (CTA pop/keys/click), nothing else: audio.py can run now
$PY scripts/compose.py s1 --runs 0,6 --preview 4.0,40.4     # one full-resolution frame per split run (+ frame 0) -> s1/preview/, chk/s1_splits.png (LOOK)
```
The split check needs the split runs' graphics in `gfx/out60/`; `prep.sh` skips it and says so when they aren't rendered yet, so run `prep.sh` again (or the preview line above) once they are.

## 5. Audio and composite
```bash
bash scripts/finish.sh s1 [NN slug]          # audio.py + every segment in parallel (cached) -> concat -> verify_final -> ../edit/short-NN_<slug>/
```
What it runs:
```bash
$PY scripts/audio.py s1                      # SFX (graphics events + CTA), riser onto the hook join, music bed, mix -> s1/stems/, s1/mix.wav
$PY scripts/compose.py s1 --segments --no-concat   # one process per run, all at once; skips runs whose inputs are unchanged; checks every segment's frame count
$PY scripts/compose.py s1 --concat           # -> s1/final_video.mp4 (stream-copied segments + AAC 48 kHz)
```
Run it only after every `render_full.sh` for the short has printed `done`. The old per-run form still works: `$PY scripts/compose.py s1 --runs 3 --seg-out s1/seg/run03.mp4`.

**Split geometry** (`s1/cam/split_geom.json`) comes from measurements. Delete the file to re-measure.
- **Webcam window:** one scale for the whole short, so the whole face (hair to chin) fits in the visible card, with the hair about 95 px above the edge. Blurred side strips fill in where needed.
- **16:9 camera:** exactly the spec's geometry, 1890×1063 at x −405, y 1008.

## 6. Verify and deliver
`finish.sh` already ran this and copied the deliverables when given `NN slug`:
```bash
$PY scripts/verify_final.py s1/final_video.mp4 chk/s1_final.png   # streams, loudness, 2 s contact sheet (parallel grabs) -> LOOK
```
Otherwise copy `final_video.mp4` to `../edit/short-NN_<slug>/final.mp4`, and `s1/stems/` to `stems/`. Write `report.md` (`editing-spec.md` section 8) and update `../edit/PUBLISH.md` (section 8b).

`$PY scripts/report_data.py s1` prints the report's numbers in one go:
- lines with source ranges, runs and END;
- every SFX event with its absolute time and level, the riser, and the music parameters;
- the split geometry, the file facts, and the integrated loudness and true peak of `final_video.mp4`.

## 7. Edits
Change the smallest thing and re-run only what it touches. `finish.sh` re-renders only the segments whose inputs changed (it prints which), so after any of these the last step is always `bash scripts/finish.sh s1 NN slug`:
- **Captions, cover or CTA:** edit `shorts.json` (highlights, cover, keyword), then `finish.sh`. Only the runs whose captions changed are re-rendered.
- **A caption word's text while graphics are rendering:** don't re-run `align_lines.py`, because re-transcription can move a word edge by a frame. Patch the `w` field in `cut.json` (and the line's `text` in `shorts.json`), then `compose.py <sk> --events-only` and `finish.sh`.
- **Camera framing (split):** delete `s1/cam/split_geom.json`, then `finish.sh` (the split segments re-render).
- **One graphic:** edit `gfx_<sk>.py`, rebuild, `render_full.sh` for that run, then `finish.sh` (that run's segment only).
- **Line timing or line choice:** edit `shorts.json`, then `cut.sh` (align_lines re-transcribes every line; it's fast), `prep.sh` (the camera clips and mattes of the runs that moved; mattes are cached per run file), re-render the graphics whose runs moved, then `finish.sh`.
- **Music or SFX levels:** `finish.sh` (audio.py + concat, seconds; no segment is touched).
- **Title or description:** edit `PUBLISH.md` only.
