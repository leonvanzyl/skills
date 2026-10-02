# Research: the two subagents

Start both the moment you know what the video is about. They run in parallel with each other and with your concept thinking. Each one checks its own output by LOOKING at it before reporting. Give each the full brief below, filled in with:
- the video's promise
- the named products
- the work folder
- the channel ID or handle

Contents: [Niche analyst](#niche-analyst) · [Asset capture](#asset-capture) · [thumbs.json schema](#thumbsjson) · [Unpublished videos](#unpublished-videos)

## Niche analyst
VidIQ tools (prefix `mcp__<vidiq-server>__`; load them with ToolSearch). Credits aren't a constraint, so go wide; breadth is what finds the outliers. Make these calls:
- **Topic outliers:** `vidiq_outliers` for 4-6 search terms (the topic, the topic + each named product, the "villain" or old way, and the most-searched adjacent term from the keyword research). Use `contentType: long` and `publishedWithin: sixMonths`, then `oneYear` for thin topics.
  - Set `requireAllTitleTerms: true` for product and tech terms. Semantic matching drifts badly ("Claude connectors" returned electrical wiring, and "MCP server" returned Minecraft).
  - Set `minEngagementRate: 0.01` to drop ad-inflated and re-upload outliers.
  - Run every search a second time with `minViews: 100000`. Only those results can become references (the spec's reference rule). The unfiltered results are still useful research on what's working.
  - Read the titles and throw out anything off-topic before ranking. Keep the highest breakout scores.
- **Your channel:** `vidiq_channel_videos` for the user's channel, long-form:
  - `popular: true` gives the top performers. Weight the last 12-18 months; label older hits by era (a 2023 hit reflects a different channel and audience). Only top performers with 100,000+ views can be HOUSE STYLE references.
  - `popular: false` gives the last ~12 uploads.
- **Competitors:** `vidiq_list_competitors` for the user's channel, then `vidiq_outliers` with those `channelIds` and the topic keyword.
- **Look-alikes:**
  - For a published video: `vidiq_similar_videos` and `vidiq_similar_thumbnails` with its `videoId`. Note what cluster the current thumbnail lands in (it may land outside the niche entirely; the brain thumbnail landed among brain-health videos).
  - For an unpublished video: `vidiq_similar_thumbnails` with a `description` of the planned imagery.
- **Keywords:** `vidiq_keyword_research` (mode `research`) for the main term and 1-2 variants.
- **Score:** for a published video, `vidiq_score_thumbnail` on the current thumbnail with its title. Its critique is a useful second opinion.

Then:
- **Download:** save every thumbnail into the work folder's `competitors/`.
  - Source: `https://i.ytimg.com/vi/<id>/maxresdefault.jpg`, falling back to `hqdefault.jpg` if maxres is missing or under 10 KB.
  - Download with Python (`urllib.request`), not a shell loop over a list file. On Windows, list files get CRLF endings, and every filename picks up a stray `\r`.
  - Names: `<prefix><number>_<channel-slug>_<id>.jpg`:
    - `bo####_` for niche outliers (the breakout score, zero-padded)
    - `owntop##_` and `ownrecent##_` for the user's own uploads
    - `CURRENT_<id>.jpg` for the video's current thumbnail
    `qa.py feed --pattern 'bo*.jpg'` relies on the `bo` prefix.
  - Aim for 25-40 niche outliers plus the user's top 12 and last 12.
- **Subscribers:** `vidiq_get_channels_by_ids` for every channel in the pool. Views next to subscribers is what makes an outlier visible in the report.
- **Record:** write `research/thumbs.json` ([schema](#thumbsjson)). Every entry needs `views`; `gen.py --check` and `report.py` read it to enforce the 100,000-view rule.
- **Sheets:** build these with `qa.py contact` and LOOK at every one. Note which thumbnails still read at 246 px, and why.
  - `research/sheet_niche.png`: the niche at 480 px (`--group niche`)
  - `research/sheet_niche_small.png`: the niche at 246 px, real mobile-feed size (`--width 246`)
  - `research/sheet_own_top.png`: the user's top performers (`--group own_top`)
  - `research/sheet_own_recent.png`: the user's recent uploads (`--group own_recent`)
- **Report:** write `research/niche.md`:
  - a) **House style:** face position and size, expressions, eye contact, text (word count, font feel, colours), logo treatment, backgrounds, recurring layouts. Which of the user's own thumbnails over- and under-performed (with breakout scores), and what each group shares.
  - b) **Niche winners:** one line per top outlier (views, breakout, and what the thumbnail does: face, expression, gaze, words, logos, the visual idea, colours).
  - c) **Rules:** what separates outliers from average videos, as concrete rules with counts ("5 of the top 8 cross out an old way").
  - d) **Saturation:** concepts, objects, palettes and words that are overused (with counts), so the concepts avoid them.
  - e) **Current thumbnail:** for a published video, the VidIQ score and critique plus your own critique at 246 px.
  - f) **Keywords:** a keyword table, and what it means for the split between title and thumbnail.
  - g) **Directions:** 5 concept directions. Each shows the video's real payoff (never an invented prop), pairs with one title, and takes its palette from its reference (never an invented one). Each has the visual, the exact text (0-4 words; the title's key noun is allowed when it's the hook), the face (side, size, a subtle expression, eyes on the lens), the logos and UI, the palette, and **the exact outlier file(s) it borrows from**. That file becomes the concept's LAYOUT REFERENCE, so it must have 100,000+ views.
