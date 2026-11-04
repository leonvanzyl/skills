# The dynamic camera (separate webcam + desktop recordings)

When the recording is a DESKTOP file and a WEBCAM file (`separate-sources.md`), the pro edit's final picture has a
**moving, morphing webcam**: full frame when you talk to the viewer, a large card beside a result, a small corner
window while the viewer watches the screen, hidden under full-frame graphics. Moves are eased morphs at sentence
breaks and cuts; the corner follows the content. It is built in code, the way an editor would build it with Resolve's
Picture in Picture effect, and checked frame by frame.

**This is the standard the user set for separate recordings.** On abacus-test (Pro Edit v3, 2026-11-01) they said:
"I'm extremely happy with that... this is exactly the quality of editing that I expect going forward: with the
transitions, the animations, and carefully deciding where to place the camera." Don't fall back to a static corner
bubble for separate recordings unless the user asks. For composited OBS recordings (webcam baked into the screen) the
PiP stays where the recording has it (editing-spec section 4); none of this applies.

The research behind every rule here, with sources: `pip-research.md`.

## The look
| State | What it is | Geometry (layout px, 1920x1080) |
|---|---|---|
| FULL | the face full frame, at the camera item's own punch-in | the whole frame, radius 0 |
| CARD | a large portrait card on the right; the content in a panel on the left, on the graphite stage | card 756x936 at (1100, 72), radius 22; panel 1000x562.5 at (64, 258), radius 16 |
| SMALL | a corner window | 384 px square (20% of the width), 40 px margin, radius 22 |
| HIDDEN | 0.8x the small window, faded out, in its corner | - |
- One radius, one hairline rim (white, ~28%, 3 px inset at 4K) and one soft shadow in every layout. The content panel
  gets its own shadow. FULL has no rim or shadow.
- Framing: the eyes in the upper third of every window. `dyncam.py cfg` measures the face (YuNet, 24 frames) and
  derives the crops from ratios to the face box that reproduce the approved abacus framing: the small window shows a
  3.17 x face-height square centred 0.47 face-heights below the box centre; the card shows 3.70 face-heights.
- The window and the face inside it are ONE uniform scale centred on one webcam point; the crop is derived from them
  every frame. Scale interpolates geometrically, everything else linearly, on a quad ease-in-out. Never interpolate
  the crop on its own: the face squashes (v2).
- Motion blur: light. 4 samples over a 0.2-frame shutter (~70 degrees), forward from the frame, on moving frames only.
  Resolve's PiP effect has none; a 180-degree shutter on a cubic ease smeared.

## When to move it (the research, applied)
- **Only with a reason, at a sentence boundary, landing in the pause.** Moves start AT a cut, so the face inside the
  window is continuous footage for the whole move (a webcam jump cut inside a move pops). Never move while the viewer
  is reading: motion onset grabs attention even when it means nothing (Abrams & Christ 2003).
- **FULL:** the hook promise, opinions, stories, reactions ("blazingly fast", "crazy impressive"), the CTA and the outro.
- **CARD:** reacting to a result where both you and it matter: the sponsor line beside the real product page, "an
  actual virtual PC" beside the VM, "this scout" beside the game, the pricing line beside the offer. The panel can
  show a captured page (`"content": "image:<png>"`, with a slow 6% push).
- **SMALL:** whenever the viewer reads or watches the screen. **HIDDEN:** full-frame graphics without a facecam, dense UI.
- **Hold every layout ~8-10 s or more**; aim for one change every 20-40 s; no ping-pong. No 1-2 s flash of the face
  (a camera line under 3 s stays SMALL). abacus v3: 26 changes in 8:43 (180/hour, median hold 14 s) and the user loved
  it; the research's ~100/hour is the calmer end.
- **Animate inside a section; hard-cut at chapter changes** (also hides webcam jump cuts), and wherever a move would
  come within ~2 s of another.
- **Durations:** grows 0.5 s, shrinks 0.4 s, card exits 0.45 s, corner hops 0.3 s, hides 0.3 s, a cut (0) out of a
  full-frame graphic into the face. Exits ~20% faster than entries. Quad ease-in-out, never linear.
