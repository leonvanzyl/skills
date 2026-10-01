# Speed and parallelism
Target: first finished short in 20-30 min of wall time, of which the machine needs about 5 min (1.7 min analysis, ~3 min from the locked plan to the delivered file); any edit after that in under 2 min. The rest is your planning, briefing and checking, so keep those tight: one stage script per stage (`analyze.sh`, `cut.sh`, `prep.sh`, `finish.sh`), run in the background while you do the next judgement call. Size worker counts to the machine (check `nproc` and `nvidia-smi` first; the reference machine had 32 cores and an RTX 5090). Never leave the GPU or spare cores idle while you wait on something else.

9.0 REUSE BEFORE YOU BUILD
- Use this skill's scripts (copied into each work-<stem>/scripts by setup.sh): the cut engine, forced aligner, HyperFrames world engine, compositor, audio synth and verification scripts. Only write code for what's missing.
- Keep per-video values in work-<stem>/project.json, never hard-coded in scripts. If you build something reusable, tell the user so it can be added to the skill.

9.1 ONE INGEST PASS AT t=0, EVERYTHING IN PARALLEL (background jobs, nothing waits on anything else)
- Decode the master exactly once, with the GPU (-hwaccel cuda). That one pass writes every proxy you'll need: 48 kHz and 16 kHz audio, a 540p full-frame proxy, a 10 fps crop of the camera region, and 1 fps thumbnails.
- The decode is bound by the hardware decoder, not by filters or the encoder: moving scale/encode to the GPU (scale_cuda, NVENC) measured no gain. `ingest.py` therefore decodes the master as 4 time slices in parallel (whole-second boundaries keep the 10 fps / 1 fps sampling identical) and stream-copies them together: a 15 min 4K master in 60 s instead of 105 s, same frame count, bit-identical audio. 8 slices measured 61 s, so 4 already saturates the RTX 5090's NVDEC engines (~900 fps of 4K H.264). `INGEST_SLICES=1` restores the single pass. Both audio outputs come from one read of the file. `ingest.py` writes `ingest_audio.done` and `ingest.done` so `analyze.sh` can start transcription about 5 s in and camera detection the moment the proxy lands.
- Never decode the full 4K master again. Later, extract only the frame ranges you actually use.
- At the same time (`analyze.sh` sequences all of this on the ingest's `.done` markers, in one call):
  - GPU transcription, batched (`BatchedInferencePipeline`, batch 16): 14.5 min of audio in ~8 s instead of ~45 s. It only drives planning; kept lines are re-transcribed and aligned. `--sequential` restores the old pass.
  - Forced alignment for word edges: `align_lines.py` re-transcribes all line windows concurrently (4 CUDA workers on one model; 8 is no faster) and runs wav2vec2 on the GPU (CUDA PyTorch): 59 s -> 29 s for 25 lines, with identical words and word edges.
  - Face and gaze landmarks, plus a framing-shift / punch-in scan, on the camera proxy (CPU). Both were single-threaded loops over every proxy frame and took the longest of the whole analysis on a 15 min master (gaze ~7 min); both now run as 8 time slices in parallel processes (`GAZE_WORKERS`, `ZOOM_WORKERS`): the zoom scan matches a sequential pass row for row (each slice starts one frame early), and the gaze landmarker warms up on the second before its slice so the VIDEO-mode tracker state at the boundary is the same.
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
  - draft-renders at 10 fps (`render_draft.sh`: draft + contact sheet in one call)
  - checks a contact sheet and fixes what it finds
  - renders at 240 fps with tmix (`render_full.sh`)
- Render compositions concurrently, but through `render_full.sh` only: it holds a machine-wide budget of RENDER_SLOTS (3) renders x HF_WORKERS (8) Chrome browsers, so six subagents rendering at once queue behind each other instead of launching 100 Chromes (24 workers on one render was already slower than 16). One 8 s composition: ~45 s alone; the full-render stage of a six-composition short stays around 2-3 min.
- The 240 fps intermediate is a lossless PNG sequence, not MOV: HyperFrames' MOV/ProRes path forces its slow alpha capture (~15 fps regardless of workers) and its MP4 path captures JPEG and has the 8 px right-edge strip (lessons.md). `PRODUCER_ENABLE_BROWSER_POOL=false` (exported by both render scripts) gives each worker its own browser, which is what makes the workers count: 11 -> 41 fps at 8 workers.
- Meanwhile, the main agent does everything that doesn't wait on graphics: frame-exact camera extraction, matting, captions, cover, CTA, and the audio synthesis and mix (`prep.sh`, one call).
- Several shorts from one recording: one subagent per short after the shared ingest.

9.4 GPU WHEREVER THERE IS A GPU PATH
- NVDEC decode and CUDA transcription. `cam_prep.py` decodes every camera run on NVDEC too (`-hwaccel cuda` with `format=yuv420p` first, which makes the nv12 output take the same colour conversion as the CPU path: byte-identical frames, verified), four runs at once, into multi-slice FFV1. `CAM_HWACCEL=0` forces the CPU decoder.
- Matting on GPU: `scripts/matte_gpu.py` runs the same u2net_human_seg model HyperFrames caches, on the onnxruntime-gpu CUDA provider, several runs at once (`--jobs 4`) and three frames in flight per run (`--threads 3`; the model takes a batch of one, the time is in the resizes and the encode, and ORT/OpenCV release the GIL). The matte is written as lossless multi-slice FFV1 (`MATTE_CODEC=png` restores PNG-in-MOV): identical alpha, about 3x faster to write and to read back in compose. Never CPU u2net: `hyperframes remove-background --device cuda` fails on Windows (its onnxruntime-node build has no CUDA) and falls back to CPU at ~0.8 s/frame.
- setup.sh verifies onnxruntime reports `CUDAExecutionProvider`; a CPU-only `onnxruntime` wheel pulled in by another package shadows onnxruntime-gpu otherwise.
- The GPU is NOT where the graphics time goes: HyperFrames captures with Chrome's hardware GPU already, and its bottleneck was one shared browser process (9.3). NVENC is fine for intermediates, but it doesn't speed up the ingest proxy (the decode is the bottleneck, see 9.1). Keep x264 -preset slow for the final encode only.

9.5 COMPOSITE IN PARALLEL SEGMENTS
- Render each run in its own process into a segment with identical encoder settings: `compose.py <sk> --segments` spawns one process per run, all at once (`--jobs N` to limit), verifies every segment's frame count against its run, then concatenates. `finish.sh` runs it together with `audio.py`. A 34 s short with six runs composites in ~55 s (the longest split run bounds it: ~75 ms a frame for the Lanczos upscale, unsharp, blurred strips and the three blends, which run only on the rows below the card's shadow); plain full-visual runs are encoder-bound at ~17 ms a frame.
- Previews (`--preview t1,t2`) seek each stream straight to the wanted frames: a six-frame spot check takes ~4 s. Use them freely.
- Concatenate the segments with stream copy, and mux the audio last.
- For previews, seek to the exact frames you need. Never decode whole streams to grab a few frames.

