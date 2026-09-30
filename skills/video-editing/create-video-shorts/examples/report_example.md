# Short 01: "Half the price of Opus?"

- **File:** `final.mp4`, 1080×1920, 60 fps, H.264 High, AAC 48 kHz stereo, 52.667 s (3,160 frames).
- **Stems:** `stems/voice.wav`, `stems/sfx.wav`, `stems/riser.wav` and `stems/music.wav`. All run the full 52.667 s, 48 kHz, 24-bit.
- **Cover (frame 0):** "Half the price / of Opus?", written by me from the hook, because no title was given.
- **CTA keyword:** `PROMPT`, from the line "If you want to try out this **prompt** yourself…".

## 1. Inputs and sync
- **Only one source file:** the project folder holds one file, `original.mov`. It is the finished long-form video: a 4K60 screen recording with your webcam as a picture-in-picture (x 3108–3811, y 30–978).
  - For 20.4–26.0 s only, the edit cuts to a full-frame 4K camera shot.
  - There is no separate clean-audio file.
- **Clean audio used:** the embedded stereo PCM track is effectively dual mono (L−R sits at −61 dB RMS), so I used it as the clean audio. Nothing else was available.
- **Offset check:** I cross-correlated L against R at 16 kHz mono over 60 s. The peak is 1.000 at 0 ms lag, with the highest side lobe at 0.061, so the offset is 0 ms.
- **Transcription:**
  - faster-whisper large-v3 transcribed the whole file with word timestamps.
  - Each kept line was then re-transcribed in a silence-bounded window.
  - Each line was force-aligned with wav2vec2 (LV60K) to get precise word edges.
  - Whisper hears "Sonic" for "Sonnet" in your accent. The captions use "Sonnet".
- **Takes:** the source is already an edited video, so there are no re-recorded takes and no swaps were needed.
  - The per-line re-transcription confirmed there are no stutters. "push the the limits" was a Whisper artefact.
  - One countdown word ("one") that Whisper dropped was placed from the RMS envelope. It isn't used in this short.

## 2. The cut (source timecodes → short)
| Line | Source (s) | Text |
|---|---|---|
| L1 | 5.46–13.37 | According to the benchmarks, Sonnet 5.5 gets very similar scores to Opus 5.5, especially on agentic coding tasks. |
| L2 | 13.71–20.10 | And Sonnet 5.5 is about half the cost of Opus 5.5, and about five times cheaper than Fable. |
| L3 | 20.47–25.81 | Now, in my experience, benchmarks can say one thing, but the real-world use case is where it matters. (4K camera) |
| L4 | 26.82–35.45 | I'm going to compare the outputs from both Sonnet 5.5, Opus 5.5 and Fable 5.1 by giving them the exact same prompt. |
| L5 | 175.47–181.16 | …and then we'll have a look at the quality of the games, we'll compare costs and how long it took for each game to complete. |
| L6 | 489.96–492.96 | So Sonnet 5.5 took about one hour and 20 minutes. |
| L7 | 495.67–501.35 | The session also costs about 26, which is only like one dollar away from Opus 5.5. |
| L8 | 623.22–629.80 | I was expecting Sonnet to be a lot cheaper and a lot faster, but it ended up costing the same as Opus 5.5. |
| L9 | 122.79–126.84 | If you want to try out this prompt yourself, you can download it from the free community. (CTA) |

**Editorial trims** (for length, and to keep every run within about 8 s):
- Dropped "This is very similar to Opus 5.5." between L6 and L7.
- Dropped "I must admit," at the start of L8.
- Started L4 at "I'm going to" (dropped "So in this video,").

**Timing rules applied:**
- **Line start:** 40 ms before the first word.
- **Line end:** each line ends at its measured true end (last 10 ms window ≥ −35 dB). It is cut earlier wherever the tail stays below −32 dB for more than 150 ms.
- **Tail fade:** 170 ms, shortened so it never runs past the next sound.
- **J-cut:** the audio leads each picture cut by 50 ms.
- **Pauses and joins:**
  - Pauses over about 220 ms inside a line were cut to 120 ms (60 ms kept each side, butt-joined).
  - Every join is placed at 120 ms loud-to-loud.
