"""The dynamic camera's choreography (references/dynamic-camera.md): a draft from the cut and the edit plan, corners
chosen from what is on screen, and a checker for the timing rules the research and abacus-test settled.

usage (cwd = W; after rs_content.py has written $M/_deliver/content.mp4 + tracks.json, and dyncam.py cfg):
  python scripts/dyncam_plan.py busy        # corner_busy.npy: edge density of the content layer under each corner, 2 samples a second
  python scripts/dyncam_plan.py targets     # dyncam_targets.json: what the narration points at - every zoom mark through its
                                            # zoom's camera, the CTA cards, plus dyncam_targets_manual.json (clicks nobody marked)
  python scripts/dyncam_plan.py draft       # dyncam_plan.json from the rules below; then EDIT it (the editor's judgment) and
  python scripts/dyncam_plan.py check       # the rules, on whatever the plan now says; exit 1 on an error

States: FULL (the face full frame, at the camera item's own punch-in), CARD (a large portrait card on the right, the
content in a panel on the left: reacting to a result where both you and it matter), SMALL (a corner window while the
viewer reads or watches the screen), HIDDEN (full-frame graphics and dense UI).
The draft:
  - FULL on camera lines (enabled items on the dyncam_cfg camera tracks) not covered by a graphic; SMALL on screen
    lines; graphics with layout "fv" (no facecam) -> HIDDEN, other graphics -> SMALL;
  - a beat may steer it: "dyncam": "full" | "card" | "small" | "hidden", "dyncam_corner": "tr",
    "dyncam_content": "image:<png>" (zoom beats already use "cam" for their own camera);
  - a FULL stretch shorter than 3 s stays SMALL (no 2-second flash of the face), unless a beat asks for it;
  - corners: top-right by default; the content layer's clutter under each corner, a heavy cost for covering a
    target, priors (tr 0.85, bottom 1.25, tl 1.8) and a switch cost of ~8 s of median clutter, so each corner holds;
    graphics keep the corner they were designed around ("dyncam_corner", default tr);
  - durations: grows 0.5 s (to FULL they hold the outgoing shot's last frame), shrinks 0.4 s, card exits 0.45 s,
    corner hops 0.3 s, hides 0.3 s; a hard cut (0) at chapter starts, out of HIDDEN, and wherever a move would come
    within 2 s of another; every key sits on a cut (a boundary in the timeline or a beat)."""
import json, os, sys, subprocess
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C

FPS = C.FPS
DELIVER = os.path.join(C.MEDIA, '_deliver')
CORN = ['tr', 'br', 'bl', 'tl']; PRIOR = np.array([0.85, 1.25, 1.25, 1.8])
IN, OUT, HOP, HIDE_D = 0.5, 0.4, 0.3, 0.3
MIN_FULL, NEAR = 3.0, 2.0


def load(p, default=None):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else default


PROG = load('program.json'); PL = load('edit_plan.json', {'beats': []}); CFG = load('dyncam_cfg.json')
TRACKS = load(os.path.join(DELIVER, 'tracks.json'))
TOTAL = PROG['frames']; DUR = TOTAL / FPS
BEATS = [b for b in PL.get('beats', []) if 't0' in b and 't1' in b]


def boxes():
    sz, m = CFG['small'], CFG['margin']; W, H = C.LAYOUT_W, C.LAYOUT_H
    return {'tr': (W - m - sz, m), 'br': (W - m - sz, H - m - sz), 'bl': (m, H - m - sz), 'tl': (m, m)}


def cuts():
    """every frame where the picture can cut: item boundaries on any video track, programme items, beat edges"""
    s = {0, TOTAL}
    for it in PROG['items']: s.update((it['rec0'], it['rec1']))
    for tr in (TRACKS or {}).get('video', []):
        for it in tr['items']: s.update((it['rec0'], it['rec1']))
    for b in BEATS: s.update((int(round(b['t0'] * FPS)), int(round(b['t1'] * FPS))))
    return sorted(x for x in s if 0 <= x <= TOTAL)


