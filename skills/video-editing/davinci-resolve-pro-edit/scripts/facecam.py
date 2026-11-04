"""The rounded facecam bubble for SEPARATE webcam recordings (references/separate-sources.md): the webcam cropped to
head and shoulders, rounded corners, a hairline rim and a soft drop shadow, as ProRes 4444 with alpha on a small
canvas that Resolve shows 1:1 (Scaling = Crop) and places with Pan/Tilt. Every clip is checked against its source
before it is reported done: frame count, playback SPEED and frame OFFSET.

Why the check exists (abacus-test, 2026-11-01): the static layers (mask / shadow / rim PNGs) went in as
`-loop 1 -i x.png`, which ffmpeg reads at its default 25 fps, and the overlay that used one as its base took ITS clock -
every output frame jumped ~2.4 webcam frames. The user saw "my mouth is moving extremely fast" and an eye-wipe that
came from much later in the recording. Every image input here is `-loop 1 -framerate FPS`; never drop that.

  python facecam.py layers <out_dir>                          mask.png, shadow.png, rim.png (once per project)
  python facecam.py render <jobs.json> <out_dir> [--jobs 6]   jobs: [{"name": "fc_g02_0.mov", "file": <webcam>, "src0": <frame>, "frames": n}]
  python facecam.py check <clip.mov> <webcam> <src0>          speed / offset report for one clip
Options: --size 640 (bubble px, timeline UHD) --crop 1800,1110,158 (square side,x,y in webcam px: face centred, eyes
~40% down) --fps 60 --radius 72. Measure the crop per project (faces.py on a few frames).

Placing a clip in Resolve (canvas C = size + 2*96): SetProperty('Scaling', 1) (Crop: 1:1 pixels), then Pan/Tilt in
CLIP-relative units: Pan = dx * TW / C, Tilt = dy * TH / C, where dx/dy are the timeline px from the frame centre to
the bubble centre (Tilt +up). Bottom-right with a 72 px margin on UHD, size 640: dx 1528, dy -688 -> Pan 7052.31,
Tilt -1786.15 for C = 832."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np

A = sys.argv
def opt(k, d): return A[A.index(k) + 1] if k in A else d
FPS = int(opt('--fps', 60)); B = int(opt('--size', 640)); RADIUS = int(opt('--radius', 72)); PAD = 96; C = B + 2 * PAD
CROP = tuple(int(v) for v in opt('--crop', '1800,1110,158').split(','))


def rounded(w, h, r, ss=4):
    import cv2
    m = np.zeros((h * ss, w * ss), np.uint8); rr = r * ss
    cv2.rectangle(m, (rr, 0), (w * ss - rr - 1, h * ss - 1), 255, -1)
    cv2.rectangle(m, (0, rr), (w * ss - 1, h * ss - rr - 1), 255, -1)
    for cx, cy in ((rr, rr), (w * ss - rr - 1, rr), (rr, h * ss - rr - 1), (w * ss - rr - 1, h * ss - rr - 1)):
        cv2.circle(m, (cx, cy), rr, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA)


def layers(d):
    import cv2
    os.makedirs(d, exist_ok=True)
    mask = rounded(B, B, RADIUS); cv2.imwrite(os.path.join(d, 'mask.png'), mask)
    sh = np.zeros((C, C), np.float32); sh[PAD + 18:PAD + 18 + B, PAD:PAD + B] = mask / 255.0
    sh = cv2.GaussianBlur(sh, (0, 0), 30) * 0.42
    shadow = np.zeros((C, C, 4), np.uint8); shadow[..., 3] = np.clip(sh * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(d, 'shadow.png'), shadow)
    ring = mask.astype(np.float32).copy(); ring[3:-3, 3:-3] -= rounded(B - 6, B - 6, RADIUS - 3)
    rim = np.zeros((C, C, 4), np.uint8); rim[..., :3] = 255
    rim[PAD:PAD + B, PAD:PAD + B, 3] = np.clip(ring * 0.38, 0, 255).astype(np.uint8)
    cv2.imwrite(os.path.join(d, 'rim.png'), rim)


def _gray(cmd, w=64):
    raw = subprocess.run(cmd, capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, w, w).astype(np.float32)


def check(clip, webcam, src0, n=None):
    """match the clip's face against the webcam: returns (frames, err at speed 1, err at speed 2.5, best offset)"""
    s, x, y = CROP
    cx, cy, cw = 250, 244, 140                                   # a mouth-height window inside the bubble (canvas px)
    wx, wy, ww = int((cx) * s / B + x), int((cy) * s / B + y), int(cw * s / B)
    got = int(subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                              'stream=nb_read_frames', '-of', 'csv=p=0', clip], capture_output=True, text=True).stdout.strip() or 0)
    if got < 8: sys.exit(f'check: {clip} has {got} frames (missing or unreadable)')
    k = min(got, 120)
    fc = _gray(['ffmpeg', '-v', 'error', '-i', clip, '-frames:v', str(k), '-vf',
                f'crop={cw}:{cw}:{PAD + cx}:{PAD + cy},scale=64:64,format=gray', '-f', 'rawvideo', '-'])
    wc = _gray(['ffmpeg', '-v', 'error', '-ss', f'{max(0.0, (src0 - 0.25) / FPS):.5f}', '-i', webcam, '-frames:v', str(k * 3),
                '-vf', f'crop={ww}:{ww}:{wx}:{wy},scale=64:64,format=gray', '-f', 'rawvideo', '-'])
    err = {}
    for sp in (1.0, 2.5):
        idx = np.round(np.arange(len(fc)) * sp).astype(int); idx = idx[idx < len(wc)]
        err[sp] = float(np.abs(fc[:len(idx)] - wc[idx]).mean())
    m = min(len(fc), len(wc)) - 3
    offs = {o: float(np.abs(fc[3:m] - wc[3 + o:m + o]).mean()) for o in (-2, -1, 0, 1, 2) if m + o <= len(wc)}
    return got, err[1.0], err[2.5], min(offs, key=offs.get)


