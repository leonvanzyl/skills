"""Render 'zoom' beats: the screen recording itself, followed frame-exactly along V1 (jump cuts included), with a
camera that pushes into the part being talked about, animated highlights, and the webcam PiP held still in its
original place. Output is a V2 clip at timeline resolution. It works on the source's own YUV planes - no colour
conversion anywhere - so a frame at rest is bit-identical to V1 and the hard cuts in and out of it are invisible.

Beat (edit_plan.json):
  {"id": "z03", "kind": "zoom", "t0": 5.30, "t1": 13.50,               programme seconds (snap to frames)
   "cam":   [{"t": 0.35, "dur": 0.8, "fx": 1300, "fy": 620, "k": 1.45, "ease": "power2.inOut"},
             {"t": 6.90, "dur": 0.8, "k": 1.0}],                        t beat-relative; fx/fy SOURCE px at the frame
                                                                        centre; k = zoom vs full frame (1 = V1 framing);
                                                                        "dur": 0 = an instant punch-in on a cut
   "marks": [{"t": 2.1, "t_out": 6.8, "type": "band", "rect": [610, 560, 1560, 80]}],   rect in SOURCE px
   "pip": "keep" | "none",                                              default: keep when the source has a PiP
   "sfx": [{"t": 3.2, "type": "click"}]}                                only visible presses (audio.py reads these)
Mark types: box (clay outline, lands with a small settle), band (marker-pen sweep; a wash on dark UI, a multiply
tint on light pages), spot (dims everything else), underline (a sweeping clay bar under the rect).
Frames that move get a 4-sample 270-degree shutter (motion blur); frames at rest are sharp.

usage: python scripts/zoom.py z01 [z02 ...] [--preview 1.0,3.5] [--x264] [--tag v2]   -> media/<id>[_v2].mp4 (or preview/<id>_<t>.png)
       (NVENC is used when available; --x264 forces the software encoder)"""
import sys, os, json
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as M
TAG = ('_' + sys.argv[sys.argv.index('--tag') + 1]) if '--tag' in sys.argv else ''   # edits: a new file, then replace_clip

SUB = 4                     # motion-blur samples across a 270-degree shutter


def cam_state(b, t, W, H, kfit):
    s = dict(fx=W / 2, fy=H / 2, k=1.0)
    if b.get('cam0'): s.update(b['cam0'])
    for m in b.get('cam', []):
        if t < m['t']: break
        d = m.get('dur', 0.7)
        p = 1.0 if d <= 0 else min(1.0, (t - m['t']) / d)
        e = M.ease(m.get('ease', 'power2.inOut'))(p)
        to = dict(fx=m.get('fx', s['fx']), fy=m.get('fy', s['fy']), k=m.get('k', s['k']))
        if p < 1:
            s = dict(fx=s['fx'] + (to['fx'] - s['fx']) * e, fy=s['fy'] + (to['fy'] - s['fy']) * e, k=s['k'] * (to['k'] / s['k']) ** e)
            break
        s = to
    kk = s['k'] * kfit
    hw, hh = C.TW / 2 / kk, C.TH / 2 / kk                      # clamp: the view never leaves the source
    fx = min(max(s['fx'], hw), W - hw) if W > 2 * hw + 1e-6 else W / 2
    fy = min(max(s['fy'], hh), H - hh) if H > 2 * hh + 1e-6 else H / 2
    return fx, fy, kk


