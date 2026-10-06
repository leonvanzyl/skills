"""The short's thumbnail (editing-spec.md 8c). The candidates are chosen while the short is built, never by scanning it: every
composition marks its thumbnail moments in its config (`thumb`, collected by build_gfx.py into gfx/thumbs.json), and this
renders only those frames, clean (no captions, CTA or cover), one compose.py seek each, all at once. finish.sh runs it in the
background while it concatenates, so the sheet is waiting when the short is done.
usage: python scripts/thumbnail.py s1 [t1,t2,...]          the marked candidates (plus any extra times) -> <sk>/thumb/f_<t>.png,
                                                           <sk>/thumb/candidates.json and chk/<sk>_thumbs.png (LOOK)
       python scripts/thumbnail.py s1 --pick t [NN slug]   that frame -> <sk>/thumbnail.jpg (1080x1920, under 2 MB) + thumbnail.json,
                                                           copied to ../edit/short-NN_<slug>/thumbnail.jpg
A `thumb` entry is a run-relative time, or a window [a, b] where the hero is landed and the camera at rest: on a split the
frame is taken in the longest word gap inside the window (mouth at rest), on a full visual in its middle. Each candidate
prints its run, layout, a sharpness score of the content area (compare frames of the same run: low = motion blur or a card
mid-entrance) and, where my face shows, the word being said. The sheet shows every frame at full and at Shorts-feed size, with Instagram's 4:5 feed crop marked."""
import io, json, os, shutil, subprocess, sys
import cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont

sk = sys.argv[1]; FPS = 60
C = json.load(open('cut.json'))[sk]; RUNS = C['runs']; WORDS = C['words']
snap = lambda t: round(t * FPS) / FPS           # compose.py renders whole frames: name the files the way it does
path = lambda t: f'{sk}/thumb/f_{t:07.3f}.png'
AREA = {'split': (40, 900), 'fv': (0, 1230), 'fc': (0, 1920)}   # where sharpness counts: the graphic above the card, the main element

def run_at(t):
    for r in RUNS:
        if r['T0'] - 1e-6 <= t < r['T1'] - 1e-6: return r
    return RUNS[-1]

def gaps(a, b):
    """quiet stretches between words inside [a, b], as (start, end)"""
    edges = [0.0] + [x for w in WORDS for x in (w['s'], w['e'])] + [C['END']]
    out = [(max(a, edges[k]), min(b, edges[k + 1])) for k in range(0, len(edges) - 1, 2)]
    return [(g0, g1) for g0, g1 in out if g1 - g0 > 0]

def mouth(t, r):
    if r['layout'] == 'fv': return ''
    for w in WORDS:
        if w['s'] <= t < w['e']: return f'"{w["w"]}"'
    g = [x for x in gaps(t - 2, t + 2) if x[0] <= t <= x[1]]
    return f'gap {(g[0][1] - g[0][0]) * 1000:.0f} ms' if g else 'gap'

def from_window(r, a, b):
    a, b = r['T0'] + max(0.0, a), r['T0'] + min(r['dur'] - 1 / FPS, b)
    if r['layout'] != 'fv':
        g = max(gaps(a, b), key=lambda x: x[1] - x[0], default=None)
        if g and g[1] - g[0] >= 0.08: return (g[0] + g[1]) / 2
    return (a + b) / 2

def render(ts):
    """one compose.py seek per frame, all in parallel (~1.5 s each)"""
    ps = [(t, subprocess.Popen([sys.executable, 'scripts/compose.py', sk, '--preview', f'{t:.3f}', '--clean'],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)) for t in ts]
    for t, p in ps:
        out = p.communicate()[0]
        if p.returncode or not os.path.exists(path(t)): print(out[-1500:]); sys.exit(f'thumbnail frame {t:.3f} FAILED')

