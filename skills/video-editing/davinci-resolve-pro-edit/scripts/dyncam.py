"""The dynamic camera for SEPARATE webcam + desktop recordings: the webcam as a rounded window that morphs between
full frame, a large side card, a small corner window and hidden, on eased moves, over the content layer (the Pro Edit
rendered without its camera, facecam and overlay tracks). Proven on abacus-test (Pro Edit v3, 2026-11-01): see
references/dynamic-camera.md for the rules and the research, lessons.md for every bug below.

The model is the one Resolve's Picture in Picture effect uses: a window (rect + corner radius) and, inside it, the
webcam at ONE uniform scale centred on one webcam point. The crop is derived from the window and the scale every frame
- never interpolated on its own - so the face can't squash. Scale interpolates geometrically, everything else
linearly, on a quad ease-in-out. Drawing is sub-pixel (cv2.warpAffine); the mask is a true signed-distance rounded box
(opaque inside at any radius: v2's mask went half transparent below r 0.5 px - the "flicker"); a light motion blur
(4 samples over a 0.2-frame shutter, FORWARD from the frame only) on moving frames; frames at rest are sharp.

Inputs (cwd = W): program.json (the webcam frame under every programme frame: items' audio_file / audio_t0),
$M/_deliver/content.mp4 + tracks.json (rs_content.py: the content layer and the timeline's tracks, for the punch-ins on
the camera track), dyncam_cfg.json (`dyncam.py cfg`), dyncam_plan.json (`dyncam_plan.py draft`, then edited and
`dyncam_plan.py check`ed). Output: $M/layout_<tag>.mp4 (built from resumable 1800-frame chunks in $M/_dyncam_<tag>/).

usage:
  python scripts/dyncam.py cfg                         # face position in the webcam -> dyncam_cfg.json (window geometry)
  python scripts/dyncam.py --preview 12.5,40.2         # preview/dyncam_<t>.jpg (programme seconds)
  python scripts/dyncam.py --strip 39.6 40             # 40 consecutive frames from 39.6 s: step through every move
  python scripts/dyncam.py --jobs 8 [--tag v1]         # the whole layer (4K60, 8 parts in parallel: ~30 min for 9 min)
  python scripts/dyncam.py patch [--keys 19.0167,353.5667] [--tag v1]
                                                       # re-render +-3 frames around every key (or the listed keys) into
                                                       # the existing chunks after a plan or code fix, then re-concatenate
Plan keys: {"t": s, "dur": s, "to": "FULL|CARD|SMALL|HIDDEN", "corner": "tr|br|bl|tl", "content": "stem|image:<png>",
"hold": true}. Key times are snapped to the frame grid on load (353.5667 s is a hair AFTER frame 21214: unsnapped, the
move's first blur sample counted as "before the key" and blended the incoming shot in)."""
import json, os, sys, subprocess, bisect, functools
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as Mx

FPS, TW, TH = C.FPS, C.TW, C.TH
S = C.UNIT                                                   # output px per layout px
LW, LH = float(C.LAYOUT_W), float(C.LAYOUT_H)
FULLR = (0.0, 0.0, LW, LH)
TAG = sys.argv[sys.argv.index('--tag') + 1] if '--tag' in sys.argv else 'v1'
DELIVER = os.path.join(C.MEDIA, '_deliver')
CONTENT = sys.argv[sys.argv.index('--content') + 1] if '--content' in sys.argv else os.path.join(DELIVER, 'content.mp4')
PROG = json.load(open('program.json', encoding='utf-8'))
TOTAL = PROG['frames']


@functools.lru_cache(None)
def vinfo(path):
    """(width, height, fps) of a video file"""
    o = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate',
                                   '-of', 'json', path], capture_output=True, text=True).stdout)['streams'][0]
    a, b = o['r_frame_rate'].split('/')
    return int(o['width']), int(o['height']), float(a) / float(b)