def webcam_cuts():
    """jump cuts in the webcam itself (programme item boundaries): a move must never straddle one"""
    return sorted({it['rec0'] for it in PROG['items']} | {it['rec1'] for it in PROG['items']})


# ---------------------------------------------------------------- busy and targets
def busy():
    p = sys.argv[sys.argv.index('--content') + 1] if '--content' in sys.argv else os.path.join(DELIVER, 'content.mp4')
    w, h = 960, 540; k = w / C.LAYOUT_W
    proc = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', p, '-vf', f'fps=2,scale={w}:{h}:flags=area,format=gray', '-f', 'rawvideo', '-'],
                            stdout=subprocess.PIPE, bufsize=0)
    q = int((CFG['small'] + CFG['margin'] + 30) * k)          # the window + its margin (+ shadow), from each corner
    out = []
    while True:
        buf = bytearray()
        while len(buf) < w * h:
            c = proc.stdout.read(w * h - len(buf))
            if not c: break
            buf += c
        if len(buf) < w * h: break
        g = np.frombuffer(bytes(buf), np.uint8).reshape(h, w).astype(np.float32)
        e = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 0)) + np.abs(cv2.Sobel(g, cv2.CV_32F, 0, 1))
        out.append([float(e[:q, -q:].mean()), float(e[-q:, -q:].mean()), float(e[-q:, :q].mean()), float(e[:q, :q].mean())])
    proc.wait()
    np.save('corner_busy.npy', np.array(out, np.float32))
    print(f'corner_busy.npy: {len(out)} samples ({len(out) / 2:.0f} s of {DUR:.0f}) | mean clutter tr/br/bl/tl', np.round(np.mean(out, 0), 4))


def targets():
    import importlib.util
    spec = importlib.util.spec_from_file_location('zoom_mod', 'scripts/zoom.py'); zm = importlib.util.module_from_spec(spec)
    saved = sys.argv; sys.argv = ['zoom.py']; spec.loader.exec_module(zm); sys.argv = saved
    sys.path.insert(0, 'scripts'); import dyncam as D
    out = []
    for b in BEATS:
        if b['kind'] == 'zoom' and b.get('marks'):
            n0 = int(round(b['t0'] * FPS)); it = next((i for i in PROG['items'] if i['rec0'] <= n0 < i['rec1']), None)
            if not it: continue
            SW, SH = D.vinfo(it['file'])[:2]; kfit = C.TW / SW
            for m in b['marks']:
                t0 = m['t']; t1 = m.get('t_out', b['t1'] - b['t0'])
                for t in (t0, (t0 + t1) / 2, t1 - 0.05):
                    fx, fy, kk = zm.cam_state(b, t, SW, SH, kfit)
                    x, y, w, h = m['rect']
                    ox = ((x - fx) * kk + C.TW / 2) / C.UNIT; oy = ((y - fy) * kk + C.TH / 2) / C.UNIT      # layout px
                    out.append([round(b['t0'] + t - 0.4, 2), round(b['t0'] + t + 0.6, 2), ox, oy, w * kk / C.UNIT, h * kk / C.UNIT, b['id']])
        if b['kind'] == 'cta':
            out.append([b['t0'], b['t1'], 64, 836, 900, 176, b['id']])      # overlay.py's CTA_BOX
    out += load('dyncam_targets_manual.json', [])
    json.dump(out, open('dyncam_targets.json', 'w'), indent=0); print(len(out), 'targets -> dyncam_targets.json')


# ---------------------------------------------------------------- the draft
def covering(n, pred):
    t = n / FPS
    return next((b for b in BEATS if b['t0'] <= t < b['t1'] and pred(b)), None)


