"""Gaze / eye-contact features at 10 fps from the proxy (never the master).
Columns of gaze10.npy: t, ok, lookdown, pitch, yaw, eye_dist_src, eye_cx_src, eye_cy_src, fullframe_face
 - pitch/yaw: head pose (deg). Reading a screen shows up as a pitch/yaw shift away from the on-lens cluster.
 - fullframe_face: 1 when a large centred face fills the whole frame (a finished edit cutting to a full-frame camera shot)
Prints the two pose clusters + candidate on-lens runs. Confirm with eyesheet.py before trusting them.
Parallel: the proxy is split into GAZE_WORKERS (default 8) time slices, each in its own process with its own landmarker
(VIDEO mode). Every slice warms its tracker up on the 10 frames before its first frame, so the rows match a single
sequential pass. A 15 min master: ~7 min sequential -> under a minute.
usage: python scripts/gaze.py"""
import subprocess, sys, os, numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C
WARM = 10   # warm-up frames (1 s) before each slice, processed but not kept


def proxy_info():
    info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames', '-of', 'csv=p=0', C.PROXY],
                          capture_output=True, text=True).stdout.strip().split(',')
    pw, ph = int(info[0]), int(info[1])
    nfr = int(info[2]) if len(info) > 2 and info[2].isdigit() else int(round(float(C.get('duration')) * C.PROXY_FPS))
    return pw, ph, nfr


def run_slice(job):
    """rows for proxy frames [f0, f1); decodes from f0-WARM so the VIDEO-mode tracker has history at f0"""
    f0, f1, pw, ph = job
    import mediapipe as mp
    from mediapipe.tasks import python as mpt
    from mediapipe.tasks.python import vision
    import faces as FD
    s = pw / C.SRC_W
    wx, wy, ww, wh = [int(round(v * s)) for v in C.WINDOW]
    ww -= ww % 2; wh -= wh % 2
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(base_options=mpt.BaseOptions(model_asset_path='face_landmarker.task'),
        output_face_blendshapes=True, output_facial_transformation_matrixes=True, num_faces=1, running_mode=vision.RunningMode.VIDEO))
    start = max(0, f0 - WARM)
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{start / C.PROXY_FPS:.3f}'] if start else []) + ['-i', C.PROXY, '-frames:v', str(f1 - start), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    rows = []; i = start; n = pw * ph * 3; last_full = 0
    while i < f1:
        b = p.stdout.read(n)
        if len(b) < n: break
        fr = np.frombuffer(b, np.uint8).reshape(ph, pw, 3); t = i / C.PROXY_FPS
        full = 0
        if C.MODE == 'pip' and i % 2 == 0:
            d = FD.detect(cv2.cvtColor(cv2.resize(fr, (pw // 4, ph // 4)), cv2.COLOR_RGB2BGR))
            full = int(bool(d) and d[0][3] > ph / 4 * 0.30 and abs(d[0][0] + d[0][2] / 2 - pw / 8) < pw / 4 * 0.2)
        elif C.MODE == 'pip': full = last_full
        last_full = full
        crop = np.ascontiguousarray(fr[wy:wy + wh, wx:wx + ww]) if C.MODE == 'pip' else fr
        r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=crop), int(i * 1000 / C.PROXY_FPS))
        if i >= f0:
            if r.face_landmarks:
                bs = {c.category_name: c.score for c in r.face_blendshapes[0]}
                R = np.array(r.facial_transformation_matrixes[0])[:3, :3]
                pitch = np.degrees(np.arctan2(-R[2, 1], R[2, 2])); yaw = np.degrees(np.arcsin(np.clip(R[2, 0], -1, 1)))
                L = r.face_landmarks[0]; ch, cw = crop.shape[:2]
                ox, oy = (wx, wy) if C.MODE == 'pip' else (0, 0)
                ex = ((L[33].x + L[263].x) / 2 * cw + ox) / s; ey = ((L[33].y + L[263].y) / 2 * ch + oy) / s
                ed = np.hypot((L[33].x - L[263].x) * cw, (L[33].y - L[263].y) * ch) / s
                rows.append([t, 1, (bs['eyeLookDownLeft'] + bs['eyeLookDownRight']) / 2, pitch, yaw, ed, ex, ey, full])
            else:
                rows.append([t, 0, 0, 0, 0, 0, 0, 0, full])
        i += 1
    p.stdout.close(); p.wait()
    return f0, np.array(rows, np.float32).reshape(-1, 9)


def main():
    pw, ph, nfr = proxy_info()
    workers = max(1, int(os.environ.get('GAZE_WORKERS', '8')))
    # slice on whole seconds (the proxy's keyframes) so every slice seeks frame-exactly
    edges = sorted(set([0] + [int(round(nfr * k / workers / C.PROXY_FPS)) * C.PROXY_FPS for k in range(1, workers)] + [nfr]))
    jobs = [(edges[k], edges[k + 1], pw, ph) for k in range(len(edges) - 1) if edges[k + 1] > edges[k]]
    if len(jobs) == 1:
        parts = [run_slice(jobs[0])]
    else:
        from multiprocessing import Pool
        with Pool(len(jobs)) as pool: parts = pool.map(run_slice, jobs)
    g = np.concatenate([r for _, r in sorted(parts, key=lambda x: x[0])], 0); np.save('gaze10.npy', g)
    ok = g[:, 1] > 0
    feat = np.stack([g[ok, 3], g[ok, 4]], 1)
    crit = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 50, 0.1)
    _, lab, cen = cv2.kmeans(feat.astype(np.float32), 2, None, crit, 5, cv2.KMEANS_PP_CENTERS)
    print(f'{len(g)} frames, face found in {ok.mean()*100:.0f}% ({len(jobs)} parallel slices)')
    for k in range(2):
        print(f' pose cluster {k}: pitch {cen[k,0]:.1f} yaw {cen[k,1]:.1f}  share {np.mean(lab==k)*100:.0f}%')
    print(' The on-lens cluster is NOT always the frontal one: with the webcam beside the screen, looking at the lens is a head turn')
    print(' (yaw ~10-15 deg) and reading the screen is frontal and slightly down. Identify it with eyesheet.py on a line you know is')
    print(' said to camera (the outro / CTA), then label every line from that.')
    if C.MODE == 'pip' and g[:, 8].mean() > 0.01:
        f = g[:, 8] > 0; runs = []; st = None
        for j, v in enumerate(f):
            if v and st is None: st = j
            if not v and st is not None: runs.append((st / 10, j / 10)); st = None
        print(' full-frame camera shots (usable 4K camera; mark lines "cam": "fullframe"):', [(round(a, 1), round(b, 1)) for a, b in runs if b - a > 0.8])


if __name__ == '__main__':
    main()
