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

**Slide-deck talks** (ai-practitioners-summit, 2026-10-06: a 37-minute conference talk, 383 V1 items, mostly the
speaker's own dark slides plus GitHub/VS Code screens, webcam PiP top-right)
- **Check the PiP window by eye when scenes.py says "consensus".** Every file's edge scan ran off and the consensus
  came out 702x1008, but the real webcam was 704x950 (a one-column scan down x 3500 shows the PiP's bottom edge as a
  step to the flat background at y 957). A window that is too tall pastes a strip of unzoomed screen under the
  webcam in every zoom. Patch `files.*.pip` and `items.*.pip` in scenes.json before rendering anything.
- **A zoom can stay in one 'screen' scene and still cross a content change.** A V1 cut from a slide to a GitHub page
  is "screen -> screen", so the scene check passes. Look at a frame just after every V1 cut inside a beat
  (`look.py`) - four beats here ran onto a different page (a slide -> the repo listing, an agent panel closing, a
  "custom harnesses" slide -> a terminal). End the beat on the cut, or plan it on the new page.
- **An instant punch-in on a cut is `cam0`, not a `dur: 0` move at t 0.** The move version motion-blurs frame 0
  (the shutter samples the k = 1 state before it). `cam0: {fx, fy, k}` starts the clip at the tighter framing.
- **Read along with the slide.** On a talk built from the speaker's own slides, the strongest body beat is a zoom
  that follows the narration through the slide's rows - a box on each card or row as it is named, a band on the line
  being read - then pulls back before the next V1 item continues the same slide. 62 such zooms in 37 minutes read as
  calm, not busy, because each one only moves on a cue word.
- **Don't add a CTA card for something already on screen.** When the speaker says "install it with npx cubefarm" over
  the README's Get started block, zoom on the real line instead of typing the same command into a card.
- **Resources that criticise:** when the speaker is critical of a site ("the same one or two names, for the silliest
  of things"), show the site but crop it so no person's or publisher's name is readable.
- **Numbers in caption fixes:** the "five point five" -> "5.5" merge runs in the same pass as `caption_fixes`, so a
  phrase fix must use the spoken words ("Opus five point five": "Opus 5.5") to keep the name and number in one cue.
- **Removed beats leave event files behind.** `audio.py` now places SFX only for beats in the plan; before that fix, a
  CTA replaced by a zoom still got its pop, key ticks and click.
- **The user's own markers:** a duplicated timeline may carry the editor's markers on chapter-like frames; `place.py
  ids --existing-markers` nudges chapter markers one frame off them. Leave the user's markers alone.

**Explainer-heavy talks** (harness-engineering, 2026-10-13: a 16-minute theory video, 128 V1 items, slides + a VS Code
demo + browser sources, webcam PiP that MOVES between OBS scenes inside one file)
- **The PiP can change corners inside one file.** 5.mkv had the webcam top-right on the slides and bottom-left in the VS
  Code scene; `scenes.py` keeps one window per file, so its edge scan failed and the consensus was wrong for 24 items.
  Detect the corner per item (colourfulness of the two corner patches over 2 fps samples) and store `items.<v1>.pip`;
  the work-dir copies of zoom.py / compose.py / look.py were patched to prefer the item's window. Graphics on those
  items mirror the fvp layout (anchor [1136, 540], capture frame at x 416).
- **Scan the cut for flash frames.** The user's cut ended an item on 22 frames of another app window (a 0.37 s flash).
  A head/tail scan of every item (96x54 grey, frame diffs > 12) plus a frame-exact look found it; `patch_flash.py` holds
  the last clean screen and pastes the live PiP back each frame on PE Graphics - V1 stays untouched.
- **Overlapping SFX need more lanes.** Typing runs and pops from busy graphics overlap; one SFX track silently drops
  the later clip in Resolve. place.py spreads SFX greedily over "PE SFX", "PE SFX 2" and "PE SFX 3" (with the
  library's auto highlights and dings, two lanes still dropped 2 of 210 sounds; three dropped none).
- **Write edit_plan.json atomically.** A plan rewrite while overlay.py read it failed one beat (StopIteration).
- **Two long-lived graphics agents beat many small ones** (the user's preference: small agents burn tokens). One per
  half of the video, each with a written brief (beats, cue words with times, real assets to use, the PiP rules) and
  its own `gfx_<name>.py`; research findings are relayed to them by message as they land.
- **Explainers that worked:** a continuous "world" split over two beats (the software-factory swarm, g20 -> g21, one
  timeline function with an offset - the cut between them is invisible); true-scale bars for token budgets; the
  speaker's own slide icons rebuilt in CSS so the B-roll matches the slides; real watch pages / thumbnails for every
  "check out my video on ...".
- **Fact check feeds the graphics.** "A hook masks the prompt" is not what Claude Code settings hooks can do (block or
  add context only); the graphic showed a mod-style handler instead. Relay accuracy notes to graphics agents early.
- **Chrome (outside the Claude app) can't write into the app's virtualised AppData.** Re-capturing a page with the
  system Chrome needed a temp folder next to the media, then a copy into `captures/`.

- **Match the channel brand, not a generic style.** Leon's slides are built from his "Leon YouTube" design system
  (bundled in references/design-system/: tokens/colors.css, typography.css, elevation.css, radii.css and the
  component prompts). Overlays that sit on his footage (keyword pops; next: CTA cards, zoom marks) take its graphite
  glass, Figtree / Geist Mono and azure/ember accents. The keyword pop design is locked in editing-spec.md section 3.
- **Split mattes: RVM, not u2net.** u2net's salient-object matte is a soft low-res blob that swallowed the guitar behind
  his head on and off (flicker at the ear). Robust Video Matting (matte_rvm.py, ResNet-50 ONNX, ratio 0.4, warmed-up
  recurrent state) follows hair strands and leaves objects touching the head in the background. A guided filter and a
  background-plate difference key were tried first and failed (a light ghost of the guitar edge; the plate never saw
  the wall behind the hair). On Windows, onnxruntime-gpu needs the nvidia-*-cu12 wheels' bin dirs added to the DLL
  path (matte_gpu.py and matte_rvm.py do it) or cuDNN fails to load.

- **Restyle by re-rendering, then swap in bulk.** The brand pass re-rendered 34 zooms and 27 graphics under `--tag brand`
  and swapped all 61 with one `script_plugin run_inline` (Python: walk the media pool, `ReplaceClip(path)` on each id
  from import_result.json, `SaveProject()`) - seconds instead of 61 MCP round trips. Keep the old renders until the
  user signs off.
- **A rebuilt audio layer goes on new tracks.** Library SFX, auto highlight/ding/whoosh/sting events and a new music
  file move and change every sound, so replace_clip can't do it: `place_audio_swap.py` plans "PE SFX v2" ... tracks,
  one append_to_timeline of 212 rows (the reply overflowed the tool output and was saved to a file - parse it), then
  the old PE audio tracks are disabled and renamed "(old)". If only the music changes (same length), re-render it under
  a new tag and replace_clip the one music clip.
- **Generated hook music: the level matters as much as the track.** ACE-Step 1.5 XL (music_gen.py, MIT, ~15 s a
  90 s take on the 5090 once loaded) wrote four "inspirational" candidates; the pick sat 18 LU under the hook's voice
  and ducked another ~5 dB under speech - barely there. 15 LU under (`music.under_voice_lu: 15`) let the lift read.
  Generate 60-90 s, cut where the lift lands (`file_offset`), keep the alternatives for the user.
- **`timeline_frame capture` can hang.** One call blocked for 30 minutes (Resolve on the Edit page with a long
  timeline). Prefer a review render through the scripting API (`run_inline`: LoadRenderPreset 'YouTube - 1080p',
  SetCurrentRenderFormatAndCodec('mp4', 'H264_NVIDIA'), SetRenderSettings TargetDir/CustomName/FormatWidth/Height,
  AddRenderJob, StartRendering - it returns at once; poll GetRenderJobStatus) and decode frames from the file.
  SetRenderSettings returns False if any one key is rejected ('VideoQuality' as a number was) but applies the rest -
  read the job back with GetRenderJobList. Frame captures also reset the Deliver page's format to JPEG.

- **No sponsor that isn't this video's sponsor.** The swarm graphic named the worker pool "Upstash Box" with its
  logo, because the speaker's software-factory skill runs on it; Upstash had sponsored an earlier video, not this one,
  and Leon had it replaced with "Agent Swarm" before release. Brand names in explainers only when the speaker names
  them; a sandbox / hosting / tooling vendor he doesn't mention stays generic. Captured pages (watch pages, READMEs)
  may carry sponsor lines in descriptions: crop or frame them out.

**Scripted sponsor reads** (tripleten-midroll, 2026-10-15: a 94 s sponsor midroll read from a script, OBS screen + PiP)
- **When the speaker is reading the script, drop the webcam.** Items where V1 shows the script itself (a Google Doc) were
  recorded with Leon looking down at it, expecting full-screen text. He asked for g04 (planned as a split) and then g03
  (fvp) to be full-frame `fv` with no PiP: "you should not show my webcam there at all... it was like that in the script
  as well." Check the PiP on every item that shows the script / notes; plan those beats `fv`.
- **Cover any frame that shows the script.** Look for the script doc in scenes (it was 9 s of the hook here).
- **Fact-check the sponsor's claims too.** "Around two hundred practicing engineers" was on no TripleTen page; the graphic
  showed the community without a number and the report flagged it. A line the script had but the recording lacked
  (instructor employers) was true for one instructor only - show it on the one it's true for.
- **A lower third the script asks for** works as a body keyword chip with a label; place it clear of the page's own
  headline (the homepage headline sat bottom-left, so the chip moved right to xy 1450,905).
- **Long chip eyebrows:** a label wider than the words overflowed the chip - overlay.py now sizes the chip to the wider
  of the two.
- **Split from a PiP:** compose.py's automatic scale (card width only) left a fill band at the bottom; the agent set the
  scale in `split/<id>_geom.json` (2.2). geometry() should check bottom coverage too.
- **music_gen.py can fail with "Insufficient KV cache"** when another app holds GPU memory (LM Studio / ComfyUI were open).
  Check `nvidia-smi`, wait, retry - never touch the other processes.
- **AppData is virtualised for the app** (`...\Packages\Claude_...\LocalCache\Local\...`): W lives there; M must stay
  next to the sources so Resolve sees the files.
- **A midroll's publishing copy** is a sponsor block for the host video (the program and audit links), not a title or
  chapters; chapters on a midroll are section markers only.

**Restructuring a cut: inserted footage, a PiP intro, a montage** (last-call, 2026-10-16: the user asked for the intro
as a corner PiP over a game capture, a gameplay montage of listed clips, the full gameplay at the end, and repetition trims)
- **The MCP can't move or trim placed clips, so a re-structured cut is a NEW V1/A1 timeline** ("<base> - Recut vN") built
  with one `AppendToTimeline` from the base's source ranges, with the gaps left open for inserted footage. That's safe only
  when the base has no grades, transforms, transitions or titles: check every V1 item's properties and node count first.
  Verify the build item for item, then duplicate it as the Pro Edit and continue as usual.
- **Count the user's list back before building.** I silently dropped one of six montage clips because the intro already
  showed it, and inserting 14 s afterwards meant a Recut v2, shifting program.json/voice48.wav/rms/transcript and every
  beat after the gap (`shift_v2.py`), and a second Pro Edit. If a requested item seems redundant, keep it and say why
  in the report.
- **Swap program.json and edit_plan.json together, and never while renders read them.** A plan rewrite mid-render
  failed one overlay (StopIteration). Tell the graphics agents first; beat-relative cues (`words()`/`W()`) survive a shift.
- **Game or demo audio is levelled per clip, not per montage.** The listed clips ranged -35 to -27 LUFS raw; each was
  levelled to the voice's loudness, with 0.12 s equal-power crossfades at the cuts and a -1 dBFS limiter. An "extremely
  low" bed under speech sat ~22 LU under the intro's voice, ducked further under words.
- **Speaker PiP from the full-frame camera:** crop the camera to the same face size and position as the screen
  recordings' webcam window (YuNet on both), round it like the OBS window, ProRes 4444 with alpha on its own track
  above the graphics, so intro graphics play under the card.
- **Screen-capture artifacts in a supplied clip** (a browser "sharing your screen" bar in the letterbox) get a static
  black mask on the overlay track wherever that stretch plays.
- **A rebuilt Recut drops the user's whole audio setup, and the API can't see it.** Fairlight track FX (voice EQ, Voice
  Isolation, de-esser, dynamics), track faders, fader automation and clip volumes live on the base timeline's tracks;
  `AppendToTimeline` onto a new timeline carries the clips only. On last-call the mix was balanced against the raw voice,
  the user's chain later added +2.8 dB to it, and every level after that was chasing the difference - "the main
  timeline had important layers and effects ... that's what's causing a lot of these frustrations". Before a rebuild:
  tell the user it will drop their voice chain and track levels, have them copy the chain onto the Recut's A1 first
  (or keep the base and only add tracks when no restructure is needed), confirm it with the voice-chain check
  (pipeline.md 9a), and mix against a render THROUGH that chain.
- **Green Fairlight faders are fader automation in Read** (they snap back when moved; typed values in the track header
  revert). The last-call Pro Edit had -14 dB automation on PE SFX and PE Riser (PE SFX 2 was at 0) from before the AI
  Audio Assistant ran - most SFX sat 14 dB under their targets and no render check caught it. `master.py fit` (least
  squares of Resolve's rendered mix against the base stem and the rebuilt layers) shows every track's real gain in
  one run: "A3 PE SFX x -14.05 dB, A4 PE Riser x -14.10 dB". Resolve's AI Audio Assistant and Deliver's loudness
  normalisation both made this mix worse; neither is part of the delivery.
- **Master outside Resolve, always - it is now the delivery step** (pipeline.md section 9, `master.py` + `rs_*.py`;
  the user asked for it on 2026-10-16: "the final result is ... the final video that's already been mixed for
  YouTube, and I can just grab the file and upload it"). How last-call's final file was made and what each piece
  guards against:
  - the voice stem rendered through the user's own A1 chain (`rs_stem.py` disables the other tracks' CLIPS -
    audio track enables are ignored by renders on 21.1 - lossless through the "Audio Only" preset);
  - the PE tracks rebuilt sample-accurately from their files (`rs_items.py` + `master.py layers`);
  - the voice stem set back to the RAW voice's speaking loudness: every layer was levelled against the raw voice,
    so the balance comes out exactly as designed (every SFX type within 0.1 LU of its target on last-call; the
    automatic gain, -5.65 dB, matched the -5.56 dB I had fitted by hand);
  - a 4x-oversampled true-peak limiter to -14.0 LUFS at -1.5 dBTP; the AAC encode still pushed one game transient
    to -0.1 dBTP, so `deliver` dips each overshoot by its excess + 0.3 dB over 0.5 s and re-muxes until none is left;
  - sync checked on the picture's own audio decoded IN FULL: ffmpeg's fast seek (-ss before -i) on AAC is off by up
    to ~20 samples, which read as a false 15-23 sample sync error;
  - `master.py chain` tells a processed voice from a raw one by fitting the stem to its own media (Pro Edit v2's
    voice: unexplained -8.4 dB, bands +7.9 to +11.8 dB = PROCESSED; raw against itself = RAW).
- **Measure loudness the way the levels were set.** `sfxlib` measures the mono sum; pyloudnorm sums the stereo
  channels, which reads 3 dB louder on dual-mono sounds. Mixing the two made every SFX look 3 LU "too loud".
- **Files Resolve writes under AppData are invisible to this app** (a packaged app's AppData writes are virtualised:
  a folder it creates there doesn't see what Resolve rendered next to it). Everything Resolve renders for delivery
  goes to `$M/_deliver/`, next to the sources, like the rest of `M`.

**Camera items under B-roll, and the webcam window's edges** (opencode-2.0, 2026-10-19: a 15-minute OpenCode 2.0
tutorial, user-cut YTHD60 used as the clean cut, 214 screen items + 3 full-frame camera items, all in the hook)
- **"Add explainer B-roll instead and show my camera in the corner"** over full-frame camera items: compose mode `fvc`
  (layout `fvc` in the plan, CFG `mode='fvp'` in the graphic). `cam_corner()` finds the PiP's face size/position on the
  screen items (YuNet) and crops the camera once per beat so his face matches the webcam elsewhere; cached in
  `split/<id>_cc.json` - delete it after changing the PiP window.
- **Check the webcam window's bottom edge on a terminal frame.** The consensus window ended 18 source px below the real
  webcam (y 990 vs 972): invisible on dark app scenes, but every zoom and fvp graphic pasted a strip of terminal text
  under the webcam. A full-resolution crop of x 3050-3840, y 880-1030 on a TUI frame shows it at once. Then match the
  corner radius too (`pip_radius` 0.066 for a 702 px window here): a smaller mask left white crescents at the PiP's
  bottom corners over light pages.
- **Duplicate first, then prove the voice chain before adding anything.** Leon asked mid-run: "there are important
  effects on the vocals on the first track ... if you use your own timeline, the audio mix is going to be completely off."
  Duplicate, then render the same 30 s of A1 from both timelines (`rs_stem.py`, KEEP [1]) and null-test them: -81 dBFS
  on a normal stretch. Voice Isolation renders a little differently each pass (two renders of the ORIGINAL differ by
  -50 dB over ~1.5 s too), so compare against a second render of the original before calling a difference a lost chain.
- **`master.py fit` +8 dB on every PE track** while the user's voice chain also lifts the raw voice by ~+11 dB: gain on
  the user's bus/chain that applies to everything, so the balance in Resolve still matches the master. Report it, don't
  "fix" it.
- **Graphics agents draw too small at first.** Both agents' first drafts had UI text well under 22 layout px with most
  of the stage empty; one message ("fill x 64-1504, UI text 26-40 px, code 24+") fixed it. Say it in the brief.
- **`media_pool safe_import_media` returns the ids inline** (a 111-file reply is too long to save by hand): dump the
  bin's clips with a `run_inline` (`GetClipList` -> name, `GetUniqueId`, 'File Path') into import_result.json instead.

**A sponsor integration carried by B-roll and a phone demo** (blotato-integration, 2026-10-22: an 87 s mid-roll, 17
full-frame camera items + 2 Claude screen items; extra sources: a 4K browser B-roll recording and a vertical phone
screen recording of the Instagram demo)
- **Mostly-camera reads: cover them with `fvc` B-roll.** 12 of 15 beats were graphics with the camera in the webcam
  corner (real homepage, real Claude connector menu, real pricing page, the phone), so about 85% of the runtime showed
  something while Leon stayed on screen. Separate B-roll files go into graphics as `videos=[...]` cards; cut them with
  ffmpeg (60 fps CFR, the beat's exact frame count) - `assets.py clip` only follows V1.
- **A vertical phone recording works as one shared phone object** (screen 434x940 layout px at rest, 12 px bezel,
  radius 64) with the world camera pushing 1.6-2.0x onto the bubble being talked about. Retime it so each tap / message
  lands on its cue word. **Phone screen recordings are VFR**: a still screen sends no frames for up to 0.5 s, so
  `-ss`/`setpts` retimes landed events up to 0.18 s early - map by each frame's real timestamp. Paint out the
  screen-record pill in the status bar.
- **A faithful UI mock when the real thing doesn't exist** ("a tonne of comments" Leon never had): build it inside the
  real recording's chrome - status bar, emoji row, input bar and nav bar cropped from his own phone frames, the real
  reel playing on top, rows measured off a real frame (Roboto from the user's fonts, Android Noto emoji), fictional
  handles, letter / default avatars, no faces. One world function drives the flood (hook) and the payoff callback
  (body: the sponsor's real auto-reply landing under every comment).
- **Removing a phrase from the user's cut without losing the voice chain:** do it IN PLACE on the duplicate, never a
  rebuild. `DeleteClips([v, a], False)` -> `AppendToTimeline` the new pieces (endFrame is EXCLUSIVE on 21.1, both
  tracks when mediaType is omitted) -> append a filler of exactly the leftover gap -> `DeleteClips(filler, True)`
  (native ripple: every later clip moves, nothing is re-created) -> `CopyGrades` from a neighbour. Then re-map in a
  staging dir (`_remap/`: prepare/transcribe/program/scenes reuse the audio and transcription caches) and swap
  program.json, scenes.json, edit_plan.json and the overlays' ABSOLUTE event files (`events/*.json`) at once, after
  telling the graphics agents to hold compose. Zoom and HyperFrames renders stay valid (same source frames,
  beat-relative cues); composites must be redone.
- **When the words run together, find another take.** "reel or a TikTok" had no gap after "reel"; a cut there clips the
  word. Transcribing the raw recording around the used take found a retake ending cleanly on "reel," - spliced in.
- **The sponsor's capabilities limit the script.** Research found Blotato's comment/DM automations are Instagram and
  Facebook only; Leon cut "or a TikTok or a short" when told. Surface that kind of finding to the user at once.
- **No bright sounds, not just no dings** (Leon, 2026-10-22: "no bells or dings ... pops and swipes are fine", then "the
  notification ping would be fine - the only exception"). Besides `exclude_types` ding/chime, plan `sfx_prefer` limited
  stings to sub_hit / hit_minimal, highlights to paper_swish / marker_underline (the marker strokes centre at ~10 kHz),
  whooshes to wind_sweep / air_full / air_short / deep_low, notification to chat_ping (triple_ping is a three-note
  E6-G6-C7 chime). The work-dir sfxlib was patched so a category in `sfx_prefer` plays ONLY the listed files (the
  skill's sfxlib still rotates the rest in after them) - adopt that if it holds up.
- **No hook music** is now a plan switch: `"music": {"off": true}` (audio.py writes no music clip, place.py adds no
  PE Music track). The riser and the sting stay.
- **In/Out marks survive one clear:** a RANGE stem render left `out 5223` on BOTH timelines although rs_stem.py had
  cleared it - Resolve re-sets the range just after the job ends. rs_stem.py now clears, waits a second and checks, up
  to five times. After any in-Resolve render, read `GetMarkInOut()` on every timeline it touched.

## User feedback log
Add the user's reactions to each edit here so the rules keep improving.
- 2026-09-30, Sonnet 5.5 vs Opus 5.5 vs Fable 5.1 (test build "YTHD60 - Pro Edit TEST", hook + two body beats):
  the brief - music only under the hook and faded out right after it; the body restrained but with zooms,
  highlights, real sources and SFX. After watching the first 40 s in Resolve: "the edit was really good" - keep
  this hook treatment (two screen zooms with marks, a punch-in with one keyword pop, an fvp graphic, a split, the
  riser into the join). Body pacing not reviewed yet (only two sample beats were built).
- 2026-10-06, AI Practitioners Summit talk ("YTHD60 - Pro Edit v1", 37 min): the brief - "the video has already been
  cut, so do not cut it any further; the length is perfect ... make this look a bit more polished, as if a
  professional video editor worked on this." Reused the current timeline as the clean cut (no foundation cut, no
  re-cut, nothing on V1/A1 changed but one punch-in). Reaction to the result: not given yet.
- 2026-10-13, Harness Engineering ("YTHD60 - Pro Edit v1", 16 min): the brief - lots of theory without on-screen
  visuals, so "think like a professional video editor and add B-roll" wherever it drags: visualisations of how things
  work (the software factory swarm, task ingestion and allocation), real articles with highlighted text, screenshots
  of his own YouTube videos, official logos; don't re-cut. Built with 27 graphics and 34 zooms (far denser than the
  default body). Mid-run feedback: "doing a really good job so far"; prefers few long-lived subagents over many small
  ones; fixed the Skool page's wrong weekday after the fact check flagged it. Reaction to the finished timeline: not
  given yet.
  Follow-up the same day: the split's head pop-out "glitchy around my ear" (u2net grabbing the guitar) -> RVM matte;
  hook music "very boring, go for something more inspirational" -> a generated track (music_gen.py); SFX "bland and
  generic" -> a royalty-free sample library with highlight swishes, dings, whooshes and stings; keyword pops: the
  yellow serif "not professional for a tech channel", a white chip "not sure it matches the channel brand", then the
  graphite-glass chip from his design system: "Now that looks cool. Lock in that design."
  After the brand pass, the RVM split, the library SFX and the generated hook music (ACE-Step cand_1, 15 LU under the
  voice), watching the 1080p review render: "Wow, this looks next level. The masking around my hair is fixed. Editing
  seems polished, sound effects seem better and the music sounds cool." - this is the baseline for the next edit.
  Then, listening to all four music takes on their own, he swapped my pick (cand_1, indie electronic with guitar and
  marimba) for **cand_3, uplifting cinematic piano + staccato strings + steady drums**: "That's the one!" - now the
  default hook style in editing-spec.md section 6. Send the user every take as MP3s, not just the pick.
  Final verdict on this edit: "really, really professional-looking ... a massive step up from the types of edits you
  did with the same skill previously. The sound effects, the zooms, and the styles ... very cool." What made the
  difference, keep doing it: everything styled from the channel's own design system, B-roll wherever theory drags,
  real recorded SFX placed on every visual event, generated music chosen by the user, RVM for the head pop-out.
- 2026-10-15, TripleTen sponsor midroll ("YTHD60 - Pro Edit v1", 1:34): the brief - "make this look way more polished"
  after approving the clean cut ("you did a really good job"). Mid-run: "Please do not include music. No, wait. Ignore
  that. Add music" (kept hook music); no webcam on the script-reading lines (g03, g04 -> fv). Built with 9 zooms, 8
  graphics, 4 chips, 2 punch-ins, 59 SFX. Reaction to the finished timeline: not given yet.
- 2026-10-16, Harness Engineering, after release: retention "higher than my previous videos by a long shot", but a
  viewer wrote "the new sounds effects get annoying fast - ding, scribble, ding, ding, ding". Measured on the edit:
  12.6 sounds a minute in the body with no music under it, 35 dings (every box mark) and 31 scribbles (every
  highlight), 25 stretches with 4+ of them in 20 s, 97% landing on words. Peak-based levels put chimes ~2 LU and
  dings / pops / scribbles ~8 LU under the voice after the bus (the main-bus compressor lifted the effects ~4.5 dB;
  my earlier note that it kept the balance was wrong). An A/B/C on two 90 s stretches, with the bus emulated from the
  upload (0.98 correlation): B (8.2 a minute, dings 11, pops 31, quieter) "overcorrected slightly - I would have
  expected sound effects on some of those animations"; C (10.5 a minute, every animation keeps its pops, 20 dings
  15 s apart, scribbles quieter and tamed) "way better ... not too distracting ... not too dense". C is the default
  now (sfxlib LONGFORM_RULES / LONGFORM_TARGET). The lesson: trim the repeated accents, never the animation sounds;
  and measure what the viewer hears (after the bus), not what the files say.
- 2026-10-16, Last Call (cozy horror game build, "YTHD60 - Pro Edit v2", 25 min incl. a 9-min playthrough): the brief -
  intro as a corner PiP over the uncut game intro (game audio extremely low), a montage of six listed gameplay clips
  with game audio, the full gameplay faded in at the end, 10-step roadmap B-roll, optional hook B-roll, no Hostinger
  before step 10, trim repetition, level game audio against the voice. Built with 24 zooms, 27 graphics (roadmap system
  s01-s10), 3 chips, 2 CTAs, no hook music. Reviewing it, the user trimmed the intro montage ("the intro felt too
  long"), caught a clipped badge and highlight boxes that outlived their dropdowns (end a mark 0.35 s before the screen
  under it changes - its fade-out takes 0.3 s). The audio went badly: the Recut had none of the user's voice chain
  (see "Restructuring a cut"), clips I rebuilt lost their volumes (a demo clip clipped), a Bus 1 limiter the user
  added never reached the render, Resolve's AI Audio Assistant mangled the game music and Deliver's normalisation left
  the upload "very soft". The user's verdict on the approach: editing a clone without their effects "seems like a
  major approach issue". Fixed by mastering outside Resolve (above). Lesson: the user's audio chain is part of the
  timeline - carry it over or have it carried over before any levelling, and measure every render against its stems.
  Then: the final file (H.264 at 97 Mb/s, 18 GB) took "an incredibly long time to upload" and the project left ~63 GB
  on disk ("absolutely enormous"). Now the picture uses the user's own "YouTube - 2160p" preset (~11 Mb/s, ~2 GB for
  25 min - what their own exports measure), and a cleanup step deletes everything once the user confirms the upload
  (`cleanup.py`, pipeline.md section 10).
  After the upload, on the externally mastered file (-14.01 LUFS, -1.18 dBTP): "the render, although large, sounds
  awesome on YouTube. You did an incredible job." The cleanup then freed 69.3 GB. Keep for the next edit: the master
  built outside Resolve against the user's own voice chain, SFX on their LONGFORM targets, the YouTube 2160p preset,
  and the cleanup on their go-ahead.
- 2026-10-19, OpenCode 2.0 ("YTHD60 - Pro Edit v1", 14:54): the brief - "In the hook, when I'm full frame (part where I
  list the new features), add explainer b-roll instead and show my camera in the corner. Add explainer b-roll to code
  mode." Mid-run: keep the vocal effects on A1 - edit the main timeline or copy everything (the duplicate null-tested
  identical); "You should have the entire GPU available to you." Built with 60 zooms, 16 graphics (g01 fvc, g11+g12 the
  code-mode world), 2 keyword pops, 1 CTA, hook music take 3 of 4 (sent as MP3s). Final file -14.01 LUFS, -1.40 dBTP,
  1.24 GB. Reviewing it in Resolve he removed the hook music himself: "It was actually too much. We don't need that intro
  song." (re-delivered without it; riser and sting kept) - so hook music is not a given: offer it, and drop it if he
  says so. He also found "this little grey bar thing at the top": an In/Out range my RANGE stem renders had left on both
  timelines (and an interrupted render had left 58 SFX clips disabled). rs_stem.py now restores the marks and recovers an
  interrupted run; after any in-Resolve render, check GetMarkInOut() and clip enables before handing the timeline back.
  A playback dropout at 0:20 he heard in Resolve went away after restarting Resolve (the file never had it).
  The next day: "The dings / bells / high pitches is a bit much. Swooshes, swipes, pops are fine. Can you remove or reduce
  the dings?" - the 25 dings and 7 chimes switched off on the timeline (reversible), master re-delivered. Now the default:
  LONGFORM_RULES exclude_types=('ding', 'chime') (editing-spec section 6). Even 15 s apart and quieter, bells read as
  too much to him; texture sounds don't.
- 2026-10-22, Blotato sponsor mid-roll ("YTHD60 - Pro Edit v1", 1:25.8): the brief - "use B-roll effectively", the
  phone demo shown on screen (the sponsor wanted a real Instagram DM), and a mock "as accurate as possible to the actual
  Instagram" of a reel flooded with "where's the tutorial" comments. Mid-run: keep the voice chain (use YTHD60 or a
  copy - duplicated and null-tested); cut "or a TikTok or a short" once research showed the automations are
  Instagram/Facebook only; "no bells or dings ... pops and swipes are fine", then "the notification ping would be fine";
  other connectors in the Claude menu are fine to show (ChannelPlan is his own tool). Built with 2 zooms, 8 graphics
  (g02/g03/g07 one Instagram comment world, g01 split + g06 the real phone demo), 2 keyword chips, 1 code card,
  2 punch-ins, 40 SFX, no music. Final -14.01 LUFS, -1.39 dBTP, 0.14 GB. Reaction to the finished timeline: not given yet.
- 2026-10-22, CubeFarm 2.0 ("YTHD60 - Pro Edit v1", 16:01, Upstash-partnered): the brief - edit YTHD60 or a copy (it
  carries his voice EQ/effects), trim what drags, B-roll and explainers "especially where I explain the benefits of having
  agents run in their own VMs / boxes", no dings/bells/chimes. Duplicated + null-tested (-88.9 dB), trimmed 24 s IN PLACE
  with ripple deletes of whole V1/A1 pairs (`DeleteClips([v, a], True)`, from the end backwards; no filler needed when
  whole items go), then mapped the trimmed duplicate. Built with 31 zooms, 22 graphics (two long-lived agents; the cloud
  section one continuous world over five beats), 2 keyword pops, 3 CTAs, a static censor, no hook music.
  Mid-run: told the fact-check findings (Upstash calls a Box an "isolated container", not a VM; no "GPT-5.5 Codex"
  model; cloud agents finish their task but nothing merges with the PC off) he said "the graphic is the correction" -
  keep his audio, label graphics correctly. Then "reduce the [SFX] volume slightly below what you would usually do" ->
  every type 3 LU under LONGFORM_TARGET (plan `sfx_levels`, `riser_db` -15); treat that as his default now.
  Final -14.01 LUFS, -1.31 dBTP, 1.36 GB. Reaction to the finished edit: not given yet.

- 2026-11-03, Career advice (camera-only, 82 min raw -> 21:52, "YTHD60 - Pro Edit v1 - Dynamic Camera"): the brief - use YTHD60
  (voice chain), build the timeline from six raw recordings incl. silence cutting, trim repetition, generate ALL the B-roll
  (clones of GitHub, editors, Claude Code, Codex, issues/PRs), position and transition the camera for energy, "don't make this
  feel like a PowerPoint presentation". Mid-run: a sponsor clip to place strategically ~2 min in, untouched, volume aligned;
  "I do not want you to add hook music at all"; the corner window cropped the top of his head. Built with 70 graphics (4
  agents), 8 zooms, 34 punch-ins, 3 pops, 4 CTAs, 268 SFX, 80 camera moves. Final -14.01 LUFS, -1.37 dBTP, 1.85 GB.
  Reaction to the finished edit: not given yet.

**From the CubeFarm 2.0 build (2026-10-22)**
- **Static censor boxes** (an email under "Logged in as", a one-time code): `censor.py`'s flood fill would blur a whole
  flat page. The work dir had `scripts/censor_static.py` (rects per time range, frame-exact via `media.decode`, mosaic +
  Gaussian, feathered alpha, ProRes 4444) - worth adopting into the skill.
- **zoom.py needs ONE PiP window per beat:** the per-item edge scan gave bottom-left windows 3-4 px apart on neighbouring
  items, so the beat fell back to the file's (top-right) window with a WARN. Unify near-identical item windows in
  scenes.json (slightly larger is fine) before rendering.
- **The top-right PiP caps zooms near the top of the screen:** with Yp ~972, fy >= 972 + 108/k pushes the view's top
  below the header - k <= 1.3 to keep a header row in view. Plan those as gentle pushes, or let a graphic do it.
- **CTA position override:** the card is fixed bottom-left; when the webcam is bottom-left, the plan's `box: [x, y, w, h]`
  moves it (work-dir overlay.py patch). Give every CTA a `logo` (a padded square on stage-800) - the empty circle looks unfinished.
- **Chapter titles follow the fact check too** - a chapter said "one VM per agent" after the graphics had been corrected.
- `sfx_prefer` playing ONLY the listed files (the Blotato work-dir patch) held up again; adopt it in sfxlib.

**Separate screen + webcam recordings, laid out in Resolve** (abacus-test, 2026-11-01: 7 OBS pairs DESKTOP 1440p +
WEBCAM 4K, an EMPTY YTHD60 template whose A1 "Voiceover" carries the voice chain)
- **Sync by audio:** both files carry the same mic; envelope cross-correlation then a sample-level refine gave r 0.99+
  and whole-frame offsets (desktop 5-9 frames earlier). Raw-waveform correlation on 16 kHz mono failed (r 0.02).
- **Build into a duplicate of the empty template** (keeps the A1 chain - voice-chain check said PROCESSED): V1 desktop,
  V3 full-frame webcam on camera lines, V4 a rounded facecam bubble on screen lines, A1 webcam audio, desktop audio
  unused; V2 stays free so zooms and screen-line graphics sit UNDER the live bubble (no PiP pasting needed).
- **Modern layout beats a fixed PiP** (the user: "follow best practices instead of just copying what I used to do"):
  the camera full-frame only on talking lines; the screen with a bubble; facecam bubble on V6 over explainer graphics on
  camera lines; short timelapses for agent waits. The bubble went into "the quietest corner" - mostly bottom-right -
  which the user later questioned ("is that based on what people actually prefer?"): the corner is now top-right by
  default, from the research (`dynamic-camera.md`).
- **ffmpeg image layers default to 25 fps.** A `-loop 1 -i mask.png` input used as the overlay base set the output
  clock: the bubble ran 2.4x fast ("my mouth is moving extremely fast") and showed frames from much later (an eye-wipe
  that wasn't there). Always `-loop 1 -framerate 60`; prove speed with a frame-match against the source (offset 0).
- **Small alpha clips 1:1:** Scaling = 1 (Crop) shows an 832x832 ProRes clip at native size, but Pan/Tilt are then
  in CLIP-relative units: Pan = px * 3840/832, Tilt = px * 2160/832.
- **HyperFrames `gfx/out/*.mp4` is NVENC lossless High 4:4:4** - Resolve decodes it as grey smears. compose.py normally
  re-encodes; when compose is skipped, transcode to High yuv420p (cq 15) before importing.
- **WAVs take the PROJECT fps (24 here) on import:** frame ranges for audio clips must be converted (n * 24/60), or
  every SFX lasts 2.5x and overlapping ones are dropped.
- **Intro energy** (user, watching the clean cut): "low energy... repeating myself... a second of breathing... showing
  me full screen the whole time, people want to see a sample of the final result". Fixes that landed: drop lines the
  hook already said, trim every pause/breath >= 0.25 s to ~0.14 s in the intro (RMS < -38 dB), a 4.5 s cold open of
  the finished result with the facecam bubble, face full-frame only on the promise line, B-roll of the real result for
  the rest of the hook, and a more energetic generated bed (electronic, 112 bpm).

**The dynamic camera** (abacus-test Pro Edit v2 -> v3, 2026-11-01; `dynamic-camera.md` is the full method)
- **The ask:** a reference video from another creator whose webcam morphs between full frame, a large side card and a
  small corner bubble; "intelligently move it around the screen to create a little bit more energy where it makes
  sense". Measured on the reference (face tracked at 30 fps): every change is a 0.5 s ease-in-out morph (position,
  size, aspect and radius together), moves land on sentence boundaries roughly every 10-25 s.
- **v2 flickered at every transition** ("a little bit of a flicker... whenever the transitions happen") and the user
  asked for "a reliable and repeatable solution", built the way Resolve editors do it, plus research on when and where.
  The cause was the rounded-mask maths (the whole window half transparent while the radius was under 0.5 px: a ghost
  frame at both ends of every move), with squash from interpolating crop and window apart, a landing bump from the
  punch-in, and moves that straddled webcam jump cuts. v3 rebuilt it on the PiP-effect model.
- **v3's first render still had 3 flash frames**: centred motion-blur samples reached back before the key. Then one
  more: a key written as 353.5667 s sits 0.002 frames after frame 21214. Forward-only samples and frame-snapped keys
  fixed both; `dyncam.py patch` re-rendered only the frames around the touched keys (minutes, not a full render).
- **A false alarm worth remembering:** a seek-based sync check said the final file's face was one frame late. ffmpeg's
  input seek lands a frame early in Resolve's MP4s (edit list); decoding from frame 0 showed lag 0 in every state.
- **The verdict on v3:** "I'm extremely happy with that... this is exactly the quality of editing that I expect going
  forward: with the transitions, the animations, and carefully deciding where to place the camera." It became the
  standard for separate recordings (this skill update). v3: 26 layout changes in 8:43, median hold 14 s, top-right
  2:44 / bottom-right 2:38 / bottom-left 1:40 (the hook's graphics were designed around a bottom-right bubble).
- **Resolve's API can't keyframe** (21.1.1): no TimelineItem keyframe methods, no OFX parameters, and `AddFusionComp()`
  keyframes are ignored at render - but `ImportFusionComp()` of a .comp with BezierSpline keyframes renders. That is
  the route if the user ever wants the moves editable inside Resolve; the rendered layer is the proven one.

**Camera-only recording with screen stretches, raw takes, and a finished sponsor** (career-advice, 2026-11-03: six raw
OBS MKVs, 82 min, a talking head at 30p inside 60p files with two GitHub screen stretches whose PiP is baked in; an empty
YTHD60 template carrying the voice chain; a finished sponsor midroll in the bin)
- **Foundation cut from raw, untrimmed recordings:** the gate leaves digital silence, so phrases come from a 10 ms RMS
  threshold (-46 dBFS), pauses >= 0.4 s, pads 0.12 / 0.18 s -> a probe-shaped structure for `vedit.py prepare`
  (986 phrases from 82 min). Build it into a duplicate of the template: one AppendToTimeline of all pieces (endFrame
  exclusive on 21.1.2) keeps the A1 chain (voice-chain check PROCESSED).
- **Hotwords that look like ordinary words leak:** "Skool" turned "skill" into "skool", "AGENTS.md" replaced "agents",
  and one clip came back as the hotword list. Keep hotwords to real product names; re-transcribe with `--force` if it happens.
- **A finished sponsor goes in whole:** picture on V2, its own mixed audio on a NEW audio track (not A1 - the chain
  would process it twice), the cut sequence shifted by its length. Level it by CLIP VOLUME measured through the user's
  bus: the bus compresses (-5.1 dB in gave -2.9 out, -9.3 gave -6.9), so iterate stem renders until its integrated
  loudness and speech match the minute either side (-7.35 dB here). The user said: "no editing to that sponsor segment".
  Nothing may overlap it, and the camera layer is placed in two pieces around it so it plays from its own clip
  (`tools/rs_layout_sponsor.py` in the work dir: SPONSOR frames, KEEP_ON B-Roll).
- **scenes.py on a camera-only file:** it may call real screen stretches "screen" - LOOK before overriding (here they
  WERE screen captures of his repo, the "one or two exceptions" he mentioned).
- **The dynamic camera on ONE file that switches camera <-> screen** (work-dir patches, worth adopting):
  - `dyncam.py cfg` measures the face on camera items only (the PiP face would skew it);
  - `rs_content.py` keeps V1 SCREEN items in the content layer (`KEEP_REC0`, V1 only - a first version also kept two
    CTA overlays that share a start frame, which would have doubled them);
  - `dyncam_plan.py` reads `dyncam_hints.json` (hidden over screen stretches and the sponsor, card moments with images,
    a forced FULL on a 2.6 s line), each with `"kind": "hint"`; screen and sponsor edges are hard cuts.
- **Lip sync: read the camera from Resolve, not from the MKV.** ffmpeg's frame numbering of these OBS MKVs differs from
  Resolve's by 1-2 frames (+1 early in file 1, +2 deep in file 6), so the first layer's face ran 17-33 ms behind the
  voice. `dyncam_qc.py sync` can't see it: on 30p-in-60p footage the motion correlation is high at every even lag. The
  test that works is pixel MAE of the layer against a short Resolve render of the same programme frames (V-shaped
  minimum). Fix: `tools/rs_plate.py` renders V1 with the punch-ins reset and everything else disabled (restored in a
  finally) -> `_deliver/plate.mp4`, and `dyncam.cam_src` returns (plate, n). After the fix, lag 0 by the same test.
- **Framing: the YuNet ratios cut tall hair.** The small window (3.17 x face height, centred 0.47 below the box) started
  above his eyebrows and cut his hair ("the top of my head is cropped out ... some space above my head"). For Leon:
  crops from the top of the frame (small_crop 1800 at y 900, card 2100 at y 1050). LOOK at a full-size crop of each
  window state before rendering.
- **Four graphics agents for 70 graphics** (~3.5 h of agent time, two render slots) held the quality bar with one shared
  brief: shared UI looks copied from one approved module (tripple-ten's Claude session), one fictional repo
  (`acme/taskflow` with fixed issue/PR numbers) and the camera keep-out stated in layout px. Graphics covering ~70% of
  the body drove SFX to 15.7/min; `sfx_rules` density (5, 15) + pop_max 4 brought it to 12.0.