def want(a, b):
    """desired (state, corner, content, forced) over the segment [a, b) of programme frames"""
    mid = (a + b) // 2
    hint = covering(mid, lambda x: 'dyncam' in x)
    if hint:
        return hint['dyncam'].upper(), hint.get('dyncam_corner'), hint.get('dyncam_content'), True
    g = covering(mid, lambda x: x['kind'] in ('gfx', 'broll'))   # anything that covers the camera with a picture
    if g:
        if g.get('layout') == 'fv': return 'HIDDEN', g.get('dyncam_corner'), None, True
        return 'SMALL', g.get('dyncam_corner', CFG.get('default_corner', 'tr')), None, bool(g.get('dyncam_corner')) or g.get('layout') == 'fvc'
    names = set(CFG.get('camera_tracks', ['Camera']))
    cam = any(it['enabled'] and it['rec0'] <= mid < it['rec1'] for tr in (TRACKS or {}).get('video', []) if tr['name'] in names for it in tr['items'])
    return ('FULL' if cam else 'SMALL'), None, None, False


def choose_corners(stretches, segs_of):
    """DP over each SMALL stretch's cut-bounded segments -> [(a, b, corner)]"""
    bz = np.load('corner_busy.npy') if os.path.exists('corner_busy.npy') else np.zeros((int(DUR * 2) + 2, 4), np.float32)
    med = float(np.median(bz[:, 0])) or 1e-3
    TG = load('dyncam_targets.json', []); B = boxes(); SZ = CFG['small']
    def tcost(s0, s1):
        c = np.zeros(4)
        for t0, t1, x, y, w, h, *_ in TG:
            ov = max(0.0, min(s1, t1) - max(s0, t0))
            if ov <= 0: continue
            for k, cn in enumerate(CORN):
                bx, by = B[cn]
                if min(x + w, bx + SZ + 20) > max(x, bx - 20) and min(y + h, by + SZ + 20) > max(y, by - 20): c[k] += ov * med * 40
        return c
    SWITCH = 14.0 * med * 0.6
    out = []
    for a, b in stretches:
        segs = []
        for s0, s1, forced in segs_of(a, b):
            t0, t1 = s0 / FPS, s1 / FPS
            sc = bz[int(t0 * 2):max(int(t0 * 2) + 1, int(t1 * 2))].mean(0) * PRIOR * (t1 - t0) + tcost(t0, t1)
            segs.append((s0, s1, sc, forced))
        INF = 1e18; cost = [[INF] * 4 for _ in segs]; back = [[0] * 4 for _ in segs]
        for i, (s0, s1, sc, forced) in enumerate(segs):
            for c in range(4):
                if forced and CORN[c] != forced: continue
                if i == 0: cost[i][c] = sc[c]; continue
                best = min(range(4), key=lambda p: cost[i - 1][p] + (SWITCH if p != c else 0))
                cost[i][c] = cost[i - 1][best] + (SWITCH if best != c else 0) + sc[c]; back[i][c] = best
        c = min(range(4), key=lambda k: cost[-1][k]); path = [c]
        for i in range(len(segs) - 1, 0, -1): c = back[i][c]; path.append(c)
        for (s0, s1, sc, forced), c in zip(segs, path[::-1]):
            if out and out[-1][2] == CORN[c] and out[-1][1] == s0: out[-1][1] = s1
            else: out.append([s0, s1, CORN[c]])
    return out


