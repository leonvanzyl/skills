# Thumbnail lab

**Retired 2026-11-22.** The `create-youtube-thumbnails` skill this bench tested was removed from the repo on that date
and replaced by `../package-youtube-videos/`, which keeps each video's work in a folder next to the video instead of
here. The notes below describe the old skill and are kept for the record; its files are in the git history
(`git log -- skills/video-editing/create-youtube-thumbnails`). The local `runs/` folder is untouched.

The test bench for the `create-youtube-thumbnails` skill (`../create-youtube-thumbnails/`). The scripts, spec and lessons all live in the skill now; this folder only holds test runs. `runs/` is git-ignored (it's about 130 MB of renders and competitor thumbnails).

- `avatar/leon.jpg`: the reference photo. The skill reads its copy in `~/.youtube-thumbnails/avatar/`.
- `runs/CwL_XeedKw4/`: the first full run, "I Gave Claude a Second Brain":
  - `out/smoke.png`, `out/edit_test.png`: the feasibility tests (Codex image generation plus the edit loop)
  - `out/c*.png`: round 1, briefed in words only. Rejected: generic clip art and look-away gazes.
  - `out/r2/`: round 2, with the real outlier and Leon's own top thumbnail attached. These became the deliverables.
  - `thumbnails/`: the five finals plus `report.md` (copied into the skill as `examples/report_example.md`)
  - `research/`, `refs/`, `competitors/`, `qa/`: the research, assets and proof sheets
- `runs/N2Ogvx_U8uM/`: the fresh-agent test. A new agent used only the skill's files on a different video.

Every finding from these runs is in `../create-youtube-thumbnails/references/lessons.md`.
