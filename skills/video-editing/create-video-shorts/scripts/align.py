import re, json, numpy as np, torch, torchaudio
from num2words import num2words
_bundle=None
def bundle():
    global _bundle
    if _bundle is None:
        b=torchaudio.pipelines.WAV2VEC2_ASR_LARGE_LV60K_960H; _bundle=(b, b.get_model().eval(), b.get_labels())
    return _bundle
def spoken(w):
    w=w.strip().lower().replace('’',"'")
    w=re.sub(r'[“”",!?;:…]','',w).strip()
    if w in ('.5','.5.','.5,'): return ['point','five']
    if w in ('.1','.1.'): return ['point','one']
    m=re.match(r"^\$(\d+)[.,]?$",w)
    if m: return num2words(int(m.group(1))).replace('-',' ').replace(',','').split()+['dollars']
    w=w.rstrip('.,')
    if w=='3d': return ['three','d']
    if w=='cli': return ['c','l','i']
    if w in ('sonic',): return ['sonnet']
    if w=='cloud': return ['claude']
    m=re.match(r'^(\d+)\.(\d+)$',w)
    if m: return num2words(int(m.group(1))).split()+['point']+[num2words(int(c)) for c in m.group(2)]
    if re.match(r'^\d+$',w): return num2words(int(w)).replace('-',' ').replace(',','').split()
    w=w.replace('-',' ').replace('.',' ')
    return [t for t in w.split() if t]
def align(audio16, words):
    """audio16: float32 mono 16k; words: list of display words. returns list of (start,end,score) per word (sec, relative)"""
    b,model,labels=bundle(); dic={c:i for i,c in enumerate(labels)}
    toks=[];owner=[]
    for wi,w in enumerate(words):
        for t in spoken(w):
            t=''.join(c for c in t.upper() if c in dic or c=="'")
            if t: toks.append(t); owner.append(wi)
    with torch.inference_mode():
        em,_=model(torch.from_numpy(audio16)[None])
        em=torch.log_softmax(em,-1)
    targets=torch.tensor([[dic[c] for t in toks for c in t]],dtype=torch.int32)
    ali,scores=torchaudio.functional.forced_align(em,targets,blank=0)
    ali=ali[0];scores=scores[0].exp()
    spans=torchaudio.functional.merge_tokens(ali,scores)
    ratio=audio16.shape[0]/16000/em.shape[1]
    # group char spans into tokens
    res=[];k=0
    for t in toks:
        n=len(t); sp=spans[k:k+n]; k+=n
        res.append((sp[0].start*ratio, sp[-1].end*ratio, float(np.mean([s.score for s in sp]))))
    out=[None]*len(words)
    for (s,e,sc),wi in zip(res,owner):
        if out[wi] is None: out[wi]=[s,e,[sc]]
        else: out[wi][1]=e; out[wi][2].append(sc)
    return [(o[0],o[1],float(np.mean(o[2]))) if o else None for o in out]
