"""Censor a chat message (or any UI block) that shows sensitive text: find it on every programme frame, trace its
exact shape, and render a heavy blur of just that shape as an alpha clip for a top track ("PE Censor").

How it finds the block: templates of the sensitive words (cut from one reference frame, e.g. a fee, a payment
method, a name) are matched on every frame at half resolution (normalised cross-correlation: robust to reflowed lines,
scrolling, dimming). Where any template hits, the block's own flat background colour is flood-filled from the hit,
holes (the glyphs) are filled, and a scrolled block's faded edge (a header fade) is followed to its end. Popups
that cover the block have their own colour and border, so they stay sharp. Frames between hits inside one V1 item
get the union of their neighbours' masks (fade-in, fast scrolls), and a short pre/post-roll covers the block
animating in or out.

Beat (edit_plan.json):
  {"id": "x01", "kind": "censor", "t0": 441.0, "t1": 567.0,
   "ref": "censor/ref_450.0.png",                          a full-res frame showing the block
   "templates": {"fee": [1542, 1561, 125, 48], ...},       word boxes in the reference frame (source px)
   "thr": 0.78, "tol": 3, "block": 24}                     match threshold, colour tolerance, blur strength
   optional "hold" (45), "roll" (30): frames bridged between two detections / held beside a longer gap
usage: python scripts/censor.py ref T                      -> censor/ref_<T>.png (full-res programme frame, no grid)
       python scripts/censor.py track x01 [--jobs 12]      -> censor/<id>_track.json (per-frame shapes; prints coverage)
       python scripts/censor.py preview x01 t [t ...]      -> preview/<id>_<t>.png (the frame with the censor applied)
       python scripts/censor.py transition x01 MOV FIRST   V1 transitions: MOV = timeline frames FIRST.. rendered out
                                                           of Resolve; adds the track's transition_patches
       python scripts/censor.py render x01 [--tag v2]      -> media/<id>.mov (ProRes 4444 + alpha)
       python scripts/censor.py scan x01 T0 T1 [--step 3] [--gpu]   safety scan: any template hit outside the beat?
Run `track` before rendering any zoom inside the beat: zoom.py bakes the censor into its frames from the track file,
and `render` leaves the overlay clear wherever a zoom clip covers the block."""
import sys, os, json, bisect
from concurrent.futures import ProcessPoolExecutor
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as M

HALF = 2                       # detection at half resolution


def beat(bid):
    return M.beat(bid)


