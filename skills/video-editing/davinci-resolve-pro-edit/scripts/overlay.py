"""Alpha overlays for the top video track (ProRes 4444 with alpha, timeline resolution), drawn in code:

  words  hook keyword pop: 1-3 words, Poppins Bold white with a black stroke, or - for a highlight - Instrument Serif
         italic in pure yellow. Pops in over 0.18 s, holds, fades out.  (hook only; the body gets none)
         {"id": "w02", "kind": "words", "t0": 6.10, "t1": 7.35, "text": "half the cost", "hl": true, "xy": [960, 905]}
  cta    lower-third community card: avatar or logo, a label, the URL typed with a clay caret, then a button press.
         {"id": "c01", "kind": "cta", "t0": 118.2, "t1": 124.6, "url": "skool.com/leonvanzyl",
          "label": "Free AI builder community", "button": "Join", "type_at": 0.9, "logo": "gfx/assets/skool.png"}
         type_at = beat-relative second the typing starts (put it on the word that names the place).

Positions and sizes are layout px (1920x1080) and scale to the timeline. SFX for visible events (pop on landing,
key ticks while typing, click on the press) go to events/<id>.json for audio.py.
Every frame is a pure function of a small state (landing/fade progress, typed characters, caret, press): frames with
the same state reuse the same drawing, and only the drawing's own box is written into a persistent, otherwise
transparent frame, so a 4K overlay no longer allocates and converts a 130 MB canvas per frame. Pixel-identical.
usage: python scripts/overlay.py w02 c01 ... [--preview 0.5] [--tag v2] [--jobs N]   -> media/<id>[_v2].mov (or preview/<id>_<t>.png)
--tag v2 writes a new file for an edit (Resolve holds the old one open): then media_pool_item replace_clip.
--jobs N renders several beats at once, one process each (default 3)."""
import sys, os, json
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, 'scripts'); import config as C, media as M
TAG = ('_' + sys.argv[sys.argv.index('--tag') + 1]) if '--tag' in sys.argv else ''   # edits: a new file, then replace_clip

U = C.UNIT


def font(name, size):
    return ImageFont.truetype(C.FONTS + name, int(round(size * U)))


def shadow_layer(size, box, radius):
    """the spec's three-layer shadow under a rounded box, as an RGBA image"""
    acc = np.zeros(size[::-1], np.float32)
    for dy, blur, a in C.SHADOW:
        m = Image.new('L', size, 0)
        x0, y0, x1, y1 = box
        ImageDraw.Draw(m).rounded_rectangle((x0, y0 + dy * U, x1, y1 + dy * U), int(radius), fill=255)
        m = m.filter(ImageFilter.GaussianBlur(blur / 2 * U))
        acc = 1 - (1 - acc) * (1 - a * np.asarray(m, np.float32) / 255)
    sh = Image.new('RGBA', size, (24, 24, 32, 0)); sh.putalpha(Image.fromarray((acc * 255).astype(np.uint8)))
    return sh


def place(canvas, im, cx, cy, scale=1.0, alpha=1.0):
    if scale != 1.0:
        im = im.resize((max(1, int(im.size[0] * scale)), max(1, int(im.size[1] * scale))), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32)
    a[..., 3] *= alpha
    h, w = a.shape[:2]; x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    ys0, ys1 = max(0, y0), min(C.TH, y0 + h); xs0, xs1 = max(0, x0), min(C.TW, x0 + w)
    if ys1 <= ys0 or xs1 <= xs0: return
    src = a[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]; dst = canvas[ys0:ys1, xs0:xs1]
    sa = src[..., 3:4] / 255; da = dst[..., 3:4] / 255
    oa = sa + da * (1 - sa)
    dst[..., :3] = np.where(oa > 0, (src[..., :3] * sa + dst[..., :3] * da * (1 - sa)) / np.maximum(oa, 1e-6), 0)
    dst[..., 3:4] = oa * 255