- **Result, verified on the final voice track:**
  - No join holds more than 150 ms of quiet.
  - The longest in-line natural pause is 210 ms.
  - A Whisper re-transcription of `voice.wav` reads word-perfect: no clipped or stray syllables.
- **Voice loudness:** normalised to −14 LUFS integrated, with a −1.1 dBFS peak.
- **END:** 52.667 s. Every layer ends exactly on it.

## 3. Eye contact
I sampled 8 frames per kept line, then 100 ms steps around every head turn.

**Rule decisions:**
- **Screen-reading lines:** you are reading the screen through L4, L6, L8 and most of L7, so those are full visuals.
- **L7 split:** the camera shows only from "only" (on-lens from 498.6 s) to "Opus". It hides at "5.5", where you look down at 500.65 s.
- **CTA (L9):** a blink and a downward glance in the first 0.2 s, plus a 0.25 s glance on "download". These are eye glances, not head turns, and the outro must be full cam, so it stays full cam.
- **Baked-in punch-ins:** the long-form's own PiP punch-ins (a 1.15× zoom at 248 s, and small auto-framing shifts at 147.6, 617 and 650.5 s) were detected by tracking the background. No camera run crosses any of them.

## 4. Layout plan (runs tiling [0, END])
| Run | Layout | Time (s) | Dur | Text |
|---|---|---|---|---|
| 0 | split (hook) | 0.000–8.117 | 8.12 | According to the benchmarks … agentic coding tasks. |
| 1 | full visual | 8.117–14.433 | 6.32 | And Sonnet 5.5 is about half the cost … cheaper than Fable. |
| 2 | full cam (4K) | 14.433–19.733 | 5.30 | Now, in my experience … where it matters. |
| 3 | full visual | 19.733–28.033 | 8.30 | I'm going to compare … the exact same prompt. |
| 4 | full cam | 28.033–33.683 | 5.65 | and then we'll have a look … to complete. |
| 5 | full visual | 33.683–39.433 | 5.75 | So Sonnet 5.5 took about 1 hour … $26, which is |
| 6 | split | 39.433–41.333 | 1.90 | only like $1 away from Opus |
| 7 | full visual | 41.333–48.650 | 7.32 | 5.5. I was expecting Sonnet … the same as Opus 5.5. |
| 8 | full cam (outro + CTA) | 48.650–52.667 | 4.02 | If you want to try out this prompt yourself … free community. |

Runs 0 and 3 are 8.1 s and 8.3 s. That is the "about 8 s" ceiling: L4 can't be split because the source has no usable camera during it. No two adjacent runs share a layout, and all three layouts are used.

**Camera geometry:** your camera is a portrait 680×924 PiP safe area, except the one 4K shot. So:
- **Full cam:** the PiP is cover-fitted at 2.08× with light sharpening. Run 2 uses the true 4K centre slice.
- **Split:**
  - **Revision 2 (after your review):** the webcam is scaled 1.35× (918×1247), not 1.8×. That size is set from your measured hair top (webcam y 30–51) and lowest chin (webcam y 614–625). The top of your hair now pops about 100 px above the card at y ≈ 1094–1099, and your whole face down to the collar fits inside the visible card.
  - At 1.35× the portrait webcam no longer spans the full width, so the thin strips at each side of the card are filled with an enlarged, blurred copy of the same frame, feathered over 40 px. This is the same idea as the washed backdrop behind the captures.
  - Above the card edge only the matted head shows: HyperFrames remove-background (u2net), eroded 1 px, feathered 40 px across the card's top edge.
  - The matte and the card use the same frame index on every frame, so they can't drift apart.

