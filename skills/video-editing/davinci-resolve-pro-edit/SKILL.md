---
name: davinci-resolve-pro-edit
description: Professionally edit a long-form YouTube recording (talking head, screencast, tutorial) in DaVinci Resolve end to end, with the create-video-shorts editing intelligence carried over to long form and assembled through the davinci-resolve MCP. Reuses or makes a clean foundation cut; gives the first 30-45 s a short-form hook (screen zooms with highlights, punch-ins, luxury-tech graphics with real source captures and motion blur, a split with a head pop-out, keyword pops, music that fades out after the hook, a riser); keeps the body restrained (zooms and highlights on what is discussed, captures of cited pages, community CTA cards, SFX, no music); builds a new Pro Edit timeline with every addition on its own track, plus chapters, an SRT and publishing copy. Use it whenever the user wants a long-form video or Resolve timeline professionally edited, polished or finished, or given zooms, graphics, B-roll, highlights, sound design or a hook, even without naming a skill. Not for shorts or a clean cut alone.
---

# DaVinci Resolve Pro Edit

You are the editor of a long-form YouTube video. The recording already carries the video; your job is to make it
feel professionally edited: an irresistible hook, then a calm, clear body where the viewer always sees exactly what
is being talked about. Everything is decided from the transcript and the frames, rendered in code (ffmpeg, Python,
HyperFrames), and assembled in Resolve through the davinci-resolve MCP on a new timeline, one named track per kind
of addition, so the user can adjust or remove anything.

**The quality contract is `references/editing-spec.md`. Read all of it before planning.** It carries the shorts
spec over to long form: the same graphics style, camera language, fact checking and sound design, with the hook /
body split. The rules the user cares most about:
- **Music plays under the hook only** and fades out over 2-3 s right after it. Never under the body.
- **The body is restrained**: zooms, highlights, real sources, CTA cards and SFX where they help - nothing over the top.
- **Nothing on the clean cut changes.** The pro edit is a duplicate of it with new tracks on top.
Where the user's request differs from the spec, the user wins.

First real project (Sonnet 5.5 vs Opus 5.5 vs Fable 5.1, 2026-09-30): an 11-minute clean cut, 4K60, OBS
recordings that switch between a full-frame camera and a screen with a webcam PiP. The test build in
`examples/` is what the scripts were proven on - including every fix in `references/lessons.md`.

## Requirements

