# Leon: what holds on every video

Leon van Zyl's channel (@leonvanzyl, about 107K subscribers) teaches building with AI coding agents: Claude Code, Codex,
Cursor, agent harnesses, automation. Viewers build real things with these tools every week.

Every line below says where it comes from, because an earlier version of this file was headed "everything here is
something he said himself" and was not. There are three kinds:
- **[said 2026-11-22]** his words in the session that built this skill, quoted exactly.
- **[earlier, date]** his words as recorded, with that date, in the notes of the older thumbnail skill, which this
  skill replaced on 2026-11-22. That skill and its notes were removed at his request, so the quotes below are all
  that was carried over and can no longer be checked against a source. Only the quotes are carried, not the rules
  that skill built on them. He did not repeat these on 2026-11-22; if one looks wrong for a video, ask him.
- **[our choice]** not his words: a working default, to be dropped the moment he says otherwise.
When he gives new feedback, add it with the date and his exact words. Never add a rule inferred from his analytics, a
report, an earlier run's output, or what one run's checks happened to find.

## His face
- **The two reference portraits** are `assets/leon/leon_front.jpg` (his smile) and `assets/leon/leon_serious.png` (his
  serious look). He calls this his avatar ("the actual avatar image", "the reference image of myself")
  [said 2026-11-22]. They are the references he works from and should not be described as camera originals;
  `leon_serious.png` is a cut-out with a few pink matting specks in the hair that the image model copies. Both were
  taken unchanged from the older skill's avatar folder. So: call them "reference portraits" on the page, never "your
  real photo"; do not clean them by script; if he offers a camera original or a cleaner file, use it. The smile portrait is small (his face is about 360 px tall, where a thumbnail renders it at
  450 px or more), so the image model invents detail when it renders him: that is one reason faces drift.
- **Likeness must be maintained** [said 2026-11-22]: some faces "look a little bit different to the actual avatar
  image. We just have to ensure that my likeness is maintained in these images."
- **Likeness is corrected by the image model, never by a script** [said 2026-11-22]: "Surely it's just a matter of
  sending the reference image of myself to Codex, along with the generated thumbnail, and asking it to correct the
  likeness." Of a scripted blend: "All of the faces are messed up... it's terrible", then "It should definitely not be
  a scripted faceplate. Why on earth would you do that if you've got access to Codex? You definitely need to ensure
  that the skill will not use that face blind script." `references/likeness.md` has the pass.
- **He is the judge of likeness.** On 2026-11-22 an inspecting agent passed, and recommended keeping, faces he called
  terrible. An agent's read is a filter. Say on the page that likeness is his call.
- **He was surprised that broken faces reached him at all** [said 2026-11-22]: "I was surprised by that mistake", and
  he asked for an independent review of the process "for such issues". Nothing with his face goes on a page before the
  likeness pass, the final inspection and a native-size look (SKILL.md).
- **"Close" is not good enough, and the checks must catch it** [said 2026-11-24]: shown ten concepts whose faces had
  been through the likeness pass, five inspections and the orchestrator's own native-size look, and which the closing
  message called "recognisably you", he answered: "those faces do not look good enough at all. The critics should
  have picked that up, and it should have been fixed." Two inspectors had graded faces as blockers that day and the
  orchestrator argued both away with a face-width measurement. Side by side with the portrait the faces were a
  similar man: narrower jaw, greyer hair that flared at the sides, lighter and more squinted eyes, a thinner
  moustache, a wider smile. **[our choice]** A face is delivered only when a stranger shown the crop beside the
  portrait would say "the same photograph of the same man, placed in a new frame"; anything that reads "a similar
  man" is re-rendered before he sees it, and a face blocker from any inspector is acted on, never argued away
  (`likeness.md`, `checks.md` section 3).
- **His portrait goes to Codex as a reference; it is never placed by code** [said 2026-11-26, at the start of the
  next run, answering the question the 2026-11-24 run left open]: "For my avatar and likeness, you can pass
  reference images to Codex when you generate the thumbnails. Simply pass my image to Codex when generating the
  thumbnail. That will sort it out. Do not place the image programmatically." So the route "place his actual
  photograph in the frame by script and let the model render the rest" is closed: do not offer it again.
- **He is not to be asked how his face gets in** [said 2026-11-26, in the session that maintains this skill, about
  that same question]: being asked "tells me something is wrong". "As part of the image generation process, obviously, you're just passing assets like my avatar image to Codex, and then Codex will generate the image, which then includes my reference."
  "I don't know why the agent says this." And: "The face should not be placed using code. You can pass reference images to Codex, and that will add the image to the thumbnail."
  **[our choice]** What to do when a rendered face falls short (render again, then the serious portrait, then
  withdraw; never an empty page, never a question to him) is in `likeness.md`. He has been asked three times for a
  larger portrait and has not taken it up: do not ask again.
