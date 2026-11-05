"""Contact sheet of the RAW recordings' frames at final-video times, through longform_program.json (import_longform.py or
build_raw_map.py) -> chk/<name>.png, each frame labelled with its final time, raw file and raw time. For planning the
graphics and writing GFX_BRIEF.md: see what the clean, unzoomed footage shows at a moment before choosing a crop.
Graphics agents use it too. Remember the webcam picture-in-picture is in the raw frames: never crop it into a graphic.
usage (in work-<stem>/):  python scripts/rawsheet.py <name> <final s> [<final s> ...]   -> chk/<name>.png (4 a row, 640 px)"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) < 3: sys.exit(__doc__)
if not os.path.exists('longform_program.json'): sys.exit('no longform_program.json: run import_longform.py or build_raw_map.py first')
P = json.load(open('longform_program.json', encoding='utf-8'))
name = sys.argv[1]; ts = [float(a) for a in sys.argv[2:]]
os.makedirs('chk/raw', exist_ok=True)


def raw_at(t):
    for it in P['items']:
        if it['t0'] <= t < it['t1']:
            r0 = it['raw0'] if 'raw0' in it else it['src0'] / it.get('fps', P.get('fps', 60))
            return it['file'], r0 + (t - it['t0'])
    return None, None


def grab(t):
    f, r = raw_at(t)
    if f is None: return None
    out = f'chk/raw/{t:.2f}.jpg'
    if not os.path.exists(out):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0, r - 1):.3f}', '-i', f, '-ss', f'{min(1, r):.3f}', '-frames:v', '1',
                        '-vf', 'scale=640:-2', '-q:v', '3', out])
    return out, t, os.path.basename(f), r


with ThreadPoolExecutor(12) as ex: res = [r for r in ex.map(grab, ts) if r]
miss = [t for t in ts if raw_at(t)[0] is None]
if miss: print('no raw item at', miss, '(a gap, the montage, a title card or a generated graphic in the long-form)')
if not res: sys.exit('nothing to show')
W, H = 640, 360; n = 4
S = Image.new('RGB', (W * n, H * ((len(res) + n - 1) // n)))
fnt = ImageFont.truetype('fonts/Poppins-Medium.ttf', 22) if os.path.exists('fonts/Poppins-Medium.ttf') else ImageFont.load_default()
for i, (f, t, fn, r) in enumerate(res):
    im = Image.open(f).convert('RGB').resize((W, H)); d = ImageDraw.Draw(im)
    d.text((6, 4), f'{t:.1f}  {fn}@{r:.1f}', fill='yellow', font=fnt, stroke_width=2, stroke_fill='black'); S.paste(im, ((i % n) * W, (i // n) * H))
S.save(f'chk/{name}.png'); print(f'chk/{name}.png')