## 5. Graphics (6 HyperFrames compositions)
All six were rendered at 240 fps with per-frame directional motion blur along the camera's screen velocity (σ = 0.29 × speed × 0.75/60, capped at 24 px). They were then blended down with `tmix=frames=3,fps=60`. Each was checked on draft contact sheets.

- **Run 0 (split):**
  - Frame 0 holds the official Claude logo at y ≈ 700–820, below the cover title.
  - On "benchmarks" the camera steps (0.5 s, power3.inOut) to the real Anthropic benchmark table for Sonnet 5.5.
  - It glides, then pushes 1.55× onto the Terminal-Bench 4.0 row.
  - A clay highlight band sweeps across Opus 5.5's 66.4% cell on "agentic". Anthropic's own page already highlights the Sonnet column.
- **Run 1 (full visual):**
  - The real claude.com pricing page sits in the fixed capture frame (x 24, y 200, 1032×1040, r 36) on its washed, blurred clone.
  - The inner camera moves from Sonnet 5.5 ($2/$10) to Opus 5.5 ($4/$20) to Fable 5.1 ($10/$50), 0.6 s moves, power2.inOut.
- **Run 3 (full visual):**
  - Named-product intro: the Claude logo, large and centred.
  - One whip (0.45 s out, 0.6 s in, with a whoosh at the midpoint) to the real Claude desktop app model menu.
  - A clay highlight steps to Sonnet 5.5, then Opus 5.5, then Fable 5.1 as you name each one.
  - The inner camera then pans to the prompt text on "exact same prompt".
- **Run 5 (full visual):**
  - Your real Sonnet usage panel, synced footage from 489–498 s.
  - The inner camera pushes to "Active 1h 21m", then to "Cost $25.95". Your own cursor selection of the cost is visible.
- **Run 6 (split):** the two real session cards, Sonnet 5.5 at $25.95 and Opus 5.5 at $27.89. The depth-of-field hand-off goes to Opus on "Opus".
- **Run 7 (full visual):**
  - The same two cards.
  - The camera pushes onto Sonnet's cost ("cheaper") and steps to its time ("faster").
  - It then pulls back to show both cards sharp ("costing the same as Opus 5.5").

Your Claude app runs in dark mode, so the real captures are dark windows in white frames. The ground, cards and type follow the bright spec. Poppins fonts and GSAP are bundled locally.

## 6. Cover, captions and CTA
- **Cover:** frame 0 only. Poppins Bold 110, black, on a white rounded box at y 262–603 with a soft shadow.
- **Captions:**
  - Burned in from the final voice track's aligned word timings, starting at frame 1 (17 ms).
  - 1–3 words per chunk, Poppins Bold 74, white, 10 px black stroke.
  - One highlight after every 2–3 normal chunks, never two in a row, never a function word. Highlights use Instrument Serif Italic (thickened for bold) in #FFFF00, e.g. *benchmarks*, *Opus 5.5*, *cheaper*, *real world*, *same prompt*, *$26*, *$1*, *prompt*, *free community*.
  - Positions:
    - split: 941–1114
    - full cam and full visual: lower third, 1290–1560
    - outro: centre band, 1037–1306
  - Instrument Serif has no bold cut, so the bold is synthesised with a 2 px same-colour stroke.
- **CTA:**
  - One comment box (43, 1344, 994×276) with a default avatar.
  - `PROMPT` is typed at 10 characters per second, starting on the word "prompt", with a blinking clay caret.
  - Then a Post button press.
  - There is no panel and no platform text.

## 7. Audio (all synthesised in numpy/scipy)
Levels are set as peaks relative to the voice peak.

