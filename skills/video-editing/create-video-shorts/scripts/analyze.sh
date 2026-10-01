#!/bin/bash
# Stage 1 in one call: ingest + transcription + camera detection + gaze + zoom scan, each starting the moment its input
# exists (ingest.py writes ingest_audio.done when the audio is ready and ingest.done when the proxy is). Run inside W:
#   bash scripts/analyze.sh
# Logs go to logs/<step>.log; the summary the plan needs is printed at the end. Then LOOK at detect_camera.png.
set -u
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
mkdir -p logs
t0=$(date +%s)
since() { echo "[$(( $(date +%s) - t0 ))s] $*"; }
"$PY" scripts/ingest.py > logs/ingest.log 2>&1 &
ING=$!
until [ -f ingest_audio.done ]; do
  kill -0 $ING 2>/dev/null || { echo "ingest failed:"; cat logs/ingest.log; exit 1; }; sleep 0.5
done
since "audio ready -> transcribing (GPU Whisper, batched)"
"$PY" scripts/transcribe.py clean16.wav transcript_full.json > logs/transcribe.log 2>&1 &
TR=$!
until [ -f ingest.done ]; do
  kill -0 $ING 2>/dev/null || { echo "ingest failed:"; cat logs/ingest.log; exit 1; }; sleep 0.5
done
wait $ING
since "proxy ready -> camera detection"
"$PY" scripts/detect_camera.py > logs/detect_camera.log 2>&1 || { echo "detect_camera failed:"; cat logs/detect_camera.log; }
since "camera window set -> gaze + zoom scan (CPU, parallel)"
"$PY" scripts/gaze.py > logs/gaze.log 2>&1 &
GZ=$!
"$PY" scripts/zoomscan.py > logs/zoomscan.log 2>&1 &
ZS=$!
wait $TR; since "transcript done"
wait $GZ $ZS; since "gaze + zoom scan done"
echo
echo "== ingest";        grep -E "sync|ingest done" logs/ingest.log
echo "== camera";        cat logs/detect_camera.log
echo "== gaze";          grep -vE "^\[|WARNING|INFO|^$|absl|TensorFlow|gl_context|inference_feedback|landmark_projection" logs/gaze.log | tail -8
echo "== zoom scan";     grep -E "framing events|tracking lost" logs/zoomscan.log | cut -c1-900
echo "== transcript";    "$PY" - <<'EOF'
import json; t = json.load(open('transcript_full.json'))
print(len(t), 'segments,', sum(len(s['words']) for s in t), 'words, last end', round(t[-1]['end'], 1), 's -> transcript_full.json')
EOF
since "analysis complete. LOOK at detect_camera.png (red = window, green = safe), then plan shorts.json"
