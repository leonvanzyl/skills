---
name: video-edit
description: Cut a DaVinci Resolve talking-head / screencast / tutorial timeline into a clean, well-paced foundation edit - removing bad takes, retakes, false starts, stumbles, "um"/"uh" fillers, lip smacks and noises - using word-level CrisperWhisper 2.0 transcription on the local GPU and the davinci-resolve MCP. Use this whenever the user wants to edit, clean up, tighten or rough-cut a Resolve timeline, remove bad takes/ums/retakes/filler words, "cut this video like a professional editor", or prepare a YouTube recording for B-roll - even if they don't say "skill" or name the tools. Also use it when they ask how their previous clean-cut edits were made. Not for adding B-roll, captions, music, transitions or motion graphics.
---

# Video Edit: clean foundation cut in DaVinci Resolve

Turn a raw timeline (usually already silence-cut by the user) into a clean foundation edit: every thought said
once, in its best take, without fillers, stumbles or noises. The user adds B-roll, SFX, transitions and lower
thirds afterwards, so don't do any of that. The original timeline is never modified; the result is a new
timeline named `<original> - Clean Cut v1`.

First real project (Jev / TypeSafe AI video, 2026-09-26): 509 clips, 31:04 -> 214 clips, 17:10. The user
called it "phenomenal". The process below is what produced that result, including the fixes for everything that went
wrong along the way.

## What's already set up on this machine

| Thing | Where |
|---|---|
| Helper script | `C:\Users\leon\.claude\skills\video-edit\scripts\vedit.py` |
| Python to run it (CrisperWhisper env: torch cu128, transformers, crisperwhisper) | `C:\Users\leon\.venvs\crisperwhisper\Scripts\python.exe` |
| Model `nyralabs/CrisperWhisper2.0_large` (2.9 GB) | `C:\Users\leon\.cache\huggingface\hub\models--nyralabs--CrisperWhisper2.0_large` |
| GPU | RTX 5090 (32 GB) |
| ffmpeg / ffprobe | on PATH (Chocolatey) |
| Resolve control | `davinci-resolve` MCP server - load its tools with ToolSearch query `davinci resolve` |

Never download or install another copy of the model or the environment - `vedit.py` runs offline against the
cache. If something is missing, see `references/setup-and-troubleshooting.md` (rebuild steps are there).

Use the CrisperWhisper model, not Whisper and not Resolve's own transcription: Whisper cleans speech up (drops
ums, merges retakes, hallucinates "Thank you for watching" on short clips) and Resolve's transcript can't be read
back through the scripting API with word timings. CrisperWhisper transcribes verbatim - `[UM]`, `[UH]`,
`[lipsmack]`, `[breath]`, `[throatclearing]`, cut-off words like `bi-` - with ~30-40 ms word timing. That verbatim
detail is what makes a clean edit possible.

## Conventions

Shell variables don't persist between Bash tool calls, so start each command with these assignments:

```bash
PY=/c/Users/leon/.venvs/crisperwhisper/Scripts/python.exe
VE=/c/Users/leon/.claude/skills/video-edit/scripts/vedit.py
WORK=/c/Users/leon/AppData/Local/video-edit/<project>__<timeline>   # e.g. jev-ai__YTHD60 (no spaces)
```

The work dir is persistent on purpose: transcripts are cached there (`segments.json`, keyed by each clip's media
and source range), so re-running or revising an edit later only transcribes clips that changed. Keep the path
short - deep paths broke `uv` on Windows.

## Workflow

### 1. Connect and pick the timeline
- Load the Resolve tools (ToolSearch `davinci resolve`). `resolve_control runtime_mode` may be undeterminable;
  `Get-Process Resolve` tells you if it's running and which project is open (window title).
- `project_manager get_current`, `timeline get_current`, `timeline list`. Default target = the current timeline;
  ask only if it's ambiguous.
- If `resolve_control get_version` reports an MCP update, mention it once; don't apply it.

### 2. Pre-flight checks (read-only)
- `timeline probe_timeline_structure` - output is large and gets saved to a tool-results file; note its path.
- Check the timeline is a single talking track: items on V1 and A1 at the same positions from the same media
  (`vedit prepare` verifies this and warns otherwise - separate audio or multicam needs a different build, stop and ask).
- Rebuilding from source loses anything applied to timeline items, so sample a few items:
  `timeline_item get_transform / get_crop / get_voice_isolation_state / get_linked_items`, `graph get_num_nodes`
  (1 node = ungraded). If anything is non-default, tell the user before building.
- `timeline get_setting` (no name) on the original: note `useCustomSettings`, resolution, fps, and `start_timecode`.

