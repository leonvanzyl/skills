"""GPU background-removal matte for split runs (replacement for `hyperframes remove-background` when its onnxruntime-node
build has no CUDA). Runs the SAME model HyperFrames caches (u2net_human_seg.onnx) on onnxruntime-gpu, frame by frame from
the frame-exact camera clip, so the matte stays frame-locked with the card.
Output: <sk>/cam/r<i>_matte.mov, RGBA (rgb = the clip frame, alpha = the matte), same size and frame count as the clip.
Cleanup: only the largest connected component (the speaker) is kept, so background fragments (a guitar neck, a lamp)
never pop out above the card edge.
usage: python scripts/matte_gpu.py s1:0,3,5 s2:0,3 ... [--jobs 3]"""
import os, sys, glob, site, subprocess, time, numpy as np, cv2
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp, 'nvidia', '*', 'bin')):
        os.add_dll_directory(d); os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
import onnxruntime as ort

MODEL = os.path.expanduser('~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx')
GPU = os.path.exists(MODEL) and 'CUDAExecutionProvider' in ort.get_available_providers()
if GPU:
    sess = ort.InferenceSession(MODEL, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    GPU = 'CUDAExecutionProvider' in sess.get_providers()
print('matte on', 'GPU (onnxruntime-gpu CUDA)' if GPU else 'CPU fallback: hyperframes remove-background (model not cached yet or no CUDA)')
INP = sess.get_inputs()[0].name if GPU else None
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)


def size_of(path):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', path],
                       capture_output=True, text=True).stdout.strip().split(',')
    return int(o[0]), int(o[1])


TOP_FEATHER = 14   # source rows faded in at the clip's top edge (hair sits well below it; objects cut by the border vanish)
TOP_RAMP = np.linspace(0, 1, TOP_FEATHER, dtype=np.float32) ** 1.5
THIN_SRC = 80   # source px: background objects narrower than this (a guitar neck, a mic arm, a lamp pole) are cut away


def keep_mask(pred, w):
    """soft gate (320x320) that keeps only the speaker: a horizontal opening removes thin vertical strips that touch the
    head (they merge into one blob, so a component test alone can't drop them), then the largest blob is kept and grown
    back so hair edges keep the model's own soft alpha."""
    m = (pred > 0.5).astype(np.uint8)
    k = max(3, int(round(THIN_SRC * 320 / w)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, k), np.uint8))
    nl, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if nl < 2: return np.ones_like(pred)
    keep = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return np.clip(cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 2.5), 0, 1)


def matte_fallback(sk, i):
    src = f'{sk}/cam/r{i}.mkv'; out = f'{sk}/cam/r{i}_matte.mov'; mp4 = f'{sk}/cam/r{i}.mp4'
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-c:v', 'libx264', '-crf', '8', '-pix_fmt', 'yuv444p', mp4], check=True)
    subprocess.run(f'npx --yes hyperframes remove-background {mp4} -o {out}', shell=True, check=True)   # also caches the model for next time
    print(f'{sk} r{i}: CPU fallback -> {out}')


def matte(sk, i):
    if not GPU: return matte_fallback(sk, i)
    src = f'{sk}/cam/r{i}.mkv'; out = f'{sk}/cam/r{i}_matte.mov'
    w, h = size_of(src); n = w * h * 3
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, bufsize=10 ** 8)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', '60', '-i', '-',
                            '-c:v', 'png', '-compression_level', '1', '-pix_fmt', 'rgba', out], stdin=subprocess.PIPE)
    k = 0; t0 = time.time()
    while True:
        b = dec.stdout.read(n)
        if len(b) < n: break
        fr = np.frombuffer(b, np.uint8).reshape(h, w, 3)
        x = cv2.resize(fr, (320, 320), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
        x = (x / max(float(x.max()), 1e-6) - MEAN) / STD
        pred = sess.run(None, {INP: x.transpose(2, 0, 1)[None]})[0][0, 0]
        pred = (pred - pred.min()) / max(float(pred.max() - pred.min()), 1e-6)
        pred = pred * keep_mask(pred, w)
        a = cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)
        a[:TOP_FEATHER] *= TOP_RAMP[:, None]   # the clip's top edge is the window border: nothing real pops out through it
        rgba = np.dstack([fr, np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)])
        enc.stdin.write(rgba.tobytes()); k += 1
    enc.stdin.close(); enc.wait(); dec.wait()
    print(f'{sk} r{i}: {k} frames {w}x{h} in {time.time() - t0:.1f}s -> {out}')


from concurrent.futures import ThreadPoolExecutor   # ORT + OpenCV release the GIL; ffmpeg decode/encode are separate processes
args = sys.argv[1:]; jobs = 3
if '--jobs' in args: k = args.index('--jobs'); jobs = int(args[k + 1]); del args[k:k + 2]
todo = [(spec.split(':')[0], int(i)) for spec in args for i in spec.split(':')[1].split(',')]
t_all = time.time()
with ThreadPoolExecutor(jobs) as ex: list(ex.map(lambda a: matte(*a), todo))
print(f'all {len(todo)} mattes in {time.time() - t_all:.1f}s')
