"""Frame-exact camera clips, one per camera run (full cam / split), following the cut's picture mapping.
Exactly one clip frame per 60 fps output frame (30 fps sources are frame-doubled), so compose + matte stay frame-locked.
kinds:  pip   -> the webcam safe region, native size (compose cover-fits it / places it in the split card)
        slice -> 9:16 centre slice of a full-frame camera, already 1080x1920 (full cam)
        frame -> the full 16:9 camera frame at 1920x1080 (split card: scaled to 1890x1063 at x -405, y 1008)
All runs are extracted concurrently (CAM_JOBS, default 4): each run is its own ffmpeg decode (NVDEC when available,
CAM_HWACCEL=0 forces CPU; the decoded frames are identical) feeding its own multi-slice FFV1 encoder.
usage: python scripts/cam_prep.py s1 [s2 ...]  [--runs 0,6]"""
import json, subprocess, os, sys, time, numpy as np
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'scripts'); import config as C
OFPS = 60
args = sys.argv[1:]
only = None
if '--runs' in args:
    k = args.index('--runs'); only = [int(x) for x in args[k + 1].split(',')]; del args[k:k + 2]
shorts = args or ['s1']
JOBS = int(os.environ.get('CAM_JOBS', '4'))
HW = [] if os.environ.get('CAM_HWACCEL', '1') == '0' else (
    ['-hwaccel', 'cuda'] if subprocess.run(['ffmpeg', '-v', 'error', '-hwaccels'], capture_output=True, text=True).stdout.find('cuda') >= 0 else [])
FFV1 = ['-c:v', 'ffv1', '-level', '3', '-slices', '16', '-slicecrc', '0', '-pix_fmt', 'bgr0']   # lossless; slices = multi-threaded encode/decode


def kind_for(layout, line):
    if line.get('cam') in ('fullframe', 'cam4k') or C.MODE == 'full':
        return 'slice' if layout == 'fc' else 'frame'
    return 'pip'


def geom(kind):
    if kind == 'pip':
        x, y, w, h = C.SAFE; return f'crop={w}:{h}:{x}:{y}', (w, h)
    if kind == 'slice':
        x, y, w, h = C.FULL_SLICE; return f'crop={w}:{h}:{x}:{y},scale=1080:1920:flags=lanczos', (1080, 1920)
    x, y, w, h = C.WINDOW if C.MODE == 'full' else [0, 0, C.SRC_W, C.SRC_H]
    return f'crop={w}:{h}:{x}:{y},scale=1920:1080:flags=lanczos', (1920, 1080)


def extract(sk, CUT, lines, r):
    n0, n1 = round(r['T0'] * OFPS), round(r['T1'] * OFPS)
    seq = []
    for n in range(n0, n1):
        t = n / OFPS
        p = [p for p in CUT['pieces'] if p['pic0'] - 1e-6 <= t < p['pic1'] - 1e-6][0]
        seq.append((int(round((t - p['off']) * C.FPS)), lines[p['line']]))
    kind = kind_for(r['layout'], seq[0][1]); vf, (w, h) = geom(kind)
    uniq = sorted(set(k for k, _ in seq))
    segs = []; a = uniq[0]; prev = a
    for k in uniq[1:]:
        if k != prev + 1: segs.append((a, prev)); a = k
        prev = k
    segs.append((a, prev))
    out = f'{sk}/cam/r{r["i"]}.mkv'
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(OFPS), '-i', '-'] + FFV1 + [out], stdin=subprocess.PIPE)
    need = [k for k, _ in seq]
    segs.sort(key=lambda sg: need.index(sg[0]))          # decode in timeline order so frames stream straight out
    frames = {}; t0 = time.time()
    for a, b in segs:
        # format=yuv420p makes the NVDEC (nv12) and CPU (yuv420p) decode paths take the same colour conversion: identical rgb
        dec = subprocess.Popen(['ffmpeg', '-v', 'error'] + HW + ['-ss', f'{a / C.FPS - 0.25 / C.FPS:.5f}', '-i', C.SRC, '-frames:v', str(b - a + 1),
                                '-vf', 'format=yuv420p,' + vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
        for k in range(a, b + 1):
            buf = dec.stdout.read(w * h * 3)
            if len(buf) < w * h * 3: break
            frames[k] = buf
            while need and need[0] in frames:                # serve every timeline frame that is ready (dupes for 30 fps sources)
                kk = need.pop(0); enc.stdin.write(frames[kk])
                if not need or need[0] != kk: frames.pop(kk, None)
        dec.wait()
    if need: raise SystemExit(f'{sk} run {r["i"]}: {len(need)} frames could not be decoded')
    enc.stdin.close(); enc.wait()
    print(sk, 'run', r['i'], r['layout'], kind, f'{w}x{h}', 'frames', n1 - n0, 'source segs', segs, f'{time.time() - t0:.1f}s', flush=True)
    return sk, str(r['i']), dict(layout=r['layout'], kind=kind, n0=n0, n1=n1, frames=n1 - n0, size=[w, h], segs=segs, file=out)


jobs = []
for sk in shorts:
    CUT = json.load(open('cut.json'))[sk]; S = json.load(open('shorts.json'))[sk]; lines = {L['id']: L for L in S['lines']}
    os.makedirs(f'{sk}/cam', exist_ok=True)
    for r in CUT['runs']:
        if r['layout'] not in ('fc', 'split') or (only is not None and r['i'] not in only): continue
        jobs.append((sk, CUT, lines, r))
t_all = time.time()
with ThreadPoolExecutor(max(1, min(JOBS, len(jobs)))) as ex: results = list(ex.map(lambda j: extract(*j), jobs))
for sk in shorts:
    planf = f'{sk}/cam/plan.json'; plan = json.load(open(planf)) if os.path.exists(planf) else {}
    for s_, ri, entry in results:
        if s_ == sk: plan[ri] = entry
    json.dump(plan, open(planf, 'w'), indent=1)
print(f'{len(jobs)} camera runs in {time.time() - t_all:.1f}s', '(NVDEC)' if HW else '(CPU decode)')
