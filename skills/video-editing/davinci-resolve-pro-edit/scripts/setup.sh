#!/bin/bash
# One-time setup of a work dir for one timeline.
#   bash <skill>/scripts/setup.sh <work_dir> <media_dir>
# - makes sure the render env exists (PRO_EDIT_VENV, default ~/.venvs/pro-edit: numpy/scipy/opencv/mediapipe/pyloudnorm,
#   nothing system-wide). Transcription uses the separate CrisperWhisper env (VEDIT_VENV) and is never touched here.
# - copies the scripts, the graphics engine, fonts and face models into the work dir, and writes project.json
# - media_dir is where finished renders go; Resolve links to them, so put it next to the project's source media
set -e
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
W="$1"; M="$2"
[ -n "$W" ] && [ -n "$M" ] || { echo "usage: setup.sh <work_dir> <media_dir>"; exit 1; }
command -v uv >/dev/null || { echo "ERROR: uv not found (https://docs.astral.sh/uv/)"; exit 1; }
command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg not found"; exit 1; }
command -v node >/dev/null || { echo "ERROR: node (22+) not found"; exit 1; }
VENV="${PRO_EDIT_VENV:-$HOME/.venvs/pro-edit}"
PY="$VENV/Scripts/python.exe"; [ -e "$PY" ] || PY="$VENV/bin/python"
if [ ! -e "$PY" ]; then mkdir -p "$(dirname "$VENV")"; uv venv "$VENV" --python 3.11; PY="$VENV/Scripts/python.exe"; [ -e "$PY" ] || PY="$VENV/bin/python"; fi
if ! "$PY" -c "import numpy, scipy, soundfile, pyloudnorm, cv2, PIL, mediapipe, onnxruntime" 2>/dev/null; then
  uv pip install --python "$PY" numpy scipy soundfile pyloudnorm opencv-python pillow mediapipe \
    onnxruntime-gpu nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"      # the split matte on the GPU (matte_gpu.py)
fi
# a CPU-only `onnxruntime` pulled in by another package shadows onnxruntime-gpu (same import name): the CUDA provider
# never shows up and the matte falls back to the CPU CLI. Remove it and reinstall the GPU build.
if ! "$PY" -c "import onnxruntime as o, sys; sys.exit(0 if 'CUDAExecutionProvider' in o.get_available_providers() else 1)" 2>/dev/null; then
  uv pip uninstall --python "$PY" onnxruntime >/dev/null 2>&1 || true
  uv pip install --python "$PY" --reinstall onnxruntime-gpu >/dev/null 2>&1 || true
  "$PY" -c "import onnxruntime as o; print('onnxruntime providers:', o.get_available_providers())"
fi
mkdir -p "$W/scripts" "$W/gfx/assets" "$W/fonts" "$W/models" "$M"
cp "$SKILL"/scripts/*.py "$SKILL"/scripts/*.sh "$W/scripts/"
cp "$SKILL"/assets/gfx/* "$W/gfx/"
cp "$SKILL"/assets/fonts/*.ttf "$W/fonts/"; cp "$SKILL"/assets/fonts/*.ttf "$W/gfx/assets/"
cp "$SKILL"/assets/models/* "$W/models/"
M_ABS="$(cd "$M" && (pwd -W 2>/dev/null || pwd))"
(cd "$W" && "$PY" - "$M_ABS" <<'PYEOF'
import json, os, sys
p = 'project.json'
c = json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}
c['media_dir'] = sys.argv[1].replace('\\', '/')
json.dump(c, open(p, 'w', encoding='utf-8'), indent=1)
PYEOF
)
echo "setup done: work dir $W | media dir $M_ABS | render python $PY"