- **Eyes into the lens, and no exaggerated faces** [earlier, 2026-10-01, from his saved feedback]: he always looks
  straight into the camera; no look-aways, gasps or open-mouthed shock. At that time a subtle smirk or slightly raised
  brow was acceptable to him. Later [earlier, 2026-11-13] he asked to "fix the goofie face" and "the goofie expression"
  on two picks that used smirk and raised-brow poses, and rejected a raised-brow pose with "it's got a funny
  expression". **[our choice]** Until he says otherwise, use only the smile of the smile portrait or the look of the
  serious portrait, exactly as they are.
- **Not tiny, not in a corner** [earlier, 2026-11-13]: "I've got a massive dislike of those thumbnails where my avatar
  is tiny and squished into the corner or at the bottom of the screen. It looks completely unprofessional." And
  [earlier, 2026-10-23]: "you have my avatar in a tiny corner in the thumbnail, which will not be visible on the
  timeline"; "my avatar is darkened out and barely visible"; "my shoulder is cut off. Why did no one notice that?"
  He gave no number for how big.
- **No glow on him** [earlier, 2026-11-18]: "there's a tendency to go to the extreme with the glow effects, which
  looks AI slopish. Obviously, there shouldn't be glows and things over myself. Please fix these to make it look like
  it was done by a professional thumbnail designer."
- **"Looks nothing like me"** [earlier, 2026-11-04]: said of a generated close-up asked for with mood words ("weary,
  grim") from the smile portrait alone; it came back longer, narrower and older.
- **[our choice]** He wears the navy crew-neck T-shirt of the reference portraits, so every render starts from the
  same person.

## The picture
- [earlier, 2026-10-18] "Those grey backgrounds with the grey, bland gradients do not look professional."
- [earlier, 2026-10-21] "I hate the orange backgrounds." (Orange as an accent was fine.)
- [earlier, 2026-10-17] A blurred blob or halo behind him as separation "looks terrible".
- [earlier, 2026-11-18] "Also ensure that the vibrancy, the brightness, and everything is correct for YouTube."
- **Not clickbait** [said 2026-11-22]: "the thumbnail needs to accommodate the hook of the video... when the user
  clicks on the video and the hook and intro play, and the thumbnail is not aligned with the video (or it's not
  supporting it in a way), then the video could be considered clickbait." The promise check exists for this.
- **Sponsors.** [earlier, 2026-10-22, about a sponsored integration] "This video was not a dedicated video. It was an
  integration with them, but the focus should not be on [the sponsor]... I just do not want you to show the [sponsor]
  logo at any point or the [sponsor] text." For a dedicated sponsor video he has given no rule: ask what the sponsor
  requires (name in the title, logo on the thumbnail, naming rules, pricing mentions) and what he wants shown.
  **[our choice, first run only]** on a dedicated sponsor video the sponsor's product was the answer in the title and
  not the hero of the picture; he has not confirmed that as a rule.

## Evidence he will and will not accept [said 2026-11-22]
- Not his daily channel report, and not rankings of his own videos by CTR or views: "The channel report tells you what
  the sort of outliers are, but that does not make for a successful thumbnail. It's very possible that that outlier is
  due to the topic." And: "let the skill perform the research instead of relying on some report".
- Not the output of earlier runs: "I don't really want you to use anything from the previous runs. I wanted you to go
  into this from a fresh perspective."
- What he asked for: use the tools (VidIQ) to find thumbnails that get lots of views, outliers, and the formulas large
  channels in his niche use. And: "You need to think like a YouTube strategist."
- He wants the work criticised hard, by the agent doing it: "Be as harsh and critical of this process and the results
  yourself as well."

## How he wants it presented [said 2026-11-22]
- "I really do like the report that you give, where you show these different thumbnails along with the motivation at
  the top on what the angle is and who it's for... that needs to be consistent across our future runs as well."
- "I really do like the variants that you gave as well, like a potential dark mode variant."
- **A dark variant of every concept, always** [said 2026-11-24]: "One issue I have is with the bright backgrounds.
  You should always give me a variant with a dark background as well, please. Even if it's not 100% black, it could
  be dark charcoal, whatever, but there should always be a dark variant." That day seven of ten concepts had a dark
  alternative and three had a second bright ground instead (one designer argued his navy T-shirt would sink into a
  dark ground). And a few minutes later, asking for it to go into this skill: "I always need the dark versions as
  well. I'm personally not a fan of bright backgrounds. I'm okay with them being in the mix, as long as they're
  based on best practises and what's working in the industry, but I always need the dark versions as well."
  So: **the dark version (charcoal or near-black) is the main version of every concept**, never optional and never
  the afterthought; a designer who thinks dark is wrong for a concept still makes it and says why in the caveats.
  A bright ground is an extra, offered only where this run's own research gives a reason for it (what the current
  thumbnails in the niche actually use, hits and flops alike), and the page says what that reason is. "It pops" is
  not a reason. The earlier line in the designer brief, "Bright, clear, vibrant", was our wording, not his: what he
  said was that grey, bland gradients look unprofessional and that vibrancy and brightness must be right for
  YouTube, which a dark ground with clean, saturated type and marks satisfies.
