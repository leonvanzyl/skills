"""Replace the image model's redrawn logo with the official mark, at the same place and size.

The model reinterprets logos even when it's given the official file (ray count, thickness, proportions drift).
This finds the rendered logo by colour inside a search box, inpaints it away, and composites the official PNG.

  python stamp.py <in.png> <logo.png> <x0,y0,x1,y1> <out.png> [--tol 60] [--rot 0] [--scale 1.0] [--sheet chk.png]

  box     search area in fractions of the frame (e.g. 0.05,0.2,0.2,0.4); keep it tight around the rendered logo
  --tol   colour distance (Lab) from the logo's main colour that counts as logo; raise it for glowing or shaded renders
  --rot   rotate the official mark (degrees, counter-clockwise) to match a tilted card
  --scale size relative to the rendered logo's bounding box (1.0 = same size)
  --sheet writes a before | after crop for QA
"""
import argparse
import cv2
import numpy as np
from PIL import Image


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('logo'); ap.add_argument('box'); ap.add_argument('out')
    ap.add_argument('--tol', type=float, default=60)
    ap.add_argument('--rot', type=float, default=0)
    ap.add_argument('--scale', type=float, default=1.0)
    ap.add_argument('--sheet')
    a = ap.parse_args()

    img = np.array(Image.open(a.src).convert('RGB'))
    H, W = img.shape[:2]
    logo = Image.open(a.logo).convert('RGBA')
    la = np.array(logo)
    solid = la[..., 3] > 200
    main_rgb = la[..., :3][solid].mean(axis=0).astype(np.uint8)

    x0, y0, x1, y1 = (float(v) for v in a.box.split(','))
    bx0, by0, bx1, by1 = int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)
    crop = img[by0:by1, bx0:bx1]
    lab = cv2.cvtColor(crop, cv2.COLOR_RGB2LAB).astype(np.float32)
    ref = cv2.cvtColor(main_rgb.reshape(1, 1, 3), cv2.COLOR_RGB2LAB).astype(np.float32)[0, 0]
    mask = (np.linalg.norm(lab - ref, axis=2) < a.tol).astype(np.uint8)
    k = max(3, int(min(crop.shape[:2]) * 0.03) | 1)
    joined = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((k, k), np.uint8))
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(joined)
    if n < 2:
        raise SystemExit('no logo-coloured region found in the box: widen the box or raise --tol')
    best = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    cx, cy, cw, ch = stats[best, :4]
    comp = (lbl == best).astype(np.uint8)

    # erase the rendered mark: inpaint a slightly dilated mask of it
    full = np.zeros((H, W), np.uint8)
    full[by0:by1, bx0:bx1] = cv2.dilate(comp, np.ones((k, k), np.uint8), iterations=2) * 255
    clean = cv2.inpaint(img, full, max(3, k), cv2.INPAINT_TELEA)

    # composite the official mark, fitted to the rendered bounding box
    bb = logo.getbbox()
    mark = logo.crop(bb)
    if a.rot:
        mark = mark.rotate(a.rot, resample=Image.BICUBIC, expand=True)
    side = max(cw, ch) * a.scale
    s = side / max(mark.size)
    mark = mark.resize((max(1, round(mark.width * s)), max(1, round(mark.height * s))), Image.LANCZOS)
    px = bx0 + cx + cw // 2 - mark.width // 2
    py = by0 + cy + ch // 2 - mark.height // 2
    out = Image.fromarray(clean).convert('RGBA')
    out.alpha_composite(mark, (int(px), int(py)))
    out = out.convert('RGB')
    out.save(a.out)
    print(f'logo found at {bx0 + cx},{by0 + cy} {cw}x{ch} px; official mark pasted at {px},{py} {mark.width}x{mark.height}')
    # provenance for report.py: which file this came from and which official mark replaced the model's version
    import json, os
    json.dump(dict(src=a.src, logo=a.logo, box=a.box, found=[int(bx0 + cx), int(by0 + cy), int(cw), int(ch)]),
              open(os.path.splitext(a.out)[0] + '.stamp.json', 'w', encoding='utf-8'), indent=1)

    if a.sheet:
        pad = int(max(cw, ch) * 0.6)
        r = (max(0, bx0 + cx - pad), max(0, by0 + cy - pad), min(W, bx0 + cx + cw + pad), min(H, by0 + cy + ch + pad))
        before = Image.fromarray(img).crop(r)
        after = out.crop(r)
        sh = Image.new('RGB', (before.width * 2 + 12, before.height), (20, 20, 20))
        sh.paste(before, (0, 0)); sh.paste(after, (before.width + 12, 0))
        sh.save(a.sheet)


if __name__ == '__main__':
    main()
