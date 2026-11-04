# Run INSIDE Resolve with script_plugin run_inline (pipeline.md section 11, the dynamic camera):
#   W = r'<work dir>'; M = r'<media dir>'; TL = '<pro edit>'; NEW = '<pro edit> - Dynamic Camera'
#   LAYER = 'layout_v1.mp4'                     # dyncam.py's output, in M
#   OVERLAYS = ['PE Overlays']                  # optional: the tracks whose clips must stay above the camera
#   exec(open(W + r'\scripts\rs_layout.py').read())
# Builds NEW as a duplicate of TL - the audio, the user's voice chain and every track come with it - with two tracks
# on top: "PE Layout" (the camera layer) and "PE Overlays (top)" (the OVERLAYS tracks' clips re-placed above it:
# keyword pops, CTA cards). Every video track below "PE Layout" is disabled but kept, so the static version is one
# toggle away. Run it again with a new LAYER (a fix re-rendered under a new --tag: Resolve holds imported files open)
# to swap the layer clip in place. TL itself is never touched and NEW is never rebuilt (proven live on abacus-test: a
# test timeline built from Pro Edit v1 rendered pixel-identical to Pro Edit v3). Every appended clip's length is
# checked: endFrame is exclusive on 21.1.1.10, re-calibrated on the first append in case a build differs. Track
# enables are read and set with NEW current (they follow the current timeline). Leaves NEW as the current timeline.
import os
OVERLAYS = globals().get('OVERLAYS', ['PE Overlays'])
byname = {project.GetTimelineByIndex(i).GetName(): project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)}
if NEW in byname: tl = byname[NEW]; fresh = False
else: project.SetCurrentTimeline(byname[TL]); tl = byname[TL].DuplicateTimeline(NEW); fresh = True
project.SetCurrentTimeline(tl); S0 = tl.GetStartFrame(); END = tl.GetEndFrame() - S0
names = {k: tl.GetTrackName('video', k) for k in range(1, tl.GetTrackCount('video') + 1)}
L = next((k for k, n in names.items() if n == 'PE Layout'), None)
if L is None:
    tl.AddTrack('video'); L = tl.GetTrackCount('video'); tl.SetTrackName('video', L, 'PE Layout')
    tl.AddTrack('video'); tl.SetTrackName('video', L + 1, 'PE Overlays (top)')
O = next(k for k in range(1, tl.GetTrackCount('video') + 1) if tl.GetTrackName('video', k) == 'PE Overlays (top)')
print('timeline', NEW, '(new)' if fresh else '(existing)', '| PE Layout = V%d, PE Overlays (top) = V%d' % (L, O))

root = mp.GetRootFolder()
pe = next((f for f in root.GetSubFolderList() if f.GetName() == 'Pro Edit'), None) or mp.AddSubFolder(root, 'Pro Edit')
b = next((f for f in pe.GetSubFolderList() if f.GetName() == NEW), None) or mp.AddSubFolder(pe, NEW)
mp.SetCurrentFolder(b)
lname = os.path.basename(LAYER)
if not any(c.GetName() == lname for c in b.GetClipList()): mp.ImportMedia([os.path.join(M, lname)])
lay = next(c for c in b.GetClipList() if c.GetName() == lname)
nfr = int(lay.GetClipProperty('Frames'))
print('layer', lname, lay.GetClipProperty('FPS'), 'fps', nfr, 'frames | timeline', END, 'frames', '' if nfr == END else '<- LENGTH MISMATCH')

EXCL = [True]
def append(mpi, s0, n, rec, track):
    """n source frames from s0, at record frame rec (from the timeline start); the new item, its length checked"""
    for attempt in range(2):
        r = mp.AppendToTimeline([{'mediaPoolItem': mpi, 'startFrame': s0, 'endFrame': s0 + n if EXCL[0] else s0 + n - 1,
                                  'recordFrame': S0 + rec, 'trackIndex': track, 'mediaType': 1}])
        it = r[0] if r else None
        if it is None or it.GetDuration() == n: return it
        if attempt == 0 and EXCL[0] and it.GetDuration() == n + 1:   # the API took endFrame as inclusive
            tl.DeleteClips([it], False); EXCL[0] = False; continue
        print('  length', it.GetDuration(), '!=', n, 'at', rec); return it


old = [it for it in (tl.GetItemListInTrack('video', L) or []) if it.GetName() != lname]
if old: print('removed the old layer', [it.GetName() for it in old], tl.DeleteClips(old, False))
if not tl.GetItemListInTrack('video', L):
    it = append(lay, 0, nfr, 0, L); print('layer placed:', bool(it), it.GetStart() - S0 if it else None, it.GetDuration() if it else None)

if not tl.GetItemListInTrack('video', O):
    src_tracks = [k for k in range(1, L) if tl.GetTrackName('video', k) in OVERLAYS]
    n_ok = n_all = 0
    for k in src_tracks:
        for it in tl.GetItemListInTrack('video', k) or []:
            mpi = it.GetMediaPoolItem(); n_all += 1
            if not mpi: print('  skipped (no media):', it.GetName()); continue
            try: s0 = it.GetSourceStartFrame()
            except Exception: s0 = it.GetLeftOffset()
            new = append(mpi, s0, it.GetDuration(), it.GetStart() - S0, O)
            if new is None: print('  NOT placed:', it.GetName(), it.GetStart() - S0); continue
            for p in ('ZoomX', 'ZoomY', 'Pan', 'Tilt', 'Opacity'):
                v = it.GetProperty(p)
                if v is not None and v != new.GetProperty(p): new.SetProperty(p, v)
            if not it.GetClipEnabled(): new.SetClipEnabled(False)
            n_ok += new.GetDuration() == it.GetDuration()
    print('overlays re-placed above the layer:', n_ok, 'of', n_all, 'from', [tl.GetTrackName('video', k) for k in src_tracks])

for k in range(1, L): tl.SetTrackEnable('video', k, False)
for k in range(1, tl.GetTrackCount('video') + 1):
    print('V%d' % k, tl.GetTrackName('video', k), 'on' if tl.GetIsTrackEnabled('video', k) else 'off', len(tl.GetItemListInTrack('video', k) or []))
resolve.GetProjectManager().SaveProject(); print('saved; current timeline:', tl.GetName())
