# DaVinci Resolve MCP: calls used and gotchas

Server: community [samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp) (not
built into Resolve - install it with the steps in its README), talking to Resolve through its scripting API.
Tested with Resolve Studio 21.x. Tools are named `mcp__davinci-resolve__<tool>`; each takes `action` + `params`.
Load them with ToolSearch query `davinci resolve` (the server may still be connecting at session start -
ToolSearch waits for it).

## Calls used by this skill

| Purpose | Call |
|---|---|
| Is Resolve running / which project | Windows: `Get-Process Resolve` (PowerShell) - window title shows the project. macOS/Linux: `pgrep -l Resolve`. `resolve_control runtime_mode` often returns "undeterminable". |
| Versions | `resolve_control get_version` (mentions MCP updates - tell the user once, don't apply) |
| Current project / timeline | `project_manager get_current`, `timeline get_current`, `timeline list` |
| Timeline settings | `timeline get_setting` (no name = all). `useCustomSettings`, `timelineResolutionWidth/Height`, `timelineFrameRate` |
| Full structure | `timeline probe_timeline_structure` -> huge; the harness saves it to a tool-results file and returns the path |
| Item state checks | `timeline_item get_transform / get_crop / get_audio / get_voice_isolation_state / get_linked_items` with `{track_type, track_index, item_index}`; `graph get_num_nodes` with `{source:"item", track_type, track_index, item_index}` |
| Build | `media_pool create_timeline_from_clips` `{name, if_exists:"fail", clip_infos:[{media_pool_item_id, start_frame, end_frame, record_frame}]}` |
| Check | `timeline detect_gaps_overlaps`, then `probe_timeline_structure` + `vedit check-build` |
| Start timecode | `timeline set_start_timecode {timecode:"00:00:00:00"}` (acts on the current timeline) |
| Markers | `timeline_markers add {frame, color, name, note, duration}` - frame is relative to the timeline start (0 = first frame) |
| Save | `project_manager save` |
| Knowledge base | `knowledge search / get` (e.g. `editorial-decision-guide`, `media-analysis-guide`) - no Resolve connection needed |
| API quirks | `resolve_control api_truth {query}` |

## Frame and range rules
- `clip_infos` `end_frame` is **exclusive**: duration = end - start. Next record_frame = previous + duration.
- `start_frame`/`end_frame` are **source** frames in the media's own frame rate (read `source_fps` per item; a WAV
  takes the project rate at import). This skill assumes source fps == timeline fps and `vedit prepare` warns if not.
- Timeline item `start`/`end` from `probe_timeline_structure` are record frames including the timeline start
  offset (e.g. 216000 = 01:00:00:00 at 60 fps). Marker frames are relative (0-based).
- New timelines use the project settings and start at 01:00:00:00 by default.

## Gotchas seen in practice
- **Auto-archive**: mutating calls the MCP considers destructive (e.g. `set_start_timecode`) first archive the
  timeline, leaving `<name>_archived_v01`. `timeline_markers add` does not archive. Tell the user about the
  duplicate; deleting timelines is theirs to decide (`delete_timelines` is labelled catastrophic).
- **Readback quirk**: after building, one item in 214 read back with source in/out 1 frame earlier but correct
  length and position. Treat +-1 source-frame shifts with correct length as reporting noise.
- **Item-level state is lost on rebuild**: transforms, crops, grades, voice isolation, clip volume live on the
  timeline items and don't come with a rebuild from the media pool. Check before building.
- **Fairlight track effects can't be read** through the API; if the user had EQ/compression on the original
  audio track they must re-apply it.
- **Separate audio** (external recorder synced to camera): `create_timeline_from_clips` would bring the camera's
  embedded audio. Use `timeline create_variant_from_ranges` with separate `track_type:"audio"` ranges instead
  (unlinked) - and confirm with the user first.
- **Don't use `timeline_frame capture`** (quality "frame"/"preview") for routine checks: it renders through the
  Deliver page and changes project render settings (TargetDir, CustomName, mark range aren't restorable).
- **Large results**: `probe_timeline_structure` on 500+ items is ~500 KB - always parse from the saved file.
- **Free vs Studio**: external scripting is Studio-only. On the free edition the server goes through Resolve's
  in-app bridge (Workspace > Scripts > resolve_bridge), and Studio-only calls raise a modal that blocks later
  calls until a human dismisses it.
- **Booleans**: server versions before 4.8.20 treated boolean params sent as the string "false" as true. Pass
  real JSON booleans, never strings.
