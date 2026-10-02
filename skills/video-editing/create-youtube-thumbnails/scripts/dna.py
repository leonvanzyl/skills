"""Reference DNA: measure what makes a reference thumbnail look the way it does, so the brief can copy it and QA can
prove the render kept it. The image model follows explicit words over attached images, so a brief that names a
different background than its reference produces a different background. These numbers stop that.

  python dna.py measure <ref.jpg> [--out refs/dna/<videoId>.json] [--sheet qa/dna_<videoId>.png]
        background colour + value class (sampled from the frame's left, right and top edges), whether it's a flat field
        or a scene, the dominant palette (k-means) with shares
  python dna.py fidelity <render.png> <ref.jpg> [--json qa/fidelity/<render>.json]
        background drift (Delta E), value class match, palette distance -> PASS / WARN / FAIL
  python dna.py jobs <jobs.json>
        fidelity for every rendered job against its own LAYOUT REFERENCE -> qa/fidelity/<id>.json, one line per render
  python dna.py contrast <#hex> <#hex>
        WCAG contrast ratio (text on its background: under 3.0 is blocked, under 4.5 is a warning)
"""
import argparse, json, os
import cv2
import numpy as np
from PIL import Image, ImageDraw

BG_DRIFT_FAIL = 25.0      # Delta E (CIE76) between reference and render background, flat fields
PALETTE_WARN = 30.0
MIN_TEXT_CONTRAST = 3.0      # WCAG large text: below this the render is blocked
GOOD_TEXT_CONTRAST = 4.5     # below this, a warning


def hex_of(rgb):
    return '#%02X%02X%02X' % tuple(int(round(v)) for v in rgb)


def rgb_of(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lab(rgb_rows):
    """uint8 RGB (N,3) -> real CIE Lab (N,3)."""
    a = np.asarray(rgb_rows, np.uint8).reshape(-1, 1, 3)
    l8 = cv2.cvtColor(a, cv2.COLOR_RGB2LAB).reshape(-1, 3).astype(np.float32)
    return np.stack([l8[:, 0] * 100 / 255, l8[:, 1] - 128, l8[:, 2] - 128], axis=1)


def delta_e(l1, l2):
    return float(np.linalg.norm(np.asarray(l1, np.float32) - np.asarray(l2, np.float32)))


CLASSES = ['dark', 'mid', 'light']


def value_class(L):
    return 'dark' if L < 35 else 'light' if L > 70 else 'mid'


def measure(path):
    im = Image.open(path).convert('RGB').resize((640, 360), Image.LANCZOS)
    a = np.asarray(im)
    ew, eh = 38, 22                                            # 6% side bands, 6% top band (the bottom is usually the person)
    ring = np.concatenate([a[:, :ew].reshape(-1, 3), a[:, -ew:].reshape(-1, 3), a[:eh].reshape(-1, 3)])
    rl = lab(ring)
    med_lab = np.median(rl, axis=0)
    spread = float(np.median(np.abs(rl - med_lab), axis=0).mean())
    bg_rgb = np.median(ring, axis=0)
    small = np.asarray(im.resize((160, 90))).reshape(-1, 3).astype(np.float32)
    k = 6
    _, labels, centers = cv2.kmeans(small, k, None, (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.5), 3,
                                    cv2.KMEANS_PP_CENTERS)
    shares = np.bincount(labels.ravel(), minlength=k) / labels.size
    order = np.argsort(-shares)
    palette = [[hex_of(centers[i]), round(float(shares[i]), 3)] for i in order]
    hsv = cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2HSV)
    return dict(source=os.path.basename(path), background=hex_of(bg_rgb), background_lab=[round(float(v), 1) for v in med_lab],
                background_class=value_class(float(med_lab[0])), flat=spread < 9.0, spread=round(spread, 1),
                palette=palette, mean_L=round(float(lab(np.asarray(im).reshape(-1, 3))[:, 0].mean()), 1),
                mean_saturation=round(float(hsv[..., 1].mean() / 255), 3))


