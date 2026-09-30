#!/bin/bash
# Render gfx beats with HyperFrames at the timeline's size and rate.
#   bash scripts/render_gfx.sh draft g01 g02     10 fps draft -> gfx/draft/<id>.mp4 (check with draftsheet.py)
#   bash scripts/render_gfx.sh full  g01 g02     4x fps with per-frame motion blur, 3 of every 4 frames blended
#                                                 down (tmix) -> gfx/out/<id>.mp4, then run compose.py
# UHD timelines render the 1920x1080 layout at device scale 2 (--resolution landscape-4k), so text stays crisp.
cd "$(dirname "$0")/../gfx"
MODE="$1"; shift
read RES FPS < <(node -e "const p=require('../project.json');const s=p.timeline_size||[3840,2160];console.log((s[0]>=3840?'landscape-4k':'landscape')+' '+(p.fps||60))")
mkdir -p draft out out_hi
for r in "$@"; do
  if [ "$MODE" = "draft" ]; then
    npx --yes hyperframes render -c $r.html --fps 10 --quality draft --video-frame-format png --output draft/$r.mp4 --quiet > draft/$r.log 2>&1 \
      && echo "draft $r" || { echo "FAILED draft $r (see gfx/draft/$r.log)"; continue; }
  else
    HI=$((FPS * 4))
    npx --yes hyperframes render -c $r.html --fps $HI --quality high --resolution $RES --video-frame-format png --output out_hi/$r.mp4 --quiet > out_hi/$r.log 2>&1 \
      || { echo "FAILED $r (see gfx/out_hi/$r.log)"; continue; }
    ffmpeg -v error -y -i out_hi/$r.mp4 -vf "tmix=frames=3,fps=$FPS" -c:v libx264 -crf 10 -preset slow -pix_fmt yuv420p \
      -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv out/$r.mp4
    echo "done $r $(ffprobe -v error -show_entries stream=width,height,nb_frames -of csv=p=0 out/$r.mp4)"
  fi
done