### 3. Prepare audio (seconds)
```bash
"$PY" "$VE" prepare --work "$WORK" --structure "<path to the saved probe_timeline_structure output>"
```
Extracts 16 kHz mono WAVs of each source file (sources are only read) and writes `items.json`. (A short
timeline's structure may come back inline instead of as a saved file - write it to `$WORK/structure_raw.json` first.)

### 4. Hotwords, then transcribe (≈1.2 s per clip - run in the background)
- `"$PY" "$VE" sample --work "$WORK" --n 30` - a quick pass with no hotwords over clips spread across the
  timeline. Find product/brand/people names and jargon that come out misspelled, plus names from the project,
  folder and file names. Tell the user the list in one line and continue unless they correct it.
- `"$PY" "$VE" transcribe --work "$WORK" --hotwords "Name1, Name2, ..."` (background; resumable; skips clips
  already in `segments.json`). Produces `listing.txt`:
  `index  timeline-time  duration  loudness | 0:word 1:word ...` - word indices are what decisions refer to.
- Hotwords can over-correct ("Cool" -> "Skool", "Claude Code" -> "Claude Codex"). Harmless for cutting.

### 5. Editorial pass - the part that needs judgement
Read the whole `listing.txt` (in chunks of ~170 lines) like an editor reading a paper edit, then write
`$WORK/keep.json`. Read `references/editorial-rules.md` first - it has the rules and worked examples.

```json
{"decisions": {
   "29": "all",
   "50": [[null, 1], [7, null]],
   "57": [[11, null]],
   "384": [[null, "2.08s"], ["2.26s", null]]
 },
 "notes": {"29": "last complete take of the cold open", "57": "spliced: '...follow along, you can' + 'download ...'"}}
```
- Key = clip index; a clip not listed is dropped. `"all"` keeps the clip as the user cut it.
- A range `[from, to]` uses word indices (inclusive); `null` = the clip's own edge; `"2.08s"` = a hand-placed time
  (seconds from the clip start) - only after probing.
- Several ranges in one clip remove stumbles inside it ("so what happened, so what happened is" -> `[[3, null]]`).
- Keep clip order chronological (screen recordings change between takes).

### 6. Verify every cut (a few minutes)
```bash
"$PY" "$VE" verify --work "$WORK"
```
For each cut inside a clip it tries the middle of each nearby pause (then frame by frame if the words are run
together), re-transcribes the kept side at the exact frame, and accepts a point only if it starts/ends with the
expected word - no filler, no extra word, and for repeated phrases the removed copy really is on the other side.
Writes `edl.json` and `cut_report.txt` (every candidate tried and why it failed). On the Jev project it verified
55/55 cuts in ~3 min. For anything `UNVERIFIED`, run `probe` (step 7) and either move the decision to a different
word boundary or hand-place a time.

Why this exists: cutting on word timestamps alone went wrong on 7 of ~60 cuts in the first project -
timestamps off by 0.3-0.5 s around fillers, the "quietest point" being the silent closure inside a word
(the "t" in "n8n"), and words run together with no pause at all. Don't skip verification.

### 7. QA the whole cut (a few minutes) and fix
```bash
"$PY" "$VE" qa --work "$WORK"                       # -> qa.txt, flags at the top
"$PY" "$VE" probe --work "$WORK" --clip 384 --from 1.8 --to 2.5   # when something needs a closer look
```
- Resolve every flag: filler/noise tags, cut-off words, the same word on both sides of a cut, stutters.
  Some repeats are natural speech ("zero to one, one meaning...", "call Jev. Jev will...") - leave those.
- Then read the full cut in `qa.txt` top to bottom as a script: does every sentence make sense, does each
  section flow, did any cut eat a word?
- A clipped word at the end of a range can be "completed" by the model ("a l-" read as "a little bit"), so a
  phrase that looks duplicated across a cut may be an artifact. `probe` prints END/START transcripts at 40 ms
  steps plus a loudness trace - trust the loudness trace and the step where the transcript changes.
- Edit `keep.json`, re-run `verify` and `qa` until clean.

### 8. Build the new timeline in Resolve
```bash
"$PY" "$VE" clipinfos --work "$WORK"    # -> clip_infos.json + markers.json
```
- `media_pool create_timeline_from_clips` with `{"name": "<original> - Clean Cut v1", "if_exists": "fail",
  "clip_infos": <contents of clip_infos.json>}` - pass the whole list in one call (214 clips worked). This gives
  linked video+audio on V1/A1, gap-free. If the name exists, use v2, v3...
- New timelines use the project settings; if the original had custom settings that differ, tell the user.

### 9. Verify the build
- `timeline detect_gaps_overlaps` -> expect 0/0.
- `timeline probe_timeline_structure` on the new timeline (saved to file) -> `"$PY" "$VE" check-build --work "$WORK" --structure <file>`.
  Expect every item exact; a 1-frame source readback shift with correct length/position is a known Resolve quirk.
- `timeline_item get_linked_items` on a sample item -> linked.
- If the original starts at 00:00:00:00 and the new one at 01:00:00:00, `timeline set_start_timecode 00:00:00:00`.
  This triggers the MCP's auto-archive and leaves a `<name>_archived_v01` duplicate - tell the user it's safe to
  delete; don't delete timelines yourself.
- Add each marker from `markers.json` with `timeline_markers add` (yellow "Listen:" markers at micro-cuts,
  hand-placed cuts and mid-sentence splices) so the user can review the risky edits in a minute.
- `project_manager save`.
- Don't use `timeline_frame capture` for checks - it changes project render settings that can't all be restored.

### 10. Report
Keep it short and plain:
- New timeline name, clip count and duration before -> after (% removed); original untouched.
- What was removed (retakes, false starts, fillers, noises, stumbles inside sentences - with 2-3 real examples).
- How it was checked (every kept piece re-transcribed; gaps/overlaps; exact placement).
- The review markers and which one you're least sure about.
- Caveats: the archived duplicate timeline; Fairlight track effects on the original (EQ/compression) can't be
  read or copied by the API - re-apply them if they existed.
- Ask how the pacing feels; fold their feedback into `references/editorial-rules.md` (this skill should get
  better with every video).

## Reference files
- `references/editorial-rules.md` - what to cut and keep, with worked examples. Read before step 5.
- `references/resolve-mcp.md` - the MCP calls used, their parameters and gotchas.
- `references/setup-and-troubleshooting.md` - environment details, rebuild steps, model quirks, why not Whisper/Resolve.
