# Editing spec (the quality contract)

This is the complete creative and technical spec behind the shorts. Every rule here was proven on real output: follow all of it, don't simplify or skip any rule to save time (speed comes from parallelism, see speed.md, never from cutting corners). Where the user's request says something different, the user wins.

You're editing my raw talking-head recording into a finished, ready-to-post 9:16 short (Instagram Reel, TikTok, YouTube Short). Do all of it yourself, end to end, in code: ffmpeg, Python, Node and HyperFrames (npx --yes hyperframes). No video editor app. Every sound effect and the music are synthesized by you in code; there are no audio files to use. You may install what you need locally inside this project (npm packages in the project folder, pip into a local venv), without asking. Never install system-wide software.

WORK FULLY AUTONOMOUSLY
- Don't ask me anything after this message. Run every step start to finish and finish with final.mp4 exported.
- Every judgement call (which take, layout choices, a fact that disagrees with its sources, a product UI you can't capture) is yours: make the best call, keep going, and log it in the report.
- If something fails, try another way (a different tool, method or fallback) rather than stopping. A missing tool is not a reason to stop: install it locally or use an alternative.
- If a real product UI is behind a login, rebuild it from public screenshots or docs and note it in the report.
- If the cover title field is empty, write one from the hook yourself.
- Only stop early if the video file is missing or unreadable. A missing clean-audio file is not a reason to stop: use the video's embedded track.

INPUTS
- Camera video: in this project folder
- Clean audio: in this project folder if there is one; otherwise the video's embedded audio track
- Cover title (frame 0): from the user's request; if none is given, you come up with one
- The full video on YouTube (URL or title): from the user's request, otherwise found as section 8b says

DELIVERABLES (in a new folder edit/)
- final.mp4: 1080x1920, 60 fps, H.264 high quality, AAC 48 kHz stereo
- stems/voice.wav, stems/sfx.wav, stems/riser.wav, stems/music.wav (all full length, so I can remix)
- A short report (see the end)
- edit/PUBLISH.md: the publishing package for every short, for YouTube Shorts, TikTok and Instagram Reels (section 8b)
- thumbnail.jpg next to final.mp4: one clean, eye-catching frame from the short, its thumbnail and cover on all three (section 8c)

1. SYNC AND TRANSCRIBE
- Cross-correlate the camera audio and the clean audio at 16 kHz mono to find the offset (confirm it with a clear correlation peak). Use only the clean audio from here on; the camera audio is discarded. If there is no separate clean audio, confirm the embedded track's channels line up (zero offset) and report it.
- Transcribe the clean audio with word-level timestamps (hyperframes transcribe or whisper), then force-align each kept line (wav2vec2 / WhisperX) for exact word edges. Raw Whisper word times are not accurate enough to cut on. Group the words into takes.

2. THE CUT
- I re-record lines until I'm happy, so keep the LAST complete take of every line. Use an earlier take only if the last one has an audible defect in the words (stutter, clipped or wrong word, restart mid-sentence). List every swap in the report.
- Remove restarts, self-corrections, "okay", stray syllables and muttered comments after a take.
- Leave 40 ms before the first word. Any quiet stretch over ~250 ms inside or between lines is cut down to ~120 ms. Natural short pauses stay.
- A line's end is its measured true end, not the transcript's word end: the last 10 ms RMS window at or above -35 dB. If it stays under -32 dB for more than ~150 ms, the true end is earlier: cut there.
- Picture cuts are hard cuts, exactly on the join. No zooms, punch-ins or moves on my footage, ever. If the source already contains punch-ins or framing jumps (e.g. it's a finished edit), detect them and keep every camera run clear of them.
- The J-cut is in the AUDIO only: each line's audio starts 50 ms before its picture cut. A line's tail holds at full level until its true end, then fades out over 170 ms, but never runs past the start of the next sound. No join may have a quiet stretch over 150 ms. Fix a bad join by tightening the cut or overlapping the lines more, never by adding silence.
- Verify the cut: re-transcribe the finished voice track (it must read word-perfect: no clipped or stray syllables) and measure the quiet at every join.
- END = the last frame of the voice track. Every layer ends exactly on END.

3. EYE CONTACT
Sample about 8 frames per kept take (then 100 ms steps around any head turn) and look at them. My camera shows only while I'm looking at the lens. If I look away mid-line, the camera hides from the last on-lens frame: split the run at the nearest word boundary before the turn and make the rest a full visual. A take read off to the side the whole way through is a full visual. Blinks and sub-0.3 s eye glances are not "looking away".

4. THE THREE LAYOUTS
Canvas 1080x1920. Every short rotates through all three, with hard cuts on the joins:
a) Full cam: my footage cover-fitted (the centre slice of a landscape source).
b) Split, cam at the bottom with my head popping out: a full-frame 1080x1920 graphic sits behind everything, with its content in y 40-900 (the main element's bottom edge at 880-900). On top of it goes a rounded camera card, 1210x864 at x -65, y 1200, corner radius 200 (squircle), bleeding off the left, right and bottom edges. For a 16:9 source, scale the footage to 1890x1063 and place it at x -405, y 1008. The card shows that footage through its window, and ABOVE the card's top edge only my matted head and shoulders show: the same scaled footage with a background-removal alpha matte (hyperframes remove-background or an equivalent), feathered 40 px at the card's top edge, pixel-aligned with the card so the head never tears from the body when I move. The matte and the card must come from the same source frame on every frame; verify this on fast head moves. For a portrait source (e.g. a webcam picture-in-picture), derive the geometry from my measured face: my WHOLE face, hair to chin, must be visible (the hair popping ~100 px above the card edge, the chin inside the visible card, never cut off by the frame's bottom). If that scale leaves the card's sides uncovered, fill the strips with a soft, enlarged, blurred copy of the same frame, feathered into the sharp footage. Check one full-resolution frame per split run.
c) Full visual: a full-frame graphic.
Rules:
- The hook (first sentence) is always the split. The outro (the CTA line onwards) is always full cam. Direct-to-camera lines (opinions, punchlines) are full cam. Screen recordings, news pages and product UI that needs zooming inside it are full visuals. A single screenshot, a card, a logo row or a short list is the split.
- No run over ~8 s, two runs in a row never share a layout, and all three layouts are used.
- Write the plan as runs tiling [0, END] before building any graphic.

