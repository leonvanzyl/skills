# Setup, model quirks and troubleshooting

## The environment
- Python env: a uv virtualenv, Python 3.13, ~4.4 GB with CUDA PyTorch. Default location `~/.venvs/crisperwhisper`
  (override with `VEDIT_VENV`); the interpreter is `Scripts/python.exe` inside it on Windows and `bin/python` on
  macOS/Linux. Known-good versions: torch 2.11.0+cu128, transformers 5.17, crisperwhisper 2.0.3.
- Model: `nyralabs/CrisperWhisper2.0_large` (~2.9 GB, not gated - no Hugging Face login needed) in the standard
  Hugging Face cache (`~/.cache/huggingface/hub`, or `$HF_HOME/hub`). Any tool asking for this model ID reuses the
  cache. `vedit.py` sets `HF_HUB_OFFLINE=1` so it can never silently re-download.
- GPU: `vedit.py` uses the first NVIDIA GPU if PyTorch can see one, otherwise the CPU. CrisperWhisper has no Apple
  Silicon (MPS) support, so Macs run on the CPU. RTX 50-series (Blackwell) cards need PyTorch built for CUDA 12.8+
  (`cu128` wheels).
- Tested on Windows 11 with an RTX 5090. macOS and Linux should work with the same steps but haven't been run end
  to end yet.

### Install (first time, or if the env is broken)
Needs [uv](https://docs.astral.sh/uv/) and ffmpeg (Windows `winget install Gyan.FFmpeg`, macOS
`brew install ffmpeg`, Debian/Ubuntu `sudo apt install ffmpeg`). Tell the user about the model license (below)
before downloading it.
```bash
VENV="${VEDIT_VENV:-$HOME/.venvs/crisperwhisper}"
mkdir -p "$(dirname "$VENV")"
uv venv "$VENV" --python 3.13
PY="$VENV/Scripts/python.exe"; [ -e "$PY" ] || PY="$VENV/bin/python"
# NVIDIA GPU (Windows or Linux):
uv pip install -p "$PY" torch torchaudio --index-url https://download.pytorch.org/whl/cu128
# No NVIDIA GPU (macOS, or CPU only) - use this line instead of the one above:
#   uv pip install -p "$PY" torch torchaudio
uv pip install -p "$PY" "crisperwhisper[transformers]"
"$PY" -c "import torch, crisperwhisper; print('cuda:', torch.cuda.is_available())"
# Download the model once (~2.9 GB):
HF_HUB_OFFLINE=0 "$PY" -c "from huggingface_hub import snapshot_download; snapshot_download('nyralabs/CrisperWhisper2.0_large')"
```

### Windows pitfalls hit during setup
- `crisperwhisper[ct2]` (fast CTranslate2 backend with speculative decoding) is **Linux-only** - its custom
  `ctranslate2-crisperwhisper` wheel has no Windows build. Use `crisperwhisper[transformers]`.
- `uv` fails with "Trivial strip failed" when the venv lives in a very deep path (Windows long paths). Keep envs
  and work dirs at short paths.
- faster-whisper needed cuBLAS/cuDNN DLLs on PATH (`...\site-packages\nvidia\{cublas,cudnn,cuda_runtime}\bin`);
  the torch-based CrisperWhisper env doesn't.

### License note
The CrisperWhisper 2.0 weights and outputs are under the nyra health Non-Commercial Research License (the
inference code is MIT). Tell the user once, before the model is downloaded, and let them decide - a monetised
video may count as commercial use. If the model is already in the cache, that decision has been made; don't raise
it again unless asked.

## Why CrisperWhisper (if the user asks)
- **Resolve's own transcription**: the API can trigger `TranscribeAudio` but only returns a truncated text
  preview - no word timings. Text-based editing in the transcript panel is UI-only. Auto-subtitles are readable but
  phrase-level only.
- **Whisper / faster-whisper**: trained to produce clean text - drops "um/uh", smooths stutters, hallucinates
  "Thank you for watching" on short/quiet clips, misspells names, and transcribes an immediately re-read sentence
  once (swallowing the retake into one long word).
- **Leaderboard models** (Canary-Qwen, Granite Speech, Parakeet, Qwen3-ASR, Cohere Transcribe) are ranked on
  normalised WER - they're built to drop disfluencies, which is the opposite of what editing needs.
