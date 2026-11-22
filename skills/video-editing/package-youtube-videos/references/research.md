# Research: what counts as evidence, and how to get it

The trap this file exists to prevent: studying winners. On 2026-11-22 a first research pass collected the niche's best
videos, read "formats that win" off them, and wrote them into the strategy. A control study then compared the top and
bottom thirds of six large channels and found most of those formats just as common on the flops:

| Claim read off winners | Top third | Bottom third | Verdict |
|---|---|---|---|
| A change of state beats naming the feature | 20% | 10% | weak, news topics only |
| A short verdict that isn't the title | 18% | 25% | no difference |
| "X just fixed Y's biggest problem" titles | 6 titles, median 0.97x | | no difference |
| Two or three elements, few words | 45% | 50% | no difference |
| The Claude spark | 56% | 39% | holds, as a topic marker |

What did separate them: the **topic** (news about a release, model or third-party tool: 74% vs 55%) and a **news word
in the title** (43% vs 26%, same direction on all six channels). The same thumbnail format swung 4x to 30x on one
channel depending on the topic. So: format is a hypothesis to test, never a rule. Say so on the page.

**Everything in this table is one run's finding, dated 2026-11-22, on six AI-coding channels (176 thumbnails), and a
hypothesis for the next run, not a rule.** Its limits, from the study's own notes: the samples are small; the measure
is views against the channel's norm, not click-through; one person coded the thumbnails; many comparisons were made
with no correction, so a p of about 0.03 (the news word, and the spark) is not far from what chance alone would turn
up; and the news word is tangled up with news topics, which were themselves more common among the hits. Do not tell a designer or Leon that a
news word, a marker or any layout "works". Run the control again for the video in hand if the strategy leans on any
of it.

## Evidence that separates packaging from topic
1. **Winners and flops from the same channels** (the control study below).
2. **Controlled tests:** YouTube Test & Compare results, on this channel (`vidiq_youtube_ab_test_list`) and the
   results ledger (`test-plan.md`).
3. **The same video before and after a packaging change** (`vidiq_title_thumbnail_wins`). It lists only changes that
   doubled views, so it has no denominator: use it for ideas, not for rates.
4. **One topic across many channels**, only with its confounds named: who published first, second videos on the same
   topic, listicle titles, channel size, and every video on the topic included, not the top dozen.
Never: the channel's daily report, a ranking of Leon's own videos by CTR or views, earlier runs' boards or concepts.

## VidIQ, and its traps
Load the tools with ToolSearch (query `vidiq`). Most calls cost 5 credits; `vidiq_balance` is free.
- `vidiq_outliers` (keyword, `channelIds`, `publishedWithin`, `minViews`, `sort`): what is breaking out.
- `vidiq_channel_videos` (channel, `videoFormat: "long"`, `popular: false`): a channel's latest uploads, hits and
  flops alike. This is the control study's source.
- `vidiq_keyword_research`: search demand for the subject and for what the audience already follows.
- `vidiq_youtube_ab_test_list`: his saved Test & Compare history (controlled tests: the one kind of own-channel data
  that is evidence). Do not pull per-video CTR or views for his own channel to rank or compare his videos: he ruled
  that out, because a video's CTR is mostly its topic.
- **The breakout score hides flops.** It was missing for 77 of 88 bottom-third videos. Never rank or sample by it
  alone. Score every video the same way: views divided by the median views of the 10 videos nearest in publish date
  on the same channel.
- Keyword search is semantic and drifts off topic; read titles before trusting a pool.
- `vidiq_score_title` rated seven very different titles between 91 and 96. It does not discriminate; do not use it to
  choose.
- A private or scheduled video cannot be fetched (`vidiq_video_transcript` fails): use the captions file.
Download thumbnails with `scripts/fetch.py` and LOOK at them (`scripts/sheet.py` builds captioned contact sheets).
Describe thumbnails from looking, never from titles.

## The pool for the blind test
`research/pool.tsv` (one video per line: the video id first, the title last, tab-separated; other columns between
them are ignored) and `research/thumbs/<id>.jpg`: 60 or more real, current videos from the
niche that a viewer of this channel would see in the same feed. Take them from the same channel pulls as the control
study, hits and flops both, so the feed is not all winners.

## The control study (one analyst agent, Opus 5.5 at xhigh, in the background while designs are made)
Run it whenever the strategy leans on a claim about what packaging wins. Brief it with the text below, with the
strategy's claims listed as C1, C2, ... and six channels chosen for this video's niche.

<!-- BEGIN CONTROL -->
You are a sceptical YouTube packaging analyst. Your job is to try to FALSIFY a set of claims a strategist made about
which thumbnail and title formats win in this niche. The strategist studied winners, so the claims may be survivorship
bias: a format seen on top videos may be just as common on the same channels' flops. Find out. A claim knocked down is
a good result.
Work folder: {WORK} (write only inside research/control/). Python: {PY}. Contact sheets: {SKILL}/scripts/sheet.py.
Thumbnails: {SKILL}/scripts/fetch.py.
THE CLAIMS: {CLAIMS}
METHOD
1. VidIQ tools (ToolSearch, query "vidiq"). Budget: {BUDGET} credits; report the balance before and after.
2. For each channel in {CHANNELS}, pull the latest long-form uploads (`vidiq_channel_videos`, popular false). Drop
   videos younger than 7 days. Do not rely on vidIQ's breakout score: it is missing for most flops. Score every video
   as views divided by the median views of the 10 videos nearest to it in publish date on the same channel.
3. Within EACH channel take the top third and the bottom third by that score. Download those thumbnails and build
   contact sheets.
4. Code every thumbnail BLIND: shuffle them onto sheets that show only a code number, code them (the attributes each
   claim needs, plus word count, element count, face, topic marker), and only then reveal which third each is in.
   Describe thumbnails from looking, never from titles. Then code the titles for the claimed shapes and for topic.
5. For each claim give counts and shares for TOP versus BOTTOM, pooled and per channel. With samples this small,
   nothing is proven: say "holds", "weak", "no difference", "reversed" or "can't test", with the numbers.
6. Look for what the strategist missed: does topic type, a news word, a named product, a number, face or no face, or
   length separate the thirds more clearly than any claim? Find pairs where the same format sits at both ends.
7. If the strategy leans on a same-topic comparison, re-examine it: publish order, repeat videos, title type, channel
   size, and whether every video on the topic was included.
Do not use any channel report, do not study the creator's own channel, and do not read outside the work folder.
OUTPUT: research/control/control.md (the per-claim table, the confounds, what was missed, and how much weight format
deserves next to topic), the sheets, and a reply of 15 lines at most.
<!-- END CONTROL -->

When it reports, rewrite the page's research section around what survived, and remove or soften anything in the
strategy and the concept notes that did not.
