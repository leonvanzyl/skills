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
- **Webcam just above the screen (Last Call, 2026-10-19):** the two pose clusters (yaw -3 / +11) and the look-down blendshape did not separate reading from on-lens. Reading the screen there is a lowered gaze with the head nearly frontal. `eyesheet.py`'s small crops misled too, and three runs had to be re-laid out after the fact. Full-resolution crops round the eyes (`eyecrop.py`, 0.3 s steps) showed it plainly. Check every candidate camera line that way before the plan is locked. Expect a lot of reading while he walks through his own prompt pages or a demo, so pick short lines he says to the lens for the camera runs. The outro may end on a glance down; it stays full cam (Leon's rule).
- **Odd camera windows:** ffmpeg's `crop` rounds an odd width or height down on yuv420p, so a raw-frame reader sized from the window (e.g. 325 px from a 650 px window at proxy scale) reads misaligned garbage and never errors. `zoomscan.py` and `gaze.py` round their proxy crop to even sizes. Any new reader must do the same.
- **Slicing the analysis:** `gaze.py` and `zoomscan.py` run as 8 parallel time slices (9 min -> under a minute on a 15 min master). The zoom rows are identical to a sequential pass; the gaze rows match on every face/no-face flag, two thirds are bit-identical and the rest are within 0.15 deg of pose and 0.4 px of eye position (the VIDEO-mode landmarker warms up on the second before each slice). The clusters are 10+ degrees apart, so nothing downstream moves.
- **Snapping switches:** a camera switch snaps to a word boundary. The switch goes before the turn when you look away, and after the turn when you look back.
- **Finished edits:**
  - Background tracking (`zoomscan.py`) catches baked-in punch-ins and zoom transitions. Keep camera runs off them.
  - A finished edit may cut briefly to a full-frame camera shot. That's the sharpest camera footage available, so prefer it for full cam (`"cam": "fullframe"`).
- **Webcam window:** in a picture-in-picture, the webcam window can be small (for example 704×948 in 4K). Full cam upscales it about 2× with a light unsharp mask. In the split card, fit the whole face (hair to chin), and fill the side strips with a blurred copy rather than cropping the chin off.

**Compositing**
- **Frame lock:** the matte is made from the same frame-exact clip as the card footage, so head and card can't drift apart. Erode the u2net matte by 1 px to remove its dark rim.
- **Captions:** draw them word by word with an extra 16 px gap, or the 10 px stroke swallows the spaces. Position each caption from the run of the current frame, not the run where the caption started.
- **Previews:** decode only the runs you need (`--runs`). Decoding whole streams for a few preview frames wastes minutes.
- **Parallel segments:** render each run as its own process, then concatenate with stream copy. That's about 2× faster than one process on a 32-core machine, and it makes edits incremental. `compose.py --segments` does it with a per-run input cache and a frame-count check.
- **Never `bufsize=10**8` on a frame pipe:** every script used to open its ffmpeg raw-frame pipe with a 100 MB Python buffer. On Windows that makes `read(n)` crawl at ~130 MB/s (48 ms per 1080p frame, more than the decode, the blend or the encode), while the default buffer reads the same pipe at ~1.6 GB/s. Measured: 100 frames in 4.85 s vs 0.39 s. Writing frames to an encoder's stdin was fast either way (~7 GB/s), and x264 `slow` itself takes only ~8 ms a frame. Leave `bufsize` alone.
- **Where compose time goes:** a plain full-visual run costs ~70 ms a frame (mostly the x264 `slow` encode); a split run ~210 ms (the 1080x1920 float blends) and the outro ~210 ms (the CTA box redrawn with three 2x Gaussian shadows every frame). The blends now run only on the rows the card, shadow and head can reach, and the CTA box is memoised by its state (typed characters, caret, press, landing), both pixel-identical to the old code by construction (verified frame for frame).
- **Verified identical:** `matte_gpu.py` FFV1 output vs the old PNG-in-MOV: 409/409 frames identical. NVDEC vs CPU camera clips: byte-identical. New `--segments` vs the old per-run compose: every segment identical.