9.6 EDITS ARE INCREMENTAL
- Every segment is cached by its inputs: `compose.py --segments` writes `<sk>/seg/runNN.key` (the run, its captions, the graphic / camera clip / matte / split geometry files with sizes and mtimes, the cover, the CTA spec, the encoder settings and a hash of compose.py) and skips any run whose key is unchanged. `--force` re-renders everything.
- On a change, re-run only what it touches (`finish.sh <sk>` does the right thing by itself; the list says what to expect):
  - Caption, cover or CTA fix: only the segments whose captions changed are re-rendered (under a minute).
  - One graphic: re-render that composition (`render_full.sh`), then `finish.sh`: only its segment is re-rendered.
  - Webcam framing: delete `<sk>/cam/split_geom.json`, then `finish.sh`: only the split segments change.
  - Timing change: re-cut that line (`cut.sh`), `prep.sh` for the camera clips and mattes of the runs that moved, re-render the graphics whose runs moved, then `finish.sh`.
  - Audio level: `finish.sh` re-mixes the stems and re-concatenates; no segment is touched (seconds).
  - Title or description change: edit only that short's section in edit/PUBLISH.md; nothing is re-rendered.
- Report what was re-rendered and the wall time it took (`finish.sh` prints which runs it rendered and which it kept).

9.7 CHECK CHEAPLY, FAIL FAST
- Verify each stage the moment it finishes, as a background job, while the next stage starts:
  - voice re-transcription and quiet at every join
  - eye-contact sheets
  - draft contact sheets for each graphic
  - one full-resolution frame of each split, checking the whole face (hair to chin) sits inside the card
- A bug found at the draft stage must never reach a full render.
