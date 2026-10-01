#!/bin/bash
# Full renders: 240 fps with per-frame viewport motion blur, then blend 3 of every 4 frames down to 60 fps.
#   bash scripts/render_full.sh s1_r0 s1_r2 ...
# Per composition:
#   1. hyperframes render --format png-sequence --fps 240 --quality high   -> gfx/png240/<r>/frame_%06d.png
#      Lossless PNG capture of every frame (the MP4 path captures JPEG and leaves an 8 px black strip at x 1072-1079;
#      the MOV/ProRes path forces a slow alpha capture: ~3x slower for the same pixels).
#   2. ffmpeg: tmix=frames=3,fps=60 on the RGB frames -> BT.709 yuv420p -> gfx/out60/<r>.mp4 (libx264 crf 10, tagged bt709)
#   3. the PNG frames are deleted.
# Throttling (several subagents call this at once): at most RENDER_SLOTS renders run on the machine at a time, each with
# HF_WORKERS Chrome workers (defaults 3 x 8 = 24 Chromes on 32 cores; more workers per render only slows all of them).
# The slots are lock directories in gfx/.render_slots; a slot whose owner process has died is reclaimed.
# PRODUCER_ENABLE_BROWSER_POOL=false gives every worker its own Chrome. With the default pool, all workers are tabs of ONE
# browser whose single GPU process encodes every PNG screenshot, so PNG capture tops out at ~15 fps however many workers
# you add (measured: 1 worker 11 fps, 16 workers 15 fps). Separate browsers: 4 workers 29 fps, 8 -> 41 fps, 16 -> 51 fps.
export PRODUCER_ENABLE_BROWSER_POOL=false
cd "$(dirname "$0")/../gfx"
mkdir -p png240 out60 .render_slots
RENDER_SLOTS=${RENDER_SLOTS:-3}
HF_WORKERS=${HF_WORKERS:-8}

take_slot() {   # blocks until a slot is free; echoes the slot path
  while :; do
    for ((k = 0; k < RENDER_SLOTS; k++)); do
      s=.render_slots/slot$k
      if mkdir "$s" 2>/dev/null; then echo $$ > "$s/pid"; echo "$s"; return; fi
      p=$(cat "$s/pid" 2>/dev/null)
      if [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; then rm -rf "$s"; fi     # stale slot from a crashed render
    done
    sleep 2
  done
}

one() {
  r=$1
  slot=$(take_slot)
  trap 'rm -rf "$slot"' EXIT
  t0=$(date +%s)
  rm -rf png240/$r
  if ! npx --yes hyperframes render -c $r.html --fps 240 --quality high --format png-sequence --video-frame-format png \
       --workers $HF_WORKERS --output png240/$r --quiet > png240/$r.log 2>&1; then
    echo "FAILED $r: render (see gfx/png240/$r.log)"; rm -rf "$slot"; return 1
  fi
  n=$(ls png240/$r | grep -c png)
  t1=$(date +%s)
  if ! ffmpeg -v error -y -framerate 240 -i png240/$r/frame_%06d.png \
       -vf "format=gbrp,tmix=frames=3,fps=60,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" \
       -c:v libx264 -crf 10 -preset slow -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv out60/$r.mp4; then
    echo "FAILED $r: tmix"; rm -rf "$slot"; return 1
  fi
  rm -rf png240/$r "$slot"
  echo "done $r $(ffprobe -v error -show_entries format=duration -of csv=p=0 out60/$r.mp4) ($n frames at 240 fps: capture $((t1 - t0)) s, tmix $(( $(date +%s) - t1 )) s, $HF_WORKERS workers)"
}

for r in "$@"; do one $r & done
wait
