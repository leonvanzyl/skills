#!/usr/bin/env bash
# Usage: bash setup.sh <work-folder> [avatar-photo ...]
# Creates the run folder, the shared Python venv and the brand folder, copies any avatar photos in, and checks Codex.
set -euo pipefail
SKILL="$(cd "$(dirname "$0")/.." && pwd)"
WORK="${1:?usage: setup.sh <work-folder> [avatar-photo ...]}"; shift || true
BRAND="${THUMB_BRAND:-$HOME/.youtube-thumbnails}"

mkdir -p "$WORK"/{research,competitors,refs,prompts,out,qa,thumbnails} "$BRAND/avatar"
for f in "$@"; do cp "$f" "$BRAND/avatar/"; done

# one venv for every run (Pillow, NumPy, OpenCV); a few seconds once uv's cache is warm
if [ ! -d "$BRAND/.venv" ]; then
  uv venv "$BRAND/.venv" -q
  if [ -x "$BRAND/.venv/Scripts/python.exe" ]; then PY="$BRAND/.venv/Scripts/python.exe"; else PY="$BRAND/.venv/bin/python"; fi
  uv pip install -q --python "$PY" pillow numpy opencv-python-headless
fi
if [ -x "$BRAND/.venv/Scripts/python.exe" ]; then PY="$BRAND/.venv/Scripts/python.exe"; else PY="$BRAND/.venv/bin/python"; fi

echo "work:    $WORK"
echo "brand:   $BRAND  (avatars: $(ls "$BRAND/avatar" 2>/dev/null | wc -l | tr -d ' '), brand.md: $([ -f "$BRAND/brand.md" ] && echo yes || echo 'no - write it after the research step'))"
echo "python:  $PY"
echo "skill:   $SKILL"

# Codex: installed, logged in, image generation on
if ! command -v codex >/dev/null; then echo "MISSING: Codex CLI (npm i -g @openai/codex, then codex login)"; exit 1; fi
echo "codex:   $(codex --version 2>&1 | head -1)"
codex login status 2>&1 | head -1 | sed 's/^/login:   /'
if codex features list 2>/dev/null | grep -E '^image_generation' | grep -q true; then echo "imagegen: on"
else echo "imagegen: OFF - enable with: codex features enable image_generation (or --enable image_generation)"; fi
[ "$(ls "$BRAND/avatar" 2>/dev/null | wc -l)" -gt 0 ] || echo "NOTE: no avatar photo yet - ask the user for one, then: cp <photo> \"$BRAND/avatar/\""
