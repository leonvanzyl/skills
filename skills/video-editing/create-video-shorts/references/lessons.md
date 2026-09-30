# Lessons (hard-won; read before improvising)

**Cutting**
- **Word edges:** never cut on raw Whisper word timestamps; they are off by 0.1–0.3 s after pauses. `align_lines.py` re-transcribes each line in a silence-bounded window and force-aligns it with wav2vec2. `cut2.py` then takes onsets from RMS with a −45 dB gap search, and true ends from the spec rule (−35 dB, with −32 dB held for 150 ms).
- **Connected speech:** when the previous word runs straight into the line (no gap), cut at the RMS minimum between the two words. If that leaves a syllable remnant ("Then|let's"), move the line start back to the nearest clean silence and keep the extra word.
- **Join quiet:** place joins loud-to-loud (last ≥ −35 dB frame to next ≥ −35 dB frame = 120 ms). Measuring from word edges instead lets quiet lead-ins stack up past 150 ms.
- **Proof:** re-transcribe the finished voice track every time (`verify_voice.py`). It catches clipped onsets ("Opus" heard as "…pus") and stray syllables.
- **Accents:** Whisper mis-hears some words for a given speaker (e.g. "Sonnet" as "Sonic", "Claude" as "cloud"). Keep these in `project.json` → `asr_fixes`. Captions always use the correct word.

**Eye contact and source quirks**
- **Detecting reading:** looking at a screen shows up as a head pitch/yaw shift. `gaze.py` clusters it; confirm with eye crops (`eyesheet.py`), and use 100 ms steps around turns.
- **Glances vs turns:** blinks and eye glances under about 0.3 s are not "looking away".
- **Snapping switches:** a camera switch snaps to a word boundary. The switch goes before the turn when you look away, and after the turn when you look back.
- **Finished edits:**
  - Background tracking (`zoomscan.py`) catches baked-in punch-ins and zoom transitions. Keep camera runs off them.
  - A finished edit may cut briefly to a full-frame camera shot. That's the sharpest camera footage available, so prefer it for full cam (`"cam": "fullframe"`).
- **Webcam window:** in a picture-in-picture, the webcam window can be small (for example 704×948 in 4K). Full cam upscales it about 2× with a light unsharp mask. In the split card, fit the whole face (hair to chin), and fill the side strips with a blurred copy rather than cropping the chin off.

**Compositing**
- **Frame lock:** the matte is made from the same frame-exact clip as the card footage, so head and card can't drift apart. Erode the u2net matte by 1 px to remove its dark rim.
- **Captions:** draw them word by word with an extra 16 px gap, or the 10 px stroke swallows the spaces. Position each caption from the run of the current frame, not the run where the caption started.
- **Previews:** decode only the runs you need (`--runs`). Decoding whole streams for a few preview frames wastes minutes.
- **Parallel segments:** render each run as its own process, then concatenate with stream copy. That's about 2× faster than one process on a 32-core machine, and it makes edits incremental.

**HyperFrames**
- **Standalone comps:** render them with `render -c file.html`. `snapshot` only reads `index.html`, so use 10 fps draft renders and contact sheets.
- **Driving the timeline:** the engine drives everything from a GSAP proxy setter (`tl.fromTo(state, {t:0}, {t:dur})`). A tween setter runs on every seek, whereas `onUpdate` callbacks can be suppressed while seeking.
- **Video clips:** re-encode clips with dense keyframes (`-g 12`) and render with `--video-frame-format png` for UI footage.
- **Blend modes:** they are isolated inside a card that has a filter or opacity. Put highlight bands under a `mix-blend-mode:multiply` screenshot inside the same card.
- **Right-edge strip:** HyperFrames' MP4 encoder leaves an 8 px black strip at x 1072-1079 on 1080-wide output (draft and high quality alike). `render_full.sh` renders the 240 fps intermediate as MOV (ProRes 4444), which is clean. Check the right edge of each `out60` file: columns 1072-1079 should match 1064-1071.
- **Don't composite while a graphic is re-rendering:** a segment decoded while its `out60` file is being rewritten silently picks up the old or a partial render. Composite only after every `render_full.sh` has printed `done`, and check each segment's frame count.
- **Exact stills:** use output seeking (`-ss X-0.5 -i src -ss 0.5`). Input-only seeking can land a frame early, e.g. on a menu that isn't open yet.

**Environment**
- **Face detection:** OpenCV 5 removed the old Haar face cascades. `faces.py` uses the bundled YuNet model (`face_detection_yunet_2023mar.onnx`), which also finds small webcam-window faces.
- **Windows shells:** in Git Bash, `\n` inside a Python heredoc becomes a real newline and breaks string literals. Write longer code with a file-writing tool.
- **Busy folders:** a folder used as the shell's working directory can't be renamed on Windows. `cd` out of it first.
- **CPU fallbacks:** Whisper falls back to CPU int8. The matte falls back to CPU u2net (`hyperframes remove-background`) at about 1 fps per process when onnxruntime-gpu is unavailable. Both work; just expect a longer run.
- **Where the time goes (RTX 5090, 14.5 min 4K master):** ingest is decode-bound, so decode in parallel slices (4 NVDEC sessions: 63 s, not ~3.5 min), because GPU scaling or NVENC doesn't help it. Full transcription: batched, ~8 s. Line alignment: parallel Whisper windows + CUDA wav2vec2, 29 s. Matting: GPU, ~70-100 s for ten split runs. Graphics renders (headless Chrome, CPU) and compositing dominate what remains, so run them as parallel processes.
- **CUDA PyTorch:** setup.sh installs the cu130 build on NVIDIA machines (the CPU build ran wav2vec2 at 11.8 s for 25 lines, CUDA at 0.9 s, with identical edges). CUDA 12 (CTranslate2/onnxruntime) and CUDA 13 (torch) DLLs coexist fine in one process.
- **Matte on GPU:** `hyperframes remove-background --device cuda` can't use CUDA on Windows (its onnxruntime-node build lacks it) and silently drops to CPU. `matte_gpu.py` runs the same cached model on onnxruntime-gpu instead: ~12x faster. If `onnxruntime.get_available_providers()` lacks `CUDAExecutionProvider`, a CPU `onnxruntime` wheel is shadowing onnxruntime-gpu: uninstall it and reinstall onnxruntime-gpu (setup.sh does this).
- **Matte cleanup:** u2net keeps background objects that touch the head (e.g. a guitar neck on the wall above the hair), and they pop out above the split card. `matte_gpu.py` gates the matte with a horizontal opening (drops thin vertical strips under 80 source px), keeps the largest blob, and feathers the clip's top 14 rows (the webcam window border). Check one matte over a flat colour above the hair line.
