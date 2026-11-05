"""Shorts cut from a finished long-form edit made with davinci-resolve-pro-edit: reuse that run's work instead of redoing it.
  - program.json -> longform_program.json: the final video's time -> the RAW recordings (file + source frame). Graphics then
    use clean, unzoomed screen footage, never the finished render (which carries the long-form's zooms, pops and cards).
  - captures/ (index.json: what each capture shows; facts.json: the fact check) -> captures/ here. Re-verify only the
    claims the shorts actually say; no fresh research pass for the rest.
  - the logos / avatars / thumbnails it cut out (gfx/assets) -> longform_assets/
  - voice48.wav (its clean dialogue track) -> project.json clean_stem.voice, for clean_from_stem.py (pipeline.md 1b)
  - its report.md / PUBLISH.md (next to the sources in pro-edit-media/) -> project.json "longform": read the report's Audio
    section for the hook-music window (clean_stem.fit_exclude) and use the full video's LIVE title (spec 8b).
OPTIONAL. setup.sh runs it with --auto for every work folder, so a fresh session finds the long-form run without knowing
about it. With none found it says so and the shorts are made standalone, exactly as before (the research subagent, graphics
from the source video); it never fails setup.
No work folder on this machine, but the raw recordings next to the video: it says so, and build_raw_map.py (after
analyze.sh) rebuilds longform_program.json and a clean voice stem from them by audio matching (Last Call, 2026-10-19).
usage (in work-<stem>/):
  $PY scripts/import_longform.py --auto                     what setup.sh runs: import if a matching run exists, else note it
  $PY scripts/import_longform.py [<pro-edit work folder>]   found under %LOCALAPPDATA%/video-pro-edit/ when omitted
  $PY scripts/import_longform.py --at 545.2 [601 ...]       final-video time -> raw file + time, and an ffmpeg still command
  $PY scripts/import_longform.py --range 545 552            the raw pieces under a final-video stretch
Learned on Harness Engineering (2026-10-14), where this was done by hand and gave the five shorts their real footage."""
import glob, json, os, shutil, sys

HERE = os.getcwd()
CFG = 'project.json'


def load(p): return json.load(open(p, encoding='utf-8'))


def norm(p): return os.path.normcase(os.path.abspath(p))


def program():
    if not os.path.exists('longform_program.json'): sys.exit('no longform_program.json: run import_longform.py first')
    P = load('longform_program.json'); fps = P.get('fps', 60)
    return P, fps


def at(ts):
    P, fps = program()
    for t in ts:
        hit = [i for i in P['items'] if i['t0'] <= t < i['t1']]
        if not hit: print(f'{t:8.2f} s: no raw item (a gap, a title card or a generated graphic in the long-form)'); continue
        for it in hit:
            raw = (it['src0'] + (t - it['t0']) * fps) / fps
            print(f"{t:8.2f} s -> {it.get('name', os.path.basename(it['file']))} @ {raw:.3f} s   (item t {it['t0']:.2f}-{it['t1']:.2f})")
            print(f'           ffmpeg -ss {max(raw - 1, 0):.3f} -i "{it["file"]}" -ss {min(raw, 1):.3f} -frames:v 1 still.png')


def span(a, b):
    P, fps = program()
    for k, it in enumerate(P['items']):
        if it['t1'] > a and it['t0'] < b:
            t0, t1 = max(a, it['t0']), min(b, it['t1'])
            r0 = (it['src0'] + (t0 - it['t0']) * fps) / fps; r1 = (it['src0'] + (t1 - it['t0']) * fps) / fps
            print(f"item {k:3d}: final {t0:8.2f}-{t1:8.2f} s -> {it.get('name', os.path.basename(it['file']))} {r0:.3f}-{r1:.3f} s")


def find_work(cfg, auto=False):
    src = os.path.join(HERE, cfg['source'])
    dirs = {norm(os.path.dirname(src)), norm(os.path.join(os.path.dirname(src), '..'))}
    base = os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~/AppData/Local')), 'video-pro-edit')
    hits = []
    for pj in glob.glob(os.path.join(base, '*', 'program.json')):
        try: files = {norm(os.path.dirname(i['file'])) for i in load(pj)['items']}
        except Exception: continue
        if files & dirs: hits.append(os.path.dirname(pj))
    if not hits:
        if auto: return None
        sys.exit(f'no davinci-resolve-pro-edit work folder under {base} uses recordings from {sorted(dirs)}; pass its path')
    hits.sort(key=lambda d: os.path.getmtime(os.path.join(d, 'program.json')), reverse=True)
    if len(hits) > 1: print('several pro-edit runs use these recordings; taking the newest:', *hits, sep='\n  ')
    return hits[0]


VIDEO_EXT = ('.mov', '.mp4', '.mkv', '.m4v', '.mxf')


