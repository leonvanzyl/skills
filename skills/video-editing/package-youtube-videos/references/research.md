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

**A second run, 2026-11-23, in a different niche (channels where an AI coding tool builds a video game; six
channels, 109 top-third against 109 bottom-third videos, thumbnails coded blind) knocked format down again.** Shares
are among game videos. Same status as the table above: one run's finding, a hypothesis, not a rule.

| Claim read off winners | Top third | Bottom third | Verdict |
|---|---|---|---|
| The subject's own picture fills the frame | 88% | 85% | weak |
| A large, readable AI name or logo | 63% | 60% | no difference: the category's entry ticket |
| A visible change (before and after, prompt and result) | 21% | 35% | reversed |
| A time, effort or cost number in the title | 19% | 6% | weak, most of it one channel |
| First-person titles beat how-to titles | 30% of first-person titles | 62% of how-to titles | reversed |
| Naming a genre or a known product | 51% | 55% | no difference |
| A human face | 26% | 33% | no difference: a channel habit |

What separated the thirds was again the subject: whether the video was in the channel's niche at all (videos outside
it were 13% of top thirds and 24% of bottom thirds), a model named in the title (71% against 51%, possibly release
timing), and a contest ("vs", 30% against 13%). Identical packaging on one channel spread 5x to 68x. Its limits: one
coder, 119 comparisons with nothing surviving correction, thumbnails as served today.

**A third run, 2026-11-24, on channels about AI assistants and automation tools (six channels, 87 top-third against
87 bottom-third videos, thumbnails coded blind).** Same status: one run's finding, a hypothesis, not a rule.

| Claim read off winners | Top third | Bottom third | Verdict |
|---|---|---|---|
| The product's icon, shown large, is the entry ticket | 48% | 51% | no difference, and no ticket: half the hits have none |
| Naming a brand the audience already follows (thumbnail or title) | 91% | 70% | holds, as a choice of subject |
| ...and its logo on the thumbnail when the title already names it | 91% | 88% | adds nothing |
| A comparison frame beats a tutorial frame | 53% of comparison videos | 50% of tutorial videos | no difference |
| FREE on the thumbnail or in the title | 9% | 2% | weak, one channel |
| An outcome phrase on the thumbnail beats the name alone | 8% | 33% | reversed, on all six channels |
| A tutorial title does no worse than a news title | 50% | 58% | holds within noise |
| A human face | 76% | 69% | no difference |

The subject separated the thirds again: news of a release from a platform the audience already uses (33% against
14%), against reviews of one sponsored or niche tool (9% against 22%) and generic tips (14% against 29%). Part of the
outcome-phrase reversal is the sponsored-tool format, which leans on outcome phrases. Three method lessons from it:
- **Check a channel's like rate before using it.** One channel named for the study had a median like rate of 0.04%
  where the others ran 0.3 to 2.1%, and its views sat flat whatever the topic: paid views. Its thirds would have
  ranked ad spend. The analyst swapped it out and dropped four paid-view videos elsewhere; brief the analyst to do so.
- **A same-topic search returns the popular end.** Fifty results for a new product held 4 videos under 1,000 views;
  three date-ordered searches found 42 more long-form videos, 31 of them under 1,000. Search by date as well.
- **Views divided by subscribers falls with channel size** whatever the packaging, so "big channels flopped on it"
  is an artefact. Compare each video with its own channel's norm. And publish order explained most of the spread:
  launch-week videos had a median more than a hundred times that of videos a week later.

Two things worth carrying forward as questions, not answers:
- **The category's entry ticket.** In both niches the topic marker and the subject's picture sat on about two thirds
  of the flops too. They do not win, but a thumbnail without them (the game's own name as the headline, the AI mark
  30 px wide) reads as something else. Check a re-package for a missing ticket before anything cleverer.
- **A video outside the channel's usual subject.** The audience for it is mostly outside the subscribers. Say so on
  the page; the blind viewers, written as the core audience, will pass on it however clear the thumbnails are.

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

## When VidIQ is not connected
It is configured per project, so a session started from a video folder may not have it (2026-11-23: ToolSearch found
nothing and the session's connector list did not show it). Check before planning, tell Leon early, and carry on with
yt-dlp, which is on PATH. What it gives, and the commands that worked:
- **Same-topic videos, hits and flops alike:** `yt-dlp --flat-playlist -J "ytsearch40:<query>"` for a dozen or more
  phrasings of the subject. Each entry has `id`, `title`, `view_count`, `duration`, `channel`, `channel_id`. Dedupe,
  drop anything under four minutes, keep every on-topic video and not the top dozen. Search results lean to videos
  that are already popular and carry no dates: say so wherever the numbers are used.
- **A channel's recent uploads with views:** `yt-dlp --flat-playlist -J --playlist-end 70 --extractor-args
  "youtubetab:approximate_date" https://www.youtube.com/channel/<id>/videos` (or `/@handle/videos`). Entries come
  newest first with `view_count` and an approximate date; the playlist carries `channel_follower_count`. Some
  channels hide views on some rows: drop those rows.
- **A score that does not need VidIQ:** views divided by the median views of the 10 uploads nearest in the list.
  That is the control study's score, so the analyst can work from these files (`research/channels/*.tsv`) instead
  of `vidiq_channel_videos`. Adapt the control brief: point it at the files and tell it there is no VidIQ.
- **The transcript and frames of a public video:** `yt-dlp --skip-download --write-auto-subs --sub-format json3`
  gives timed captions (turn them into `[m:ss] text` lines); a 1080p picture-only download plus ffmpeg gives
  time-stamped contact sheets and full-size frames for the designers and the promise checker.
- **What people type:** `https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q=<query>` returns
  YouTube's search suggestions. Phrases, not volumes.
What it cannot give: search volumes (say on the page that there are none), and his saved Test & Compare history (use
the dated snapshot in the ledger and say how old it is).

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

### Dark ground or bright ground: count it on the control set, every run
Leon wants a dark version of every concept and accepts bright grounds only "as long as they're based on best
practises and what's working in the industry" (`leon.md`, 2026-11-24). So before any concept is given a bright
alternate, measure the control study's own thumbnails. It takes a minute and needs no agent: for each thumbnail in
`research/control/joined.tsv`, resize to 320x180, take the median brightness (luma) of a band along the top and
both sides (the outer 12%), and class it dark under 70, bright over 140, otherwise mid; then compare the shares in
the top and bottom thirds, pooled and per channel. It is a script reading a border band, not an eye, so a subject
that fills the frame is misread: say that on the page.
One run's finding (2026-11-24, 174 thumbnails on six channels in the AI-builder niche): dark 63% of top thirds
and 69% of bottom thirds, bright 17% and 21%, mid 20% and 10%. Dark is the niche's norm and brightness did not
separate hits from flops on any channel. That is not evidence that dark wins; it is the absence of any evidence
for bright. A hypothesis for the next run, not a rule.