def templates(b):
    ref = cv2.imread(b['ref'])
    T = {}
    for k, (x, y, w, h) in b['templates'].items():
        p = 8
        g = cv2.cvtColor(ref[y - p:y + h + p, x - p:x + w + p], cv2.COLOR_BGR2GRAY)
        T[k] = cv2.resize(g, ((w + 2 * p) // HALF, (h + 2 * p) // HALF), interpolation=cv2.INTER_AREA)
    return T


def frames_seq(f0, f1):
    """[(n, file, item, src)] for every frame in [f0, f1); frames on a V1 transition come back with file None"""
    P = M.program(); items = P['items']; starts = [it['rec0'] for it in items]; out = []
    fx = P.get('nomedia', [])
    for n in range(f0, f1):
        if any(x['rec0'] <= n < x['rec1'] for x in fx): out.append((n, None, None, None)); continue
        k = bisect.bisect_right(starts, n) - 1
        if k < 0 or n >= items[k]['rec1']: out.append((n, None, None, None)); continue
        it = items[k]; out.append((n, it['file'], it, it['src0'] + (n - it['rec0'])))
    return out


def runs(seq):
    """contiguous source runs (one decode each)"""
    out, cur = [], []
    for s in seq:
        if s[1] is None:
            if cur: out.append(cur); cur = []
            continue
        if cur and (s[1] != cur[-1][1] or s[3] != cur[-1][3] + 1): out.append(cur); cur = []
        cur.append(s)
    if cur: out.append(cur)
    return out


def shape(rgb, hits, b):
    """the block's shape on one half-res frame, from the template hits: flat-colour flood + holes + faded edges"""
    tol = b.get('tol', 3)
    g = rgb[..., 1].astype(np.int16)
    gray = np.ascontiguousarray(rgb[..., 1])
    sat = (rgb.max(2).astype(np.int16) - rgb.min(2)) > 12
    v, c = np.unique(g[::4, ::4], return_counts=True); bg = int(v[np.argmax(c)])      # the page background
    modes = []
    for (k, x, y, w, h, s) in hits:
        vv, cc = np.unique(g[y:y + h, x:x + w], return_counts=True); modes.append(int(vv[np.argmax(cc)]))
    col = max(modes)                                            # the block's own colour (faded hits read darker)
    # flood with a floating range: walks smooth gradients (a header fade over the block) but stops at hard edges
    # (the block's border against the background, a popup's border, glyphs). Background and anything brighter than
    # the block are walls, so the flood can never leak into the page.
    ff = np.zeros((g.shape[0] + 2, g.shape[1] + 2), np.uint8)
    wall = (g <= bg + 1) | (g > col + tol) | sat
    ff[1:-1, 1:-1][wall] = 1
    for (k, x, y, w, h, s), md in zip(hits, modes):
        ys, xs = np.where((np.abs(g[y:y + h, x:x + w] - md) <= 1) & ~wall[y:y + h, x:x + w])
        for j in range(0, len(ys), max(1, len(ys) // 12)):
            px, py = int(x + xs[j]), int(y + ys[j])
            if ff[py + 1, px + 1] == 0:
                cv2.floodFill(gray, ff, (px, py), 0, 2, 2, 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8))
    m = (ff[1:-1, 1:-1] == 255).astype(np.uint8) * 255
    if not m.any(): return None, col
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))
    cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    m = np.zeros_like(m); cv2.drawContours(m, cs, -1, 255, -1)
    ys, xs = np.where(m > 0)
    if not len(ys): return None, col
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    if (x1 - x0) * (y1 - y0) > 0.35 * m.size:                 # flood ran into a whole panel: fall back to the hits
        m = np.zeros_like(m)
        for (k, x, y, w, h, s) in hits: cv2.rectangle(m, (x - 12, y - 12), (x + w + 12, y + h + 12), 255, -1)
        return m, col
    bg = np.median(np.concatenate([g[max(0, y0 - 6), x0:x1 + 1], g[min(g.shape[0] - 1, y1 + 6), x0:x1 + 1]]))
    # a block scrolled under a header fade: its rows keep going above the flat part, darker but still readable
    for direction, start in ((-1, y0), (1, y1)):
        r = start + direction; ext = []
        while 0 <= r < g.shape[0]:
            seg = g[r, x0 + 4:x1 - 4]
            med = np.median(seg)
            if med <= bg + 1.5 or med > col + 1.5: break
            ext.append(r); r += direction
        if ext and len(ext) < 0.25 * g.shape[0]:
            a, z = min(ext), max(ext)
            m[a:z + 1, x0:x1 + 1] = 255
    return m, col


def track_run(args):
    bid, run = args
    b = beat(bid); T = templates(b); thr = b.get('thr', 0.78)
    W, H = C.TW // HALF, C.TH // HALF
    seq = [(f, it, s) for (n, f, it, s) in run]
    out = {}
    for (n, f, it, s), fr in zip(run, M.decode(seq, W, H, f'scale={W}:{H}:flags=area')):
        gray = cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY)
        hits = []
        for k, t in T.items():
            r = cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(r)
            if mx >= thr: hits.append((k, loc[0], loc[1], t.shape[1], t.shape[0], round(float(mx), 3)))
        if not hits: continue
        m, col = shape(fr, hits, b)
        if m is None: continue
        cs, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        out[n] = dict(v1=it['v1'], col=col, hits=[h[0] + f'@{h[5]}' for h in hits],
                      poly=[(c.reshape(-1, 2) * HALF).tolist() for c in cs if cv2.contourArea(c) > 30])
    return out