**HyperFrames**
- **Standalone comps:** render them with `render -c file.html`. `snapshot` only reads `index.html`, so use 10 fps draft renders and contact sheets.
- **Driving the timeline:** the engine drives everything from a GSAP proxy setter (`tl.fromTo(state, {t:0}, {t:dur})`). A tween setter runs on every seek, whereas `onUpdate` callbacks can be suppressed while seeking.
- **Video clips:** re-encode clips with dense keyframes (`-g 12`) and render with `--video-frame-format png` for UI footage.
- **Blend modes:** they are isolated inside a card that has a filter or opacity. Put highlight bands under a `mix-blend-mode:multiply` screenshot inside the same card.
- **Right-edge strip:** HyperFrames' MP4 path leaves an 8 px black strip at x 1072-1079 on 1080-wide output (still true in 0.8.97; the PNG capture itself is clean, so it's the MP4 encoder). The MP4 path also captures frames as JPEG (quality 95 for `high`), so it's out for the 240 fps intermediate twice over. `render_full.sh` renders `--format png-sequence` (lossless PNG frames, no strip) and runs the tmix itself. Drafts still use MP4 (fine for a contact sheet). Check the right edge of each `out60` file anyway: columns 1072-1079 should match 1064-1071.
- **One browser per worker:** `hyperframes render --workers N` makes N *tabs of one Chrome* by default (`PRODUCER_ENABLE_BROWSER_POOL=true`), and that one browser's GPU process encodes every PNG screenshot, so PNG capture tops out at ~15 fps no matter how many workers you ask for (measured: 1 worker 11 fps, 6 workers 14.6 fps, 16 workers 15 fps; MOV/ProRes and png-sequence alike). With `PRODUCER_ENABLE_BROWSER_POOL=false` every worker gets its own Chrome: 4 workers 29 fps, 8 workers 41 fps, 16 workers 51 fps. `render_full.sh` and `render_draft.sh` export it. Software rendering (`--no-browser-gpu`) is slower, not faster, and BeginFrame capture is Linux-only, so on Windows screenshot capture with hardware GPU is the path.
- **Workers are not free:** 24 workers on one render was slower than 16 (63 s vs 37 s capture). Size for the whole machine, not one render: `render_full.sh` runs at most `RENDER_SLOTS` (3) renders at once with `HF_WORKERS` (8) browsers each, machine-wide, through lock directories in `gfx/.render_slots`, so six graphics subagents calling it at once don't launch 100 Chromes.
- **PNG path = same pixels:** against the lossless capture, the old ProRes-4444 intermediate came back at 45.1 dB PSNR and the PNG-sequence intermediate at 46.1 dB (both yuv420p crf 10 out60 files); the two out60 files differ from each other at 44.6 dB, i.e. codec noise. The PNG path tags BT.709/tv explicitly on the way in and out so the clay accent decodes to within 1 LSB of #D97757.
- **Don't composite while a graphic is re-rendering:** a segment decoded while its `out60` file is being rewritten silently picks up the old or a partial render. Composite only after every `render_full.sh` has printed `done`. `compose.py --segments` (used by `finish.sh`) counts the frames of every segment against its run and fails loudly on a mismatch.
- **Exact stills:** use output seeking (`-ss X-0.5 -i src -ss 0.5`). Input-only seeking can land a frame early, e.g. on a menu that isn't open yet.
- **Frame 0 of a split:** the hero is already on screen when the cut lands. "Nothing lands at frame 0" means don't start a landing animation at frame 0; it doesn't mean "land just after". A card that landed at 0.05 s left three empty frames after the cut. Supporting cards (logo tiles, a bubble arriving) may land later with a pop.
- **Highlights on dark UI:** a light band under a `multiply` screenshot vanishes on a dark app. Re-ink the real text dark on the azure wash in an overlay revealed by a wipe, or use an azure outline with a soft glow. Both read well.
- **Wide UI columns:** a captured chat column at 4K is so wide that "show both bubbles whole" leaves the text around 21 px. Frame the line the viewer must read at 30 px or more and let the others crop at the frame edge.
- **Parallel graphics subagents:** give each one a tag (`s1a`, `s1b`, `s2a`…) with its own `scripts/prep_assets_<tag>.py`, `gfx/asset_dims_<tag>.json` (build_gfx_common merges every `asset_dims*.json`) and `scripts/gfx_<tag>.py`. Build with `build_gfx.py <tag>`; it locks the shared `gfx/sfx_events.json`. A shared `GFX_BRIEF.md` (`examples/GFX_BRIEF_template.md`) plus a short per-agent prompt worked well: 16 compositions from 5 agents, then 31 from 3 long-lived agents (the reference run; Leon prefers few long-lived agents), with no collisions.

