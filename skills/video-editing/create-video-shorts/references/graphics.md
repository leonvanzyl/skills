# Graphics: the HyperFrames world engine

Every split or full-visual run is one standalone HyperFrames composition, `gfx/<sk>_r<i>.html`.

It is generated from a compact Python config by `scripts/build_gfx.py <sk>`, which imports `scripts/gfx_<sk>.py`. Each page contains the shared `gfx/engine.js`, which implements the spec's style, camera, depth of field and motion blur, plus one `window.CFG` object. The worked example for a whole short is `SKILL/examples/gfx_s1.py`. Copy its patterns.

Contents: [Build helpers](#build-helpers) · [CFG](#cfg) · [Cards](#cards) · [Camera moves](#camera-moves) · [Depth of field](#depth-of-field) · [Captures](#real-captures-full-visual) · [Split rules](#split-rules) · [SFX](#sfx-events) · [Check](#checking)

## Build helpers (`scripts/build_gfx_common.py`)
- **`words(sk, ri)`:** returns `(run, words)`. Word times are relative to the run start, taken from `cut.json`.
- **`W(words, 'text', n=1)`:** the start time of the n-th occurrence of a word, with punctuation stripped. Use it for every cue, e.g. a step starts at `W(ws, 'opus') - 0.25`.
- **`page(rid, cfg, extra_html='', extra_css='', videos=(), backdrop=None, extra_js='')`:** writes the composition.
  - `videos=[(card_id, 'assets/clip.mp4', fw, fh)]` gives a card live footage. Video must be a root child in HyperFrames; the engine positions it and clips it to the card every frame.
  - `backdrop=('img'|'video', src, fw, fh)` adds the washed clone behind a capture.
- **`capture_card(id, fw, fh, x=540, y=720, inner0=…, inner=[…], img=…)`:** the spec's fixed capture frame: x 24, y 200, 1032×1040, radius 36, when the world camera rests at (540, 720, s=1) in `fv` mode.
- **`LOGO_HTML`:** `<img src="assets/claude-logo.svg">`. Copy the product's official logo into `gfx/assets/` in `prep_assets.py`, and swap the file per product.
- **`D`:** asset dimensions, merged from `gfx/asset_dims.json` and every `gfx/asset_dims_<tag>.json`. Parallel graphics subagents each write their own file, so they never race. Modules are `scripts/gfx_<tag>.py`; `build_gfx.py <tag>` builds one, and with no tag it builds them all.

## CFG
```python
cfg = dict(
  id='s1_r3', dur=r['dur'],            # duration = the run exactly
  mode='fv' | 'split',                  # split: content in y 40-900, world fades out from 900 over 160 px (built in)
  anchor=[540, 720],                    # default: split [540,470], fv [540,720] - where the camera point lands on screen
  cam0=dict(x=540, y=720, s=1),         # frame-0 camera = the landing state (sharp, at rest)
  cards=[...], moves=[...], heroes=[...],
  pushRef=1.0,                          # camera scale that counts as "not pushed" (neighbour blur grows as s exceeds it)
  reveals=[dict(el='hlb2', t=2.1, dur=0.5, type='scaleX'|'fade'|'pop'|'fadeout')],
  typings=[dict(el='cmd', t0=0.3, cps=14, text='claude update', caret=True)],   # typed text with clay caret
  sfx=[dict(t=1.35, type='whoosh'|'click'|'pop'|'chime'|'key')],                 # run-relative; audio.py mixes them
)
```
`extra_js` can define `window.CFG_RENDER = function(t, cam){...}`. It is called every frame after the engine renders; use it for custom, time-driven UI such as the moving menu highlight in `gfx_s1.py`. Keep it a pure function of `t`.

## Cards
```python
dict(id='bench', kind='media'|'doc'|'tile'|'phone'|'capture'|'logo'|'plain',
     x=540, y=1300, w=1040, h=438,         # world px, centre-based
     img='assets/x.png' | html='<div>…</div>',
     radius=None,                          # default per kind: media 3% of w, doc 40, tile 72, phone 84, capture 36
     bg='#fff', land=dict(t=0.3, dur=0.55), exit=dict(t=5, dur=0.35),
     fw=..., fh=..., inner0=dict(fx, fy, k), inner=[dict(t, dur, fx, fy, k, ease)],  # footage camera INSIDE the card
     overlay='<div …>',                    # html in footage px: moves with the inner camera (e.g. a highlight on a UI row)
     backdrop={'tIn': -1},                 # washed clone behind this capture (tIn/tOut fade)
     noDof=True, forceSharp=True)
```
- **Shadows:** every non-logo card gets the spec's three-layer shadow automatically.
- **Landing:** a landing uses power3.out: scale 0.92 → 1, +70 px → 0, fade in. Add a `pop` SFX at `land.t`. Nothing lands at frame 0, and the HERO is already on screen at frame 0: the cut lands on it. Landing the hero at 0.05 s leaves empty frames after the cut. Only supporting cards (logo tiles, a message arriving) land later.
- **Highlight bands on screenshots:** blend modes are isolated per card. Put the band `div` under the screenshot inside the same card `html`, and give the `<img>` `mix-blend-mode:multiply`. See the `bench` card in `gfx_s1.py`.
- **Highlights on dark UI:** a multiply band vanishes on a dark app. Instead, pre-render the real text re-inked #111 on #FBEEE8 as an overlay revealed by a left-to-right wipe, or use a clay #D97757 outline with a dark clay fill, screen-blended, with a hole over bright elements.

## Camera moves
`moves` is a list of `dict(t, dur, kind, to=dict(x, y, s), ease=None)`. Geometric scale interpolation is built in.

| kind | use | default ease | spec timing |
|---|---|---|---|
| `glide` | slow drift while holding | sine.inOut | scale change ≤ 0.04 |
| `step` | to the next item | power3.inOut | 0.5 s, starting 0.25 s before the word that names it |
| `push` | onto the card being talked about | power2.inOut | 1.2–2 s, up to about 1.6× |
| `pull` | back out to reveal the bigger picture | power2.inOut | 1–2 s |
| `whip` | `dict(t, kind='whip', to=…, via=…)` | power3.in / power3.out | 0.45 s out, 0.6 s in, at most one per run and three per short |

Add a `whoosh` SFX at the whip midpoint, which is `t + 0.45`.

While a product window is the subject, keep the world camera still and move only its `inner` camera (1.15–1.4×, 0.4–0.7 s, power2.inOut).

## Depth of field
`heroes=[dict(t, id)]` names the card being read from each time `t`. The engine handles:
- **Push blur:** as the camera pushes, neighbours blur up to 14 px and dim 30%.
- **Old hero:** the previous hero goes to a 9 px blur at 40% opacity.
- **All sharp:** `id='none'` switches depth of field off, e.g. when a pull-back should show every card sharp.
- **Readability:** never blur a word the viewer needs to read.

## Motion blur
Built in: the viewport and each footage layer are blurred along their screen velocity every frame (σ = 0.29 × speed × 0.75/60, capped at 24 px). `render_full.sh` renders at 240 fps, then `tmix=frames=3,fps=60`. A frame at rest is sharp; if it isn't, something is still moving.

## Real captures (full visual)
Anything that happened (a release, a number, pricing, benchmarks, your own usage stats) is shown as the real page or the real UI:
- **Pages:** 2x screenshots by the research subagent.
- **Your UI:** stills or synced clips of your screen recording, cut by `prep_assets.py`.

The frame never moves; the footage pans and zooms inside it with `inner` keyframes (`fx`, `fy` = footage px at the frame centre; `k` = CSS px per footage px). The engine clamps `inner` so the view never leaves the footage. Crops must avoid the webcam window. Dark UI is fine inside the white frame.

## Split rules
- **Frame 0 of run 0** (the hook) is also the cover frame: keep all content below y 620. For example, put the product logo at y ≈ 700–820, then step to the hero card with the card landing so its bottom edge sits at y 880–900.
- **Content** stays in y 40–900.
- **Captions** sit at y 941–1114, and the camera card with the head pop-out starts at 1200. `compose.py` draws both; the graphic stays clear of them.

## SFX events
Put `sfx` on each CFG, run-relative. `audio.py` reads `gfx/sfx_events.json`, which `build_gfx.py` writes, and places each one:
- **Whooshes:** only on whips.
- **UI sounds:** only for visible real presses, typing and landings.
- **Camera moves:** nothing on steps, pushes, glides or layout cuts.

## Checking
Before any full render, check each composition:
- a 10 fps draft
- a contact sheet (`scripts/draftsheet.py <rid> 8`)
- one full-resolution frame of anything with text

Look for:
- the frame-0 landing state (the hero already on screen)
- any text the viewer must read at 30 px or more (captured UI included)
- content inside its bounds
- nothing important blurred at rest
- the bottom edge in 880–900 (split) or 1200–1240 (full visual)
- each cue landing on its word