def render(job, out_dir, lay):
    name, f, a, n = job['name'], job['file'], job['src0'], job['frames']
    out = os.path.join(out_dir, name)
    s, x, y = CROP
    to709 = 'scale=out_color_matrix=bt709:out_range=tv,format=yuva444p'
    fc = (f'[0:v]crop={s}:{s}:{x}:{y},scale={B}:{B}:flags=lanczos,format=yuva444p[c];[1:v]format=gray[m];[c][m]alphamerge[b];'
          f'[2:v]{to709}[s];[s][b]overlay={PAD}:{PAD}:format=yuv444[o];[3:v]{to709}[r];'
          f'[o][r]overlay=0:0:format=yuv444,format=yuva444p10le,setpts=N/{FPS}/TB[v]')
    img = lambda p: ['-loop', '1', '-framerate', str(FPS), '-i', os.path.join(lay, p)]   # -framerate: see the docstring
    cmd = (['ffmpeg', '-v', 'error', '-y', '-ss', f'{max(0.0, (a - 0.25) / FPS):.5f}', '-i', f] + img('mask.png') + img('shadow.png')
           + img('rim.png') + ['-filter_complex', fc, '-map', '[v]', '-frames:v', str(n), '-r', str(FPS), '-c:v', 'prores_ks',
           '-profile:v', '4444', '-qscale:v', '8', '-alpha_bits', '16', '-vendor', 'apl0', '-colorspace', 'bt709',
           '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', '-an', out])
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: return name, f'FAILED {r.stderr[-300:]}'
    got, e1, e25, off = check(out, f, a, n)
    ok = got == n and e1 < e25 * 0.5 and off == 0
    return name, f"{'ok ' if ok else 'BAD'} frames {got}/{n} | match err speed 1x {e1:.1f} vs 2.5x {e25:.1f} | offset {off:+d}"


if __name__ == '__main__':
    cmd = A[1] if len(A) > 1 else ''
    if cmd == 'layers':
        layers(A[2]); print('layers ->', A[2])
    elif cmd == 'render':
        jobs = json.load(open(A[2])); out = A[3]; lay = os.path.join(out, '_layers')
        if not os.path.exists(os.path.join(lay, 'rim.png')): layers(lay)
        with ThreadPoolExecutor(int(opt('--jobs', 6))) as ex:
            res = list(ex.map(lambda j: render(j, out, lay), jobs))
        for name, msg in res: print(name, msg)
        bad = [n for n, m in res if not m.startswith('ok')]
        print(f'{len(res)} clips, {len(bad)} bad' + (f': {bad}' if bad else ''))
        sys.exit(1 if bad else 0)
    elif cmd == 'check':
        got, e1, e25, off = check(A[2], A[3], int(A[4]))
        print(f'frames {got} | match err speed 1x {e1:.1f} vs 2.5x {e25:.1f} | best offset {off:+d} -> '
              f"{'OK' if e1 < e25 * 0.5 and off == 0 else 'WRONG SPEED OR SYNC'}")
    else:
        print(__doc__)
