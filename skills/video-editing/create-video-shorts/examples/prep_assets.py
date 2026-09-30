# EXAMPLE from the "Half the price of Opus?" short. Every crop rectangle, time and filename below is specific to that video.
# Copy to work-<stem>/scripts/prep_assets.py and rewrite for your video. Crops must avoid the webcam window (project.json camera.window).
import json, subprocess, os, shutil
from PIL import Image
A='gfx/assets'; os.makedirs(A,exist_ok=True)
C=json.load(open('cut.json'))
import sys; sys.path.insert(0, 'scripts'); import config as _C
SRC = _C.SRC   # the master, from project.json
def still(t,crop,out,scale=None):
    x,y,w,h=crop; vf=f'crop={w}:{h}:{x}:{y}'+(f',scale={scale[0]}:{scale[1]}:flags=lanczos' if scale else '')
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.3f}','-i',SRC,'-frames:v','1','-vf',vf,f'{A}/{out}'],check=True)
def clip(out,segs,crop,maxw=2000):
    """segs: list of (src_start, dur) ; src_start may be ('freeze', t)"""
    x,y,w,h=crop; sc=min(1,maxw/w); ow,oh=int(w*sc)//2*2,int(h*sc)//2*2
    parts=[]
    for i,(s,d) in enumerate(segs):
        p=f'{A}/_tmp_{out}_{i}.mp4'
        if isinstance(s,tuple):
            vf=f'crop={w}:{h}:{x}:{y},scale={ow}:{oh}:flags=lanczos,loop=loop=-1:size=1,trim=duration={d:.4f},fps=60'
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{s[1]:.3f}','-i',SRC,'-frames:v','1','-vf',f'crop={w}:{h}:{x}:{y},scale={ow}:{oh}:flags=lanczos',p+'.png'],check=True)
            subprocess.run(['ffmpeg','-v','error','-y','-loop','1','-framerate','60','-i',p+'.png','-t',f'{d:.4f}','-c:v','libx264','-crf','12','-pix_fmt','yuv420p','-r','60',p],check=True)
            os.remove(p+'.png')
        else:
            subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{s:.4f}','-i',SRC,'-t',f'{d:.4f}','-vf',f'crop={w}:{h}:{x}:{y},scale={ow}:{oh}:flags=lanczos,fps=60','-an','-c:v','libx264','-crf','12','-pix_fmt','yuv420p',p],check=True)
        parts.append(p)
    lst=f'{A}/_list_{out}.txt'; open(lst,'w').write(''.join(f"file '{os.path.basename(p)}'\n" for p in parts))
    subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-c','copy',f'{A}/{out}'],check=True)
    for p in parts: os.remove(p)
    os.remove(lst)
    return ow,oh
def synced(sk,ri,override=None):
    """source segments matching run ri of short sk picture mapping"""
    r=C[sk]['runs'][ri]; segs=[]
    for p in C[sk]['pieces']:
        a=max(r['T0'],p['pic0']); b=min(r['T1'],p['pic1'])
        if b-a>1e-4: segs.append((a-p['off'],b-a))
    return segs
dims={}
# ---- stills from the published source pages
im=Image.open('captures/anthropic-sonnet-5-5-benchmark-table.png'); im.crop((0,0,1440,606)).save(f'{A}/bench.png')
shutil.copy('captures/claude-pricing-api-latest-models.png',f'{A}/pricing.png')
Image.open('captures/anthropic-sonnet-5-5-hero.png').convert('RGB').save(f'{A}/hero.jpg',quality=93)
shutil.copy('captures/claude-logo.svg',f'{A}/claude-logo.svg')
# ---- stills from the long-form screen recording (4K, PiP region x>=3108,y<=978 always avoided)
still(496.0,(690,885,1110,215),'usage_sonnet.png')
still(374.0,(690,655,1110,215),'usage_opus.png')
still(258.0,(690,885,1110,215),'usage_fable.png')
still(263.8,(640,260,2440,1840),'fable_menu.jpg',(1464,1104))
still(144.40,(1400,900,1700,1150),'menu_still.png')
# ---- footage clips
dims['s1_r5']=clip('s1_r5.mp4',synced('s1',5),(640,300,1240,1500))
dims['s2_r1']=clip('s2_r1.mp4',synced('s2',1),(600,1000,2100,1100))
segs=synced('s2',3); segs=[(('freeze',256.56),segs[0][1])]+segs[1:]
dims['s2_r3']=clip('s2_r3.mp4',segs,(640,300,1240,1500))
segs=synced('s2',5); segs=[(('freeze',371.45),segs[0][1])]+segs[1:]
dims['s2_r5']=clip('s2_r5.mp4',segs,(640,60,1240,1500))
dims['s2_r7_opus']=clip('s2_r7_opus.mp4',[(452.0,7.0)],(60,470,3000,1690),1600)
dims['s2_r7_sonnet']=clip('s2_r7_sonnet.mp4',[(597.4,7.0)],(60,470,3000,1690),1600)
dims['s3_r1']=clip('s3_r1.mp4',synced('s3',1),(880,340,2220,1760))
dims['s3_r3']=clip('s3_r3.mp4',[(('freeze',143.40),1.0),(143.40,2.4),(('freeze',145.80),2.0)],(1400,900,1700,1150))
dims['s3_r5']=clip('s3_r5.mp4',synced('s3',5),(1400,900,1700,1150))
for f in ['usage_sonnet.png','usage_opus.png','usage_fable.png','fable_menu.jpg','menu_still.png','bench.png','pricing.png','hero.jpg']:
    dims[f]=Image.open(f'{A}/{f}').size
json.dump(dims,open('gfx/asset_dims.json','w'),indent=1); print(json.dumps(dims))