def track(bid, jobs=12):
    b = beat(bid); f0, f1 = M.frames_of(b['t0'], b['t1'])
    seq = frames_seq(f0, f1); rs = runs(seq)
    # split long runs so the pool stays busy
    chunks = []
    for r in rs:
        for k in range(0, len(r), 240): chunks.append(r[k:k + 240])
    raw = {}
    with ProcessPoolExecutor(jobs) as ex:
        for d in ex.map(track_run, [(bid, c) for c in chunks]): raw.update(d)
    hold = b.get('hold', 45); roll = b.get('roll', 30)
    v1_of = {n: (it['v1'] if it else None) for (n, f, it, s) in seq}
    final = {}
    det = sorted(raw)
    for (n, f, it, s) in seq:
        if n in raw: final[n] = dict(src='det', polys=raw[n]['poly']); continue
        if it is None: continue
        same = [d for d in det if raw[d]['v1'] == it['v1']]
        i = bisect.bisect_left(same, n)
        prev = same[i - 1] if i > 0 else None; nxt = same[i] if i < len(same) else None
        use = []
        # bridge short gaps; around a longer gap (a modal over the block) hold each side for `roll` frames. No
        # pre-roll before the first detection in an item: the block fades in where the chat has just jumped, so a
        # mask from after the jump would blur the wrong bubbles, and the faintest first frame is already detected.
        if prev is not None and nxt is not None and nxt - prev <= 2 * hold: use = [prev, nxt]
        elif prev is not None and n - prev <= roll: use = [prev]
        elif prev is not None and nxt is not None and nxt - n <= roll: use = [nxt]
        if use: final[n] = dict(src='hold', polys=sum((raw[u]['poly'] for u in use), []))
    trans = [n for (n, f, it, s) in seq if it is None]
    os.makedirs('censor', exist_ok=True)
    json.dump(dict(beat=bid, f0=f0, f1=f1, frames={str(k): v for k, v in final.items()}, transition_frames=trans,
                   detections={str(k): dict(v1=v['v1'], hits=v['hits']) for k, v in raw.items()}),
              open(f'censor/{bid}_track.json', 'w'))
    ndet = len(raw); nhold = sum(1 for v in final.values() if v['src'] == 'hold')
    print(f'{bid}: {f1 - f0} frames | detected on {ndet}, held on {nhold}, nothing on {f1 - f0 - len(final) - len(trans)}, '
          f'{len(trans)} on a V1 transition')
    by_item = {}
    for n, v in raw.items(): by_item.setdefault(v['v1'], []).append(n)
    for v1, ns in sorted(by_item.items()):
        print(f'  V1 item {v1}: frames {min(ns)}-{max(ns)} ({min(ns) / C.FPS:.2f}-{max(ns) / C.FPS:.2f}s), {len(ns)} detections')
    first = min(raw) if raw else None; last = max(raw) if raw else None
    print(f'  first detection {first} ({first / C.FPS:.2f}s), last {last} ({last / C.FPS:.2f}s)' if raw else '  NO DETECTIONS')


def mask_of(polys, feather=True):
    m = np.zeros((C.TH, C.TW), np.uint8)
    for p in polys: cv2.fillPoly(m, [np.array(p, np.int32)], 255)
    m = cv2.dilate(m, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (17, 17)))
    return m


