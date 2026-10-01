"""Finish gfx beats into V2 clips (timeline resolution, the source's colour), frame-locked to V1:
  fv     the graphic as rendered
  fvp    the graphic + the webcam PiP pasted frame-exactly at its original place, so the face never jumps on the cut
  split  (hook) the graphic + a squircle camera card on the right (x 1236, y 318, 760x842 layout px, radius 120,
         bleeding off the right and bottom edges) with the speaker's matted head and shoulders popping out above
         the card's top edge. The camera is the full-frame camera or the PiP, whichever V1 shows; the card and the
         matte come from the same decoded frames, so the head can never drift from the body.
Reads gfx/out/<id>.mp4 (render_gfx.sh full). Split beats also need the matte: run with --matte first (GPU u2net through
matte_gpu.py; the HyperFrames CLI on the CPU when CUDA is unavailable).
usage: python scripts/compose.py g01 g04 [--matte] [--preview 1.0,2.5] [--tag v2] [--jobs N]   -> media/<id>[_v2].mp4
  --jobs N   several beats at once, each in its own process (default: up to 3)
  --preview  seeks straight to the wanted frames (seconds): a spot check takes seconds, not the beat's decode"""
import sys, os, json, subprocess
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as M
TAG = ('_' + sys.argv[sys.argv.index('--tag') + 1]) if '--tag' in sys.argv else ''   # edits: a new file, then replace_clip

U = C.UNIT
CARD = dict(x=1236, y=318, w=760, h=842, r=120)
HAIR_Y, CHIN_Y, FACE_X = 222, 742, 1578          # layout px: hair pops ~96 px above the card, whole face inside it


def S(v): return int(round(v * U))


def squircle(x0, y0, w, h, r, n=5.0, ss=2):
    H2, W2 = C.TH * ss, C.TW * ss
    yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32) / ss + 0.5 / ss
    cx = np.clip(xx, x0 + r, x0 + w - r); cy = np.clip(yy, y0 + r, y0 + h - r)
    dx = np.abs(xx - cx) / r; dy = np.abs(yy - cy) / r
    inside = (dx ** n + dy ** n <= 1) & (xx >= x0) & (xx <= x0 + w) & (yy >= y0) & (yy <= y0 + h)
    return inside.astype(np.float32).reshape(C.TH, ss, C.TW, ss).mean((1, 3))


def shadow_from(mask):
    sh = np.zeros_like(mask)
    for dy, blur, a in C.SHADOW:
        m = np.roll(mask, S(dy), 0); m[:S(dy)] = 0
        sh = 1 - (1 - sh) * (1 - a * cv2.GaussianBlur(m, (0, 0), blur / 2 * U))
    return sh


def reader(path, pix='rgb24', ch=3, start=None, count=None):
    """decoded frames of a stream; start/count seek frame-exactly to frame `start` of these CFR streams (previews)"""
    p = M.probe(path); w, h = p['width'], p['height']
    vf = ['-vf', M.dec_vf(path)] if pix == 'rgb24' else []          # the file's own matrix, never ffmpeg's bt601 default
    pre = ['-ss', f'{(start - 0.5) / C.FPS:.6f}'] if start else []   # half a frame early: lands on `start` whatever the timestamp rounding
    post = ['-frames:v', str(count)] if count else []
    proc = M.reader_proc(['ffmpeg', '-v', 'error'] + pre + ['-i', path] + post + vf + ['-f', 'rawvideo', '-pix_fmt', pix, '-'])
    n = w * h * ch
    try:
        while True:
            b = M.read_exact(proc.stdout, n)
            if b is None: break
            yield np.frombuffer(b, np.uint8).reshape(h, w, ch)
    finally:
        proc.stdout.close(); proc.kill() if proc.poll() is None else None; proc.wait()


def scenes():
    return json.load(open('scenes.json')) if os.path.exists('scenes.json') else {'files': {}, 'items': {}}


def cam_region(seq):
    """where the camera is in the source for this beat: the full frame (cam scene) or the PiP safe area"""
    f = seq[0][0]; sc = scenes()
    kinds = {sc['items'].get(str(it['v1']), {}).get('scene') for _, it, _ in seq[::15]}
    p = M.probe(f)
    if kinds == {'cam'}: return [0, 0, p['width'], p['height']]
    safe = (sc['files'].get(f) or {}).get('safe')
    if not safe: raise SystemExit('split beat: no full-frame camera and no PiP found for this beat - run scenes.py, or use fv/fvp')
    return safe


