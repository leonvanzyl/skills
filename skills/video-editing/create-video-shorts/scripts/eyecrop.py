"""Full-resolution eye crops from the master's webcam, labelled, as one sheet -> chk/<name>.png. Use it to decide on-lens vs
reading before a line becomes a camera run (pipeline.md 2). eyesheet.py's crops show the whole face at about 0.4x, which
hides a lowered gaze; these are a tight crop round the eyes at about 0.75x, from the median eye position in gaze10.npy.
Learned on "Last Call" (2026-10-19): with the webcam just above the screen, gaze.py's two pose clusters and the look-down
blendshape did not separate reading from looking at the lens, and three runs had to be re-laid out. At this size reading
shows plainly: eyes lowered, the head nearly frontal.
usage (in work-<stem>/):  python scripts/eyecrop.py <name> <t> [<t> ...] | <a0>:<a1>:<step> [...]   (master / source seconds)
  e.g. python scripts/eyecrop.py e_L4 347.4:354.0:0.3     -> chk/e_L4.png, 8 crops a row, cached in chk/eyec/"""
import os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, 'scripts'); import config as C

if len(sys.argv) < 3: sys.exit(__doc__)
name = sys.argv[1]; ts = []
for a in sys.argv[2:]:
    if ':' in a:
        a0, a1, st = map(float, a.split(':')); ts += [round(float(t), 2) for t in np.arange(a0, a1 + 1e-6, st)]
    else: ts.append(float(a))
x, y, w, h = [int(v) for v in C.SAFE]
if os.path.exists('gaze10.npy'):
    g = np.load('gaze10.npy'); ok = g[:, 1] > 0
    ed, ex, ey = (float(np.median(g[ok, i])) for i in (5, 6, 7))
else:   # no gaze scan yet: eyes at about 44% of the webcam's height, 1/4 of its width apart
    ed, ex, ey = w / 4, x + w / 2, y + 0.44 * h
cw, ch = int(2.45 * ed) // 2 * 2, int(1.0 * ed) // 2 * 2          # tuned on a 700x946 webcam (eye distance 180 px)
cx0 = int(min(max(ex - cw / 2, 0), C.SRC_W - cw)); cy0 = int(min(max(ey - ch / 2, 0), C.SRC_H - ch))
os.makedirs('chk/eyec', exist_ok=True)


def grab(t):
    f = f'chk/eyec/{t:.2f}_{cw}x{ch}.png'
    if not os.path.exists(f):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, t - 1):.3f}', '-i', C.SRC, '-ss', f'{min(1, t):.3f}', '-frames:v', '1',
                        '-vf', f'crop={cw}:{ch}:{cx0}:{cy0},scale=330:-2', f])
    return f


with ThreadPoolExecutor(int(os.environ.get('EYE_WORKERS', '12'))) as ex_: fs = list(ex_.map(grab, ts))
ims = [Image.open(f).convert('RGB') for f in fs]; W, H = ims[0].size; n = 8
S = Image.new('RGB', (W * n, H * ((len(ims) + n - 1) // n)))
fnt = ImageFont.truetype('fonts/Poppins-Medium.ttf', 22) if os.path.exists('fonts/Poppins-Medium.ttf') else ImageFont.load_default()
for i, (t, im) in enumerate(zip(ts, ims)):
    ImageDraw.Draw(im).text((4, 2), f'{t:.2f}', fill='yellow', font=fnt, stroke_width=2, stroke_fill='black')
    S.paste(im, ((i % n) * W, (i // n) * H))
os.makedirs('chk', exist_ok=True); S.save(f'chk/{name}.png'); print(f'chk/{name}.png  ({len(ts)} crops of {cw}x{ch} source px at {cx0},{cy0})')