# ---------------------------------------------------------------- the webcam under every programme frame
VOICE = sorted([it for it in PROG['items'] if it.get('audio_file')], key=lambda it: it['rec0'])
VST = [it['rec0'] for it in VOICE]


def cam_src(n):
    """(webcam file, webcam frame) shown at programme frame n: the webcam's own audio is the voice (A1), so the
    picture under it is the same file at the same time"""
    k = bisect.bisect_right(VST, n) - 1
    if k < 0 or n >= VOICE[k]['rec1']: return None
    it = VOICE[k]; cfps = vinfo(it['audio_file'])[2]
    return it['audio_file'], int(round(it['audio_t0'] * cfps)) + int(round((n - it['rec0']) * cfps / FPS))


CAM_W, CAM_H = vinfo(VOICE[0]['audio_file'])[:2] if VOICE else (TW, TH)


def face_cfg():
    """measure the face in the webcam (YuNet, ~24 frames across the programme) and derive the window geometry: eyes in
    the upper third of every window, the same framing as abacus-test v3 scaled to this face and webcam"""
    sys.path.insert(0, 'scripts'); import faces
    R = Reader(); boxes = []
    try:
        for n in np.linspace(0, TOTAL - 1, 24).astype(int):
            cs = cam_src(int(n))
            if not cs: continue
            img = R.get(cs[0], cs[1], CAM_W, CAM_H); R.close()
            f = faces.detect(cv2.cvtColor(np.ascontiguousarray(img), cv2.COLOR_RGB2BGR))
            if f: boxes.append(f[0][:4])
    finally:
        R.close()
    if not boxes: sys.exit('no face found in the webcam frames - set dyncam_cfg.json by hand (see the abacus values in dynamic-camera.md)')
    x, y, w, h = np.median(np.array(boxes), axis=0)
    fx, fy = x + w / 2, y + h / 2
    # ratios to the YuNet box, from the abacus v3 framing the user approved (box 504x568 at 1768,612 in a 4K webcam ->
    # small square 1800 px centred at y 1164, card 2100 px tall centred at y 1110): eyes ~30% down the small window
    k = CAM_H / 2160.0
    small_crop = float(np.clip(h * 3.17, 900 * k, 2100 * k)) # the square the small window shows, in webcam px
    card_h = float(min(CAM_H, h * 3.70))
    clampx = lambda cx, w: float(np.clip(cx, w / 2, CAM_W - w / 2))
    clampy = lambda cy, h: float(np.clip(cy, h / 2, CAM_H - h / 2))
    cfg = dict(face=[round(fx), round(fy)], face_box=[round(v) for v in (x, y, w, h)], webcam=[CAM_W, CAM_H],
               small=384, margin=40, small_crop=round(small_crop), small_center=[round(clampx(fx, small_crop)), round(clampy(fy + 0.47 * h, small_crop))],
               small_radius=22, card=[1100, 72, 756, 936], card_crop_h=round(card_h),
               card_center=[round(clampx(fx, card_h * 756 / 936)), round(clampy(fy + 0.377 * h, card_h))], card_radius=22,
               panel=[64, 258, 1000, 562.5], panel_radius=16, default_corner='tr', camera_tracks=['Camera'])
    old = json.load(open('dyncam_cfg.json')) if os.path.exists('dyncam_cfg.json') else {}
    cfg.update({k: v for k, v in old.items() if k in ('camera_tracks', 'default_corner')})
    json.dump(cfg, open('dyncam_cfg.json', 'w'), indent=1)
    print(f'face box {cfg["face_box"]} in a {CAM_W}x{CAM_H} webcam ({len(boxes)} frames) -> dyncam_cfg.json; LOOK at a --preview of each state')


# ---------------------------------------------------------------- plan and geometry
CFG = json.load(open('dyncam_cfg.json')) if os.path.exists('dyncam_cfg.json') else None
PLAN = json.load(open('dyncam_plan.json')) if os.path.exists('dyncam_plan.json') else None
KEYS = sorted(PLAN['keys'], key=lambda k: k['t']) if PLAN else []
for _k in KEYS: _k['t'] = round(_k['t'] * FPS) / FPS     # snap to the frame grid (see the docstring)
DEFC = (CFG or {}).get('default_corner', 'tr')