| Sound | Detail | Level |
|---|---|---|
| Whoosh | 1, at the Run 3 whip. Low, airy band-passed noise with its loudest moment exactly on the whip midpoint (21.083 s). The variant rotates per whip. | −9 dB |
| Pop | 1, when the CTA box lands (48.77 s) | −10 dB |
| Key presses | 6, one per typed character of PROMPT | −16 dB |
| Click | 1, the bubbly Post press | −10 dB |
| Riser | 2.6 s low swell (rising 48 → 104 Hz tone plus band-moving air). Its audible end lands exactly on the hook → first-point join at 8.117 s (12 ms end fade). | −12 dB |
| Music | Warm minimal bed (D–Bm–G–A pads, soft plucks, sub, simple reverb) at 92 BPM. Sidechain-ducked under the voice, about −33 LUFS, fades out exactly on END. | about −33 LUFS |

There is no sound on layout cuts, steps, pushes, glides or zooms.

**Mix:** −13.9 LUFS integrated, −1.0 dBFS peak.

The prompt text was cut off after the riser section, so the music level and this report's format are my choices.

## 8. Fact check (2+ sources each)
- **Pricing:** "About half the cost of Opus 5.5, about five times cheaper than Fable" is **correct**. Per MTok, Sonnet 5.5 is $2 in / $10 out, Opus 5.5 is $4/$20 and Fable 5.1 is $10/$50. Sources: claude.com/pricing, platform.claude.com pricing docs, and the Anthropic announcement.
  - These are per-token prices. In your test the per-session cost came out almost the same, and the short says exactly that.
- **Benchmarks:** "Very similar scores to Opus 5.5, especially on agentic coding" is **mostly right, but uneven on coding**:
  - **Terminal-Bench 4.0:** Sonnet leads, 70.6% vs 66.4%.
  - **CursorBench 4.0:** close, 55.5% vs 57.8%.
  - **FrontierCode 1.1:** Opus leads clearly, 54.4% vs Sonnet's 46.2% (Max) or 52.1% (Xhigh).
  - The closest matches are actually knowledge work (GDPval-AA 1844 vs 1846) and computer use.
  - Anthropic itself says Opus 5.5 "remains clearly stronger at complex, open-ended work".
  - The graphic shows the real table rather than asserting "similar".
  - Sources: anthropic.com/claude-sonnet-5-5, the Sonnet 5.5 system card, The Decoder, The New Stack and Simon Willison.
- **Release date:** Sonnet 5.5 was released on September 28, 2026 (the Anthropic page and press).
- **Your session numbers** (read from your own usage panels):

  | Model | Cost | Active | API time |
  |---|---|---|---|
  | Sonnet 5.5 | $25.95 | 1h 21m | 1h 14m |
  | Opus 5.5 | $27.89 | 1h 26m | 1h 20m |
  | Fable 5.1 | $51.40 | 1h 41m | 1h 36m |

- **Disagreement:** "only like one dollar away from Opus" is really **$1.94** ($27.89 − $25.95). The captions keep your words, and the graphics show the real $25.95 and $27.89.

## 9. Judgement calls
- **Missing clean audio:** I used the embedded track, with sync verified as above.
- **Which short:** you asked for one short first, so I built only this one. I chose the Sonnet vs Opus price verdict as the strongest story. Two more are planned from the same source but not built: "Which AI built the best game?" (CTA `GAMES`) and "Get more out of Sonnet 5.5" (CTA `LABS`).
- **Source edits avoided:** your long-form edit already has its own graphics and zooms. Camera runs avoid its punch-ins, and graphics use real captures (Anthropic pages, claude.com pricing, your Claude app, your usage panels) rather than the edit's own "API pricing" card.
- **Menu still:** the Claude app model menu is a still frame (143.95 s) with a clay highlight added to step through the models as you name them. The real menu hover order didn't match your narration order.
- **Compositor:** it now renders each run as a separate process in parallel and joins the segments with stream copy. That took 204 s instead of about 7 minutes.
- **Tools:** everything was built locally in the project: a `.venv` (faster-whisper, torch CPU, mediapipe, opencv, pyloudnorm) and npx HyperFrames. Nothing was installed system-wide.
