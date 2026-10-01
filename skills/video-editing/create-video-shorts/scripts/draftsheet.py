"""Contact sheet of a 10 fps draft render: python scripts/draftsheet.py s1_r0 [8] -> chk/s1_r0_sheet.png
The frame grabs run in parallel (one ffmpeg seek each)."""
import subprocess, sys, os, json
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont
rid=sys.argv[1]; n=int(sys.argv[2]) if len(sys.argv)>2 else 8
src=f'gfx/draft/{rid}.mp4'
dur=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',src],capture_output=True,text=True).stdout)
ts=[min(dur-0.2, i*dur/(n-1)) for i in range(n)]
os.makedirs('chk/d',exist_ok=True)
font=ImageFont.truetype('arial.ttf',28)
def grab(t):
    f=f'chk/d/{rid}_{t:.2f}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.3f}','-i',src,'-frames:v','1','-vf','scale=270:480',f],check=True)
    return f
with ThreadPoolExecutor(min(8, len(ts))) as ex: files=list(ex.map(grab, ts))
ims=[]
for t,f in zip(ts,files):
    im=Image.open(f).convert('RGB'); ImageDraw.Draw(im).text((6,4),f'{t:.1f}',fill='red',font=font); ims.append(im)
S=Image.new('RGB',(270*len(ims),480)); [S.paste(im,(i*270,0)) for i,im in enumerate(ims)]
S.save(f'chk/{rid}_sheet.png')
