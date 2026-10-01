# Graphics: the HyperFrames world engine (16:9)

Every `gfx` beat is one standalone HyperFrames composition, `gfx/<id>.html`, generated from a compact Python config
by `scripts/build_gfx.py`, which imports `scripts/gfx_<name>.py` modules from the work dir. Each page holds the shared
`gfx/engine.js` (the shorts engine generalised to 16:9: world camera, depth of field, motion blur, captures) and one
`window.CFG`. The worked example is `SKILL/examples/gfx_example.py` (two beats from a real edit). Copy its patterns.

Contents: [Helpers](#build-helpers) · [CFG](#cfg) · [Cards](#cards) · [Camera](#camera-moves) · [Depth of field](#depth-of-field) · [Captures](#real-captures) · [Splits](#split-beats) · [SFX](#sfx-events) · [Render and check](#render-and-check)

## Build helpers (`scripts/build_gfx_common.py`)
- **`words(bid)`** returns `(beat, words)`: the beat with its `dur`, and its words with times relative to the beat
  start, from `program.json`.
- **`W(words, 'text', n=1)`**: the start of the n-th occurrence of a word (punctuation stripped). Use it for every
  cue, e.g. a step starts at `W(ws, 'opus') - 0.25`.
- **`page(bid, cfg, extra_html='', extra_css='', videos=(), backdrop=None, extra_js='')`** writes the composition.
  - `videos=[(card_id, 'assets/clip.mp4', fw, fh)]` gives a card live footage (made with `assets.py clip`). Videos
    must be root children in HyperFrames; the engine positions and clips them to the card every frame.
  - `backdrop=('img'|'video', src, fw, fh)` adds the washed, blurred clone behind a capture.
- **`capture_card(id, fw, fh, mode='fv'|'fvp'|'split', inner0=..., inner=[...], img=...)`**: the fixed capture frame
  for the layout (spec section 4) when the camera rests at the anchor.
- **`logo_html(src)`**: an `<img>` for an official logo copied into `gfx/assets/`.
- **`D`**: `gfx/asset_dims.json`, the pixel size of every asset `assets.py` made.

Assets come from two places:
- **The recording** (the real UI and numbers the speaker shows): `python scripts/assets.py still <t> x,y,w,h name.png`
  for a programme-time still, `still src:<file>@<seconds> ...` for any source moment (e.g. the result shown later in
  the video), `clip <bid> x,y,w,h name.mp4` for footage synced to the beat. Crops avoid the PiP window.
- **The research subagent** (pages, logos, pricing tables, docs): 2x PNG captures in `captures/`, copied into
  `gfx/assets/` and added to `asset_dims.json` with `assets.save_dims`.

## CFG
```python
cfg = dict(
  id='g01', dur=b['dur'],                # duration = the beat exactly
  mode='fv' | 'fvp' | 'split',           # anchors: fv (960,540), fvp (784,540), split (620,540); split masks the world right of x 1180
  anchor=[x, y],                         # optional override: where the camera point lands on screen
  cam0=dict(x=784, y=540, s=1),          # frame-0 camera = the landing state (sharp, at rest)
  cards=[...], moves=[...], heroes=[...],
  pushRef=1.0,                           # camera scale that counts as "not pushed"
  reveals=[dict(el='hlA', t=2.1, dur=0.5, type='scaleX'|'fade'|'pop'|'fadeout')],
  typings=[dict(el='cmd', t0=0.3, cps=14, text='claude update', caret=True)],
  sfx=[dict(t=1.35, type='whoosh'|'click'|'pop'|'chime'|'key')],     # beat-relative; audio.py places them
)
```
`extra_js` may define `window.CFG_RENDER = function(t, cam){...}`, called every frame after the engine renders, for
custom time-driven UI (a moving menu highlight, a counter). Keep it a pure function of `t`.

## Cards
```python
dict(id='bench', kind='media'|'doc'|'tile'|'phone'|'capture'|'logo'|'plain',
     x=784, y=540, w=1000, h=420,           # world px, centre-based (world = screen at the rest camera)
     img='assets/x.png' | html='<div>...</div>',
     radius=None,                           # default per kind: media 3% of w, doc 40, tile 72, phone 84, capture 32
     bg='#fff', land=dict(t=0.3, dur=0.55), exit=dict(t=5, dur=0.35),
     fw=..., fh=..., inner0=dict(fx, fy, k), inner=[dict(t, dur, fx, fy, k, ease)],   # camera INSIDE the card
     overlay='<div ...>',                   # html in footage px that moves with the inner camera
     backdrop={'tIn': -1}, noDof=True, forceSharp=True)
```
- Every non-logo card gets the spec's three-layer shadow.
- A landing is power3.out: scale 0.92 -> 1, +70 px -> 0, fade in. Add a `pop` SFX at `land.t`. Nothing lands at
  frame 0 - frame 0 already shows the content, because the clip hard-cuts in over V1.
- **Highlight bands on screenshots:**
  - Light page in a card's `html`: put the band `div` under the `<img>` and give the image `mix-blend-mode:multiply`.
  - Light page in a capture (`img` + `inner` camera): put the band in the card's `overlay` (footage px, it moves
    with the inner camera) and set `overlayBlend='multiply'` on the card - a blend mode on the band itself does
    nothing, because the overlay layer is its own stacking context. Band colour `#F6D3C2`. See `r01` in the example.
  - Dark UI (most apps in dark mode): a translucent clay `div` (`rgba(217,119,87,.30)`, radius 8,
    `transform:scaleX(0)`) ABOVE the image, revealed with `scaleX`. See the `sess` card in the example.

