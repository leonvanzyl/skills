# The launch and test plan

Every review page includes the plan for testing the packages on YouTube, written for this video. Leon asked for it,
and it is the only step that produces real evidence: nothing before it is proof of clicks.

## What YouTube's test does
Source: YouTube Help, "A/B test titles & thumbnails", support.google.com/youtube/answer/16391400 (read 2026-11-22;
re-read it each run, the feature changes, and quote it rather than this file if they differ).
- Up to three variants. A test can be **title only, thumbnail only, or title and thumbnail together**.
- The winner is chosen on **watch-time share**, not click-through rate.
- Outcomes: a winner ("clearly outperformed the others based on watch time share"), performed the same, or
  inconclusive. With no clear winner, **the first title and thumbnail uploaded stay on the video**.
- "Your A/B test can take a few days or up to 2 weeks to complete." It can be stopped at any time. **"If a video's
  title or thumbnail is changed during the test, the test will automatically stop."**
- "Testing titles and thumbnails that are too similar to each other can cause tests to run for longer."
- **Resolution:** "If the resolution of any thumbnail is lower than 720p (1280 x 720), all experiment thumbnails will
  be downscaled to 480p (854 x 480)." YouTube's recommended thumbnail size is 3840 x 2160 ("as large as possible"; up
  to 50 MB on a computer, 2 MB from a phone). The skill's upload files in `final/` are 3840x2160, all of them.
- **Where and who:** only on a computer in YouTube Studio, and only with advanced features enabled.
- **Not eligible:** private videos, videos made for kids or for mature audiences, Shorts, scheduled lives, and
  Premieres until they have ended. The help page does not say whether a test can be attached to a video that is
  scheduled (private until its publish time). So for a scheduled upload, tell him: try to attach the test in Studio
  before the publish time; if Studio refuses, attach it the moment the video goes public, and until then set the
  package he would keep anyway as the video's own title and thumbnail.

## What Leon's own tests show
His saved Test & Compare history is his private data, so its numbers are not in this file (the skill is published).
At the start of a run:
1. Pull it with `vidiq_youtube_ab_test_list`. The tool says when it was last saved from Studio; if it is stale, say so
   on the page.
2. Recompute, never quote from memory: how many finished tests ended with a declared winner; the time to a declared
   winner (the fastest, how many came inside three days, how many came after day 7 and by what margin); winners by
   kind of test WITH the number of tests of each kind; and how far apart the variants finished where there was no
   winner.
3. Write the result as a dated snapshot at the top of the ledger (`~/.yt-packaging/ledger.md`), replacing the previous
   snapshot, and use it on the page.
Traps from the first run, so they are not repeated: a count of winners given without its denominator, which made one
kind of test look better than three examples can show; "the variants finished within N points of each other" when N
was the distance from an even split, not the gap between variants; and a rule to stop at day 7 that his own history
contradicted, because his clearest wins were declared later than that. Three tests of a kind are too few to say one
kind works better than another.

## The default plan (argue for a different one when the video calls for it)
1. **One combined test of three packages**, each a thumbnail with its own title, each a different reason to click, all
   confirmed by the hook in their current wording. The argument for it is YouTube's own: variants that differ more
   resolve sooner, and a test started at publish gets the launch traffic. Check the snapshot before saying his own
   history supports it: he had run very few combined tests.
2. **Upload first the package he would keep anyway**, because that is what stays if there is no winner.
3. **Do not touch the title or thumbnail while it runs**: a manual change ends the test. Do not read a leader into
   the first day or two.
4. **Let YouTube finish it** (up to two weeks) unless he has a reason to stop. If he stops it early, he is choosing
   by eye, and the page should say so.
5. **Optionally, a title-only test** afterwards on the winner with the best remaining titles. It runs on a fraction of
   the launch traffic; treat a result as a bonus.
6. **Record the result** in the ledger.
State the trade-off honestly on the page: a combined test says which package won, not whether the title or the
thumbnail did it. Leon's own first idea was thumbnails for 24 hours, then titles; that isolates one variable at a
time, at the cost of a second test on decayed traffic, and a test needs days to resolve, not 24 hours (check the
snapshot for how long his take). If he prefers his order, give the thumbnail test days.

## The results ledger: `~/.yt-packaging/ledger.md`
The one kind of data from his own channel that separates packaging from topic. `setup.py` creates it empty. Read it at
the start of every run, and ask him for the outcome of the previous video's test if it is missing. One entry per test:
```
## 2026-11-24 · <video title> · <video id>
Test: combined, 3 packages, started at publish
A (default): <thumbnail words> + "<title>"  -> <watch-time share>%
B: ...                                        -> ...
C: ...                                        -> ...
Result: Winner B after 3.1 days | Performed same | Inconclusive (ran 14 days)
What it suggests, in one line (and what it does not).
```
Read the ledger as a short list of experiments, never as a rule book: three results do not make a law.
