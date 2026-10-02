---
name: create-youtube-thumbnails
description: Design high-click YouTube thumbnails that show what the video is actually about. Reads the transcript and titles to find the video's payoff, researches proven outliers in the niche with VidIQ (100k+ views), and re-makes one outlier per variant faithfully for this video (its layout, background, palette, type and treatment, measured), with the creator's own photo, the video's real payoff frames and official logos. Renders with ChatGPT image generation through the Codex CLI, then proves every render mechanically against its reference (background and palette drift, text contrast), against the title (a blind "stranger test" subagent must say what the video is about) and at real feed sizes. Delivers 1280x720 variants for YouTube Test & Compare with an HTML report showing where every decision came from. Use it whenever the user wants a thumbnail, thumbnail ideas, A/B thumbnail variants or a better thumbnail for a video, from a YouTube link, a transcript, a recording or just an idea and a hook, even if they never mention a skill.
---

# create-youtube-thumbnails

You are the thumbnail designer. From a video (or just its idea) you produce finished thumbnails whose quality comes from three kinds of fidelity, each enforced by a check rather than by taste:
1. **To the video:** every thumbnail shows the video's own payoff, from the video itself. Never an invented prop.
2. **To the title:** the title states the claim and the thumbnail shows it. A blind stranger shown both must say what the video is about.
3. **To the reference:** each variant re-makes one proven outlier (its layout, background, palette, type style and subject treatment) and changes only the person, the words and the hero content. The image model follows the brief's words over the attached image, so the brief carries the reference's measured DNA.

The first real run broke all three. It produced a blue background where the reference was black and a red one where it was dark, dropped a sticker outline, and showed a Tetris phone for a video about coding agents in a 3D office. Each of those is now caught by a gate before or after rendering.

**The quality contract is `references/thumbnail-spec.md`. Read all of it before planning anything.** Where the user's request differs from the spec, the user wins.

