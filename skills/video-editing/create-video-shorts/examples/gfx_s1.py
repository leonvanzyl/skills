# EXAMPLE from the "Half the price of Opus?" short. Every crop rectangle, time and filename below is specific to that video.
# Copy to work-<stem>/scripts/prep_assets.py and rewrite for your video. Crops must avoid the webcam window (project.json camera.window).
# ===================================================================== SHORT 1 (imported by build_gfx.py)
from build_gfx_common import *

UW, UH = 1000, round(1000 * 214 / 1110)          # session cards (real crops 1110x214)
U_COST = (150 / 1110, 97 / 214); U_TIME = (900 / 1110, 97 / 214)

MENU_JS = """window.CFG_RENDER=function(t){const m=CFG.menu;const el=document.getElementById('menuhl');if(!el)return;
  let y=null,prev=null,p=1;for(const [tt,k] of m.t){if(t>=tt){prev=y;y=m.rows[k];p=Math.min(1,(t-tt)/0.5);}}
  const e=gsap.parseEase('power3.inOut')(p);const yy=(prev==null||y==null)?y:prev+(y-prev)*e;
  let o=y==null?0:Math.min(1,(t-m.t[0][0])/0.25); if(t>m.hide) o*=Math.max(0,1-(t-m.hide)/0.3);
  el.style.opacity=o; if(yy!=null) el.style.top=(yy-32)+'px';};"""
MENU_ROWS = {'opus': 752, 'fable': 828, 'sonnet': 906, 'haiku': 984}
MENU_HL = '<div id="menuhl" style="position:absolute;left:1102px;width:392px;height:64px;border-radius:12px;background:rgba(217,119,87,.28);border:3px solid #D97757;opacity:0"></div>'


