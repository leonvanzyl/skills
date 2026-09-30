# Speed and parallelism
Target: first finished short in 30-40 min; any edit after that in under 5 min. Size worker counts to the machine (check `nproc` and `nvidia-smi` first; the reference machine had 32 cores and an RTX 5090). Never leave the GPU or spare cores idle while you wait on something else.

9.0 REUSE BEFORE YOU BUILD
- Use this skill's scripts (copied into each work-<stem>/scripts by setup.sh): the cut engine, forced aligner, HyperFrames world engine, compositor, audio synth and verification scripts. Only write code for what's missing.
- Keep per-video values in work-<stem>/project.json, never hard-coded in scripts. If you build something reusable, tell the user so it can be added to the skill.

9.1 ONE INGEST PASS AT t=0, EVERYTHING IN PARALLEL (background jobs, nothing waits on anything else)
- Decode the master exactly once, with the GPU (-hwaccel cuda). That one pass writes every proxy you'll need: 48 kHz and 16 kHz audio, a 540p full-frame proxy, a 10 fps crop of the camera region, and 1 fps thumbnails.
- The decode is bound by ONE hardware decoder session (~340 fps of 4K H.264 on an RTX 5090), not by filters or the encoder: moving scale/encode to the GPU (scale_cuda, NVENC) measured no gain. `ingest.py` therefore decodes the master as 4 time slices in parallel (whole-second boundaries keep the 10 fps / 1 fps sampling identical) and stream-copies them together: a 14.5 min 4K master in 63 s instead of ~3.5 min, with the same frames and bit-identical audio. `INGEST_SLICES=1` restores the single pass. Both audio outputs come from one read of the file.
- Never decode the full 4K master again. Later, extract only the frame ranges you actually use.
- At the same time:
  - GPU transcription, batched (`BatchedInferencePipeline`, batch 16): 14.5 min of audio in ~8 s instead of ~45 s. It only drives planning; kept lines are re-transcribed and aligned. `--sequential` restores the old pass.
  - Forced alignment for word edges: `align_lines.py` re-transcribes all line windows concurrently (4 CUDA workers on one model; 8 is no faster) and runs wav2vec2 on the GPU (CUDA PyTorch): 59 s -> 29 s for 25 lines, with identical words and word edges.
  - Face and gaze landmarks, plus a framing-shift / punch-in scan, on the camera proxy (CPU).
  - A scene-cut scan.
- Start a research subagent immediately. It checks every figure against 2+ sources and captures the source pages, logos and pricing tables as PNGs.

9.2 PLAN ONCE, THEN FAN OUT
- After ingest, write one plan file and lock it. It holds:
  - the lines and their source ranges
  - eye-contact switch points
  - the run layout tiling [0, END]
  - one graphic brief per run, with word-cue times
  - the SFX events
- Everything downstream reads that file. Don't re-derive decisions later.

9.3 PARALLEL SUBAGENTS (up to 6 at once; each one checks its own output before reporting)
- Graphics: one subagent per composition, or one per 2-3 short compositions. Each gets the shared engine, its run brief, its cue times and its assets. It then:
  - lints the composition
  - draft-renders at 10 fps
  - checks a contact sheet and fixes what it finds
  - renders at 240 fps with tmix
- Render compositions concurrently.
- Meanwhile, the main agent does everything that doesn't wait on graphics: frame-exact camera extraction, matting, captions, cover, CTA, and the audio synthesis and mix.
- Several shorts from one recording: one subagent per short after the shared ingest.

9.4 GPU WHEREVER THERE IS A GPU PATH
- NVDEC decode and CUDA transcription.
- Matting on GPU: `scripts/matte_gpu.py` runs the same u2net_human_seg model HyperFrames caches, on the onnxruntime-gpu CUDA provider, several runs at once (`--jobs 4`). Never CPU u2net: `hyperframes remove-background --device cuda` fails on Windows (its onnxruntime-node build has no CUDA) and falls back to CPU at ~0.8 s/frame.
- setup.sh verifies onnxruntime reports `CUDAExecutionProvider`; a CPU-only `onnxruntime` wheel pulled in by another package shadows onnxruntime-gpu otherwise.
- NVENC is fine for intermediates, but it doesn't speed up the ingest proxy (the decode is the bottleneck, see 9.1). Keep x264 -preset slow for the final encode only.

9.5 COMPOSITE IN PARALLEL SEGMENTS
- Render each run in its own process into a segment with identical encoder settings.
- Concatenate the segments with stream copy, and mux the audio last.
- For previews, seek to the exact frames you need. Never decode whole streams to grab a few frames.

9.6 EDITS ARE INCREMENTAL
- Cache every stage, keyed by its inputs: the plan entry, the assets and a hash of the code.
- On a change, re-run only what it touches:
  - Caption, cover or CTA fix: re-composite only the affected segments (about 1 min).
  - One graphic: re-render that composition and its segment.
  - Webcam framing: re-composite only the split and full-cam segments.
  - Timing change: re-cut that line, shift the downstream runs, re-render only the affected segments.
  - Audio level: re-mix the stems only (seconds).
  - Title or description change: edit only that short's section in edit/PUBLISH.md; nothing is re-rendered.
- Report what was re-rendered and the wall time it took.

9.7 CHECK CHEAPLY, FAIL FAST
- Verify each stage the moment it finishes, as a background job, while the next stage starts:
  - voice re-transcription and quiet at every join
  - eye-contact sheets
  - draft contact sheets for each graphic
  - one full-resolution frame of each split, checking the whole face (hair to chin) sits inside the card
- A bug found at the draft stage must never reach a full render.
