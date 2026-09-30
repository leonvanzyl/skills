# EXAMPLE from the first real pro edit ("Sonnet 5.5 vs Opus 5.5 vs Fable 5.1", 2026-09-30): the two graphics beats
# of its hook, plus a resource beat. Every time, crop and filename is specific to that video. Copy to W/scripts/gfx_<name>.py and rewrite.
# Assets were cut from the recording itself with:
#   python scripts/assets.py still src:7.mkv@473.27 0,110,3060,1720 game_fable.png     (the game Fable built)
#   python scripts/assets.py still 260.0 700,880,1120,200 session_fable.png            (its real usage panel)
from build_gfx_common import *

TILE = ('<div style="position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;padding:0 48px">'
        '<div style="font:500 30px/1.2 Poppins;color:#8A8A84">Anthropic</div>'
        '<div style="font:700 52px/1.15 Poppins;color:{c};margin-top:6px">{name}</div></div>')
PROMPT = ('<div style="position:absolute;inset:0;padding:40px 52px">'
          '<div style="font:600 30px/1.2 Poppins;color:#B25730;letter-spacing:.02em">PROMPT.txt</div>'
          '<div style="font:700 40px/1.25 Poppins;color:#111;margin-top:14px">Build a complete, polished 3D adventure mini golf game that runs in the browser.</div>'
          '<div style="font:400 30px/1.45 Poppins;color:#55554F;margin-top:18px">Static front end only: Vite + Three.js (JavaScript or TypeScript, your choice).<br>'
          'No external asset files. Create all models, textures and sounds in code.</div></div>')


