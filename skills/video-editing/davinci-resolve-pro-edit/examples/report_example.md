# Pro edit report: "YTHD60 - Pro Edit TEST" (example)

A partial test build that proved the pipeline end to end: the whole hook and two body beats of the Sonnet 5.5 vs
Opus 5.5 vs Fable 5.1 video. A full edit follows the same shape with beats through the body. Plan:
`edit_plan_example.json`; graphics config: `gfx_example.py`.

## Inputs
- **Timeline:** "YTHD60 - Clean Cut v1" (made by davinci-resolve-video-edit, then worked on by the editor: two
  mTuber transitions and whooshes on A2). 11:07.6, 3840x2160 at 60 fps, 141 media items + 2 transitions on V1.
- **Sources:** seven 4K60 OBS recordings. `scenes.py`: 140 items are screen + webcam PiP (window 3108, 30,
  702x948 in every file - four files needed the cross-file consensus), 1 item is the full-frame camera (item 3,
  "Now in my experience...").
- **Transcription:** CrisperWhisper 2.0 per V1 item with the foundation cut's hotwords; 2,192 words, 193 sentences.
- **Voice:** -25.7 LUFS integrated (hook -25.1), robust peak -10.7 dBFS. Untouched on A1.

## The hook (0 -> 41.00 s)
hook_end = 41.00 s, the cut under the editor's "Bounce" transition between "...each of these projects." and "First,
let's kick things off with Fable." Every sentence treated; no two beats alike in a row:
| Beat | Time (s) | What |
|---|---|---|
| (V1) | 0.00-5.28 | "I've spent hours playing with Sonnet 5.5..." - the recording (the Anthropic Sonnet 5.5 page) |
| z01 zoom | 5.28-13.55 | Benchmarks slide: push to the chart on "benchmarks" (k 1.22), then onto Terminal-Bench on "especially" (k 1.75); a clay wash over 70.6% / 66.4% on "agentic". |
| z02 zoom | 13.55-20.30 | Pricing slide: push to Input (k 1.6); boxes on $2 ("half") and $4 ("Opus"); step to Fable; box on $10 ("cheaper"). |
| p01 punch | 20.30-26.03 | Full-frame camera, direct-to-camera opinion: static 1.15 punch-in (native transform). |
| w01 words | 23.58-24.70 | "real-world" - Instrument Serif yellow keyword pop. |
| g01 gfx fvp | 26.03-35.63 | Three model cards, camera steps to each as named (depth of field on the others), pulls back, then the real PROMPT.txt lands and the camera pushes onto it on "exact same prompt". Webcam kept in its corner. |
| g02 gfx split | 35.63-40.63 | "quality" -> the real game Fable built (Puttopia); "speed" -> a clay band on Active 1h 41m; "cost" -> on Cost $51.40, both from the real usage panel. Camera card with the head pop-out on the right. Ends at the transition. |

## The body (two sample beats)
| Beat | Time (s) | What |
|---|---|---|
| z03 zoom | 45.50-52.18 | "select Fable 5.1... extra high": push onto the model picker and effort control (k 1.8), box on the Fable 5.1 row, box on "Extra", pull back to V1 framing before the next line on the same screen. |
| c01 cta | 124.90-129.90 | "...download it from the free community": the community card, `skool.com/leonvanzyl` typed from "free", then a Join press. |
| r01 gfx fvp | (mechanics test, not placed) | A resource beat: anthropic.com/claude/sonnet captured with `hyperframes capture`; the capture frame scrolls from the hero to "Availability and pricing" and a marker band sweeps across "Sonnet 5.5 is priced at $2 per million input tokens and $10 per million output tokens". It confirms the page backs up "about half the cost of Opus" ($2/$10 vs the slide's $4/$20). |

## Graphics
- g01: 1920x1080 layout rendered at device scale 2 (UHD), 240 fps with per-frame motion blur, tmix to 60 fps;
  three tiles (Anthropic / model name), the real prompt text as a doc card; 1 pop (prompt landing).
- g02: the game still (7.mkv @ 473.27 s) and the usage row (programme 260.0 s) cut from the recording itself; two
  scaleX clay bands. Split camera from the PiP (678x926 safe area) at 2.02x (cover; fit was 1.87x), hair 96 px
  above the card, pop-out limited to a band around the head. Known flaw: the matte includes a sliver of a guitar
  headstock touching the hair.

## Audio
| Sound | Detail | Level |
|---|---|---|
| Music | chillhop, warm (jazz family), F, 94 bpm, seed 125309, swing 0.57; filtered intro, drop at 5.16 s (end of the first sentence), ducked under speech, fades out 41.00 -> 43.50 s | -43.1 LUFS (18 LU under the hook voice) |
| Riser | 2.6 s, audible end exactly at 41.000 s | -12 dB vs voice peak |
| Pop | 34.10 s (prompt card lands), 124.96 s (CTA lands) | -10 dB |
| Key ticks | one clip for the 20 typed characters, 125.97 s | -16 dB |
| Click | 128.09 s (Join press) | -10 dB |
Nothing on zooms, punch-ins or cuts. Mix preview: -25.7 LUFS, peak -7.3 dBFS (normalise to -14 LUFS on delivery).

## The Resolve build
- `timeline duplicate` of the clean cut -> "YTHD60 - Pro Edit TEST" (kept its transitions, A2 whooshes, markers
  and 00:00:00:00 start). New tracks: V2 PE Graphics, V3 PE Overlays, A3 PE SFX, A4 PE Music, A5 PE Riser (stereo).
- 12 files imported into "Pro Edit/YTHD60 - Pro Edit TEST"; 13 clips placed in one `append_to_timeline`
  (readback-verified); 1 punch-in via `bulk_set_item_properties` (readback exact); 5 chapter markers + the
  "Listen: hook -> content" marker (nudged off frames the clean cut's markers already used).
- `place.py verify`: 13/13 clips exactly where planned, clean-cut tracks untouched. Frame captures checked the
  zoom, the punch-in with the keyword pop (alpha clean), the split and the CTA.
- Edit loop tested: z01 re-rendered with a tighter band (`--tag v2`) and swapped with `replace_clip`.
- Archives made by the MCP (safe to delete): "YTHD60 - Clean Cut v1_archived_v02", "YTHD60 - Pro Edit TEST_archived_v01".

## Judgement calls
- hook_end on the transition's cut rather than after "Let's jump in" (the editor had already trimmed that line).
- g02's split uses the PiP camera (the only camera in that stretch), scaled to cover the card.
- The punch-in placed the eyes at 34% of the height; the eye estimate was corrected afterwards (32% down the face
  box, target 36%).
- Captions: "five point five" -> "5.5" and five hotword fixes ("agent-decoding" -> "agentic coding", "Gentic Labs"
  -> "Agentic Labs"...).
