#!/bin/bash
# 10 fps draft of one or more compositions + their contact sheets, in one call:
#   bash scripts/render_draft.sh s1_r0 s1_r3 ...     -> gfx/draft/<r>.mp4, chk/<r>_sheet.png (LOOK at it)
# Drafts are small (about 80 frames) so they use 4 Chrome workers each (own browser each, see render_full.sh) and run all at once.
export PRODUCER_ENABLE_BROWSER_POOL=false
cd "$(dirname "$0")/.."
PY=../.venv/Scripts/python.exe; [ -f "$PY" ] || PY=../.venv/bin/python
mkdir -p gfx/draft chk
one() {
  r=$1
  (cd gfx && npx --yes hyperframes render -c $r.html --fps 10 --quality draft --video-frame-format png --workers ${HF_DRAFT_WORKERS:-4} \
     --output draft/$r.mp4 --quiet > draft/$r.log 2>&1) || { echo "FAILED $r (see gfx/draft/$r.log)"; return 1; }
  "$PY" scripts/draftsheet.py $r 8 && echo "draft $r -> chk/${r}_sheet.png"
}
for r in "$@"; do one $r & done
wait
