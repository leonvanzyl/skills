"""Eye-contact sheet: 8 frames per kept line (or --step 0.1 around a turn) cropped to the eyes, labelled with timeline and
source time, so you can SEE on-lens vs reading. Crop comes from the median eye position in gaze10.npy.
usage: python scripts/eyesheet.py s1            -> s1_eyes.png (8 per line)
       python scripts/eyesheet.py --window 498.2,498.9 [--step 0.1] -> eyes_498.2.png (source seconds)
Frames are grabbed by parallel ffmpeg seeks (EYE_WORKERS, default 12) and cached in eyes/, so a sheet takes seconds."""
import json, subprocess, os, sys, numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, 'scripts'); import config as C

g = np.load('gaze10.npy'); ok = g[:, 1] > 0
ex, ey, ed = np.median(g[ok, 6]), np.median(g[ok, 7]), np.median(g[ok, 5])
cw, ch = int(ed * 4.4) // 2 * 2, int(ed * 2.0) // 2 * 2
x0, y0 = int(max(0, ex - cw / 2)), int(max(0, ey - ch * 0.45))
CROP = f'crop={cw}:{ch}:{x0}:{y0},scale=330:{int(330 * ch / cw) // 2 * 2}'
TH = int(330 * ch / cw) // 2 * 2
font = ImageFont.truetype('fonts/Poppins-Medium.ttf', 15) if os.path.exists('fonts/Poppins-Medium.ttf') else ImageFont.load_default()
os.makedirs('eyes', exist_ok=True)
WORKERS = int(os.environ.get('EYE_WORKERS', '12'))

def fetch(src_t):
    """one exact still (output seeking) -> eyes/<t>.png, cached"""
    f = f'eyes/{src_t:.3f}.png'
    if not os.path.exists(f):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, src_t - 1):.3f}', '-i', C.SRC, '-ss', f'{min(1, src_t):.3f}', '-frames:v', '1', '-vf', CROP, f])
    return f

def prefetch(times):
    """grab every missing frame at once: the seeks are independent, so they run in parallel"""
    with ThreadPoolExecutor(WORKERS) as ex_: list(ex_.map(fetch, sorted(set(round(float(t), 3) for t in times))))

def grab(src_t, label):
    im = Image.open(fetch(src_t)).convert('RGB'); d = ImageDraw.Draw(im)
    d.text((3, 2), label, fill='yellow', font=font, stroke_width=2, stroke_fill='black'); return im

if '--window' in sys.argv:
    a, b = [float(x) for x in sys.argv[sys.argv.index('--window') + 1].split(',')]
    step = float(sys.argv[sys.argv.index('--step') + 1]) if '--step' in sys.argv else 0.1
    ts = list(np.arange(a, b + 1e-6, step)); prefetch(ts)
    ims = [grab(t, f'{t:.2f}') for t in ts]
    cols = 10; rows = [ims[i:i + cols] for i in range(0, len(ims), cols)]
    S = Image.new('RGB', (330 * cols, TH * len(rows)))
    for r, row in enumerate(rows):
        for c, im in enumerate(row): S.paste(im, (c * 330, r * TH))
    S.save(f'eyes_{a}.png'); print(f'eyes_{a}.png'); sys.exit()

sk = sys.argv[1]
Cc = json.load(open('cut.json'))[sk]; S_ = json.load(open('shorts.json'))[sk]
plan = []
for L in S_['lines']:
    ps = [p for p in Cc['pieces'] if p['line'] == L['id']]
    t0, t1 = ps[0]['pic0'], ps[-1]['pic1']
    cells = []
    for t in np.linspace(t0 + 0.05, t1 - 0.05, 8):
        p = [p for p in ps if p['pic0'] - 1e-6 <= t < p['pic1'] + 1e-6] or ps
        src = t - p[0]['off']
        cells.append((src, f'{L["id"]} T{t:.2f} s{src:.2f}'))
    plan.append((L, cells))
prefetch([src for _, cells in plan for src, _ in cells])
rows = []
for L, cells in plan:
    ims = [grab(src, label) for src, label in cells]
    row = Image.new('RGB', (330 * 8, TH)); [row.paste(im, (i * 330, 0)) for i, im in enumerate(ims)]
    ImageDraw.Draw(row).text((2, TH - 20), L['layout'], fill='cyan', font=font, stroke_width=2, stroke_fill='black'); rows.append(row)
sheet = Image.new('RGB', (330 * 8, TH * len(rows))); [sheet.paste(r, (0, i * TH)) for i, r in enumerate(rows)]
sheet.save(f'{sk}_eyes.png'); print(f'{sk}_eyes.png')
