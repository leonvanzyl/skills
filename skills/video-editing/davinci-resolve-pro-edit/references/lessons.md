# Lessons (hard-won; read before improvising)

**From the shorts skill, still true here**
- **Word edges:** never cut or cue on raw Whisper times. The foundation cut verifies every cut by re-transcribing
  it; cues for beats use CrisperWhisper's word starts (~30-40 ms), which is plenty for a camera move.
- **Captures:** real pages are 2x PNGs; crops never include the webcam window.
- **Blend modes:** a light highlight band under a `mix-blend-mode:multiply` screenshot vanishes on dark UI. On dark
  UI use a translucent clay wash above the image (`zoom.py` chooses automatically for zoom marks). On a captured
  page, a multiply band inside a card's `overlay` did nothing and simply hid the text: the overlay layer is its own
  stacking context. Set `overlayBlend='multiply'` on the card instead (engine support added after the first test).
- **Frame 0 is the landing state** of every graphic, because it hard-cuts in over V1.
- **Split geometry:** the matte and the card come from the same decoded frames, so the head can't drift from the
  body; erode the matte 1 px; check one full-resolution frame of every split.
- **Windows shells:** in Git Bash, `\n` and `\b` inside a Python heredoc become real characters and break string
  literals and regexes. Write code with a file-writing tool, or patch with a script file.

**Long-form and Resolve**
- **Duplicate, never rebuild.** The first test's clean cut had two transitions (mTuber "Bounce" and "Through
  Screen") and whoosh sounds the user had added after the foundation cut. A rebuild from source ranges would have
  dropped them silently. `timeline duplicate` keeps everything.
- **Transitions change the structure dump:** a clip next to a transition reports its handle in its video source
  range (record 322 frames, source 344), the transition itself is a V1 item with no media, and V1 "overlaps" appear.
  What plays at record frame n is still `source_start + (n - record_start)`. Words said inside a handle are not
  heard; drop them. Never plan a beat across the transition.
- **Frames matter more than seconds:** snap every t0/t1 to the frame grid (`round(t*fps)/fps`); the beat's clip is
  exactly `t1 - t0` frames and lands exactly on `round(t0*fps)`.
- **The webcam PiP is part of the continuity.** Every zoom and every screen-scene graphic pastes the same frame's PiP
  back where V1 has it, with a rounded mask (inset 3 px, radius 5.6% of the width) so none of the screen behind
  its corners comes along. On the white world it also gets the spec shadow.
- **Zooms near the webcam:** the held-still PiP covers part of the zoomed view. Frame the target outside
  `look.py`'s red box. The source PiP area is inpainted once per V1 item so a zoomed view never shows a second face.
  That patch must stay under the held-still PiP, or the smudge shows. For a top-right PiP whose left edge is Xp and
  bottom edge Yp (source px, UHD), a zoom of k centred on fx,fy is safe when fx <= Xp - (Xp - 1920)/k and
  fy >= Yp - (Yp - 1080)/k (openai-dots: Xp 3074, Yp 1171). Outside that, move the target or skip the zoom.
- **Colour exactness:** zoom renders work on the source's own YUV planes and encode with the source's tags - a frame
  at rest is bit-identical to V1, so the cut in is invisible. ffmpeg's default YUV->RGB is bt601: never use it for
  footage that sits next to V1.
- **Windows pipes:** a default subprocess pipe moved raw 4K frames at 4 fps; a 64 MB pipe (`_winapi.CreatePipe`)
  did 16x better. Measure the pipe before blaming the encoder. The shorts skill found the other half of the story:
  Python's *buffered* reader is the slow part (`bufsize=10**8` read at 130 MB/s, the default or an unbuffered
  `readinto` at 1.6 GB/s). `media.py` reads unbuffered; never add `bufsize=` to a frame pipe.
- **HyperFrames workers are tabs of one Chrome by default** (`PRODUCER_ENABLE_BROWSER_POOL=true`), and that browser's
  single GPU process encodes every screenshot: more `--workers` barely helps. `render_gfx.sh` exports
  `PRODUCER_ENABLE_BROWSER_POOL=false` (one Chrome per worker) and captures lossless PNG frames
  (`--format png-sequence`); the MP4 path captures JPEG at quality 95, which measured 48.6 dB against the lossless
  frame on the cubefarm g03 beat (no right-edge strip at 3840 px, unlike the shorts' 1080 px). At 4K the PNG encode
  inside each Chrome is the cost: 8 workers captured g03 (1,349 frames) in 70 s, 12 in 62 s, 16 in 80 s, so 12 is
  the default and the script throttles to RENDER_SLOTS x HF_WORKERS browsers machine-wide. The old MP4 path took
  88 s in total and JPEG capture with 16 separate browsers 100 s: lossless is also fastest. The tmix output is NVENC
  lossless when an NVIDIA encoder exists (11 s vs 16 s for x264 crf 10 slow on g03, zero generation loss, same
  decode speed).
- **The matte on the GPU:** `hyperframes remove-background --device cuda` can't use CUDA on Windows (its
  onnxruntime-node build lacks it) and runs the CPU at 2-3 fps. `matte_gpu.py` runs the same cached u2net model on
  onnxruntime-gpu with the shorts' speaker-only cleanup (a horizontal opening drops thin strips that touch the
  head, then the largest blob is kept - the guitar-headstock case from the first test), lossless FFV1 out.
  `compose.py --matte` uses it and falls back to the CLI by itself.