**Finished edits as the source (learned on a 12 min long-form export with its own music, SFX, zooms and censor)**
- **Sound under the voice:** a finished export can carry the long-form edit's hook music, riser and SFX (pops, whooshes, clicks, a CTA card's key ticks) under lines you want to keep. Look for a clean voice stem, e.g. the long-form edit's own dialogue track (a previous davinci-resolve-pro-edit run keeps `voice48.wav`). Then run `clean_from_stem.py` (pipeline.md §1b). Its `--suspects` (30-90 Hz band vs the stem) found the riser (+20 dB), hook pops and whoosh (+22 dB) and two CTA-card SFX bursts (+17 and +25 dB). A quiet music bed 18 LU under the voice did not show, so treat the hook as suspect anyway.
- **Match the stem, don't just swap it:** the export's voice chain had added +4 to +11 dB of bass and presence and about 3 dB of compression over the raw mic. A raw stem dropped in sounded different and sat 3-4 dB low on quieter frames. A linear-phase FIR EQ match (within 0.6 dB per band), a static compression curve fitted on clean stretches, and a per-patch median level match make patched and unpatched lines indistinguishable.
- **Never rescale the whole file for a few hot samples:** one stray transient took a global `*0.98/peak` rescale down 3 dB everywhere. Soft-knee only the hot samples.
- **Piecewise sync:** the export had small trims against the stem's timeline, so the offset jumped (+21 ms, +371 ms, +38 ms, +55 ms, +2.85 s). A single cross-correlation offset is wrong after the first trim. Find each change point by minimising (error with offset A before it) + (error with offset B after it) on 10 ms frames. Whisper word times and "the quietest frame nearby" each put a trim about 170 ms off.
- **Sound the stem never had:** e.g. an AI agent's voice on a call, recorded on another track. It shows as weak correlation in `--scan` and a big low-band excess in `--suspects`. Keep the export audio there; never patch it.
- **Burned-in text on a full-frame camera stretch:** the long-form edit's keyword pops ("no VPS", "ChatGPT subscription") sat at 80-87% of the frame height, inside both the full-cam slice and the split card's visible area. `zoomscan.py` sees framing changes, not text, so look at frames of every `fullframe` stretch before planning a camera run on it.
- **Transitions warp the webcam:** a "bounce" transition zoomed and blurred the PiP for about 0.7 s. `zoomscan.py`'s "tracking lost" lists it. If a line starts inside it, open the line as a short full-visual cutaway (1.35 s worked) and switch to the camera at a later word.
- **The webcam can move:** for 30 s the long-form edit put the webcam bottom right. The detector used to merge both positions into one tall window, because the bottom border scored 0.385 against a 0.4 threshold (dark shirt on dark UI). `detect_camera.py` now retries an implausible side with a lower threshold and prints a WARNING listing the samples whose face is elsewhere. Keep camera runs out of those stretches.
- **Eye contact with the webcam beside the screen:** looking at the lens is the TURNED pose cluster (yaw about 13°). Reading the screen is frontal and slightly down. Calibrate on the outro or another line you know is said to camera, never assume the frontal cluster is on-lens.
- **Echo on calls:** an AI voice through speakers with room echo made the window ASR hear "I'm doing great" and "How about you?" twice. Mark such lines `"echo": true` (align_lines collapses the repeat into one phrase spanning the echo tail). Never on a stutter.
- **Things to keep off screen go in the graphics brief:** baked titles ("sorry about echo :-)"), the censored (blurred) bubble, the long-form zooms, the webcam's other position. Prefer stills from unzoomed moments and do the camera work yourself.
- **Reuse the long-form edit's research:** a previous long-form run's report lists its music, SFX, riser, zoom and censor times. Its `captures/facts.json` and logos can be reused, so re-verify only the claims the shorts actually say.

