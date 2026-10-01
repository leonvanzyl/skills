"""GPU background-removal matte for split beats (replaces `hyperframes remove-background`, whose onnxruntime-node build
has no CUDA on Windows and crawls on the CPU at 2-3 fps). Runs the SAME model HyperFrames caches
(u2net_human_seg.onnx) on onnxruntime-gpu, frame by frame from the frame-exact camera clip, so the matte stays
frame-locked with the card. Ported from create-video-shorts.
  input   split/<bid>_cam.mp4   (compose.py --matte makes it: the camera region at <= 1280 px, frame-exact to V1)
  output  split/<bid>_matte.mov RGBA (rgb = the clip frame, alpha = the matte), same size and frame count, lossless FFV1
Cleanup: a horizontal opening drops thin vertical strips that touch the head (a guitar headstock, a mic arm, a lamp
pole - the first project's lesson), then only the largest connected component (the speaker) is kept and grown back so
hair edges keep the model's own soft alpha, and the clip's top rows are feathered (the PiP window border).
Speed: frames are pipelined over --threads (default 3) workers per clip (ORT and OpenCV release the GIL); several
beats run at once with --jobs. A 300-frame beat takes seconds instead of minutes.
usage: python scripts/matte_gpu.py g03 [g07 ...] [--jobs 3] [--threads 3]
Falls back to the HyperFrames CLI (CPU) by itself when the model isn't cached yet or CUDA is missing."""
import os, sys, glob, site, subprocess, time, collections, numpy as np, cv2
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp, 'nvidia', '*', 'bin')):
        os.add_dll_directory(d); os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, 'scripts'); import media as M

MODEL = os.path.expanduser('~/.cache/hyperframes/background-removal/models/u2net_human_seg.onnx')
try:
    import onnxruntime as ort
    GPU = os.path.exists(MODEL) and 'CUDAExecutionProvider' in ort.get_available_providers()
except ImportError:
    ort = None; GPU = False
if GPU:
    sess = ort.InferenceSession(MODEL, providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
    GPU = 'CUDAExecutionProvider' in sess.get_providers()
INP = sess.get_inputs()[0].name if GPU else None
MEAN = np.array([0.485, 0.456, 0.406], np.float32); STD = np.array([0.229, 0.224, 0.225], np.float32)
CODEC = ['-c:v', 'ffv1', '-level', '3', '-slices', '16', '-slicecrc', '0', '-pix_fmt', 'bgra']
TOP_FEATHER = 14; TOP_RAMP = np.linspace(0, 1, TOP_FEATHER, dtype=np.float32) ** 1.5
THIN_SRC = 80       # source px: background objects narrower than this that touch the head are cut away


def keep_mask(pred, w):
    m = (pred > 0.5).astype(np.uint8)
    k = max(3, int(round(THIN_SRC * 320 / w)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((1, k), np.uint8))
    nl, lab, st, _ = cv2.connectedComponentsWithStats(m, connectivity=8)
    if nl < 2: return np.ones_like(pred)
    keep = (lab == 1 + int(np.argmax(st[1:, cv2.CC_STAT_AREA]))).astype(np.uint8)
    keep = cv2.dilate(keep, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    return np.clip(cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 2.5), 0, 1)


def matte_frame(b, w, h):
    fr = np.frombuffer(b, np.uint8).reshape(h, w, 3)
    x = cv2.resize(fr, (320, 320), interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
    x = (x / max(float(x.max()), 1e-6) - MEAN) / STD
    pred = sess.run(None, {INP: x.transpose(2, 0, 1)[None]})[0][0, 0]
    pred = (pred - pred.min()) / max(float(pred.max() - pred.min()), 1e-6)
    pred = pred * keep_mask(pred, w)
    a = cv2.resize(pred, (w, h), interpolation=cv2.INTER_LINEAR)
    a[:TOP_FEATHER] *= TOP_RAMP[:, None]
    return np.dstack([fr, np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8)]).tobytes()


def fallback(bid):
    cam, out = f'split/{bid}_cam.mp4', f'split/{bid}_matte.mov'
    log = open(f'split/{bid}_matte.log', 'w')
    r = subprocess.run(f'npx --yes hyperframes remove-background {cam} -o {out} --device cuda', shell=True, stdout=log, stderr=log)
    if r.returncode != 0:
        print('GPU matting unavailable - using the HyperFrames CLI on the CPU (about 2-3 fps)')
        subprocess.run(f'npx --yes hyperframes remove-background {cam} -o {out} --device cpu', shell=True, check=True, stdout=log, stderr=log)
    print(f'{bid}: matte (CLI) -> {out}')


def matte(bid, threads=3):
    if not GPU: return fallback(bid)
    cam, out = f'split/{bid}_cam.mp4', f'split/{bid}_matte.mov'
    p = M.probe(cam); w, h = p['width'], p['height']; n = w * h * 3
    dec = M.reader_proc(['ffmpeg', '-v', 'error', '-i', cam, '-vf', M.dec_vf(cam), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    enc = M.writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', str(M.C.FPS), '-i', '-'] + CODEC + [out])
    k = 0; t0 = time.time(); pending = collections.deque()
    with ThreadPoolExecutor(threads) as ex:
        while True:
            b = M.read_exact(dec.stdout, n)
            if b is None: break
            pending.append(ex.submit(matte_frame, bytes(b), w, h))
            while len(pending) > 2 * threads: enc.stdin.write(pending.popleft().result()); k += 1
        while pending: enc.stdin.write(pending.popleft().result()); k += 1
    enc.stdin.close(); enc.wait(); dec.stdout.close(); dec.wait()
    print(f'{bid}: matte {k} frames {w}x{h} on the GPU in {time.time() - t0:.1f}s -> {out}', flush=True)


if __name__ == '__main__':
    args = sys.argv[1:]; jobs = 3; threads = 3
    if '--jobs' in args: k = args.index('--jobs'); jobs = int(args[k + 1]); del args[k:k + 2]
    if '--threads' in args: k = args.index('--threads'); threads = int(args[k + 1]); del args[k:k + 2]
    ids = [a for a in args if not a.startswith('--')]
    print('matte on', 'GPU (onnxruntime-gpu CUDA)' if GPU else 'CPU fallback (hyperframes remove-background)')
    t = time.time()
    with ThreadPoolExecutor(max(1, min(jobs, len(ids)))) as ex: list(ex.map(lambda b: matte(b, threads), ids))
    print(f'all {len(ids)} mattes in {time.time() - t:.1f}s')