5. GRAPHICS (HyperFrames, one composition per run; use parallel subagents)
The style is luxury tech: one bright world of floating white cards, and a camera that moves through it.
- Ground: a radial near-white fill (#FFFFFF at 50%/36%, falling to #F3F3F0 at the edges). No grid, no orbs, nothing dark anywhere.
- Every object off the ground carries one three-layer shadow: 0 60px 120px rgba(24,24,32,.16), 0 24px 48px rgba(24,24,32,.10), 0 4px 10px rgba(24,24,32,.06). Radii: media cards 3% of the width, docs 40, tiles 72, phones 84.
- Type: Poppins throughout. Headline 96/700, subhead 52/700, body 30/400; nothing under 30 px. Ink #111111. Accent Clay #D97757 for fills, #B25730 for Clay text on white, highlight band #FBEEE8, green #34C759 for checks, red #FF3B30 for stamps.
- A world camera moves over the cards: a glide (sine.inOut, scale change 0.04 at most), a step to the next item (0.5 s power3.inOut, starting 0.25 s before the word that names it), a push onto the card being talked about (1.2-2 s power2.inOut, up to ~1.6x), a pull back to reveal the bigger picture (1-2 s), and at most ONE whip per run (0.45 s out power3.in, 0.6 s in power3.out). Frame 0 of every run is the landing state, sharp, with the camera at rest.
- Depth of field: the card being read is in focus; neighbours blur up to 14 px and dim 30% as the camera pushes. A new hero sends the old one back to a 9 px blur at 40% opacity. Never blur a word the viewer needs to read.
- Motion blur: blur the camera viewport along its screen velocity on every frame (sigma = 0.29 x speed x 0.75/60, capped at 24 px), then render at 240 fps and blend 3 of every 4 frames down to 60 fps (ffmpeg tmix=frames=3,fps=60). Blur only mid-move; a blurred frame at rest is a bug.
- Animate the action, never label it: no label pills, step chips or word rows restating the narration. A named product is its real UI, captured live (hyperframes capture or a headless screenshot) and doing the action: typing, streaming, clicking. While a product window is the subject, only a camera INSIDE the window moves (1.15-1.4x, 0.4-0.7 s power2.inOut); the world camera holds still. Named-product intro: its official logo large and centred first, then the UI.
- "Claude Code" means the Claude desktop app UI, never a terminal, unless I'm talking about the terminal.
- Anything that HAPPENED (a release, a quote, a number, a headline) shows its real source page. Check every figure I say against two or more reputable sources and report any disagreement. A real capture sits sharp in a fixed frame (x 24, y 200, 1032x1040, radius 36, white, shadowed) on a blurred, enlarged, WASHED near-white clone of itself (blur 40px, saturate .7, brightness 1.05, a 72% white wash over it) that moves with the footage. The frame never moves; the footage pans and zooms inside it.
- Full visuals keep content above y 1230 (main element's bottom edge at 1200-1230). Splits keep it in y 40-900 and fade the world out from y 900 over 160 px.
- Keep every scene sparse: one dominant subject, at most one supporting cue, smooth eased motion, never frantic.
- Duration of each composition = its run exactly. Check each render with a contact sheet before using it.

6. COVER, CAPTIONS, CTA
- Cover: frame 0 only. My title in Poppins bold 110, black on a white rounded box (radius ~2.8%, soft shadow), centred at y 0.13 (about y 262-603 for two lines, ~50 px side padding). On frame 0 the intro graphic keeps everything below y 620.
- Captions burned in from the FINAL voice track's word timings, starting at 17 ms (frame 0 stays clean). 1-3 words per chunk, Poppins bold 74, white, black stroke 10, no box. Keep clear word spacing (the stroke must never swallow the spaces). After every 2-3 normal chunks, one or two meaningful words (a product name, number, benefit, the CTA keyword) switch to Instrument Serif bold italic in pure yellow #FFFF00, same size and stroke. Never two highlights in a row, never function words.
- Caption position per run, never on my face, the card edge or a visual: split = centred in the gap, y 941-1114; full cam and full visual = lower third, y 1290-1560; a visual with low content = top, y 365-634; outro = centre, y 1037-1306. A caption that spans a layout cut moves with the cut: position it from the run of the frame it's on.
- CTA card, outro only, lower third (box 43, 1344, 994x276): one centred comment box on a transparent canvas, a default avatar, the keyword from my CTA line typed with a blinking caret, then a Post button press. Nothing else: no panel, no background, no "DM me", no platform text.

7. AUDIO: SYNTHESIZE EVERYTHING, THEN MIX TO THESE LEVELS
Synthesize with numpy/scipy, or the Web Audio API rendered offline with OfflineAudioContext. Clean, modern and premium, never cartoony.
- Voice (stems/voice.wav): the J-cut track from step 2, loudness-normalized to -14 LUFS integrated.
- SFX (stems/sfx.wav), one sound per meaningful VISIBLE event only:
  - a soft bubbly click on real button presses and taps
  - a short soft key press on typing (a light tick stream for longer typing or data streaming)
  - a dull soft pop on a card, tile or device landing
  - a gentle two-note notification chime on an answer, modal or confirmation
  - a LOW, airy whoosh (filtered noise) whose loudest moment lands exactly on the midpoint of each whip, and only on whips: at most one per run, three per short. Rotate 3-4 variants so no two in a row repeat.
  - Nothing on layout cuts, camera steps, pushes, glides or zooms. A logo lockup and any CTA under it get a whoosh or nothing, never a UI sound.
  - Levels, peak against the voice's peak: clicks, pops and chimes -10 dB, whooshes -9 dB, key presses and ticks -16 dB.
- Intro riser (stems/riser.wav): a low, swelling riser, about 2-3 s long, whose audible end lands exactly on the join where the hook ends and the first point starts. It's the one sound allowed to rise into a cut. Peak about -12 dB against the voice peak.
- Music (stems/music.wav): synthesized for THIS short, never a repeat. Pick the style that fits the topic and energy, and set a mood (warm or moody). The styles are:
  - lofi hip-hop: the default for talking-head tech content. Dusty swung drums, Rhodes 7th/9th chords, warm bass, vinyl crackle, tape wobble.
  - chillhop: relaxed how-tos.
  - ambient: serious or reflective topics.
  - synthwave: retro, hype, "the future is here".
  - upbeat house: launches and wins.
  Key, tempo, chord progression, drum pattern and texture come from a per-short seed (scripts/music.py), so no two shorts share a track. Arrange it to the edit: a low-passed intro under the hook, then the beat drops exactly on the hook -> first-point join, where the riser lands. Level: about -31 to -33 LUFS integrated, sidechain-ducked ~5 dB under my voice. It fades in over ~0.8 s and fades out to end exactly on END. Log the style, mood, key, tempo and seed in the report.
- Final mix: about -14 LUFS integrated, true peak at or below -1 dBFS.

8. REPORT (edit/.../report.md)
- Inputs and sync (offset and correlation peak), transcription method.
- The cut: every kept line with its source timecodes, every take swap, every trim, and the join and pause verification results.
- Eye contact: where the camera hides and why.
- The layout plan: runs tiling [0, END], with layout, times and durations, plus the camera and split geometry used.
- Graphics: one line per composition (what it shows, real sources used, camera moves, whips).
- Cover, captions (highlight words) and CTA keyword.
- Audio: every SFX event with its time and level, the riser timing, the music (style, mood, key, tempo, seed), and the final loudness and peak.
- Fact check: each figure I say, with 2+ sources, and any disagreement.
- The thumbnail: its time and run, what it shows, and why it beat the other candidates.
- The full video the TikTok and Instagram copy points to, and where its title came from (section 8b).
- Every judgement call you made.

8b. PUBLISHING PACKAGE (edit/PUBLISH.md)
Every short goes out on YouTube Shorts, TikTok and Instagram Reels, and each platform gets its own copy. One Markdown file for the whole project, with one section per short, in order. If the file already exists from an earlier run, add or update only the sections for the shorts you made; leave the others as they are. Write it after the short is final, from what the short actually says. On every platform, every claim must be backed by the short and hold against the fact check.

The full video. TikTok and Instagram viewers are sent to the full video on YouTube, and the Short links to it with YouTube's Related video field. Use the URL or title I give. Otherwise, when the shorts are cut from a finished long-form edit, take its title from that edit's publishing copy (a davinci-resolve-pro-edit run writes it to pro-edit-media/PUBLISH.md next to the sources). With neither, point to my channel, Leon van Zyl, without a title. Log which one you used in the report. Never invent a URL or a handle.

YouTube Shorts
- Title: under 55 characters (54 at most; count them), so it's never truncated. Its job is the click: a stranger scrolling past must want to know more.
  - At least one power word: Secret, Hidden, Truth, Finally, Never, Stop, Instantly, Free, Proven, Insane, Brutal, Mistake, Beats, Killer, Dead, Exposed, Shocking, or another word with the same pull.
  - Drive curiosity: open a loop the short closes. A bold statement, a surprising result, a contrarian take, or a question with something at stake. Never give the payoff away in the title.
  - Name the tool, model or topic people recognise (e.g. "Sonnet 5.5"), so the title still matches what people search for.
  - Bold, but true: a promise the short doesn't keep loses the viewer in the first second.
  - Every short's title is different. No emojis, no hashtags (they go in the description).
  - Examples, for a short where Sonnet 5.5 is half the price per token but cost almost the same as Opus in a real test: "Sonnet 5.5 Is Half the Price? The Truth Surprised Me" (52), "The Hidden Cost of Sonnet 5.5's Half Price" (42). Not "Sonnet 5.5 vs Opus 5.5: Is Sonnet Really Half the Price?" (56 characters, no power word).
- Description: one or two lines (about 200 characters at most). Natural, keyword-rich wording that says what the viewer learns or sees, using the same search terms as the title.
- Then a blank line, then these two lines exactly as written, in this order, each followed by a blank line:
  🎁 Get the resources from this video + my free AI builder course: https://skool.com/leonvanzyl
  🚀 Go deeper inside Agentic Labs: AI coding courses, live Q&A, weekly challenges, and direct access to me: https://skool.com/agentic-labs
- Then the hashtags as the description's last line: exactly three, each about this short's content: the tool or model, its maker, the topic (e.g. #ClaudeCode #Anthropic #AICoding). CamelCase, no spaces or punctuation inside a tag. No filler that says nothing about the video (#shorts, #viral, #fyp, #trending). Different shorts may share a tag, but pick each short's three for its own content.
- Related video: the full video, to set in YouTube Studio's Related video field. Links in a Short's description aren't clickable (since 2023); this is the one link a Short gets.

TikTok (a video has one caption and no title; TikTok search reads the whole caption)
- First line: the hook, under 100 characters so it shows before "more". The YouTube title's idea in a conversational voice; it still needs the power word and the open loop.
- Then one or two lines with the words people type into TikTok search for this topic (the tool, the task, the problem), said naturally. Specifics beat adjectives: the real numbers, names and results from the short.
- Then the full video, on its own line: 🎬 Full video on YouTube: "<full video title>" (link in bio). With no title: 🎬 Full video on my YouTube channel, Leon van Zyl (link in bio).
- Then the short's CTA in the speaker's words, if it has one: the keyword and what it gets you (e.g. 💬 Want to try this prompt yourself? Comment PROMPT).
- Then 3-5 hashtags on the last line: the same subject tags as YouTube, plus one or two TikTok communities that fit (#TechTok, #CodingTok). No #fyp, #foryou or #viral.
- About 300 characters in all. No URLs: caption links aren't clickable on TikTok.

Instagram Reels
- First line: the hook, under 125 characters (Instagram cuts the caption there with "more"). Same idea as the YouTube title, written for Instagram; power word and open loop still apply.
- Then two or three short lines, one idea each, each separated by a blank line: what the viewer learns or sees, with the natural keywords people search for. Instagram search and Google both read captions.
- Then the full video, on its own line, as on TikTok.
- Then the short's CTA in the speaker's words, as on TikTok.
- Then 3-5 hashtags on the last line. Instagram allows at most 5 (enforced since December 2025); more gets the post blocked or trimmed.
- No URLs: caption links aren't clickable on Instagram.

Layout of each section (every piece of copy in its own fenced code block, so it copies cleanly):
  ## Short NN: <slug>  (file: edit/short-NN_<slug>/final.mp4)
  **Thumbnail** (short-NN_<slug>/thumbnail.jpg, from <time> s: <what it shows>). The YouTube thumbnail and the Instagram cover; on TikTok, upload it as the cover or pick the frame at <time> s.

  ![Short NN thumbnail](short-NN_<slug>/thumbnail.jpg)

  ### YouTube Shorts
  **Title**
  ```
  <title>
  ```
  **Description**
  ```
  <1-2 line description>

  🎁 Get the resources from this video + my free AI builder course: https://skool.com/leonvanzyl

  🚀 Go deeper inside Agentic Labs: AI coding courses, live Q&A, weekly challenges, and direct access to me: https://skool.com/agentic-labs

  #Tag1 #Tag2 #Tag3
  ```
  **Related video:** <full video title or URL, or "the full video, once it's on YouTube">

  ### TikTok
  **Caption**
  ```
  <hook line>
  <1-2 keyword lines>

  🎬 Full video on YouTube: "<full video title>" (link in bio)
  💬 <CTA>

  #Tag1 #Tag2 #Tag3 #Tag4
  ```

  ### Instagram Reels
  **Caption**
  ```
  <hook line>

  <idea 1>

  <idea 2>

  🎬 Full video on YouTube: "<full video title>" (link in bio)

  💬 <CTA>

  #Tag1 #Tag2 #Tag3 #Tag4
  ```

8c. THUMBNAIL (edit/short-NN_<slug>/thumbnail.jpg)
One frame from the finished short: the YouTube thumbnail, the Instagram cover and the TikTok cover. The candidates are chosen while the short is built, never by scanning it afterwards.
- Clean: the picture alone, with no captions, CTA box or cover title. The platforms put the title next to it, and a caption cut off mid-sentence reads as noise.
- What it shows: what the short is about, recognisable at a glance. The product's official logo, its real UI doing the thing, the number or headline the short is built on, a striking result (the game it built, the chart that jumped). The most eye-catching element the short has, not the most typical frame.
- Best is a split, where my head pops out above that element: face plus subject. Next best is a full visual with the element large. Not the outro, not a plain full cam (no subject), and not run 0's opening frames, which leave the top 620 px empty for the cover title.
- The landing state only: the hero fully on screen, sharp and in focus, the camera at rest. No motion blur, no card mid-entrance or half faded, no blurred neighbour in front, nothing cut off by the frame edge.
- My face, when it shows: eyes into the lens and a subtle expression (relaxed or closed mouth, no blink, no mid-syllable grimace).
- It must read at feed size (about 180 px wide): one dominant subject, high contrast, nothing that only works full screen. Keep the subject and my eyes inside the centre 1080x1350 (y 285-1635): Instagram's feed shows the centre 4:5 and its profile grid the centre 3:4.
- How:
  - While building: every graphics composition marks its eye-catching still moments (`thumb` windows, graphics.md). build_gfx.py clips them to where nothing moves.
  - finish.sh then renders only those frames, clean, in parallel while it concatenates. Each is placed in the longest word gap of its window, so the mouth is at rest.
  - LOOK at chk/<sk>_thumbs.png, which shows each frame at full and feed size with the Instagram crop marked, and pick one with `thumbnail.py <sk> --pick <t> NN slug`.
  - If none is strong, add moments with `thumbnail.py <sk> t1,t2` rather than settling.
- The file: 1080x1920 JPEG under 2 MB (YouTube's limit for custom thumbnails), in the short's delivery folder next to final.mp4.
