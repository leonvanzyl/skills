import json, sys, numpy as np, soundfile as sf, pyloudnorm as pyln, os
sys.path.insert(0,'scripts'); from align import spoken
FPS=60; SR=48000
db=np.load('rms10ms.npy'); X,_=sf.read('clean48.wav'); X=X.astype(np.float32)
S=json.load(open('shorts.json')); A=json.load(open('line_align.json'))
def I(t): return int(round(t*100))
def onset_at(fs, pe):
    """return (onset, contiguous). fs: aligned first-word start; pe: previous word end (or None)"""
    lo=I(pe) if pe is not None else I(fs-0.35)
    lo=max(lo-5, I(fs-0.35)); hi=I(fs+0.30)
    # gaps: >=30ms below -45 dB between previous word and this word
    gaps=[]; r=None
    for i in range(lo,hi):
        if db[i]<-45:
            if r is None: r=i
        else:
            if r is not None and i-r>=4 and r<I(fs+0.10): gaps.append((r,i))
            r=None
    if r is not None and hi-r>=4 and r<I(fs+0.10): gaps.append((r,hi))
    if gaps:
        i=gaps[-1][1]
        while i<I(fs+0.2) and db[i]<-45: i+=1
        return i/100, False
    if pe is None:
        return max(lo, I(fs-0.03))/100, True
    a0=I(pe)-4; a1=I(fs)+4
    k=a0+int(np.argmin(db[a0:a1])); return k/100, True
def trueend_at(ls, le, ns):
    """ls: last word start, le: aligned end, ns: next source word start (or None)"""
    lim=I(ns) if ns else I(le+0.8)
    if ns is not None and ns-le<0.08 and not any(db[I(le)-2:I(ns)+2]<-40):
        k=I(le)-3+int(np.argmin(db[I(le)-3:I(ns)+4])); return k/100, 'contig'
    i=I(ls); last=i
    while i<lim:
        if db[i]>=-35: last=i
        if db[i]<-32 and all(db[i:i+15]<-32) and i>=I(le)-5: return max(i,last+1)/100 if i<=last+1 else i/100, 'sub32'
        i+=1
    return (last+1)/100, 'lim'
def pauses(t0,t1):
    out=[];r=None
    for j in range(I(t0),I(t1)):
        if db[j]<-35:
            if r is None: r=j
        else:
            if r is not None and (j-r)/100>0.22: out.append((r/100,j/100))
            r=None
    return out
