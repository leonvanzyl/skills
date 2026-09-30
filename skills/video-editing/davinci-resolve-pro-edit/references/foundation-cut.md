# The foundation cut (when there is no clean cut yet)

The pro edit sits on a clean foundation cut: every thought said once, in its best take, without fillers, stumbles
or noises. This is the davinci-resolve-video-edit procedure; its script (`scripts/vedit.py`) and editorial rules
(`references/editorial-rules.md`) are vendored here. Skip this file entirely when the target is already a clean cut.

Work dir for the foundation cut: `WF="${VEDIT_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/video-edit}/<project>__<timeline>"`
(the same place davinci-resolve-video-edit uses, so its transcript cache is shared). `VE="$SKILL/scripts/vedit.py"`,
`CW` = the CrisperWhisper Python.

1. **Pre-flight (read-only).** `timeline probe_timeline_structure` (saved to a file). The timeline should be one
   talking track: V1 and A1 items at the same positions from the same media (`vedit prepare` warns otherwise -
   separate audio or multicam needs a different build: stop and ask). Sample a few items with
   `timeline_item get_transform / get_crop / get_voice_isolation_state` and `graph get_num_nodes` (1 = ungraded):
   a rebuild loses item-level state, so tell the user before building if anything is non-default.
   `timeline get_setting` on the original: note `useCustomSettings`, resolution, fps, start timecode.
2. **Prepare:** `"$CW" "$VE" prepare --work "$WF" --structure <saved probe>`.
3. **Hotwords, then transcribe:** `"$CW" "$VE" sample --work "$WF" --n 30`; collect names and jargon that come out
   misspelled (plus names from the project and file names); tell the user the list in one line and continue.
   `"$CW" "$VE" transcribe --work "$WF" --hotwords "A, B, ..."` (background, ~1.2 s per clip) -> `listing.txt`.
4. **Editorial pass:** read all of `listing.txt` like a paper edit and write `$WF/keep.json`
   (`{"decisions": {"29": "all", "50": [[null, 1], [7, null]], "384": [[null, "2.08s"], ["2.26s", null]]}, "notes": {...}}`;
   a clip not listed is dropped; ranges are word indices, inclusive; `"2.08s"` is a hand-placed time).
   Follow `references/editorial-rules.md`: last complete take, remove fillers/false starts/restarts/off-script
   talk, keep natural repetition and tone words, keep chronological order.
5. **Verify every cut:** `"$CW" "$VE" verify --work "$WF"` -> `edl.json`, `cut_report.txt`. Probe anything
   UNVERIFIED (`"$CW" "$VE" probe --work "$WF" --clip 384 --from 1.8 --to 2.5`) and fix `keep.json`.
6. **QA the whole cut:** `"$CW" "$VE" qa --work "$WF"` -> `qa.txt`. Resolve every flag, then read the full cut
   top to bottom as a script. Repeat 4-6 until clean.
7. **Build:** `"$CW" "$VE" clipinfos --work "$WF"` -> `media_pool create_timeline_from_clips {name: "<original> -
   Clean Cut v1", if_exists: "fail", clip_infos: <clip_infos.json>}` (one call; linked V1/A1, gap-free).
8. **Check the build:** `timeline detect_gaps_overlaps` (expect 0/0), `probe_timeline_structure` ->
   `"$CW" "$VE" check-build --work "$WF" --structure <file>` (a 1-frame source readback shift with the right length
   and position is a known Resolve quirk). If the original starts at 00:00:00:00, `timeline set_start_timecode
   00:00:00:00` (it archives the timeline - tell the user the duplicate is safe to delete). Add each entry of
   `markers.json` with `timeline_markers add`; `project_manager save`.
9. Tell the user in two lines what the clean cut removed (clips and duration before -> after), then continue with
   the pro edit on the new "Clean Cut" timeline. If the user wants to review the cut first, stop here and wait.
