# The review page

Leon reviews one page per video. He asked for this format to stay the same from run to run: the motivation at the top
(what the angle is and who it is for), then each thumbnail with its reasoning beside it, with variants, and the
packaging strategy. `scripts/report.py <report dir>` builds it from `<report dir>/data.json`, with images in
`<report dir>/img/`. Publish `index.html` as a private Artifact with the images as supporting files, and republish the
same file path as things change so the link stays the same.

The schema is the list below. If `~/.yt-packaging/report-example.json` exists on this machine, it is a complete real
`data.json` from an earlier run: copy its shape, not its claims. It lives outside the skill because the skill is
published and a real page holds an unreleased video's details. After a run he is happy with, and once that video is
public, you may replace it with that run's `report/data.json`.

## When it is published
**Not before step 9 of the workflow.** Every image on the page has been through the likeness pass, the final
inspection and your own native-size look. He was once shown faces nobody had looked at properly, and it cost his
trust. If he asks to see work earlier, set `banner` ("Early look: faces not yet corrected or inspected") so the page
says what it is.

## Order of the page (fixed)
1. **The angle:** `headline` (the move, in a sentence), `lede` (why, with the numbers), `move` (three short pairs:
   the pain, the change, where the answer goes).
2. **The three to test first:** `trio` (each: concept number, image, a label for its click reason, **its own title,
   the one the test plan pairs it with**, one line on why) and `trio_note`. The reason on a trio card is the idea and
   the hook line that confirms it. Not tap counts from the blind read test.
3. **The launch and test plan:** `plan` (`head`, `note`, `stats`, `steps`, `facts`, `caveat`, `source_url`). See
   `test-plan.md`.
4. **The concepts:** `concepts`, each with `n`, `name`, `reason` (the click reason and who it is for), `words`, `title`,
   `title_alt`, `one_second`, `why`, `evidence` (where the idea comes from, stated without claiming it is proven),
   `img`, optional `alt_img` + `alt_note` (a ground variant, an expression variant), and what the checks found:
   `reads` (what blind viewers expected), `panel` (`picked`, `shown`, `by_viewer`, optional `note`), `promise` (`cls`:
   ok | late | bad, `label`, `text`), `qa` (`label`, `text`), `likeness` (`label`, `text`), `caveat`.
5. **The checks:** `checks` (`note`, `viewers` (column heads), `findings`, `doubts`). Each concept's `seg` list fills
   the per-viewer columns.
6. **The research:** `research` (`head`, `note`, optional `table`, `lists`, `take`): what the control study found,
   including which of your own claims failed.
7. **The titles:** `titles` (key, title, why).
8. **Still open:** `open`: decisions that are his (sponsor requirements, a claim only he can confirm, likeness).

## How check results are shown
- **Agents' reads are shown as reads.** `report.py` draws the inspection and likeness chips in neutral grey whatever
  you pass, and heads the likeness row "Likeness (your call)". Write the label as what it is ("Inspector: no blocker
  found", "Agent's read: close") and the text as what differs from the portrait, feature by feature. Never "clearly
  you", "passed" or "upload-ready".
- **The promise chip is coloured, so it must be honest:** `ok` only when the hook confirms it AND no overclaim above
  MINOR was found; `late` for a late payoff or a MODERATE overclaim; `bad` for a mismatch or a SERIOUS one. A green
  chip above text that says "a moderate overclaim" is a contradiction.
- **Say which version each check saw.** If a concept was reworded or re-rendered after a check, either the check ran
  again (say so) or the row says it predates the change.
- **Blind read test:** lead with the reads. If `tally.py` flagged the taps (ours tapped at more than twice the real
  rate), put that in `panel.note` and in `checks.doubts`, and do not quote the taps anywhere else.

## Writing it
- Write for someone who has not followed the run: plain sentences, his video's own words, numbers with their units.
- Call his two images "reference portraits" or "your avatar reference", never "your real photo" (`leon.md`).
- **Claim only what was done, on the files that are on the page.** "I looked at each at full size" is true only if
  you opened every `out/<id>_full.png` and every native face sheet. "All passed the inspection" is true only if the
  inspection ran after the last change to every image. If something was not done, the page says it was not done.
- State what is not proven. Always include "reasons to doubt this page" (`checks.doubts`): simulated viewers are not
  viewers; an agent's likeness read is not his; what was not tested; what the portraits are.
- Never claim a format is proven. `evidence` says where an idea was seen and whether the control study supported it.
- Before publishing, look at the page once at desktop and phone width, with lazy loading off so every image shows.
- Tell him what changed each time you republish.

## The upload folder
`python SKILL/scripts/tools.py finals report/data.json final` writes the upload files into `final/`: exactly the
images on the page, named by concept (`03_the-specimen.jpg`, `03_the-specimen_alt.jpg`), **each at 3840x2160**, plus
`TEST_ORDER.txt` with the three packages in upload order and the title for each. Leon wants the 4K files every time,
and it is YouTube's recommended size. How it works, and what it needs from you:
- It matches every image on the page, byte for byte, to its export in `out/` and enlarges that export's full-size
  original (`out/<id>_full.png`). So copy `out/<id>.jpg` into `report/img/` unchanged, and never deliver an image
  without its original. If one is missing it stops and writes nothing; fix that rather than uploading 720p files.
- The enlargement is plain: no sharpening, no AI upscaler. The image model renders about 1,672 px wide, so 3840x2160
  is the same picture made bigger. Zoomed to 100% the skin shows the model's texture and letter edges are soft; at
  any size a thumbnail is shown it is scaled back down. Say this on the page in one sentence, so he knows what the
  4K files are.
- Files stay under 2 MB (the limit for uploading from a phone; on a computer it is 50 MB).
After running it, check the folder: every file 3840x2160, one per image on the page. It warns if two packages in the trio share a title. Tell him to
upload from `final/` only: `out/` also holds superseded versions under similar names.