def _camera_items():
    """camera-track items with their punch-in (ZoomX, Pan, Tilt in timeline px) from rs_content.py's tracks.json"""
    p = os.path.join(DELIVER, 'tracks.json')
    if not os.path.exists(p) or not CFG: return []
    T = json.load(open(p, encoding='utf-8')); names = set(CFG.get('camera_tracks', ['Camera']))
    return sorted([it for tr in T['video'] if tr['name'] in names for it in tr['items']], key=lambda i: i['rec0'])


CAMITEMS = _camera_items()


def punch_at(n):
    for it in CAMITEMS:
        if it['rec0'] <= n < it['rec1']: return it.get('ZoomX', 1.0) or 1.0, it.get('Pan', 0.0) or 0.0, it.get('Tilt', 0.0) or 0.0
    return 1.0, 0.0, 0.0


def state(st, corner, n_land):
    """window rect (layout px), video scale (layout px per webcam px), webcam point at the window centre, radius,
    opacity; content rect and radius. n_land: the frame whose shot sets the FULL framing (its punch-in)"""
    if st == 'FULL':                                         # the camera item's own punch: Resolve zooms about the centre,
        z, pan, tilt = punch_at(n_land); st_ = TW / CAM_W    # Pan +right, Tilt +up, in timeline px
        return dict(r=FULLR, s=LW / CAM_W * z, c=(CAM_W / 2 - pan / (z * st_), CAM_H / 2 + tilt / (z * st_)), rad=0.0, a=1.0, cr=FULLR, crad=0.0)
    if st == 'CARD':
        r = tuple(CFG['card']); return dict(r=r, s=r[3] / CFG['card_crop_h'], c=tuple(CFG['card_center']), rad=CFG['card_radius'],
                                             a=1.0, cr=tuple(CFG['panel']), crad=CFG['panel_radius'])
    sz = CFG['small']; m = CFG['margin']; corner = corner or DEFC
    x = m if corner[1] == 'l' else LW - m - sz; y = m if corner[0] == 't' else LH - m - sz
    s = sz / CFG['small_crop']
    if st == 'SMALL':
        return dict(r=(x, y, sz, sz), s=s, c=tuple(CFG['small_center']), rad=CFG['small_radius'], a=1.0, cr=FULLR, crad=0.0)
    k = 0.8                                                  # HIDDEN: a little smaller, faded, in its corner
    return dict(r=(x + sz * (1 - k) / 2, y + sz * (1 - k) / 2, sz * k, sz * k), s=s * k, c=tuple(CFG['small_center']), rad=CFG['small_radius'] * k,
                a=0.0, cr=FULLR, crad=0.0)


def ease(p):                                                 # quad in-out: peak speed 2x the average (cubic's 3x smeared)
    p = min(1.0, max(0.0, p))
    return 2 * p * p if p < 0.5 else 1 - 2 * (1 - p) ** 2


def mix(g0, g1, e):
    out = {}
    for k in g0:
        a, b = g0[k], g1[k]
        if k == 's': out[k] = a * (b / a) ** e               # scale interpolates geometrically: constant-feeling zoom
        elif isinstance(a, tuple): out[k] = tuple(x + (y - x) * e for x, y in zip(a, b))
        else: out[k] = a + (b - a) * e
    return out