# ------------------------------------------------------------------ matte (split beats)
def matte(bid):
    b = M.beat(bid); f0, f1 = M.frames_of(b['t0'], b['t1']); seq = M.source_map(f0, f1)
    x, y, w, h = cam_region(seq)
    sc = min(1.0, 1280 / max(w, h)); mw, mh = int(w * sc) // 2 * 2, int(h * sc) // 2 * 2
    os.makedirs('split', exist_ok=True)
    cam = f'split/{bid}_cam.mp4'
    enc = M.writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{mw}x{mh}', '-r', str(C.FPS), '-i', '-',
                         '-c:v', 'libx264', '-crf', '8', '-pix_fmt', 'yuv444p', cam])
    for fr in M.decode(seq, w, h, f'crop={w}:{h}:{x}:{y}'):
        enc.stdin.write(cv2.resize(fr, (mw, mh), interpolation=cv2.INTER_AREA).tobytes())
    enc.stdin.close(); enc.wait()
    import matte_gpu                                            # the same u2net model on onnxruntime-gpu; CLI fallback inside
    matte_gpu.matte(bid)


def geometry(bid, region):
    """one scale per split beat: the whole face (hair to chin) fits the card, the hair pops ~96 px above it"""
    gf = f'split/{bid}_geom.json'
    if os.path.exists(gf): return json.load(open(gf))
    mp = M.probe(f'split/{bid}_matte.mov'); mw, mh = mp['width'], mp['height']
    tops = []
    for k, a in enumerate(reader(f'split/{bid}_matte.mov', 'rgba', 4)):
        if k % 6: continue
        col = a[:, int(mw * 0.3):int(mw * 0.7), 3].max(1); idx = np.where(col > 128)[0]
        if len(idx): tops.append(idx[0])
    if not tops:
        raise SystemExit(f'{bid} (split): no head found in its matte - the camera is probably hidden in that part of the source '
                         f'(check scenes.png / look.py); a split beat needs the speaker on camera. Move the beat or use fv/fvp.')
    import mediapipe as mpp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path=C.LANDMARKER), num_faces=1))
    chins, xs = [], []
    for k, fr in enumerate(reader(f'split/{bid}_cam.mp4')):
        if k % 10: continue
        res = det.detect(mpp.Image(image_format=mpp.ImageFormat.SRGB, data=np.ascontiguousarray(fr)))
        if res.face_landmarks:
            L = res.face_landmarks[0]; chins.append(L[152].y * mh); xs.append(L[1].x * mw)
    k_m = region[2] / mw                                   # source px per matte px
    hair, chin, nose = float(np.median(tops)) * k_m, float(np.max(chins)) * k_m, float(np.median(xs)) * k_m
    s_fit = (CHIN_Y - HAIR_Y) * U / max(1.0, chin - hair)  # output px per source px: the whole face fits
    vis_w = (1920 - CARD['x']) * U                         # the card's visible width
    s_cover = vis_w / region[2]                            # the camera covers the card with no blurred strip
    s = s_fit
    if s_fit < s_cover <= 1.25 * s_fit and HAIR_Y * U + s_cover * (chin - hair) <= 1000 * U:
        s = s_cover                                        # cover when the face still fits (chin above y 1000)
    x = FACE_X * U - s * nose
    fw_ = region[2] * s
    if fw_ >= vis_w: x = min(CARD['x'] * U, max(C.TW - fw_, x))     # no uncovered strip at either side
    g = dict(scale=s, scale_fit=s_fit, scale_cover=s_cover, x=x, y=HAIR_Y * U - s * hair, hair=hair, chin=chin, nose=nose,
             head_half=0.46 * (chin - hair), region=region)      # a head is ~0.8x as wide as it is tall
    json.dump(g, open(gf, 'w'), indent=1)
    return g