def raw_recordings(cfg):
    """the other videos next to the source: the long-form edit's raw recordings when its pro-edit work folder is gone
    (build_raw_map.py). In the single-file form (the source hard-linked into <folder>/shorts/) that is <folder>; never the
    source itself or its copy."""
    src = os.path.abspath(os.path.join(HERE, cfg['source'])); d = os.path.dirname(src)
    size = os.path.getsize(src) if os.path.exists(src) else -1
    dirs = [d, os.path.dirname(d)] if os.path.basename(d).lower() == 'shorts' else [d]
    out = []
    for dd in dirs:
        for f in sorted(os.listdir(dd)):
            p = os.path.join(dd, f)
            if os.path.isfile(p) and f.lower().endswith(VIDEO_EXT) and not (f == os.path.basename(src) and os.path.getsize(p) == size):
                out.append(p)
    return out


def media_folder(cfg):
    src_dir = os.path.dirname(os.path.join(HERE, cfg['source']))
    for d in (src_dir, os.path.join(src_dir, '..')):
        m = os.path.join(d, 'pro-edit-media')
        if os.path.isdir(m): return os.path.abspath(m)
    return None


def fwd(p): return os.path.abspath(p).replace('\\', '/')


def main(work, auto=False):
    cfg = load(CFG)
    W = work or find_work(cfg, auto)
    m = media_folder(cfg)
    if W is None:
        if m:   # the long-form was edited elsewhere (another machine): only its report and publishing copy are here
            cfg['longform'] = {'report': fwd(os.path.join(m, 'report.md')), 'publish': fwd(os.path.join(m, 'PUBLISH.md'))}
            json.dump(cfg, open(CFG, 'w', encoding='utf-8'), indent=1)
            print(f'long-form: no pro-edit work folder on this machine, but its report and publishing copy are in {m}: read the',
                  'report (fact check, music and SFX windows); everything else is made standalone')
        else:
            print('long-form: no davinci-resolve-pro-edit run found for this video - the shorts are made standalone')
        raws = raw_recordings(cfg)
        single = os.path.basename(os.path.dirname(os.path.abspath(os.path.join(HERE, cfg['source'])))).lower() == 'shorts'
        if raws and (m or single):   # a finished edit with its raw recordings next to it: they can stand in for the work folder
            print(f'long-form: {len(raws)} other recording(s) next to the video ({", ".join(os.path.basename(r) for r in raws[:8])}).',
                  'If they are its raw recordings, run build_raw_map.py after analyze.sh: a clean voice stem and the',
                  'final -> raw map, as if the work folder were here (pipeline.md 1c)')
        return
    print('pro-edit work folder:', W)
    shutil.copy(os.path.join(W, 'program.json'), 'longform_program.json')
    P = load('longform_program.json')
    raws = sorted({i['file'] for i in P['items']})
    print(f"longform_program.json: {len(P['items'])} items over {P.get('dur', 0):.1f} s from {len(raws)} raw recordings:", *[os.path.basename(r) for r in raws])
    for sub, dst in (('captures', 'captures'), (os.path.join('gfx', 'assets'), 'longform_assets')):
        s = os.path.join(W, sub)
        if os.path.isdir(s):
            shutil.copytree(s, dst, dirs_exist_ok=True); print(f'{sub} -> {dst}/ ({sum(len(f) for _, _, f in os.walk(dst))} files)')
    v = os.path.join(W, 'voice48.wav')
    if os.path.exists(v):
        st = cfg.get('clean_stem') or {}
        st['voice'] = v.replace('\\', '/'); cfg['clean_stem'] = st
        ca = cfg.get('clean_audio')
        if ca and os.path.exists(os.path.join(HERE, ca)) and os.path.getsize(os.path.join(HERE, ca)) == os.path.getsize(v):
            cfg['clean_audio'] = None; print(f'clean_audio was a copy of the stem ({ca}): set to null (the export is the base, the stem patches it)')
        print('clean_stem.voice =', st['voice'], '-> next: clean_from_stem.py --scan / --suspects / --build (pipeline.md 1b)')
    cfg['longform'] = {'work': fwd(W)}
    if m:
        cfg['longform'].update(report=fwd(os.path.join(m, 'report.md')), publish=fwd(os.path.join(m, 'PUBLISH.md')))
        print('long-form report / publishing copy:', cfg['longform']['report'], cfg['longform']['publish'])
    json.dump(cfg, open(CFG, 'w', encoding='utf-8'), indent=1)
    print('project.json updated. Graphics: give GFX_BRIEF.md the raw recordings + `import_longform.py --at <t>` (webcam PiP',
          'region of the RAW recordings is never shown), captures/index.json and longform_assets/.')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['--at']: at([float(x) for x in a[1:]])
    elif a[:1] == ['--range']: span(float(a[1]), float(a[2]))
    elif a[:1] == ['--auto']:   # setup.sh: never fails; no long-form run = standalone shorts, as always
        try: main(None, auto=True)
        except Exception as e: print(f'long-form import skipped ({e}); the shorts are made standalone')
    else: main(a[0] if a else None)
