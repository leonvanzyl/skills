"""Clean voice for a FINISHED edit whose audio has music / SFX / a riser mixed under the voice, using a clean voice stem
(e.g. the long-form edit's own dialogue track rendered on ITS timeline, or a previous run's voice48.wav). The export is the
voice wherever it is clean; the stem is patched in only where something sits under a kept line, synced piecewise (the
export may have small trims vs the stem's timeline), EQ-matched (linear-phase FIR), compression-matched (static curve) and
level-matched to the export, so patched and unpatched lines sound the same. Run after analyze.sh, before cut.sh.

project.json -> "clean_stem": {"voice": "<path to the stem wav>",
                               "sync": [[t0, t1, offset_s], ...],      # written by --scan (export time -> stem time = t + offset)
                               "patches": [[t0, t1, "why"], ...]}      # export-time windows to replace; boundaries in quiet gaps
usage:
  python scripts/clean_from_stem.py --scan        # piecewise sync map (1 s steps), change points refined, stretches the stem lacks
  python scripts/clean_from_stem.py --suspects    # where the export has extra sound under the voice (music, SFX) -> patch candidates
  python scripts/clean_from_stem.py --build       # clean48.wav / clean16.wav / rms10ms.npy rebuilt; the export audio kept as export48.wav
Stretches the stem lacks (e.g. a call's far-end voice recorded on another track) keep the export audio: never patch them."""
import json, os, shutil, subprocess, sys
import numpy as np, soundfile as sf
from scipy import signal
from scipy.ndimage import uniform_filter1d
sys.path.insert(0, 'scripts'); import config as C

SR, SR16 = 48000, 16000
cfg = C.get('clean_stem') or {}
if not cfg.get('voice'): sys.exit('set project.json -> clean_stem.voice to the clean voice stem first')
if not os.path.exists('export48.wav'): shutil.copy('clean48.wav', 'export48.wav')   # the export's own audio, kept once
x, _ = sf.read('export48.wav', dtype='float32'); v, sr2 = sf.read(cfg['voice'], dtype='float32')
if sr2 != SR: v = signal.resample_poly(v, SR, sr2, axis=0).astype(np.float32)
if v.ndim == 1: v = np.stack([v, v], 1)
xm, vm = x.mean(1), v.mean(1)
x16, v16 = signal.resample_poly(xm, 1, 3), signal.resample_poly(vm, 1, 3)
DUR = len(xm) / SR


def xcorr_off(t, win, guess, rng):
    """offset (stem - export) of the export window [t, t+win] searched in guess +/- rng; returns (offset, normalised peak)"""
    a = x16[int(t * SR16):int((t + win) * SR16)]
    if len(a) < win * SR16 * 0.9 or np.sqrt((a ** 2).mean()) < 1e-3: return None, 0.0
    lo = max(0, int((t + guess - rng) * SR16)); b = v16[lo:int((t + guess + win + rng) * SR16)]
    if len(b) <= len(a): return None, 0.0
    c = signal.fftconvolve(b, a[::-1], mode='valid'); i = int(np.argmax(np.abs(c)))
    pk = abs(c[i]) / (np.sqrt((a ** 2).sum() * (b[i:i + len(a)] ** 2).sum()) + 1e-9)
    return (lo + i) / SR16 - t, float(pk)


def refine(t0, t1, o):
    """sample-exact offset at 48 kHz from the middle of a piece"""
    mid = (t0 + t1) / 2; w = max(1.0, min(8.0, (t1 - t0) / 2 - 0.5))
    a = xm[int((mid - w / 2) * SR):int((mid + w / 2) * SR)]
    lo = int((mid - w / 2 + o - 0.006) * SR); b = vm[lo:lo + len(a) + int(0.012 * SR)]
    c = signal.fftconvolve(b, a[::-1], mode='valid'); k = int(np.argmax(c))
    return (lo + k) / SR - (mid - w / 2)


def r_db(s, hop):
    n = len(s) // hop; return 20 * np.log10(np.sqrt((s[:n * hop].reshape(n, hop) ** 2).mean(1)) + 1e-9)


