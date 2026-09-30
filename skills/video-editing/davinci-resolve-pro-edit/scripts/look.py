"""See the programme at given times, with a SOURCE-pixel grid, to pick zoom targets and highlight rectangles.
  python scripts/look.py 6.2 9.8 12.0              -> look/<t>.jpg (1920 wide, grid every 200 source px, labelled)
  python scripts/look.py 6.2 --rect 1100,560,1560,80 --zoom 1.5,1600,700
        draws a rectangle (x,y,w,h source px) and the view a zoom of k centred on fx,fy would show (k,fx,fy)
Prints which V1 item, source file and source time each frame comes from."""
import sys, os
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as M

argv = sys.argv[1:]
rect = zoom = None
if '--rect' in argv:
    k = argv.index('--rect'); rect = [float(v) for v in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
if '--zoom' in argv:
    k = argv.index('--zoom'); zoom = [float(v) for v in argv[k + 1].split(',')]; argv = argv[:k] + argv[k + 2:]
os.makedirs('look', exist_ok=True)
for a in argv:
    t = float(a); n = int(round(t * C.FPS))
    (f, it, sf), = M.source_map(n, n + 1)
    p = M.probe(f); W, H = p['width'], p['height']
    fr = next(M.decode([(f, it, sf)], W, H))
    img = cv2.cvtColor(np.ascontiguousarray(fr), cv2.COLOR_RGB2BGR)
    step = 200 if W >= 2560 else 100
    for x in range(0, W, step):
        cv2.line(img, (x, 0), (x, H), (0, 255, 255) if x % 1000 == 0 else (0, 160, 160), 2 if x % 1000 == 0 else 1)
        cv2.putText(img, str(x), (x + 4, 36), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
    for y in range(0, H, step):
        cv2.line(img, (0, y), (W, y), (0, 255, 255) if y % 1000 == 0 else (0, 160, 160), 2 if y % 1000 == 0 else 1)
        cv2.putText(img, str(y), (6, y - 8), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 255, 255), 3)
    if rect:
        x, y, w, h = [int(v) for v in rect]; cv2.rectangle(img, (x, y), (x + w, y + h), (87, 119, 217), 6)
    if zoom:
        k, fx, fy = zoom; kfit = min(C.TW / W, C.TH / H); vw, vh = C.TW / (k * kfit), C.TH / (k * kfit)
        cv2.rectangle(img, (int(fx - vw / 2), int(fy - vh / 2)), (int(fx + vw / 2), int(fy + vh / 2)), (255, 80, 255), 6)
        import json
        S = json.load(open('scenes.json')) if os.path.exists('scenes.json') else {'files': {}}
        win = (S['files'].get(f) or {}).get('pip')
        if win:     # what the held-still PiP will cover in this zoomed view (keep targets out of the red box)
            px, py, pw, ph = [v * kfit for v in win]
            sx0, sy0 = fx + (px - C.TW / 2) / (k * kfit), fy + (py - C.TH / 2) / (k * kfit)
            cv2.rectangle(img, (int(sx0), int(sy0)), (int(sx0 + pw / (k * kfit)), int(sy0 + ph / (k * kfit))), (40, 40, 255), 6)
    out = f'look/{t:07.2f}.jpg'
    cv2.imwrite(out, cv2.resize(img, (1920, int(1920 * H / W)), interpolation=cv2.INTER_AREA), [cv2.IMWRITE_JPEG_QUALITY, 88])
    print(f'{out}  t={t:.2f}s  V1 item {it["v1"]}  {os.path.basename(f)} @ {sf / C.FPS:.2f}s (frame {sf})  source {W}x{H}')
