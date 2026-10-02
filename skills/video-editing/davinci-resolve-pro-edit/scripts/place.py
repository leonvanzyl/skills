"""Turn the plan and the renders into exact Resolve placements, in two steps.

1) python scripts/place.py plan --video-tracks 1 --audio-tracks 2
     --video-tracks / --audio-tracks: how many tracks the DUPLICATED timeline already has (probe it). The edit's own
     tracks go above them: V+1 "PE Graphics" (opaque V2-style clips), V+2 "PE Overlays" (alpha), V+3 "PE Censor"
     (alpha blur over sensitive UI, always topmost), A+1 "PE SFX",
     A+2 "PE Music", A+3 "PE Riser". Writes placement.json: the tracks to add, the files to import, every clip with
     its record frame, the punch-in transforms for V1 items and the markers.
2) python scripts/place.py ids <import_result.json> [--existing-markers <get_all.json>]
     after media_pool safe_import_media: maps each file to its media_pool_item_id and writes
       append_clip_infos.json   -> media_pool append_to_timeline {clip_infos: <this>}   (one call)
       bulk_ops.json            -> timeline bulk_set_item_properties {ops: <this>}     (punch-ins; not archived)
       markers_add.json         -> one timeline_markers add per entry (nudged off frames that already have a marker:
                                   Resolve keeps one marker per frame, and a duplicated clean cut brings its own)
3) python scripts/place.py verify <built_structure.json> <clean_cut_structure.json>
     after the build: every planned clip at its exact track/frame/length, and the clean cut's own tracks untouched.
Record frames are relative to the timeline start (the MCP's default), end frames are exclusive."""
import sys, os, json
sys.path.insert(0, 'scripts'); import config as C, media as M

ROLES_V = [('graphics', 'PE Graphics'), ('overlays', 'PE Overlays'), ('censor', 'PE Censor')]   # censor: always on top
ROLES_A = [('sfx', 'PE SFX'), ('music', 'PE Music'), ('riser', 'PE Riser')]


def punch_transform(it, face, z, src_w, src_h):
    """static punch-in on a camera item: keep the face's x, put the eyes on ~36% of the height, never show an edge.
    Resolve: zoom about the frame centre, Pan +right, Tilt +up, in timeline pixels."""
    s = C.TW / src_w
    fx = (face[0] + face[2] / 2) * s; ey = (face[1] + face[3] * 0.32) * s          # eyes sit ~32% down a YuNet box
    cx, cy = C.TW / 2, C.TH / 2
    pan = (1 - z) * (fx - cx)
    tilt = cy + z * (ey - cy) - C.TH * 0.36
    mx, my = (z - 1) * C.TW / 2, (z - 1) * C.TH / 2
    return dict(ZoomX=round(z, 4), ZoomY=round(z, 4), Pan=round(max(-mx, min(mx, pan)), 1), Tilt=round(max(-my, min(my, tilt)), 1))


def plan(nv, na):
    P = M.program(); PL = M.plan(); fps = C.FPS
    S = json.load(open('scenes.json')) if os.path.exists('scenes.json') else {'items': {}}
    vt = {r: nv + 1 + k for k, (r, _) in enumerate(ROLES_V)}
    at = {r: na + 1 + k for k, (r, _) in enumerate(ROLES_A)}
    clips, punches, missing = [], [], []
    for b in PL['beats']:
        if b['kind'] == 'punch':
            for v1 in b['items']:
                it = next(i for i in P['items'] if i['v1'] == v1)
                face = S['items'].get(str(v1), {}).get('face')
                if not face: missing.append(f"{b['id']}: V1 item {v1} has no measured face (scenes.json) - not a camera shot?"); continue
                p = M.probe(it['file'])
                punches.append(dict(beat=b['id'], item_index=v1, transform=punch_transform(it, face, b.get('zoom', 1.15), p['width'], p['height'])))
            continue
        ext = '.mov' if b['kind'] in ('words', 'cta', 'censor') else '.mp4'
        role = 'censor' if b['kind'] == 'censor' else 'overlays' if ext == '.mov' else 'graphics'
        f = os.path.abspath(os.path.join(C.MEDIA, b['id'] + ext))
        if not os.path.exists(f): missing.append(f"{b['id']}: {f} not rendered"); continue
        f0, f1 = M.frames_of(b['t0'], b['t1'])
        clips.append(dict(beat=b['id'], role=role, file=f, media_type=1,
                          track_index=vt[role], record_frame=f0, start_frame=0, end_frame=f1 - f0))
    A = json.load(open('audio_clips.json')) if os.path.exists('audio_clips.json') else {'clips': []}
    for c in A['clips']:
        clips.append(dict(beat=c.get('src', c['track']), role=c['track'], file=c['file'], media_type=2, track_index=at[c['track']],
                          record_frame=c['record_frame'], start_frame=c['start_frame'], end_frame=c['end_frame']))
    # a clip may not overlap another on the same track (Resolve silently drops the later one)
    for role in {c['role'] for c in clips}:
        cs = sorted([c for c in clips if c['role'] == role], key=lambda c: c['record_frame'])
        for a, b in zip(cs, cs[1:]):
            if a['record_frame'] + a['end_frame'] - a['start_frame'] > b['record_frame']:
                missing.append(f"overlap on {role}: {a['beat']} runs into {b['beat']} - shorten one")
    markers = [dict(frame=int(round(ch['t'] * fps)), color='Blue', name=ch['title'], note='Chapter', duration=1) for ch in PL.get('chapters', [])]
    if PL.get('hook_end'):
        markers.append(dict(frame=int(round(PL['hook_end'] * fps)), color='Yellow', name='Listen: hook -> content',
                            note='The riser lands here and the hook music fades out over the next few seconds.', duration=1))
    markers = nudge(markers)
    out = dict(source_timeline=PL.get('source_timeline'), new_timeline=PL.get('new_timeline'),
               tracks=dict(video=[dict(index=vt[r], name=n) for r, n in ROLES_V if r != 'censor' or any(c['role'] == 'censor' for c in clips)], audio=[dict(index=at[r], name=n, audio_type='stereo') for r, n in ROLES_A]),
               import_files=sorted({c['file'] for c in clips}), clips=clips, punches=punches, markers=markers, problems=missing)
    json.dump(out, open('placement.json', 'w'), indent=1)
    print(f"placement.json: {len(clips)} clips ({sum(c['media_type'] == 1 for c in clips)} video, {sum(c['media_type'] == 2 for c in clips)} audio), "
          f"{len(punches)} punch-ins, {len(markers)} markers, {len(out['import_files'])} files to import")
    print('tracks to add:', [(t['index'], t['name']) for t in out['tracks']['video']], [(t['index'], t['name']) for t in out['tracks']['audio']])
    for m in missing: print('  PROBLEM', m)


