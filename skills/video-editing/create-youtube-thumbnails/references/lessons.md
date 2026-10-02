# Lessons (hard-won; read before improvising)

**The CubeFarm run: three fidelities broken (2026-10-01)**
The video: AI coding agents as little workers in a cartoon 3D office you walk around in. The brief understood it perfectly. Ten variants still went wrong in three ways, and each now has a gate:
- **The look was invented, not copied.** The spec told every variant to use "a different background and palette" and to "break the pattern with flat orange or blue". So the briefs named cobalt blue where the reference was near-black, and coral red where it was dark; the model followed the words. Measured afterwards, 10 of 24 renders had left their reference's background (Delta E up to 124). The reference block also said "copy the layout, never its artwork", so the reference's white sticker outline was dropped.
  - Now: the reference decides the look; the brief carries its measured REFERENCE DNA; `gen.py --check` blocks a brief whose BACKGROUND drifts; `dna.py jobs` fails a render that drifts.
- **Unreadable text.** Yellow #FFD60A on coral #E5484D is 2.8:1. Now `gen.py --check` measures every text fill colour against the background (under 3:1 blocks).
- **The hero wasn't the video.** Ten variants that had to be "completely different", plus "never repeat the title's words" (the brief even banned AI, AGENTS, GAME), pushed concepts into a Tetris phone ("THEY WORK. I PLAY.") and two logo tiles ("NEW COWORKERS"). A blind stranger test, shown only title + thumbnail, read C as "a gaming or productivity video", J as "a generic AI tools review", D as "a jobs or hiring video", and three office-scene variants as "a kids' game". Only the variant with a visible "Ada · Claude Code" label tied the cartoon office to AI coding.
  - Now: the hero comes from the video's payoff (real frames); each concept pairs with a title; variants differ in angle, not subject; the stranger test runs before and after rendering; and the hero must show the link to the title's subject (terminals, a Claude Code cue), not just the world.

**What makes them good**
- **Show the model the real thing.** Round 1 briefed concepts from research in words only and came back as generic "AI thumbnail" art: 3D clip-art icons, glows, small crowded cards. Round 2 attached the real outlier each concept borrows from plus one of the creator's own top performers, and the output jumped to the outliers' production level. The briefs barely changed. The references did the work.
- **Research decides the concept, not taste.** The first smoke test (a glowing brain, "IT REMEMBERS") looked fine in isolation, and it was the most saturated idea in the niche: about 10 of 24 outliers used a brain or network, and a near-identical "it knows everything" + brain thumbnail did 0.99x on a 1M-subscriber channel. VidIQ's similar-thumbnail search even filed the video's real brain thumbnail with brain-health videos.
- **Bigger and fewer.** Top outliers have a face that fills the frame height, one giant hero (often a glossy app-icon tile) and 1-3 huge words. Anything small (a document inside a brain, a question line in a chat card) is texture at 246 px.
- **Pattern breaks win in a dark niche.** In the feed mock, flat yellow, flat orange and saturated blue stopped the eye. The dark navy variants blended in with the niche's dark-purple neon.
- **Every variant a different idea.** Five variants with five mechanics and five palettes make an A/B test that teaches something. Two takes on one idea don't.

- **Breakout alone isn't proof (the 100k rule).** The first runs borrowed from a 673x outlier that had only 53k views (on a 539-subscriber channel), and from 56-59k-view videos. The creator's rule: every reference has at least 100,000 views. One of his own house-style thumbnails missed it by 156 views (99,844), so the check is strict and mechanical. Searching with `minViews: 100000` found more than enough eligible outliers, several with huge breakouts (467x at 105k views, 222x at 223k).
- **Show your work.** The creator wants to see where every thumbnail came from, every time. `report.py` builds that page from the run's records, so keep the chain unbroken: render with `gen.py`, stamp with `stamp.py`, deliver with `qa.py norm`. A hand-copied file breaks the lineage.