def fidelity(render, ref):
    r, d = measure(render), measure(ref)
    de = delta_e(r['background_lab'], d['background_lab'])
    ref_pal = [(rgb_of(h), s) for h, s in d['palette'] if s >= 0.08]
    ren_lab = lab([rgb_of(h) for h, _ in r['palette']])
    pal = sum(s * min(delta_e(lab([c])[0], x) for x in ren_lab) for c, s in ref_pal) / max(1e-6, sum(s for _, s in ref_pal))
    problems, warnings = [], []
    step = abs(CLASSES.index(r['background_class']) - CLASSES.index(d['background_class']))
    changed = f"background value changed: reference is {d['background_class']} ({d['background']}), render is {r['background_class']} ({r['background']})"
    if d['flat']:                      # a flat field is part of the look: keep its value and colour
        if step:
            problems.append(changed)
        if de > BG_DRIFT_FAIL:
            problems.append(f"background colour drifted: Delta E {de:.0f} (reference {d['background']}, render {r['background']}; limit {BG_DRIFT_FAIL:.0f})")
    else:                              # a scene varies with the hero content: only a dark <-> light flip fails
        if step == 2:
            problems.append(changed)
        elif step == 1:
            warnings.append(changed + ' (a scene, so a warning)')
        if de > BG_DRIFT_FAIL * 1.6:
            warnings.append(f"scene background differs: Delta E {de:.0f}")
    if pal > PALETTE_WARN:
        warnings.append(f"palette distance {pal:.0f} (limit {PALETTE_WARN:.0f}): the overall colours differ from the reference")
    verdict = 'FAIL' if problems else 'WARN' if warnings else 'PASS'
    return dict(verdict=verdict, background_delta_e=round(de, 1), palette_distance=round(pal, 1), problems=problems,
                warnings=warnings, reference=d, render=r)


def luminance(h):
    c = [v / 255 for v in rgb_of(h)]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(h1, h2):
    a, b = sorted((luminance(h1), luminance(h2)), reverse=True)
    return (a + 0.05) / (b + 0.05)


def swatch_sheet(path, d, out):
    im = Image.open(path).convert('RGB').resize((480, 270))
    sheet = Image.new('RGB', (480, 270 + 70), (20, 20, 20))
    sheet.paste(im, (0, 0))
    dr = ImageDraw.Draw(sheet)
    x = 0
    for h, s in d['palette']:
        w = max(2, int(480 * s))
        dr.rectangle([x, 270, x + w, 310], fill=rgb_of(h))
        x += w
    dr.rectangle([0, 312, 60, 340], fill=rgb_of(d['background']))
    dr.text((70, 318), f"background {d['background']} ({d['background_class']}, {'flat' if d['flat'] else 'scene'})", fill=(230, 230, 230))
    sheet.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['measure', 'fidelity', 'jobs', 'contrast'])
    ap.add_argument('args', nargs='+')
    ap.add_argument('--out')
    ap.add_argument('--sheet')
    ap.add_argument('--json')
    a = ap.parse_args()
    if a.cmd == 'measure':
        d = measure(a.args[0])
        vid = os.path.splitext(os.path.basename(a.args[0]))[0][-11:]
        out = a.out or os.path.join('refs', 'dna', vid + '.json')
        os.makedirs(os.path.dirname(out), exist_ok=True)
        json.dump(d, open(out, 'w'), indent=1)
        if a.sheet:
            os.makedirs(os.path.dirname(a.sheet) or '.', exist_ok=True)
            swatch_sheet(a.args[0], d, a.sheet)
        print(f"{out}: background {d['background']} ({d['background_class']}, {'flat' if d['flat'] else 'scene'}), "
              f"palette {', '.join(h + f' {s:.0%}' for h, s in d['palette'][:4])}")
    elif a.cmd == 'fidelity':
        f = fidelity(a.args[0], a.args[1])
        if a.json:
            os.makedirs(os.path.dirname(a.json) or '.', exist_ok=True)
            json.dump(f, open(a.json, 'w'), indent=1)
        print(f"{f['verdict']}: background Delta E {f['background_delta_e']}, palette distance {f['palette_distance']}")
        for p in f['problems'] + f['warnings']:
            print('  -', p)
    elif a.cmd == 'jobs':
        base = os.path.dirname(os.path.abspath(a.args[0]))
        jobs = json.load(open(a.args[0], encoding='utf-8'))
        os.makedirs(os.path.join(base, 'qa', 'fidelity'), exist_ok=True)
        fails = 0
        for j in jobs:
            out = os.path.join(base, j['out'])
            lay = next((p for p, w in j.get('refs', []) if w.split(':', 1)[0].strip().upper() == 'LAYOUT REFERENCE'), None)
            if not lay or not os.path.exists(out):
                continue
            f = fidelity(out, os.path.join(base, os.path.expanduser(lay)))
            json.dump(f, open(os.path.join(base, 'qa', 'fidelity', j['id'] + '.json'), 'w'), indent=1)
            fails += f['verdict'] == 'FAIL'
            note = '; '.join(f['problems'] + f['warnings'])
            print(f"{j['id']:8} {f['verdict']:4}  bg dE {f['background_delta_e']:5.1f}  palette {f['palette_distance']:5.1f}  {note}")
        print(f'{fails} FAIL')
    else:
        c = contrast(a.args[0], a.args[1])
        print(f"{c:.2f}:1 ({'FAIL' if c < MIN_TEXT_CONTRAST else 'WARN' if c < GOOD_TEXT_CONTRAST else 'PASS'}: under {MIN_TEXT_CONTRAST} blocks, under {GOOD_TEXT_CONTRAST} warns)")


if __name__ == '__main__':
    main()
