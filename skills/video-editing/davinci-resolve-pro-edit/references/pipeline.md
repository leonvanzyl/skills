# Pipeline: exact commands

Conventions (SKILL.md): `SKILL` this skill's folder, `CW` the CrisperWhisper Python, `PY` the render Python,
`W` the work dir (every command runs there: `cd "$W"`), `M` the media dir next to the source media.
Beat ids: `z..` zoom, `p..` punch, `g..` gfx, `w..` words, `c..` cta, `x..` censor.

Contents: [1 Setup](#1-setup) · [2 Programme map](#2-programme-map) · [3 Research](#3-research) · [4 Plan](#4-plan) ·
[5 Render](#5-render) · [6 Audio](#6-audio) · [7 Assemble](#7-assemble-in-resolve) · [8 Edits](#8-edits) ·
[9 Master and deliver](#9-master-and-deliver) · [10 Cleanup](#10-cleanup) ·
[11 Dynamic camera](#11-dynamic-camera-separate-webcam--desktop-recordings) · [Timings](#timings)

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
$PY scripts/pip_items.py                                                  # the PiP corner per V1 item (OBS scenes move it inside a file)
$PY scripts/patch_flash.py scan                                           # items that start/end on a flash of another window - LOOK
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
$PY scripts/compose.py g02 --matte                     # split beats only: the frame-exact camera clip + its matte on the GPU
                                                       #   (matte_rvm.py, Robust Video Matting; u2net matte_gpu.py when RVM is missing)
$PY scripts/matte_rvm.py g02 --preview 30,229          # RVM matte stills on grey (chk/g02_rvm_<n>.png) - LOOK at the hair edge
$PY scripts/compose.py g01 g02 --jobs 3                # -> $M/g01.mp4 (fvp: PiP pasted; split: camera card + head), one process per beat
$PY scripts/compose.py g02 --preview 0.5               # one full-resolution split frame in seconds - LOOK at the whole face
$PY scripts/draftsheet.py g01 8 --full
```
`render_gfx.sh full` throttles itself machine-wide (RENDER_SLOTS renders at a time, HF_WORKERS Chrome browsers each),
so every graphics subagent can call it freely; it prints `done <id> ... (capture N s, tmix M s)` or `FAILED <id>`.
Run `render_beats.sh`, the graphics renders and the composes concurrently; HyperFrames is the long pole.

## 6. Audio
SFX come from the royalty-free library in the skill's `assets/sfx` (`sfx_library.py --check`; `sfxlib.py`
loads it) and fall back to synthesized sounds without it. Besides the beats' own events, `audio.py` adds a highlight
swish on band/underline marks and highlight reveals, a soft ding on box marks, a soft whoosh peaking on the cut into
each full-visual graphic, and a sting on hook_end (`auto_sfx: false` in the plan turns that off). Then
`sfxlib.select` decides which play in the body (only a zoom's first ding / scribble, at most 5 pops per animation,
accents 15 s apart, at most 7 sounds in 15 s; plan `sfx_rules`), and every sound is levelled by loudness against the
RAW voice (`voice48.wav`; plan `sfx_levels`, `sfx_hook_bonus`; editing-spec section 6). The master (section 9) sets the
user's processed voice back to that reference, so leave `sfx_bus_lift` at its default 0. It prints the body's sounds per
minute, the accents, the busiest 15 s and why events were not played (also in `audio_clips.json` "sfx"): about
10-11 a minute is the reference. Hook music: `music.file` in the plan (a generated track from `music_gen.py`, with
`file_offset` where its lift should start) or the synthesized `music.style`; `music.under_voice_lu` sets how far under
the hook's voice it sits before the ~5 dB speech duck (default 18; 15 for a track that should lift the hook).
An edit writes new names with `--tag v2`.
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
    cut's tracks untouched).
12. Review render (also the user's review copy) with `script_plugin run_inline`, then decode frames of a zoom, a
    punch-in with a keyword pop, a split and a CTA from the file (ffmpeg `-ss <s> -frames:v 1`):
    ```python
    project.LoadRenderPreset('YouTube - 1080p'); project.SetCurrentRenderFormatAndCodec('mp4', 'H264_NVIDIA')
    project.SetRenderSettings({'SelectAllFrames': True, 'TargetDir': r'<M>
eview', 'CustomName': '<timeline> - review 1080p',
                               'FormatWidth': 1920, 'FormatHeight': 1080})   # False if any key is rejected: read the job back
    job = project.AddRenderJob(); project.StartRendering([job], False)       # returns at once; poll GetRenderJobStatus(job)
    ```
    `timeline_frame capture` works for one or two frames but once hung for 30 minutes.
13. Master and deliver (section 9), then `$PY scripts/publish.py`, then write `$M/report.md`.

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
- **Music only (same length):** edit the plan -> `audio.py --tag v3` -> `replace_clip` the music clip with
  `$M/music_hook_v3.wav`.
- **SFX or a new music file:** `audio.py --tag v2` moves sounds, so it is a new placement: `place_audio_swap.py plan
  --audio-tracks N --tag v2` -> add the tracks it lists -> `safe_import_media` its files -> `place_audio_swap.py ids`
  -> one `append_to_timeline` -> disable the old PE audio tracks and rename them "(old)" (`timeline set_track_enable`,
  `set_track_name`) -> save. One `timeline_versioning` run around it.
- **Many clips at once (a restyle):** one `script_plugin run_inline` that walks the media pool and calls
  `ReplaceClip(path)` per id, then `SaveProject()` (61 swaps in seconds).
- **A beat's timing or length changes:** the MCP cannot move or trim a placed clip. Append the new render at the new
  frame on the same track, then ask the user to delete the old clip (or use `timeline delete_clips`, which archives
  the timeline and needs the Edit page).
- **Publishing copy or chapters:** edit the plan -> `publish.py`; chapter markers with `timeline_markers`.
- **Anything on the timeline changed (yours or the user's):** run section 9 again (from 9b) so the final file
  matches the timeline; re-run 9a too if the user touched their voice track's effects.
Report what was re-rendered and how long it took.

## 9. Master and deliver
The user gets ONE file to upload: `$M/final/<timeline> - FINAL (-14 LUFS).mp4`, the timeline's picture with a master
made OUTSIDE Resolve's mixer and measured on the decoded file. Why outside: lessons.md, "Restructuring a cut".
In-Resolve steps are `script_plugin run_inline` calls that set a few globals and exec a script from `W/scripts`
(each restores the current timeline; a long one is moved to the background by the MCP - wait for its notification).
They write to `$M/_deliver/` (next to the sources: this app can't see files Resolve writes under AppData).
Every `$PY` step runs in `W`.

**9a. The voice chain** (always; also right after assembly when the pro edit had to be rebuilt). Render 30 s of A1
from the user's own timeline and from the pro edit, and compare each with its raw media:
```python
W = r'<W>'; M = r'<M>'
for TL, tag in (('<user timeline>', 'base'), ('<pro edit>', 'pe')):
    NAME = 'items_' + tag; exec(open(W + r'\scripts\rs_items.py').read())
    NAME = 'chain_' + tag; KEEP = [1]; RANGE = (0, 30 * 60)           # 30 s in frames (60 fps); a stretch with speech
    exec(open(W + r'\scripts\rs_stem.py').read())
```
```bash
$PY scripts/master.py chain "$M/_deliver/chain_base.wav" --items "$M/_deliver/items_base.json"
$PY scripts/master.py chain "$M/_deliver/chain_pe.wav"   --items "$M/_deliver/items_pe.json"
```
Each prints PROCESSED (EQ / isolation / dynamics on the voice: unexplained residual above -30 dB or band levels
1.5 dB apart) or RAW. The user's timeline PROCESSED and the pro edit RAW = their chain was lost (a rebuilt
timeline): stop and ask them to copy their voice-track effects onto the pro edit's A1, then check again. Both RAW
or both PROCESSED: carry on.

**9b. In Resolve: the item list, the stems, the picture** (the picture takes longest; run 9c meanwhile):
```python
W = r'<W>'; M = r'<M>'; TL = '<pro edit>'
NAME = 'items'; exec(open(W + r'\scripts\rs_items.py').read())
NAME = 'stem_base'; KEEP = 'base'; RANGE = None; exec(open(W + r'\scripts\rs_stem.py').read())   # the user's tracks, through their chain and bus
NAME = 'mix_resolve'; KEEP = 'all'; exec(open(W + r'\scripts\rs_stem.py').read())               # the mix as Resolve plays it, for `fit`
```
```python
W = r'<W>'; M = r'<M>'; TL = '<pro edit>'; exec(open(W + r'\scripts\rs_picture.py').read())     # -> $M/_deliver/picture.mp4
```
`rs_stem.py` disables the other tracks' CLIPS for the render (audio track enables are ignored by renders on 21.1)
and re-enables them - check it prints "still disabled: 0". `rs_picture.py` renders with the user's own export preset,
Resolve's built-in "YouTube - 2160p" (H.264 High, ~11 Mb/s at 4K60, ~2 GB for 25 minutes - what their own uploads
measure); it prints whether the preset loaded and names any render setting Resolve rejects.

**9c. The master:**
```bash
$PY scripts/master.py layers     # PE tracks rebuilt from their files at their clip positions -> levels/layer_A<n>.wav
$PY scripts/master.py fit        # Resolve's mix = base stem x g + layers x g: FLAGs any part not at 0 dB
$PY scripts/master.py build      # voice stem set to the raw voice's speaking loudness (minus sfx_bus_lift), + layers,
                                 # -> true-peak limiter (ceiling -1.5 dBTP) -> -14.0 LUFS; SFX audited against targets
```
`fit` flags explain what the user heard in Resolve that the master leaves out (on last-call: -14 dB fader automation
on PE SFX and PE Riser). Mention every flag to the user; the master keeps the designed levels unless they say
otherwise (`build --voice-db X` overrides the voice gain). `build` prints each SFX type's median offset from its
target (expect within +-0.5 LU) and the hook / body loudness and the quietest / loudest 30 s.

**9d. The final file:**
```bash
mkdir -p "$M/final"
$PY scripts/master.py deliver "$M/_deliver/picture.mp4" "$M/final/<timeline> - FINAL (-14 LUFS).mp4"
```
It checks sync (band-limited GCC-PHAT on 5 windows of the picture's own audio, decoded in full: ffmpeg's fast seek
on AAC is off by up to ~20 samples), muxes (video stream copied, AAC 384k), decodes the result and measures it,
dips any AAC overshoot over -1 dBTP (a 0.5 s dip of the overshoot + 0.3 dB) and re-muxes until none is left, then
prints FINAL {...} (with the bitrate and size: expect ~11 Mb/s and ~2 GB for 25 minutes; a NOTE flags anything over
30 Mb/s) and PASS (-14 +-0.3 LUFS, true peak <= -1 dBTP). Everything lands in `levels/master_report.json` for the
report. Tell the user the final file's path and numbers, then ask about the cleanup (section 10).

## 10. Cleanup
A finished edit leaves tens of GB behind (last-call: ~63 GB - the renders the timeline links to, the stems, the
picture, the final file, graphics frames, level checks, caches). Once the final file is delivered, ask the user to
say when it is safe to clean up - when the video is uploaded - and say what that means: every render goes,
including the final file, and the Pro Edit timeline's added clips will show as media offline in Resolve (the
timelines themselves stay). Show the dry run's total with the question. Only on their go-ahead:
```bash
cd "$M/.."                                                  # anywhere outside W: W is deleted
$PY "$SKILL/scripts/cleanup.py" "$M"                        # dry run: what goes, biggest first - nothing is deleted
$PY "$SKILL/scripts/cleanup.py" "$M" --delete               # after the user's yes; prints what it freed and what is left
```
It deletes every work dir whose `project.json` names this `M` (the clean cut's and any "__Recut" one) and everything
in `M` except `report.md`, `PUBLISH.md` and `captions.srt` (a few KB; `--all` removes those too). It refuses any
folder that isn't a `pro-edit-media` named by a work dir, and never touches the source recordings, the Resolve
project, or the shared caches (venvs, models, the SFX library, HyperFrames). Then run the check it prints inside
Resolve (`script_plugin run_inline`): this app's view of AppData is virtualised and can show a work dir as gone while
the real folder Resolve wrote is still there (last-call: an empty `levels/` survived). Last-call freed 69.3 GB.
Never delete timelines: the user removes those if they want.

## 11. Dynamic camera (separate webcam + desktop recordings)
The final picture for separate recordings (`dynamic-camera.md` has the rules and the why). Build the Pro Edit as
usual first (sections 1-7): it is the static version and the source of the content layer. Then:

**11a. In Resolve: the content layer and the track map** (~2 min for 9 minutes of 4K60):
```python
W = r'<W>'; M = r'<M>'; TL = '<pro edit>'
HIDE = ['Camera', 'Facecam', 'PE Facecam', 'PE Overlays']      # the tracks the camera layer replaces or must sit under
exec(open(W + r'\scripts\rs_content.py').read())                # -> $M/_deliver/content.mp4 + tracks.json
```
It prints the tracks it left out and any HIDE name it didn't find - check them against the timeline's track names.
PE Censor stays in the content.

**11b. The plan:**
```bash
$PY scripts/dyncam.py cfg                  # the face in the webcam -> dyncam_cfg.json ("camera_tracks": ["Camera"] by default)
$PY scripts/dyncam_plan.py busy            # clutter under each corner of the content layer -> corner_busy.npy
$PY scripts/dyncam_plan.py targets         # zoom marks, CTA cards (+ dyncam_targets_manual.json) -> dyncam_targets.json
$PY scripts/dyncam_plan.py draft           # -> dyncam_plan.json (the previous one is kept as dyncam_plan.prev.json)
```
Read the draft against `transcript.txt`, then edit it: CARD moments, FULL on reactions, `"content": "image:<png>"`
for a card beside a captured page, corners where the draft covers something (`dynamic-camera.md`, "The plan"). Beats
in `edit_plan.json` can steer a redraft (`"dyncam"`, `"dyncam_corner"`, `"dyncam_content"`). Then:
```bash
$PY scripts/dyncam_plan.py check           # exit 1 on errors; read every WARN
$PY scripts/dyncam.py --preview 46,300,100 # one frame per state: LOOK (preview/dyncam_<t>.jpg)
$PY scripts/dyncam.py --strip 39.5 45      # 45 consecutive frames across a move: step through them
```

**11c. The layer** (background; ~30 min for 9 minutes with 8 jobs on an RTX 5090; resumable):
```bash
$PY scripts/dyncam.py --jobs 8 --tag v1    # -> $M/layout_v1.mp4 (chunks in $M/_dyncam_v1/)
$PY scripts/dyncam_qc.py flash "$M/layout_v1.mp4"
```
A fix after the render: edit the plan or code, then `$PY scripts/dyncam.py patch --keys 19.0167,353.5667 --tag v1`
(+-3 frames around those keys, or every key without `--keys`). If the layer is already in Resolve, render the fix
under a new tag instead (Resolve holds the imported file open).

**11d. In Resolve: the dynamic timeline, then the final file:**
```python
W = r'<W>'; M = r'<M>'; TL = '<pro edit>'; NEW = '<pro edit> - Dynamic Camera'; LAYER = 'layout_v1.mp4'
exec(open(W + r'\scripts\rs_layout.py').read())                 # V+1 "PE Layout", V+2 "PE Overlays (top)", lower video off
TL = NEW; exec(open(W + r'\scripts\rs_picture.py').read())      # -> $M/_deliver/picture.mp4
```
```bash
$PY scripts/master.py deliver "$M/_deliver/picture.mp4" "$M/final/<pro edit> - Dynamic Camera - FINAL (-14 LUFS).mp4"
$PY scripts/dyncam_qc.py flash "$M/final/<...> - FINAL (-14 LUFS).mp4"
$PY scripts/dyncam_qc.py sync  "$M/final/<...> - FINAL (-14 LUFS).mp4"   # every state: lag 0, corr >= 0.85
```
The audio is the Pro Edit's own, so the master from section 9c is reused as it is (run 9 first if it isn't built).
`rs_layout.py` checks every appended clip's length and prints the track list: the layer must be one item of the
timeline's full length, and the overlays all re-placed.

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
- Master and deliver (last-call, 24:30 at 4K60): an audio-only stem render 70 s (2.3 min with the job overhead), the
  4K picture 6.5 min (that run used H.264 NVIDIA at ~97 Mb/s, 18 GB; the "YouTube - 2160p" preset gives ~2 GB), `layers`
  3 s, `fit` 5 s, `build` ~2 min, `deliver` ~4 min with the 18 GB picture (mux, decode, one overshoot fix and re-mux).
  About 15-20 minutes in all, mostly Resolve rendering. Cleanup dry run: ~10 s for 67 GB.
