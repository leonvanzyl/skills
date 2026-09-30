"""Generate one HyperFrames composition per 'gfx' beat from a compact Python config (16:9, 1920x1080 layout px).
Each page = the shared engine.js + a CFG object. Times are beat-relative seconds; W(...) looks up a word's start.
Per-project configs live in scripts/gfx_<name>.py (see SKILL/examples/gfx_example.py) and call page()."""
import json, os, re
os.chdir(os.path.dirname(os.path.abspath(__file__)) + '/..')
P = json.load(open('program.json', encoding='utf-8'))
PL = json.load(open('edit_plan.json', encoding='utf-8'))
D = json.load(open('gfx/asset_dims.json')) if os.path.exists('gfx/asset_dims.json') else {}
OUT = 'gfx'
SFX = {}  # beat id -> list of events (beat-relative)

# capture frames (layout px, screen rect when the camera rests at the anchor): x, y, w, h
CAPTURE = {'fv': (160, 72, 1600, 936), 'fvp': (64, 72, 1440, 936), 'split': (64, 90, 1112, 900)}


def beat(bid):
    return next(b for b in PL['beats'] if b['id'] == bid)


def words(bid):
    """(beat, words) with word times relative to the beat start"""
    b = beat(bid); b = dict(b, dur=round(b['t1'] - b['t0'], 4))
    return b, [dict(w=w['w'], t=round(w['s'] - b['t0'], 3)) for w in P['words']
               if not w.get('tag') and b['t0'] - 0.06 <= w['s'] < b['t1'] - 0.03]


def W(ws, text, n=1):
    k = 0
    for w in ws:
        if re.sub(r'[^a-z0-9$.]', '', w['w'].lower()).rstrip('.') == text.lower():
            k += 1
            if k == n: return w['t']
    raise KeyError(text)


CSS = """
@font-face{font-family:Poppins;src:url(assets/Poppins-Regular.ttf);font-weight:400}
@font-face{font-family:Poppins;src:url(assets/Poppins-Medium.ttf);font-weight:500}
@font-face{font-family:Poppins;src:url(assets/Poppins-SemiBold.ttf);font-weight:600}
@font-face{font-family:Poppins;src:url(assets/Poppins-Bold.ttf);font-weight:700}
@font-face{font-family:Instrument Serif;src:url(assets/InstrumentSerif-Italic.ttf);font-style:italic}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1920px;height:1080px;overflow:hidden;background:#F3F3F0}
#root{position:relative;width:1920px;height:1080px;overflow:hidden;font-family:Poppins,sans-serif;color:#111}
#ground{position:absolute;inset:0;background:radial-gradient(ellipse 90% 120% at 50% 36%,#FFFFFF 0%,#FAFAF8 45%,#F3F3F0 100%)}
#viewport{position:absolute;inset:0;z-index:2}
#world{position:absolute;left:0;top:0;width:10px;height:10px;transform-origin:0 0}
.card{position:absolute;transform-origin:50% 50%}
.card img{display:block}
.inner{position:absolute;inset:0}
.bd{position:absolute;left:0;top:0;transform-origin:0 0;z-index:0}
#bd-wash{position:absolute;inset:0;background:#fff;opacity:0;z-index:1}
video.fg{position:absolute;left:0;top:0;transform-origin:0 0;z-index:3}
.caret{display:inline-block;width:4px;height:1.05em;background:#D97757;vertical-align:-0.15em;margin-left:3px;border-radius:2px}
.h1{font:700 88px/1.05 Poppins;letter-spacing:-0.02em}
.h2{font:700 52px/1.15 Poppins;letter-spacing:-0.01em}
.body{font:400 30px/1.45 Poppins}
.serif{font:italic 400 64px/1.1 'Instrument Serif'}
.mono{font:500 32px/1.5 'Cascadia Mono','Consolas',monospace}
"""

# world fades out before the camera card (split) - content lives in x 64-1176
SPLIT_MASK = ('#viewport{-webkit-mask-image:linear-gradient(to right,#000 0,#000 1180px,transparent 1300px);'
              'mask-image:linear-gradient(to right,#000 0,#000 1180px,transparent 1300px)}')


def page(bid, cfg, extra_html='', extra_css='', videos=(), backdrop=None, extra_js=''):
    """write gfx/<bid>.html. cfg: id, dur, mode ('fv'|'fvp'|'split'), cam0, cards, moves, heroes, reveals, typings, sfx"""
    dur = cfg['dur']
    mask = SPLIT_MASK if cfg['mode'] == 'split' else ''
    vid_html = ''
    filters = ['<filter id="mb-world" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="mbg-world" stdDeviation="0 0"/></filter>']
    for c in cfg['cards']:
        if c.get('inner') is not None or c.get('video'):
            filters.append(f'<filter id="mb-{c["id"]}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="mbg-{c["id"]}" stdDeviation="0 0"/></filter>')
    for i, (cid, src, fw, fh) in enumerate(videos):
        vid_html += f'<video id="v-{cid}" data-card="{cid}" class="clip fg" src="{src}" data-start="0" data-duration="{dur}" data-track-index="{2 + i}" muted playsinline style="width:{fw}px;height:{fh}px"></video>\n'
    bd_html = ''
    if backdrop:
        kind, src, fw, fh = backdrop
        if kind == 'video':
            bd_html = f'<video id="v-bd" data-backdrop="1" class="clip bd" src="{src}" data-start="0" data-duration="{dur}" data-track-index="1" muted playsinline style="width:{fw}px;height:{fh}px;opacity:0"></video>'
        else:
            bd_html = f'<img id="bd-img" class="bd" src="{src}" style="width:{fw}px;height:{fh}px;opacity:0">'
        bd_html += '<div id="bd-wash"></div>'
    html = f"""<!doctype html>
<html lang="en" data-resolution="landscape"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1920, height=1080"/>
<script src="gsap.min.js"></script>
<style>{CSS}{mask}{extra_css}</style></head>
<body>
<div id="root" data-composition-id="{bid}" data-start="0" data-duration="{dur}" data-width="1920" data-height="1080">
<div id="ground"></div>
{bd_html}
<div id="viewport"><div id="world"></div></div>
{vid_html}
{extra_html}
<svg width="0" height="0" style="position:absolute">{''.join(filters)}</svg>
</div>
<script>window.CFG={json.dumps(cfg)};</script>
<script>{extra_js}</script>
<script src="engine.js"></script>
</body></html>"""
    open(f'{OUT}/{bid}.html', 'w', encoding='utf8').write(html)
    SFX[bid] = cfg.get('sfx', [])


def capture_card(cid, fw, fh, mode='fv', inner0=None, inner=(), backdrop=True, land=None, **kw):
    """the fixed capture frame for a real page / real UI (radius 32, white, shadowed) on its washed, blurred clone.
    The frame never moves; the footage pans and zooms inside it with `inner` keyframes."""
    x, y, w, h = CAPTURE[mode]
    c = dict(id=cid, kind='capture', x=x + w / 2, y=y + h / 2, w=w, h=h, radius=32, fw=fw, fh=fh, inner=list(inner),
             backdrop={'tIn': -1} if backdrop is True else backdrop, bg='#fff', **kw)
    if inner0: c['inner0'] = inner0
    if land: c['land'] = land
    return c


def logo_html(src):
    return f'<img src="{src}" style="width:100%;height:100%;object-fit:contain;display:block">'
