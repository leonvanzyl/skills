"""QC for the dynamic camera (references/dynamic-camera.md). Run on the layer AND on the final file.

usage (cwd = W):
  python scripts/dyncam_qc.py flash [file]   # around every key: a frame that differs from BOTH neighbours by more than the
                                             # neighbours differ from each other (a one-frame flash / ghost / blend), > 3
                                             # (mean abs, 8-bit). Default file: $M/layout_<tag>.mp4. A morph should be a
                                             # smooth bell in the frame-difference curve, never a spike.
  python scripts/dyncam_qc.py sync <file>    # the face's speed and sync in each state: the frame-to-frame motion inside the
                                             # camera window, correlated with the webcam frames mapped there. Pass: best lag
                                             # 0 with correlation >= 0.85 in every state (abacus v3: 0.91-0.99).
Decoding: `sync` reads from frame 0 with no seek. ffmpeg's input seek lands ONE FRAME EARLY in Resolve's MP4s (they
carry an edit list), which once read as "the face is a frame late" on a file that was frame-exact. `flash` seeks
(only the pattern matters), so frame numbers it reports on a Resolve render may be one low."""
import subprocess, sys
import numpy as np, cv2
sys.path.insert(0, 'scripts')
import dyncam as D

FPS = D.FPS


def window_frames(src, a, b, w=480, h=270):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{(a - 0.5) / FPS:.6f}', '-i', src, '-frames:v', str(b - a + 1),
                          '-vf', f'scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)


def flash(src):
    found = []
    for k in D.KEYS:
        a = int(round(k['t'] * FPS)) - 6; b = int(round((k['t'] + k['dur']) * FPS)) + 6
        f = window_frames(src, max(0, a), min(D.TOTAL - 1, b))
        for i in range(1, len(f) - 1):
            dp, dn, dpn = (np.abs(f[i] - f[i - 1]).mean(), np.abs(f[i] - f[i + 1]).mean(), np.abs(f[i - 1] - f[i + 1]).mean())
            if min(dp, dn) - dpn > 3: found.append((round((max(0, a) + i) / FPS, 3), round(float(min(dp, dn) - dpn), 1), k['to']))
    print(f'{src}\nmoves {len(D.KEYS)} | flash frames: {found or "none"}')
    return not found


def tests():
    """the middle of the longest hold of each state (and of each SMALL corner)"""
    keys = [D.PLAN['start'] | {'t': 0.0, 'dur': 0}] + D.KEYS
    best = {}
    for k, nx in zip(keys, keys[1:] + [{'t': D.TOTAL / FPS}]):
        a, b = k['t'] + k.get('dur', 0), nx['t']
        if k['to'] == 'HIDDEN' or b - a < 3.5: continue
        lab = k['to'] + (' ' + k.get('corner', D.DEFC) if k['to'] == 'SMALL' else '')
        if b - a > best.get(lab, (0, 0))[1] - best.get(lab, (0, 0))[0]: best[lab] = (a, b)
    return [(round((a + b) / 2 - 1.25, 2), lab) for lab, (a, b) in sorted(best.items())]


def sync(src, N=150):
    T = [(t, lab) for t, lab in tests() if D.cam_src(int(round(t * FPS)))]
    want = {n for t, _ in T for n in range(int(round(t * FPS)), int(round(t * FPS)) + N)}
    k = 480 / D.LW; SEQ = {}
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-frames:v', str(max(want) + 1), '-vf', 'scale=480:270:flags=area,format=gray',
                          '-f', 'rawvideo', '-'], stdout=subprocess.PIPE, bufsize=0)
    for n in range(max(want) + 1):
        buf = bytearray()
        while len(buf) < 480 * 270:
            c = p.stdout.read(480 * 270 - len(buf))
            if not c: break
            buf += c
        if n in want: SEQ[n] = np.frombuffer(bytes(buf), np.uint8).reshape(270, 480)
    p.wait()
    R = D.Reader(); ok = True
    try:
        for t, lab in T:
            n0 = int(round(t * FPS)); g = D.at(t)[0]
            x, y, w, h = [int(round(v * k)) for v in g['r']]; x += 2; y += 2; w -= 4; h -= 4
            a = np.stack([cv2.resize(SEQ[n][y:y + h, x:x + w], (64, 64), interpolation=cv2.INTER_AREA) for n in range(n0, n0 + N)]).astype(np.float32)
            bsrc = []
            for n in range(n0, n0 + N):
                f, fr = D.cam_src(n); img = R.get(f, fr, D.CAM_W, D.CAM_H)
                bsrc.append(cv2.resize(cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2GRAY), (64, 64), interpolation=cv2.INTER_AREA))
            ma, mb = np.abs(np.diff(a, axis=0)).mean(axis=(1, 2)), np.abs(np.diff(np.stack(bsrc).astype(np.float32), axis=0)).mean(axis=(1, 2))
            res = []
            for lag in range(-4, 5):
                xa, yb = (ma[lag:], mb[:len(mb) - lag]) if lag >= 0 else (ma[:lag], mb[-lag:])
                res.append((round(float(np.corrcoef(xa, yb)[0, 1]), 3), lag))
            c0 = dict((l, c) for c, l in res)[0]; cb, lb = max(res)
            good = lb == 0 and c0 >= 0.85; ok &= good
            print(f'{lab:9s} t={t:7.2f}  corr@0={c0:5.3f}  best lag={lb:+d} ({cb:.3f})  {"ok" if good else "<- CHECK (speed or sync)"}')
    finally:
        R.close()
    print('face speed and sync:', 'PASS' if ok else 'FAIL')
    return ok


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['flash']: sys.exit(0 if flash(a[1] if len(a) > 1 else D.OUT) else 1)
    if a[:1] == ['sync'] and len(a) > 1: sys.exit(0 if sync(a[1]) else 1)
    sys.exit(__doc__)
