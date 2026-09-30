"""Finish gfx beats into V2 clips (timeline resolution, the source's colour), frame-locked to V1:
  fv     the graphic as rendered
  fvp    the graphic + the webcam PiP pasted frame-exactly at its original place, so the face never jumps on the cut
  split  (hook) the graphic + a squircle camera card on the right (x 1236, y 318, 760x842 layout px, radius 120,
         bleeding off the right and bottom edges) with the speaker's matted head and shoulders popping out above
         the card's top edge. The camera is the full-frame camera or the PiP, whichever V1 shows; the card and the
         matte come from the same decoded frames, so the head can never drift from the body.
Reads gfx/out/<id>.mp4 (render_gfx.sh full). Split beats also need the matte: run with --matte first.
usage: python scripts/compose.py g01 g04 [--matte] [--preview 1.0,2.5] [--tag v2]   -> media/<id>[_v2].mp4"""
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


def reader(path, pix='rgb24', ch=3):
    p = M.probe(path); w, h = p['width'], p['height']
    vf = ['-vf', M.dec_vf(path)] if pix == 'rgb24' else []          # the file's own matrix, never ffmpeg's bt601 default
    proc = M.reader_proc(['ffmpeg', '-v', 'error', '-i', path] + vf + ['-f', 'rawvideo', '-pix_fmt', pix, '-'])
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
    out = f'split/{bid}_matte.mov'
    log = open(f'split/{bid}_matte.log', 'w')                   # its progress bar floods a terminal
    r = subprocess.run(f'npx --yes hyperframes remove-background {cam} -o {out} --device cuda', shell=True, stdout=log, stderr=log)
    if r.returncode != 0:
        print('GPU matting unavailable - using the CPU (about 2-3 fps)')
        subprocess.run(f'npx --yes hyperframes remove-background {cam} -o {out} --device cpu', shell=True, check=True, stdout=log, stderr=log)
    print(f'{bid}: matte -> {out}')


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
    def __init__(self):
        self.CM = squircle(S(CARD['x']), S(CARD['y']), S(CARD['w']), S(CARD['h']), S(CARD['r']))
        self.CSH = shadow_from(self.CM) * (1 - self.CM)
        self.RAMP = np.ones(C.TH, np.float32); y0 = S(CARD['y']); self.RAMP[y0:y0 + S(40)] = np.linspace(1, 0, S(40)); self.RAMP[y0 + S(40):] = 0

    def frame(self, bg, cam, alpha, g):
        """bg: graphic (TH, TW, 3); cam: source camera crop (region size); alpha: matte (any size, uint8)"""
        s = g['scale']; ox, oy = g['x'], g['y']
        X0 = S(CARD['x']) - S(8); Y0 = 0                    # output area that can show camera: right of the content
        Wd, Hd = C.TW - X0, C.TH
        M_ = np.float32([[s, 0, ox - X0], [0, s, oy - Y0]])  # source px -> area px
        foot = cv2.warpAffine(cam, M_, (Wd, Hd), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_CONSTANT)
        A = cv2.resize(alpha, (cam.shape[1], cam.shape[0]), interpolation=cv2.INTER_LINEAR)
        A = cv2.warpAffine(A, M_, (Wd, Hd), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT).astype(np.float32) / 255
        A = cv2.GaussianBlur(cv2.erode(A, np.ones((3, 3), np.uint8)), (0, 0), 1.2 * U)
        cover = cv2.warpAffine(np.ones(cam.shape[:2], np.float32), M_, (Wd, Hd), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
        if cover.min() < 0.999:                              # soft fill where the (portrait) camera can't reach
            blur = cv2.GaussianBlur(cv2.resize(cam, (cam.shape[1] // 4, cam.shape[0] // 4), interpolation=cv2.INTER_AREA), (0, 0), 6)
            sb = max(Wd / cam.shape[1], Hd / cam.shape[0]) * 1.12
            Mb = np.float32([[sb, 0, (Wd - sb * cam.shape[1]) / 2], [0, sb, (Hd - sb * cam.shape[0]) / 2]])
            fill = cv2.warpAffine(cv2.resize(blur, (cam.shape[1], cam.shape[0])), Mb, (Wd, Hd), borderMode=cv2.BORDER_REPLICATE)
            wgt = cv2.GaussianBlur(cover, (0, 0), 20 * U)[..., None]
            foot = (foot * wgt + fill * (1 - wgt)).astype(np.float32)
        out = bg.astype(np.float32)
        out *= (1 - self.CSH[..., None] * (1 - np.array([24, 24, 32], np.float32) / 255))
        cm = self.CM[:, X0:, None]
        area = out[:, X0:]
        area[:] = area * (1 - cm) + foot * cm
        # the pop-out above the card is the head and shoulders only: a feathered band around the face (a matte can
        # pick up a guitar or a lamp beside the head)
        cx = g['x'] + s * g['nose'] - X0; hw = s * g['head_half']
        band = np.clip((hw - np.abs(np.arange(Wd, dtype=np.float32) - cx)) / (24 * U) + 0.5, 0, 1)
        up = np.ones(Hd, np.float32); up[:S(CARD['y'])] = 0; keep = np.maximum(up[:, None], band[None, :])
        ah = (A * cover * keep * self.RAMP[:, None])[..., None]
        area[:] = area * (1 - ah) + foot * ah
        return out


def compose(bid, preview=None, nvenc=None):
    b = M.beat(bid); f0, f1 = M.frames_of(b['t0'], b['t1']); n = f1 - f0
    mode = b.get('layout', 'fv')
    src_g = f'gfx/out/{bid}.mp4'
    if not os.path.exists(src_g): raise SystemExit(f'{src_g} missing - run render_gfx.sh full {bid}')
    seq = M.source_map(f0, f1)
    want = None if preview is None else {int(round(t * C.FPS)) for t in preview}
    os.makedirs(C.MEDIA, exist_ok=True); os.makedirs('preview', exist_ok=True)
    out = os.path.join(C.MEDIA, f'{bid}{TAG}.mp4')
    enc = None if want is not None else M.encoder(out, C.TW, C.TH, seq[0][0], nvenc=nvenc)
    gfx = reader(src_g)
    if mode == 'fvp':
        f = seq[0][0]; win = (scenes()['files'].get(f) or {}).get('pip')
        if not win: raise SystemExit(f'{bid}: fvp needs a PiP window for {f} (scenes.json) - use fv')
        x, y, w, h = win; kfit = min(C.TW / M.probe(f)['width'], C.TH / M.probe(f)['height'])
        X, Y, Wo, Ho = [int(round(v * kfit)) for v in win]
        cams = M.decode(seq, w, h, f'crop={w}:{h}:{x}:{y}')
        pa = M.pip_mask(Wo, Ho)[..., None]                       # rounded, inset: no screen corners on the white world
        full = np.zeros((C.TH, C.TW), np.float32); full[Y:Y + Ho, X:X + Wo] = pa[..., 0]
        psh = (shadow_from(full) * (1 - full))[..., None] * (1 - np.array([24, 24, 32], np.float32) / 255)
        ys_, xs_ = np.where(psh[..., 0] > 1e-3); sy0, sy1, sx0, sx1 = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
        psh = psh[sy0:sy1, sx0:sx1]                                # only the shadow's own box is touched per frame
    elif mode == 'split':
        region = cam_region(seq); g = geometry(bid, region); sp = Split()
        x, y, w, h = region
        cams = M.decode(seq, w, h, f'crop={w}:{h}:{x}:{y}'); mattes = reader(f'split/{bid}_matte.mov', 'rgba', 4)
    for k in range(n):
        bg = next(gfx)
        if mode == 'fvp':
            cam = next(cams)
            if (Wo, Ho) != (w, h): cam = cv2.resize(cam, (Wo, Ho), interpolation=cv2.INTER_AREA)
            img = bg.copy()                                        # the PiP is a card in the world: spec shadow
            img[sy0:sy1, sx0:sx1] = np.clip(bg[sy0:sy1, sx0:sx1] * (1 - psh) + 0.5, 0, 255).astype(np.uint8)
            reg = img[Y:Y + Ho, X:X + Wo].astype(np.float32)
            img[Y:Y + Ho, X:X + Wo] = np.clip(reg * (1 - pa) + cam * pa + 0.5, 0, 255).astype(np.uint8)
        elif mode == 'split':
            cam = next(cams); al = next(mattes)[..., 3]
            img = np.clip(sp.frame(bg, cam, al, g) + 0.5, 0, 255).astype(np.uint8) if (want is None or k in want) else None
        else:
            img = bg
        if want is not None:
            if k in want: cv2.imwrite(f'preview/{bid}_{k / C.FPS:06.2f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
            continue
        enc.stdin.write(np.ascontiguousarray(img).tobytes())
    if enc:
        enc.stdin.close(); enc.wait(); print(f'{bid}: {mode} {n} frames -> {out}')
    else:
        print(f'{bid}: previews in preview/{bid}_*.png')


if __name__ == '__main__':
    argv = sys.argv[1:]; prev = None
    if '--tag' in argv: k = argv.index('--tag'); argv = argv[:k] + argv[k + 2:]
    if '--preview' in argv:
        k = argv.index('--preview'); prev = [float(v) for v in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
    ids = [a for a in argv if not a.startswith('--')]
    for bid in ids:
        if '--matte' in argv: matte(bid)
        else: compose(bid, prev, False if '--x264' in argv else None)