- **Frames are pure functions of a small state.** The keyword pop and CTA overlays are drawn once per distinct
  state (landing progress, typed characters, caret, press) and written into a persistent transparent 4K frame as
  their own box; the split blend runs only on the columns right of the card's shadow. Both are pixel-identical to
  the per-frame code they replaced. Previews seek straight to the wanted frames instead of decoding the beat up to
  them - except the source footage, which `media.decode_at` decodes from the start of its contiguous run: a time
  seek to a single frame of an OBS recording (millisecond timestamps) lands one frame late, so a seeked still is
  not the frame the render uses. (`look.py` and `assets.py still` keep the direct seek: they are for looking and
  for assets, not frame-locked.) The PiP inpaint patch of a zoom is made from the beat's first zoomed frame of the
  V1 item, in renders and previews alike; with one process per beat, two beats on the same item no longer share
  whichever patch came first.
- **NVENC for intermediates:** Resolve re-encodes on delivery, so zoom and graphic clips use NVENC (cq 15) when
  available. x264 `-preset fast -crf 12` is the fallback.
- **GPU decode per seek is slower:** one CUDA context per short seek (scene sampling) cost more than it saved. Use
  it only for long sequential decodes, if at all.
- **Scenes:** OBS recordings switch between a full-frame camera and screen + PiP inside one file. Classify per item
  from 3+ samples (big centred face = camera). The PiP window edge scan can run off on some files; a consensus
  across files fixes it.
- **Punch-in framing:** YuNet face boxes put the eyes ~32% down the box. Put them on ~36% of the frame height.
  Resolve: zoom about the centre, Pan +right, Tilt +up, timeline pixels (measured).
- **Split scale:** a portrait webcam (the PiP) is narrower than the camera card. Scale it to cover the card when the
  whole face still fits (chin above y 1000) instead of filling strips with blur; limit the pop-out above the card to
  a band around the head.
- **Matting limits:** the salient-object matte can include an object touching the hair (a guitar headstock). Check
  the full-resolution split frame; choose a different beat for the split if it's distracting.
- **Mark rects:** `box` and `band` add 8 layout px of padding around the rect. Leave room, or the band grazes the
  next row (it did on the first benchmark zoom).
- **CTA URLs:** a long URL ran under the CTA button. `overlay.py` now shrinks the URL font (44 down to 30 px) until
  the whole URL fits left of the button.
- **Captions:** convert "five point five" to "5.5" and apply phrase fixes on the WORDS before cutting cues, or a
  number splits across two cues. Hotword mishearings ("agent-decoding", "Gentic Labs") go in `caption_fixes`.
- **Markers:** one per frame. A duplicated clean cut brings its own review markers (frame 0 was taken).
- **Levels:** the user's voice sat at -25.7 LUFS. The added layers are levelled against the voice, so the final
  -14 LUFS is one normalisation on delivery; don't touch A1.
- **The machine is shared:** the user may be rendering something else (a shorts session was compositing during the
  first test). Timings vary; keep parallelism reasonable and never touch processes you didn't start.

**Censoring private details** (openai-dots, 2026-10-01: a chat message with private business details, on screen
for two minutes while the chat scrolled)
- **Match words, trace the block.** Templates of the sensitive words, cut from one full-resolution reference frame
  and matched at half resolution (normalised cross-correlation), followed the message through reflowed lines,
  scrolling and dimming. The blur shape is a flood of the bubble's own flat colour from each hit, so it hugs the
  bubble, and a popup drawn over it (its own colour and border) stays sharp.
- **No pre-roll before the first detection.** The block fades in where the chat has just jumped, so a mask held back
  from later frames blurred the wrong bubbles. The faintest first frame is already detected; bridge gaps only
  between detections inside one V1 item.
- **Zooms carry their own blur.** An overlay can't follow a camera move, so `zoom.py` bakes the censor into the
  source planes before the move (from `censor/<id>_track.json`), and `censor.py render` leaves the overlay clear
  over zoom clips. Track before rendering any zoom inside the beat.
- **Transitions can't be followed from the source.** Render the transition's frames out of Resolve and let
  `censor.py transition` register each one against the last clean frame (ECC, affine), warp the mask onto it and
  widen it by the frame's motion. Check the incoming side by eye.
- **Scan the whole programme.** The same words can show up outside the beat (a notification, a later scroll back).
  `censor.py scan --gpu` decodes on NVDEC: CPU decoding of 4K for a full scan would starve the renders beside it.
- **Reference frames:** `censor.py ref` is frame-exact. The first reference was cut with a direct seek and came out
  one frame late (see "Frames are pure functions" above); harmless for matching, but measure boxes on the exact frame.

## User feedback log
Add the user's reactions to each edit here so the rules keep improving.
- 2026-09-30, Sonnet 5.5 vs Opus 5.5 vs Fable 5.1 (test build "YTHD60 - Pro Edit TEST", hook + two body beats):
  the brief - music only under the hook and faded out right after it; the body restrained but with zooms,
  highlights, real sources and SFX. After watching the first 40 s in Resolve: "the edit was really good" - keep
  this hook treatment (two screen zooms with marks, a punch-in with one keyword pop, an fvp graphic, a split, the
  riser into the join). Body pacing not reviewed yet (only two sample beats were built).