**Captions, CTA and mix**
- **Caption text = the plan's words:** align_lines overwrites the aligned words with the line's `text` when the counts match. That gives casing at sentence starts ("keep" → "Keep"), numbers as said ("5" → "five") and misheard words ("is" → "it's", "OPS" → "OBS"). So write the line `text` exactly as it should read on screen.
- **Caption-only fixes while graphics render:** don't re-run `align_lines.py`, because GPU re-transcription can move a word edge by a frame and change the run durations the graphics are rendering to. Patch the `w` text in `cut.json` and run `compose.py <sk> --events-only`.
- **CTA keyword as the last word:** typing started on it, so the Post press landed after END. compose.py now starts typing early enough that the press ends 0.3 s before END.
- **True peak:** a less-compressed voice (a patched stem) peaked at −0.4 dBTP through the old sample-peak rescale. audio.py now runs a 4× oversampled true-peak limiter at −1.3 dBTP that touches only the transients (−13.9 LUFS kept).

**Research captures**
- **Headless blocks:** OpenAI's pages answer plain headless Chromium with "This page couldn't load". Playwright's new headless mode (`channel: 'chromium'`) loads them.
- **Localised pricing:** pricing pages localise by country (ZAR from South Africa). Capture the provider's US prices (OpenAI serves its own US pricing config), and log that in the report.

**Brand, sound and music (October 2026, carried over from the long-form edits Leon called "a massive step up")**
- **The channel's design system, everywhere.** The yellow Instrument Serif caption highlight was "ugly" and the white
  luxury world generic; the long-form edits in his "Leon YouTube" design system (graphite glass, Figtree / Geist Mono,
  azure) got "Now that looks cool. Lock it in". Shorts now use the same: the keyword chip, the glass cover and CTA, and
  the engine's `stage` theme. The design system is bundled in references/design-system/ (SOURCE.md says how to refresh it).
