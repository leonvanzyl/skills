# Setup and troubleshooting

## Environments
Two Python environments, on purpose: transcription needs CUDA PyTorch and the CrisperWhisper model, rendering needs
OpenCV and MediaPipe. Installing one into the other risks breaking both.

**CrisperWhisper (transcription)** - shared with davinci-resolve-video-edit. `~/.venvs/crisperwhisper` or
`VEDIT_VENV`; interpreter `Scripts/python.exe` (Windows) or `bin/python`. Check:
```bash
"$CW" -c "import torch, crisperwhisper; from huggingface_hub import try_to_load_from_cache as c; print('cuda:', torch.cuda.is_available(), '| model cached:', isinstance(c('nyralabs/CrisperWhisper2.0_large', 'config.json'), str))"
```
If it's missing, ask the user first (about 7 GB with CUDA PyTorch and the model), then:
```bash
VENV="${VEDIT_VENV:-$HOME/.venvs/crisperwhisper}"; mkdir -p "$(dirname "$VENV")"; uv venv "$VENV" --python 3.13
CW="$VENV/Scripts/python.exe"; [ -e "$CW" ] || CW="$VENV/bin/python"
uv pip install -p "$CW" torch torchaudio --index-url https://download.pytorch.org/whl/cu128   # no NVIDIA GPU: drop the index URL
uv pip install -p "$CW" "crisperwhisper[transformers]"
HF_HUB_OFFLINE=0 "$CW" -c "from huggingface_hub import snapshot_download; snapshot_download('nyralabs/CrisperWhisper2.0_large')"
```
The CrisperWhisper 2.0 weights are under the nyra health Non-Commercial Research License (the code is MIT). Tell the
user once before downloading; a monetised video may count as commercial use. If the model is already cached, that
decision was made - don't raise it again. `vedit.py` runs offline against the cache.

**Render env** - `~/.venvs/pro-edit` or `PRO_EDIT_VENV`, Python 3.11 (MediaPipe wheels), created by `setup.sh`
with uv: numpy, scipy, soundfile, pyloudnorm, opencv-python, pillow, mediapipe, plus onnxruntime-gpu with the CUDA
12 runtime wheels (nvidia-cublas-cu12, nvidia-cudnn-cu12) for the split matte on the GPU. An existing env gets
the extra packages the next time `setup.sh` runs. If `onnxruntime.get_available_providers()` lacks
`CUDAExecutionProvider`, a CPU-only `onnxruntime` wheel pulled in by another package is shadowing the GPU build;
`setup.sh` uninstalls it and reinstalls onnxruntime-gpu.

**Also needed:** ffmpeg on PATH (with `h264_nvenc` when there is an NVIDIA GPU - `media.has_nvenc()` tests it;
`PRO_EDIT_X264=1` forces software), Node 22+ for `npx --yes hyperframes` (the first run downloads the CLI; built
and tested with 0.8.96), uv.

## Work and media folders
- `W` (work dir) holds caches, intermediates, drafts and previews. Default under `%LOCALAPPDATA%\video-pro-edit`
  (Windows) or `~/.cache/video-pro-edit`; `PRO_EDIT_WORK_ROOT` moves it. Keep the path short (deep paths break uv).
- `M` (media dir) holds everything Resolve links to. Put it next to the recording's source files. Never under
  AppData: a packaged app (like the Claude desktop app) can virtualise writes there, so the files exist for the
  scripts but not for Resolve.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `vedit prepare`: TypeError on `source_start` | The timeline has titles/generators/transitions on V1: this skill's `vedit.py` skips them (the stock one crashes). Make sure the work dir has this skill's copy. |
| `prepare` warns "record length != source length" / "slipped audio" next to a clip | A transition the editor added: its handle is counted in the video source range. Expected; `program.py` maps it; keep beats off the transition. |
| `source_map` / "the beat overlaps V1 item ... title/generator/transition" | Move the beat's t0/t1 off the transition (look at `transcript.txt` around it). |
| `scenes.py`: a PiP window taller than the screen | The edge scan ran off; the consensus window from the other files is used when the face is inside it (printed). If every file fails, set `files.<path>.pip` in `scenes.json` by hand from a `look.py` frame. |
| Renders crawl at ~4 fps on Windows | Something bypassed `media.reader_proc/writer_proc` (64 MB pipes). Windows' default 4 KB pipe caps raw 4K video at ~60 MB/s. |
| A colour shift at the cut into a zoom or graphic | Footage went through ffmpeg's default RGB conversion (bt601). Zooms must use `decode(..., yuv=True)`; RGB paths must use `media.dec_vf()` / `enc_args()`. |
| `matte_gpu.py` says "CPU fallback" | onnxruntime-gpu is missing or shadowed (see Render env), or `~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx` isn't cached yet (one CLI run caches it). The fallback is the HyperFrames CLI on the CPU (~2-3 fps); the GPU path does a 300-frame beat in seconds. |
| A full render seems stuck at ~15 fps capture, or 100 Chromes appear | `render_gfx.sh` exports `PRODUCER_ENABLE_BROWSER_POOL=false` and throttles with `RENDER_SLOTS` x `HF_WORKERS`; a bare `npx hyperframes render` from a subagent does neither. Always go through the script. |
| The split's pop-out shows a bit of the background next to the hair | The salient-object matte grabbed an object touching the hair (a guitar headstock on the test). Pick another beat for the split, or shift the hair line (`HAIR_Y` in `compose.py`); a person-segmentation model would fix it but isn't bundled. |
| HyperFrames render fails | Read `gfx/out_hi/<id>.log` or `gfx/draft/<id>.log`; the hyperframes-cli skill covers `lint`, `validate` and `doctor`. |
| Resolve drops an appended clip | Two clips overlapped on one track (Resolve keeps the earlier). `place.py plan` lists overlaps as PROBLEMs - fix the plan. |
| A marker doesn't appear | Its frame already had a marker. Use `place.py ids --existing-markers`. |
| An edited render doesn't show in Resolve | Resolve holds the old file open; render with `--tag v2` and `media_pool_item replace_clip`. |
| `timeline_frame capture` changed the render target | Expected - it renders one frame through Deliver. Tell the user to re-check the Deliver page before their final render. |