**The face**
- **Eye contact:** the eyes go into the lens, always. The creator reported that look-away thumbnails under-perform, and the niche's top outliers nearly all hold eye contact.
- **Subtle expressions:** a knowing half-smirk, serious, a skeptical raised brow, or a calm closed-mouth smile. "Delighted gasp" and "amazed" came back goofy; never ask for an open mouth or wide eyes.
- **Muscle-level direction:** "slightly amazed" came back as a hand-on-chin smile, so describe muscles, not adjectives. Unspecified hands wander onto the chin, so always say where the hands are, or "arms out of frame".
- **Likeness:** one front-facing photo gave an unmistakable likeness in every render of the first test run (20 of 20, edits included). Naming the distinctive features in words (hair, beard, eyes, skin) helps. Re-attach the avatar on every edit pass.

**Logos and text**
- **The model redraws logos even with the official file attached:** the Claude starburst came back with thinner, more regular rays and a different count, and the ChatGPT Blossom came back as an outlined knot. `stamp.py` finds the rendered mark by colour in a tight box, inpaints it, and composites the official PNG at the same size. It's clean on flat tiles, cards and UI headers. Keep the box tight, or other same-coloured things (an orange cylinder, a glow) join the mask.
- **Text renders reliably at 1-5 words,** including small UI strings ("Which video said storms make antimatter?"). Still read every letter at full resolution.
- **The duration badge:** a full-width headline at the bottom ran into the badge zone. The ladder sheet draws the badge, so the clash is visible; fix it with an edit that lifts and narrows the text.

**Codex image generation**
- **Calling it:** `codex exec --json -s read-only -i <ref> … -` with the brief on stdin. Give every ref an UPPERCASE LABEL and name refs by label in the brief, never by position ("reference image 3" broke as soon as a concept had two logos instead of one). `gen.py` prints the labelled legend and `--check` warns about unlabelled refs.
- **Where the image goes:** it is NOT in the `--json` events. It's saved to `$CODEX_HOME/generated_images/<thread_id>/exec-<uuid>.png`, and the thread id is the first `thread.started` event.
- **Output:** 16:9 briefs come back at 1672x941, in ~50-75 s each. Five jobs in parallel worked without throttling (10 renders in ~2.5 min).
- **Model selection:** the config's default model can be rejected on a ChatGPT login ("not supported when using Codex with a ChatGPT account") even though `models_cache.json` lists it first. `gen.py` falls through the listed models and remembers the one that works.
- **Edit passes:** "keep everything identical except: 1. … 2. …" changes only what was named; the composition, lighting and text survive near pixel-identical. Small drift is normal (a font gets slightly wider, the smile grows a little). One or two changes per pass.

**From the fresh-agent test** (a new agent used only these files, on a second video: 3 variants that passed QA in ~29 min; the friction it hit is fixed in the docs)
- **Likeness words come from the photo, not from memory.** The first `brand.md` said "light blue-grey eyes"; the photo shows brown. The renders followed the photo, but a wrong word is a coin-flip on every render. Zoom into the avatar and check every feature you name.
- **VidIQ outliers drift on tech terms** ("Claude connectors" returned electrical wiring, and "MCP server" returned Minecraft). Use `requireAllTitleTerms: true` and `minEngagementRate: 0.01`, and read the titles before ranking.
- **Old hits mislead.** All-time "popular" pulls in a different era of the channel. Weight the last 12-18 months.
- **Reports:** a subagent can be blocked from writing `report.md`. The main agent writes it.
- **Downloads on Windows:** a shell loop over a list file adds `\r` to every filename. Download with Python.

**Environment**
- **Shell quoting:** long briefs written through bash heredocs broke on quotes. Write briefs with a file-writing tool.
- **Python:** use the brand folder's own venv (`setup.sh`), not whatever `python` is on PATH; that one may belong to another tool.
- **Waiting on logs:** a `.log.json` left from an earlier run can be mistaken for the new result. `gen.py` deletes a job's old output and log when the job starts.