def build():
    # g01 (fvp, keeps the webcam corner): the three models are on screen from frame 0; the camera steps to each as
    # it is named, pulls back, then the real prompt lands and the camera pushes onto it on "exact same prompt".
    b, ws = words('g01')
    ys = 430
    cards = [dict(id='son', kind='tile', x=334, y=ys, w=420, h=260, html=TILE.format(c='#B25730', name='Sonnet 5.5')),
             dict(id='opu', kind='tile', x=784, y=ys, w=420, h=260, html=TILE.format(c='#111', name='Opus 5.5')),
             dict(id='fab', kind='tile', x=1234, y=ys, w=420, h=260, html=TILE.format(c='#111', name='Fable 5.1')),
             dict(id='doc', kind='doc', x=784, y=850, w=1300, h=330, html=PROMPT, land=dict(t=W(ws, 'exact') - 0.15, dur=0.55))]
    t_s, t_o, t_f = W(ws, 'sonnet') - 0.25, W(ws, 'opus') - 0.25, W(ws, 'fable') - 0.25
    moves = [dict(t=t_s, dur=0.5, kind='step', to=dict(x=334, y=ys, s=1.12)),
             dict(t=t_o, dur=0.5, kind='step', to=dict(x=784, y=ys, s=1.12)),
             dict(t=t_f, dur=0.5, kind='step', to=dict(x=1234, y=ys, s=1.12)),
             dict(t=W(ws, 'giving') - 0.3, dur=1.0, kind='pull', to=dict(x=784, y=620, s=0.9)),
             dict(t=W(ws, 'same') - 0.25, dur=1.0, kind='push', to=dict(x=784, y=850, s=1.2))]
    cfg = dict(id='g01', dur=b['dur'], mode='fvp', cam0=dict(x=784, y=ys, s=1.0), cards=cards, moves=moves, pushRef=1.0,
               heroes=[dict(t=0, id='none'), dict(t=t_s + 0.1, id='son'), dict(t=t_o + 0.1, id='opu'), dict(t=t_f + 0.1, id='fab'),
                       dict(t=W(ws, 'giving') - 0.2, id='none'), dict(t=W(ws, 'same') - 0.2, id='doc')],
               sfx=[dict(t=round(W(ws, 'exact') - 0.15, 3), type='pop')])
    page('g01', cfg)

    # g02 (split, camera card on the right): the real game Fable built (quality), then the real usage panel -
    # a clay band on Active 1h 41m (speed), then on Cost $51.40 (cost).
    b, ws = words('g02')
    gw, gh = D['game_fable.png']; sw_, sh_ = D['session_fable.png']
    GW = 1000; GH = round(GW * gh / gw); SW = 1000; k = SW / sw_; SH = round(sh_ * k)
    gy, sy = 380, 802
    band = lambda i, x0, x1: (f'<div id="hl{i}" style="position:absolute;left:{x0 * k - 8:.0f}px;top:{80 * k - 6:.0f}px;'
                              f'width:{(x1 - x0) * k + 16:.0f}px;height:{45 * k + 12:.0f}px;border-radius:8px;background:rgba(217,119,87,.30);'
                              'transform-origin:0 50%;transform:scaleX(0)"></div>')
    sess = f'<img src="assets/session_fable.png" style="position:absolute;inset:0;width:100%;height:100%">' + band('A', 758, 1025) + band('C', 28, 252)
    cards = [dict(id='game', kind='media', x=620, y=gy, w=GW, h=GH, img='assets/game_fable.png'),
             dict(id='sess', kind='media', x=620, y=sy, w=SW, h=SH, html=sess, bg='#141414')]
    left = 620 - SW / 2; top = sy - SH / 2
    act = (left + (758 + 1025) / 2 * k, top + 102 * k); cost = (left + 140 * k, top + 102 * k)
    t_q, t_sp, t_c = W(ws, 'quality') - 0.25, W(ws, 'speed') - 0.25, W(ws, 'cost') - 0.25
    moves = [dict(t=t_q, dur=1.2, kind='push', to=dict(x=620, y=gy, s=1.18)),
             dict(t=t_sp, dur=0.5, kind='step', to=dict(x=act[0], y=act[1], s=1.6)),
             dict(t=t_c, dur=0.5, kind='step', to=dict(x=cost[0] + 120, y=cost[1], s=1.6))]
    cfg = dict(id='g02', dur=b['dur'], mode='split', cam0=dict(x=620, y=540, s=1.0), cards=cards, moves=moves, pushRef=1.0,
               heroes=[dict(t=0, id='none'), dict(t=t_q + 0.1, id='game'), dict(t=t_sp + 0.1, id='sess')],
               reveals=[dict(el='hlA', t=W(ws, 'speed'), dur=0.5, type='scaleX'), dict(el='hlC', t=W(ws, 'cost'), dur=0.5, type='scaleX')],
               sfx=[])
    page('g02', cfg)

    # r01 (fvp resource): a page the speaker cites, captured with
    #   npx --yes hyperframes capture https://www.anthropic.com/claude/sonnet -o captures/sonnet_page --skip-assets --skip-vision
    # (screenshots/full-page.png is 1920 wide; extracted/visible-text.txt feeds the fact check). The frame never
    # moves: the inner camera scrolls to the passage, and a light band sweeps across it. On a light page the band is
    # an overlay with overlayBlend='multiply' (a marker pen); on dark UI use a translucent clay wash instead.
    b, ws = words('r01')
    fw, fh = D['sonnet_page.png']
    band = ('<div id="hlP" style="position:absolute;left:630px;top:1572px;width:700px;height:46px;border-radius:6px;'
            'background:#F6D3C2;transform-origin:0 50%;transform:scaleX(0)"></div>')
    cap = capture_card('cap', fw, fh, mode='fvp', img='assets/sonnet_page.png', overlay=band, overlayBlend='multiply',
                       inner0=dict(fx=960, fy=640, k=0.75),                         # the page top, whole width
                       inner=[dict(t=1.2, dur=0.9, fx=980, fy=1560, k=1.25)])      # scroll + push to the pricing lines
    cfg = dict(id='r01', dur=b['dur'], mode='fvp', cam0=dict(x=784, y=540, s=1.0), cards=[cap], moves=[], heroes=[dict(t=0, id='cap')],
               reveals=[dict(el='hlP', t=2.3, dur=0.6, type='scaleX')], sfx=[])
    page('r01', cfg, backdrop=('img', 'assets/sonnet_page.png', fw, fh))