- **A grow out of a screen or graphic shot holds that shot's last frame** behind the growing camera (`"hold": true`):
  the content cuts at the same frame the move starts, and the held frame keeps the cut from flashing through the
  growing window. The FULL landing framing IS the punch of the shot it lands on (no bump after landing).

## Where to put it (the research, applied)
- **Top-right is the house default** for agent, chat, terminal and IDE demos:
  - YouTube's bottom strip is the most crowded part of the frame: the progress bar and controls on hover or pause,
    captions (pushed up by the controls), and the channel watermark at bottom-right;
  - in AI chat and terminal tools the prompt box and the newest output sit at the bottom: a bottom window covers
    exactly what is typed and read; the top-right usually holds window chrome.
- **The right side beats left or middle** (the only part with real evidence: Zhang et al. 2022 - learning and
  satisfaction highest with the instructor on the right; a middle position drew the most attention away; NN/g's
  F-pattern puts reading attention on the left and the top lines). No study compares top-right with bottom-right;
  bottom-right is only the generic default of tools like Camtasia and Clueso. Loom and Tella start bottom-left.
- **The corner follows the content, not a habit.** Switch corners only when something important is under the window,
  at a cut, and hold the new corner. Never centre it. Earlier edits put the bubble bottom-right by measuring the
  emptiest corner - the user asked why, and the research changed the default.
- Size 18-28% of the frame width (20% used: "smaller than feels right is usually correct"); margins about 1.5-2.5% of
  the width; a rounded rectangle (it morphs cleanly to full frame; a circle only for a tiny bubble).
- Keep clear of the end-screen area in the last 5-20 s and of the CTA card (x 64, y 836, 900x176).

**How `dyncam_plan.py draft` chooses** (the method that reproduced the approved v3 plan):
1. Clutter under each corner of the CONTENT layer (zooms and graphics included, not the raw desktop): Sobel edge
   strength, 2 samples a second (`busy`).
2. Attention targets (`targets`): every zoom mark mapped through its zoom's camera into the frame at the mark's time,
   the CTA cards, and `dyncam_targets_manual.json` for what nobody marked (abacus: the prompt's send button,
   `[106.6, 108.8, 1690, 680, 90, 90, "send button"]` = t0, t1, x, y, w, h, label in layout px). Covering a target
   costs 40x the median clutter.
3. Priors: top-right x0.85, bottom corners x1.25, top-left x1.8 (app logos and navigation).
4. Graphics and B-roll keep the corner they were designed around (`"dyncam_corner"` on the beat; `fvc` without one
   means top-right).
5. A dynamic programme over each SMALL stretch's cut-bounded segments, a switch costing ~8 s of median clutter (so each corner holds).

**Brief the graphics with the camera in mind.** Plan the camera before the graphics agents start: tell them the
window is a 384 px square, 40 px from the edges, top-right unless the beat says otherwise (`fvc` keep-out), and that
`fv` graphics hide the camera. Put the corner on the beat as `"dyncam_corner"`. On abacus the graphics had been built
around a bottom-right bubble, which kept the hook bottom-right (2:38 of 7:02 small) - fine, but not the research default.

## The pipeline
Build the Pro Edit as usual first (SKILL.md steps 1-6, separate-sources.md): it is the static version, the source of
the content layer, and the fallback. Then (`pipeline.md` section 11 has the exact calls):

