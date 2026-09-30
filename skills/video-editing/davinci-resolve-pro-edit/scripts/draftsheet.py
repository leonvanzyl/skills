"""Contact sheet of a draft render: n frames across the beat -> chk/<id>_sheet.png (LOOK at it).
usage: python scripts/draftsheet.py g01 [8] [--full]      --full reads gfx/out/<id>.mp4 or media/<id>.mp4 instead of the draft"""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, 'scripts'); import config as C
rid = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 8
src = f'gfx/draft/{rid}.mp4'
if '--full' in sys.argv:
    src = next((p for p in (os.path.join(C.MEDIA, f'{rid}.mp4'), os.path.join(C.MEDIA, f'{rid}.mov'), f'gfx/out/{rid}.mp4') if os.path.exists(p)))
dur = float(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', src], capture_output=True, text=True).stdout)
ts = [min(dur - 0.1, i * dur / (n - 1)) for i in range(n)]
os.makedirs('chk/d', exist_ok=True); ims = []
font = ImageFont.truetype(C.FONTS + 'Poppins-SemiBold.ttf', 22)
cols = 4; tw, th = 480, 270
for t in ts:
    f = f'chk/d/{rid}_{t:.2f}.png'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{t:.3f}', '-i', src, '-frames:v', '1', '-vf', f'scale={tw}:{th}', f], check=True)
    im = Image.open(f).convert('RGB'); ImageDraw.Draw(im).text((8, 4), f'{t:.2f}s', fill='red', font=font, stroke_width=2, stroke_fill='white'); ims.append(im)
rows = (len(ims) + cols - 1) // cols
S = Image.new('RGB', (tw * cols, th * rows), 'white')
for i, im in enumerate(ims): S.paste(im, ((i % cols) * tw, (i // cols) * th))
os.makedirs('chk', exist_ok=True); S.save(f'chk/{rid}_sheet.png'); print(f'chk/{rid}_sheet.png')
