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
- **Colour exactness:** zoom renders work on the source's own YUV planes and encode with the source's tags - a frame
  at rest is bit-identical to V1, so the cut in is invisible. ffmpeg's default YUV->RGB is bt601: never use it for
  footage that sits next to V1.
- **Windows pipes:** a default subprocess pipe moved raw 4K frames at 4 fps; a 64 MB pipe (`_winapi.CreatePipe`)
  did 16x better. Measure the pipe before blaming the encoder.
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
- **Captions:** convert "five point five" to "5.5" and apply phrase fixes on the WORDS before cutting cues, or a
  number splits across two cues. Hotword mishearings ("agent-decoding", "Gentic Labs") go in `caption_fixes`.
- **Markers:** one per frame. A duplicated clean cut brings its own review markers (frame 0 was taken).
- **Levels:** the user's voice sat at -25.7 LUFS. The added layers are levelled against the voice, so the final
  -14 LUFS is one normalisation on delivery; don't touch A1.
- **The machine is shared:** the user may be rendering something else (a shorts session was compositing during the
  first test). Timings vary; keep parallelism reasonable and never touch processes you didn't start.

## User feedback log
Add the user's reactions to each edit here so the rules keep improving.
- 2026-09-30, Sonnet 5.5 vs Opus 5.5 vs Fable 5.1 (test build "YTHD60 - Pro Edit TEST", hook + two body beats):
  the brief - music only under the hook and faded out right after it; the body restrained but with zooms,
  highlights, real sources and SFX. After watching the first 40 s in Resolve: "the edit was really good" - keep
  this hook treatment (two screen zooms with marks, a punch-in with one keyword pop, an fvp graphic, a split, the
  riser into the join). Body pacing not reviewed yet (only two sample beats were built).
