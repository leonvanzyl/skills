# Editorial rules for the foundation cut

The goal is the version a good editor would hand back before any B-roll: every idea said once, in its best
take, in order, with no fillers, stumbles or noises - and nothing cut that the viewer needs. Think "paper edit":
you are editing a script that happens to be spoken.

The user's recordings are typically: a talking-head intro/hook recorded many times, then a screen-recorded
tutorial where they talk while clicking, re-saying sentences until happy. They silence-cut the timeline in
Resolve first, so each timeline clip is usually one attempt at a phrase.

## Priorities (in order)
1. Complete, clear thoughts - never leave a sentence half-said or a reference dangling.
2. The best delivery of each thought - usually the last complete take.
3. Rhythm - no stutters, no dead restarts, no "okay"/lipsmack clips between thoughts.
4. Continuity - screen state and chronology stay believable.

## Choosing takes
- **Default to the last complete take.** Speakers keep retrying until they're happy; the last full version is
  usually the one they meant. The cold open in the Jev video had ~12 attempts at "Jev from TypeSafe AI is..." -
  the kept one was the final, complete one (clip 29).
- Pick an earlier take only when the last one has a flaw the earlier doesn't (a stumble, a cut-off word, weaker
  wording), e.g. "For this demo, let's add a new facial expression" (67) over "For this demo, I'm thinking,
  let's add..." (68).
- When a section was recorded twice in full (the credits explanation: 310-312 vs 315/318/321), keep one whole
  version rather than mixing - mixing risks repeating information.
- A take that trails off or ends in a cut-off word ("...I'll link to it in the descri-") gets trimmed to its
  last clean sentence boundary, or dropped.

## Always remove
- Lone filler/noise clips: `[UM]`, `[UH]`, `[lipsmack]`, `[breath]`, `[throatclearing]`, and the quiet "okay"
  clips (~0.4 s at -55 to -65 dB - they're the speaker's reset between takes).
