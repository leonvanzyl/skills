"""What is on screen in every V1 item: the full-frame camera ('cam'), a screen recording with the webcam as a
picture-in-picture ('screen', PiP window found per source file), or a screen with no face ('screen' without pip).
OBS-style recordings switch scenes mid-file, so items are sampled (3+ frames each, every 2 s in long items); items
whose samples disagree are 'mixed' - look at them before planning anything that depends on the scene.
Writes scenes.json and scenes.png (one labelled thumbnail per item - LOOK at it), and adds the scene to transcript.txt.
usage: python scripts/scenes.py"""
import json, subprocess, sys, os
from concurrent.futures import ThreadPoolExecutor
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, 'scripts'); import config as C, faces as FD, program as PG

P = json.load(open('program.json', encoding='utf-8'))
fps = P['fps']
SW, SH = 960, 540          # classification sample size


def probe_size(f):
    o = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', f],
                       capture_output=True, text=True).stdout.strip().split(',')
    return int(o[0]), int(o[1])


HW = []          # CPU decode: a CUDA context per seek costs more than it saves here


def grab(f, t, w, h):
    p = subprocess.run(['ffmpeg', '-v', 'error'] + HW + ['-ss', f'{t:.3f}', '-i', f, '-frames:v', '1', '-vf', f'scale={w}:{h}',
                        '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], capture_output=True)
    b = p.stdout
    return np.frombuffer(b, np.uint8).reshape(h, w, 3) if len(b) >= w * h * 3 else None


def classify(fr):
    d = FD.detect(fr)
    if not d: return 'screen', None
    x, y, w, h, _ = d[0]
    if h > 0.30 * SH and abs(x + w / 2 - SW / 2) < 0.2 * SW: return 'cam', [x, y, w, h]
    return 'screen', [x, y, w, h]


def pip_window(frames, faces_):
    """static-edge scan outward from the median small face (same method as the shorts skill's detect_camera)."""
    fs = np.array(faces_); ph, pw = frames[0].shape[:2]
    cx, cy = np.median(fs[:, 0] + fs[:, 2] / 2), np.median(fs[:, 1] + fs[:, 3] / 2); fh = np.median(fs[:, 3])
    gx = [np.abs(cv2.Sobel(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_32F, 1, 0, ksize=3)) for f in frames]
    gy = [np.abs(cv2.Sobel(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), cv2.CV_32F, 0, 1, ksize=3)) for f in frames]
    ex = np.mean([g > 40 for g in gx], 0); ey = np.mean([g > 40 for g in gy], 0)
    y0b, y1b = int(max(0, cy - 1.2 * fh)), int(min(ph, cy + 1.2 * fh)); x0b, x1b = int(max(0, cx - 1.2 * fh)), int(min(pw, cx + 1.2 * fh))
    colscore = ex[y0b:y1b].mean(0); rowscore = ey[:, x0b:x1b].mean(1)

    def nearest(score, c, direction, lo, hi):
        rng = range(int(c - 0.5 * fh), lo, -1) if direction < 0 else range(int(c + 0.5 * fh), hi)
        for i in rng:
            if score[i] > 0.4:
                j = i
                while lo < j + direction < hi and score[j + direction] > score[j]: j += direction
                return j
        return lo if direction < 0 else hi - 1
    L = nearest(colscore, cx, -1, 0, pw); R = nearest(colscore, cx, 1, 0, pw)
    T = nearest(rowscore, cy, -1, 0, ph); B = nearest(rowscore, cy, 1, 0, ph)
    return [L, T, R - L, B - T]


def main():
    jobs = []
    for it in P['items']:
        d = it['t1'] - it['t0']
        ts = [d / 2] if d < 1.2 else sorted(set([0.25, d / 2, d - 0.25] + list(np.arange(2.0, d - 1.0, 2.0))))
        for t in ts:
            jobs.append((it['v1'], it['t0'] + t, it['file'], (it['src0'] + t * fps) / fps))
    print(f'sampling {len(jobs)} frames from {len(P["items"])} items ...')
    with ThreadPoolExecutor(8) as ex:
        frames = list(ex.map(lambda j: grab(j[2], j[3], SW, SH), jobs))
    res = {}
    by_file = {}
    for (v1, t, f, st), fr in zip(jobs, frames):
        if fr is None: continue
        sc, box = classify(fr)
        res.setdefault(v1, []).append((round(t, 2), sc, box, st))
        if sc == 'screen' and box: by_file.setdefault(f, []).append(st)
    # PiP window per source file, measured on 1920-wide samples of its screen frames
    files = {}
    for f in sorted({it['file'] for it in P['items']}):
        sw_, sh_ = probe_size(f); sts = by_file.get(f, [])
        entry = dict(size=[sw_, sh_], pip=None, safe=None)
        if len(sts) >= 4:
            pick = [sts[int(k)] for k in np.linspace(0, len(sts) - 1, min(24, len(sts)))]
            with ThreadPoolExecutor(8) as ex:
                big = [b for b in ex.map(lambda st: grab(f, st, 1920, 1080), pick) if b is not None]
            fcs = [FD.detect(b)[0][:4] for b in big if FD.detect(b)]
            if len(fcs) >= 3:
                s = sw_ / 1920
                win = [int(round(v * s)) for v in pip_window(big, fcs)]
                ins = int(round(12 * sw_ / 3840)) or 2
                entry['pip'] = win
                entry['safe'] = [win[0] + ins, win[1] + ins, (win[2] - 2 * ins) // 2 * 2, (win[3] - 2 * ins) // 2 * 2]
        entry['face_c'] = [float(np.median([b[0] + b[2] / 2 for b in fcs])) * s, float(np.median([b[1] + b[3] / 2 for b in fcs])) * s] if len(sts) >= 4 and len(fcs) >= 3 else None
        files[f] = entry
    # OBS scenes put the webcam in the same place in every recording: a file whose edge scan ran off (implausible
    # shape) takes the consensus window, as long as its face sits inside it
    good = [v['pip'] for v in files.values() if v['pip'] and 1.1 <= v['pip'][3] / v['pip'][2] <= 1.6 or v['pip'] and 0.45 <= v['pip'][3] / v['pip'][2] <= 0.8]
    if good:
        cons = [int(np.median([g[k] for g in good])) for k in range(4)]
        for f, v in files.items():
            if not v['pip'] or v['pip'] in good or not v.get('face_c'): continue
            fx, fy = v['face_c']; x, y, w, h = cons
            if x <= fx <= x + w and y <= fy <= y + h:
                print(f'{os.path.basename(f)}: pip {v["pip"]} looks wrong - using the consensus {cons}')
                v['pip'] = cons; ins = int(round(12 * v['size'][0] / 3840)) or 2
                v['safe'] = [x + ins, y + ins, (w - 2 * ins) // 2 * 2, (h - 2 * ins) // 2 * 2]; v['pip_from'] = 'consensus'
    items = {}
    for it in P['items']:
        smp = res.get(it['v1'], [])
        kinds = [s[1] for s in smp]
        scene = kinds[0] if kinds and all(k == kinds[0] for k in kinds) else ('mixed' if kinds else 'unknown')
        e = dict(scene=scene, samples=[[t, k] for t, k, _, _ in smp])
        if scene == 'cam':
            s = files[it['file']]['size'][0] / SW
            bx = np.median(np.array([b for _, k, b, _ in smp if k == 'cam']), 0)
            e['face'] = [int(round(v * s)) for v in bx]          # source px: x, y, w, h (for punch-in framing)
        if scene in ('screen', 'mixed'):
            e['pip'] = files[it['file']]['pip']
        items[str(it['v1'])] = e
    json.dump(dict(files=files, items=items), open('scenes.json', 'w'), indent=1)
    PG.write_transcript(P)
    # contact sheet: one thumbnail per item
    tw, th, cols = 320, 180, 12
    rows = (len(P['items']) + cols - 1) // cols
    S = Image.new('RGB', (cols * tw, rows * th), 'black'); d = ImageDraw.Draw(S)
    try: font = ImageFont.truetype(C.FONTS + 'Poppins-SemiBold.ttf', 18)
    except Exception: font = ImageFont.load_default()
    thumbs = {}
    for (v1, t, f, st), fr in zip(jobs, frames):
        if fr is not None and v1 not in thumbs: thumbs[v1] = fr
    for it in P['items']:
        k = it['v1']; x, y = (k % cols) * tw, (k // cols) * th
        if k in thumbs: S.paste(Image.fromarray(cv2.cvtColor(cv2.resize(thumbs[k], (tw, th)), cv2.COLOR_BGR2RGB)), (x, y))
        sc = items[str(k)]['scene']
        d.text((x + 6, y + 4), f"{k} {PG.tc(it['t0'])} {sc}", fill=(255, 255, 0) if sc != 'mixed' else (255, 80, 80), font=font, stroke_width=2, stroke_fill='black')
    S.save('scenes.png')
    n = {}
    for e in items.values(): n[e['scene']] = n.get(e['scene'], 0) + 1
    print('scenes:', n, '| pip windows:', {os.path.basename(f): v['pip'] for f, v in files.items()}, '| LOOK at scenes.png')


if __name__ == '__main__':
    main()