| What | Notes |
|---|---|
| DaVinci Resolve Studio + the `davinci-resolve` MCP server | Community server [samuelgursky/davinci-resolve-mcp](https://github.com/samuelgursky/davinci-resolve-mcp). Load its tools with ToolSearch query `davinci resolve` (it may still be connecting at session start). Studio is needed for external scripting; see `references/resolve-assembly.md`. |
| CrisperWhisper env (transcription) | The same env as davinci-resolve-video-edit: `~/.venvs/crisperwhisper` or `VEDIT_VENV`, model `nyralabs/CrisperWhisper2.0_large` in the Hugging Face cache. Never modified by this skill. |
| Render env | `~/.venvs/pro-edit` or `PRO_EDIT_VENV` (Python 3.11: numpy, scipy, soundfile, pyloudnorm, opencv, pillow, mediapipe, onnxruntime-gpu for the split matte). `setup.sh` creates it with uv and adds what an older env lacks. |
| ffmpeg, Node 22+, uv | ffmpeg with NVENC is used when present. HyperFrames runs through `npx --yes hyperframes`. |
| NVIDIA GPU | Recommended (transcription, NVENC, the split matte). Everything has a CPU fallback. |

Missing pieces: `references/setup-and-troubleshooting.md` (ask before the ~7 GB CrisperWhisper install).

## Conventions
Shell variables don't persist between Bash calls, so start each command with:
```bash
SKILL="<this skill's folder>"
VENV="${VEDIT_VENV:-$HOME/.venvs/crisperwhisper}"; CW="$VENV/Scripts/python.exe"; [ -e "$CW" ] || CW="$VENV/bin/python"
RV="${PRO_EDIT_VENV:-$HOME/.venvs/pro-edit}"; PY="$RV/Scripts/python.exe"; [ -e "$PY" ] || PY="$RV/bin/python"
W="${PRO_EDIT_WORK_ROOT:-${LOCALAPPDATA:-$HOME/.cache}/video-pro-edit}/<project>__<timeline>"   # short, no spaces
M="<folder of the source media>/pro-edit-media"     # renders Resolve links to: next to the sources, never under AppData
```
Every script runs with `W` as the working directory (`cd "$W"`). `W` holds caches and intermediates; `M` holds the
finished media, `captions.srt`, `PUBLISH.md` and `report.md`.

## Workflow
Commands for every step are in `references/pipeline.md`.

1. **Connect and choose the timeline** (read-only). `project_manager get_current`, `timeline get_current`,
   `timeline list`. Default target = the current timeline. If a "<name> - Clean Cut vN" exists for it, that is the
   base; if the current timeline is raw, make the foundation cut first (`references/foundation-cut.md`).
   If `resolve_control get_version` reports an MCP update, mention it once.
2. **Set up and map the programme** (~5-10 min, mostly background). `setup.sh "$W" "$M"`, then on the clean cut:
   `probe_timeline_structure` -> `vedit.py prepare` + `transcribe` (CrisperWhisper, hotwords as in the foundation
   cut) -> `program.py` (every V1 item and word on programme time, the voice as it plays) -> `scenes.py` (camera vs
   screen, the PiP window per file). LOOK at `scenes.png`. Read `transcript.txt` like a paper edit.
3. **Research, in parallel** (subagent): fact-check every figure against 2+ sources; capture the pages the speaker
   cites but the recording doesn't show, official logos, pricing and docs as 2x PNGs into `W/captures/`.
4. **Plan once** into `W/edit_plan.json` (`examples/edit_plan_example.json`): hook_end, music style and mood,
   the beats (zoom, punch, gfx, words, cta) with word-cued times, chapters, caption fixes, the publishing copy.
   Use `look.py` to see the programme at any time with a source-pixel grid, and `--zoom k,fx,fy` to frame a zoom
   clear of the webcam. Check the plan against the spec's density rules before rendering anything.
5. **Render, fanning out:**
   - zooms, keyword pops, CTA cards and the audio: preview a few zoom frames first (`zoom.py --preview`, seconds),
     then `bash scripts/render_beats.sh` in the background renders every zoom / words / cta beat of the plan in
     parallel (one process per beat) and runs `audio.py` after them - then listen to the hook in `mix_preview.wav`;
   - graphics: one subagent per 1-3 gfx beats, following `references/graphics.md` and `examples/gfx_example.py`:
     assets -> `build_gfx.py` -> `render_gfx.sh draft` -> `draftsheet.py` (LOOK, fix) -> `render_gfx.sh full`
     (lossless PNG capture, one Chrome per worker, throttled machine-wide so any number of subagents can call it)
     -> `compose.py` (split beats: `--matte` first, on the GPU; several beats with `--jobs`).
   Check every render: previews and sheets before full renders, one full-resolution frame of every split
   (`compose.py <id> --preview t` seeks straight to it).
6. **Assemble in Resolve** (`references/resolve-assembly.md`): duplicate the clean cut as
   "<base> - Pro Edit vN", count its tracks, `place.py plan`, add and name the PE tracks, import `M` into a bin,
   `place.py ids`, one `append_to_timeline`, punch-ins with `bulk_set_item_properties`, markers, save. Then
   `place.py verify` against a fresh structure probe and capture a few frames with `timeline_frame capture`.
7. **Publish and report:** `publish.py` (`captions.srt`, `PUBLISH.md` with chapters and the community links),
   then `report.md` (spec section 9). Tell the user: the timeline name, what was added and where, the archived
   duplicates the MCP made (safe to delete - never delete them yourself), and to normalise to -14 LUFS on delivery.
8. **Edits are incremental:** change the plan, re-render only the touched beats, re-import those files and replace
   their clips (`references/pipeline.md` section 8). Fold the user's taste into `references/lessons.md`.

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Colour at the cut:** zoom renders work on the source's own YUV planes, so a frame at rest is bit-identical to
  V1. Never route footage through ffmpeg's default RGB conversion (bt601) - the cut into V2 would shift colour.
- **Windows pipes:** raw 4K video through a Python-buffered pipe crawls; `media.py`'s unbuffered 64 MB pipes move
  it at GB/s. Never add `bufsize=` to a frame pipe (the shorts skill lost 48 ms a frame to a 100 MB buffer).
- **The user's timeline is not pristine:** duplicate it, never rebuild it; skip titles/transitions in the
  programme map; never plan a beat across a transition.
- **Frame the zoom around the webcam:** the PiP is held still; keep targets out of `look.py`'s red box.
- **Resolve's API can't set clip volume or keyframes reliably:** levels are baked into the audio files, motion is
  rendered, punch-ins are static transforms.

## Files
- `scripts/`: the pipeline (copied into `W/scripts` by `setup.sh`; per-project values live in `W/project.json`).
  `vedit.py` (vendored from davinci-resolve-video-edit), `program.py`, `scenes.py`, `look.py`, `zoom.py`,
  `overlay.py`, `assets.py`, `build_gfx*.py`, `render_gfx.sh`, `draftsheet.py`, `compose.py`, `matte_gpu.py`,
  `audio.py`, `music.py` (from create-video-shorts), `render_beats.sh`, `place.py`, `publish.py`, `media.py`,
  `config.py`, `faces.py`.
- `assets/`: the 16:9 graphics engine + GSAP, Poppins and Instrument Serif, the face models.
- `examples/`: the real test plan, its graphics config and its report.
- `references/`: `editing-spec.md` (the contract), `pipeline.md` (commands), `resolve-assembly.md` (MCP calls and
  gotchas), `graphics.md` (engine API), `foundation-cut.md` + `editorial-rules.md` (the clean cut),
  `setup-and-troubleshooting.md`, `lessons.md`.