class Split:
    """the split blend. Everything that does not change between frames (card mask, shadow multiplier, the camera's
    coverage map and its feather) is computed once; per frame the float maths runs only on the columns right of
    the card's shadow (left of them every factor is exactly 1 or 0, so those pixels come back untouched)."""

    def __init__(self):
        self.CM = squircle(S(CARD['x']), S(CARD['y']), S(CARD['w']), S(CARD['h']), S(CARD['r']))
        self.CSH = shadow_from(self.CM) * (1 - self.CM)
        self.RAMP = np.ones(C.TH, np.float32); y0 = S(CARD['y']); self.RAMP[y0:y0 + S(40)] = np.linspace(1, 0, S(40)); self.RAMP[y0 + S(40):] = 0
        self.X0 = S(CARD['x']) - S(8)                           # output area that can show camera: right of the content
        cols = np.where((self.CSH > 0).any(0))[0]
        self.R0 = int(min(self.X0, cols[0])) if len(cols) else self.X0     # first column anything touches
        self.SHADE = 1 - self.CSH[:, self.R0:, None] * (1 - np.array([24, 24, 32], np.float32) / 255)
        self.cm = self.CM[:, self.X0:, None]
        self._geo = None

    def _prep(self, cam_shape, g):
        """per-beat constants: the footage transform, the coverage map and its feather"""
        key = (cam_shape, g['scale'], g['x'], g['y'])
        if self._geo and self._geo[0] == key: return self._geo[1]
        s = g['scale']; ox, oy = g['x'], g['y']
        Wd, Hd = C.TW - self.X0, C.TH
        M_ = np.float32([[s, 0, ox - self.X0], [0, s, oy]])
        cover = cv2.warpAffine(np.ones(cam_shape[:2], np.float32), M_, (Wd, Hd), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        partial = cover.min() < 0.999
        wgt = cv2.GaussianBlur(cover, (0, 0), 20 * U)[..., None] if partial else None
        sb = max(Wd / cam_shape[1], Hd / cam_shape[0]) * 1.12
        Mb = np.float32([[sb, 0, (Wd - sb * cam_shape[1]) / 2], [0, sb, (Hd - sb * cam_shape[0]) / 2]])
        cx = g['x'] + s * g['nose'] - self.X0; hw = s * g['head_half']
        band = np.clip((hw - np.abs(np.arange(Wd, dtype=np.float32) - cx)) / (24 * U) + 0.5, 0, 1)
        up = np.ones(Hd, np.float32); up[:S(CARD['y'])] = 0; keep = np.maximum(up[:, None], band[None, :])
        self._geo = (key, dict(M_=M_, Wd=Wd, Hd=Hd, cover=cover, partial=partial, wgt=wgt, Mb=Mb, keep=keep))
        return self._geo[1]

    def frame(self, bg, cam, alpha, g):
        """bg: graphic (TH, TW, 3) uint8; cam: source camera crop (region size); alpha: matte (any size, uint8) -> uint8 frame"""
        P = self._prep(cam.shape, g); M_, Wd, Hd = P['M_'], P['Wd'], P['Hd']
        foot = cv2.warpAffine(cam, M_, (Wd, Hd), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        A = cv2.resize(alpha, (cam.shape[1], cam.shape[0]), interpolation=cv2.INTER_LINEAR)
        A = cv2.warpAffine(A, M_, (Wd, Hd), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(np.float32) / 255
        A = cv2.GaussianBlur(cv2.erode(A, np.ones((3, 3), np.uint8)), (0, 0), 1.2 * U)
        if P['partial']:                                      # soft fill where the (portrait) camera can't reach
            blur = cv2.GaussianBlur(cv2.resize(cam, (cam.shape[1] // 4, cam.shape[0] // 4), interpolation=cv2.INTER_AREA), (0, 0), 6)
            fill = cv2.warpAffine(cv2.resize(blur, (cam.shape[1], cam.shape[0])), P['Mb'], (Wd, Hd), borderMode=cv2.BORDER_REPLICATE)
            foot = (foot * P['wgt'] + fill * (1 - P['wgt'])).astype(np.float32)
        out = bg[:, self.R0:].astype(np.float32)             # only the columns anything can touch
        out *= self.SHADE
        area = out[:, self.X0 - self.R0:]
        area[:] = area * (1 - self.cm) + foot * self.cm
        # the pop-out above the card is the head and shoulders only: a feathered band around the face (a matte can
        # pick up a guitar or a lamp beside the head)
        ah = (A * P['cover'] * P['keep'] * self.RAMP[:, None])[..., None]    # same operand order as before: bit-identical
        area[:] = area * (1 - ah) + foot * ah
        img = bg.copy()
        img[:, self.R0:] = np.clip(out + 0.5, 0, 255).astype(np.uint8)
        return img


def frame_fvp(bg, cam, X, Y, Wo, Ho, pa, psh, box):
    sy0, sy1, sx0, sx1 = box
    img = bg.copy()                                           # the PiP is a card in the world: spec shadow
    img[sy0:sy1, sx0:sx1] = np.clip(bg[sy0:sy1, sx0:sx1] * (1 - psh) + 0.5, 0, 255).astype(np.uint8)
    reg = img[Y:Y + Ho, X:X + Wo].astype(np.float32)
    img[Y:Y + Ho, X:X + Wo] = np.clip(reg * (1 - pa) + cam * pa + 0.5, 0, 255).astype(np.uint8)
    return img


def compose(bid, preview=None, nvenc=None):
    b = M.beat(bid); f0, f1 = M.frames_of(b['t0'], b['t1']); n = f1 - f0
    mode = b.get('layout', 'fv')
    src_g = f'gfx/out/{bid}.mp4'
    if not os.path.exists(src_g): raise SystemExit(f'{src_g} missing - run render_gfx.sh full {bid}')
    seq = M.source_map(f0, f1)
    want = None if preview is None else sorted({int(round(t * C.FPS)) for t in preview})
    os.makedirs(C.MEDIA, exist_ok=True); os.makedirs('preview', exist_ok=True)
    out = os.path.join(C.MEDIA, f'{bid}{TAG}.mp4')
    fvp = sp = None
    if mode == 'fvp':
        f = seq[0][0]; win = (scenes()['files'].get(f) or {}).get('pip')
        if not win: raise SystemExit(f'{bid}: fvp needs a PiP window for {f} (scenes.json) - use fv')
        x, y, w, h = win; kfit = min(C.TW / M.probe(f)['width'], C.TH / M.probe(f)['height'])
        X, Y, Wo, Ho = [int(round(v * kfit)) for v in win]
        crop = f'crop={w}:{h}:{x}:{y}'
        pa = M.pip_mask(Wo, Ho)[..., None]                       # rounded, inset: no screen corners on the white world
        full = np.zeros((C.TH, C.TW), np.float32); full[Y:Y + Ho, X:X + Wo] = pa[..., 0]
        psh = (shadow_from(full) * (1 - full))[..., None] * (1 - np.array([24, 24, 32], np.float32) / 255)
        ys_, xs_ = np.where(psh[..., 0] > 1e-3); box = (ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1)
        psh = psh[box[0]:box[1], box[2]:box[3]]                 # only the shadow's own box is touched per frame
        fvp = (X, Y, Wo, Ho, pa, psh, box)
        fit = lambda cam: cam if (Wo, Ho) == (w, h) else cv2.resize(cam, (Wo, Ho), interpolation=cv2.INTER_AREA)
    elif mode == 'split':
        region = cam_region(seq); g = geometry(bid, region); sp = Split()
        x, y, w, h = region; crop = f'crop={w}:{h}:{x}:{y}'

    def make(bg, cam, al):
        if mode == 'fvp': return frame_fvp(bg, fit(cam), *fvp)
        if mode == 'split': return sp.frame(bg, cam, al, g)
        return bg

    if want is not None:                                         # previews: seek every stream to the wanted frames only
        for k in want:
            if not 0 <= k < n: continue
            bg = next(reader(src_g, start=k, count=1))
            cam = M.decode_at(seq, k, w, h, crop) if mode in ('fvp', 'split') else None
            al = next(reader(f'split/{bid}_matte.mov', 'rgba', 4, start=k, count=1))[..., 3] if mode == 'split' else None
            cv2.imwrite(f'preview/{bid}_{k / C.FPS:06.2f}.png', cv2.cvtColor(make(bg, cam, al), cv2.COLOR_RGB2BGR))
        print(f'{bid}: previews in preview/{bid}_*.png'); return
    enc = M.encoder(out, C.TW, C.TH, seq[0][0], nvenc=nvenc)
    gfx = reader(src_g)
    cams = M.decode(seq, w, h, crop) if mode in ('fvp', 'split') else None
    mattes = reader(f'split/{bid}_matte.mov', 'rgba', 4) if mode == 'split' else None
    for k in range(n):
        bg = next(gfx)
        img = make(bg, next(cams) if cams else None, next(mattes)[..., 3] if mattes else None)
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    enc.stdin.close(); enc.wait(); print(f'{bid}: {mode} {n} frames -> {out}', flush=True)


if __name__ == '__main__':
    argv = sys.argv[1:]; prev = None; jobs = 3
    if '--tag' in argv: k = argv.index('--tag'); argv = argv[:k] + argv[k + 2:]
    if '--jobs' in argv: k = argv.index('--jobs'); jobs = int(argv[k + 1]); argv = argv[:k] + argv[k + 2:]
    if '--preview' in argv:
        k = argv.index('--preview'); prev = [float(v) for v in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
    ids = [a for a in argv if not a.startswith('--')]
    if '--matte' in argv:
        for bid in ids: matte(bid)
    elif len(ids) > 1 and jobs > 1 and prev is None:            # one process per beat, up to --jobs at once
        import time
        procs, pending = [], list(ids)
        while pending or procs:
            while pending and len(procs) < jobs:
                bid = pending.pop(0); procs.append((bid, subprocess.Popen([sys.executable, __file__, bid] + [a for a in sys.argv[1:] if a not in ids and a != '--jobs' and not a.isdigit()])))
            time.sleep(0.5)
            for item in procs[:]:
                if item[1].poll() is not None:
                    procs.remove(item)
                    if item[1].returncode: print(f'FAILED {item[0]} (exit {item[1].returncode})')
    else:
        for bid in ids: compose(bid, prev, False if '--x264' in argv else None)