- **PIL replaces pixels, it doesn't blend:** `ImageDraw` with a translucent fill on an RGBA canvas punches a see-through
  hole (the CTA's input field showed the footage through it). Mix translucent fills to opaque colours first, or draw them
  on their own layer and `alpha_composite`. (The chip's 33% accent hairline relies on it on purpose: the approved look.)
- **Real sounds.** The synthesized SFX were "bland and generic"; the library (assets/sfx, CC0 + Mixkit) with highlight
  swishes on bands, the minimal hit on the hook join and real single key strokes was what he liked.
- **Generated music, chosen by ear.** ACE-Step 1.5 XL in its own env; the cinematic preset is the take he picked out of four
  ("That's the one!"). Level matters as much as the track: 18 LU under the voice was barely there, 15 LU reads. A take is
  only usable with a lift; the pick rejects takes without one (1 of 2 in the first test) and any with a vocal stem.
- **RVM for the head pop-out.** u2net grabbed the guitar behind his ear on and off; RVM (matte_rvm.py) follows the hair
  and leaves the wall objects behind. 225 frames of a 704x948 webcam clip in 4.5 s on an idle 5090 (32 s while a
  HyperFrames encode held the GPU). No 1 px erosion on an RVM matte: it would thin the hair.
- **No sponsor that isn't this video's sponsor.** A long-form graphic labelled the agent pool with a sandbox vendor
  that had sponsored an earlier video; Leon had it replaced. Name brands only when the speaker does.

- **Loudness, not peak (2026-10-16):** viewers of the long-form found "ding, scribble, ding, ding" annoying; measured,
  peak-based levels made bells, chimes and scribbles 6-14 dB louder to the ear than clicks at the same setting. Both
  skills now level every sound by loudness (`sfxlib`). The shorts kept their density and levels (approved); only the
  chimes came down (-8 -> -12 LU) and the scribble lost its hiss. The long-form's body got variant C (fewer dings and
  scribbles, every animation keeps its pops).

**Shorts from a finished long-form edit (Harness Engineering, 2026-10-14: 5 shorts from the 4K export)**
- **Reuse the pro-edit run, by script:** the long-form's `program.json` (final time -> raw recordings), captures, logos
  and `voice48.wav` were copied by hand here, and the raw footage is what gave the graphics clean, unzoomed UI and app
  footage. `import_longform.py` now does it in a second (pipeline.md 1c); `--at <t>` finds the raw frame for the brief.
- **Few long-lived graphics agents:** 3 agents (real sources + footage / concept diagrams / one continuous world) built
  31 compositions in about an hour, each rendering every draft first. The brief's composition list (words at run-relative
  times) is now `brief_runs.py`.
- **Reports and publishing copy by script** (`examples/harness-engineering/make_reports.py`, `make_publish.py`): numbers
  from the data, judgement written per short after looking at every sheet. Run `check_publish.py` every time, even when a
  generator wrote the copy. Writing the reports is also a check: it is where the garbled "Bölük" caption was found.
- **Which pose is on-lens changes with the setup - calibrate on frames, never assume.** In this recording the frontal
  cluster (yaw ~ -3) was the lens and the turned one (yaw 13-21) the slides on a screen to his left - the OPPOSITE of the
  older "webcam beside the screen" note. Look at full-size webcam crops from a few known moments (a to-camera sign-off,
  a line read off a slide, a demo) with their yaw before labelling lines. Frontal also covers looking at the main monitor
  just under the lens (a live demo), so check the camera runs' eye sheets anyway.
- **A finished edit with SFX everywhere: patch the whole voice.** The long-form put ~210 library SFX plus hook music under
  the voice, so `clean_from_stem.py` got one patch [0, END] and `fit_exclude` windows (the hook music) for the EQ /
  compression fit; extra gain 0.1 dB, bands within 0.6 dB. The stem was offset 21 ms and ended before the export, so the
  patch clamps at the stem's ends. Don't let setup pair the stem as `clean_audio` (a WAV next to the video is taken as
  the clean recording): set `clean_audio: null` and use `clean_stem`.
- **Switch times from ALIGNED words, not the full transcript.** The batched transcript's word starts ran 0.15-0.4 s early
  against the forced alignment, so hand-typed switches snapped one word early ("6.7% | all the way" became "6.7 | %").
  Read the aligned word from `line_align.json` (span `fi..li`) and use its `s`.
- **Whisper splits numbers and hyphens** ("6 .7 %", "30 ,000", "GPT -5 .2", "sub -agents", "consumer grade"): align_lines
  now rejoins `.digit`, `,digit`, `%` and `-word` pieces (and absorbs one just past the line's last matched word, which had
  clipped "GPT-5.2" to "GPT-5"), so captions use the plan's exact words. A two-word plan word the ASR keeps apart
  ("consumer grade", "open weight") still needs the plan text written the same way.
- **One line's window can swallow the previous line's tail:** a line that starts right after continuous speech got its
  first word aligned 0.9 s early and repeated "66%". Find the real pause in `rms10ms.npy` and start the line in it.
- **Multi-word ASR fixes:** `asr_fixes` values may be several words ("tardis": "The harness"); they are aligned one by one.
- **Captions and the J-cut:** a line's first word starts ~10 ms before its picture cut, so captions assigned it to the
  run before (a one-word flash: "The", "They", "Well"). compose.py now places a word in the run it is heard in 60 ms later.
