"""Find where the speaker's camera lives in the frame and write it to project.json -> "camera".
  mode 'full' : the frame IS the camera (raw talking-head footage)
  mode 'pip'  : a webcam window inside a screen recording (finished long-form edit); window = its rectangle
Reads the 10 fps proxy only. Always LOOK at detect_camera.png afterwards and correct project.json if needed.
usage: python scripts/detect_camera.py"""
import subprocess, sys, json, numpy as np, cv2
sys.path.insert(0, 'scripts'); import config as C

W = C.PROXY_W
info = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,nb_frames', '-of', 'csv=p=0', C.PROXY], capture_output=True, text=True).stdout.strip().split(',')
pw, ph = int(info[0]), int(info[1]); nfr = int(info[2]) if info[2].isdigit() else int(C.get('duration') * 10)
idx = np.linspace(5, nfr - 5, 90).astype(int)
p = subprocess.run(['ffmpeg', '-v', 'error', '-i', C.PROXY, '-vf', 'select=' + '+'.join(f'eq(n\\,{i})' for i in idx), '-vsync', '0',
                    '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
frames = np.frombuffer(p.stdout, np.uint8).reshape(-1, ph, pw, 3)
import faces as FD
faces = []
for f in frames:
    d = FD.detect(f)
    if d: faces.append([int(v) for v in d[0][:4]])
faces = np.array(faces)
if len(faces) == 0:
    print('no face found in the samples - set camera manually in project.json'); sys.exit(1)
# a real full-frame camera face is large AND horizontally central; a webcam window sits off to a side
fcx = faces[:, 0] + faces[:, 2] / 2
big = (faces[:, 3] > 0.30 * ph) & (np.abs(fcx - pw / 2) < 0.2 * pw)
s = C.SRC_W / pw
if big.mean() > 0.5:
    cam = {'mode': 'full', 'window': [0, 0, C.SRC_W, C.SRC_H], 'safe': [0, 0, C.SRC_W, C.SRC_H]}
else:
    small = faces[~big]
    cx, cy = np.median(small[:, 0] + small[:, 2] / 2), np.median(small[:, 1] + small[:, 3] / 2)
    fh = np.median(small[:, 3])
    # static edges: fraction of sampled frames with a strong gradient at each pixel
    gx = [np.abs(cv2.Sobel(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_32F, 1, 0, ksize=3)) for f in frames]
    gy = [np.abs(cv2.Sobel(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_32F, 0, 1, ksize=3)) for f in frames]
    ex = np.mean([g > 40 for g in gx], 0); ey = np.mean([g > 40 for g in gy], 0)
    y0b, y1b = int(max(0, cy - 1.2 * fh)), int(min(ph, cy + 1.2 * fh)); x0b, x1b = int(max(0, cx - 1.2 * fh)), int(min(pw, cx + 1.2 * fh))
    colscore = ex[y0b:y1b].mean(0); rowscore = ey[:, x0b:x1b].mean(1)
    def nearest(score, c, direction, lo, hi):
        # first static edge outward from just outside the face centre; snap to that peak's maximum
        rng = range(int(c - 0.5 * fh), lo, -1) if direction < 0 else range(int(c + 0.5 * fh), hi)
        for i in rng:
            if score[i] > 0.4:
                j = i
                while lo < j + direction < hi and score[j + direction] > score[j]: j += direction
                return j
        return lo if direction < 0 else hi - 1
    L = nearest(colscore, cx, -1, 0, pw); R = nearest(colscore, cx, 1, 0, pw)
    T = nearest(rowscore, cy, -1, 0, ph); B = nearest(rowscore, cy, 1, 0, ph)
    win = [int(round(L * s)), int(round(T * s)), int(round((R - L) * s)), int(round((B - T) * s))]
    ins = int(round(12 * C.SRC_W / 3840)) or 2
    safe = [win[0] + ins, win[1] + ins, (win[2] - 2 * ins) // 2 * 2, (win[3] - 2 * ins) // 2 * 2]
    cam = {'mode': 'pip', 'window': win, 'safe': safe}
old = C.get('camera', {})
for k in ('fullframe_slice',):
    if k in old: cam[k] = old[k]
C.save(camera=cam)
# verification image
vis = frames[len(frames) // 2].copy()
for (x, y, w, h) in faces: cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 200, 255), 1)
x, y, w, h = [int(v / s) for v in cam['window']]; cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 3)
x, y, w, h = [int(v / s) for v in cam['safe']]; cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 255, 0), 2)
cv2.imwrite('detect_camera.png', cv2.resize(vis, (960, int(960 * ph / pw))))
print(json.dumps(cam), '| faces found in', len(faces), 'of', len(frames), 'samples | check detect_camera.png (red=window, green=safe)')
