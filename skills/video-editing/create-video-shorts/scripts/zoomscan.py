"""Detect punch-ins / zooms / framing jumps baked into the source camera picture (finished edits, auto-framing webcams).
Tracks the background (left/right strips + top band of the camera window) frame-to-frame on the 10 fps proxy.
Writes zoom10.npy (t, scale, tx, ty, inliers, keypoints; tx/ty in source px) and prints the events.
Keep every camera run clear of these events.
Parallel: ZOOM_WORKERS (default 8) processes, each on a time slice that starts one frame early so the frame-to-frame
match at the slice boundary is the same one the sequential pass makes (identical rows).
usage: python scripts/zoomscan.py"""
import subprocess, sys, os, numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C


def proxy_info():
    info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames', '-of', 'csv=p=0', C.PROXY],
                          capture_output=True, text=True).stdout.strip().split(',')
    pw, ph = int(info[0]), int(info[1])
    nfr = int(info[2]) if len(info) > 2 and info[2].isdigit() else int(round(float(C.get('duration')) * C.PROXY_FPS))
    return pw, ph, nfr


def run_slice(job):
    f0, f1, pw, ph = job
    s = pw / C.SRC_W
    wx, wy, ww, wh = [int(round(v * s)) for v in C.WINDOW]
    ww -= ww % 2; wh -= wh % 2      # ffmpeg's crop rounds odd sizes down on yuv420p; an odd width would misalign every raw frame read
    start = max(0, f0 - 1)
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{start / C.PROXY_FPS:.3f}'] if start else []) + ['-i', C.PROXY, '-frames:v', str(f1 - start),
           '-vf', f'crop={ww}:{wh}:{wx}:{wy}', '-f', 'rawvideo', '-pix_fmt', 'gray', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    n = ww * wh; prev = None; out = []; i = start
    mask = np.zeros((wh, ww), np.uint8)
    bx, by = max(8, ww // 6), max(8, wh // 6)
    mask[by:wh - by, 4:bx] = 255; mask[by:wh - by, ww - bx:ww - 4] = 255; mask[4:by, 4:ww - 4] = 255
    orb = cv2.ORB_create(1500); bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    while i < f1:
        b = p.stdout.read(n)
        if len(b) < n: break
        f = np.frombuffer(b, np.uint8).reshape(wh, ww)
        kp, des = orb.detectAndCompute(f, mask)
        sc, tx, ty, inl = 1, 0, 0, 0
        if prev is not None and des is not None and prev[1] is not None and len(kp) > 10:
            m = bf.match(prev[1], des)
            if len(m) >= 8:
                A = np.float32([prev[0][x.queryIdx].pt for x in m]); B = np.float32([kp[x.trainIdx].pt for x in m])
                M, inm = cv2.estimateAffinePartial2D(A, B, method=cv2.RANSAC, ransacReprojThreshold=2.0)
                if M is not None:
                    sc = float(np.hypot(M[0, 0], M[1, 0])); tx, ty = float(M[0, 2]) / s, float(M[1, 2]) / s; inl = int(inm.sum())
        if i >= f0: out.append([i / C.PROXY_FPS, sc, tx, ty, inl, len(kp)])
        prev = (kp, des); i += 1
    p.stdout.close(); p.wait()
    return f0, np.array(out, np.float32).reshape(-1, 6)


def main():
    pw, ph, nfr = proxy_info()
    workers = max(1, int(os.environ.get('ZOOM_WORKERS', '8')))
    edges = sorted(set([0] + [int(round(nfr * k / workers / C.PROXY_FPS)) * C.PROXY_FPS for k in range(1, workers)] + [nfr]))
    jobs = [(edges[k], edges[k + 1], pw, ph) for k in range(len(edges) - 1) if edges[k + 1] > edges[k]]
    if len(jobs) == 1:
        parts = [run_slice(jobs[0])]
    else:
        from multiprocessing import Pool
        with Pool(len(jobs)) as pool: parts = pool.map(run_slice, jobs)
    z = np.concatenate([r for _, r in sorted(parts, key=lambda x: x[0])], 0); np.save('zoom10.npy', z)
    ev = [(round(float(r[0]), 1), 'scale' if abs(r[1] - 1) > 0.012 else 'shift', round(float(r[1]), 3), round(float(np.hypot(r[2], r[3])), 1))
          for r in z if r[4] >= 8 and (abs(r[1] - 1) > 0.025 or np.hypot(r[2], r[3]) > 20 * C.SRC_W / 3840)]   # proxy-res jitter stays below this
    lost = [round(float(r[0]), 1) for r in z if r[4] < 8 and r[5] > 10]
    print(f'{len(z)} frames ({len(jobs)} parallel slices). framing events (t, kind, scale, shift_px):', ev[:200])
    print('tracking lost (cuts / transitions) at:', lost[:200])


if __name__ == '__main__':
    main()
