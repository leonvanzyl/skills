"""Graphics assets cut from the recording itself (the real UI, the real numbers) into gfx/assets/, and their sizes
into gfx/asset_dims.json (build_gfx_common.D).
  python scripts/assets.py still 260.0 700,880,1100,200 usage_fable.png         a programme-time still, cropped (SOURCE px)
  python scripts/assets.py still src:7.mkv@473.27 0,60,3080,1740 game.png       a still from any source time
  python scripts/assets.py clip g03 640,300,1240,1500 panel.mp4                 footage synced to beat g03 (follows V1)
Crops must avoid the webcam window (scenes.json -> files -> pip). Stills are PNG at source resolution (max 2400 wide)."""
import sys, os, json, subprocess
import numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C, media as M

A = 'gfx/assets'; DIMS = 'gfx/asset_dims.json'


def save_dims(name, wh):
    d = json.load(open(DIMS)) if os.path.exists(DIMS) else {}
    d[name] = list(wh); json.dump(d, open(DIMS, 'w'), indent=1)


def resolve_src(spec):
    """'260.0' -> programme time; 'src:7.mkv@473.27' -> a source file (matched by name) at seconds"""
    if spec.startswith('src:'):
        name, t = spec[4:].rsplit('@', 1)
        f = next(it['file'] for it in M.program()['items'] if os.path.basename(it['file']) == name or it['file'] == name)
        it = next(i for i in M.program()['items'] if i['file'] == f)
        return f, it, int(round(float(t) * C.FPS))
    n = int(round(float(spec) * C.FPS))
    return M.source_map(n, n + 1)[0]


def still(spec, crop, out, maxw=2400):
    f, it, sf = resolve_src(spec)
    x, y, w, h = crop
    fr = next(M.decode([(f, it, sf)], w, h, f'crop={w}:{h}:{x}:{y}'))
    if w > maxw: fr = cv2.resize(fr, (maxw, int(h * maxw / w)), interpolation=cv2.INTER_AREA)
    os.makedirs(A, exist_ok=True)
    cv2.imwrite(f'{A}/{out}', cv2.cvtColor(np.ascontiguousarray(fr), cv2.COLOR_RGB2BGR))
    save_dims(out, (fr.shape[1], fr.shape[0])); print(f'{A}/{out}', fr.shape[1], 'x', fr.shape[0])


def clip(bid, crop, out, maxw=2000):
    b = M.beat(bid); f0, f1 = M.frames_of(b['t0'], b['t1']); seq = M.source_map(f0, f1)
    x, y, w, h = crop; sc = min(1.0, maxw / w); ow, oh = int(w * sc) // 2 * 2, int(h * sc) // 2 * 2
    os.makedirs(A, exist_ok=True)
    enc = M.writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{ow}x{oh}', '-r', str(C.FPS), '-i', '-',
                         '-c:v', 'libx264', '-crf', '12', '-g', '12', '-pix_fmt', 'yuv420p', '-an', f'{A}/{out}'])
    for fr in M.decode(seq, w, h, f'crop={w}:{h}:{x}:{y}'):
        enc.stdin.write((fr if sc == 1 else cv2.resize(fr, (ow, oh), interpolation=cv2.INTER_AREA)).tobytes())
    enc.stdin.close(); enc.wait()
    save_dims(out, (ow, oh)); print(f'{A}/{out}', ow, 'x', oh, f'{f1 - f0} frames (synced to {bid})')


if __name__ == '__main__':
    kind, spec, crop, out = sys.argv[1:5]
    crop = [int(float(v)) for v in crop.split(',')]
    (still if kind == 'still' else clip)(spec, crop, out)
