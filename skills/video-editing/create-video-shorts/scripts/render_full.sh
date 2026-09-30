#!/bin/bash
# full renders: 240 fps with per-frame viewport motion blur, then blend 3 of every 4 frames down to 60 fps
cd "$(dirname "$0")/../gfx"
mkdir -p out240 out60
for r in "$@"; do
  npx --yes hyperframes render -c $r.html --fps 240 --quality high --video-frame-format png --output out240/$r.mp4 --quiet > out240/$r.log 2>&1
  ffmpeg -v error -y -i out240/$r.mp4 -vf "tmix=frames=3,fps=60" -c:v libx264 -crf 10 -preset slow -pix_fmt yuv420p out60/$r.mp4
  echo "done $r $(ffprobe -v error -show_entries format=duration -of csv=p=0 out60/$r.mp4)"
done