def build():
    # R0 split hook. Frame 0 (cover): Claude logo lockup at y~762 (below the title box).
    # Step to the real benchmark table at "benchmarks", then push onto the Terminal-Bench row.
    r, ws = words('s1', 0)
    bw, bh = 1040, round(1040 * 606 / 1440); sx = bw / 1440
    by = 1300
    band = lambda i, x0, x1: f'<div id="hlb{i}" class="band" style="position:absolute;left:{x0*sx}px;top:{96*sx}px;width:{(x1-x0)*sx}px;height:{134*sx}px"></div>'
    bench_html = band(2, 1124, 1436) + '<img src="assets/bench.png" style="position:absolute;inset:0;width:100%;height:100%;mix-blend-mode:multiply">'
    cards = [dict(id='logo', kind='logo', x=540, y=762, w=520, h=114, html=LOGO_HTML),
             dict(id='bench', kind='media', x=540, y=by, w=bw, h=bh, html=bench_html, radius=30)]
    by0 = by - bh / 2
    land_y = by - (690 - 470)          # bench centre lands at screen y 690 (bottom edge ~900)
    t_b = W(ws, 'benchmarks') - 0.25; t_ag = W(ws, 'especially') - 0.15
    moves = [dict(t=t_b, dur=0.5, kind='step', to=dict(x=540, y=land_y, s=1.0)),
             dict(t=t_b + 0.55, dur=t_ag - t_b - 0.6, kind='glide', to=dict(x=540, y=land_y - 8, s=1.03)),
             dict(t=t_ag, dur=1.6, kind='push', to=dict(x=540 - bw / 2 + sx * 960, y=by0 + sx * 163 - 120 / 1.55, s=1.55))]
    extra_css = '.band{background:#FBEEE8;transform-origin:0 50%;border-radius:8px;transform:scaleX(0)}'
    cfg = dict(id='s1_r0', dur=r['dur'], mode='split', cam0=dict(x=540, y=470, s=1.0), cards=cards, moves=moves, pushRef=1.03,
               heroes=[dict(t=0, id='logo'), dict(t=t_b + 0.1, id='bench')],
               reveals=[dict(el='hlb2', t=W(ws, 'agentic') - 0.1, dur=0.5, type='scaleX')], sfx=[],
               thumb=[[t_b + 0.5, t_ag]])          # thumbnail candidate: the real benchmark table landed, before the push
    page('s1_r0', cfg, extra_css=extra_css)

    # R1 full visual: real claude.com pricing page in the fixed capture frame; inner camera Sonnet -> Opus -> Fable price rows
    r, ws = words('s1', 1)
    fw, fh = D['pricing.png']
    inner = [dict(t=W(ws, 'half') - 0.25, dur=0.6, fx=1712, fy=990, k=1.32),
             dict(t=W(ws, 'opus') - 0.25, dur=0.6, fx=1040, fy=990, k=1.32),
             dict(t=W(ws, 'five') - 0.25, dur=0.6, fx=368, fy=990, k=1.32)]
    cards = [capture_card('cap', fw, fh, inner0=dict(fx=1712, fy=720, k=1.05), inner=inner, img='assets/pricing.png')]
    cfg = dict(id='s1_r1', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1), cards=cards, moves=[], heroes=[dict(t=0, id='cap')], sfx=[])
    page('s1_r1', cfg, backdrop=('img', 'assets/pricing.png', fw, fh))

    # R3 full visual: Claude logo large + centred -> whip -> real model menu; highlight steps to each named model; pan to the prompt
    r, ws = words('s1', 3)
    fw, fh = D['menu_still.png']
    t_whip = 0.9
    cards = [dict(id='logo', kind='logo', x=540, y=720, w=760, h=166, html=LOGO_HTML),
             capture_card('cap', fw, fh, x=540, y=720 + 2400, img='assets/menu_still.png', overlay=MENU_HL,
                          inner0=dict(fx=1260, fy=800, k=1.5), backdrop={'tIn': t_whip + 0.35},
                          inner=[dict(t=W(ws, 'exact') - 0.4, dur=0.7, fx=700, fy=560, k=1.25)])]
    cfg = dict(id='s1_r3', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1), cards=cards,
               moves=[dict(t=t_whip, kind='whip', to=dict(x=540, y=720 + 2400, s=1), via=dict(x=540, y=720 + 1200, s=0.85))],
               heroes=[dict(t=0, id='logo'), dict(t=t_whip + 0.45, id='cap')], sfx=[dict(t=round(t_whip + 0.45, 3), type='whoosh')],
               thumb=[[0, t_whip]],                # the Claude logo, large and centred, before the whip
               menu=dict(rows=MENU_ROWS, t=[[W(ws, 'sonnet') - 0.25, 'sonnet'], [W(ws, 'opus') - 0.25, 'opus'], [W(ws, 'fable') - 0.25, 'fable']], hide=W(ws, 'exact') - 0.45))
    page('s1_r3', cfg, backdrop=('img', 'assets/menu_still.png', fw, fh), extra_js=MENU_JS)

    # R5 full visual: synced Sonnet usage panel ; push to Active 1h 21m, then Cost $25.95
    r, ws = words('s1', 5)
    fw, fh = D['s1_r5']
    cards = [capture_card('cap', fw, fh, inner0=dict(fx=620, fy=700, k=1.0),
                          inner=[dict(t=W(ws, '1') - 0.25, dur=0.6, fx=900, fy=682, k=1.6),
                                 dict(t=W(ws, 'cost') - 0.25, dur=0.6, fx=330, fy=682, k=1.6)])]
    cfg = dict(id='s1_r5', dur=r['dur'], mode='fv', cam0=dict(x=540, y=720, s=1), cards=cards, moves=[], heroes=[dict(t=0, id='cap')], sfx=[])
    page('s1_r5', cfg, videos=[('cap', 'assets/s1_r5.mp4', fw, fh)], backdrop=('video', 'assets/s1_r5.mp4', fw, fh))

    # R6 split: the two real session cards (Sonnet $25.95 / Opus $27.89)
    r, ws = words('s1', 6)
    cards = [dict(id='son', kind='media', x=540, y=450, w=UW, h=UH, img='assets/usage_sonnet.png', bg='#141414'),
             dict(id='opu', kind='media', x=540, y=790, w=UW, h=UH, img='assets/usage_opus.png', bg='#141414')]
    cfg = dict(id='s1_r6', dur=r['dur'], mode='split', cam0=dict(x=540, y=470, s=1.0), cards=cards,
               moves=[dict(t=0.2, dur=r['dur'] - 0.2, kind='glide', to=dict(x=540, y=476, s=1.03))], pushRef=1.0,
               heroes=[dict(t=0, id='son'), dict(t=W(ws, 'opus') - 0.25, id='opu')], sfx=[],
               thumb=[[W(ws, 'opus'), r['dur']]])  # $25.95 vs $27.89 above the head pop-out (build_gfx clips off the focus hand-off)
    page('s1_r6', cfg)

    # R7 full visual: same two cards ; push onto Sonnet cost, step to its time, pull back to both
    r, ws = words('s1', 7)
    ys, yo = 780, 1120
    cost = (540 - UW / 2 + UW * U_COST[0], ys - UH / 2 + UH * U_COST[1]); tim = (540 - UW / 2 + UW * U_TIME[0], cost[1])
    cards = [dict(id='son', kind='media', x=540, y=ys, w=UW, h=UH, img='assets/usage_sonnet.png', bg='#141414'),
             dict(id='opu', kind='media', x=540, y=yo, w=UW, h=UH, img='assets/usage_opus.png', bg='#141414')]
    moves = [dict(t=0.25, dur=W(ws, 'cheaper') - 0.65, kind='glide', to=dict(x=540, y=712, s=1.04)),
             dict(t=W(ws, 'cheaper') - 0.4, dur=1.2, kind='push', to=dict(x=cost[0] + 150, y=cost[1], s=1.7)),
             dict(t=W(ws, 'faster') - 0.25, dur=0.5, kind='step', to=dict(x=tim[0] - 150, y=tim[1], s=1.7)),
             dict(t=W(ws, 'costing') - 0.25, dur=1.5, kind='pull', to=dict(x=540, y=722, s=1.0))]
    cfg = dict(id='s1_r7', dur=r['dur'], mode='fv', cam0=dict(x=540, y=722, s=1.0), cards=cards, moves=moves, pushRef=1.04,
               heroes=[dict(t=0, id='son'), dict(t=W(ws, 'costing') - 0.1, id='none')], sfx=[],
               thumb=[[W(ws, 'costing') + 1.25, r['dur']]])   # pulled back: both cards sharp
    page('s1_r7', cfg)
