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
  uv pip install --python "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cpu &
  wait
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