- **CrisperWhisper 2.0**: verbatim by design - fillers, repetitions, cut-offs (`bi-`), vocal events
  (`[lipsmack]`, `[throatclearing]`, `[breath]`), ~30-40 ms word boundaries, hotword support, anti-hallucination
  decoding. On the Jev video it found ~20 things Whisper missed and no hallucinations.

## Model behaviour to know
- Throughput on an RTX 5090 (transformers backend): model load ~20 s, ~1.2 s per short clip (509 clips ~10 min).
  Smaller GPUs are slower and a CPU much slower - on a CPU, run `transcribe` in the background and tell the user.
- Transcribe each timeline clip on its own, not the whole timeline in one go - the user's silence cut already
  separates attempts, and per-clip decoding keeps retakes from merging.
- **Filler timestamps can be compressed**: `[UH]` stamped as 20 ms right before the next word while the real
  "uh" sits in the preceding gap; timestamps near restarts can be 0.3-0.5 s off. Never cut on raw timestamps -
  `vedit verify` exists for this.
- **Truncated audio gets "completed"**: a range ending in "a l" can be transcribed as "a little bit". When QA shows
  a phrase duplicated across a cut, `probe` before believing it.
- **Out-of-context mishearing**: short snippets can mishear ("We've got" -> "We bought"). The verifier uses fuzzy
  sequence matching for this reason.
- **Hotwords** help names a lot but over-correct similar-sounding words ("Cool" -> "Skool").

## Cut verification details (what `vedit verify` does)
Tested on the Jev project: 55/55 cuts verified automatically in ~3 min, landing inside the same pauses an editor
chose by hand - including every cut that needed manual probing in the first run.
1. Window of +-0.5 s around the model's word boundary (timestamps can be 0.5 s off near restarts), bounded so
   ranges in the same clip can never overlap (an overlap duplicates audio).
2. Candidates: real pauses (< -48 dB) first, deepest first, each placed at the **middle of the whole quiet
   stretch** (cutting at the quietest point can sit 20 ms from the next word's onset); shallow dips between
   run-together words only after that. Every candidate is snapped to the frame grid first - the check must hear
   exactly the frame Resolve will cut on (a 7 ms rounding difference let an "uh" back in).
3. A candidate passes when the 2 s kept-side snippet:
   - has a real word at the edge (not `[UH]`) that matches the expected word - exactly for short words and
     fillers ("well" is not "we", "to" is not "so"), fuzzily for longer ones ("Jeff"/"Jev"), contractions ignored
     ("we've"/"we"), and pieces of words with digits accepted ("n eight n" = "n8n");
   - matches the expected word sequence (>= 0.5; snippet and full-clip transcripts legitimately differ);
   - has no extra word at the cut (it lines up better with the expectation once its edge word is dropped);
   - and, when the kept phrase repeats words that were just removed ("And one, | and one cool"), the removed copy
     is audible on the other side (the repeat guard - otherwise the wrong copy matches).
4. If no pause passes (filler fused onto the next word, words run together), scan frame by frame within
   +-0.4 s and take the second frame of the first run of two passing frames.
5. Otherwise the cut is marked UNVERIFIED and left at the model timestamp - probe it.
Short snippets (< 1 s) transcribe badly ("I'm not going" -> "I'm okay"), which is why the removed side is only
checked for repeats and never required to be word-perfect.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `Could not load nyralabs/...` | Cache missing: run once with `HF_HUB_OFFLINE=0`. |
| `torch.cuda.is_available()` False on a machine with an NVIDIA GPU | Wrong torch wheel - reinstall with the cu128 index. Check `nvidia-smi`. |
| Very slow transcription | Running on CPU; see above. |
| `items.json missing` | Run `prepare` first with the saved structure file. |
| prepare warns "separate audio" | Audio track uses another media item; the linked build would use camera audio - see resolve-mcp.md. |
| Many UNVERIFIED cuts | Look at `cut_report.txt`: if the kept-side text is right but the removed side is empty, the removed words may be tags only or the decision's word index is off by one. |
| QA shows a stutter the listing didn't | Short stutters ("I I'm") can be hidden by per-clip decoding; decide whether it's worth a micro-cut. |
