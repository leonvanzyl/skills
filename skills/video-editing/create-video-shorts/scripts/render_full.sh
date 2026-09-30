#!/bin/bash
# full renders: 240 fps with per-frame viewport motion blur, then blend 3 of every 4 frames down to 60 fps.
# The 240 fps intermediate is MOV (ProRes 4444): hyperframes' MP4 encoder leaves an 8 px black strip at x 1072-1079 on
# 1080-wide output (the frame is padded to a 16-px macroblock width and cropped wrong). The MOV path is clean.
# usage: bash scripts/render_full.sh s1_r0 s1_r2 ...   (runs up to $JOBS renders at once; default 4)
cd "$(dirname "$0")/../gfx"
mkdir -p out240 out60
JOBS=${JOBS:-4}
one() {
  r=$1
  npx --yes hyperframes render -c $r.html --fps 240 --quality high --format mov --video-frame-format png --output out240/$r.mov --quiet > out240/$r.log 2>&1
  ffmpeg -v error -y -i out240/$r.mov -vf "tmix=frames=3,fps=60" -c:v libx264 -crf 10 -preset slow -pix_fmt yuv420p out60/$r.mp4
  rm -f out240/$r.mov
  echo "done $r $(ffprobe -v error -show_entries format=duration -of csv=p=0 out60/$r.mp4)"
}
n=0
for r in "$@"; do one $r & n=$((n+1)); if [ $((n % JOBS)) -eq 0 ]; then wait; fi; done
wait
