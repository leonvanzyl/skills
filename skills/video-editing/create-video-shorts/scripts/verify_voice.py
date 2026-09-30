import os, glob, site, json, numpy as np, soundfile as sf
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp,'nvidia','*','bin')): os.add_dll_directory(d); os.environ['PATH']=d+os.pathsep+os.environ['PATH']
from faster_whisper import WhisperModel
def _wm():
    try: return WhisperModel('large-v3', device='cuda', compute_type='float16')
    except Exception as e:
        print('no CUDA for Whisper (' + str(e)[:60] + ') - using CPU int8 (slower)'); return WhisperModel('large-v3', device='cpu', compute_type='int8')
import sys as _s; _s.path.insert(0, 'scripts'); import config as _C
import scipy.signal as ss
wm=_wm()
C=json.load(open('cut.json'))
for sk in (_s.argv[1:] or list(C.keys())):
    x,sr=sf.read(f'{sk}/voice.wav'); m=x.mean(1)
    hop=480; n=len(m)//hop; db=20*np.log10(np.sqrt((m[:n*hop].reshape(n,hop)**2).mean(1))+1e-9)
    # quiet stretches relative: voice normalised to -14 LUFS, source threshold -35 dBFS was at ~-17 LUFS-ish; use same abs threshold
    q=[];r=None
    for j in range(n):
        if db[j]<-35:
            if r is None: r=j
        else:
            if r is not None and r>5: q.append((r/100,(j-r)*10))
            r=None
    long=[(round(a,2),d) for a,d in q if d>150]
    x16=ss.resample_poly(m,1,3).astype(np.float32)
    segs,_=wm.transcribe(x16,language='en',beam_size=5,condition_on_previous_text=False,initial_prompt=_C.ASR_PROMPT)
    txt=' '.join(s.text.strip() for s in segs)
    print(f'== {sk} len={len(m)/sr:.2f}s  quiet>150ms: {long}  max quiet={max(d for a,d in q) if q else 0}ms')
    print('  ',txt)
