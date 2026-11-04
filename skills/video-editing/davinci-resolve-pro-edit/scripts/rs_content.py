# Run INSIDE Resolve with script_plugin run_inline (pipeline.md section 11, the dynamic camera):
#   W = r'<work dir>'; M = r'<media dir>'; TL = '<pro edit>'
#   HIDE = ['Camera', 'Facecam', 'PE Facecam', 'PE Overlays']   # optional: the tracks left out of the content layer
#   RENDER = True                                                 # optional: False writes tracks.json only
#   exec(open(W + r'\scripts\rs_content.py').read())
# Writes <M>/_deliver/tracks.json - every video track of TL (index, name, enabled) with its items (record range from
# the timeline start, file, source start, enabled, ZoomX/ZoomY/Pan/Tilt/Opacity): dyncam.py reads the punch-ins of the
# camera track from it, dyncam_plan.py the camera and graphics spans. Then renders <M>/_deliver/content.mp4: TL with
# the clips of the HIDE tracks disabled - the content the camera layer is composited over. PE Censor stays IN the
# content (its blur must move with the content into the CARD panel). The clips are re-enabled afterwards; an
# interrupted run is undone by the next one (the disabled clips are listed in _rs_content_pending.json first).
# Codec: H.264 on NVENC without the YouTube preset - ~55 Mb/s at 4K60, a good intermediate (the preset's ~11 Mb/s is
# too lossy for a file that is re-encoded twice more). VideoQuality and FrameRate keys are rejected on 21.1.1.
# A 9-minute 4K60 timeline took ~2 min on an RTX 5090. Restores the current timeline.
import time, os, json
OUT = os.path.join(M, '_deliver'); os.makedirs(OUT, exist_ok=True)
PENDING = os.path.join(OUT, '_rs_content_pending.json')
HIDE = globals().get('HIDE', ['Camera', 'Facecam', 'PE Facecam', 'PE Overlays'])
RENDER = globals().get('RENDER', True)
byname = {project.GetTimelineByIndex(i).GetName(): project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)}


def _vitems(t):
    return [it for k in range(1, t.GetTrackCount('video') + 1) for it in (t.GetItemListInTrack('video', k) or [])]


if os.path.exists(PENDING):                                   # an earlier run was interrupted: undo what it disabled
    left = json.load(open(PENDING))
    for tname, ids in left.items():
        if tname in byname:
            want = set(ids)
            print('recovered an interrupted run on', tname, '| re-enabled',
                  sum(bool(it.SetClipEnabled(True)) for it in _vitems(byname[tname]) if it.GetUniqueId() in want), 'of', len(ids))
    os.remove(PENDING)

tl = byname[TL]; prev = project.GetCurrentTimeline()
project.SetCurrentTimeline(tl); S0 = tl.GetStartFrame()
dump = {'timeline': TL, 'start_frame': S0, 'frames': tl.GetEndFrame() - S0, 'video': []}
for k in range(1, tl.GetTrackCount('video') + 1):
    items = []
    for it in tl.GetItemListInTrack('video', k) or []:
        mpi = it.GetMediaPoolItem()
        try: src0 = it.GetSourceStartFrame()
        except Exception: src0 = it.GetLeftOffset()
        d = dict(name=it.GetName(), rec0=it.GetStart() - S0, rec1=it.GetEnd() - S0, src0=src0, enabled=bool(it.GetClipEnabled()),
                 file=(mpi.GetClipProperty('File Path') if mpi else '') or '')
        for p in ('ZoomX', 'ZoomY', 'Pan', 'Tilt', 'Opacity'): d[p] = it.GetProperty(p)
        items.append(d)
    dump['video'].append(dict(index=k, name=tl.GetTrackName('video', k), enabled=bool(tl.GetIsTrackEnabled('video', k)), items=items))
json.dump(dump, open(os.path.join(OUT, 'tracks.json'), 'w'), indent=0)
print('tracks.json:', [(t['index'], t['name'], len(t['items'])) for t in dump['video']])
hide = [t['index'] for t in dump['video'] if t['name'] in HIDE]
print('left out of the content:', [(k, tl.GetTrackName('video', k)) for k in hide], '| missing names:',
      [n for n in HIDE if n not in {t['name'] for t in dump['video']}])

if RENDER:
    off = [it for k in hide for it in (tl.GetItemListInTrack('video', k) or []) if it.GetClipEnabled()]
    json.dump({TL: [it.GetUniqueId() for it in off]}, open(PENDING, 'w'))
    print('disabled', sum(bool(it.SetClipEnabled(False)) for it in off), 'of', len(off), 'clips')
    try:
        if 'H.264 Master' in (project.GetRenderPresetList() or []): project.LoadRenderPreset('H.264 Master')
        ok = project.SetCurrentRenderFormatAndCodec('mp4', 'H264_NVIDIA') or project.SetCurrentRenderFormatAndCodec('mp4', 'H264')
        print('format', ok, project.GetCurrentRenderFormatAndCodec())
        rs = {'SelectAllFrames': True, 'TargetDir': OUT, 'CustomName': 'content', 'ExportVideo': True, 'ExportAudio': False,
              'FormatWidth': int(tl.GetSetting('timelineResolutionWidth') or 3840), 'FormatHeight': int(tl.GetSetting('timelineResolutionHeight') or 2160)}
        bad = [k for k, v in rs.items() if not project.SetRenderSettings({k: v})]
        print('render settings rejected:', bad or 'none')
        job = project.AddRenderJob(); project.StartRendering([job], False); t0 = time.time()
        while time.time() - t0 < 3500:
            st = project.GetRenderJobStatus(job)
            if st.get('JobStatus') in ('Complete', 'Failed', 'Cancelled'): break
            time.sleep(3)
        print('content', st.get('JobStatus'), round(time.time() - t0, 1), 's ->', os.path.join(OUT, 'content.mp4'))
        project.DeleteRenderJob(job)
    finally:
        print('re-enabled', sum(bool(it.SetClipEnabled(True)) for it in off), 'of', len(off),
              '| still disabled:', sum(not it.GetClipEnabled() for it in off))
        if all(it.GetClipEnabled() for it in off) and os.path.exists(PENDING): os.remove(PENDING)
        resolve.GetProjectManager().SaveProject()
project.SetCurrentTimeline(prev)
