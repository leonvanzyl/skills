# Assembly in Resolve: the MCP calls and their gotchas

Server: community [samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp), tools
`mcp__davinci-resolve__<tool>`, each taking `action` + `params`. Load them with ToolSearch query `davinci resolve`.
Every call below was run on Resolve Studio 21.1 with MCP 2.103 on the first project (2026-09-30).

## The build, call by call
| Step | Call | Notes |
|---|---|---|
| One archive, not twenty | `timeline_versioning begin_run {analysis_run_id: "pro-edit-<name>", label, initiator}` | Put the same `analysis_run_id` in EVERY destructive call below. Measured: one archive of the source at `duplicate`, one of the new timeline at the first `add_track`, none after. `end_run` at the end. |
| Pick the base | `timeline set_current {name: "<clean cut>"}` | Also used read-only for probing. |
| New timeline | `timeline duplicate {name: "<base> - Pro Edit v1", analysis_run_id}` | Keeps everything the editor did (transitions, sounds, titles, markers, start timecode) and becomes the current timeline. Never rebuild the timeline from source ranges: that silently drops titles, generators and transitions. If the name exists, use v2, v3... |
| Existing tracks | `timeline get_track_count {track_type: "video" / "audio"}` | Feed to `place.py plan --video-tracks N --audio-tracks M`. |
| Add tracks | `timeline add_track {track_type: "video", analysis_run_id}`; audio: `{track_type: "audio", options: {audio_type: "stereo"}, analysis_run_id}` | Audio defaults to MONO without `audio_type`. Appends at the top. |
| Name tracks | `timeline set_track_name {track_type, index, name, analysis_run_id}` | The key is `index`, not `track_index`. Names: PE Graphics, PE Overlays, PE Censor (only with a censor beat), PE SFX, PE Music, PE Riser. |
| A bin | `media_pool add_subfolder {name: "Pro Edit"}`, then `{name: "<timeline>", parent_path: "Pro Edit"}` | `safe_import_media` needs the folder to exist. |
| Import | `media_pool safe_import_media {paths: [...], target_folder: "Pro Edit/<timeline>"}` | Returns `clips: [{name, id, file_path, duration}]`; save the whole result as `import_result.json` for `place.py ids`. Raw `import_media` returns only a count and lands in whatever folder is current (after an archive that is the Archive bin). |
| Existing markers | `timeline_markers get_all` | Save as `existing_markers.json` - a duplicated clean cut brings its review markers, and Resolve keeps one marker per frame. |
| Place everything | `media_pool append_to_timeline {clip_infos: <append_clip_infos.json>}` | ONE call for all clips. Rows: `media_pool_item_id, start_frame, end_frame (exclusive), record_frame (relative to the timeline start), track_index, media_type (1 video, 2 audio)`. Not archived. The response lists every item on the timeline (huge on long timelines) - read `success`, `count` and `verified`. |
| Punch-ins | `timeline bulk_set_item_properties {ops: <bulk_ops.json>, readback: true}` | `ops: [{timeline_item: {track_type: "video", track_index: 1, item_index: <v1>}, transform: {ZoomX, ZoomY, Pan, Tilt}}]`. Not archived; returns per-key `success` + `readback`. |
| Markers | `timeline_markers add {frame, color, name, note, duration: 1, analysis_run_id}` | `frame` is relative to the timeline start. Chapters Blue; "Listen: hook -> content" Yellow. A taken frame fails - `place.py` nudges to the next free frame. |
| Save | `project_manager save` | |

## Verify
- `timeline probe_timeline_structure` on the new timeline -> saved to a tool-results file -> copy to
  `built_structure.json` -> `place.py verify built_structure.json structure_raw.json`. Expect
  "N/N clips exactly where planned | clean-cut tracks untouched".
- `timeline detect_gaps_overlaps` is NOT a pass/fail here: the PE tracks are sparse by design, and the editor's
  transitions show up as V1 overlaps on the clean cut too.
- Look at the result: `timeline_frame capture {frame, quality: "preview", max_width: 1280}` inside a zoom, on a
  punch-in with a keyword pop, inside a split and on a CTA card. Add `timeline_name: "<clean cut>"` to capture the
  same frame from the clean cut for a before/after (it switches and restores the current timeline). It renders one
  frame through the Deliver page and resets the project's render target directory, file name and mark range - say
  so in the report. One capture once hung for 30 minutes on a 16-minute timeline: for more than a frame or two,
  make the 1080p review render instead (pipeline.md section 7, step 12) and decode frames from the file - the user
  gets a review copy out of it too.

## Facts measured on the build
- **Transforms:** `ZoomX/ZoomY` 1.0 = 100%, about the frame centre. `Pan` +right and `Tilt` +UP, in timeline
  pixels (a 1.15 zoom with Tilt -116 on a UHD timeline moved the eye line from 32% to 34% of the height).
- **Alpha:** ProRes 4444 written by ffmpeg with straight alpha composites correctly on an upper track with no
  clip-attribute changes (clean strokes, soft shadows, no halos).
- **Audio levels:** there is no working API for fades, track levels, bus or track effects - every level is baked
  into the WAV. WAVs are padded to whole frames so every requested frame range exists. Clip volume does work on 21.1
  (`TimelineItem.SetProperty('AudioVolume', dB)` / `GetProperty`), and `master.py` reads it back for the master.
