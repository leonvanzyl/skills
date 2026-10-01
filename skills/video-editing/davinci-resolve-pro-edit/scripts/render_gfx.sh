#!/bin/bash
# Render gfx beats with HyperFrames at the timeline's size and rate.
#   bash scripts/render_gfx.sh draft g01 g02     10 fps drafts -> gfx/draft/<id>.mp4 (check with draftsheet.py); all at once
#   bash scripts/render_gfx.sh full  g01 g02     4x fps with per-frame motion blur, 3 of every 4 frames blended down
#                                                 (tmix) -> gfx/out/<id>.mp4, then run compose.py
# UHD timelines render the 1920x1080 layout at device scale 2 (--resolution landscape-4k), so text stays crisp.
# Full renders capture lossless PNG frames (--format png-sequence: the MP4 path captures JPEG, measured 48.6 dB against
# the lossless frame) with ONE CHROME PER WORKER (PRODUCER_ENABLE_BROWSER_POOL=false; the default pool makes every
# worker a tab of one browser whose single GPU process encodes every screenshot). The tmix output is NVENC lossless
# when there is an NVIDIA encoder (no generation loss, GPU-fast), else x264 crf 10 as before.
# Throttle (several subagents call this at once): at most RENDER_SLOTS (2) full renders on the machine at a time,
# HF_WORKERS (12) browsers each - at 4K the PNG encode inside each Chrome is the cost: 8 browsers captured the
# cubefarm g03 beat (1,349 frames) in 70 s, 12 in 62 s, 16 in 80 s; lock directories in gfx/.render_slots. For the
# record: the old MP4 path took 88 s in total, and JPEG capture with 16 separate browsers 100 s, so the lossless path
# is also the fastest one.
export PRODUCER_ENABLE_BROWSER_POOL=false
cd "$(dirname "$0")/../gfx"
MODE="$1"; shift
read RES FPS < <(node -e "const p=require('../project.json');const s=p.timeline_size||[3840,2160];console.log((s[0]>=3840?'landscape-4k':'landscape')+' '+(p.fps||60))")
mkdir -p draft out png_hi .render_slots
RENDER_SLOTS=${RENDER_SLOTS:-2}; HF_WORKERS=${HF_WORKERS:-12}
NVENC=$(ffmpeg -v error -f lavfi -i color=black:s=256x256:d=0.1 -c:v h264_nvenc -f null - 2>/dev/null && [ -z "${PRO_EDIT_X264:-}" ] && echo 1 || echo 0)

take_slot() {   # blocks until a slot is free; echoes the slot path. A slot whose owner has died is reclaimed.
  while :; do
    for ((k = 0; k < RENDER_SLOTS; k++)); do
      s=.render_slots/slot$k
      if mkdir "$s" 2>/dev/null; then echo $$ > "$s/pid"; echo "$s"; return; fi
      p=$(cat "$s/pid" 2>/dev/null); if [ -n "$p" ] && ! kill -0 "$p" 2>/dev/null; then rm -rf "$s"; fi
    done
    sleep 2
  done
}

draft_one() {
  r=$1
  npx --yes hyperframes render -c $r.html --fps 10 --quality draft --video-frame-format png --workers ${HF_DRAFT_WORKERS:-4} --output draft/$r.mp4 --quiet > draft/$r.log 2>&1 \
    && echo "draft $r" || echo "FAILED draft $r (see gfx/draft/$r.log)"
}

full_one() {
  r=$1; HI=$((FPS * 4))
  slot=$(take_slot); t0=$(date +%s)
  if [ "$NVENC" = 1 ]; then ENC="-c:v h264_nvenc -preset p1 -tune lossless"; else ENC="-c:v libx264 -crf 10 -preset slow"; fi
  TAGS="-colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv"
  rm -rf png_hi/$r
  if ! npx --yes hyperframes render -c $r.html --fps $HI --quality high --resolution $RES --format png-sequence --video-frame-format png \
       --workers $HF_WORKERS --output png_hi/$r --quiet > png_hi/$r.log 2>&1; then
    echo "FAILED $r: render (see gfx/png_hi/$r.log)"; rm -rf "$slot"; return 1
  fi
  n=$(ls png_hi/$r | grep -c png); t1=$(date +%s)
  if ! ffmpeg -v error -y -framerate $HI -i png_hi/$r/frame_%06d.png \
       -vf "format=gbrp,tmix=frames=3,fps=$FPS,scale=out_color_matrix=bt709:out_range=tv,format=yuv420p" $ENC -pix_fmt yuv420p $TAGS out/$r.mp4; then
    echo "FAILED $r: tmix"; rm -rf "$slot"; return 1
  fi
  rm -rf png_hi/$r "$slot"
  echo "done $r $(ffprobe -v error -show_entries stream=width,height,nb_frames -of csv=p=0 out/$r.mp4) ($n frames at $HI fps: capture $((t1 - t0)) s, tmix $(( $(date +%s) - t1 )) s)"
}

for r in "$@"; do
  if [ "$MODE" = "draft" ]; then draft_one $r & else full_one $r & fi
done
wait
