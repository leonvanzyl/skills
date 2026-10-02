import os, glob, site, json, re, difflib, numpy as np, soundfile as sf, sys
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp,'nvidia','*','bin')): os.add_dll_directory(d); os.environ['PATH']=d+os.pathsep+os.environ['PATH']
sys.path.insert(0,'scripts'); from align import align, spoken
from faster_whisper import WhisperModel
ASR_WORKERS = 4   # line windows are re-transcribed concurrently: one model, 4 CUDA workers (identical results, ~2x faster; 8 is no faster)
def _wm():
    try: return WhisperModel('large-v3', device='cuda', compute_type='float16', num_workers=ASR_WORKERS)
    except Exception as e:
        print('no CUDA for Whisper (' + str(e)[:60] + ') - using CPU int8 (slower)'); return WhisperModel('large-v3', device='cpu', compute_type='int8')
S=json.load(open('shorts.json')); db=np.load('rms10ms.npy')
x,sr=sf.read('clean16.wav'); x=x.astype(np.float32)
wm=_wm()
def sil_back(t):
    i=int(t*100)
    while i>12:
        if all(db[i-12:i]<-45): return (i-6)/100
        i-=1
    return 0.0
def sil_fwd(t):
    i=int(t*100)
    while i<len(db)-12:
        if all(db[i:i+12]<-45): return (i+6)/100
        i+=1
    return len(db)/100
import config as _C
FIX=_C.ASR_FIXES   # known mis-hearings for this speaker, from project.json -> asr_fixes
def norm(w): return ' '.join(spoken(w))
def _asr(job):
    sk,L,t0,t1=job; seg=x[int(t0*sr):int(t1*sr)]
    segs,_=wm.transcribe(seg,language='en',word_timestamps=True,beam_size=5,condition_on_previous_text=False,
         initial_prompt=_C.ASR_PROMPT)
    return [w.word for s in segs for w in s.words]     # the generator is consumed here, inside the worker thread
import time as _time
from concurrent.futures import ThreadPoolExecutor
_t=_time.time()
JOBS=[(sk,L,sil_back(L['a']-0.15),sil_fwd(L['b']+0.25)) for sk,sv in S.items() for L in sv['lines']]
with ThreadPoolExecutor(ASR_WORKERS) as _ex: RAW=dict(zip([(j[0],j[1]['id']) for j in JOBS],_ex.map(_asr,JOBS)))
print(f'ASR: {len(JOBS)} line windows in {_time.time()-_t:.1f}s ({ASR_WORKERS} workers)')
out={}
for sk,sv in S.items():
    for L in sv['lines']:
        t0=sil_back(L['a']-0.15); t1=sil_fwd(L['b']+0.25)
        seg=x[int(t0*sr):int(t1*sr)]
        W=[{'w':FIX.get(w.strip().lower().strip('.,'),w.strip())} for w in RAW[(sk,L['id'])]]
        al=align(seg,[w['w'] for w in W])
        for w,a in zip(W,al): w['s'],w['e'],w['sc']=round(a[0]+t0,3),round(a[1]+t0,3),round(a[2],3)
        # match line text tokens to window tokens
        wt=[]; wo=[]
        for i,w in enumerate(W):
            for t in spoken(w['w']): wt.append(t); wo.append(i)
        lt=[t for w in L['text'].split() for t in spoken(w)]
        sm=difflib.SequenceMatcher(None,wt,lt,autojunk=False)
        blocks=[b for b in sm.get_matching_blocks() if b.size>0]
        fi=wo[blocks[0].a - blocks[0].b] if blocks[0].a>=blocks[0].b else wo[blocks[0].a]
        lb=blocks[-1]; li=wo[lb.a+lb.size-1]
        matched=sum(b.size for b in blocks)
        out[f'{sk}.{L["id"]}']={'win':[t0,t1],'words':W,'fi':fi,'li':li}
        prev=W[fi-1] if fi>0 else None; nxt=W[li+1] if li+1<len(W) else None
        print(f"{sk} {L['id']} win={t0:.2f}-{t1:.2f} match={matched}/{len(lt)} first={W[fi]['w']}@{W[fi]['s']:.2f} last={W[li]['w']}@{W[li]['s']:.2f}-{W[li]['e']:.2f} prev={prev['w']+'@'+str(prev['e']) if prev else '-'} next={nxt['w']+'@'+str(nxt['s']) if nxt else '-'}")
        print('    ',' '.join(w['w'] for w in W))
json.dump(out,open('line_align.json','w'),indent=1)
# Whisper occasionally drops a short word (e.g. the last beat of a countdown). If a line's text has a word the window
# transcript lacks, add it by hand here from the RMS envelope, e.g.:
#   a = out['s2.L3']; a['words'].insert(a['li'] + 1, {'w': 'one.', 's': 247.71, 'e': 248.14, 'sc': 1.0}); a['li'] += 1
#   json.dump(out, open('line_align.json', 'w'), indent=1)
# (hand fixes go above this line; the generic passes below run last)

def _n(w): return re.sub(r'[^a-z0-9$]', '', w.lower())
for sk, sv in S.items():
    for L in sv['lines']:
        a = out.get(f'{sk}.{L["id"]}')
        if not a: continue
        ws = a['words']; toks = L['text'].split()
        if L.get('echo'):
            # Opt-in per line ("echo": true) for audio with a room echo, e.g. an AI voice on a call through speakers: the window
            # ASR hears phrases twice ("I'm doing great. I'm doing great."). Collapse an immediately repeated n-gram that the
            # plan's text has only once into ONE phrase spanning both copies, so the cut keeps the whole echo tail and the
            # captions show it once. Never use it on a stutter (that would keep the stutter in the cut).
            tn = [_n(t) for t in toks]
            def text_repeats(g): return any(tn[i:i + len(g)] == g and tn[i + len(g):i + 2 * len(g)] == g for i in range(len(tn)))
            changed = True
            while changed:
                changed = False
                hi = min(len(ws), a['li'] + 1 + 4)          # also an echo of the line's last words just after it
                for n in (4, 3, 2, 1):
                    for i in range(a['fi'], hi - 2 * n + 1):
                        g1 = [_n(w['w']) for w in ws[i:i + n]]; g2 = [_n(w['w']) for w in ws[i + n:i + 2 * n]]
                        if g1 == g2 and not text_repeats(g1) and i + n - 1 <= a['li'] and ws[i + n]['s'] - ws[i + n - 1]['e'] < 0.8:
                            end2 = i + 2 * n - 1
                            ws[i + n - 1]['e'] = ws[end2]['e']; del ws[i + n:end2 + 1]
                            if a['li'] >= end2: a['li'] -= n
                            elif a['li'] >= i + n: a['li'] = i + n - 1
                            changed = True; break
                    if changed: break
            print(f'{sk} {L["id"]} echo collapsed:', ' '.join(w['w'] for w in ws[a['fi']:a['li'] + 1]))
        # Captions use the plan's exact words (casing at sentence starts, "five" not "5", a word the ASR misheard) with the
        # aligned timings, whenever the aligned span has as many words as the line's text.
        span = ws[a['fi']:a['li'] + 1]
        if len(span) == len(toks):
            for w, t in zip(span, toks): w['w'] = t
        else:
            print(f'captions keep the ASR words for {sk}.{L["id"]}: {len(span)} aligned vs {len(toks)} text words')
json.dump(out, open('line_align.json', 'w'), indent=1)