- **4K exports:** always Resolve's built-in "YouTube - 2160p" preset (`LoadRenderPreset('YouTube - 2160p')`; the
  user's rule), changing only `SelectAllFrames`/range, `TargetDir` and `CustomName`. It gives H.264 High at ~11 Mb/s
  for 4K60. `rs_picture.py` does this.
- **Rendering stems (21.1):** `SetTrackEnable('audio', k, False)` changes nothing (`GetIsTrackEnabled` still reads
  True and the render plays the track); disabling the clips works (`TimelineItem.SetClipEnabled(False)`, re-enable
  afterwards - `rs_stem.py`). `LoadRenderPreset('Audio Only')` renders a 24-bit WAV (the "Wave" format itself can't
  be set by `SetCurrentRenderFormatAndCodec`). `SetRenderSettings` returns False for the whole dict when ONE key is
  rejected, so set keys one at a time to know which.
- **What the API can't see in Fairlight:** track and bus effects (EQ, Voice Isolation, De-Esser, dynamics, plugins),
  fader levels and fader automation. A green fader that snaps back when moved is reading volume automation (on
  last-call -14 dB on the SFX tracks, there before anyone noticed); a limiter added on Bus 1 never reached the
  render. Measure what Resolve's mix does instead: render it and `master.py fit` it against the stems.
- **Replace an edited render:** `media_pool_item replace_clip {clip_id, path}` swaps the media under every
  timeline use of that clip in place. Resolve keeps imported files open, so write edits to a new file name.
- **Start timecode:** a duplicate keeps the base's start (00:00:00:00 here). Record frames and marker frames are
  relative either way.
- **Studio:** external scripting (what the MCP uses) is Studio-only. On the free edition the MCP goes through the
  in-app bridge and Studio-only calls raise a modal that blocks later calls; none of the calls above are Studio-only.

## Gotchas from the MCP's source
- Auto-archive: destructive calls (duplicate, add_track, set_track_name, markers, set_transform, set_start_timecode,
  delete_clips, insert_*...) first copy the current timeline to the Archive bin as `<name>_archived_vNN`, once per
  run id; without an id a run closes after 90 s idle and the next call archives again. Tell the user the archived
  copies are safe to delete; never delete timelines yourself (`delete_timelines` is labelled catastrophic).
- An archive leaves the Archive bin as the current Media Pool folder: always import with `safe_import_media` and a
  `target_folder`.
- `append_to_timeline` does not create tracks, and on a track two clips may not overlap: Resolve silently drops the
  later one (`place.py plan` reports overlaps).
- A top-level `record_frame_mode` is ignored by `append_to_timeline`; the default (relative) is what `place.py` writes.
- No transitions, no speed changes, no razor, no moving or trimming a placed clip through the API. The pro edit
  never needs them: every move is rendered into its own clip.
- Titles and generators can't be placed on a chosen track/frame directly; the pro edit renders its own text
  (keyword pops, CTA) as alpha clips instead.
- `timeline_item` actions address items by `track_type/track_index/item_index` only; `bulk_set_item_properties`
  also accepts `timeline_item_id`.
- Pass real JSON booleans, never the string "false".

## The dynamic camera's calls (separate recordings; `dynamic-camera.md`)
Everything runs through `script_plugin run_inline` (`rs_content.py`, `rs_layout.py`), proven on abacus-test (Studio
21.1.1.10):
- `Timeline.DuplicateTimeline(name)` copies every track, the voice chain included; the new timeline then gets the
  layer on its own top track. The source Pro Edit is never touched.
- A content layer = the Pro Edit rendered with the camera, facecam and overlay CLIPS disabled
  (`TimelineItem.SetClipEnabled(False)`, re-enabled in a `finally`; the ids are written to a pending file first so an
  interrupted run is undone by the next). Track enables are not used for renders.
- `MediaPool.AppendToTimeline([{mediaPoolItem, startFrame, endFrame, recordFrame, trackIndex, mediaType: 1}])` with
  `recordFrame` = timeline start + offset; `endFrame` is EXCLUSIVE (measured live on 21.1.1.10). `rs_layout.py` still
  checks the first clip's length (and every clip after it) in case a build differs.
- **Track enables follow the CURRENT timeline:** `GetIsTrackEnabled` on a timeline object that isn't current returned
  the current timeline's values (Pro Edit v1 read "all off" while v3 was open; all on once v1 was current). Make the
  timeline current before reading or setting track enables (the rs_ scripts do).
- **`GetSourceStartFrame()` can read one frame low:** 2 of 33 webcam items on abacus (60 fps) reported src0 one less
  than placed, while the picture showed the right frame (v1 and v3 finals matched at lag 0). Fine for clips that start
  at frame 0 (every skill render); look at the picture before trusting it for a mid-source copy.
- **Proven live (abacus-test, 2026-11-01):** `rs_content.py` on Pro Edit v1 rendered a content layer pixel-identical
  to the one v3 was built on (134 clips disabled and re-enabled, 132 s); `rs_layout.py` built a test timeline whose
  "YouTube - 2160p" render was pixel-identical to Pro Edit v3's picture, to the byte (742,669,565 bytes).
- Keyframes: TimelineItem has none in the API; OFX parameters (the PiP effect) can't be set; keyframes written into a
  comp made with `AddFusionComp()` are ignored at render; `ImportFusionComp(<.comp>)` with BezierSpline keyframes is
  honoured (watch the comp time base: a new empty timeline took the project's 24 fps on a 60 fps source).
