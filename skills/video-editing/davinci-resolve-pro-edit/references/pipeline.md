# Pipeline: exact commands

Conventions (SKILL.md): `SKILL` this skill's folder, `CW` the CrisperWhisper Python, `PY` the render Python,
`W` the work dir (every command runs there: `cd "$W"`), `M` the media dir next to the source media.
Beat ids: `z..` zoom, `p..` punch, `g..` gfx, `w..` words, `c..` cta, `x..` censor.

Contents: [1 Setup](#1-setup) · [2 Programme map](#2-programme-map) · [3 Research](#3-research) · [4 Plan](#4-plan) ·
[5 Render](#5-render) · [6 Audio](#6-audio) · [7 Assemble](#7-assemble-in-resolve) · [8 Edits](#8-edits) · [Timings](#timings)

## 1. Setup
```bash
bash "$SKILL/scripts/setup.sh" "$W" "$M"
```
Creates the render env if needed (uv, ~1 min the first time), copies scripts, the graphics engine, fonts and face
models into `W`, and writes `W/project.json` (`media_dir`). Put `M` next to the recording's source files (for
example `<sources>/pro-edit-media`): Resolve links to these files, so they must stay put, and a packaged app may
virtualise writes under AppData so Resolve would never see them.

If the chosen timeline is not a clean cut yet, make one first (`references/foundation-cut.md`) and continue on it.

## 2. Programme map
In Resolve (read-only): make the clean cut current (`timeline set_current {name}`), then
`timeline probe_timeline_structure`. The result is large and is saved to a tool-results file: copy it to
`$W/structure_raw.json` (a short timeline may come back inline - write it there yourself).
```bash
cp "<saved probe file>" structure_raw.json
"$CW" scripts/vedit.py prepare --work . --structure structure_raw.json    # items.json, 16 kHz audio per source
"$CW" scripts/vedit.py sample --work . --n 30                              # names/jargon for hotwords (tell the user in one line)
"$CW" scripts/vedit.py transcribe --work . --hotwords "Name1, Name2"      # background, ~1.5 s per clip; resumable
$PY scripts/program.py                                                    # program.json, voice48.wav, rms10ms.npy, transcript.txt
$PY scripts/scenes.py                                                     # scenes.json + scenes.png (LOOK), scene column in transcript.txt
```
- If the clean cut was made by the foundation-cut step in this same session, reuse its hotwords (and its
  `hotwords.txt`); the transcripts of the clean cut's clips are re-made here because clip boundaries differ.
- `prepare` warns about clips next to transitions ("record length != source length", "slipped audio"): expected on
  a timeline the user has worked on. `program.py` handles them; beats must not cross the transition itself.
- `scenes.py` prints the PiP window per source file. When one file's edge scan runs off, the consensus window is
  used and reported. Confirm on `scenes.png` that `cam` items really are the full-frame camera.

## 3. Research
Spawn a subagent as soon as `transcript.txt` exists. Give it the transcript and ask it to:
- fact-check every figure, date, price and claim against 2+ reputable sources, noting disagreements;
- capture, as 2x PNGs into `W/captures/`, every page the speaker cites that the recording does not show (docs,
  announcements, repos, pricing, benchmark tables, posts), cropped to the passage, plus official logos (SVG or
  PNG) of every named product;
- write `captures/facts.json` (figure -> sources, verdict) and `captures/index.json` (file -> url, what it shows).
Capture pages with `npx --yes hyperframes capture <url> -o captures/<name> --skip-assets --skip-vision`
(`screenshots/full-page.png` + `extracted/visible-text.txt`; tested on anthropic.com), or the Browser tools for a
single view. If a page is behind a login, rebuild the view from public screenshots or docs and say so.

## 4. Plan
Read `transcript.txt` top to bottom (one line per V1 item: index, programme time, duration, scene, words). Then:
```bash
$PY scripts/look.py 12.5 16.0 47.5                                   # look/<t>.jpg with a source-pixel grid
$PY scripts/look.py 12.5 --rect 1900,730,200,170 --zoom 1.75,1150,700 # a mark (clay) + the zoomed view (magenta)
                                                                      # + what the held-still PiP covers (red)
```
Word times for cues: `python -c "import json;P=json.load(open('program.json'));print([(w['w'],w['s']) for w in P['words'] if 45<=w['s']<52])"`.
Write `edit_plan.json` (schema: `SKILL/examples/edit_plan_example.json`):
- `hook_end` (spec section 2), `music` {style, mood, fade_out, optional drop/seed/bpm/key}
- `beats`: every beat with `id`, `kind`, `t0`/`t1` (programme seconds; snap to frames: round(t*fps)/fps), a `note`
  saying why it earns its place, and the kind's fields (`zoom.py`, `overlay.py`, `compose.py`, `censor.py` docstrings)
- `chapters` [{t, title}], `caption_fixes` {phrase: replacement}, `publish` {title, description}
Check before rendering: every hook sentence treated, no two hook beats alike in a row, body density per the spec,
no beat across a V1 transition or a scene change, no overlap between beats on the same track (graphics/zooms share
V+1, words/CTAs share V+2).

## 5. Render
Censor beats come first, because a zoom inside one bakes the blur into its own frames from the track file:
```bash
$PY scripts/censor.py ref 450.0                        # censor/ref_450.0.png, full resolution: measure the word boxes on it
$PY scripts/censor.py track x01 --jobs 12              # censor/x01_track.json; prints detections per V1 item - check the first and last
$PY scripts/censor.py scan x01 0 <programme end> --gpu # the same words anywhere else? (NVDEC, so it can run beside renders)
$PY scripts/censor.py preview x01 442.0 500.0 565.5    # preview/x01_<t>.png - LOOK: the whole block blurred, nothing else
$PY scripts/censor.py render x01                       # -> $M/x01.mov (ProRes 4444 + alpha) for "PE Censor", the top track
```
A V1 transition inside the beat (a Bounce the editor added) can't be followed from the source: render its frames out
of Resolve, then `censor.py transition x01 <that.mov> <its first timeline frame>` before `render`. It patches the
outgoing side; check the incoming side by eye.

Preview a few zooms first (frames at rest are bit-identical to V1; a preview decodes only the frames it shows):
```bash
$PY scripts/zoom.py z01 --preview 0.0,1.2,6.5          # preview/z01_<t>.png - LOOK (seconds, not the beat's decode)
$PY scripts/overlay.py w01 c01 --preview 0.6,3.2       # on grey, to see the alpha
```
Then every zoom, keyword pop and CTA of the plan plus the audio, in one background call:
```bash
bash scripts/render_beats.sh                           # all zoom/words/cta beats: zooms 4 at a time, overlays 3 at a time, then audio.py
bash scripts/render_beats.sh z01 z02 c01               # only these (and audio.py again)
```
What it runs (each also takes `--jobs N` on its own):
```bash
$PY scripts/zoom.py z01 z02 z03 --jobs 4               # -> $M/z01.mp4 ... one process per beat (NVENC when available; --x264 forces software)
$PY scripts/overlay.py w01 c01 --jobs 3                # -> $M/w01.mov, $M/c01.mov (ProRes 4444 + alpha), events/<id>.json
$PY scripts/audio.py                                   # after the overlays (it reads their SFX events)
```
Graphics (one subagent per 1-3 beats; `references/graphics.md`):
```bash
$PY scripts/assets.py still 260.0 700,880,1120,200 session.png          # real UI/numbers from the recording
$PY scripts/assets.py still src:7.mkv@473.27 0,110,3060,1720 game.png   # a later moment of any source file
$PY scripts/build_gfx.py <name>                        # scripts/gfx_<name>.py -> gfx/<id>.html (+ gfx/sfx_events.json)
bash scripts/render_gfx.sh draft g01 g02               # 10 fps drafts, all at once
$PY scripts/draftsheet.py g01 8                        # chk/g01_sheet.png - LOOK, fix, rebuild
bash scripts/render_gfx.sh full g01 g02                # 4x fps + motion blur, lossless PNG capture, UHD at device scale 2 -> gfx/out/
$PY scripts/compose.py g02 --matte                     # split beats only: the frame-exact camera clip + its matte on the GPU (matte_gpu.py)
$PY scripts/compose.py g01 g02 --jobs 3                # -> $M/g01.mp4 (fvp: PiP pasted; split: camera card + head), one process per beat
$PY scripts/compose.py g02 --preview 0.5               # one full-resolution split frame in seconds - LOOK at the whole face
$PY scripts/draftsheet.py g01 8 --full
```
`render_gfx.sh full` throttles itself machine-wide (RENDER_SLOTS renders at a time, HF_WORKERS Chrome browsers each),
so every graphics subagent can call it freely; it prints `done <id> ... (capture N s, tmix M s)` or `FAILED <id>`.
Run `render_beats.sh`, the graphics renders and the composes concurrently; HyperFrames is the long pole.

## 6. Audio
```bash
$PY scripts/audio.py        # $M/sfx/*.wav, $M/music_hook.wav, $M/riser.wav, audio_clips.json, mix_preview.wav
```
Run it after every overlay and graphic exists (it reads their SFX events). Listen to the first minute of
`mix_preview.wav`: music under the hook, the drop after the first sentence, the riser landing on hook_end, the
music gone by hook_end + fade_out, every SFX audible but under the voice.

## 7. Assemble in Resolve
Full call sequence and gotchas: `references/resolve-assembly.md`. In short:
1. `timeline_versioning begin_run {analysis_run_id: "pro-edit-<name>"}`; pass that id to every destructive call.
2. `timeline set_current {name: <clean cut>}` -> `timeline duplicate {name: "<base> - Pro Edit v1"}` (it becomes current).
3. `timeline get_track_count` video/audio -> `$PY scripts/place.py plan --video-tracks N --audio-tracks M`.
4. `timeline add_track` for each PE track (audio `options: {audio_type: "stereo"}`), `set_track_name` each.
5. `media_pool add_subfolder` "Pro Edit" and "<timeline name>" inside it -> `media_pool safe_import_media
   {paths: placement.json import_files, target_folder: "Pro Edit/<timeline name>"}` -> save the result as
   `import_result.json`.
6. `timeline_markers get_all` -> save as `existing_markers.json` ->
   `$PY scripts/place.py ids import_result.json --existing-markers existing_markers.json`.
7. `media_pool append_to_timeline {clip_infos: <append_clip_infos.json>}` (one call).
8. `timeline bulk_set_item_properties {ops: <bulk_ops.json>, readback: true}` (punch-ins).
9. `timeline_markers add` for each entry of `markers_add.json`.
10. `project_manager save`, `timeline_versioning end_run`.
11. `timeline probe_timeline_structure` -> `built_structure.json` ->
    `$PY scripts/place.py verify built_structure.json structure_raw.json` (expect every clip exact and the clean
    cut's tracks untouched), then `timeline_frame capture {frame, quality: "preview", max_width: 1280}` on a zoom,
    a punch-in with a keyword pop, a split and a CTA.
12. `$PY scripts/publish.py`, then write `$M/report.md`.

## 8. Edits
Change the plan, then re-run only what it touches. Resolve holds the imported files open, so an edit renders to a
NEW file (`--tag v2` -> `<id>_v2.<ext>`) and swaps it in with
`media_pool_item replace_clip {clip_id: <the old file's media pool id>, path: <new file>}`: every timeline use of
that clip picks up the new render in place (tested: same length, same position, new pixels).
- **A zoom or overlay (same t0/t1):** `zoom.py <id> --tag v2` / `overlay.py <id> --tag v2` -> `replace_clip`.
- **A censor (same t0/t1):** `censor.py track` -> `censor.py render <id> --tag v2` -> `replace_clip`; re-render
  every zoom inside the beat too, since they carry the old blur.
- **A graphic (same t0/t1):** edit `scripts/gfx_<name>.py` -> build -> draft -> `render_gfx.sh full <id>` ->
  `compose.py <id> --tag v2` -> `replace_clip`.
- **Music or SFX:** edit the plan -> `audio.py` writes the same names; copy the changed WAVs to new names (or
  re-run with the old ones removed from the pool) and `replace_clip` each; a changed SFX *time* is a new placement.
- **A beat's timing or length changes:** the MCP cannot move or trim a placed clip. Append the new render at the new
  frame on the same track, then ask the user to delete the old clip (or use `timeline delete_clips`, which archives
  the timeline and needs the Edit page).
- **Publishing copy or chapters:** edit the plan -> `publish.py`; chapter markers with `timeline_markers`.
Report what was re-rendered and how long it took.

## Timings
Measured on the cubefarm project (RTX 5090, 32 cores, 4K60 timeline, 192 V1 items), old scripts vs the current ones
on the same beats; every "new" output was compared frame for frame with the old one (lessons.md):
- `vedit transcribe`: 141 clips in 4 min (unchanged; the CrisperWhisper env). `program.py`: 10 s.
- `scenes.py`: 858 samples from 192 items, 243 s -> 195 s with 16 decode threads (`SCENE_WORKERS`), same labels and
  PiP windows; each sample is one ffmpeg seek into a 4K60 recording, so this stays decode-bound.
- `zoom.py`: a 7 s beat in 26 s (NVENC, unchanged per beat); four beats 101 s one after another -> 69 s with
  `--jobs 4` (`render_beats.sh` does this for the whole plan). A 3-frame preview 6 s -> 2 s.
- `overlay.py`: a 1 s keyword pop 7 s -> 3 s; a 5 s CTA 80 s -> 29 s (94 distinct drawings for 300 frames).
- HyperFrames full render at 240 fps, UHD (g03, 5.6 s, 1,349 frames): 88 s -> 68 s capture with 12 own browsers,
  lossless instead of JPEG; tmix 16 s (x264 slow) -> 11 s (NVENC lossless). Budget ~2 min per 10 s graphic.
- `compose.py`: fvp 10 s beat 35 s (unchanged, encoder-bound); split 5.6 s beat 137 s -> 88 s; a split preview
  8 s -> 4 s. The split matte: 87 s on the CPU CLI -> 15 s on the GPU (`matte_gpu.py`).
- Assembly in Resolve: under a minute of MCP calls.
