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
| Name tracks | `timeline set_track_name {track_type, index, name, analysis_run_id}` | The key is `index`, not `track_index`. Names: PE Graphics, PE Overlays, PE SFX, PE Music, PE Riser. |
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
  so in the report.

## Facts measured on the build
- **Transforms:** `ZoomX/ZoomY` 1.0 = 100%, about the frame centre. `Pan` +right and `Tilt` +UP, in timeline
  pixels (a 1.15 zoom with Tilt -116 on a UHD timeline moved the eye line from 32% to 34% of the height).
- **Alpha:** ProRes 4444 written by ffmpeg with straight alpha composites correctly on an upper track with no
  clip-attribute changes (clean strokes, soft shadows, no halos).
- **Audio levels:** there is no working API for clip volume, fades or track levels - every level is baked into the
  WAV. WAVs are padded to whole frames so every requested frame range exists.
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