def at(t):
    """geometry at programme time t (seconds, may be a sub-frame time), the content source and the frame it started
    on, and a held content frame if any"""
    n = int(np.floor(t * FPS + 1e-6))
    prev, cur = PLAN['start'], None
    for k in KEYS:
        if t < k['t']: break
        if t < k['t'] + k['dur']: cur = k; break
        prev = k
    content, c0 = 'stem', 0
    for k in KEYS:
        if k is cur or k['t'] > t: break
        if 'content' in k: content, c0 = k['content'], int(round(k['t'] * FPS))
    if cur is not None and 'content' in cur: content, c0 = cur['content'], int(round(cur['t'] * FPS))
    land = lambda k: int(round((k['t'] + k['dur']) * FPS)) if k is not PLAN['start'] else 0
    g0 = state(prev['to'], prev.get('corner'), max(land(prev), n) if prev['to'] == 'FULL' else n)
    if cur is None: return g0, (content, c0), None
    g1 = state(cur['to'], cur.get('corner'), land(cur))
    if prev['to'] == 'FULL': g0 = state('FULL', None, int(round(cur['t'] * FPS)) - 1)   # leave from the outgoing framing
    e = ease((t - cur['t']) / cur['dur'])
    hold = int(round(cur['t'] * FPS)) - 1 if cur.get('hold') else None   # a grow holds the outgoing shot's last frame
    return mix(g0, g1, e), (content, c0), hold


# ---------------------------------------------------------------- drawing (all sub-pixel)
def rbox_alpha(w, h, fx, fy, rw, rh, rad):
    """coverage of a rounded rectangle (offset fx,fy; size rw,rh; radius rad) in a w x h buffer - signed distance,
    1 inside at any radius (v2's formula gave 0.5 + r inside when r < 0.5: the ghost frames)"""
    rad = max(0.0, min(rad, rw / 2, rh / 2))
    ys = np.arange(h, dtype=np.float32)[:, None] + 0.5 - fy; xs = np.arange(w, dtype=np.float32)[None, :] + 0.5 - fx
    qx = np.abs(xs - rw / 2) - (rw / 2 - rad); qy = np.abs(ys - rh / 2) - (rh / 2 - rad)
    d = np.sqrt(np.maximum(qx, 0) ** 2 + np.maximum(qy, 0) ** 2) + np.minimum(np.maximum(qx, qy), 0) - rad
    return np.clip(0.5 - d, 0, 1)