def draft():
    cs = cuts()
    runs = []                                                   # [a, b, state, corner, content, forced]
    for a, b in zip(cs, cs[1:]):
        if b <= a: continue
        st, corner, content, forced = want(a, b)
        if runs and runs[-1][2] == st and runs[-1][4] == content and (runs[-1][3] == corner or st != 'SMALL' or not (forced and runs[-1][5])):
            runs[-1][1] = b; runs[-1][5] = runs[-1][5] or forced
            if corner and not runs[-1][3]: runs[-1][3] = corner
        else: runs.append([a, b, st, corner, content, forced])
    for r in runs:                                              # no 2-second flash of the face
        if r[2] == 'FULL' and not r[5] and (r[1] - r[0]) / FPS < MIN_FULL: r[2] = 'SMALL'
    merged = []
    for r in runs:
        if merged and merged[-1][2] == r[2] == 'SMALL' and merged[-1][4] == r[4]: merged[-1][1] = r[1]; merged[-1][5] = merged[-1][5] or r[5]
        elif merged and merged[-1][2] == r[2] and r[2] != 'SMALL' and merged[-1][4] == r[4]: merged[-1][1] = r[1]
        else: merged.append(list(r))
    # corners for the SMALL stretches
    def segs_of(a, b):
        inner = [c for c in cs if a + FPS <= c <= b - FPS]       # switch only on a cut, at least 1 s in
        bounds = [a] + inner + [b]
        return [(s0, s1, want(s0, s1)[1] if want(s0, s1)[3] and want(s0, s1)[0] == 'SMALL' else None)
                for s0, s1 in zip(bounds, bounds[1:]) if s1 > s0]
    corner_runs = choose_corners([(r[0], r[1]) for r in merged if r[2] == 'SMALL'], segs_of)
    def corner_at(n):
        return next((c for a, b, c in corner_runs if a <= n < b), CFG.get('default_corner', 'tr'))
    final = []                                                  # split SMALL runs at corner changes
    for r in merged:
        if r[2] != 'SMALL': final.append(r); continue
        for a, b, c in corner_runs:
            if a >= r[0] and b <= r[1]: final.append([a, b, 'SMALL', c, r[4], r[5]])
    for r in final:
        if r[2] == 'HIDDEN' and not r[3]: r[3] = corner_at(max(0, r[0] - 1))
    chapters = {int(round(c['t'] * FPS)) for c in PL.get('chapters', []) if c.get('t', 0) > 0}
    keys = []
    for prev, r in zip(final, final[1:]):
        a, frm, to = r[0], prev[2], r[2]
        if frm == to and prev[4] == r[4] and (to in ('FULL', 'CARD') or (prev[3] or corner_at(prev[0])) == (r[3] or corner_at(a))):
            continue                                            # nothing changes on screen: no key
        if to == 'FULL': d = IN
        elif to == 'CARD': d = IN
        elif to == 'HIDDEN': d = HIDE_D
        elif frm == 'CARD': d = OUT + 0.05
        elif frm == 'SMALL': d = HOP
        elif frm == 'HIDDEN': d = OUT
        else: d = OUT
        why = []
        if any(abs(a - c) <= 1 for c in chapters): d = 0; why.append('chapter cut')
        if frm == 'HIDDEN' and to == 'FULL': d = 0; why.append('cut out of a full-frame graphic')
        if (r[1] - r[0]) / FPS < NEAR or (prev[1] - prev[0]) / FPS < NEAR: d = 0; why.append('too close to another move: cut')
        k = dict(t=a / FPS, dur=d, to=to)                       # exact: 4-decimal seconds sit off the frame grid
        if to in ('SMALL', 'HIDDEN'): k['corner'] = r[3] or corner_at(a)
        if r[4]: k['content'] = r[4]
        elif prev[4] and to != 'CARD': k['content'] = 'stem'
        if to == 'FULL' and d > 0 and frm in ('SMALL', 'HIDDEN'): k['hold'] = True
        k['why'] = ', '.join(why) or f'{frm.lower()} -> {to.lower()}'
        keys.append(k)
    s0 = final[0]
    start = {'to': s0[2]}
    if s0[2] in ('SMALL', 'HIDDEN'): start['corner'] = s0[3] or 'tr'
    plan = {'start': start, 'keys': keys}
    if os.path.exists('dyncam_plan.json'):
        os.replace('dyncam_plan.json', 'dyncam_plan.prev.json'); print('kept the previous plan as dyncam_plan.prev.json')
    json.dump(plan, open('dyncam_plan.json', 'w'), indent=1)
    n = {s: sum((r[1] - r[0]) for r in final if r[2] == s) / FPS for s in ('FULL', 'CARD', 'SMALL', 'HIDDEN')}
    cn = {c: sum((r[1] - r[0]) for r in final if r[2] == 'SMALL' and r[3] == c) / FPS for c in CORN}
    print(f'{len(keys)} keys -> dyncam_plan.json | ' + ', '.join(f'{s} {v:.0f}s' for s, v in n.items()) + ' | SMALL corners ' +
          ', '.join(f'{c} {v:.0f}s' for c, v in cn.items() if v))
    print('Now edit it: CARD for reactions to a result, FULL for the hook promise / opinions / CTA / outro, then `check`.')


