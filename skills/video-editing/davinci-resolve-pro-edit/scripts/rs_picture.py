# Run INSIDE Resolve with script_plugin run_inline (pipeline.md section 9):
#   W = r'<work dir>'; M = r'<media dir>'; TL = '<timeline>'
#   exec(open(W + r'\scripts\rs_picture.py').read())
# Renders the delivery picture of timeline TL to <M>/_deliver/picture.mp4 with the user's own export preset, Resolve's
# built-in "YouTube - 2160p" (3840x2160 at the timeline frame rate, MP4, H.264 High, quality Auto, AAC, Normalize Audio
# off): the user's 4K60 uploads come out at ~11 Mb/s, ~2 GB for 25 minutes. Only the range, folder and name are changed. The
# first delivery (last-call) used H.264 "automatic" at 97 Mb/s - 18 GB, which took "an incredibly long time to upload".
# Its audio is Resolve's mix and is replaced by master.py deliver, which prints the real bitrate and size. Each
# setting is set on its own so a rejected key is named (SetRenderSettings returns False for the whole dict when one key
# fails). A 25-minute 4K60 timeline took 6.5 min on an RTX 5090. Restores the current timeline.
import time, os
OUT = os.path.join(M, '_deliver'); os.makedirs(OUT, exist_ok=True)
PRESET = globals().get('PRESET', 'YouTube - 2160p')
byname = {project.GetTimelineByIndex(i).GetName(): project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)}
tl = byname[TL]; prev = project.GetCurrentTimeline()
project.SetCurrentTimeline(tl)
ok = project.LoadRenderPreset(PRESET)
print('preset', PRESET, ok, project.GetCurrentRenderFormatAndCodec())
rs = {'SelectAllFrames': True, 'TargetDir': OUT, 'CustomName': 'picture', 'ExportVideo': True, 'ExportAudio': True}
if not ok:                                       # the preset is missing: the same settings by hand
    print('format', project.SetCurrentRenderFormatAndCodec('mp4', 'H264'))
    rs.update({'FormatWidth': int(tl.GetSetting('timelineResolutionWidth') or 3840),
               'FormatHeight': int(tl.GetSetting('timelineResolutionHeight') or 2160)})
bad = [k for k, v in rs.items() if not project.SetRenderSettings({k: v})]
print('render settings rejected:', bad or 'none')
job = project.AddRenderJob(); project.StartRendering([job], False); t0 = time.time()
while time.time() - t0 < 3500:
    st = project.GetRenderJobStatus(job)
    if st.get('JobStatus') in ('Complete', 'Failed', 'Cancelled'): break
    time.sleep(5)
print('picture', st.get('JobStatus'), round(time.time() - t0, 1), 's ->', os.path.join(OUT, 'picture.mp4'))
project.DeleteRenderJob(job)
project.SetCurrentTimeline(prev)
