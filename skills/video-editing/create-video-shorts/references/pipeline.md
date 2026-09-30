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
```
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
$PY scripts/ingest.py            &   # the ONE decode of the master
```
`ingest.py` writes:
- `clean48.wav`, `clean16.wav` and `rms10ms.npy`.
- `proxy1080_10.mp4` and `thumbs/`.

If a clean-audio file exists, ingest cross-correlates it against the camera track (16 kHz mono) and saves `sync` to `project.json`: the offset and the peak. It then writes the clean track already shifted onto video time. If not, it records that the embedded channels line up at zero lag.

The following steps start as soon as their input exists. Don't wait for the whole ingest.
```bash
$PY scripts/transcribe.py clean16.wav transcript_full.json &   # GPU Whisper large-v3, word timestamps (as soon as clean16.wav exists)
$PY scripts/detect_camera.py                                    # as soon as the proxy exists -> LOOK at detect_camera.png
$PY scripts/gaze.py &  $PY scripts/zoomscan.py &                # both read the proxy + camera window
```
- **`detect_camera.py`:**
  - Sets `camera.mode`: `full` means the frame is the camera; `pip` means a webcam window inside a screen recording.
  - Sets `camera.window` and `camera.safe`, which is the window inset past its border and rounded corners.
  - Always look at `detect_camera.png`. The red box is the window; the green box is the safe area. Fix `project.json` by hand if it's wrong.
- **`gaze.py`:**
  - Prints two head-pose clusters: on-lens vs reading.
  - In `pip` mode, it also lists stretches where a finished edit cuts to a full-frame camera shot. Mark lines taken from those with `"cam": "fullframe"`.
- **`zoomscan.py`:** lists punch-ins and framing jumps baked into the source. Keep every camera run clear of them.

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

Rules for choosing layouts are in `editing-spec.md` sections 3–4. The hook is a split, the outro is full cam, no run runs past about 8 s, and no two runs in a row share a layout.

## 3. Cut
```bash
$PY scripts/align_lines.py           # silence-bounded re-transcription + wav2vec2 forced alignment -> line_align.json
$PY scripts/cut2.py                  # onsets / true ends / pause compression / J-cuts / loud-to-loud joins -> <sk>/voice.wav, cut.json (runs + words)
$PY scripts/verify_voice.py s1 &     # re-transcribe voice.wav (must read word-perfect) + list quiet stretches (joins must be <= 150 ms)
$PY scripts/eyesheet.py s1 &         # 8 eye crops per line -> s1_eyes.png (LOOK at it)
```
- **Switch points:** a switch snaps to the nearest aligned word start. To place one precisely, check `cut.json` → `lines[].words` and the RMS dips.
- **Missing word:** if Whisper drops a word, add it by hand at the end of `align_lines.py`. There's a commented example there.
- **Re-running:** `cut2.py` takes seconds, so iterate freely.

## 4. Fan out
**Graphics (parallel subagents):**
1. Write `scripts/prep_assets.py`, modelled on `SKILL/examples/prep_assets.py`. It copies captures into `gfx/assets/`, cuts still crops and synced footage clips (`synced()` follows the edit map), and writes `gfx/asset_dims.json`.
2. Give one subagent per composition, or per 2–3 short ones:
   - the run's brief, from `cut.json` runs plus the plan
   - `references/graphics.md`
   - `SKILL/examples/gfx_s1.py`
3. Each subagent writes its part of `scripts/gfx_<sk>.py`, builds it, renders a 10 fps draft, checks a contact sheet, fixes, then renders at full quality:
   ```bash
   $PY scripts/build_gfx.py s1
   (cd gfx && npx --yes hyperframes render -c s1_r0.html --fps 10 --quality draft --video-frame-format png --output draft/s1_r0.mp4)
   $PY scripts/draftsheet.py s1_r0 8          # -> chk/s1_r0_sheet.png
   bash scripts/render_full.sh s1_r0          # 240 fps + motion blur -> tmix -> gfx/out60/s1_r0.mp4 (run several in parallel)
   ```

**At the same time, in the main agent:**
```bash
$PY scripts/cam_prep.py s1                   # frame-exact camera clips per camera run -> s1/cam/r<i>.mkv + plan.json
# matte, split runs only (same frames as the card => frame-locked):
ffmpeg -v error -y -i s1/cam/r0.mkv -c:v libx264 -crf 8 -pix_fmt yuv444p s1/cam/r0.mp4
npx --yes hyperframes remove-background s1/cam/r0.mp4 -o s1/cam/r0_matte.mov --device cuda   # falls back: omit --device (CPU, ~7 fps)
```

## 5. Audio and composite
```bash
$PY scripts/compose.py s1 --preview 0        # writes captions.json + events_extra.json (CTA pop/keys/click); measures split geometry
$PY scripts/audio.py s1                      # SFX (graphics events + CTA), riser onto the hook join, music bed, mix -> s1/stems/, s1/mix.wav
$PY scripts/compose.py s1 --runs 0,6 --preview 3.0,40.0     # spot-check frames of chosen runs only -> s1/preview/
mkdir -p s1/seg; for i in $(seq 0 <last run>); do $PY scripts/compose.py s1 --runs $i --seg-out s1/seg/run$(printf %02d $i).mp4 & done; wait
$PY scripts/compose.py s1 --concat           # -> s1/final_video.mp4 (stream-copied segments + AAC 48 kHz)
```
**Split geometry** (`s1/cam/split_geom.json`) comes from measurements. Delete the file to re-measure.
- **Webcam window:** one scale for the whole short, so the whole face (hair to chin) fits in the visible card, with the hair about 95 px above the edge. Blurred side strips fill in where needed.
- **16:9 camera:** exactly the spec's geometry, 1890×1063 at x −405, y 1008.

## 6. Verify and deliver
```bash
$PY scripts/verify_final.py s1/final_video.mp4 chk/s1_final.png   # streams, loudness, 2 s contact sheet -> LOOK
```
Copy `final_video.mp4` to `../edit/short-NN_<slug>/final.mp4`, and `s1/stems/` to `stems/`. Write `report.md` (`editing-spec.md` section 8) and update `../edit/PUBLISH.md` (section 8b).

## 7. Edits
Change the smallest thing and re-run only what it touches:
- **Captions, cover, CTA or camera framing:** re-run step 5 for the affected runs (segments), then `--concat`.
- **One graphic:** edit `gfx_<sk>.py`, rebuild, run `render_full.sh` for that run, then re-run its compose segment and `--concat`.
- **Line timing or line choice:** edit `shorts.json`, then run `align_lines.py` (for new lines only) and `cut2.py`. Graphics whose runs moved need re-rendering; re-composite everything after the change.
- **Music or SFX levels:** `audio.py`, then `--concat` (seconds).
- **Title or description:** edit `PUBLISH.md` only.