- **Leon's CTA rule:** every short ends on the "Watch the full video" card pointing at the full-video link; 3-5 shorts per
  video, the most interesting moments, never more than 5.
- **Read the full video's LIVE title.** The file was "The 3 Levels of Harness Engineering (Beginner to Pro)", but it went
  live as "Harness Engineering: Make Any Coding Agent 10x Better". With a URL or video ID (Leon's stats-for-nerds
  screenshot carries it), fetch `https://www.youtube.com/oembed?url=<watch URL>&format=json` and use its `title` in the
  TikTok / Instagram CTA lines and the Related video. Never trust the file name or the pro-edit draft title alone.
- **Two big videos in one HyperFrames page ran Chrome out of memory** (a full-res clip plus its blurred backdrop clone).
  Give the backdrop its own small copy (640 px wide is plenty under a 40 px blur) and render with
  `NODE_OPTIONS=--max-old-space-size=16384`.
- **A music take Leon rejects:** don't regenerate blindly; offer the other takes and the long-form hook track
  (`music_lib/cand_N.wav`). In `shorts.json` a `music.file` + `file_offset` plays a given track instead of a take; set the
  offset so its lift lands on the hook join. He called s1's take 2 "terrible", and s1 used the long-form cand_3.

**A finished edit whose work folder is gone (Last Call, 2026-10-19: 4 shorts from a 24.5 min 4K export)**
- **The raw recordings can stand in for the work folder.** The pro-edit run had been cleaned up: no `voice48.wav`, no
  `program.json`, only `pro-edit-media/` (report and publishing copy). The export had the game playing under the intro and
  ~130 library SFX under the talk. The raw recordings (1-5.mkv) were next to the export, so `build_raw_map.py` rebuilt
  both by audio matching: 213 pieces in ~25 s on the GPU. `clean_from_stem.py` then matched the raw mic to his voice chain
  within 0.6 dB in every band. The same map gave the graphics clean, unzoomed footage (`rawsheet.py`, `import_longform.py --at`).
- **Raw tracks that caught the speakers match the wrong stretches.** His screen recordings had the game's voice samples
  playing through the speakers, so the export's montage and playthrough matched them. Limit `clean_stem.sync` and
  `.patches` to the talk by hand; outside the patches the export keeps its own audio.
- **`clean_from_stem.py` near-zero offsets:** a sync offset of -2e-05 s made the 1 s fit slices 47,999 vs 48,000
  samples and the level fit crashed. The slices now round their start and take exactly SR samples.
- **The game's own dialogue as a line.** A line of the montage ("Eight years, four vans, one fire." / "Small fire.") cut
  and aligned like any other, with the export's audio (game music under it) and the montage's own frames synced in the
  graphic. Showing the voice acting beat naming it.
- **A camera placed by the long-form:** its intro put his full-frame camera in the webcam's spot and size. Detection
  treats it as the PiP, but the face is bigger, so that short's split scale came out 1.21 (the webcam shorts 1.41-1.44).
  One scale per short keeps it consistent.
- **A music pick with a negative score** (lift 1.8 s before the join, the other takes with no lift): generate a new batch
  (`music.seed` + `takes: 4` in `shorts.json`, move the old `<sk>/music/` aside, `music_takes.py <sk> --force`). The second
  batch landed its lift on the join.
- **The game's own project folder is the richest source** when the video builds something: the real style pages, the
  docs the agent wrote, the debug tool's contact sheets and the critic agents' review files. Point the graphics brief at it.

