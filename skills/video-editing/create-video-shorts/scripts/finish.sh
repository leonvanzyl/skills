#!/bin/bash
# Final assembly of one short in one call: audio (SFX, riser, music, stems, mix) and every compose segment in parallel,
# then the stream-copy concat, verify_final, and delivery into ../edit/short-NN_<slug>/.
#   bash scripts/finish.sh s1 [NN slug]        e.g. bash scripts/finish.sh s1 01 half-the-price-of-opus
# Segments are cached by their inputs: after an edit only the runs that changed are re-rendered (seconds to a minute).
# Run it only after every render_full.sh has printed "done" for this short's graphics (a segment composited while its
# graphic is still being written would be short; the frame-count check catches that and fails).
set -u
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
sk=$1; NN=${2:-}; SLUG=${3:-}
mkdir -p logs chk
t0=$(date +%s)
since() { echo "[$(( $(date +%s) - t0 ))s] $*"; }
"$PY" scripts/audio.py $sk > logs/audio_$sk.log 2>&1 &
AU=$!
"$PY" scripts/compose.py $sk --segments --no-concat 2>&1 | tee logs/segments_$sk.log | grep -E "segment|FAILED|MISMATCH|missing|geometry"
SEG=${PIPESTATUS[0]}
wait $AU || { echo "audio failed:"; tail -20 logs/audio_$sk.log; exit 1; }
grep -E "^music|mix_lufs" logs/audio_$sk.log
[ "$SEG" -eq 0 ] || { echo "segments failed (see logs/segments_$sk.log)"; exit 1; }
"$PY" scripts/compose.py $sk --concat
"$PY" scripts/verify_final.py $sk/final_video.mp4 chk/${sk}_final.png 2>&1 | grep -vE "^\s*$" | tail -6
if [ -n "$NN" ] && [ -n "$SLUG" ]; then
  D=../edit/short-${NN}_${SLUG}; mkdir -p "$D/stems"
  cp $sk/final_video.mp4 "$D/final.mp4"; cp $sk/stems/*.wav "$D/stems/"
  since "delivered $D/final.mp4 + stems/ (write report.md there and the PUBLISH.md section)"
fi
since "$sk finished. LOOK at chk/${sk}_final.png"
