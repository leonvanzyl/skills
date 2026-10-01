#!/bin/bash
# Stage 3 in one call: forced alignment -> the cut -> the proof (voice re-transcription + eye sheets), in parallel.
#   bash scripts/cut.sh s1 [s2 ...]        (shorts to verify; all in shorts.json if none given)
# Iterate freely: align_lines.py only re-transcribes, cut2.py takes seconds.
set -u
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
mkdir -p logs
SKS="$*"; [ -n "$SKS" ] || SKS=$("$PY" -c "import json; print(' '.join(json.load(open('shorts.json'))))")
t0=$(date +%s)
"$PY" scripts/align_lines.py > logs/align_lines.log 2>&1 || { echo "align_lines failed:"; tail -30 logs/align_lines.log; exit 1; }
grep -E "^ASR:|match=" logs/align_lines.log
"$PY" scripts/cut2.py > logs/cut2.log 2>&1 || { echo "cut2 failed:"; tail -20 logs/cut2.log; exit 1; }
grep -E "^==|RUN" logs/cut2.log
"$PY" scripts/verify_voice.py $SKS > logs/verify_voice.log 2>&1 &
VV=$!
for sk in $SKS; do "$PY" scripts/eyesheet.py $sk > logs/eyesheet_$sk.log 2>&1 & done
wait
echo "== voice proof (must read word-perfect; joins <= 150 ms)"; grep -vE "^\[|WARNING|INFO|^$" logs/verify_voice.log
for sk in $SKS; do echo "== eyes: $(tail -1 logs/eyesheet_$sk.log) (LOOK at it)"; done
echo "cut stage done in $(( $(date +%s) - t0 ))s"