if '--scan' in sys.argv:
    # coarse global offset from the first minute, then 1 s steps tracking the offset (wider search when the peak is weak)
    g0, p0 = xcorr_off(min(30, DUR / 4), 20, 0, 30)
    rows, prev = [], (g0 or 0.0)
    for t in np.arange(0, DUR - 3, 1.0):
        o, pk = xcorr_off(t, 3.0, prev, 4.0)
        if o is not None and pk < 0.6:
            o2, pk2 = xcorr_off(t, 3.0, g0 or 0.0, 15.0)
            if pk2 > pk: o, pk = o2, pk2
        rows.append((float(t), o, pk))
        if o is not None and pk >= 0.6: prev = o
    # pieces of constant offset (4 ms tolerance); weak samples are stretches the stem lacks (or silence)
    pieces = []
    for t, o, pk in rows:
        if o is None or pk < 0.6: continue
        if pieces and abs(pieces[-1]['o'] - o) < 0.004 and t - pieces[-1]['t1'] <= 3.0: pieces[-1]['t1'] = t; continue
        pieces.append(dict(t0=t, t1=t, o=o))
    pieces = [p for p in pieces if p['t1'] - p['t0'] >= 2.0 or len(pieces) == 1]
    # change point between two pieces: over 10 ms frames from the last window that matched A to the end of the first that
    # matched B, pick the split minimising (error with A before it) + (error with B after it). Exact to a frame, and it
    # does not assume the trim sits in silence (snapping to the quietest frame put cuts on the wrong side of connected speech).
    def change_point(ta, tb, oa, ob):
        i0, i1 = int(ta * SR16), int(tb * SR16); a = x16[i0:i1]
        ba = v16[i0 + int(oa * SR16):i0 + int(oa * SR16) + len(a)]; bb = v16[i0 + int(ob * SR16):i0 + int(ob * SR16) + len(a)]
        n = min(len(a), len(ba), len(bb)) // 160 * 160; a, ba, bb = a[:n], ba[:n], bb[:n]
        ga = (a * ba).sum() / ((ba * ba).sum() + 1e-12); gb = (a * bb).sum() / ((bb * bb).sum() + 1e-12)
        ea = ((a - ga * ba) ** 2).reshape(-1, 160).sum(1); eb = ((a - gb * bb) ** 2).reshape(-1, 160).sum(1)
        cost = np.concatenate([[0], np.cumsum(ea)]) + (eb.sum() - np.concatenate([[0], np.cumsum(eb)]))
        return ta + int(np.argmin(cost)) * 0.01
    out = []
    for k, p in enumerate(pieces):
        t0 = 0.0 if k == 0 else out[-1][1]
        cut = change_point(p['t1'], pieces[k + 1]['t0'] + 3.0, p['o'], pieces[k + 1]['o']) if k + 1 < len(pieces) else DUR
        out.append([round(t0, 2), round(cut, 2), round(refine(max(t0, p['t0']), min(cut, p['t1'] + 3), p['o']), 5)])
    weak = [(t, round(pk, 2)) for t, o, pk in rows if o is not None and pk < 0.6]
    cfg['sync'] = out; C.save(clean_stem=cfg)
    print('sync pieces (export t0, t1, offset s):'); [print('  ', p) for p in out]
    if weak: print('weak correlation (sound the stem lacks, e.g. a call\'s far end - never patch these):', weak[:80])
    sys.exit()

SYNC = cfg.get('sync') or sys.exit('run --scan first')
def off_at(t):
    for t0, t1, o in SYNC:
        if t0 <= t < t1: return o
    return None

# EQ + compression + level match: fit on synced stretches outside the patches (up to ~400 s of audio)
PATCH = cfg.get('patches', [])
fit_ix = []
for t0, t1, o in SYNC:
    for t in np.arange(t0 + 1, t1 - 1, 1.0):
        if not any(a - 1 <= t <= b + 1 for a, b, *_ in PATCH): fit_ix.append((t, o))