| Step | Where | What | Time (abacus, 8:43 4K60, RTX 5090) |
|---|---|---|---|
| `rs_content.py` | Resolve | `tracks.json` + `content.mp4`: the Pro Edit without the Camera, Facecam, PE Facecam and PE Overlays clips (PE Censor stays in) | ~2 min |
| `dyncam.py cfg` | W | the face position -> `dyncam_cfg.json` | 15 s |
| `dyncam_plan.py busy`, `targets`, `draft` | W | the draft plan | ~1 min |
| edit `dyncam_plan.json`, `check` | you | the judgment: CARD moments, FULL lines, holds, image content | - |
| `dyncam.py --strip t n` / `--preview` | W | LOOK at every move frame by frame | seconds each |
| `dyncam.py --jobs 8 --tag v1` | W | `$M/layout_v1.mp4` (resumable chunks) | ~30 min |
| `dyncam_qc.py flash` | W | no flash frames | ~1 min |
| `rs_layout.py` | Resolve | "<Pro Edit> - Dynamic Camera": the layer on "PE Layout", overlays re-placed above it, lower tracks disabled | seconds |
| `rs_picture.py`, `master.py deliver` | Resolve, W | the final file (the audio master is the Pro Edit's: same audio) | ~3 min |
| `dyncam_qc.py flash` + `sync` on the final | W | flash frames, face speed and sync in every state | ~2 min |

Proven end to end on abacus-test: the skill's scripts rebuilt Pro Edit v3 from Pro Edit v1 and the render matched v3's
picture pixel for pixel; `dyncam.py` matches the v3 renderer within 0-1 levels; the draft reproduced v3's skeleton.

Fixes: change the plan or code, `dyncam.py patch --keys <t,...>` re-renders +-3 frames around those keys into the
existing chunks (one extra cq-15 generation for those chunks only) - minutes instead of a full render. A changed
layer must reach Resolve as a NEW file (Resolve holds imported files open): `--tag v2` renders `layout_v2.mp4`, then
`rs_layout.py` with `LAYER = 'layout_v2.mp4'` swaps it in place.

## The plan (`dyncam_plan.json`)
The approved abacus v3 plan, every key with its reason, is `examples/dynamic-camera/plan_abacus_v3.json` (and its
`cfg_abacus_v3.json`): read it before editing a draft. An excerpt:
```json
{"start": {"to": "SMALL", "corner": "br"},
 "keys": [
  {"t": 10.65, "dur": 0.3, "to": "HIDDEN", "corner": "br", "why": "the models graphic is full-frame"},
  {"t": 14.883333333333333, "dur": 0, "to": "FULL", "why": "cut to the face on 'push the limits'"},
  {"t": 39.63333333333333, "dur": 0.5, "to": "FULL", "hold": true, "why": "'I'll leave a link...'"},
  {"t": 43.766666666666666, "dur": 0.5, "to": "CARD", "content": "image:C:/.../captures/product_page_2x.png"},
  {"t": 51.083333333333336, "dur": 0.45, "to": "SMALL", "corner": "br", "content": "stem"},
  {"t": 93.11666666666666, "dur": 0.3, "to": "SMALL", "corner": "bl", "why": "keep the send button clear"},
  {"t": 113.0, "dur": 0, "to": "SMALL", "corner": "br", "why": "chapter cut"}]}
```
- `t` is programme seconds: write the exact frame time (`frame / fps`), never 4 decimals (353.5667 is a hair after
  frame 21214; `dyncam.py` snaps on load, but write it exact). `content`: `"stem"` (the content layer) or
  `"image:<png>"`; it persists until a key changes it. `why` is for you and the user; the renderer ignores it.
- **Steer the draft from the edit plan** instead of editing keys by hand where you can: a beat with `"dyncam": "full" |
  "card" | "small" | "hidden"`, `"dyncam_corner"`, `"dyncam_content"` forces that state over its span (zoom beats
  already use `"cam"` for their own camera). Then add what only judgment finds: CARD moments, a FULL on a one-line
  reaction, the image for a card.
- `check` errors: unknown state, overlapping moves, a webcam jump cut inside a move, a missing image. Warnings: a grow
  without `hold` across a content cut, a dur outside 0.25-0.6, moves under 2 s apart, a chapter change that animates,
  a SMALL window over a target, a key between frames. The abacus v3 plan passes with only target warnings.

## How editors do this in Resolve, and why it is rendered
- **Resolve 21's ResolveFX "Picture in Picture"** is the native tool: window size/position separate from the content's
  zoom and pan (no squash), rounding, border and drop shadow built in, keyframed with Ease In and Out. It resizes from
  its centre, so growing out of a corner means keying Position with Width/Height on the same frames. No motion blur.
- The old Inspector route (Zoom + Position with easing) has a known S-shaped-path bug on big moves (Blackmagic forum,
  "an issue for 8+ years"). Motion blur comes from Fusion (Transform/Merge Motion Blur, quality 4-6).
- **The API can't drive any of that** (Studio 21.1.1.10): TimelineItem has no keyframe methods, OFX parameters can't be
  set, and keyframes written into a comp made with `AddFusionComp()` are ignored at render. **`ImportFusionComp(<.comp
  file>)` with BezierSpline keyframes IS honoured** - the route to a natively editable camera (a Transform + rounded
  RectangleMask + shadow per webcam clip). Not built yet; watch the comp's time base (a new empty timeline took the
  project's 24 fps while the source was 60) and the many jump-cut pieces of the webcam.
- So the camera is rendered as one layer (the same model as the PiP effect) and placed on its own track; the static
  Pro Edit stays one toggle away.

## Bugs that were found and fixed (all in the code now)
1. **Ghost frames - the "flicker" the user saw in v2.** The rounded-mask formula `clip(0.5 - d)` with an interior
   distance of `-r` made the WHOLE window 50-80% transparent while the radius was under 0.5 px, the first and last
   frame of every move: a one-frame ghost of the face over the screen, a grey veil when the card opened. Fix: a true
   signed-distance rounded box (`rbox_alpha`), opaque inside at any radius.
2. **Squash mid-morph:** crop and window interpolated independently. Fix: one uniform scale; the crop is derived.
3. **Landing bump:** a grow landed, then the shot's punch-in (1.15x) snapped in. Fix: land on the punch.
4. **Pops inside a move:** moves started 0.5 s before a cut, so a webcam jump cut landed mid-move. Fix: moves start
   at the cut; grows hold the outgoing shot.
5. **Integer stepping:** integer crop boxes stepped on slow moves. Fix: `cv2.warpAffine`, pre-shrinking below 0.6x.
6. **Over-blur:** cubic ease (peak 3x the average speed) with a 180-degree shutter smeared. Fix: quad, 0.2-frame shutter.
7. **Motion-blur samples must run forward from the frame.** Centred samples on a move's first frame (or a cut)
   reached back before the key and blended the previous layout or shot in: half-blend flash frames.
8. **Key times on the frame grid.** 353.5667 s is 21214.002 frames: the move's first frame counted as "before the key"
   for its first blur sample and the incoming shot blended in. Ten of 26 keys had it. Fix: snap on load; write exact.
9. **QC trap, not a video bug:** ffmpeg's input seek (`-ss` before `-i`) lands one frame early in Resolve's H.264 MP4s
   (an edit list): every cut in a Resolve render looked one frame late and the face-sync check said "lag 1" on a
   frame-exact file. Decoding from frame 0 showed every cut on its exact frame. `dyncam_qc.py sync` decodes
   sequentially; never conclude an A/V offset from a seek-based comparison across encoders.
Also from the same project (lessons.md): looped PNG layers without `-framerate` play at 25 fps - the facecam ran 2.4x
fast ("my mouth is moving extremely fast"); `dyncam.py` reads the webcam itself, frame-mapped through `program.json`,
and `dyncam_qc.py sync` proves speed and sync in every state.

## QC (before the user sees it)
- `dyncam.py --strip <move start - 0.1> 40` across a few moves of each kind (grow with hold, card in/out, hop, cut):
  a smooth bell in the frame-difference curve, no ghost, no oval corners, no popping shadow, no squash.
- `dyncam_qc.py flash` on the layer AND on the final file: "flash frames: none".
- `dyncam_qc.py sync <final>`: every state best lag 0, correlation >= 0.85 (abacus: 0.91-0.99).
- Loudness, peak and sync as usual (`master.py deliver`).
- Tell the user the layout changes per hour, the time in each corner and why (graphics designed around a corner,
  content under top-right), and that the static Pro Edit is still there.
