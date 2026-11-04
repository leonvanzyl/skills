# Animated webcam (PiP) layouts: how, when and where

Research notes for a 4K60 tech/AI tutorial edit (screen recordings plus a separate webcam recording) in DaVinci Resolve Studio 21. Compiled 2026-11-01.

**How to read these notes.** Every claim has a source link next to it. The most reliable sources are Blackmagic's own documents:
- the Resolve 21 New Features Guide (NFG21);
- the Resolve 21.1 Reference Manual (Sept 2026) installed on this machine at `C:\Program Files\Blackmagic Design\DaVinci Resolve\Documents\DaVinci Resolve.pdf` (cited below as "Manual 21.1, p.N"; public copy via https://www.blackmagicdesign.com/support/family/davinci-resolve-and-fusion);
- the scripting docs installed at `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\` (README "Last Updated: 31 Aug 2026", CHANGELOG "1 Sep 2026", `DaVinciResolveScript.pyi`).

Lines marked **(inference)** are my own reasoning, not something a source says.

---

## A. HOW editors build an animated, morphing facecam in Resolve

### A1. Native routes and which Resolve version added them

| Route | What it gives you | Version | Source |
|---|---|---|---|
| **ResolveFX "Picture in Picture"** (Effects > Resolve FX Transform) | One effect does the whole facecam. **Content**: Zoom, Pan, Tilt of the source inside the window. **Position**: X/Y, Width, Height of the window. **Style**: Rounding "from right angles (0) to circle (1)", Rotation, Opacity, Border (width, colour, opacity), Fill, Drop Shadow (Strength, Color, Drop Angle, Drop Distance, Expand, Blur), Use Alpha. Works on the Cut and Edit pages, and on the Color page if you add an Alpha Output. | **New in 21** | NFG21 pp.97-99 https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_21_New_Features_Guide.pdf ; Manual 21.1 pp.3704-3705 ; feature list (Scott Simmons, ProVideo Coalition, 4 Jun 2026) https://www.provideocoalition.com/davinci-resolve-21-released-in-record-time-including-the-ipad-version-with-the-new-photo-page/ |
| **Inspector Transform + Cropping** (Edit page) | Zoom X/Y "can be linked to lock the aspect ratio... or released to stretch or squeeze". Position, Anchor Point. Crop Left/Right/Top/Bottom are "in pixels", plus Softness and "Retain Image Position". **No rounding, border, shadow or motion blur.** | All versions | Manual 21.1 pp.919-921 ; DaVinci Resolve Club (Jason Miller) https://davinciresolveclub.com/davinci-resolve-picture-in-picture/ |
| **ResolveFX Transform** | Position, Zoom, Width/Height, corner pin. Crop, **Edge Rounding** ("rounds the corners of the Alpha channel"), Edge Softness. A **Motion Blur** slider ("Keyframing the transform so the frame moves rapidly will create a blurring effect"). Edge Behavior: Transparent. | Added in **17** | Manual 21.1 pp.3720-3722 ; Resolve 17 list of new FX https://www.redsharknews.com/davinci-resolve-17-is-now-out-of-beta |
| **ResolveFX Video Collage** | Grid tiles with Rounding, Tile Styling (border, fill), Drop Shadow, intro/outro Tile Animation (Fly, Shrink, Rotate, Fade). Its "Easing & Blur" section has Motion and Size Ease (None, Linear, In, Out, In & Out), Ease Amount, and a **Motion Blur** slider. | Added in **17**; **21** added separate tile fill and border controls | Manual 21.1 pp.3723-3735 ; NFG21 p.97 ; JayAreTV PiP tutorial (Justin Robinson) https://jayaretv.com/edit/picture-in-picture-tutorial/ |
| **Fusion** (Rectangle mask with Corner Radius, Shadow node, Transform/Merge motion blur) | Full control and true motion blur. Rectangle **Corner Radius** runs from 0.0 (sharp) to 1.0 (maximum). It is relative, not pixels. The Shadow node makes a drop shadow from alpha. | All versions; **21** added a new Macro Editor with live inspector preview and "publishing to edit effects" | Manual 21.1 (Rectangle mask, Shadow node) ; NFG21 p.112 ; Simmons list above ; DaVinci Resolve Club rounded corners https://davinciresolveclub.com/round-corners-davinci-resolve/ |
| **Blackmagic's sample "Rounded Window" Fusion generator** | A macro around a RectangleMask that exposes Width, Height, CornerRadius (default 0.25), SoftEdge and BorderWidth. A ready-made starting point. | Ships in the Developer folder | `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Fusion Templates\Generators\Rounded Window.setting` |
| **Smart Reframe** (Studio) | Reframes footage for aspect-ratio changes using the Neural Engine. **Not a PiP tool**: a May 2026 forum post asks for it to be integrated into the PiP effect. | 17+ | Manual 21.1 p.920 ; https://forum.blackmagicdesign.com/search.php?keywords=picture+in+picture+effect+21&terms=all&sf=titleonly&sr=topics |

Key points for building the morph:

- **The 21 PiP effect separates the window from the content.** Width and Height change the box, while Content Zoom, Pan and Tilt frame the face inside it. You can therefore morph a square bubble into a 16:9 full frame without distorting the face. This is what makes it the best native route (NFG21 pp.98-99).
- **Gotcha: the PiP window resizes from its centre.** A forum user (kaiyo90, 11 Oct 2026) asks for an anchor point because resizing "resizes from the center so you need to constantly resize, reposition". In practice, to grow out of a corner you must keyframe Position along with Width and Height. https://forum.blackmagicdesign.com/viewtopic.php?f=33&t=240807
  - **(inference)** The pinned corner is centre ± size/2. That is linear, so if Position and Width/Height share the same keyframe times and the same easing, the corner stays put through the whole move.
- **Rounding is relative, from 0 to 1 (1 = circle).** Use 1.0 for a circular bubble, then lower it as the window grows. **(inference, verify in Resolve)** The pixel radius probably changes with window size, so keyframe Rounding as well if you want a constant-looking radius.
- **Older Edit-page route (Transform + Crop):** DaVinci Resolve Club warns that "Zoom scales the whole V2 image rather than a fixed PiP boundary". If you transform after masking, rounded corners turn oval, so "Transform the source before a masked Merge". https://davinciresolveclub.com/davinci-resolve-picture-in-picture/ , https://davinciresolveclub.com/round-corners-davinci-resolve/
- **Finishing practice:** colourist Patrick Inhofer (Mixing Light, 2016) rebuilt dozens of PiPs on the Edit page by stacking layers, cropping each box and "keyframe the crops". He chose the Edit page over Color-page crops because the timeline shows the layer hierarchy clearly. https://mixinglight.com/color-tutorial/advanced-finishing-techniques-dealing-with-picture-in-picture-effects/
- **Alternative build: holes in the background.** Video Collage can work this way. The background becomes "a layer with holes cut out", and the clips sit underneath and are positioned with Transform and Crop (Justin Robinson, JayAreTV). https://jayaretv.com/edit/picture-in-picture-tutorial/

### A2. Keyframe technique for a smooth, professional move

**Interpolation tools on the Edit page (Resolve 20 and 21)**
- Resolve 20 brought an "Upgraded Keyframe and Curve Editor" that "fully replaced the older version". https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_20_New_Features_Guide.pdf
- In the Inspector, right-click the orange keyframe button and choose Ease In, Ease Out, Ease In and Out, or Linear (Manual 21.1 p.1251).
- The Curve Editor toolbar has Linear, Ease In, Ease In and Out, Ease Out, Step In, Step Out, Flat Handle, draggable Bezier handles and a Shape Box. "To change the interpolation of multiple keyframes", select them and click one of the Bezier buttons (Manual 21.1 pp.1261-1262).
- New in 21:
  - Step In/Out, Loop, Ping Pong and Reverse (NFG21 pp.63-65).
  - Keyframing across several selected clips at once (NFG21 p.62).
  - Keyframing Fusion effect, generator and title parameters in the Edit-page Keyframe Editor (NFG21 p.66).
  - "Subframe support for keyframing" (Simmons list).
  - Retime curves using the same 4-point Bezier easing (NFG21 p.62 ; Justin Robinson, JayAreTV https://jayaretv.com/news/new-keyframe-and-curves-editor-in-davinci-resolve-21/).
- **Dynamic Zoom Ease** (Linear, Ease In, Ease Out, Ease In and Out) applies only to the Dynamic Zoom pan-and-scan, not to PiP moves (Manual 21.1 p.921).

**Known Edit-page easing bug, and how to avoid it**
- Blackmagic forum, Andy Fed (Resolve 19.1.4, Apr 2025): when Zoom and Position are both eased, the subject "moves along an S-shaped spline at the beginning and at the end".
- Replying, philipbowser says it "has been an issue for 8+ years". The new keyframe panel in Resolve 20 made it "a little bit better", but it is "still much more challenging to do accurate keyframe easing compared to the Fusion page". https://forum.blackmagicdesign.com/viewtopic.php?p=1141853
- What helps:
  - set the Anchor Point to the corner you want pinned, so only Zoom animates (the forum poster mentions this option);
  - use the PiP effect, where box, position and content are separate parameters;
  - or do the move in Fusion.

**Easing in Fusion**
- "By default, Fusion keyframes are linear."
- In the Spline Editor (F8): select the keys and press Shift+S for smooth, T for numeric Ease In/Out, or F for flat (Cameron Jeffords, Mt. Mograph, Apr 2026). https://mtmograph.com/blogs/tools/easing-curves-in-davinci-resolve-fusion-a-motion-designers-guide
- Fusion's Spline Editor has an Ease In/Out dialog (Manual 21.1, Fusion Spline Editor chapter).

**Durations and curves (UI-motion research and tools)**
- NN/g (Page Laubheimer, 2020):
  - most animations fall in "the range of 100–500 ms"; 400 ms is "a very slow animation, to be used only for big movements across large screens";
  - entrances should be slightly longer than exits (e.g. 300 ms in, 200–250 ms out);
  - default to ease-out, and avoid linear;
  - "It is far more common for animations to be too long than too short."
  - https://www.nngroup.com/articles/animation-duration/
- Broadcast-style squeezeback rebuilt for the web (Dave Kiss, Mux, Aug 2026): 850 ms with `cubic-bezier(0.65, 0, 0.35, 1)`, a strong ease-in-out. https://www.mux.com/blog/the-broadcast-squeezeback-rebuilt-with-css-grid-and-webvtt
- **(inference)** For video, which is watched passively rather than clicked, editors usually go a little slower than UI motion. 0.35–0.6 s (21–36 frames at 60 fps) for a bubble ↔ full-screen morph is consistent with both sources.

**Animate crop and scale together, and never squash the face**
- Keep Zoom X and Y linked (Manual 21.1 p.919).
- In the PiP effect, change the box with Width/Height and keep Content Zoom uniform (NFG21 p.99).
- If you crop on the Edit page, drive every crop edge and the zoom from keyframes at the same frames with the same ease. Otherwise the edges "lead" or "lag" the scale (**inference**, consistent with the S-curve bug above).
- In Fusion, put the per-move transform before the masked Merge (DaVinci Resolve Club rounded corners).

**Motion blur**
- The Edit-page Inspector Transform has no motion blur (Manual 21.1 pp.919-921).
- Options that do:
  - ResolveFX Transform's Motion Blur slider (Manual 21.1 p.3722);
  - Video Collage's Motion Blur slider for tile animation (p.3735);
  - in Fusion, the Motion Blur checkbox on Transform or Merge. Quality defaults to 2 ("two samples on either side"); Shutter Angle defaults to 100, and 360 equals a full-frame exposure (Manual 21.1, Fusion common Settings tab). https://davinciresolveclub.com/davinci-resolve-motion-blur/
- ResolveFX Motion Blur (Studio) uses "optical-flow based motion estimation" on picture content (Manual 21.1 p.3520, Color page Motion Effects; p.3681, ResolveFX Motion Blur). It is meant for footage motion, not for a transform you keyframed. **(inference)** Applied to an adjustment clip it would also blur the cursor and scrolling underneath.

**Flicker and jitter**
- Larry Jordan (Resolve 20): "All keyframe animation MUST be rendered to play smoothly." Turn on Render Cache before judging a move. He also prefers typed Inspector values to dragging handles in the viewer. https://larryjordan.com/articles/add-and-modify-keyframes-in-davinci-resolve-20/
- Resize filter: "Sharper: Usually provides the best quality in projects using clips that must be scaled up..." (Manual 21.1 p.146). It is also settable per clip (`ResizeFilter` in the API).
- Mixed frame rates: a webcam at 30 fps on a 60 fps timeline duplicates frames. Retime Process (Nearest, Frame Blend, Optical Flow) controls this (Manual 21.1 Project Settings ; tryuncle note https://tryuncle.com/learn/davinci-resolve/davinci-resolve-mixed-frame-rate-timeline-jittery). Best fix: record the webcam at 60 fps.

**Making it repeatable**
- **Inspector Presets:** "Create Preset" from a section header (Transform, Cropping, Composite...) saves to Effects > User Presets. The manual describes static values (its example is a 1.5x zoom) and doesn't say whether keyframes are saved (Manual 21.1 pp.938-939).
- **Paste Attributes** (Option-V) copies keyframed attributes with "Maintain Timing or Stretch to Fit". 21 adds Retain Image Position for crops (Manual 21.1 p.1155 ; NFG21).
- **Fusion macro or template:**
  - save to `...\Fusion\Templates\Edit\Effects\`. Blackmagic's README recommends driving animation with the **Anim Curves** modifier (Easing presets Sine, Quad, Cubic, Quart, Quint, Expo, Circ, Back...) so it "will speed up and slow down automatically to match the edit duration";
  - bundle as `.drfx`;
  - add "Create Transition Preset" for user presets;
  - source: `Developer\Fusion Templates\README.txt` (local).
  - 21's Macro Editor publishes macros to edit effects (NFG21 p.112).
- **Video Collage presets** and Paste Attributes: once the layout is set, paste the instance to the other clips; tile keyframes can then be offset with Synchronize Keyframing (Manual 21.1 p.3730).
- **PowerGrade / .drx:** the PiP effect can live on a Color-page node with an Alpha Output (NFG21 p.98). A keyframed node can be saved as a still and re-applied (see A3).
- **Plug-ins:** Stirling Supply's "Picture-in-Picture Pro" (Edit-page PiP, with a 21 update that adds an "Anim tab") and "Easier Ease" exist. I haven't evaluated them. https://stirlingsupply.co/products/picture-in-picture-pro

### A3. Can the scripting API set Transform/Crop keyframes? (Resolve 21.1)

- **No.** `TimelineItem.SetProperties()` / `GetProperties()` cover static values only:
  - `Pan`, `Tilt`, `ZoomX/Y`, `ZoomGang`, `RotationAngle`, `AnchorPointX/Y`;
  - `CropLeft/Right/Top/Bottom`, `CropSoftness`, `CropRetain`;
  - `DynamicZoomEase`, `Opacity`, `CompositeMode`, `RetimeProcess`, `ResizeFilter`, and others.
  - There are no keyframe methods for these. `SetProperty()` is now deprecated in favour of `SetProperties()`. Source: local `DaVinciResolveScript.pyi` (TimelineItemProperties, class TimelineItem) and README.
  - The only keyframe-related API is `Resolve.Get/SetKeyframeMode` (Color page) plus read-only stereo keyframe getters.
- **The PiP / ResolveFX parameters on the Edit page cannot be scripted at all.** A forum post in the "Scripting API Wishlist" thread (21 Oct 2026, after 21.1) says "scripts can't see any of it; SetProperty only touches the native Transform". The author asks for `AddOFXKeyframe(...)` and notes "today the only ways are Fusion or a .drx still". https://forum.blackmagicdesign.com/viewtopic.php?f=44&t=235665
- **The 21.1 API additions** (CHANGELOG): `TimelineItem.AddTransition`, fades, speed (`SetSpeed`, including `StretchKeyframesToFit`), output blanking, audio properties, multicam. **No transform keyframes.**
- **Repeatable routes that work:**
  1. **Fusion comps.**
     - `TimelineItem.AddFusionComp()` / `ImportFusionComp(path)` / `GetFusionCompByIndex()` hand you a FusionComp object (pyi).
     - Fusion inputs can be keyframed from script by attaching a `BezierSpline` and setting `input[frame] = value`. davinci-resolve-mcp v2.32.1 reports this tested live on Resolve Studio 21.0.0 ("Transform Size keyframed at 1.0@f0 and 1.4@f75 interpolated to 1.197@f37"). https://github.com/samuelgursky/davinci-resolve-mcp/releases/tag/v2.32.1
     - Or write the `.comp`/`.setting` text yourself. The keyframe syntax, from Blackmagic's bundled `Templates.drfx` > `Fusion/Particles/Matrix.setting`, is `BezierSpline { KeyFrames = { [0] = { 5, RH = {133.33, 3.33}, Flags = { Linear = true } }, [400] = { 0, LH = {...} } } }`. Easing comes from the LH/RH handle positions: flat handles give ease in/out.
  2. **A .drx still holding a keyframed PiP node on the Color page.** Apply it with `Graph.ApplyGradeFromDRX(path, gradeMode=2)`, where 2 means "Start Frames aligned" (pyi). Only works if each move has a fixed shape and timing relative to the clip start, so split the webcam clip at each layout change.
  3. **Hard-cut layouts with no animation.** Blade the webcam clip at each layout boundary and give each segment static `SetProperties` values.

---

## B. WHEN to move or resize the facecam

The evidence is thin. I found no public interview with a named creator's editor (Ali Abdaal, MKBHD, Thomas Frank, Theo, Primeagen) that gives facecam-move rules, and reddit.com is blocked for the research tools, so no r/davinciresolve, r/VideoEditing or r/NewTubers threads were read. The guidance below therefore comes from tool behaviour, tool docs and attention research.

**What the tools do**
- **Screen Studio**
  - Layouts sit on a timeline track: Fullscreen (the default for a new layout), Default (camera plus screen) and hidden. https://screen.studio/guide/dynamic-camera-layouts-
  - It "shrinks the camera frame during zooms... to avoid covering the content of your recording" (configurable). https://screen.studio/guide/camera
  - Auto zooms fire on clicks. https://screen.studio/guide/auto-zoom
- **Descript**
  - Layouts apply per scene. Scenes are created by typing "/" in the script, so layout changes are tied to transcript positions. https://help.descript.com/getting-started/scenes.md
  - **Smart Transitions** "rearranging, zooming, and fading visual elements", on by default. https://help.descript.com/effects-animations-transitions/smart-transitions
  - Automatic Multicam cutaways: "Frequent" adds "a cutaway every 10 seconds"; "Occasional" adds one "every 30 seconds during longer monologues". https://help.descript.com/visuals/automatic-multicam.md
  - Users asked for a minimum cut length because of "far too many cuts". https://feedback.descript.com/feature-requests/p/automatic-multicam-force-minimum-scene-cut-length
- **Tella**
  - Layout sections "snap to word boundaries".
  - Use **Smooth** for camera+screen → screen-only, and **Hard cut** "between very different sections".
  - Use Side-by-Side when both matter equally, and screen-dominant when screen detail matters.
  - "Stay with one layout when content is consistent."
  - https://www.tella.com/help/editing/use-layouts.md
- **Riverside**
  - Smart Layouts pick the main speaker "based on speech and head nods". https://support.riverside.com/hc/en-us/articles/5500983027101
  - Riverside's own editing lesson says Smart Layouts create more scene changes than needed, so place them by hand. Let the person "speak a sentence or two first, then cut at a natural pause".
  - Change scenes sparingly: about 100 scenes per hour at most, one every ~36 s. Frequent changes "draw attention to the edit".
  - https://riverside.com/university-videos/cut-scenes-for-smoother-camera-switches
- **OBS Move (Exeldro)**
  - Morphs sources with matching names between scenes, with ease in/out functions.
  - The "Aspect" scale type means "Always scale the sources, but keep aspect ratio".
  - https://obsproject.com/forum/resources/move.913/
- **Wistia** (Chris Lavigne and Austin Canary, 2024): open on webcam, split for the presentation, "go full screen on a slide when you want to emphasize the content", then back to the webcam for commentary. https://wistia.com/blog/presentation-videos
- **Clueso PiP guide**
  - Show the PiP for the intro/hook, transitions between steps, "emphasis or reactions", and CTAs.
  - Hide it for "dense UI walkthroughs, fine cursor work".
  - Move it whenever it would block content.
  - https://www.clueso.io/cluebooks/making-tasteful-screen-recording-videos--using-pictureinpicture-pip
- **OverseerOS** (Zaid Alkuheli, Oct 2026)
  - Show the face while explaining, then switch to full-screen interface for the steps.
  - Don't cut away during an action the viewer must follow.
  - Prefer hard cuts to decorative transitions.
  - Treat zoom as a signal: "constant zooming makes everything seem equally important".
  - https://www.overseeros.com/blog/how-to-edit-screen-recordings-for-youtube

**Attention research behind these rules**
- Motion onset captures attention. A previously static object that starts to move grabs attention even when the motion is uninformative (Abrams & Christ 2003, *Psychological Science*). So moving the PiP while viewers read code or text pulls their eyes off it. https://pubmed.ncbi.nlm.nih.gov/12930472/
- With a lower-right instructor PiP, learners spent "about 41% of time looking at the face" and switched between face and slide every 3.7 s (Kizilcec, Papadopoulos and Sritanyaratana, CHI 2014). The face is a strong attractor, so grow it only when the face is the content. https://rene.kizilcec.com/wp-content/uploads/2014/01/final_version2.pdf
- Mayer's image principle: adding the speaker's image doesn't reliably help learning, so use the face for motivation and emphasis, not by default. https://communities.springernature.com/posts/face-or-no-face-the-image-principle
- In a field study (Kizilcec, Bailenson and Gomez 2015), 35% chose to watch without the face. https://vhil.stanford.edu/publications/learning/instructors-face-video-instruction-evidence-two-large-scale-field-studies
- Showing the instructor's face "had no significant effect on learning" (Schneider and Sung 2024). https://learning-analytics.info/index.php/JLA/article/view/8235
- Eye-trace (Walter Murch's Rule of Six): put the next point of interest where the eye already is. In fast-paced video it may be "the single most important factor" (Piotr Toczyński, No Film School, 2018). https://nofilmschool.com/2018/08/editing-eye-trace-mind-rule-six-incorrect

**Rules of thumb (synthesis)**
1. **Change layout only on a sentence or clause boundary**, in the breath between sentences (Tella snaps to words; Riverside cuts at natural pauses). Let the move finish as the new sentence starts, or cut exactly on the boundary.
2. **Every change needs a motivation:**
   - face full or big for the hook, a personal opinion or story, "here's why", a reaction to a result, and the CTA/outro;
   - small bubble or hidden while the viewer must read or watch the screen;
   - side card (split) when both the speaker and an output matter;
   - move the bubble when content appears under it.
3. **Hold each layout long enough.** The tools suggest roughly 10 s at the busiest (Descript "Frequent") to about 30–40 s on average (Descript "Occasional", Riverside's ~100/hour). Avoid ping-pong, meaning a move and its reverse within a few seconds.
4. **Never animate while the viewer is reading code, chat output or terminal text, or while the cursor is acting** (motion onset; OverseerOS).
5. **Cut or animate?**
   - Animate a continuous change (bubble grows into full face; card slides aside to make room).
   - Hard-cut between unrelated sections or very different layouts (Tella).
   - A cut also hides a jump cut in the camera, the classic punch-in trick: "a slight digital zoom can disguise cuts". https://nofilmschool.com/easy-ways-to-hide-jump-cuts-your-next-video
6. **Duration:** about 0.35–0.6 s (21–36 frames at 60 fps) for big morphs, about 0.25–0.4 s (15–24 frames) for small hops; exits slightly faster than entries. Use ease-in-out or ease-out. Never linear (NN/g ; Mux).
7. **What looks amateur:** linear moves; moves in the middle of a word; squashed faces; corners that change radius or turn oval; mismatched shadows or borders between layouts; a bubble that covers the thing being clicked; constant movement with no motivation; a bubble that jitters on slow moves (render cache, resize filter). (Synthesis of the sources above.)

---

## C. WHERE to place the PiP

**Defaults and the evidence**
- **Camtasia:** the webcam overlay defaults to the lower-right corner. https://nus.atlassian.net/wiki/spaces/CTS/pages/36382403/Camtasia+Recorder+FAQs
- **Loom:** the camera bubble starts bottom-left and "snaps" to corners and sides. https://www.tella.com/definition/camera-frames ; https://support.atlassian.com/loom/docs/make-your-camera-bubble-visible-in-loom-recordings/
- **Tella:** 3×3 position grid; sizes S, M, L.
- **Clueso:** default to bottom-right and move it if it blocks content.
- **Research layouts:**
  - Kizilcec 2014 used lower-right.
  - A 2022 MDPI study placed the instructor in the upper-right at 260×260 px. https://pmc.ncbi.nlm.nih.gov/articles/PMC9313280/
  - Zhang, Xu, Pi and Yang (2022) compared left, middle and right: "Learning performance and satisfaction were highest when the instructor appeared on the right side of the screen". A middle position drew the most attention away from content. https://ideas.repec.org/a/taf/tbitxx/v41y2022i9p1988-1997.html
  - No study I found compares top-right with bottom-right.
- **Reading patterns:** NN/g's F-pattern (left edge and top lines get the most attention; mirrored in right-to-left languages). By that logic the right side, and especially the right-hand area below the top lines, gets the least reading attention. https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content/ ; https://www.nngroup.com/articles/text-scanning-patterns-eyetracking/
  - **(inference)** This supports "right side" over "left side". It doesn't decide top versus bottom.

**What the YouTube player and screen UIs cover**
- **Branding watermark:** "a channel-level image overlay in the bottom-right corner" (vidIQ, Sep 2026). It shows in landscape on desktop and mobile, for the end, a custom start, or the entire video (YouTube Help). https://vidiq.com/blog/post/youtube-video-watermark/ ; https://support.google.com/youtube/answer/2897336
- **Info-card teaser:** appears in the "upper-right corner" when a card fires. https://vidiq.com/blog/post/youtube-info-cards/ ; https://support.google.com/youtube/answer/6140493
- **End screens:** use the last 5–20 s with up to four elements; card teasers and watermarks are suppressed during them. Keep the face clear of where you'll put end-screen elements. https://support.google.com/youtube/answer/6388789
- **Captions and controls:** captions sit at the bottom centre and get pushed up when the control bar appears on hover or pause (browser caption-rendering discussion: https://lists.w3.org/Archives/Public/public-texttracks/2022Mar/0000.html). The progress bar and controls cover the bottom strip on hover or pause (observable).
  - **(inference)** The bottom edge is the most crowded part of a YouTube frame.
- **Desktop UIs:**
  - VS Code: the minimap is on the right of each editor and the Panel/terminal sits "below the editor region". https://code.visualstudio.com/docs/getstarted/userinterface
  - Windows 11 notification banners appear bottom-right; macOS notifications appear top-right. https://www.elevenforum.com/t/change-windows-11-notification-panel-position.5821/ ; https://developer.apple.com/forums/thread/722992
  - **(inference)** In terminal and chat AI tools (Claude Code, chat apps), the newest output and the prompt box are at the bottom. A bottom PiP covers exactly what's being typed and read. The top-right usually holds window chrome or toolbar icons.
- **Shorts and vertical:**
  - Third-party safe-zone guides say about 300 px at the bottom and about 96–192 px on the right are covered by UI at 1080×1920. https://adaptlypost.com/blog/social-media-safe-zones-2026-complete-guide
  - A centre 9:16 crop of 16:9 keeps only the middle ~32% of the width, so any corner PiP is lost anyway **(inference)**. Shorts need their own layout (face top or bottom half).

**Gaze, size, margins, shape, border, shadow**
- **Gaze, lead room:** viewers expect space "in front, and in the direction of" a subject. https://en.wikipedia.org/wiki/Lead_room
  - Clueso: "eyes in the upper third... looking toward the interface".
  - **(inference)** Put the PiP on the side your off-camera glances point away from, so you look into the frame toward the content.
- **Size:**
  - Clueso: 18–28% of frame width.
  - Dubb: "Smaller than feels right is usually correct". Test: if someone paused at a random second, could they still read what's behind? https://dubb.com/blog/webcam-bubble-screen-recording
  - Screencastify: bigger when the focus is you, smaller when the screen matters (via search summary).
  - The current pipeline's 704 px-wide card at 4K is 18.3% of the width, inside Clueso's range.
- **Shape:**
  - Circle (Loom default) versus rounded rectangle. Clueso: rounded rectangle or circle, matching the brand radius (12–16 px at 1080p, so 24–32 px at 4K). Dubb: match the shape to the page.
  - **(inference)** A rounded rectangle morphs cleanly into a 16:9 full frame and keeps hand gestures. A circle suits only tiny bubbles.
- **Border and shadow:** Clueso suggests a 2–4 px border (1080p) or a soft shadow. The PiP effect offers both natively.
- **Margins:** no source gives a number. **(inference)** Use equal margins on both edges, about 1.5–2.5% of the width (roughly 56–96 px at 4K), aligned with the graphics grid.
- **Disagreements:**
  - bottom-right is the generic default (Camtasia, Clueso, academic studies);
  - Loom and Tella use bottom-left;
  - Dubb argues "The corner is a default, not a decision" and puts the bubble beside the subject;
  - Webex puts the active-speaker thumbnail top-right (https://help.webex.com/en-us/nrsx5hy/Video-Centric-Recordings-in-Cisco-Webex-Site-Administration);
  - academics find position matters less than not putting it in the middle.

---

## D. What a pro editor would insist on

1. **One motion language.** Use the same curve, duration family, corner radius, border and shadow for every layout change across the whole video (Descript layout packs and Smart Transitions embody this: https://descript.com/blog/article/make-video-that-looks-great-by-default).
2. **Grow from the corner the card is pinned to**, never from the centre. Keyframe Position with Width/Height using identical easing, because the PiP effect resizes from its centre (forum, kaiyo90).
3. **Never squash the face.** Lock the zoom gang, scale the content uniformly, and keep the eye line in the upper third with consistent headroom at every size (Manual 21.1 p.919 ; Clueso).
4. **Keep a constant-looking corner radius as the size changes.** Keyframe Rounding if needed. A circle should only appear at the smallest size.
5. **Motion blur on fast moves**, via Fusion Transform/Merge or the ResolveFX Transform slider. Keep it subtle: Fusion's default 100° shutter is a good start (Manual 21.1).
6. **Resolution and frame rate.**
   - If the face goes full screen on a 4K timeline, the webcam must be 4K, or Super Scale or Sharper must be used. A 1080p face blown up to 3840 px looks soft (Larry Jordan recommends source images "2-3X the frame size" for zooms).
   - Record the webcam at 60 fps.
7. **Render cache before judging smoothness** (Larry Jordan), then step through every move frame by frame for edge aliasing, oval corners, popping shadows and the S-curve path bug.
8. **Audio continuity.** A layout change must not change the audio. Use J/L cuts when the move covers a jump cut.
9. **Leave clear areas.** Keep the face out of the bottom strip on YouTube (captions, controls, watermark) and away from where end-screen elements go. Never cover the active cursor, the prompt box or freshly printed output.
10. **Colour-match the webcam to the screen grade and keep it constant across layouts.** The Video Collage and PiP fill and border colours should come from the brand palette.
11. **Restraint.** Go a few seconds without a move rather than add an unmotivated one (Riverside: changes "draw attention to the edit"; OverseerOS on overuse).

---

## Recommendations for our edit

1. **Build all layout morphs with ResolveFX Picture in Picture (Resolve 21) on the webcam track**, with the clip's Inspector Transform left at default.
   - Animate Position X/Y + Width/Height for the box and Content Zoom/Pan/Tilt for framing, all keyed on the same frames with Ease In and Out (or bezier) applied to all keys together in the 21 Keyframe Editor.
   - Keyframe Rounding (bubble about 0.15–0.25; full screen 0) and keep Border and Drop Shadow identical in every state.
2. **Where motion blur is needed (the big bubble ↔ full-screen moves), or when the move must be generated by script**, use a Fusion comp:
   - MediaIn → Transform (content) → Rectangle mask with Corner Radius → Shadow → Transform (layout move, Motion Blur on, Quality 4–6, Shutter about 100–180) → MediaOut.
   - Generate it from our pipeline via `TimelineItem.ImportFusionComp()` with BezierSpline keyframes and flat handles for ease.
   - Don't try to script Inspector Transform/Crop or PiP-effect keyframes: the 21.1 API can't set them.
3. **Timing:**
   - Change layout only at sentence boundaries, landing in the pause.
   - Big morph 0.4–0.5 s (24–30 f at 60 fps); corner hop or small resize 0.3 s (18 f); exits about 20% faster than entries.
   - Hold every layout at least 8–10 s; aim for about one change every 20–40 s of body content; no ping-pong.
4. **Motivation map:**
   - full-screen face for the hook, opinions or stories, and the CTA/outro;
   - large side card (face about 35–45% of the width, screen squeezed into the rest) when reacting to an AI result;
   - small card while the viewer reads or watches the screen;
   - hide the card for dense UI walkthroughs;
   - move the card (hop corners) when content appears under it.
   - Use hard cuts for section changes and to hide camera jump cuts; animate only continuous changes.
5. **Placement:**
   - Keep **top-right as the house default** for terminal, chat and agent UIs. The bottom strip on YouTube is crowded and AI-tool prompt and output live at the bottom.
   - Switch to bottom-left only for beats where the top-right holds the content (as the existing `fvp` beats already do), checked per beat against what's under the card.
   - Never centre the card.
6. **Size and style at 4K:**
   - Small card about 18–20% of the width (current 704×948 portrait card fits).
   - Equal margins of about 56–96 px if the inpainted OBS PiP allows; the current 18–28 px margins are tighter than typical.
   - Rounded-rectangle radius about 32–48 px, border 0–6 px (or none), soft shadow (low opacity, large blur, small offset).
   - Avoid a circle except for a tiny bubble.
7. **QC each move:** render cache, check frame by frame, check at phone size, confirm the webcam is 4K60 (or Super Scale) before any full-screen face beat, and confirm audio is untouched across the change.

## Ten best sources
1. Resolve 21 New Features Guide (PiP, keyframe eases, Macro Editor): https://documents.blackmagicdesign.com/SupportNotes/DaVinci_Resolve_21_New_Features_Guide.pdf
2. Resolve 21.1 Reference Manual, local `C:\Program Files\Blackmagic Design\DaVinci Resolve\Documents\DaVinci Resolve.pdf` (Ch.44 Inspector, Ch.54 Paste Attributes, Ch.60 Keyframing, Ch.168 ResolveFX Transform: PiP, Transform, Video Collage; Fusion Motion Blur)
3. Resolve Scripting README / pyi / CHANGELOG 21.1, local `C:\ProgramData\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\`; with the Fusion Templates README `...\Developer\Fusion Templates\README.txt`
4. Blackmagic forum, "Scripting API Wishlist" (OFX and keyframes not scriptable, 21.1 status): https://forum.blackmagicdesign.com/viewtopic.php?f=44&t=235665
5. Blackmagic forum, "Inconsistent Zoom and Position speed when eased" (Edit-page S-curve bug): https://forum.blackmagicdesign.com/viewtopic.php?p=1141853
6. Kizilcec, Papadopoulos and Sritanyaratana, CHI 2014 (41% face dwell, 3.7 s switching, lower-right PiP): https://rene.kizilcec.com/wp-content/uploads/2014/01/final_version2.pdf
7. NN/g, Page Laubheimer, "Executing UX Animations: Duration and Motion Characteristics": https://www.nngroup.com/articles/animation-duration/
8. Tella layouts doc (word-boundary sections, smooth vs hard cut): https://www.tella.com/help/editing/use-layouts.md
9. Screen Studio camera guide (camera shrinks during zooms to avoid covering content): https://screen.studio/guide/camera
10. Riverside, "Cut scenes for smoother camera switches" (sparing changes, cut at pauses): https://riverside.com/university-videos/cut-scenes-for-smoother-camera-switches
