# Run INSIDE Resolve with script_plugin run_inline (pipeline.md section 9):
#   W = r'<work dir>'; M = r'<media dir>'; TL = '<timeline>'; NAME = 'stem_base'; KEEP = 'base'; RANGE = None
#   exec(open(W + r'\scripts\rs_stem.py').read())
# Renders the audio of timeline TL to <M>/_deliver/NAME.wav (24-bit 48 kHz, the "Audio Only" preset) with only the
# KEEP tracks playing:
#   'base' - every audio track whose name doesn't start with "PE " (the user's own tracks: the voice through their
#            track effects, faders and bus) - the stem master.py builds the final mix on;
#   'all'  - the mix exactly as Resolve plays it (master.py fit);
#   [1]    - a list of track numbers (master.py chain: A1 alone).
# RANGE = (in, out) in timeline frames from the start; None = the whole timeline.
# Audio track enables are ignored by renders (Resolve 21.1: SetTrackEnable('audio', ...) changes nothing), so the
# other tracks' CLIPS are disabled for the render and re-enabled afterwards. Restores the current timeline.
# Leaves the user's timeline as it found it, even after an interrupted run (opencode-2.0, 2026-10-19: a killed run left
# 58 SFX clips disabled and a render range rendered into the timeline as an In/Out mark - "this little grey bar"):
#   - the clips it disables are listed in <M>/_deliver/_rs_stem_pending.json first; every run re-enables whatever an
#     earlier interrupted run left there before it starts;
#   - the timeline's own In/Out marks are read before the render and put back afterwards (a RANGE render sets them).
import time, os, json
OUT = os.path.join(M, '_deliver'); os.makedirs(OUT, exist_ok=True)
PENDING = os.path.join(OUT, '_rs_stem_pending.json')
byname = {project.GetTimelineByIndex(i).GetName(): project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)}


def _items(t):
    return [it for k in range(1, t.GetTrackCount('audio') + 1) for it in (t.GetItemListInTrack('audio', k) or [])]


if os.path.exists(PENDING):                                   # an earlier run was interrupted: undo what it disabled
    left = json.load(open(PENDING))
    for tname, ids in left.items():
        if tname in byname:
            want = set(ids)
            print('recovered an interrupted run on', tname, '| re-enabled',
                  sum(bool(it.SetClipEnabled(True)) for it in _items(byname[tname]) if it.GetUniqueId() in want), 'of', len(ids))
    os.remove(PENDING)

tl = byname[TL]; prev = project.GetCurrentTimeline()
project.SetCurrentTimeline(tl)
marks = tl.GetMarkInOut() or {}
n = tl.GetTrackCount('audio')
names = {k: tl.GetTrackName('audio', k) for k in range(1, n + 1)}
keep = ([k for k in names if not names[k].startswith('PE ')] if KEEP == 'base' else
        list(names) if KEEP == 'all' else list(KEEP))
off = [it for k in names if k not in keep for it in (tl.GetItemListInTrack('audio', k) or []) if it.GetClipEnabled()]
json.dump({TL: [it.GetUniqueId() for it in off]}, open(PENDING, 'w'))
print('playing', [(k, names[k]) for k in keep], '| disabled', sum(bool(it.SetClipEnabled(False)) for it in off),
      'of', len(off), 'clips on the other tracks')
try:
    print('preset', project.LoadRenderPreset('Audio Only'))
    R = globals().get('RANGE'); S0 = tl.GetStartFrame()
    rs = {'TargetDir': OUT, 'CustomName': NAME, 'ExportVideo': False, 'ExportAudio': True, 'AudioSampleRate': 48000,
          'AudioBitDepth': 24}
    rs.update({'SelectAllFrames': False, 'MarkIn': S0 + R[0], 'MarkOut': S0 + R[1] - 1} if R else {'SelectAllFrames': True})
    bad = [k for k, v in rs.items() if not project.SetRenderSettings({k: v})]
    if bad: print('render settings rejected:', bad)
    job = project.AddRenderJob(); project.StartRendering([job], False); t0 = time.time()
    while time.time() - t0 < 1500:
        st = project.GetRenderJobStatus(job)
        if st.get('JobStatus') in ('Complete', 'Failed', 'Cancelled'): break
        time.sleep(2)
    print(NAME, st.get('JobStatus'), round(time.time() - t0, 1), 's ->', os.path.join(OUT, NAME + '.wav'))
    project.DeleteRenderJob(job)
finally:
    print('re-enabled', sum(bool(it.SetClipEnabled(True)) for it in off), 'of', len(off),
          '| still disabled:', sum(not it.GetClipEnabled() for it in off))
    if not any(it.GetClipEnabled() is False for it in off) and os.path.exists(PENDING):
        os.remove(PENDING)
    for _ in range(5):                                        # put the user's own marks back (none -> none); Resolve
        tl.ClearMarkInOut('all')                              # can re-set the render range just after the job ends
        for typ in ('video', 'audio'):                        # (blotato, 2026-10-22: 'out' 5223 survived one clear)
            m = marks.get(typ) or {}
            if 'in' in m and 'out' in m: tl.SetMarkInOut(m['in'], m['out'], typ)
        time.sleep(1.0)
        if (tl.GetMarkInOut() or {}) == marks or all(not v for v in (tl.GetMarkInOut() or {}).values()) and not any(marks.values()):
            break
    print('marks', tl.GetMarkInOut(), '(before:', marks, ')')
    project.SetCurrentTimeline(prev)