res={}
for sk,sv in S.items():
    lines=sv['lines']; M=[]
    for k,L in enumerate(lines):
        a=A[f'{sk}.{L["id"]}']; W=a['words']; fi,li=a['fi'],a['li']
        pe=W[fi-1]['e'] if fi>0 else None; ns=W[li+1]['s'] if li+1<len(W) else None
        on,cg=onset_at(W[fi]['s'],pe); te,why=trueend_at(W[li]['s'],W[li]['e'],ns)
        words=[dict(w=w['w'],s=w['s'],e=w['e']) for w in W[fi:li+1]]
        M.append(dict(L,on=on,contig=cg,te=te,te_why=why,words=words))
    # blocks: consecutive lines contiguous in source
    for k,m in enumerate(M):
        m['same_block']= k>0 and 0<m['on']-M[k-1]['te']<1.2
    # build pieces
    pieces=[]
    for k,m in enumerate(M):
        segs=[]; t0=m['on']; 
        cuts=pauses(m['on'],m['te'])
        cur=m['on']
        for q0,q1 in cuts:
            segs.append((cur,q0+0.06)); cur=q1-0.06
        segs.append((cur,m['te']))
        for j,(s0,s1) in enumerate(segs):
            pieces.append(dict(line=m['id'],src0=s0,src1=s1,first=(j==0),last=(j==len(segs)-1),contig=m['contig'] and j==0))
    # timeline placement: joins measured loud-to-loud (>= -35 dB) so no join holds more than ~120ms of quiet
    def first_loud(t0,t1):
        for i in range(I(t0),I(t1)):
            if db[i]>=-35: return i/100
        return t0
    def last_loud(t0,t1):
        for i in range(I(t1)-1,I(t0),-1):
            if db[i]>=-35: return (i+1)/100
        return t1
    tl=[]
    for p_i,p in enumerate(pieces):
        m=[x for x in M if x['id']==p['line']][0]
        p['fl']=first_loud(p['src0'],p['src1']); p['ll']=last_loud(p['src0'],p['src1'])
        if p_i==0:
            p['a_in']=p['src0']-0.04; off=0.04-p['src0']
        else:
            prev=tl[-1]
            if p['first'] and m['same_block']:
                nat=p['fl']-prev['ll']; gap=nat if nat<=0.15 else 0.12
            else:
                gap=0.12
            off=prev['ll']+prev['off']+gap-p['fl']
            if p['first'] and not (p['contig'] or m['same_block']):
                p['a_in']=max(p['src0']-0.04, p['src0']-(p['fl']-p['src0'])) if False else p['src0']-0.04
            else:
                p['a_in']=p['src0']
        off=round(off*FPS)/FPS; p['off']=off
        p['T_on']=p['src0']+off; p['T_in']=p['a_in']+off; p['T_end']=p['src1']+off
        p['T_fl']=p['fl']+off; p['T_ll']=p['ll']+off
        tl.append(p)
    END=tl[-1]['T_end']+0.17; END=np.ceil(END*FPS)/FPS
    # audio render
    N=int(round(END*SR)); out=np.zeros((N,2),np.float32)
    for k,p in enumerate(tl):
        nxt=tl[k+1] if k+1<len(tl) else None
        fade=0.17 if nxt is None else max(0.012,min(0.17,nxt['T_fl']-p['T_end']))
        if nxt is not None and (nxt['contig'] or not nxt['first'] or [x for x in M if x['id']==nxt['line']][0]['same_block']) and nxt['T_on']-p['T_end']<0.02:
            fade=0.012
        s0=p['a_in']; s1=p['src1']+fade
        seg=X[int(round(s0*SR)):int(round(s1*SR))].copy()
        n=len(seg); env=np.ones(n,np.float32)
        fi=int((0.012 if (p['contig'] or not p['first']) else 0.006)*SR); env[:fi]=np.linspace(0,1,fi)
        fo=int(fade*SR); env[n-fo:]*=np.cos(np.linspace(0,np.pi/2,fo))**2
        seg*=env[:,None]; i0=int(round(p['T_in']*SR)); i1=min(N,i0+n)
        out[i0:i1]+=seg[:i1-i0]
    os.makedirs(sk,exist_ok=True)
    meter=pyln.Meter(SR); lufs=meter.integrated_loudness(out)
    gain=10**((-14-lufs)/20); outn=out*gain
    pk=np.abs(outn).max()
    sf.write(f'{sk}/voice.wav',outn,SR,subtype='PCM_24')
    # picture EDL: each piece holds from its cut (T_in+0.05, or exact join for internal/contig) to next cut
    cutsT=[]
    for k,p in enumerate(tl):
        if k==0: c=0.0
        elif p['first'] and not p['contig']: c=p['T_in']+0.05
        else: c=p['T_on']
        cutsT.append(round(c*FPS)/FPS)
    for k,p in enumerate(tl):
        p['pic0']=cutsT[k]; p['pic1']=cutsT[k+1] if k+1<len(tl) else END
    # timeline words
    TW=[]
    for m in M:
        for w in m['words']:
            p=[p for p in tl if p['line']==m['id'] and p['src0']-0.08<=w['s']<=p['src1']+0.05]
            p=p[0] if p else min([p for p in tl if p['line']==m['id']],key=lambda p:abs(p['src0']-w['s']))
            TW.append(dict(w=w['w'],line=m['id'],s=round(max(w['s'],p['src0'])+p['off'],3),e=round(min(w['e'],p['src1']+0.05)+p['off'],3),src_s=w['s']))
    # layout segments + runs
    segs=[]
    for m in M:
        ps=[p for p in tl if p['line']==m['id']]
        t0=ps[0]['pic0']; t1=ps[-1]['pic1']; cur=m['layout']; pts=[]
        for sw in m.get('switches',[]):
            w=min(m['words'],key=lambda w:abs(w['s']-sw['t']))
            p=[p for p in ps if p['src0']-0.08<=w['s']<=p['src1']] or ps
            Tsw=round((max(w['s'],p[0]['src0'])+p[0]['off'])*FPS)/FPS
            pts.append((Tsw,sw['layout'],w['w']))
        for Tsw,lay,ww in pts:
            segs.append(dict(T0=t0,T1=Tsw,layout=cur,line=m['id'])); t0=Tsw; cur=lay
        segs.append(dict(T0=t0,T1=t1,layout=cur,line=m['id']))
    runs=[]
    for s_ in segs:
        if s_['T1']-s_['T0']<1e-6: continue
        if runs and runs[-1]['layout']==s_['layout']:
            runs[-1]['T1']=s_['T1']; runs[-1]['lines'].append(s_['line'])
        else: runs.append(dict(T0=s_['T0'],T1=s_['T1'],layout=s_['layout'],lines=[s_['line']]))
    for i,r in enumerate(runs):
        r['i']=i; r['dur']=round(r['T1']-r['T0'],3)
        r['text']=' '.join(w['w'] for w in TW if r['T0']-0.03<=w['s']<r['T1']-0.03)
    res[sk]=dict(runs=runs,segs=segs,END=END,lufs_before=lufs,gain_db=20*np.log10(gain),peak_after=float(20*np.log10(pk)),lines=M,pieces=tl,words=TW)
    print(f'== {sk} END={END:.3f}s lufs={lufs:.1f} gain={20*np.log10(gain):+.1f}dB peak={20*np.log10(pk):.1f}dBFS')
    for r in runs: print(f"  RUN{r['i']:02d} {r['layout']:5s} {r['T0']:7.3f}-{r['T1']:7.3f} ({r['dur']:.2f}s) {r['text']}")
    for p in tl: print(f"  {p['line']} src {p['src0']:.2f}-{p['src1']:.2f} -> T {p['T_on']:.3f}-{p['T_end']:.3f} pic {p['pic0']:.3f}-{p['pic1']:.3f} {'contig' if p['contig'] else ''}{'' if p['first'] else ' (internal)'}")
json.dump(res,open('cut.json','w'),indent=1,default=float)