## Inputs and defaults
- **The video (any one is enough):** a YouTube URL (pull the transcript with VidIQ), a transcript, script or recording, or just the idea and the hook. Unpublished is the normal case.
- **The title(s):** every concept pairs with one of them.
- **How many variants:** ask once, with AskUserQuestion, unless the user already said; suggest 3 (YouTube's Test & Compare takes 3). Variants differ in angle (which part of the payoff, which hook, which reference), never in subject. That is the only question; after it, **work fully autonomously** and log every judgement call in the report. If you can't find that many strong on-topic angles, deliver fewer and say why. Never pad the count with off-topic ideas.
- **The brand folder** `~/.youtube-thumbnails/` (`THUMB_BRAND` overrides it):
  - `avatar/`: the creator's photos. If it's empty, ask for one clear front-facing photo, and save any photo the user shares into it.
  - `brand.md`: the likeness words, the creator's face rules, and what has worked on the channel. Read it first. The research refreshes it.
- **The work folder:** `thumbnails-<slug>/` in the current folder unless the user names one.
- **Image generation:** the Codex CLI logged in with ChatGPT, with `image_generation` on (`setup.sh` checks both). Research needs the VidIQ MCP server.

## Workflow
Detailed commands are in `references/pipeline.md`. `SKILL` is this skill's folder, and every script runs inside the work folder.

1. **Setup (seconds):** `bash SKILL/scripts/setup.sh <work> [avatar…]` creates the folders and the shared venv, and checks Codex.
2. **Understand the video and the title:**
   - Get the transcript (VidIQ, a file, or a transcription).
   - Write `brief.md`: the promise, the payoff, the villain, the named products, every claim with the line that backs it, and **the picture of each title** (the one image that makes it believable).
   - Grab real frames of the payoff from the recording into `refs/ui/`.
3. **Research, both at once (`references/research.md`):**
   - a **niche analyst** subagent: VidIQ outliers (100k+ views), the creator's top and recent uploads, competitors, similar thumbnails and keywords. It downloads every thumbnail, builds contact sheets, LOOKs at them, and writes `research/niche.md`.
   - an **asset capture** subagent: official logos as transparent PNGs, and real UI captures with Playwright.
4. **Plan once:**
   - LOOK at the niche sheets yourself.
   - Write `concepts.json`. Each concept has: a title it pairs with, a hero from the video (with its source frame), an angle, and an eligible reference whose layout fits that hero.
   - `dna.py measure` every reference, LOOK at it, and record its full DNA: background, palette, subject treatment, type, hero treatment and grid.
   - Run the **stranger test** on the concept descriptions (`references/review.md`), and drop anything it misreads.
   - Write the briefs from the template in `references/prompting.md` (with a REFERENCE DNA paragraph), then `jobs.json`.
5. **Render:**
   - Run `gen.py jobs.json --check` first. It blocks references under 100k views, missing DNA, a background that drifts from the reference, and unreadable text.
   - Then `gen.py jobs.json --parallel 5`: two renders per concept, spares included.
   - Each job attaches labelled refs: `AVATAR:`, `LOGO: <BRAND>:` (only the logos it shows), `LAYOUT REFERENCE:`, `HOUSE STYLE:`, and `UI:` (the payoff frame) whenever the hero is a scene, a screen or the product.
6. **Prove it:**
   - `dna.py jobs jobs.json`: each render against its own reference. A FAIL means it left the reference's look.
   - `qa.py compare`: LOOK, same composition, outline and type?
   - The **stranger test** on the actual images (`qa.py card` + one fresh subagent). A miss means the concept failed.
   - `qa.py faces`, full-resolution checks (text, hands, logos), `qa.py ladder` (246 and 168 px, greyscale, badge) and `qa.py feed`.
7. **Fix:**
   - `stamp.py` puts the official logo over the model's version.
   - An edit pass (one or two changes) fixes anything else, including a background that drifted.
   - Re-run fidelity and the ladder on every fix.
8. **Deliver:**
   - `qa.py norm` into `thumbnails/A_<slug>.jpg`, `B…` (1280x720, under 2 MB, plus a 1920 master), ranked.
   - `report.py` → `thumbnails/report.html`, **every run**. Each variant appears next to its reference and the creator's thumbnail, with the title it pairs with, the stranger test's answers, the measured fidelity, the reasoning, the brief and the full render → edit → stamp chain. Tell the user where it is.
   - `thumbnails/report.md` (spec section 8), written by you in the main agent.
   - Update `brand.md`.

## Things that are easy to get wrong
Read `references/lessons.md` before improvising. The biggest ones:
- **Inventing the look.** Never choose a background, palette or type style "to make the variant different". It comes from the reference, as measured hex values in the brief. The words win over the image.
- **Inventing the hero.** If the video doesn't show it (a phone game, a brain, logo tiles standing in for "coworkers"), it isn't the hero. And show the link to the title's subject: in a game-world video, the agents' terminals or a Claude Code cue make "AI coding agents" readable. Without them, a blind viewer read the office as "a kids' game".
- **Vague text.** "THEY WORK. I PLAY." and "NEW COWORKERS" told the stranger nothing. Text adds the hook (a number, a result, a reaction) about the same subject as the title. No text beats vague text.
- **Words-only briefs** produce generic AI clip art. Attach the real outlier, the creator's own best thumbnail and the payoff frame every time.
- **The reference rule:** every reference thumbnail comes from a video with **at least 100,000 views**, and among those the highest breakout.
- **Gaze and expression:** eyes go into the lens in every variant, and expressions stay subtle.
- **Logos:** the model redraws them even with the official file attached. Always stamp.
- **Small detail** is texture at 246 px. Go bigger and fewer: one face, one hero, 1-4 words.
- **Honesty:** no number, timestamp, result or brand the video doesn't back up.

## Files
- `scripts/`:
  - `setup.sh`: folders, venv, Codex checks
  - `gen.py`: parallel Codex image jobs and the preflight gates (`--check`)
  - `dna.py`: reference DNA (`measure`), render-vs-reference fidelity (`fidelity`, `jobs`) and `contrast`
  - `qa.py`: `contact`, `compare`, `faces`, `ladder`, `feed`, `card`, `norm`
  - `stamp.py`: official-logo compositing
  - `report.py`: the HTML provenance report
- `references/`:
  - `thumbnail-spec.md`: the contract
  - `research.md`: the two research subagent briefs
  - `prompting.md`: reference DNA and the brief template
  - `review.md`: the stranger test
  - `pipeline.md`: the commands
  - `lessons.md`
- `examples/`: worked runs (concepts, briefs, jobs, report)
- `assets/fonts/`: Poppins, for the QA sheets.