def rrect_mask(h, w, r):
    m = np.zeros((max(1, h), max(1, w)), np.uint8)
    r = int(max(1, min(r, h // 2, w // 2)))
    cv2.rectangle(m, (r, 0), (w - r - 1, h - 1), 255, -1); cv2.rectangle(m, (0, r), (w - 1, h - r - 1), 255, -1)
    for cx, cy in ((r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)):
        cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return m.astype(np.float32) / 255


class Painter:
    """draws marks on the SOURCE planes (so they zoom with the picture); sizes are layout px at rest"""

    def __init__(self, src, kfit):
        self.m, self.r = M.color(src)
        self.px = C.UNIT / kfit
        self.clay = M.rgb2yuv(C.CLAY, self.m, self.r)
        self.black = 16.0 if self.r == 'tv' else 0.0
        self.span = 219.0 if self.r == 'tv' else 255.0

    def blend(self, P, m_full, x0, y0, color):
        """P = [Y, U, V] float-safe copies; m_full: mask for Y region at (x0, y0) (even-aligned)"""
        h, w = m_full.shape
        Y = P[0][y0:y0 + h, x0:x0 + w].astype(np.float32)
        P[0][y0:y0 + h, x0:x0 + w] = np.clip(Y * (1 - m_full) + color[0] * m_full + 0.5, 0, 255).astype(np.uint8)
        mu = cv2.resize(m_full, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
        for c in (1, 2):
            pl = P[c][y0 // 2:y0 // 2 + h // 2, x0 // 2:x0 // 2 + w // 2].astype(np.float32)
            P[c][y0 // 2:y0 // 2 + h // 2, x0 // 2:x0 // 2 + w // 2] = np.clip(pl * (1 - mu) + color[c] * mu + 0.5, 0, 255).astype(np.uint8)

    def region(self, rect, pad, W, H):
        x, y, w, h = rect
        x0, y0 = max(0, int(x - pad)) // 2 * 2, max(0, int(y - pad)) // 2 * 2
        x1, y1 = min(W, int(np.ceil(x + w + pad))), min(H, int(np.ceil(y + h + pad)))
        x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
        return x0, y0, x1, y1

    def draw(self, P, marks, t, W, H):
        px = self.px
        for mk in marks:
            t0, t1 = mk['t'], mk.get('t_out', 1e9)
            if t < t0 or t > t1 + 0.3: continue
            pin = min(1.0, (t - t0) / mk.get('dur', 0.45)); pout = 1 - min(1.0, max(0.0, (t - t1) / 0.25))
            typ = mk.get('type', 'box')
            if typ == 'spot':
                a = 0.45 * M.ease('power2.out')(pin) * pout
                x0, y0, x1, y1 = self.region(mk['rect'], 10 * px, W, H)
                mask = np.zeros((H, W), np.float32)
                mask[y0:y1, x0:x1] = rrect_mask(y1 - y0, x1 - x0, int(14 * px))
                mask = cv2.GaussianBlur(mask, (0, 0), 10 * px)
                f = 1 - a * (1 - mask)
                P[0][:] = np.clip(self.black + (P[0].astype(np.float32) - self.black) * f + 0.5, 0, 255).astype(np.uint8)
                fu = cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
                for c in (1, 2): P[c][:] = np.clip(128 + (P[c].astype(np.float32) - 128) * fu + 0.5, 0, 255).astype(np.uint8)
                continue
            pad = 8 * px if typ in ('box', 'band') else 0
            x0, y0, x1, y1 = self.region(mk['rect'], pad, W, H); rh, rw = y1 - y0, x1 - x0
            if rh < 2 or rw < 2: continue
            if typ == 'band':
                sweep = M.ease('power3.out')(pin)
                m = rrect_mask(rh, rw, int(8 * px)); m[:, int(rw * sweep):] = 0; m *= pout
                light = P[0][y0:y1, x0:x1].mean() > self.black + 0.6 * self.span
                if light:       # marker pen on a light page: multiply with a clay tint (exact, via RGB for this region)
                    rgb = M.yuv2rgb(P[0][y0:y1, x0:x1], P[1][y0 // 2:y1 // 2, x0 // 2:x1 // 2], P[2][y0 // 2:y1 // 2, x0 // 2:x1 // 2], self.m, self.r).astype(np.float32)
                    tint = np.array([248, 216, 200], np.float32) / 255
                    rgb = rgb * (1 - m[..., None]) + rgb * tint * m[..., None]
                    yuv = M.rgb2yuv(rgb, self.m, self.r)
                    P[0][y0:y1, x0:x1] = np.clip(yuv[..., 0] + 0.5, 0, 255).astype(np.uint8)
                    for c in (1, 2):
                        P[c][y0 // 2:y1 // 2, x0 // 2:x1 // 2] = np.clip(cv2.resize(yuv[..., c], (rw // 2, rh // 2), interpolation=cv2.INTER_AREA) + 0.5, 0, 255).astype(np.uint8)
                else:           # dark UI: a translucent clay wash
                    self.blend(P, 0.28 * m, x0, y0, self.clay)
            elif typ == 'underline':
                sweep = M.ease('power3.out')(pin)
                bh = max(2, int(4 * px)) // 2 * 2
                m = np.zeros((rh, rw), np.float32); m[rh - bh:, :int(rw * sweep)] = pout
                self.blend(P, m, x0, y0, self.clay)
            else:               # box: clay outline + faint fill, lands with a small settle
                e = M.ease('power3.out')(pin); a = min(1.0, pin * 2.5) * pout
                grow = (1 - e) * 0.04; gx, gy = int(rw * grow / 2), int(rh * grow / 2)
                sub = rrect_mask(rh - 2 * gy, rw - 2 * gx, int(12 * px))
                outer = np.zeros((rh, rw), np.float32); outer[gy:gy + sub.shape[0], gx:gx + sub.shape[1]] = sub
                bw = max(2, int(3 * px)); inner = np.zeros_like(outer)
                ih, iw = sub.shape[0] - 2 * bw, sub.shape[1] - 2 * bw
                if ih > 0 and iw > 0: inner[gy + bw:gy + bw + ih, gx + bw:gx + bw + iw] = rrect_mask(ih, iw, max(1, int(12 * px) - bw))
                self.blend(P, 0.14 * a * inner, x0, y0, self.clay)
                self.blend(P, np.clip(outer - inner, 0, 1) * a, x0, y0, self.clay)


_FILL = {}


def fill_pip(P, win, key=None):
    """replace the source PiP window with an inpainted patch so zoomed views never show a second, bigger face.
    The patch sits under the held-still PiP, so it is computed once per V1 item (key) and reused."""
    x, y, w, h = win
    if key is not None and key in _FILL:
        for c, s in ((0, 1), (1, 2), (2, 2)):
            P[c][y // s:(y + h) // s, x // s:(x + w) // s] = _FILL[key][c]
        return
    for c, s in ((0, 1), (1, 2), (2, 2)):
        pl = P[c]; H_, W_ = pl.shape; g = 48 // s
        xs, ys, ws, hs = x // s, y // s, w // s, h // s
        x0, y0, x1, y1 = max(0, xs - g), max(0, ys - g), min(W_, xs + ws + g), min(H_, ys + hs + g)
        reg = pl[y0:y1, x0:x1]; q = 4
        small = cv2.resize(reg, ((x1 - x0) // q, (y1 - y0) // q), interpolation=cv2.INTER_AREA)
        mask = np.zeros(small.shape, np.uint8)
        mask[(ys - y0) // q:(ys - y0 + hs) // q + 1, (xs - x0) // q:(xs - x0 + ws) // q + 1] = 255
        inp = cv2.GaussianBlur(cv2.inpaint(small, mask, 6, cv2.INPAINT_TELEA), (0, 0), 3)
        big = cv2.resize(inp, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
        pl[ys:ys + hs, xs:xs + ws] = big[ys - y0:ys - y0 + hs, xs - x0:xs - x0 + ws]
    if key is not None:
        _FILL[key] = [P[c][y // s:(y + h) // s, x // s:(x + w) // s].copy() for c, s in ((0, 1), (1, 2), (2, 2))]


def warp(P, states):
    """warp the three planes for each camera sample and average them (the shutter)"""
    out = []
    for c, s in ((0, 1), (1, 2), (2, 2)):
        tw, th = C.TW // s, C.TH // s
        acc = None
        for fx, fy, kk in states:
            A = np.float32([[kk, 0, tw / 2 - kk * fx / s], [0, kk, th / 2 - kk * fy / s]])
            w_ = cv2.warpAffine(P[c], A, (tw, th), flags=cv2.INTER_LINEAR if len(states) > 1 else cv2.INTER_CUBIC,
                                borderMode=cv2.BORDER_REPLICATE)
            acc = w_.astype(np.float32) if acc is None else acc + w_
        out.append(np.clip(acc / len(states) + 0.5, 0, 255).astype(np.uint8) if len(states) > 1 else w_)
    return out


def render(bid, preview=None, nvenc=None):
    b = M.beat(bid)
    f0, f1 = M.frames_of(b['t0'], b['t1'])
    seq = M.source_map(f0, f1)
    kinds = scene_kinds(seq)
    if len({s[0] for s in seq}) > 1 or len(kinds) > 1:
        print(f'WARN {bid}: spans {len({s[0] for s in seq})} source files / scenes {sorted(kinds)} - a zoom should stay inside one scene')
    src = seq[0][0]; p = M.probe(src); W, H = p['width'], p['height']
    kfit = min(C.TW / W, C.TH / H)
    S = json.load(open('scenes.json')) if os.path.exists('scenes.json') else {'files': {}}
    win = (S['files'].get(src) or {}).get('pip')
    keep = bool(win) and b.get('pip', 'keep') == 'keep'
    if keep: win = [v // 2 * 2 for v in win]
    marks = b.get('marks', []); painter = Painter(src, kfit)
    if keep:                                                     # rounded paste masks, one per plane size
        Wo_, Ho_ = int(round(win[2] * kfit)), int(round(win[3] * kfit))
        pm = M.pip_mask(Wo_, Ho_); pmask = [pm, cv2.resize(pm, (Wo_ // 2, Ho_ // 2), interpolation=cv2.INTER_AREA)]
        pmask.append(pmask[1])
    want = None if preview is None else {int(round(t * C.FPS)) for t in preview}
    os.makedirs(C.MEDIA, exist_ok=True); os.makedirs('preview', exist_ok=True)
    out = os.path.join(C.MEDIA, f'{bid}{TAG}.mp4')
    enc = None if want is not None else M.yuv_encoder(out, C.TW, C.TH, src, nvenc=nvenc)
    N = f1 - f0; moving_frames = 0; passthrough = 0
    for n, planes in enumerate(M.decode(seq, W, H, yuv=True)):
        item = seq[n][1]['v1']
        if want is not None and n not in want:
            if n > max(want): break
            continue
        t = n / C.FPS
        states = [cam_state(b, t + (j - (SUB - 1) / 2) * 0.75 / (SUB * C.FPS), W, H, kfit) for j in range(SUB)]
        a, z = states[0], states[-1]
        moving = abs(a[0] - z[0]) * a[2] > 0.35 or abs(a[1] - z[1]) * a[2] > 0.35 or abs(a[2] / z[2] - 1) > 2e-4
        fx, fy, kk = cam_state(b, t, W, H, kfit)
        zoomed = kk > kfit * 1.0005 or moving
        active = [mk for mk in marks if mk['t'] <= t <= mk.get('t_out', 1e9) + 0.3]
        identity = (W, H) == (C.TW, C.TH) and not zoomed
        if identity and not active:
            outp = planes; passthrough += 1
        else:
            P = [pl.copy() for pl in planes]
            painter.draw(P, active, t, W, H)
            if keep and zoomed: fill_pip(P, win, item)
            if identity: outp = P
            elif not zoomed:                                     # a smaller timeline at rest: plain area downscale
                outp = [cv2.resize(pl, (C.TW // s, C.TH // s), interpolation=cv2.INTER_AREA) for pl, s in zip(P, (1, 2, 2))]
            else: outp = warp(P, states if moving else [(fx, fy, kk)])
            if moving: moving_frames += 1
            if keep and zoomed:                                  # the webcam stays exactly where V1 has it
                x, y, w, h = win
                for c, s in ((0, 1), (1, 2), (2, 2)):
                    crop = planes[c][y // s:(y + h) // s, x // s:(x + w) // s]
                    X, Y, Wo, Ho = [int(round(v * kfit / s)) for v in (x, y, w, h)]
                    if kfit != 1: crop = cv2.resize(crop, (Wo, Ho), interpolation=cv2.INTER_AREA)
                    a = pmask[c]
                    dst = outp[c][Y:Y + Ho, X:X + Wo].astype(np.float32)
                    outp[c][Y:Y + Ho, X:X + Wo] = np.clip(dst * (1 - a) + crop * a + 0.5, 0, 255).astype(np.uint8)
        if want is not None:
            m_, r_ = M.color(src)
            cv2.imwrite(f'preview/{bid}_{t:06.2f}.png', cv2.cvtColor(M.yuv2rgb(*outp, m_, r_), cv2.COLOR_RGB2BGR))
        else:
            for pl in outp: enc.stdin.write(np.ascontiguousarray(pl).tobytes())
    if enc:
        enc.stdin.close(); enc.wait()
        print(f'{bid}: {N} frames ({N / C.FPS:.2f}s) -> {out} | {passthrough} untouched, {moving_frames} motion-blurred | pip {"kept" if keep else "none"}')
    else:
        print(f'{bid}: previews in preview/{bid}_*.png')


def scene_kinds(seq):
    S = json.load(open('scenes.json')) if os.path.exists('scenes.json') else {'items': {}}
    return {S['items'].get(str(it['v1']), {}).get('scene', 'unknown') for _, it, _ in seq[::30]}


if __name__ == '__main__':
    argv = sys.argv[1:]; prev = None
    if '--tag' in argv: k = argv.index('--tag'); argv = argv[:k] + argv[k + 2:]
    if '--preview' in argv:
        k = argv.index('--preview'); prev = [float(x) for x in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
    for bid in [a for a in argv if not a.startswith('--')]:
        render(bid, prev, False if '--x264' in argv else None)
