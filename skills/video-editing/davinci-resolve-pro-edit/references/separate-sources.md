# Separate webcam + desktop recordings

Use this when the recording is NOT one composited OBS file: a DESKTOP file and a WEBCAM file per take (OBS source
record), often with an empty template timeline (YTHD60) whose A1 carries the user's voice chain. First run:
abacus-test, 2026-11-01 (7 pairs: DESKTOP 2560x1440, WEBCAM 3840x2160, both 60 fps). Details in lessons.md,
"Separate screen + webcam recordings".

**The final picture is the dynamic camera** (`dynamic-camera.md`, `pipeline.md` section 11): the webcam morphs between
full frame, a side card, a corner window and hidden, on eased moves at cuts and sentence breaks, top-right by default.
The user approved it as the standard for separate recordings ("exactly the quality of editing that I expect going
forward"). The static tracks below are still built: they are the content layer's source and the fallback.

## The rules that bit
1. **Facecam renders: every image input is `-loop 1 -framerate <fps>`.** ffmpeg reads a looped PNG at 25 fps, and an
   overlay whose base is that PNG takes its clock: the bubble played ~2.4x fast ("my mouth is moving extremely
   fast") and showed frames from much later (an eye-wipe that was never there). Render bubbles ONLY with
   `scripts/facecam.py`: it has the fix and checks every clip against its source (frame count, speed 1x vs 2.5x,
   frame offset 0) before it says `ok`. Check any bubble made another way with `facecam.py check`.
2. **WAVs take the PROJECT frame rate on import** (24 in this template while the timeline was 60): convert every audio
   clip's frame range (`n * clip_fps / timeline_fps`) or each SFX lasts 2.5x and overlapping ones are silently dropped.
3. **HyperFrames `gfx/out/*.mp4` is NVENC lossless High 4:4:4**, which Resolve decodes as grey smears. This layout
   needs no compose.py (no PiP to paste), so transcode to High yuv420p (cq 15, bt709 tags) before importing.
4. **Small alpha clips 1:1:** `Scaling` = 1 (Crop), then Pan/Tilt in CLIP-relative units (`px * TW / clip_w`,
   `px * TH / clip_h`; facecam.py's docstring has the numbers).

## The build
- **Sync:** both files carry the same mic. Correlate 5 ms log-RMS envelopes (+-3 s), then refine at sample level:
  r 0.99+, whole-frame offsets (the desktop started 5-9 frames earlier). Raw-waveform correlation failed (r 0.02).
- **Foundation cut:** split the webcam audio into phrases at pauses (>= 0.45 s, 0.18 s pads) into a
  probe-shaped structure for `vedit.py prepare`, then transcribe / keep.json / verify / qa as usual.
- **Clean cut = a duplicate of the template** (the voice chain comes with it; voice-chain check PROCESSED):
  - V1: desktop, with the same source range + the pair's offset
  - V2: empty, so zooms and screen-line graphics can sit under the live bubble
  - V3: full-frame webcam on camera lines
  - V4: facecam bubble on screen lines, top-right by default (the research: `dynamic-camera.md`, "Where to put it");
    another corner only where the screen's content sits under it
  - A1: webcam audio. The desktop audio is not used.
- **Layout per line** (the user's ask: modern best practice, not a fixed PiP): camera full-frame for talking lines;
  the screen + bubble for demos; short timelapses for agent waits; the hook opens on the finished result.
- **Programme map for the skill's renderers:** V1 items = desktop file + source frames, audio = the webcam file.
  `zoom.py` handles the 1440p source (kfit) with `"pip": "none"`. scenes.json needs a `files` key ({} is fine).
- **Pro edit tracks:**
  - V2: zooms and screen-line graphics (under V4)
  - V5 PE Graphics: graphics and B-roll over the camera
  - V6 PE Facecam: bubble pieces over `fvc` graphics, rendered per programme item so they follow the cut (only
    for the static version: the dynamic camera replaces V3/V4/V6 in the final picture)
  - V7 PE Overlays
  - A4+: PE audio
  - Punch-ins go on the V3 camera items.
- **Graphics and B-roll are briefed with the camera's corner** (`dynamic-camera.md`, "Brief the graphics"): `fvc`
  keeps a 384 px square clear 40 px from the top-right corner unless the beat's `"dyncam_corner"` says otherwise; `fv`
  hides the camera. On abacus the graphics were built around a bottom-right bubble, which held the hook bottom-right.

## The final picture
After the Pro Edit is assembled and mastered: `rs_content.py` (the Pro Edit without Camera, Facecam, PE Facecam and
PE Overlays) -> `dyncam.py cfg` -> `dyncam_plan.py busy / targets / draft` -> edit the plan -> `check` -> strips ->
`dyncam.py --jobs 8` -> `dyncam_qc.py flash` -> `rs_layout.py` ("<Pro Edit> - Dynamic Camera") -> `rs_picture.py` ->
`master.py deliver` -> `dyncam_qc.py flash` + `sync` on the final file. Exact calls: `pipeline.md` section 11.