# ---------------------------------------------------------------- the checker
def check():
    P = load('dyncam_plan.json'); keys = sorted(P['keys'], key=lambda k: k['t'])
    cs = set(cuts()); wc = webcam_cuts(); errs, warns = [], []
    chapters = [c['t'] for c in PL.get('chapters', []) if c.get('t', 0) > 0]
    TG = load('dyncam_targets.json', []); B = boxes(); SZ = CFG['small']
    for i, k in enumerate(keys):
        n = k['t'] * FPS; nr = int(round(n)); tag = f"{k['t']:.3f} {k['to']}"
        if abs(n - nr) > 0.05: warns.append(f'{tag}: between frames ({n:.3f}); dyncam.py snaps it to frame {nr} - is that the cut you meant?')
        if k['to'] not in ('FULL', 'CARD', 'SMALL', 'HIDDEN'): errs.append(f'{tag}: unknown state')
        d = k.get('dur', 0)
        if d and not 0.25 <= d <= 0.6: warns.append(f'{tag}: dur {d} s outside 0.25-0.6 (entries 0.5, exits 0.4, hops 0.3)')
        if i + 1 < len(keys) and k['t'] + d > keys[i + 1]['t'] + 1e-6: errs.append(f'{tag}: overlaps the next move')
        e = int(round((k['t'] + d) * FPS))
        inside = [c for c in wc if nr < c < e]
        if d and inside: errs.append(f'{tag}: a webcam jump cut at {inside[0] / FPS:.3f} lands inside the move (a pop): start the move at that cut')
        if i + 1 < len(keys):
            gap = keys[i + 1]['t'] - (k['t'] + d)
            if gap < NEAR and d and keys[i + 1].get('dur', 0): warns.append(f'{tag}: held {gap:.2f} s before the next move (aim >= 8 s; cut instead under 2 s)')
        if k['to'] == 'FULL' and d and i > 0 and keys[i - 1]['to'] in ('SMALL', 'HIDDEN') and not k.get('hold'):
            content_cut = [c for c in cs if nr < c < e]
            if content_cut: warns.append(f'{tag}: the content cuts at {content_cut[0] / FPS:.3f} inside the grow: set "hold": true')
        if str(k.get('content', '')).startswith('image:') and not os.path.exists(k['content'][6:]): errs.append(f'{tag}: {k["content"][6:]} missing')
        if k['to'] == 'SMALL':
            t1 = keys[i + 1]['t'] if i + 1 < len(keys) else DUR
            bx, by = B[k.get('corner', 'tr')]
            for t0g, t1g, x, y, w, h, *lab in TG:
                if min(t1, t1g) - max(k['t'], t0g) > 0.2 and min(x + w, bx + SZ) > max(x, bx) and min(y + h, by + SZ) > max(y, by):
                    warns.append(f'{tag}: the {k.get("corner")} window covers target {lab[0] if lab else "?"} at {t0g:.1f}-{t1g:.1f}')
    for c in chapters:
        k = next((k for k in keys if abs(k['t'] - c) < 0.05), None)
        if k and k.get('dur', 0): warns.append(f'chapter at {c:.2f}: animated ({k["dur"]} s) - chapter changes are hard cuts')
    holds = [b['t'] - (a['t'] + a.get('dur', 0)) for a, b in zip(keys, keys[1:])]
    rate = len(keys) / (DUR / 3600)
    print(f'{len(keys)} keys, {rate:.0f} layout changes an hour (research: ~100; v3 abacus 180), median hold {np.median(holds) if holds else 0:.1f} s')
    for w in warns: print('WARN ', w)
    for e in errs: print('ERROR', e)
    print('OK' if not errs else f'{len(errs)} errors'); sys.exit(1 if errs else 0)


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if not CFG: sys.exit('dyncam_cfg.json first: python scripts/dyncam.py cfg')
    if cmd in ('busy', 'targets', 'draft') and not TRACKS: sys.exit(f'{DELIVER}/tracks.json missing: run rs_content.py in Resolve first')
    {'busy': busy, 'targets': targets, 'draft': draft, 'check': check}.get(cmd, lambda: sys.exit(__doc__))()