- False starts: clips that begin a sentence and stop ("Jev from TypeSafe AI is...", "And within a second was...").
- Restarts inside a clip: "So what happened, so what happened is..." -> keep from the second "So";
  "Whereas, whereas System 2 models..." -> from the second; "And one, and one cool thing..." -> from the second.
  With three attempts in one clip, keep the last ("And just to b- and just to get a little bit b- and just to get
  a little bit technical" -> `[[12, null]]`).
- Fillers inside kept sentences: "for any three-D [UH] and for any three-D work" -> `[[null, 14], [20, null]]`.
- Cut-off fragments: `sk-`, `b-`, `l-`, `ag-` inside sentences when a clean cut exists (verify will tell you).
- Off-script talk: "What am I doing?", "Wait, I've seen this", mumbling at -35 to -40 dB while reading the screen.
- Duplicate information: if two kept clips say the same thing (e.g. "you get a confidence score back" twice),
  keep the better one.

## Keep
- Natural repetition used for rhythm or clarity: "a score from zero to one, one meaning 100%",
  "This will call Jev. Jev will then classify these issues", "this is up to you, you can make it as complex..."
- Conversational tone words ("you know", "look,", "so,") inside otherwise clean sentences - removing them all
  makes the speaker sound robotic and costs micro-cuts. Only cut them when they're part of a stumble.
- Section transitions like "All right, so" / "Right," - keep one, drop the repeats.
- The pauses the user's own silence cut left in. Don't tighten every breath; the foundation cut is for content.
- Dictation to a coding agent read aloud in fragments ("please add... these labels to the GitHub repo... Claude
  running Fable... Codex running... Astra") - it matches what's typed on screen.

## Splicing takes
- Allowed when both halves are clean and the grammar joins naturally:
  "If you want to follow along, you can" (54) + "download the source files from my free community." (57).
- Best join points: a pause, or just before a hard consonant ("you can | download"). Words that run together with
  no pause ("follow along you can") can't be split cleanly - move the join to the next consonant instead.
- Every splice gets a "Listen: spliced takes" marker so the user can check it.

## Order and continuity
- Keep chronological order. In screen recordings the screen changes between takes, so pulling a take from much
  earlier or later can show the wrong screen. Choose among takes that sit next to each other.
- Don't reorder sections to "improve" the story - the foundation cut follows the recording.

## Micro-cuts inside continuous speech
- Removing a 0.1-0.3 s stumble in the middle of fluent speech ("like the sk- current state", "you a l- little bit")
  is worth doing, but it's the riskiest kind of edit. It needs a verified or probed cut point, and gets a
  "Listen: micro-cut" marker.
- If no clean point exists after probing, leave the stumble in - a tiny natural stumble is better than a clipped word.

## Things that are NOT problems
- Hotword leakage: on short or quiet clips the model can output the hotword list itself
  ("Sonnet Opus Fable Claude Code Anthropic"). Treat such a clip as noise/unknown, never as content.
- Transcript misspellings of names (Jev -> "JF", "Jeff", "JEV", "J four") - the audio is fine.
- Hotword over-corrections ("Skool" for "Cool") - cutting decisions don't depend on spelling.

## Worked example: the Jev video, first 90 seconds

| Clips | Transcript (abridged) | Decision |
|---|---|---|
| 0 | `[throatclearing]` | drop |
| 1-28 | ~12 attempts at "Jev from TypeSafe AI is ...", "Okay", `[lipsmack]` | drop all |
| 29 | "Jev from TypeSafe AI is an incredible model, but it's also being overhyped right now. I've seen too many videos calling this a Claude killer, and it's not, it can't even write a full sentence." | keep (last complete hook) |
| 30-33, 35-38 | "But there's one job it can do..." variants, one with "with us bi- but there is one job with us..." | drop |
| 34 | "But there is one job it does better and faster than any LLM." | keep |
| 39 | "And in this video, I'll show you how to use it in a real project, not a demo." | keep (last of three identical takes) |
| 41 | "So let me show you [throatclearing] so let me show you what so let me show you what..." | drop |
| 42 | "So let me show you what we'll build in this video." | keep |

## Duplicate demo sections: check the screen
- When a whole walkthrough appears twice, don't assume both show the same thing. Extract a frame from each
  with ffmpeg (source file + mid source time from items.json) and compare URL bar / titles / level names.
  Sonnet-vs-Opus-vs-Fable video (2026-09-29): the first "Fable" demo actually showed Opus's game
  (localhost:5173, "Jurassic Jungle"); the re-recorded one showed Fable's (Puttopia, localhost:1235). The user
  confirmed: drop the mislabelled demo, keep the re-recording, and keep the section order Fable -> Opus -> Sonnet.
- Repeated "through the power of editing... 3, 2, 1" lines that were abandoned because recording continued live
  get dropped; keep only the one right before the actual time jump.

## Pace benchmark
First project: 45% of the silence-cut timeline removed (31:04 -> 17:10), ~214 kept ranges from 509 clips,
~57 cuts inside clips. A result far from that isn't wrong, but check whether you're under- or over-cutting.

## User feedback log
Add the user's reactions to each edit here so the rules keep improving.
- 2026-09-26, Jev video: "excellent job", "phenomenal" - no pacing complaints. Keep this level of cutting.
- 2026-09-29, Sonnet 5.5 vs Opus 5.5 vs Fable 5.1 video: 399 clips, 22:59 -> 142 clips, 11:11 (51% removed).
  User confirmed CrisperWhisper + hotwords is the right setup, and the mislabelled-demo call. Pacing feedback pending.
- 2026-09-30, Cubefarm demo (cubefarm-demo project): 336 clips, 23:11 -> 192 clips, 16:09 (30% removed, 45 in-clip
  cuts). Lower than the 45-51% of earlier videos: many clips were already single clean takes. Two things QA caught:
  a stutter the first transcript hid ("I am" was really "I, I'm") and a word said twice across a silence-cut
  boundary ("career advice, issues || issues, new model releases"). Pacing feedback pending.