fit_ix = fit_ix[::max(1, len(fit_ix) // 400)]
ex = np.concatenate([xm[int(t * SR):int((t + 1) * SR)] for t, o in fit_ix])
cl = np.concatenate([vm[int((t + o) * SR):int((t + o + 1) * SR)] for t, o in fit_ix])
f, px = signal.welch(ex, SR, nperseg=8192); f, pc = signal.welch(cl, SR, nperseg=8192)
ratio = np.sqrt(px / (pc + 1e-20)); sm = np.empty_like(ratio)
for i, fi in enumerate(f):                                    # 1/3-octave smoothing in the log domain
    m = (f >= fi / 2 ** (1 / 6)) & (f <= fi * 2 ** (1 / 6)) if fi > 0 else (f <= f[1])
    sm[i] = np.exp(np.log(ratio[m] + 1e-12).mean())
band = (f > 60) & (f < 16000); sm[f < 60] = sm[band][0]; sm[f > 16000] = sm[band][-1]
TAPS = 4095
fir = signal.firwin2(TAPS, f / (SR / 2), sm / sm[np.argmin(abs(f - 1000))])
vq = np.stack([signal.fftconvolve(v[:, c], fir)[TAPS // 2:TAPS // 2 + len(v)] for c in range(2)], 1).astype(np.float32)
vqm = vq.mean(1); cq = np.concatenate([vqm[int((t + o) * SR):int((t + o + 1) * SR)] for t, o in fit_ix])
re_, rc_ = r_db(ex, SR // 10), r_db(cq, SR // 10); sp = (re_ > -40) & (rc_ > -60)
vq *= 10 ** ((np.median(re_[sp]) - np.median(rc_[sp])) / 20)
vqm = vq.mean(1); cq = np.concatenate([vqm[int((t + o) * SR):int((t + o + 1) * SR)] for t, o in fit_ix])
le, lc = r_db(ex, SR // 50), r_db(cq, SR // 50)
bins = np.arange(-60, -2, 2.0); curve = []
for b0 in bins:
    m = (lc >= b0) & (lc < b0 + 2); curve.append(np.median(le[m] - lc[m]) if m.sum() > 50 else np.nan)
curve = np.array(curve); ok = ~np.isnan(curve); curve = np.interp(bins, bins[ok], curve[ok])
gdb = np.interp(r_db(vqm, SR // 50), bins + 1, curve)
k = np.exp(-np.arange(0, 8) / 2.5); gdb = np.convolve(gdb, k / k.sum(), mode='same')
env = np.repeat(10 ** (gdb / 20), SR // 50); env = np.pad(env, (0, max(0, len(vq) - len(env))), mode='edge')[:len(vq)]
vq *= uniform_filter1d(env, SR // 100)[:, None].astype(np.float32)
vqm = vq.mean(1); chk = np.concatenate([vqm[int((t + o) * SR):int((t + o + 1) * SR)] for t, o in fit_ix])
f, p1 = signal.welch(ex, SR, nperseg=4096); f, p2 = signal.welch(chk, SR, nperseg=4096)
MATCH = {f'{lo}-{hi}': round(float(10 * np.log10(p1[(f >= lo) & (f < hi)].mean() / p2[(f >= lo) & (f < hi)].mean())), 1)
         for lo, hi in [(100, 400), (400, 1600), (1600, 6400), (6400, 12000)]}
print('EQ match after FIR (export/stem, dB per band):', MATCH)

if '--suspects' in sys.argv:
    # Extra sound shows in the LOW band (30-90 Hz), where a voice has little energy but a riser, pops, low whooshes and a
    # music bass do. (Broadband comparisons are useless: the export's own voice processing leaves ~-7 dB of residual
    # everywhere.) Measured on a finished edit: riser +12 dB, CTA-card pops +6..14 dB, a call's far-end voice +16 dB, over a
    # median of -2 dB. A quiet music bed (~18 LU under the voice) and tiny high clicks may NOT show: also use what you know
    # about the edit (its own report or timeline lists music/SFX/riser times) and treat the hook as suspect.
    # Sound the stem never had (a far-end voice on a call) also shows here: never patch that.
    sos = signal.butter(4, [30, 90], btype='band', fs=SR, output='sos')
    vl = np.zeros_like(xm)
    for t0, t1, o in SYNC:
        i0, i1 = int(t0 * SR), int(t1 * SR); j0 = i0 + int(o * SR)
        seg = vqm[max(0, j0):j0 + (i1 - i0)][:len(vl) - i0]; vl[i0:i0 + len(seg)] = seg
    hop = SR // 2
    e = r_db(signal.sosfiltfilt(sos, xm), hop); s = r_db(signal.sosfiltfilt(sos, vl), hop); n = min(len(e), len(s))
    d = e[:n] - s[:n]; med = np.median(d)
    spans = []
    for k in np.where((d > med + 6) & (e[:n] > -62))[0]:
        t = k / 2
        if spans and t - spans[-1][1] <= 1.0: spans[-1][1] = t + 0.5; spans[-1][2] = max(spans[-1][2], d[k] - med)
        else: spans.append([t, t + 0.5, d[k] - med])
    print(f'extra low-band sound vs the stem (median {med:.1f} dB): risers, pops, low whooshes, music bass - or a far-end voice:')
    for a, b, x_ in spans: print(f'  {a:7.1f} - {b:7.1f} s   +{x_:.0f} dB')
    print('Patch the kept lines inside music/SFX spans (boundaries in quiet gaps; never a far-end voice), then --build.')
    sys.exit()

if '--build' in sys.argv:
    out = x.copy(); fade = int(0.010 * SR); ramp = np.linspace(0, 1, fade, dtype=np.float32)[:, None]; info = []
    for t0, t1, *why in PATCH:
        i0, i1 = int(t0 * SR), int(t1 * SR); piece = np.zeros((i1 - i0, 2), np.float32); used = []
        for s0, s1, o in SYNC:                                # a patch may span a trim: each part with its own offset
            a_, b_ = max(t0, s0), min(t1, s1)
            if b_ <= a_: continue
            k0, k1 = int(a_ * SR), int(b_ * SR); jj = k0 + int(round(o * SR))
            piece[k0 - i0:k1 - i0] = vq[jj:jj + (k1 - k0)]; used.append(o)
        if not used: print(f'patch {t0}-{t1}: no sync piece covers it - skipped'); continue
        # per-patch level: median of (export - stem) on loud speech frames (a riser or pops touch only a few of them)
        re_p, rc_p = r_db(xm[i0:i1], SR // 10), r_db(piece.mean(1), SR // 10); spm = (re_p > -30) & (rc_p > -50)
        gp = 10 ** (np.median(re_p[spm] - rc_p[spm]) / 20) if spm.sum() > 5 else 1.0
        piece *= gp
        w = np.ones((i1 - i0, 1), np.float32)
        if i0 > 0: w[:fade] = ramp
        w[-fade:] = ramp[::-1]
        out[i0:i1] = out[i0:i1] * (1 - w) + piece * w
        info.append(dict(t0=t0, t1=t1, why=why[0] if why else '', offsets_s=[round(o, 5) for o in used], extra_gain_db=round(float(20 * np.log10(gp)), 2)))
    hot = np.abs(out) > 0.9                                   # soft knee on the few hot samples only (never rescale the file)
    out[hot] = np.sign(out[hot]) * (0.9 + 0.09 * np.tanh((np.abs(out[hot]) - 0.9) / 0.09))
    sf.write('clean48.wav', out, SR, subtype='PCM_24')
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'clean48.wav', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', 'clean16.wav'], check=True)
    m = out.mean(1); hop = SR // 100; n = len(m) // hop
    np.save('rms10ms.npy', (20 * np.log10(np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))).astype(np.float32))
    C.save(sync=dict(note='clean48 = export audio with the clean voice stem patched in where music/SFX sat under kept lines; '
                          'synced piecewise, EQ/compression/level matched (scripts/clean_from_stem.py)',
                     voice=cfg['voice'], sync_pieces=SYNC, patches=info, eq_match_db=MATCH))
    print(json.dumps(info, indent=1)); print('clean48.wav / clean16.wav / rms10ms.npy rebuilt (export audio kept as export48.wav)')