**Environment**
- **Face detection:** OpenCV 5 removed the old Haar face cascades. `faces.py` uses the bundled YuNet model (`face_detection_yunet_2023mar.onnx`), which also finds small webcam-window faces.
- **Text encoding on Windows:** Python's `open()` defaults to cp1252 there, so "Bölük" in `shorts.json` became "BÃ¶lÃ¼k"
  in `cut.json` and burned into a caption chip (found only on a frame check; the voice proof can't see it). Every script
  now reads JSON with `encoding='utf-8'`, every stage script exports `PYTHONUTF8=1`, and `check_text.py` stops `finish.sh`
  on garbled text. Any new script must do the same.
  After a fix, repair the stored text in place (`s.encode('cp1252').decode('utf-8')`) rather than re-aligning.
- **Windows shells:** in Git Bash, `\n` inside a Python heredoc becomes a real newline and breaks string literals. Write longer code with a file-writing tool.
- **Backgrounding with `cd`:** `cd W && (a; b) & c` backgrounds the whole `cd W && (...)` group, so `c` runs in the OLD directory and fails. Use one subshell for everything (`(cd W && a && b) & (cd W && c)`) or absolute paths.
- **Busy folders:** a folder used as the shell's working directory can't be renamed on Windows. `cd` out of it first.
- **CPU fallbacks:** Whisper falls back to CPU int8. The matte falls back to CPU u2net (`hyperframes remove-background`) at about 1 fps per process when onnxruntime-gpu is unavailable. Both work; just expect a longer run.
- **Where the time goes (RTX 5090, 32 cores, 15 min 4K master, measured):** `analyze.sh` about 1.7 min: ingest 60 s (4 NVDEC slices; 105 s single pass; 8 slices no faster), transcription ~8 s inside it, camera detection ~10 s, gaze + zoom scans ~30 s (they were 9-14 min sequential: 575 s + 49 s). `cut.sh` ~40 s (alignment 6 s, cut 2 s, voice proof + eye sheets in parallel). Four full graphics renders (5,458 frames at 240 fps) 93 s through 3 slots x 8 browsers (one 8 s composition alone: 45 s; it was 168 s). `prep.sh` ~20 s: camera clips 4 s (were 22 s), two mattes 9 s (were 17 s), events, split previews 4 s (were 132 s). `finish.sh` ~70 s for a 34 s short: six segments in parallel 55 s (were 139 s), audio, concat and verify. After the plan is locked, a short with four graphics takes about 3 min of machine time (measured end to end: cut 24 s, renders 84 s, prep 22 s, finish 61 s); what remains is the agent's own planning, briefing and checking.
- **Why it was slow:** not the GPU. One Python argument (`bufsize=10**8` on every frame pipe) cost 48 ms a frame everywhere; HyperFrames' default browser pool serialised PNG capture through one GPU process; the gaze scan was a single-threaded loop over 9,000 frames; previews decoded whole runs to show one frame; the CTA box was redrawn every frame; and the stages were run as many separate agent turns. All of that is fixed in code; none of it changed a pixel.
- **CUDA PyTorch:** setup.sh installs the cu130 build on NVIDIA machines (the CPU build ran wav2vec2 at 11.8 s for 25 lines, CUDA at 0.9 s, with identical edges). CUDA 12 (CTranslate2/onnxruntime) and CUDA 13 (torch) DLLs coexist fine in one process.
- **Matte on GPU:** `hyperframes remove-background --device cuda` can't use CUDA on Windows (its onnxruntime-node build lacks it) and silently drops to CPU. `matte_gpu.py` runs the same cached model on onnxruntime-gpu instead: ~12x faster. If `onnxruntime.get_available_providers()` lacks `CUDAExecutionProvider`, a CPU `onnxruntime` wheel is shadowing onnxruntime-gpu: uninstall it and reinstall onnxruntime-gpu (setup.sh does this).
- **Matte cleanup:** u2net keeps background objects that touch the head (e.g. a guitar neck on the wall above the hair), and they pop out above the split card. `matte_gpu.py` gates the matte with a horizontal opening (drops thin vertical strips under 80 source px), keeps the largest blob, and feathers the clip's top 14 rows (the webcam window border). Check one matte over a flat colour above the hair line.