if '--pick' in sys.argv:
    i = sys.argv.index('--pick'); t = snap(float(sys.argv[i + 1])); NN, SLUG = (sys.argv[i + 2:i + 4] + [None, None])[:2]
    if not os.path.exists(path(t)): render([t])
    r = run_at(t); im = Image.open(path(t)).convert('RGB')
    for q in (95, 92, 90, 87, 85, 80):           # YouTube's custom-thumbnail limit is 2 MB
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=q, subsampling=0, optimize=True, progressive=True)
        if buf.tell() < 2_000_000: break
    open(f'{sk}/thumbnail.jpg', 'wb').write(buf.getvalue())
    cands = json.load(open(f'{sk}/thumb/candidates.json')) if os.path.exists(f'{sk}/thumb/candidates.json') else []
    json.dump(dict(t=round(t, 3), run=r['i'], layout=r['layout'], text=r.get('text', ''), quality=q, bytes=buf.tell(), candidates=cands),
              open(f'{sk}/thumbnail.json', 'w'), indent=1)
    print(f'{sk}/thumbnail.jpg  1080x1920  q{q}  {buf.tell() / 1e6:.2f} MB  from {t:.3f} s (run {r["i"]}, {r["layout"]})')
    if NN and SLUG:
        D = f'../edit/short-{NN}_{SLUG}'; os.makedirs(D, exist_ok=True)
        shutil.copy(f'{sk}/thumbnail.jpg', f'{D}/thumbnail.jpg'); print(f'delivered {D}/thumbnail.jpg')
    sys.exit(0)

# the candidates: what the compositions marked, plus any times given here
marked = json.load(open('gfx/thumbs.json')) if os.path.exists('gfx/thumbs.json') else {}
T = []
for r in RUNS:
    for m in marked.get(f'{sk}_r{r["i"]}', []):
        T.append(from_window(r, *m) if isinstance(m, (list, tuple)) else r['T0'] + m)
if len(sys.argv) > 2 and not sys.argv[2].startswith('-'):
    T += [float(x) for x in sys.argv[2].split(',')]
if not T:
    sys.exit(f'{sk}: no thumbnail candidates. Mark them in the compositions (thumb=[[a, b]] in gfx_<tag>.py, then build_gfx.py), '
             f'or pass times: thumbnail.py {sk} t1,t2,...')
T = sorted({snap(t) for t in T})
render(T)                                       # always fresh: after an edit a cached frame would be stale, and each costs ~1.5 s

TW, TH, FW, FH, LH, PAD = 360, 640, 180, 320, 64, 16    # each frame at 1/3 size, its label, and at Shorts-feed size underneath
cols = min(6, len(T)); rows = (len(T) + cols - 1) // cols; CH = TH + LH + FH + PAD
try: font = ImageFont.truetype('fonts/Poppins-Medium.ttf', 20)
except OSError: font = ImageFont.load_default()
sheet = Image.new('RGB', (cols * (TW + PAD) + PAD, rows * CH + PAD), (40, 40, 44)); d = ImageDraw.Draw(sheet)
cands = []
for k, t in enumerate(T):
    r = run_at(t); im = Image.open(path(t)).convert('RGB'); m = mouth(t, r)
    y0, y1 = AREA[r['layout']]
    s = cv2.Laplacian(cv2.cvtColor(np.asarray(im)[y0:y1], cv2.COLOR_RGB2GRAY), cv2.CV_64F).var()
    cands.append(dict(t=round(t, 3), run=r['i'], layout=r['layout'], sharpness=round(s), mouth=m))
    print(f'{t:8.3f} s  run {r["i"]} {r["layout"]:5s}  sharpness {s:6.0f}  {m}')
    x, y = PAD + (k % cols) * (TW + PAD), PAD + (k // cols) * CH
    sheet.paste(im.resize((TW, TH), Image.LANCZOS), (x, y))
    for yc in (285, 1635):                      # Instagram's feed shows the centre 4:5 (its grid the centre 3:4): keep the subject inside
        d.line([(x, y + yc * TH // 1920), (x + TW - 1, y + yc * TH // 1920)], fill=(217, 119, 87), width=2)
    d.text((x, y + TH + 6), f'{t:.3f} s  run {r["i"]} {r["layout"]}', fill='white', font=font)
    d.text((x, y + TH + 32), f'sharp {s:.0f}  {m}'[:34], fill=(200, 200, 200), font=font)
    sheet.paste(im.resize((FW, FH), Image.LANCZOS), (x + (TW - FW) // 2, y + TH + LH))
json.dump(cands, open(f'{sk}/thumb/candidates.json', 'w'), indent=1)
os.makedirs('chk', exist_ok=True); sheet.save(f'chk/{sk}_thumbs.png')
print(f'LOOK at chk/{sk}_thumbs.png, then: python scripts/thumbnail.py {sk} --pick <t> NN slug')
