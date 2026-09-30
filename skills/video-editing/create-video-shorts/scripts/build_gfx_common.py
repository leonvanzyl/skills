"""Generate one HyperFrames composition per graphic run (split / full-visual) from compact configs.
Each page = shared engine.js + a CFG object. Times are run-relative seconds; W(...) looks up a word start."""
import json, os, re
import os as _os
_os.chdir(_os.path.dirname(_os.path.abspath(__file__))+'/..')
C = json.load(open('cut.json'))
D = json.load(open('gfx/asset_dims.json'))
OUT = 'gfx'
SFX = {}  # run id -> list of events (run-relative)

def words(sk, ri):
    r = C[sk]['runs'][ri]
    return r, [dict(w=w['w'], t=round(w['s'] - r['T0'], 3)) for w in C[sk]['words'] if r['T0'] - 0.06 <= w['s'] < r['T1'] - 0.03]

def W(ws, text, n=1):
    k = 0
    for w in ws:
        if re.sub(r'[^a-z0-9$.]', '', w['w'].lower()) == text.lower():
            k += 1
            if k == n: return w['t']
    raise KeyError(text)

CSS = """
@font-face{font-family:Poppins;src:url(assets/Poppins-Regular.ttf);font-weight:400}
@font-face{font-family:Poppins;src:url(assets/Poppins-Medium.ttf);font-weight:500}
@font-face{font-family:Poppins;src:url(assets/Poppins-SemiBold.ttf);font-weight:600}
@font-face{font-family:Poppins;src:url(assets/Poppins-Bold.ttf);font-weight:700}
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#F3F3F0}
#root{position:relative;width:1080px;height:1920px;overflow:hidden;font-family:Poppins,sans-serif;color:#111}
#ground{position:absolute;inset:0;background:radial-gradient(ellipse 120% 90% at 50% 36%,#FFFFFF 0%,#FAFAF8 45%,#F3F3F0 100%)}
#viewport{position:absolute;inset:0;z-index:2}
#world{position:absolute;left:0;top:0;width:10px;height:10px;transform-origin:0 0}
.card{position:absolute;transform-origin:50% 50%}
.card img{display:block}
.inner{position:absolute;inset:0}
.bd{position:absolute;left:0;top:0;transform-origin:0 0;z-index:0}
#bd-wash{position:absolute;inset:0;background:#fff;opacity:0;z-index:1}
video.fg{position:absolute;left:0;top:0;transform-origin:0 0;z-index:3}
.caret{display:inline-block;width:4px;height:1.05em;background:#D97757;vertical-align:-0.15em;margin-left:3px;border-radius:2px}
.h1{font:700 96px/1.05 Poppins;letter-spacing:-0.02em}
.h2{font:700 52px/1.15 Poppins;letter-spacing:-0.01em}
.body{font:400 30px/1.45 Poppins}
.mono{font:500 34px/1.5 'Cascadia Mono','Consolas',monospace}
"""

def page(rid, cfg, extra_html='', extra_css='', videos=(), backdrop=None, extra_js=''):
    dur = cfg['dur']
    split_mask = ''
    if cfg['mode'] == 'split':
        split_mask = '#viewport{-webkit-mask-image:linear-gradient(to bottom,#000 0,#000 900px,transparent 1060px);mask-image:linear-gradient(to bottom,#000 0,#000 900px,transparent 1060px)}'
    vid_html = ''
    filters = ['<filter id="mb-world" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="mbg-world" stdDeviation="0 0"/></filter>']
    for c in cfg['cards']:
        if c.get('inner') is not None or c.get('video'):
            filters.append(f'<filter id="mb-{c["id"]}" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur id="mbg-{c["id"]}" stdDeviation="0 0"/></filter>')
    for i, (cid, src, fw, fh) in enumerate(videos):
        vid_html += f'<video id="v-{cid}" data-card="{cid}" class="clip fg" src="{src}" data-start="0" data-duration="{dur}" data-track-index="{2+i}" muted playsinline style="width:{fw}px;height:{fh}px"></video>\n'
    bd_html = ''
    if backdrop:
        kind, src, fw, fh = backdrop
        if kind == 'video':
            bd_html = f'<video id="v-bd" data-backdrop="1" class="clip bd" src="{src}" data-start="0" data-duration="{dur}" data-track-index="1" muted playsinline style="width:{fw}px;height:{fh}px;opacity:0"></video>'
        else:
            bd_html = f'<img id="bd-img" class="bd" src="{src}" style="width:{fw}px;height:{fh}px;opacity:0">'
        bd_html += '<div id="bd-wash"></div>'
    html = f"""<!doctype html>
<html lang="en" data-resolution="portrait"><head><meta charset="UTF-8"/><meta name="viewport" content="width=1080, height=1920"/>
<script src="gsap.min.js"></script>
<style>{CSS}{split_mask}{extra_css}</style></head>
<body>
<div id="root" data-composition-id="{rid}" data-start="0" data-duration="{dur}" data-width="1080" data-height="1920">
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
    open(f'{OUT}/{rid}.html', 'w', encoding='utf8').write(html)
    SFX[rid] = cfg.get('sfx', [])

def capture_card(cid, fw, fh, x=540, y=720, inner0=None, inner=(), backdrop=True, land=None, **kw):
    c = dict(id=cid, kind='capture', x=x, y=y, w=1032, h=1040, fw=fw, fh=fh, inner=list(inner), backdrop={'tIn': -1} if backdrop is True else backdrop, bg='#fff', **kw)
    if inner0: c['inner0'] = inner0
    if land: c['land'] = land
    return c

LOGO_HTML = '<img src="assets/claude-logo.svg" style="width:100%;height:100%;display:block">'


