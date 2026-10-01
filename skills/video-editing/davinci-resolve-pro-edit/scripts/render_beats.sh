#!/bin/bash
# Render every zoom, keyword-pop and CTA beat of the plan (or the ids given) in parallel, then the audio, in one call:
#   bash scripts/render_beats.sh                 every zoom / words / cta beat in edit_plan.json
#   bash scripts/render_beats.sh z01 z02 c01     only these
# Zooms run up to ZOOM_JOBS (4) at once, overlays up to OVERLAY_JOBS (3); audio.py runs after them (it reads the
# overlays' SFX events). Graphics beats are not rendered here: they need their gfx_<name>.py first (render_gfx.sh).
# Run it in the background while the graphics subagents work; it prints one line per beat and a summary.
set -u
cd "$(dirname "$0")/.."
RV="${PRO_EDIT_VENV:-$HOME/.venvs/pro-edit}"; PY="$RV/Scripts/python.exe"; [ -e "$PY" ] || PY="$RV/bin/python"
mkdir -p logs
t0=$(date +%s)
since() { echo "[$(( $(date +%s) - t0 ))s] $*"; }
read -r ZOOMS OVERLAYS < <("$PY" - "$@" <<'EOF'
import json, sys
PL = json.load(open('edit_plan.json', encoding='utf-8')); want = set(sys.argv[1:])
z = [b['id'] for b in PL['beats'] if b['kind'] == 'zoom' and (not want or b['id'] in want)]
o = [b['id'] for b in PL['beats'] if b['kind'] in ('words', 'cta') and (not want or b['id'] in want)]
print(','.join(z) or '-', ','.join(o) or '-')
EOF
)
if [ "$ZOOMS" != "-" ]; then
  since "zooms: ${ZOOMS//,/ }"
  "$PY" scripts/zoom.py ${ZOOMS//,/ } --jobs "${ZOOM_JOBS:-4}" 2>&1 | tee logs/zooms.log | grep -E "frames|FAILED|WARN|Error"
fi
if [ "$OVERLAYS" != "-" ]; then
  since "overlays: ${OVERLAYS//,/ }"
  "$PY" scripts/overlay.py ${OVERLAYS//,/ } --jobs "${OVERLAY_JOBS:-3}" 2>&1 | tee logs/overlays.log | grep -E "frames|FAILED|Error"
fi
since "audio (SFX, hook music, riser, mix preview)"
"$PY" scripts/audio.py 2>&1 | tee logs/audio.log | grep -E "music:|riser|mix preview|Error"
since "beats done. LISTEN to the first minute of mix_preview.wav; LOOK at preview/ frames before trusting a zoom"