- **Brand:** update `<brand>/brand.md` with the house style, what over- and under-performed, and the date.
- **Return:** a summary under 400 words.

## Asset capture
Collect clean, official, high-resolution references for every product the concepts may show. The image model gets these attached, and `stamp.py` composites the logos over its renders.
- **Playwright setup:** a scratch folder `refs/_pw/` with `npm init -y && npm i playwright && npx playwright install chromium`, all local.
- **Logos:**
  - the official mark of each product as a transparent PNG of at least 1024 px
  - source: the official SVG (press kit, brand page or the product's own site); use Wikimedia Commons only to cross-check. Never redraw or recolour.
  - rasterise with Playwright, which works the same on Windows with no native dependencies: `page.setContent('<img src="data:image/svg+xml;base64,…" style="width:2048px">')`, then screenshot the `<img>` with `omitBackground: true`.
  - when the mark only exists inside a lockup (symbol + wordmark), crop the symbol out by narrowing the SVG's `viewBox`, or crop the raster at its alpha bounds.
  - also make a `*_on_grey.png` preview, and a white version of a black mark for use on dark tiles
- **UI:**
  - a 2x capture (`deviceScaleFactor: 2`) of the product's real UI from its own public pages. Add a cropped "chat only" or "main panel" version when the UI is busy.
  - When the UI that matters is behind a login (for example Claude's connector settings), use the newest public docs or marketing image, or frames of the creator's own screen recording if they have one. Say which in `assets.md`. The image model only needs the visual style, never the private data.
- **Check and report:** LOOK at every file and confirm it's the current mark, undistorted, with a real alpha channel. Write `refs/assets.md` listing each file with its pixel size, source URL and caveats (rebuilt, recoloured, only a marketing render found, blocked by a bot check).
- Never bypass a login or a bot check. Note it and move on.
- **Return:** a summary under 200 words.

## thumbs.json
A list of objects, one per downloaded thumbnail:
```json
{"group": "niche" | "own_top" | "own_recent" | "current", "rank": 1, "id": "<videoId>", "channel": "...", "title": "...",
 "views": 421079, "subs": 20500, "breakout": 128.89, "engagement": 0.022, "published": "2026-09-06",
 "file": "bo0129_jordan-urbs_yFvl2x8_9gI.jpg"}
```
`file` is relative to `competitors/`. Keep under-100k outliers in the pool for the research. The report shows them faded, and they can never be references.

## Unpublished videos
This is the normal case: the thumbnail is made before the upload.
- There is no transcript or current thumbnail to score. Research the idea: its search terms, the outliers for them, and similar thumbnails by `description`.
- Every concept's claims must stay inside what the user told you the video will show. List those claims in `brief.md`.
