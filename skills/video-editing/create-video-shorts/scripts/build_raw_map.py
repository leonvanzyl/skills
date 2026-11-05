"""Rebuild a finished long-form edit's map (final-video time -> raw recording + time) and a clean voice stem on the final
video's timeline, when the davinci-resolve-pro-edit work folder is gone (edited on another machine, cleaned up) but the raw
recordings sit next to the export. Learned on the "Last Call" shorts (2026-10-19): the export had the game playing under the
intro and ~130 library SFX under the talk, and neither voice48.wav nor program.json survived.
How: each raw track is extracted once (raw/<name>.16k.wav and .48k.wav). Every 0.5 s window of the export's audio is then
searched in ALL raw tracks at once (FFT cross-correlation, normalised; on the GPU when torch has CUDA, ~25 s for a 25 min
export against an hour of raw), or first right after the previous match (cheap, so the CPU fallback stays usable).
Consecutive windows with the same raw offset merge into pieces, and each boundary is refined to 10 ms with the same
two-offset error split clean_from_stem.py uses. Writes:
  longform_program.json  {"fps", "dur", "items": [{t0, t1, file, name, fps, src0 (raw frame at t0), raw0 (raw s at t0)}]}
                         -> import_longform.py --at / --range and rawsheet.py work as after a real pro-edit import
  raw/stem48.wav         the raw mic pasted at its final-video time (zeros where nothing matched: music, game, montage)
  project.json           clean_stem.voice = raw/stem48.wav, unless one is set
Next: clean_from_stem.py --scan, then clean_stem.sync / .patches limited to the voiced stretches you keep, --build
(pipeline.md 1b/1c). A raw recording that caught game or demo audio through the speakers also matches the export's
montage or playthrough: those pieces belong in no patch.
usage (in work-<stem>/, after analyze.sh):
  $PY scripts/build_raw_map.py                     the raw recordings next to the video (import_longform.raw_recordings)
  $PY scripts/build_raw_map.py 1.mkv 2.mkv ...     these files (absolute, or relative to the video's folder)
  options: --end <s> (stop matching there)   --min-peak <0.55> (normalised correlation a window needs)"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import numpy as np, soundfile as sf
from scipy import signal
sys.path.insert(0, 'scripts'); import config as C
from import_longform import raw_recordings

SR16, SR48 = 16000, 48000
WIN, HOP = 1.5, 0.5
args = sys.argv[1:]
def opt(name, default):
    if name in args: i = args.index(name); v = float(args[i + 1]); del args[i:i + 2]; return v
    return default
T_END, MIN_PEAK = opt('--end', None), opt('--min-peak', 0.55)
src_dir = os.path.dirname(os.path.abspath(C.SRC))
files = [a if os.path.isabs(a) else os.path.join(src_dir, a) for a in args] or raw_recordings(C._cfg)
files = [os.path.abspath(f) for f in files if os.path.exists(f)]
if not files: sys.exit('no raw recordings: pass them (paths relative to the video\'s folder) or put them next to the video')
os.makedirs('raw', exist_ok=True)
names = []
for f in files:   # unique short names for the raw/ WAVs
    n = os.path.splitext(os.path.basename(f))[0]; k = 2
    while n in names: n = f'{os.path.splitext(os.path.basename(f))[0]}_{k}'; k += 1
    names.append(n)


def extract(job):
    f, n = job
    if not (os.path.exists(f'raw/{n}.16k.wav') and os.path.exists(f'raw/{n}.48k.wav')):
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f, '-vn', '-map', '0:a:0', '-ac', '1', '-ar', str(SR16), '-c:a', 'pcm_s16le',
                        f'raw/{n}.16k.wav', '-vn', '-map', '0:a:0', '-ar', str(SR48), '-c:a', 'pcm_f32le', f'raw/{n}.48k.wav'], check=True)
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=r_frame_rate', '-of', 'csv=p=0', f],
                       capture_output=True, text=True).stdout.strip() or '60/1'
    a, b = (r.split('/') + ['1'])[:2]; return float(a) / float(b or 1)


with ThreadPoolExecutor(min(8, len(files))) as ex: FPS = list(ex.map(extract, zip(files, names)))
print('raw recordings:', *[f'{n} ({fp:g} fps)' for n, fp in zip(names, FPS)])

# the export's OWN audio: clean_from_stem.py --build keeps it as export48.wav once clean48 has been patched
if os.path.exists('export48.wav'):
    e48, _ = sf.read('export48.wav', dtype='float32'); x16 = signal.resample_poly(e48.mean(1) if e48.ndim > 1 else e48, 1, 3).astype(np.float32)
else:
    x16, _ = sf.read('clean16.wav', dtype='float32'); x16 = x16.mean(1) if x16.ndim > 1 else x16
DUR = len(x16) / SR16; T_END = min(T_END or DUR, DUR)
raws = [sf.read(f'raw/{n}.16k.wav', dtype='float32')[0] for n in names]
offs = np.cumsum([0] + [len(r) for r in raws]); cat = np.concatenate(raws); L = int(WIN * SR16)

try:
    import torch
    dev = 'cuda' if torch.cuda.is_available() else None
except ImportError:
    torch, dev = None, None
if dev:
    N = 1 << int(np.ceil(np.log2(len(cat) + L + 1)))
    R = torch.from_numpy(cat).to(dev); FR = torch.fft.rfft(R, n=N)
    cs = torch.cat([torch.zeros(1, device=dev, dtype=torch.float64), torch.cumsum(R.double() ** 2, 0)])
    ENERGY = (cs[L:] - cs[:-L]).float().clamp_min(1e-9)
else:
    _cs = np.concatenate([[0], np.cumsum(cat.astype(np.float64) ** 2)]); CAT_EN = np.maximum(_cs[L:] - _cs[:-L], 1e-9)
print('matching on', dev or 'the CPU (local search first; a global search per miss is slow)')


def global_search(a):
    """best (file, offset raw - export, peak) over all raw tracks for window a (zero-mean)"""
    if dev:
        A = torch.from_numpy(a).to(dev)
        c = torch.fft.irfft(FR * torch.conj(torch.fft.rfft(A, n=N)), n=N)[:len(ENERGY)]
        nc = c.abs() / torch.sqrt(ENERGY * (A ** 2).sum()); i = int(torch.argmax(nc)); pk = float(nc[i])
    else:
        c = signal.fftconvolve(cat, a[::-1], mode='valid')
        nc = np.abs(c) / np.sqrt(CAT_EN[:len(c)] * (a ** 2).sum()); i = int(np.argmax(nc)); pk = float(nc[i])
    k = int(np.searchsorted(offs, i, side='right') - 1)
    return (k, i - offs[k], pk) if i + L <= offs[k + 1] else None   # a window straddling two files is no match


def local_search(a, k, s0, rng=0.5):
    """the same, only around sample s0 of raw track k (right after the previous match)"""
    r = raws[k]; lo = max(0, int(s0 - rng * SR16)); b = r[lo:int(s0 + rng * SR16) + L]
    if len(b) <= L: return None
    c = signal.fftconvolve(b, a[::-1], mode='valid'); cs2 = np.concatenate([[0], np.cumsum(b.astype(np.float64) ** 2)])
    en = np.maximum(cs2[L:] - cs2[:-L], 1e-9)[:len(c)]; nc = np.abs(c) / np.sqrt(en * (a ** 2).sum()); j = int(np.argmax(nc))
    return k, lo + j, float(nc[j])


good, prev = [], None
for t in np.arange(0, T_END - WIN, HOP):
    a = x16[int(t * SR16):int(t * SR16) + L]
    if len(a) < L or np.sqrt((a ** 2).mean()) < 3e-3: continue
    a = (a - a.mean()).astype(np.float32); hit = None
    if prev:
        hit = local_search(a, prev[0], (t + prev[1]) * SR16)
        if hit and hit[2] < MIN_PEAK: hit = None
    if hit is None: hit = global_search(a)
    if hit and hit[2] >= MIN_PEAK:
        k, s, pk = hit; o = s / SR16 - t; good.append((float(t), k, o)); prev = (k, o)
print(f'{len(good)} of {int((T_END - WIN) / HOP)} windows matched (peak >= {MIN_PEAK})')

pieces = []
for t, k, o in good:
    p = pieces[-1] if pieces else None
    if p and p['k'] == k and abs(p['o'] - o) < 0.006 and t - p['t1'] <= 2.0: p['t1'] = t; p['os'].append(o); continue
    pieces.append(dict(k=k, o=o, t0=t, t1=t, os=[o]))
pieces = [p for p in pieces if p['t1'] - p['t0'] >= 1.0]   # one stray window is noise
for p in pieces: p['o'] = float(np.median(p['os']))


def seg(k, s0, n):
    r = raws[k]; s0 = int(round(s0)); out = np.zeros(n, np.float32); a, b = max(0, s0), min(len(r), s0 + n)
    if b > a: out[a - s0:b - s0] = r[a:b]
    return out


def change_point(ta, tb, pa, pb):
    """the 10 ms frame between ta and tb where switching from piece pa to pb leaves the least residual (clean_from_stem.py)"""
    i0 = int(ta * SR16); a = x16[i0:int(tb * SR16)]; n = len(a) // 160 * 160; a = a[:n]
    ba = seg(pa['k'], i0 + pa['o'] * SR16, n); bb = seg(pb['k'], i0 + pb['o'] * SR16, n)
    ga = (a * ba).sum() / ((ba * ba).sum() + 1e-12); gb = (a * bb).sum() / ((bb * bb).sum() + 1e-12)
    ea = ((a - ga * ba) ** 2).reshape(-1, 160).sum(1); eb = ((a - gb * bb) ** 2).reshape(-1, 160).sum(1)
    cost = np.concatenate([[0], np.cumsum(ea)]) + (eb.sum() - np.concatenate([[0], np.cumsum(eb)]))
    return ta + int(np.argmin(cost)) * 0.01


items = []
for j, p in enumerate(pieces):
    if j and pieces[j - 1]['t1'] + WIN >= p['t0'] - 1.0:      # adjacent pieces: the boundary where the residual is least
        t0 = change_point(pieces[j - 1]['t1'], p['t0'] + WIN, pieces[j - 1], p); items[-1]['t1'] = round(t0, 3)
    else:
        t0 = p['t0']                                          # after a gap (music, game, a graphic with no voice)
    items.append(dict(t0=round(t0, 3), t1=round(min(DUR, p['t1'] + WIN), 3), k=p['k'], o=p['o']))
for it in items:
    k = it['k']; it.update(file=files[k].replace('\\', '/'), name=os.path.basename(files[k]), fps=FPS[k],
                           raw0=round(it['t0'] + it['o'], 3), src0=round((it['t0'] + it['o']) * FPS[k], 2))
fps_main = max(set(FPS), key=FPS.count)
json.dump(dict(fps=fps_main, dur=round(DUR, 3), made_by='build_raw_map.py (audio matched against the raw recordings)',
               items=[{k: v for k, v in it.items() if k not in ('k', 'o')} for it in items]),
          open('longform_program.json', 'w', encoding='utf-8'), indent=1)

# the stem: raw 48 kHz audio pasted at final-video time, 4 ms ramps at every piece edge
n48 = int(round(DUR * SR48)); stem = np.zeros((n48, 2), np.float32); r48 = {}; F = int(0.004 * SR48)
for it in items:
    k = it['k']
    if k not in r48:
        d = sf.read(f'raw/{names[k]}.48k.wav', dtype='float32')[0]; r48[k] = d if d.ndim == 2 else np.stack([d, d], 1)
    a, b = int(it['t0'] * SR48), min(n48, int(it['t1'] * SR48)); s0 = int(round((it['t0'] + it['o']) * SR48)); src = r48[k]
    lo, hi = max(0, s0), min(len(src), s0 + (b - a)); piece = np.zeros((b - a, 2), np.float32)
    if hi > lo: piece[lo - s0:hi - s0] = src[lo:hi]
    ramp = np.ones(b - a, np.float32); f = min(F, (b - a) // 2)
    if f: ramp[:f] = np.linspace(0, 1, f); ramp[-f:] = np.linspace(1, 0, f)
    stem[a:b] += piece * ramp[:, None]
sf.write('raw/stem48.wav', stem, SR48, subtype='FLOAT')
st = C.get('clean_stem') or {}
if not st.get('voice'): st['voice'] = 'raw/stem48.wav'; C.save(clean_stem=st)

# voiced export stretches the raw recordings don't cover (music, game audio, a montage): keep the export audio there
db = 20 * np.log10(np.sqrt(np.maximum(signal.convolve((x16 ** 2), np.ones(1600) / 1600, mode='same'), 1e-12)))[::160]
cov = np.zeros(len(db), bool)
for it in items: cov[int(it['t0'] * 100):int(it['t1'] * 100)] = True
gaps, r = [], None
for i, (v, c) in enumerate(zip(db, cov)):
    if v > -35 and not c:
        if r is None: r = i
    elif r is not None:
        if i - r >= 100: gaps.append((r / 100, i / 100))
        r = None
print(f'{len(items)} raw pieces -> longform_program.json, raw/stem48.wav (clean_stem.voice = {st["voice"]})')
for it in items[:12]: print(f"  {it['t0']:8.2f}-{it['t1']:8.2f}  {it['name']} @ {it['raw0']:.2f}")
if len(items) > 12: print(f'  ... {len(items) - 12} more')
if gaps: print('sound the raw recordings lack (music, game, montage; keep the export there):', [(round(a, 1), round(b, 1)) for a, b in gaps[:30]])
print('next: clean_from_stem.py --scan; set clean_stem.sync/.patches to the voiced stretches you keep (fit_exclude where music sits under the voice); --build (pipeline.md 1c)')
