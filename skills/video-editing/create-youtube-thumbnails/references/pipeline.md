# Pipeline: exact commands

Conventions:
- `SKILL`: this skill's folder.
- `W`: the run's work folder, `thumbnails-<slug>/` inside the user's current folder unless they name one. Every command runs with `W` as the working directory.
- `B`: the brand folder, `~/.youtube-thumbnails` (override it with `THUMB_BRAND`). It holds `avatar/` and `brand.md`.
- `PY`: `$B/.venv/Scripts/python.exe` (Windows) or `$B/.venv/bin/python`.
- Variants are `v1`, `v2` and so on; their renders are `v1a`, `v1b`; edits are `v1a_e1`, and so on.

Contents: [0 Setup](#0-setup) · [1 Understand](#1-understand-the-video) · [2 Research](#2-research-parallel) · [3 Concepts](#3-concepts-and-briefs) · [4 Render](#4-render) · [5 QA](#5-qa-look-at-every-sheet) · [6 Fix](#6-fix) · [7 Deliver](#7-deliver)

## 0. Setup
```bash
bash "$SKILL/scripts/setup.sh" "$W" [avatar.jpg ...]
```
- Creates `W/{research,competitors,refs,prompts,out,qa,thumbnails}` and the shared venv (Pillow, NumPy, OpenCV).
- Copies any avatar photos into `B/avatar/`.
- Checks that Codex is installed, logged in, and has `image_generation` on.
- No avatar yet: ask the user for one (one clear, front-facing, evenly lit photo; 2-3 more angles help).
- Read `B/brand.md` if it exists. It holds the house style, the likeness words and the creator's face rules.

## 1. Understand the video
- **URL:** `vidiq_get_videos_by_ids` (title, description, chapters) and `vidiq_video_transcript`.
- **Transcript, script or outline:** read it in full.
- **Recording only:** transcribe it (`create-video-shorts/scripts/transcribe.py` works, or `npx hyperframes transcribe`).
- **Idea and hook only:** work from those.
- Write `brief.md` (spec section 1): the promise, the payoff, the villain, the named products, the claims with their source lines, and **the picture of each title** (the one image that makes it believable).
- Grab the payoff from the recording, when there is one, into `refs/ui/`: a few clean frames of the thing the video is about (the product, the world, the result). Use ffmpeg at the moments the transcript names. These become the heroes' `UI:` references.

## 2. Research (parallel)
Spawn both subagents from `references/research.md` at once: the niche analyst and asset capture. While they run, think about mechanics, not pictures.

## 3. Concepts and briefs
1. Read `research/niche.md` and LOOK at `research/sheet_niche*.png` yourself, not just the summary.
2. Write `concepts.json`, one entry per variant plus 1-2 spares (spec section 3: the hero comes from the video, each concept pairs with one title, variants differ in angle, never in subject):
   ```json
   {"id": "v1", "title": "I Turned My AI Coding Agents Into a Video Game", "angle": "the payoff: the whole office floor at work",
    "hero": "the cartoon 3D office floor, agent-workers at desks with terminal monitors", "hero_source": "refs/ui/mov_84.png (recording 1:04)",
    "borrows": "bo0260_eric-tech_N7CQdYaeUEE.jpg", "why_this_reference": "face centre with the hero beside it, a dark field that makes the bright scene pop",
    "dna": {"background": "#0D0D0C near-black, flat", "subject": "thick white sticker outline", "type": "...", "hero_treatment": "...", "grid": "..."},
    "house": "owntop01_leon-van-zyl_uZGDO0L-Dr4.jpg", "text": "...", "face": "centre, calm satisfied smile",
    "logos": [], "claims": ["each worker is a real Claude Code or Codex agent (0:07)"], "why": "..."}
   ```
3. **Reference DNA** for every layout reference (prompting.md). Measure it, LOOK at the swatch sheet and the reference, and fill in the concept's `dna`:
   ```bash
   $PY "$SKILL/scripts/dna.py" measure competitors/<ref>.jpg --sheet qa/dna_<videoId>.png     # -> refs/dna/<videoId>.json
   ```
4. **Stranger test, before rendering** (review.md): one fresh subagent, given only each concept's title and a plain description of the thumbnail. Save its answers to `qa/stranger_pre.json`. Drop or rework every concept whose "about" misses the promise.
5. Write `prompts/_common.md` from `SKILL/examples/prompts/_common.md`. Fill in the likeness words from `brand.md` (checked against the photo), and keep the other blocks as they are.
6. Write one brief per concept, `prompts/v<n>_<slug>.txt`, from the template in prompting.md. It needs a REFERENCE DNA paragraph, and its BACKGROUND and TEXT sections must use the reference's measured hex values. Pull the shared blocks in with `{LIKENESS}`, `{GAZE}`, `{LAYOUT REFERENCE}`, `{HOUSE STYLE}`, `{CLAUDE LOGO}` (or your own logo block), `{KEEP CLEAR}` and `{STYLE RULES}`.
7. Write `jobs.json`: two renders per concept, spares included.
   - Each ref's description starts with its UPPERCASE LABEL and a colon: `AVATAR:`, `LOGO: <BRAND>:`, `LAYOUT REFERENCE:`, `HOUSE STYLE:`, `UI:`. Briefs name refs by label, never by number, so a concept with 0, 1 or 2 logos never shifts the others.
   - Attach in that order, and attach only the logos that concept actually shows. Attach the hero's real frame or capture as `UI:` whenever the hero is a scene, a screen or the product.
   - See `SKILL/examples/jobs_example.json`.
8. Preflight it, which takes seconds. Fix every problem it reports before rendering:
   ```bash
   $PY "$SKILL/scripts/gen.py" jobs.json --check
   ```
   `gen.py` refuses to render while any of these remains:
   - a missing ref file, an unlabelled ref or an unfilled `{BLOCK}`
   - a LAYOUT REFERENCE or HOUSE STYLE thumbnail under 100,000 views (looked up in `research/thumbs.json`)
   - a layout reference with no `refs/dna/<videoId>.json`, or a brief with no REFERENCE DNA paragraph
   - a BACKGROUND colour that drifts from the reference's (Delta E over 25 on a flat field, or a different value class)
   - a TEXT fill colour under 3:1 contrast against the background, or against its own box (3 to 4.5 prints a warning)
   - more than 5 reference images on one job (Codex's image tool limit)

## 4. Render
```bash
$PY "$SKILL/scripts/gen.py" jobs.json --parallel 5      # ~60-75 s per image, 10 images in ~2.5 min
```
- Each job runs `codex exec -i <refs…>` read-only. The image is copied out of `$CODEX_HOME/generated_images/<thread>/` to the job's `out`.
- A model the login rejects is skipped automatically. The model that works is remembered in `$CODEX_HOME/thumbnail_gen_model.txt`.
- `--only v2a,v4b` re-runs single jobs; re-running a job replaces its output.

## 5. QA (LOOK at every sheet)
```bash
$PY "$SKILL/scripts/dna.py" jobs jobs.json                                    # every render vs its own LAYOUT REFERENCE -> qa/fidelity/<id>.json: PASS / WARN / FAIL
$PY "$SKILL/scripts/qa.py" compare qa/compare.png jobs.json                     # each render next to its reference: same look? pick the better of each pair
$PY "$SKILL/scripts/qa.py" faces qa/faces.png "$B/avatar/<photo>" out/v1b.png:0.30,0,0.70,0.75 ...   # likeness + gaze + expression
$PY "$SKILL/scripts/qa.py" ladder qa/ladder.png out/v1b.png out/v2a.png ...    # 480 / 246 / 168 px + greyscale + duration badge
$PY "$SKILL/scripts/qa.py" feed qa/feed.png --cands out/v1b.png ... --field competitors --pattern 'bo*.jpg' --title "<title>" --channel "<channel>" --dur <mm:ss>
```
Also open each pick at full resolution and check:
- every letter
- the hands
- each logo next to its file in `refs/`

Then the **stranger test, after rendering** (review.md): make a feed card per pick (`qa.py card qa/cards/<id>.png <render> --title "<its title>"`), and give the cards to one fresh subagent. Save its answers to `qa/stranger_post.json`, keyed by the deliverable name. A miss on "about" means the concept failed: rework the concept, not the render.

Record a pass or fail per check (spec section 6) in the report.

## 6. Fix
- **Logos:** stamp the official file over the model's version, one call per logo. Use a tight search box (fractions of the frame) around the rendered mark:
  ```bash
  $PY "$SKILL/scripts/stamp.py" out/v2a.png refs/claude-mark.png 0.60,0.40,0.86,0.93 out/v2a_s.png --sheet qa/stamp_v2a.png
  ```
  - `--tol 45` suits black marks.
  - `--rot <deg>` matches a tilted card.
  - LOOK at the `--sheet` before and after.
- **Anything else** (text in the badge zone, small UI text, a hand, an expression): an edit pass.
  - Write `prompts/edit_<id>.txt` from the template in prompting.md.
  - Put the job in a separate `jobs_edit.json`, so `compare` keeps reading only the concept renders. Its refs are `THUMBNAIL:` (the render) and `AVATAR:`, plus `LOGO: <BRAND>:` if the change involves a logo.
  - Run it with `gen.py jobs_edit.json`, then re-run the ladder on the result.
- **Rejected likeness, gaze or concept:** re-render from the brief, never edit it.
- **Changed a concept** (a new reference, a new layout, a dropped element): update its `concepts.json` entry (`borrows`, `house`, `face`, `hero`, `why`) in the same step. `report.py` reads the reasoning from there, so a stale entry shows reasoning that no longer matches the image.
- **Naming:** `v2a` (render) → `v2a_e1`, `v2a_e2` (edit passes) → `v2a_s` (stamped, final). When there are two logos, stamp in a chain: `v4a_e1` → `v4a_s1` (the first logo) → `v4a_s` (the second). The file you `norm` is always the last one in the chain.

## 7. Deliver
```bash
$PY "$SKILL/scripts/qa.py" norm out/v5a.png thumbnails/A_<slug>      # -> A_<slug>.jpg (1280x720, <2 MB) + A_<slug>_master.png
```
- One `norm` per variant, lettered by rank. Each `norm` records which file the deliverable came from in `thumbnails/manifest.json`. Spares stay in `out/`.
- Run a final `feed` sheet of the deliverables (plus the current thumbnail, if there is one).
- Build the HTML report and open it. It must say "Reference rule met"; if it lists a violation, re-render that variant with an eligible reference.
  ```bash
  $PY "$SKILL/scripts/report.py" . --url <video URL, if published>     # -> thumbnails/report.html (self-contained)
  ```
  It walks each deliverable back through `*.stamp.json` (stamp.py) and the edit and render logs (gen.py) to the render's attached references. Use the scripts for every step, so that chain stays unbroken.
- Write `thumbnails/report.md` (spec section 8) yourself, in the main agent. Some harnesses block subagents from writing report files.
- Update `B/brand.md` if the research changed the house style.