def place(canvas, src, sx, sy, sw, sh, rect, rad, alpha, shade, rim=0.0):
    """draw src region (sx,sy,sw,sh in src px, floats) into rect (x,y,w,h in output px, floats), rounded, with a shadow"""
    x, y, w, h = rect
    if w < 1 or h < 1 or alpha <= 0.002: return
    X0, Y0 = max(0, int(np.floor(x))), max(0, int(np.floor(y))); X1, Y1 = min(TW, int(np.ceil(x + w))), min(TH, int(np.ceil(y + h)))
    if X1 <= X0 or Y1 <= Y0: return
    if shade > 0.01: shadow(canvas, x, y, w, h, shade * alpha)
    k = w / sw                                               # output px per src px (uniform)
    img = src
    if k < 0.6:                                              # pre-shrink so the warp does not alias
        f = max(1, int(0.75 / k)); img = cv2.resize(src, (src.shape[1] // f, src.shape[0] // f), interpolation=cv2.INTER_AREA)
        sx, sy, sw, sh, k = sx / f, sy / f, sw / f, sh / f, k * f
    M = np.float32([[k, 0, x - X0 - sx * k], [0, k, y - Y0 - sy * k]])
    patch = cv2.warpAffine(img, M, (X1 - X0, Y1 - Y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    m0 = rbox_alpha(X1 - X0, Y1 - Y0, x - X0, y - Y0, w, h, rad)
    m = m0[..., None] * alpha
    reg = canvas[Y0:Y1, X0:X1].astype(np.float32)
    px = reg * (1 - m) + patch.astype(np.float32) * m
    if rim > 0 and min(w, h) < TW * 0.98:                    # hairline rim, inset 3 px (none at full frame)
        inner = rbox_alpha(X1 - X0, Y1 - Y0, x - X0 + 3, y - Y0 + 3, w - 6, h - 6, max(0.0, rad - 3))
        ring = np.clip(m0 - inner, 0, 1)[..., None] * rim * alpha
        px = px * (1 - ring) + 255.0 * ring
    canvas[Y0:Y1, X0:X1] = (px + 0.5).astype(np.uint8)


def shadow(canvas, x, y, w, h, strength):
    q = 8; pad = max(w, h) * 0.12 + 40
    X0, Y0 = max(0, int(x - pad)), max(0, int(y - pad)); X1, Y1 = min(TW, int(x + w + pad)), min(TH, int(y + h + pad + h * 0.04))
    if X1 <= X0 or Y1 <= Y0: return
    sw, sh = max(1, (X1 - X0) // q), max(1, (Y1 - Y0) // q)
    m = np.zeros((sh, sw), np.float32)
    cv2.rectangle(m, (int((x - X0) / q), int((y - Y0 + h * 0.025) / q)), (int((x - X0 + w) / q), int((y - Y0 + h * 1.025) / q)), 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), max(1.0, w * 0.035 / q))
    m = cv2.resize(m, (X1 - X0, Y1 - Y0), interpolation=cv2.INTER_LINEAR) * strength
    reg = canvas[Y0:Y1, X0:X1].astype(np.float32)
    canvas[Y0:Y1, X0:X1] = (reg * (1 - m[..., None])).astype(np.uint8)


def stage_bg():
    """the graphite stage behind the CARD layout (the design system's stage, with its dot grid)"""
    ys, xs = np.mgrid[0:TH, 0:TW].astype(np.float32)
    top = np.array([24, 25, 28], np.float32); bot = np.array([11, 12, 14], np.float32)
    g = (ys / TH)[..., None]; img = top * (1 - g) + bot * g
    light = np.exp(-(((xs - TW * 0.38) / (TW * 0.5)) ** 2 + ((ys + TH * 0.1) / (TH * 0.7)) ** 2))[..., None] * 10
    vig = (1 - 0.35 * (((xs - TW / 2) / (TW / 2)) ** 2 + ((ys - TH / 2) / (TH / 2)) ** 2))[..., None]
    img = (img + light) * np.clip(vig, 0.6, 1)
    d = int(32 * S)
    dots = ((xs.astype(int) % d < 3) & (ys.astype(int) % d < 3))[..., None] * 6
    return np.clip(img + dots, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- sources
class Reader:
    """sequential frame reader that restarts ffmpeg only on a jump; a repeated frame (a 30 fps webcam on a 60 fps
    timeline) is served from the last one"""
    def __init__(self): self.f = None; self.next = None; self.p = None; self.last = None
    def get(self, f, frame, w, h):
        if self.f == f and self.last is not None and frame == self.next - 1: return self.last
        if self.f != f or self.next != frame:
            self.close()
            fps = vinfo(f)[2]
            self.p = Mx.reader_proc(['ffmpeg', '-v', 'error', '-ss', f'{max(0.0, (frame - 0.25) / fps):.5f}', '-i', f,
                                     '-vf', Mx.dec_vf(f), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
            self.f, self.next = f, frame
        b = Mx.read_exact(self.p.stdout, w * h * 3); self.next += 1
        if b is None: raise RuntimeError(f'{f}: no frame {frame}')
        self.last = np.frombuffer(b, np.uint8).reshape(h, w, 3)
        return self.last
    def close(self):
        if self.p:
            self.p.stdout.close(); self.p.kill() if self.p.poll() is None else None; self.p.wait(); self.p = None
        self.f = self.next = self.last = None


_imgs = {}
def image(path, n, k0):
    """a still (a captured page) for the CARD panel, with a slow 6% push over 7.3 s from the frame it starts on"""
    if path not in _imgs: _imgs[path] = cv2.cvtColor(cv2.imread(path, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
    im = _imgs[path]; hh, ww = im.shape[:2]
    k = 1.0 + 0.06 * min(1.0, max(0.0, (n - k0) / (7.3 * FPS)))
    ch = min(hh, ww * 9 / 16) / k; cw = ch * 16 / 9; cx0 = (ww - cw) * 0.12; cy0 = (hh - ch) * 0.5
    return cv2.resize(im[int(cy0):int(cy0 + ch), int(cx0):int(cx0 + cw)], (TW, TH), interpolation=cv2.INTER_AREA)


def draw(g, content_img, cam_img, bg):
    full_content = g['cr'] == FULLR
    if g['r'] == FULLR and g['a'] >= 0.999 and g['rad'] < 0.01 and cam_img is not None:
        out = np.empty((TH, TW, 3), np.uint8); out[:] = 0          # the camera covers everything
    elif full_content:
        out = content_img.copy()
    else:
        out = bg.copy()
        cr = tuple(v * S for v in g['cr'])
        place(out, content_img, 0, 0, TW, TH, cr, g['crad'] * S, 1.0, 0.55)
    if cam_img is not None and g['a'] > 0.002:
        r = tuple(v * S for v in g['r'])
        sw, sh = g['r'][2] / g['s'], g['r'][3] / g['s']              # webcam px shown
        sx = min(max(0.0, g['c'][0] - sw / 2), CAM_W - sw); sy = min(max(0.0, g['c'][1] - sh / 2), CAM_H - sh)
        full = (g['r'][2] * g['r'][3]) / (LW * LH)
        place(out, cam_img, sx, sy, sw, sh, r, g['rad'] * S, g['a'], 0.5 * (1 - full), rim=0.28 * (1 - full) ** 0.5)
    return out


class Frames:
    """content (with held frames) and webcam frames for programme frame n"""
    def __init__(self):
        self.cont, self.cam, self.held = Reader(), Reader(), {}
        self.bg = stage_bg()
    def content(self, n, content, hold, stream_frame):
        if content[0].startswith('image:'): return image(content[0][6:], n, content[1])
        if hold is None: return stream_frame
        if hold not in self.held:
            r = Reader(); self.held = {hold: r.get(CONTENT, hold, TW, TH).copy()}; r.close()
        return self.held[hold]
    def camera(self, n):
        cs = cam_src(n)
        return self.cam.get(cs[0], cs[1], CAM_W, CAM_H) if cs else None
    def close(self): self.cont.close(); self.cam.close()


SUB = 4; SHUTTER = 0.2                      # light blur (~70 degrees): Resolve's PiP effect uses none
def render(n, F):
    stream = F.cont.get(CONTENT, n, TW, TH)
    cam = F.camera(n)
    g, content, hold = at(n / FPS)
    moving = at((n + SHUTTER) / FPS)[0] != g
    if not moving:
        return draw(g, F.content(n, content, hold, stream), cam, F.bg)
    acc = np.zeros((TH, TW, 3), np.float32)
    for i in range(SUB):                                          # motion blur: sub-frame samples over the shutter
        # forward from the frame time only: a sample before a key would blend the previous layout (and, at a cut,
        # the previous shot) into the move's first frame - the abacus v3 first-render flashes
        ts = (n + i / SUB * SHUTTER) / FPS
        gi, ci, hi = at(ts)
        acc += draw(gi, F.content(n, ci, hi, stream), cam, F.bg)
    return (acc / SUB + 0.5).astype(np.uint8)


# ---------------------------------------------------------------- the layer: chunks, patching, concatenation
PARTS = os.path.join(C.MEDIA, f'_dyncam_{TAG}'); SIZE = 1800
OUT = os.path.join(C.MEDIA, f'layout_{TAG}.mp4')


def chunk(job):
    f0, f1, out_path = job
    F = Frames(); enc = Mx.encoder(out_path, TW, TH, None)
    try:
        for n in range(f0, f1): enc.stdin.write(np.ascontiguousarray(render(n, F)).tobytes())
    finally:
        F.close(); enc.stdin.close(); enc.wait()
    return out_path


def fix_chunk(job):
    """decode an existing chunk, re-render only the listed frames, re-encode (one extra cq-15 generation, this chunk only)"""
    f0, f1, path, frames = job
    tmp = path.replace('.mp4', '_fix.mp4')
    F = Frames(); old = Reader(); enc = Mx.encoder(tmp, TW, TH, None)
    try:
        for n in range(f0, f1):
            img = old.get(path, n - f0, TW, TH)
            if n in frames: img = render(n, F)
            enc.stdin.write(np.ascontiguousarray(img).tobytes())
    finally:
        F.close(); old.close(); enc.stdin.close(); enc.wait()
    os.replace(tmp, path)
    return path, len([n for n in frames if f0 <= n < f1])


def count_frames(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-count_packets', '-select_streams', 'v:0', '-show_entries', 'stream=nb_read_packets',
                        '-of', 'csv=p=0', path], capture_output=True, text=True).stdout.strip()
    return int(r) if r.isdigit() else -1


def concat(jobs):
    lst = os.path.join(PARTS, 'parts.txt')
    open(lst, 'w').write(''.join(f"file '{j[2].replace(chr(92), '/')}'\n" for j in jobs))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', '-movflags', '+faststart', OUT], check=True)
    k = count_frames(OUT)
    print(f'{OUT}: {k} frames (expected {TOTAL})' + ('' if k == TOTAL else '  <- MISMATCH'))


if __name__ == '__main__':
    a = sys.argv
    if a[1:2] == ['cfg']:
        face_cfg(); sys.exit()
    if not (CFG and PLAN): sys.exit('dyncam_cfg.json and dyncam_plan.json first (dyncam.py cfg, dyncam_plan.py draft)')
    if not os.path.exists(CONTENT): sys.exit(f'{CONTENT} missing: render the content layer first (rs_content.py)')
    if '--preview' in a or '--strip' in a:
        os.makedirs('preview', exist_ok=True)
        if '--strip' in a:
            t0, k = float(a[a.index('--strip') + 1]), int(a[a.index('--strip') + 2]); ns = [int(round(t0 * FPS)) + i for i in range(k)]
        else:
            ns = [int(round(float(t) * FPS)) for t in a[a.index('--preview') + 1].split(',')]
        F = Frames()
        for n in ns:
            img = render(n, F)
            cv2.imwrite(f'preview/dyncam_{n / FPS:08.3f}.jpg', cv2.cvtColor(cv2.resize(img, (960, 540), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
        F.close(); print('previews written', len(ns), '-> preview/dyncam_*.jpg'); sys.exit()
    jobs_n = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 8
    os.makedirs(PARTS, exist_ok=True)
    jobs = [(s, min(TOTAL, s + SIZE), os.path.join(PARTS, f'part_{s:06d}.mp4')) for s in range(0, TOTAL, SIZE)]
    if a[1:2] == ['patch']:
        only = None
        if '--keys' in a: only = {int(round(float(v) * FPS)) for v in a[a.index('--keys') + 1].split(',')}
        P = set()
        for k in KEYS:                                       # +-3 frames around each move
            if only and int(round(k['t'] * FPS)) not in only: continue
            P.update(range(max(0, int(round(k['t'] * FPS)) - 3), min(TOTAL, int(round((k['t'] + k['dur']) * FPS)) + 4)))
        fj = [(s, e, p, {n for n in P if s <= n < e}) for s, e, p in jobs]
        fj = [j for j in fj if j[3]]
        if any(not os.path.exists(j[2]) for j in fj): sys.exit('render the layer first: patch works on existing chunks')
        print(len(P), 'frames to re-render in', len(fj), 'chunks', flush=True)
        with ProcessPoolExecutor(jobs_n) as ex:
            for p, k in ex.map(fix_chunk, fj): print('patched', os.path.basename(p), k, 'frames', flush=True)
        concat(jobs); sys.exit()
    todo = [j for j in jobs if not (os.path.exists(j[2]) and count_frames(j[2]) == j[1] - j[0])]   # resumable
    print(f'{len(jobs) - len(todo)} of {len(jobs)} parts complete; rendering {len(todo)}', flush=True)
    with ProcessPoolExecutor(jobs_n) as ex: list(ex.map(chunk, todo))
    concat(jobs)
