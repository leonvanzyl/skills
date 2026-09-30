#!/bin/bash
# One-time setup for a folder of recordings.
#   bash <skill>/scripts/setup.sh <project_folder>
# - creates <project>/.venv (local, nothing system-wide; model weights come from the user caches)
# - for every video in the folder root creates <project>/work-<stem>/ with the scripts, the graphics engine,
#   fonts, the face model and a project.json (init_project.py)
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
PROJ="$(cd "${1:-.}" && pwd)"
command -v uv >/dev/null || { echo "ERROR: uv not found (https://docs.astral.sh/uv/)"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v node >/dev/null || { echo "ERROR: node (22+) not found"; exit 1; }
cd "$PROJ"
[ -d .venv ] || uv venv .venv --python 3.11
PY=.venv/Scripts/python.exe; [ -f "$PY" ] || PY=.venv/bin/python
if ! "$PY" -c "import faster_whisper, torchaudio, mediapipe, cv2, pyloudnorm, num2words" 2>/dev/null; then
  uv pip install --python "$PY" numpy scipy soundfile pyloudnorm faster-whisper opencv-python pillow mediapipe num2words \
    nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*" onnxruntime-gpu &
  # CUDA PyTorch on NVIDIA machines: wav2vec2 forced alignment runs ~13x faster on the GPU (word edges identical to CPU).
  # cu130 wheels need an NVIDIA driver >= 580; any failure falls back to the CPU build.
  if command -v nvidia-smi >/dev/null 2>&1; then
    ( uv pip install --python "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cu130       || uv pip install --python "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cpu ) &
  else
    uv pip install --python "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cpu &
  fi
  wait
fi
# an existing venv with CPU-only torch on an NVIDIA machine: swap in the CUDA build (same API, identical results)
if command -v nvidia-smi >/dev/null 2>&1 && ! "$PY" -c "import torch, sys; sys.exit(0 if torch.cuda.is_available() else 1)" 2>/dev/null; then
  uv pip install --python "$PY" --reinstall-package torch --reinstall-package torchaudio torch torchaudio     --index-url https://download.pytorch.org/whl/cu130 >/dev/null 2>&1 || true
  "$PY" -c "import torch; print('torch', torch.__version__, 'cuda:', torch.cuda.is_available())"
fi
# a CPU-only `onnxruntime` pulled in by another package shadows onnxruntime-gpu (same import name), so the CUDA provider
# never shows up. Remove it and reinstall the GPU build; matte_gpu.py then runs the matting model on CUDA (~12x faster).
if ! "$PY" -c "import onnxruntime as o, sys; sys.exit(0 if 'CUDAExecutionProvider' in o.get_available_providers() else 1)" 2>/dev/null; then
  uv pip uninstall --python "$PY" onnxruntime >/dev/null 2>&1 || true
  uv pip install --python "$PY" --reinstall onnxruntime-gpu >/dev/null 2>&1 || true
  "$PY" -c "import onnxruntime as o; print('onnxruntime providers:', o.get_available_providers())"
fi
shopt -s nullglob nocaseglob
n=0
for V in *.mov *.mp4 *.mkv *.m4v *.mxf; do
  STEM="${V%.*}"; W="work-$STEM"
  mkdir -p "$W/scripts" "$W/gfx/assets" "$W/fonts"
  cp "$SKILL"/scripts/*.py "$SKILL"/scripts/*.sh "$W/scripts/"
  cp "$SKILL"/assets/gfx/* "$W/gfx/"
  cp "$SKILL"/assets/fonts/*.ttf "$W/fonts/"; cp "$SKILL"/assets/fonts/*.ttf "$W/gfx/assets/"
  cp "$SKILL"/assets/models/* "$W/"
  (cd "$W" && "../$PY" scripts/init_project.py "../$V")
  n=$((n+1))
done
[ $n -gt 0 ] || { echo "ERROR: no video found in $PROJ"; exit 1; }
mkdir -p edit
echo "setup done: .venv + $n work folder(s)"