def censor_patch(rgb, m, b):
    """(x0, y0, rgba patch) - the frame's own pixels under the mask, blurred beyond recovery"""
    ys, xs = np.where(m > 0)
    if not len(ys): return None
    pad = 48
    x0, x1 = max(0, xs.min() - pad), min(C.TW, xs.max() + pad + 1); y0, y1 = max(0, ys.min() - pad), min(C.TH, ys.max() + pad + 1)
    reg = rgb[y0:y1, x0:x1].astype(np.float32)
    blk = b.get('block', 24)
    small = cv2.resize(reg, (max(1, (x1 - x0) // blk), max(1, (y1 - y0) // blk)), interpolation=cv2.INTER_AREA)
    up = cv2.resize(small, (x1 - x0, y1 - y0), interpolation=cv2.INTER_CUBIC)
    up = cv2.GaussianBlur(up, (0, 0), blk * 0.35)
    a = cv2.GaussianBlur(m[y0:y1, x0:x1].astype(np.float32) / 255, (0, 0), 2.5)
    rgba = np.dstack([np.clip(up, 0, 255), a * 255]).astype(np.uint8)
    return x0, y0, rgba


def censor_yuv(planes, polys, b):
    """the same blur on a frame's native YUV planes (zoom.py bakes it in before the camera moves)"""
    m = mask_of(polys)
    ys, xs = np.where(m > 0)
    if not len(ys): return planes
    pad = 48; blk = b.get('block', 24)
    x0, x1 = max(0, xs.min() - pad) // 2 * 2, min(C.TW, xs.max() + pad + 1); y0, y1 = max(0, ys.min() - pad) // 2 * 2, min(C.TH, ys.max() + pad + 1)
    x1 -= (x1 - x0) % 2; y1 -= (y1 - y0) % 2
    out = []
    for pl, s in zip(planes, (1, 2, 2)):
        pl = pl.copy()
        reg = pl[y0 // s:y1 // s, x0 // s:x1 // s].astype(np.float32); h, w = reg.shape; bs = max(2, blk // s)
        small = cv2.resize(reg, (max(1, w // bs), max(1, h // bs)), interpolation=cv2.INTER_AREA)
        up = cv2.GaussianBlur(cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC), (0, 0), bs * 0.35)
        a = cv2.resize(m[y0:y1, x0:x1], (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
        a = cv2.GaussianBlur(a, (0, 0), 2.5 / s)
        pl[y0 // s:y1 // s, x0 // s:x1 // s] = np.clip(reg * (1 - a) + up * a + 0.5, 0, 255).astype(np.uint8)
        out.append(pl)
    return out


_BAKE = None


def baked(n, planes):
    """zoom.py: censor programme frame n's planes if any censor beat covers it"""
    global _BAKE
    if _BAKE is None:
        _BAKE = {}
        for b in M.plan()['beats']:
            if b['kind'] != 'censor' or not os.path.exists(f'censor/{b["id"]}_track.json'): continue
            for k, v in json.load(open(f'censor/{b["id"]}_track.json'))['frames'].items():
                _BAKE.setdefault(int(k), []).append((v['polys'], b))
    for polys, b in _BAKE.get(n, []): planes = censor_yuv(planes, polys, b)
    return planes


def zoom_frames():
    """programme frames that a zoom clip covers: the zoom bakes the censor in, so the overlay stays clear there"""
    out = set()
    for b in M.plan()['beats']:
        if b['kind'] == 'zoom':
            f0, f1 = M.frames_of(b['t0'], b['t1']); out.update(range(f0, f1))
    return out


def render(bid, tag=None):
    b = beat(bid); Tk = json.load(open(f'censor/{bid}_track.json'))
    f0, f1 = M.frames_of(b['t0'], b['t1']); F = Tk['frames']
    seq = frames_seq(f0, f1)
    Z = zoom_frames(); skipped = 0
    os.makedirs(C.MEDIA, exist_ok=True)
    out = os.path.join(C.MEDIA, bid + (f'_{tag}' if tag else '') + '.mov')
    enc = M.writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{C.TW}x{C.TH}', '-r', str(C.FPS),
                         '-i', '-', '-vf', 'scale=out_color_matrix=bt709:out_range=tv,format=yuva444p10le',
                         '-c:v', 'prores_ks', '-profile:v', '4444', '-alpha_bits', '16', '-vendor', 'apl0',
                         '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv', out])
    canvas = np.zeros((C.TH, C.TW, 4), np.uint8); dirty = None
    gen = {r[0][0]: M.decode([(f, it, s) for (n, f, it, s) in r], C.TW, C.TH) for r in runs(seq)}
    cur = None; done = 0
    for (n, f, it, s) in seq:
        if n in gen: cur = gen[n]
        rgb = next(cur) if f is not None else None
        if dirty is not None:
            x0, y0, x1, y1 = dirty; canvas[y0:y1, x0:x1] = 0; dirty = None
        polys = F.get(str(n), {}).get('polys')
        if n in Z and polys: skipped += 1; polys = None                  # the zoom clip carries the censor here
        if rgb is not None and polys:
            p = censor_patch(rgb, mask_of(polys), b)
            if p:
                x0, y0, rgba = p; h, w = rgba.shape[:2]
                canvas[y0:y0 + h, x0:x0 + w] = rgba; dirty = (x0, y0, x0 + w, y0 + h)
        elif rgb is None and str(n) in Tk.get('transition_patches', {}):
            x0, y0, w, h = Tk['transition_patches'][str(n)]['rect']        # filled in by hand for V1 transitions
            rgba = cv2.imread(Tk['transition_patches'][str(n)]['png'], cv2.IMREAD_UNCHANGED)
            canvas[y0:y0 + h, x0:x0 + w] = cv2.cvtColor(rgba, cv2.COLOR_BGRA2RGBA); dirty = (x0, y0, x0 + w, y0 + h)
        enc.stdin.write(canvas.tobytes()); done += 1
    enc.stdin.close(); enc.wait()
    print(f'{out}: {done} frames ({f0}-{f1 - 1}) | {skipped} left clear under zoom clips that bake the censor in')


def ref(t, out=None):
    """the full-resolution programme frame at t (frame-exact, like preview), to measure the template boxes on"""
    n = int(round(t * C.FPS)); seq = frames_seq(n, n + 1)
    if seq[0][1] is None: print(t, 'is on a V1 transition - pick another time'); return
    it = seq[0][2]
    full = frames_seq(it['rec0'], it['rec1']); k = n - it['rec0']
    rgb = M.decode_at([(f_, it_, s_) for (_, f_, it_, s_) in full], k, C.TW, C.TH)
    out = out or f'censor/ref_{t:.1f}.png'
    os.makedirs(os.path.dirname(out) or '.', exist_ok=True)
    cv2.imwrite(out, cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    print(out)


def preview(bid, ts):
    b = beat(bid); Tk = json.load(open(f'censor/{bid}_track.json')); F = Tk['frames']
    os.makedirs('preview', exist_ok=True)
    for t in ts:
        n = int(round(t * C.FPS)); seq = frames_seq(n, n + 1)
        if seq[0][1] is None: print(t, 'on a transition'); continue
        (_, f, it, s) = seq[0]
        full = frames_seq(it['rec0'], it['rec1']); k = n - it['rec0']
        rgb = M.decode_at([(f_, it_, s_) for (_, f_, it_, s_) in full], k, C.TW, C.TH)
        out = rgb.copy()
        polys = F.get(str(n), {}).get('polys')
        if polys:
            x0, y0, rgba = censor_patch(rgb, mask_of(polys), b); h, w = rgba.shape[:2]
            a = rgba[..., 3:4].astype(np.float32) / 255
            out[y0:y0 + h, x0:x0 + w] = (rgba[..., :3] * a + out[y0:y0 + h, x0:x0 + w] * (1 - a)).astype(np.uint8)
        p = f'preview/{bid}_{t:.2f}.png'
        cv2.imwrite(p, cv2.cvtColor(cv2.resize(out, (1920, 1080), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2BGR))
        print(p, F.get(str(n), {}).get('src', 'none'))


def transition(bid, mov, first):
    """V1 transitions (a zoom/bounce the editor added) can't be followed from the source: render them out of Resolve
    (frames `first`.. of the timeline into `mov`), register each frame against the last clean frame before the
    transition (ECC, affine, coarse to fine), warp that frame's mask onto it, widen it by the frame's own motion
    (the transition blurs) and blur the RENDERED pixels under it. Writes censor/trans/<n>.png + the track's
    transition_patches."""
    b = beat(bid); path = f'censor/{bid}_track.json'; Tk = json.load(open(path)); F = Tk['frames']
    tf = sorted(Tk['transition_frames'])
    if not tf: print('no transition frames'); return
    ref_n = tf[0] - 1
    if str(ref_n) not in F: print(f'frame {ref_n} before the transition has no mask - nothing to carry over'); return
    cut = min(it['rec0'] for it in M.program()['items'] if it['rec0'] >= tf[0])
    print(f'transition frames {tf[0]}-{tf[-1]}, cut at {cut}: patching the outgoing side ({tf[0]}-{cut - 1}); '
          f'the incoming side shows the next item - check it by eye')
    tf = [n for n in tf if n < cut]
    m_ref = mask_of(F[str(ref_n)]['polys'])
    n_all = tf[-1] - first + 2
    p = M.reader_proc(['ffmpeg', '-v', 'error', '-i', mov, '-frames:v', str(n_all), '-vf', M.dec_vf(mov), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    frames = {}
    for k in range(n_all):
        bb = M.read_exact(p.stdout, C.TW * C.TH * 3)
        if bb is None: break
        frames[first + k] = np.frombuffer(bb, np.uint8).reshape(C.TH, C.TW, 3)
    p.stdout.close(); p.wait()
    S = 4; small = lambda im: cv2.cvtColor(cv2.resize(im, (C.TW // S, C.TH // S), interpolation=cv2.INTER_AREA), cv2.COLOR_RGB2GRAY).astype(np.float32)
    ref = small(frames[ref_n])
    os.makedirs('censor/trans', exist_ok=True)
    A = np.eye(2, 3, dtype=np.float32); prev_A = A.copy(); patches = {}; log = []
    for n in tf:
        cur = small(frames[n])
        ok = True
        try:
            _, A1 = cv2.findTransformECC(ref, cur, A.copy(), cv2.MOTION_AFFINE,
                                          (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 200, 1e-5), None, 5)
            A = A1
        except cv2.error:
            ok = False
            A = A + (A - prev_A)                                  # extrapolate the zoom when ECC loses it
        Af = A.copy(); Af[:, 2] *= S                                # to full-res pixels
        warped = cv2.warpAffine(m_ref, Af, (C.TW, C.TH), flags=cv2.INTER_LINEAR)
        ys, xs = np.where(m_ref > 0)
        corners = np.array([[xs.min(), ys.min(), 1], [xs.max(), ys.min(), 1], [xs.min(), ys.max(), 1], [xs.max(), ys.max(), 1]], np.float32)
        Pp = prev_A.copy(); Pp[:, 2] *= S
        motion = float(np.abs(corners @ Af.T - corners @ Pp.T).max())
        grow = int(24 + 1.2 * motion + (40 if not ok else 0))
        warped = cv2.dilate(warped, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * grow + 1, 2 * grow + 1)))
        prev_A = A.copy()
        if not warped.any(): log.append((n, ok, 0, 'off screen')); continue
        x0, y0, rgba = censor_patch(frames[n], warped, b)
        f = f'censor/trans/{n}.png'
        cv2.imwrite(f, cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
        patches[str(n)] = dict(rect=[int(x0), int(y0), int(rgba.shape[1]), int(rgba.shape[0])], png=f)
        log.append((n, ok, round(float(A[0, 0]), 3), grow))
    Tk['transition_patches'] = patches
    json.dump(Tk, open(path, 'w'))
    for l in log: print('  frame %d ecc %s scale %s grow %s' % l)
    print(f'{len(patches)} transition patches')


def gpu_gray(run, W, H):
    """grey frames for one contiguous source run, decoded and scaled on the GPU (NVDEC + scale_cuda): the safety
    scan reads every frame of the programme, and CPU decode of 4K would starve the renders running beside it"""
    f, a, n = run[0][1], run[0][3], len(run)
    p = M.reader_proc(['ffmpeg', '-v', 'error', '-hwaccel', 'cuda', '-hwaccel_output_format', 'cuda',
                       '-ss', f'{max(0.0, (a - 0.25) / C.FPS):.5f}', '-i', f, '-frames:v', str(n),
                       '-vf', f'scale_cuda={W}:{H}:format=nv12,hwdownload,format=nv12', '-f', 'rawvideo', '-pix_fmt', 'gray', '-'])
    try:
        for _ in range(n):
            bb = M.read_exact(p.stdout, W * H)
            if bb is None: break
            yield np.frombuffer(bb, np.uint8).reshape(H, W)
    finally:
        p.stdout.close(); p.kill() if p.poll() is None else None; p.wait()


def scan_run(args):
    bid, run, step, gpu = args
    b = beat(bid); T = templates(b); thr = b.get('thr', 0.78)
    W, H = C.TW // HALF, C.TH // HALF
    out = []
    # decode the whole run once, test every step-th frame
    seq = [(f, it, s) for (n, f, it, s) in run]
    frames = gpu_gray(run, W, H) if gpu else (cv2.cvtColor(fr, cv2.COLOR_RGB2GRAY) for fr in M.decode(seq, W, H, f'scale={W}:{H}:flags=area'))
    for k, gray in enumerate(frames):
        if k % step: continue
        for key, t in T.items():
            mx = cv2.minMaxLoc(cv2.matchTemplate(gray, t, cv2.TM_CCOEFF_NORMED))[1]
            if mx >= thr: out.append((run[k][0], key, round(float(mx), 3)))
    return out


def scan(bid, t0, t1, step=3, jobs=12, gpu=False):
    f0, f1 = int(round(t0 * C.FPS)), int(round(t1 * C.FPS))
    rs = runs(frames_seq(f0, f1)); chunks = []
    for r in rs:
        for k in range(0, len(r), 600): chunks.append(r[k:k + 600])
    hits = []
    with ProcessPoolExecutor(jobs) as ex:
        for d in ex.map(scan_run, [(bid, c, step, gpu) for c in chunks]): hits += d
    b = beat(bid); bf0, bf1 = M.frames_of(b['t0'], b['t1'])
    outside = [h for h in hits if not (bf0 <= h[0] < bf1)]
    print(f'scan {t0:.1f}-{t1:.1f}s every {step} frames: {len(hits)} template hits, {len(outside)} outside {bid} ({b["t0"]:.2f}-{b["t1"]:.2f}s)')
    by = {}
    for n, k, s in outside: by.setdefault(n, []).append(f'{k}@{s}')
    for n in sorted(by)[:200]: print(f'  {n} ({n / C.FPS:.2f}s): {", ".join(by[n])}')


if __name__ == '__main__':
    a = sys.argv[1:]
    jobs = int(a[a.index('--jobs') + 1]) if '--jobs' in a else 12
    if a[0] == 'ref': ref(float(a[1]))
    elif a[0] == 'track': track(a[1], jobs)
    elif a[0] == 'render': render(a[1], a[a.index('--tag') + 1] if '--tag' in a else None)
    elif a[0] == 'preview': preview(a[1], [float(x) for x in a[2:]])
    elif a[0] == 'transition': transition(a[1], a[2], int(a[3]))
    elif a[0] == 'scan':
        step = int(a[a.index('--step') + 1]) if '--step' in a else 3
        scan(a[1], float(a[2]), float(a[3]), step, jobs, gpu='--gpu' in a)