## Camera moves
`moves` is a list of `dict(t, dur, kind, to=dict(x, y, s), ease=None)`; scale interpolates geometrically.

| kind | use | default ease | timing |
|---|---|---|---|
| `glide` | slow drift while holding | sine.inOut | scale change <= 0.04 |
| `step` | to the next item | power3.inOut | 0.5 s, 0.25 s before the word that names it |
| `push` | onto the card being talked about | power2.inOut | 1.2-2 s, up to ~1.6x |
| `pull` | back out to show the bigger picture | power2.inOut | 1-2 s |
| `whip` | `dict(t, kind='whip', to=..., via=...)` | power3.in / power3.out | 0.45 s out, 0.6 s in; one per graphic |

Add a `whoosh` SFX at the whip midpoint (`t + 0.45`). While a product window is the subject, keep the world camera
still and move only its `inner` camera (1.15-1.4x, 0.4-0.7 s, power2.inOut).

## Depth of field
`heroes=[dict(t, id)]` names the card being read from time `t`. As the camera pushes, other cards blur up to 14 px
and dim 30%; the previous hero goes to a 9 px blur at 40%; `id='none'` keeps everything sharp (a pull-back that
shows the whole set). Never blur a word the viewer needs to read.

## Motion blur
Built in: the viewport and each footage layer blur along their screen velocity every frame
(sigma = 0.29 x speed x 0.75/60, capped at 24 px). `render_gfx.sh full` renders at 4x the timeline rate and blends
3 of every 4 frames (tmix). A frame at rest is sharp; if it isn't, something is still moving.

## Real captures
Anything that happened is shown as the real page or the real UI:
- **Pages:** `npx --yes hyperframes capture <url> -o captures/<name> --skip-assets --skip-vision` (the research
  subagent) writes `screenshots/full-page.png` (1920 wide, the whole page) and `extracted/visible-text.txt` (for the
  fact check). Copy the full page into `gfx/assets/` and let the inner camera scroll to the passage; find its y by
  scaling the page down with a y ruler.
- **UI:** stills or synced clips of the recording (`assets.py`).
The capture frame never moves; the footage pans and zooms inside it with `inner` keyframes (`fx`, `fy` = footage px
at the frame centre; `k` = layout px per footage px). The engine clamps `inner` so the view never leaves the
footage. Dark UI is fine inside the white frame.

## Split beats
- Mode `split`: content in x 64-1176, y 90-990. The camera card and the head pop-out are added by `compose.py`
  from the same frames as V1 (the full-frame camera, or the PiP when the scene is a screen recording).
- Run `compose.py <id> --matte` once (background removal on a frame-exact camera clip), then `compose.py <id>`.
- Check one full-resolution frame: the whole face (hair to chin) inside the card, hair ~96 px above its edge,
  the head never torn from the body on fast moves.

## SFX events
Put `sfx` on each CFG, beat-relative. `build_gfx.py` writes `gfx/sfx_events.json` and `audio.py` places them:
whooshes only on whips, UI sounds only for visible presses, typing and landings, nothing on steps, pushes, glides.

## Render and check
```bash
$PY scripts/build_gfx.py <name>                      # gfx/<id>.html for every beat in scripts/gfx_<name>.py
bash scripts/render_gfx.sh draft g01 g02             # 10 fps drafts, all at once
$PY scripts/draftsheet.py g01 8                      # chk/g01_sheet.png - LOOK
bash scripts/render_gfx.sh full g01 g02              # 4x rate + motion blur, lossless PNG capture -> gfx/out/<id>.mp4 (UHD: device scale 2)
$PY scripts/compose.py g02 --matte                   # split beats: camera clip + GPU matte
$PY scripts/compose.py g01 g02 --jobs 3              # -> media/<id>.mp4 (PiP pasted for fvp, camera card for split), one process per beat
$PY scripts/compose.py g02 --preview 0.5             # one full-resolution frame, in seconds
$PY scripts/draftsheet.py g01 8 --full               # the finished clip
```
`render_gfx.sh full` renders each composition with its own Chrome per worker and throttles itself machine-wide
(`RENDER_SLOTS` x `HF_WORKERS`), so call it from as many subagents as you like, always through the script.
Look for: the frame-0 landing state; content inside its bounds and clear of the PiP corner; nothing important
blurred at rest; each cue on its word; text crisp in one full-resolution frame.