# ------------------------------------------------------------------ keyword pops
def words_img(text, hl):
    f = font('InstrumentSerif-Italic.ttf', 96) if hl else font('Poppins-Bold.ttf', 80)
    stroke = int(round((9 if hl else 8) * U)); pad = stroke * 3
    d0 = ImageDraw.Draw(Image.new('L', (1, 1)))
    gap = d0.textlength(' ', font=f) + 10 * U                  # wider than the stroke, so spaces survive
    ws = text.split(); tw = sum(d0.textlength(w, font=f) for w in ws) + gap * (len(ws) - 1)
    asc, desc = f.getmetrics()
    im = Image.new('RGBA', (int(tw + 2 * pad), int(asc + desc + 2 * pad)), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x = pad
    for w in ws:
        if hl:
            d.text((x, pad), w, font=f, fill=C.HL_YELLOW + (255,), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
            d.text((x, pad), w, font=f, fill=C.HL_YELLOW + (255,), stroke_width=max(1, int(2 * U)), stroke_fill=C.HL_YELLOW + (255,))
        else:
            d.text((x, pad), w, font=f, fill=(255, 255, 255, 255), stroke_width=stroke, stroke_fill=(0, 0, 0, 255))
        x += d0.textlength(w, font=f) + gap
    return im


def words_state(b, t):
    dur = b['t1'] - b['t0']
    pin = min(1.0, t / 0.18); pout = min(1.0, max(0.0, (dur - t) / 0.14))
    return None if (pin <= 0 or pout <= 0) else (pin, pout)


def words_draw(b, state, cache):
    if 'img' not in cache: cache['img'] = words_img(b['text'], b.get('hl', False))
    pin, pout = state
    e = M.ease('power3.out')(pin)
    cx, cy = b.get('xy', [960, 905])
    canvas = np.zeros((C.TH, C.TW, 4), np.float32)
    place(canvas, cache['img'], cx * U, cy * U, (0.86 + 0.14 * e) * (0.97 + 0.03 * pout), min(1.0, pin * 2) * pout)
    return canvas


# ------------------------------------------------------------------ community CTA card
CTA_BOX = (64, 836, 900, 176)          # x, y, w, h (layout px): bottom-left, clear of the webcam corner


def cta_static(b):
    x, y, w, h = CTA_BOX; r = 44
    pad = 260                                                    # room for the whole shadow falloff (no clipped edge)
    size = (int((w + 2 * pad) * U), int((h + 2 * pad) * U))
    box = (pad * U, pad * U, (pad + w) * U, (pad + h) * U)
    im = shadow_layer(size, box, r * U)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle(box, int(r * U), fill=(255, 255, 255, 255))
    ax, ay, ar = box[0] + 34 * U + 54 * U, box[1] + h * U / 2, 54 * U
    if b.get('logo') and os.path.exists(b['logo']):
        lg = Image.open(b['logo']).convert('RGBA').resize((int(2 * ar), int(2 * ar)), Image.LANCZOS)
        mk = Image.new('L', lg.size, 0); ImageDraw.Draw(mk).ellipse((0, 0, lg.size[0] - 1, lg.size[1] - 1), fill=255)
        im.paste(lg, (int(ax - ar), int(ay - ar)), mk)
    else:
        d.ellipse((ax - ar, ay - ar, ax + ar, ay + ar), fill=(232, 232, 228, 255))
        d.ellipse((ax - 20 * U, ay - 33 * U, ax + 20 * U, ay + 7 * U), fill=(178, 178, 172, 255))
        d.pieslice((ax - 38 * U, ay + 11 * U, ax + 38 * U, ay + 84 * U), 180, 360, fill=(178, 178, 172, 255))
    tx = ax + ar + 28 * U
    if b.get('label'):
        d.text((tx, box[1] + 38 * U), b['label'], font=font('Poppins-Medium.ttf', 30), fill=(110, 110, 104, 255))
    return im, box, tx


def cta_state(b, t):
    dur = b['t1'] - b['t0']
    land = min(1.0, max(0.0, t / 0.5)); out = min(1.0, max(0.0, (dur - t) / 0.35))
    if land <= 0 or out <= 0: return None
    url = b['url']; cps = b.get('cps', 12.0); t0 = b.get('type_at', 0.6)
    n = int(max(0, min(len(url), (t - t0) * cps + 1e-6))) if t >= t0 else 0
    press = t0 + len(url) / cps + 0.45; typed_end = t0 + len(url) / cps
    blink = True if t < typed_end else int((t - typed_end) * 2.2) % 2 == 0
    caret = t < press + 0.12 and blink
    pp = (t - press) / 0.24
    sc = float(1 - 0.08 * np.sin(np.pi * pp)) if 0 <= pp <= 1 else 1
    col = C.CLAY_T if 0 <= pp <= 1 else C.CLAY
    return (land, out, n, caret, sc, col)


def cta_draw(b, state, cache):
    if 'st' not in cache: cache['st'] = cta_static(b)
    base, box, tx = cache['st']
    land, out, n, caret, sc, col = state
    e = M.ease('power3.out')(land)
    im = base.copy(); d = ImageDraw.Draw(im)
    url = b['url']
    fb = font('Poppins-Bold.ttf', 44)
    ty = box[1] + (100 if b.get('label') else 88) * U
    d.text((tx, ty), url[:n], font=fb, fill=C.INK + (255,), anchor='lm')
    if caret:
        cw = d.textlength(url[:n], font=fb)
        d.rounded_rectangle((tx + cw + 5 * U, ty - 28 * U, tx + cw + 10 * U, ty + 28 * U), int(2 * U), fill=C.CLAY + (255,))
    if b.get('button'):
        bxc, byc = box[2] - (40 + 80) * U, box[1] + CTA_BOX[3] * U / 2
        hw, hh = 80 * U * sc, 40 * U * sc
        d.rounded_rectangle((bxc - hw, byc - hh, bxc + hw, byc + hh), int(hh), fill=col + (255,))
        d.text((bxc, byc), b['button'], font=font('Poppins-SemiBold.ttf', 34 * sc), fill=(255, 255, 255, 255), anchor='mm')
    canvas = np.zeros((C.TH, C.TW, 4), np.float32)
    x, y, w, h = CTA_BOX
    cx, cy = (x + w / 2) * U, (y + h / 2 + 40 * (1 - e) + 24 * (1 - out)) * U
    place(canvas, im, cx, cy, 0.94 + 0.06 * e, min(1.0, land * 2.2) * out)
    return canvas


def cta_events(b):
    url = b['url']; cps = b.get('cps', 12.0); t0 = b.get('type_at', 0.6)
    ev = [dict(t=b['t0'] + 0.06, type='pop')]
    ev += [dict(t=b['t0'] + t0 + k / cps, type='key') for k in range(len(url))]
    if b.get('button'): ev.append(dict(t=b['t0'] + t0 + len(url) / cps + 0.45, type='click'))
    return ev


KINDS = {'words': (words_state, words_draw), 'cta': (cta_state, cta_draw)}


class Frames:
    """frames by state: the drawing (an RGBA float canvas) is made once per distinct state and kept as its uint8 box;
    each output frame is the persistent transparent frame with that box written in (what np.clip(canvas + 0.5) gave)"""

    def __init__(self, b):
        self.b = b; self.state_fn, self.draw_fn = KINDS[b['kind']]; self.cache = {}; self.boxes = {}
        self.frame = np.zeros((C.TH, C.TW, 4), np.uint8); self.last = None

    def box(self, state):
        if state not in self.boxes:
            canvas = self.draw_fn(self.b, state, self.cache)
            ys, xs = np.where(canvas[..., 3] > 0)
            if len(ys):
                y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
                self.boxes[state] = ((y0, y1, x0, x1), np.clip(canvas[y0:y1, x0:x1] + 0.5, 0, 255).astype(np.uint8))
            else:
                self.boxes[state] = None
        return self.boxes[state]

    def at(self, t):
        """the full RGBA uint8 frame for beat-relative time t (a view of the persistent buffer)"""
        state = self.state_fn(self.b, t)
        box = None if state is None else self.box(state)
        if self.last is not None:                                 # clear what the previous frame drew
            y0, y1, x0, x1 = self.last; self.frame[y0:y1, x0:x1] = 0
        if box is None: self.last = None; return self.frame
        (y0, y1, x0, x1), px = box
        self.frame[y0:y1, x0:x1] = px; self.last = (y0, y1, x0, x1)
        return self.frame


def render(bid, preview=None):
    b = M.beat(bid)
    f0, f1 = M.frames_of(b['t0'], b['t1'])
    os.makedirs(C.MEDIA, exist_ok=True); os.makedirs('preview', exist_ok=True); os.makedirs('events', exist_ok=True)
    ev = cta_events(b) if b['kind'] == 'cta' else []
    json.dump(ev, open(f'events/{bid}.json', 'w'), indent=1)
    fr = Frames(b)
    if preview is not None:
        for t in preview:
            f = fr.at(t).astype(np.float32)
            # preview on a mid-grey checker so the alpha is visible
            bg = np.full((C.TH, C.TW, 3), 90, np.float32)
            a = f[..., 3:4] / 255
            Image.fromarray((bg * (1 - a) + f[..., :3] * a).astype(np.uint8)).save(f'preview/{bid}_{t:06.2f}.png')
        print(f'{bid}: previews in preview/{bid}_*.png'); return
    out = os.path.join(C.MEDIA, f'{bid}{TAG}.mov')
    enc = M.prores4444(out, C.TW, C.TH)
    for n in range(f1 - f0):
        enc.stdin.write(fr.at(n / C.FPS).tobytes())
    enc.stdin.close(); enc.wait()
    print(f'{bid}: {f1 - f0} frames ({len(fr.boxes)} distinct drawings) -> {out} | {len(ev)} sfx events', flush=True)


def run_parallel(ids, jobs):
    import subprocess, time
    keep = [a for a in sys.argv[1:] if a not in ids and a != '--jobs' and not a.isdigit()]
    procs, pending, failed = [], list(ids), []
    while pending or procs:
        while pending and len(procs) < jobs:
            bid = pending.pop(0); procs.append((bid, subprocess.Popen([sys.executable, __file__, bid] + keep)))
        time.sleep(0.5)
        for item in procs[:]:
            if item[1].poll() is not None:
                procs.remove(item)
                if item[1].returncode: failed.append(item[0]); print(f'FAILED {item[0]} (exit {item[1].returncode})')
    return failed


if __name__ == '__main__':
    argv = sys.argv[1:]
    prev = None; jobs = 3
    if '--tag' in argv: k = argv.index('--tag'); argv = argv[:k] + argv[k + 2:]
    if '--jobs' in argv: k = argv.index('--jobs'); jobs = int(argv[k + 1]); argv = argv[:k] + argv[k + 2:]
    if '--preview' in argv:
        k = argv.index('--preview'); prev = [float(x) for x in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
    ids = [a for a in argv if not a.startswith('--')]
    if len(ids) > 1 and jobs > 1 and prev is None:
        sys.exit(1 if run_parallel(ids, jobs) else 0)
    for bid in ids:
        render(bid, prev)