def nudge(markers, taken=()):
    """Resolve keeps one marker per frame: move each marker to the next free frame"""
    used = set(int(f) for f in taken)
    for m in sorted(markers, key=lambda m: m['frame']):
        while m['frame'] in used: m['frame'] += 1
        used.add(m['frame'])
    return markers


def ids(result_path, existing=None):
    R = json.load(open(result_path, encoding='utf-8'))
    R = R.get('result', R)
    by = {}
    for c in R.get('clips', []):
        by[os.path.normcase(os.path.abspath(c.get('file_path') or ''))] = c['id']
        by[os.path.basename(c.get('file_path') or c.get('name', '')).lower()] = c['id']
    PLC = json.load(open('placement.json'))
    infos, lost = [], []
    for c in PLC['clips']:
        mid = by.get(os.path.normcase(os.path.abspath(c['file']))) or by.get(os.path.basename(c['file']).lower())
        if not mid: lost.append(c['file']); continue
        infos.append(dict(media_pool_item_id=mid, start_frame=c['start_frame'], end_frame=c['end_frame'],
                          record_frame=c['record_frame'], track_index=c['track_index'], media_type=c['media_type']))
    json.dump(infos, open('append_clip_infos.json', 'w'), indent=1)
    ops = [dict(timeline_item=dict(track_type='video', track_index=1, item_index=p['item_index']), transform=p['transform']) for p in PLC['punches']]
    json.dump(ops, open('bulk_ops.json', 'w'), indent=1)
    taken = []
    if existing:                                   # timeline_markers get_all, saved: {"markers": {"<frame>": {...}}}
        E = json.load(open(existing, encoding='utf-8')); E = E.get('result', E); taken = list(E.get('markers', E).keys())
    json.dump(nudge(PLC['markers'], taken), open('markers_add.json', 'w'), indent=1)
    print(f'append_clip_infos.json: {len(infos)} clips | bulk_ops.json: {len(ops)} punch-ins | markers_add.json: {len(PLC["markers"])}')
    for f in lost: print('  NOT IMPORTED', f)


def verify(built_path, source_path):
    """compare the built pro-edit timeline with the plan and with the clean cut it was duplicated from"""
    def load(p):
        d = json.load(open(p, encoding='utf-8')); return d.get('result', d)
    B, S = load(built_path), load(source_path)
    tracks = lambda st, kind: {t['track_index']: t['items'] for t in st['tracks'][kind]['tracks']}
    bad = []
    for kind in ('video', 'audio'):                     # the clean cut's own tracks must be untouched (bar punch-ins)
        bt, st = tracks(B, kind), tracks(S, kind)
        for ti, items in st.items():
            got = bt.get(ti, [])
            key = lambda x: (x['start'], x['end'], x.get('source_start'), x.get('media_pool_item_id'))
            if [key(x) for x in got] != [key(x) for x in items]:
                bad.append(f'{kind} track {ti} differs from the clean cut ({len(got)} vs {len(items)} items)')
    PLC = json.load(open('placement.json')); start = B.get('start_frame') or 0
    names = {os.path.basename(c['file']) for c in PLC['clips']}
    placed = {}
    for kind in ('video', 'audio'):
        for ti, items in tracks(B, kind).items():
            for x in items:
                if x.get('name') in names or os.path.basename(x.get('file_path') or '') in names:
                    placed.setdefault((kind, ti), []).append((x['start'] - start, x['end'] - x['start'], os.path.basename(x.get('file_path') or x['name'])))
    ok = 0
    for c in PLC['clips']:
        kind = 'video' if c['media_type'] == 1 else 'audio'
        want = (c['record_frame'], c['end_frame'] - c['start_frame'], os.path.basename(c['file']))
        if want in placed.get((kind, c['track_index']), []): ok += 1
        else: bad.append(f"{c['beat']} ({os.path.basename(c['file'])}) not at {kind} {c['track_index']} frame {c['record_frame']} for {want[1]} frames")
    print(f"{ok}/{len(PLC['clips'])} clips exactly where planned | clean-cut tracks {'untouched' if not any('differs' in b for b in bad) else 'CHANGED'}")
    for b in bad: print('  PROBLEM', b)


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[0] == 'plan':
        nv = int(a[a.index('--video-tracks') + 1]) if '--video-tracks' in a else 1
        na = int(a[a.index('--audio-tracks') + 1]) if '--audio-tracks' in a else 1
        plan(nv, na)
    elif a[0] == 'verify':
        verify(a[1], a[2])
    else:
        ids(a[1], a[a.index('--existing-markers') + 1] if '--existing-markers' in a else None)