- The packaging strategy on the page: "What I also want your artefact or this final report to include is the packaging
  strategy" (how to use YouTube's A/B tests for thumbnails and titles); "If you think that that is a good strategy,
  you're welcome to push back."
- "I should be able to ask for 3 variants and find 3 extremely strong thumbnails."
- **4K upload files, every time** [said 2026-11-23]: asked whether the thumbnails were "at the highest possible
  resolution for YouTube" and told they were 1280x720, he said: "you need to add that rule to the skill then. We need
  the 4K versions of the thumbnails every time, please." The upload folder is 3840x2160 (`report.md`).
- **The title in the file name** [said 2026-11-23]: "The file names for the thumbnails need to include the video's
  title. Apparently, YouTube actually wants that... you can keep the number, like 01. Maybe with Alt, you can have
  that, but use maybe the recommended title from your list in the file names for the thumbnail files." (YouTube's
  help page on custom thumbnails says nothing about file names, so treat this as his preference, not a ranking
  fact, and do not tell him it helps discovery.)

## Re-packaging a published video [said 2026-11-23]
- "You can ignore the existing packaging for this video. It's not really working, so let's go in with a fresh
  perspective." **[our choice]** Look at the old package once, to know what not to repeat and what a stranger takes
  from it, and build nothing on it.

## Keeping the skill current [said 2026-11-23]
- Asked, during a run that hit rate limits: "I would appreciate it if you could add the lessons learned, like the
  rate limit issues, to the global skill as well." **[our choice]** At the end of every run, write what went wrong
  and what was learned into this skill (the "Mistakes already made once" list in `SKILL.md` and the reference it
  belongs to), dated, with findings labelled as one run's findings. Nothing about an unpublished video, a sponsor's
  terms or his channel's numbers.

## Progress during a run [observed 2026-11-23, not his words]
- He asked where things stood three times in one long run, and once what model and effort the subagents were
  using. **[our choice]** Tell him where
  things stand at each stage boundary, and at once when an obstacle changes the time estimate, in a few lines: what
  is done, what is running, what is left, and the new estimate.

## At the end of a run [said 2026-11-23]
- **Put the thumbnails in front of him.** After the page had been published and linked, he asked: "Can I view the
  thumbnails?" **[our choice]** When the page is published, open it for him and attach the images themselves (the
  three to test first), as well as giving the link and the folder.
- **Name one title.** With three packages and a list of titles on the page, he asked: "What title would you
  recommend?" **[our choice]** Say in the closing message, and beside the trio, which single title and thumbnail you
  would pick if he ran no test, and why, in a few lines.
- **Clean up once he has uploaded.** "I've uploaded the thumbnails... Once you're done, please can you remove all of
  the files that you created? The thumbnails I've uploaded, so we no longer need these." **[our choice]** That was
  his request for that run, not a standing order to delete. When he says the thumbnails are uploaded: add the run's
  lessons to the skill, note the upload in the ledger, then offer to clean up, saying what would go and how big it
  is (the work folder holds the only full-size originals outside YouTube). Delete the work folder and scratch files
  only when he says yes for this run, after moving out anything the skill or the ledger still needs. Keep the
  ledger and the skill. Ask separately before deleting the published review page, and before clearing what the
  image tool left in its own folder (see `SKILL.md`, "What a run leaves behind").
- Asked that day whether to clear the 2.3 GB the run had left in the image tool's folder, he answered: "Yes, clear
  them". That was for that run; ask again each time, with the size.

## Models [said 2026-11-22]
- "Opus 5.5 on extra high should be used for all subagents."
