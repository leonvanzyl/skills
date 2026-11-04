# Run INSIDE Resolve with script_plugin run_inline (read-only; doesn't change the current timeline):
#   W = r'<work dir>'; M = r'<media dir>'; TL = '<timeline>'; NAME = 'items'
#   exec(open(W + r'\scripts\rs_items.py').read())
# Writes <M>/_deliver/NAME.json: the timeline's fps and length, every audio track (name, enabled) and every audio item
# (track, file, timeline start and duration in frames, source in-point, clip volume, enabled) - what master.py needs to
# rebuild a track sample-accurately from its files (`layers`) or to compare a stem with its raw media (`chain`).
import json, os
byname = {project.GetTimelineByIndex(i).GetName(): project.GetTimelineByIndex(i) for i in range(1, project.GetTimelineCount() + 1)}
tl = byname[TL]; S0 = tl.GetStartFrame()
fps = float(tl.GetSetting('timelineFrameRate') or project.GetSetting('timelineFrameRate'))
tracks, rows = {}, []
for k in range(1, tl.GetTrackCount('audio') + 1):
    tracks[k] = dict(name=tl.GetTrackName('audio', k), enabled=bool(tl.GetIsTrackEnabled('audio', k)),
                     type=tl.GetTrackSubType('audio', k))
    for it in tl.GetItemListInTrack('audio', k) or []:
        mpi = it.GetMediaPoolItem()
        rows.append(dict(track=k, name=it.GetName(), path=mpi.GetClipProperty('File Path') if mpi else None,
                         start=it.GetStart() - S0, dur=it.GetDuration(), left=it.GetLeftOffset(),
                         src_time=it.GetSourceStartTime() if hasattr(it, 'GetSourceStartTime') else None,
                         vol=it.GetProperty('AudioVolume'), enabled=bool(it.GetClipEnabled())))
os.makedirs(os.path.join(M, '_deliver'), exist_ok=True)
json.dump(dict(timeline=TL, fps=fps, end=tl.GetEndFrame() - S0, tracks=tracks, items=rows),
          open(os.path.join(M, '_deliver', NAME + '.json'), 'w'), indent=1)
print(TL, '|', len(rows), 'audio items on', len(tracks), 'tracks', [(k, t['name']) for k, t in tracks.items()],
      '| fps', fps, '| end', tl.GetEndFrame() - S0)
