"""Master and deliver: the final YouTube file (-14 LUFS, true peak under -1 dBTP), mixed OUTSIDE Resolve's mixer.

Why outside: on last-call (2026-10-16) Resolve's own mix could not be trusted - fader automation held the SFX tracks at
-14 dB, a limiter on Bus 1 never reached the render, the AI Audio Assistant mangled the game music and Deliver's
loudness normalisation left the upload soft. Here every level is measured and the user gets one file to upload.

What goes in:
  - the BASE stem: every audio track the user had before the pro edit (the voice and anything else of theirs), rendered
    by Resolve THROUGH their own track effects, faders and bus (rs_stem.py, KEEP='base');
  - the pro edit's own tracks ("PE ..."), rebuilt here sample-accurately from their files (rs_items.py -> `layers`),
    at unity: audio.py baked their levels into the files against the RAW voice (voice48.wav);
  - the picture, rendered by Resolve (rs_picture.py).
The base stem is set back to the raw voice's speaking loudness (minus the plan's sfx_bus_lift), so every layer sits
exactly where audio.py levelled it, then the sum is driven into a true-peak limiter to -14.0 LUFS.

  $PY scripts/master.py chain $M/_deliver/chain_<tl>.wav --items $M/_deliver/items_<tl>.json [--from <timeline s>]
        is the voice on that timeline processed (the user's EQ / isolation / dynamics) or raw? (fit against its media)
  $PY scripts/master.py layers [--items $M/_deliver/items.json]  -> levels/layer_A<n>.wav per enabled PE track
  $PY scripts/master.py fit [--mix $M/_deliver/mix_resolve.wav] each part's real gain in Resolve's own mix (flags faders,
                                                                automation and bus effects that the master leaves out)
  $PY scripts/master.py build [--voice-db X] [--ceil -1.5]      -> levels/premix.wav, levels/master.wav + level audit
  $PY scripts/master.py deliver <picture.mp4> <final.mp4>       sync check, mux (video copied, AAC 384k), measure the
                                                                decoded file, dip any AAC overshoot, re-mux, report
Everything runs in W; results also go to levels/master_report.json for report.md."""
import sys, os, re, json, argparse, subprocess, collections
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy.signal import resample_poly, correlate, welch
from scipy.ndimage import maximum_filter1d, uniform_filter1d

sys.path.insert(0, 'scripts'); import config as C
SR = 48000
L = 'levels/'                                   # this script's own outputs, in W
DLV = os.path.join(C.MEDIA, '_deliver')         # what Resolve writes for delivery: next to the sources, never under
os.makedirs(L, exist_ok=True)                   # AppData (a packaged app can't see files Resolve wrote there)
METER = pyln.Meter(SR)
REPORT = L + 'master_report.json'


def report(**kw):
    """merge kw into levels/master_report.json (numpy values made plain; written atomically)"""
    try: r = json.load(open(REPORT))
    except Exception: r = {}
    r.update(kw)
    json.dump(r, open(REPORT + '.tmp', 'w'), indent=1, default=lambda o: o.item() if hasattr(o, 'item') else str(o))
    os.replace(REPORT + '.tmp', REPORT)


def lufs(x):
    try: return float(METER.integrated_loudness(x))
    except Exception: return float('-inf')


def db(x): return 20 * np.log10(max(float(x), 1e-12))


def read_wav(p):
    x, sr = sf.read(p, dtype='float32', always_2d=True)
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    if sr != SR: x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
    return x[:, :2]


def read_segment(path, t, d):
    """d seconds of a media file's audio from t: audio files directly, anything else (mkv, mov, mp4) through ffmpeg"""
    if os.path.splitext(path)[1].lower() in ('.wav', '.flac', '.aif', '.aiff', '.w64'):
        info = sf.info(path); a = int(round(t * info.samplerate))
        x, sr = sf.read(path, start=a, stop=a + int(round(d * info.samplerate)), dtype='float32', always_2d=True)
    else:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', f'{t:.6f}', '-t', f'{d:.6f}', '-i', path, '-map', '0:a:0',
                              '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        x, sr = np.frombuffer(raw, np.float32).reshape(-1, 2), SR
    if x.shape[1] == 1: x = np.repeat(x, 2, 1)
    if sr != SR: x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
    return x[:, :2]


def build_tracks(J, tracks, t0=0.0, t1=None):
    """every enabled item of the given tracks, from its own file at its source in-point and clip volume, on timeline
    time [t0, t1) - one stereo float array per track"""
    fps = J['fps']; t1 = J['end'] / fps if t1 is None else t1
    n = int(round((t1 - t0) * SR)); out = {k: np.zeros((n, 2), np.float32) for k in tracks}
    for it in J['items']:
        if it['track'] not in tracks or not it.get('enabled', True) or not it.get('path'): continue
        s = it['start'] / fps; e = s + it['dur'] / fps; a, b = max(s, t0), min(e, t1)
        if b <= a: continue
        src = (it['src_time'] if it.get('src_time') is not None else it['left'] / fps) + (a - s)
        x = read_segment(it['path'], src, b - a) * np.float32(10 ** (float(it.get('vol') or 0) / 20))
        i = int(round((a - t0) * SR)); x = x[:n - i]; out[it['track']][i:i + len(x)] += x
    return out


def pe_tracks(J):
    """the pro edit's own audio tracks that play: named "PE ...", enabled, not an "(old)" layer"""
    return [int(k) for k, t in sorted(J['tracks'].items(), key=lambda kv: int(kv[0]))
            if t['name'].startswith('PE ') and t.get('enabled', True) and '(old)' not in t['name']]


def tp_env(y, chunk=SR * 30):
    """the true peak (4x oversampled) under every sample, in chunks so a 25-minute mix fits in memory"""
    out = np.empty(len(y), np.float32); pad = 64
    for a in range(0, len(y), chunk):
        s, e = max(0, a - pad), min(len(y), a + chunk + pad); m = min(chunk, len(y) - a)
        pk = np.abs(resample_poly(y[s:e], 4, 1, axis=0)).max(1)[:(e - s) * 4].reshape(-1, 4).max(1)
        out[a:a + m] = pk[a - s:a - s + m]
    return out


def limit(y, ceil_db):
    """true-peak limiter: instant attack with 1.5 ms look-ahead, 80 ms release, ceiling ceil_db dBTP"""
    ceil = 10 ** (ceil_db / 20); la = int(0.0015 * SR)
    need = np.minimum(1.0, ceil / np.maximum(maximum_filter1d(tp_env(y), 2 * la + 1), 1e-9)).astype(np.float32)
    B = 16; nb = -(-len(need) // B)                                   # the release runs on 16-sample blocks
    blk = np.pad(need, (0, nb * B - len(need)), constant_values=1.0).reshape(nb, B).min(1)
    rel = np.exp(-B / (0.080 * SR)); g = np.empty(nb, np.float32); cur = 1.0
    for i in range(nb):
        t = blk[i]; cur = t if t < cur else rel * cur + (1 - rel) * t; g[i] = cur
    g = np.minimum(uniform_filter1d(np.repeat(g, B)[:len(need)], la), need)
    return y * g[:, None], g


def plan():
    return json.load(open('edit_plan.json')) if os.path.exists('edit_plan.json') else {}


# ---------------------------------------------------------------- chain: is the voice processed on this timeline?
def cmd_chain(a):
    stem = read_wav(a.stem)
    if a.raw: raw = read_wav(a.raw)
    else:
        J = json.load(open(a.items)); t1 = a.t0 + len(stem) / SR
        raw = sum(build_tracks(J, a.tracks, a.t0, t1).values())
    n = min(len(stem), len(raw)); x, y = stem[:n].mean(1), raw[:n].mean(1)
    L_ = int(0.05 * SR); c = correlate(x, y, mode='full', method='fft')[n - 1 - L_:n + L_]
    lag = int(np.argmax(np.abs(c))) - L_
    if lag > 0: x, y = x[lag:], y[:len(y) - lag]
    elif lag < 0: y, x = y[-lag:], x[:len(x) + lag]
    g = float((x * y).sum() / max((y * y).sum(), 1e-12)); res = x - g * y
    rel = db(np.sqrt((res ** 2).mean()) / max(np.sqrt((x ** 2).mean()), 1e-12))
    f, Ps = welch(x, SR, nperseg=8192); _, Pr = welch(y, SR, nperseg=8192)
    bands = [(80, 250), (250, 1000), (1000, 4000), (4000, 12000)]
    tilt = [float(np.median(10 * np.log10(Ps[(f >= lo) & (f < hi)] / Pr[(f >= lo) & (f < hi)]))) for lo, hi in bands]
    processed = rel > -30 or (max(tilt) - min(tilt)) > 1.5
    print(f'{a.stem}: gain {db(abs(g)):+.1f} dB, lag {lag} samples, unexplained {rel:+.1f} dB, band levels vs raw '
          + ', '.join(f'{lo}-{hi} Hz {t:+.1f}' for (lo, hi), t in zip(bands, tilt)))
    print('-> PROCESSED: the voice carries a chain (EQ / isolation / dynamics)' if processed else
          '-> RAW: no processing on this voice - if the user\'s own timeline is PROCESSED, their chain was lost')
    report(**{f'chain_{os.path.basename(a.stem)}': dict(processed=processed, unexplained_db=round(rel, 1),
                                                         bands_db=[round(t, 1) for t in tilt], gain_db=round(db(abs(g)), 1))})


# ---------------------------------------------------------------- layers: the PE tracks from their files
def cmd_layers(a):
    J = json.load(open(a.items)); ks = pe_tracks(J)
    for k, buf in build_tracks(J, ks).items():
        sf.write(L + f'layer_A{k}.wav', buf, SR, subtype='FLOAT')
        print(f"A{k} {J['tracks'][str(k)]['name']}: {sum(1 for i in J['items'] if i['track'] == k)} items, "
              f'peak {db(np.abs(buf).max()):.1f} dBFS -> {L}layer_A{k}.wav')
    report(layers={f'A{k}': J['tracks'][str(k)]['name'] for k in ks}, items=a.items)


def load_layers():
    r = json.load(open(REPORT)); return {k: (name, read_wav(L + f'layer_{k}.wav')) for k, name in r['layers'].items()}


# ---------------------------------------------------------------- fit: what Resolve's own mix really does
def cmd_fit(a):
    mix = read_wav(a.mix); parts = [('base stem', read_wav(a.stem))] + [(f'{k} {nm}', x) for k, (nm, x) in load_layers().items()]
    n = min([len(mix)] + [len(x) for _, x in parts]); k = len(parts)
    AtA = np.zeros((k, k)); Aty = np.zeros(k); yy = 0.0
    for s in range(0, n, SR * 30):                                  # normal equations in chunks
        e = min(n, s + SR * 30); A = np.stack([x[s:e].reshape(-1) for _, x in parts], 1).astype(np.float64)
        y = mix[s:e].reshape(-1).astype(np.float64); AtA += A.T @ A; Aty += A.T @ y; yy += y @ y
    g = np.linalg.lstsq(AtA, Aty, rcond=None)[0]
    res = yy - 2 * g @ Aty + g @ AtA @ g
    print(f"Resolve's mix ({a.mix}) = " + ' + '.join(f'{nm} x {db(abs(v)):+.2f} dB' for (nm, _), v in zip(parts, g))
          + f'   (unexplained {db(np.sqrt(max(res, 0) / max(yy, 1e-12))):+.1f} dB)')
    flags = []
    for (nm, _), v in zip(parts, g):
        if abs(db(abs(v))) > 1.0:
            flags.append(f'{nm} plays at {db(abs(v)):+.1f} dB in Resolve (a fader, automation, clip gain or bus effect) '
                         'that the master leaves out - ask the user if it was meant')
    print('\n'.join('FLAG: ' + f for f in flags) or 'every part plays at its designed level in Resolve')
    report(fit={nm: round(db(abs(v)), 2) for (nm, _), v in zip(parts, g)}, fit_flags=flags)


# ---------------------------------------------------------------- build: premix + master
def sfx_audit(voice, layers, hook_end, P):
    import sfxlib
    vs = sfxlib.speech_loudness(voice)
    target = dict(sfxlib.LONGFORM_TARGET, **(P.get('sfx_levels') or {})); bonus = float(P.get('sfx_hook_bonus', 3.0))
    J = json.load(open(json.load(open(REPORT))['items'])); per = collections.defaultdict(list); w = int(0.4 * SR)
    for it in J['items']:
        key = f"A{it['track']}"
        if key not in layers or 'SFX' not in layers[key][0]: continue
        t0 = int(it['start'] / J['fps'] * SR); seg = layers[key][1][t0:t0 + max(int(it['dur'] / J['fps'] * SR), w)]
        best = sfxlib.loudness(seg)                  # audio.py's own measure (mono sum), so the targets compare 1:1
        nm = it['name']; typ = nm.split('__')[0] if '__' in nm else re.match(r'[a-z]+', nm).group(0)
        typ = {'typing': 'key'}.get(typ, typ); hook = it['start'] / J['fps'] < hook_end
        per[(typ, hook)].append(best - vs - (target.get(typ, -14) + (bonus if hook else 0.0)))
    rows = {f"{t}{' (hook)' if h else ''}": round(float(np.median(v)), 1) for (t, h), v in sorted(per.items())}
    print(f'SFX against the voice ({vs:.1f} LUFS speaking), median LU off target per type: '
          + ', '.join(f'{k} {v:+.1f}' for k, v in rows.items()))
    off = {k: v for k, v in rows.items() if abs(v) > 1.5}
    if off: print('FLAG: SFX off target by more than 1.5 LU:', off)
    return dict(voice_speaking_lufs=round(vs, 1), off_target_lu=rows)


def windows(y, hook_end):
    """hook vs body loudness and the quietest / loudest 30 s - where a level problem would show"""
    out = {'hook': round(lufs(y[:int(hook_end * SR)]), 2) if hook_end else None, 'body': round(lufs(y[int(hook_end * SR):]), 2)}
    w = []
    for s in range(0, len(y) - 30 * SR + 1, 15 * SR):
        v = lufs(y[s:s + 30 * SR])
        if np.isfinite(v) and v > -40: w.append((v, s / SR))
    if w:
        lo, hi = min(w), max(w)
        out.update(quietest_30s=[round(lo[0], 1), f'{int(lo[1] // 60)}:{int(lo[1] % 60):02d}'],
                   loudest_30s=[round(hi[0], 1), f'{int(hi[1] // 60)}:{int(hi[1] % 60):02d}'])
    return out


def cmd_build(a):
    P = plan(); import sfxlib
    hook_end = float(P.get('hook_end') or 0.0); bus_lift = float(P.get('sfx_bus_lift', 0.0))
    stem = read_wav(a.stem); layers = load_layers()
    if a.voice_db is None:
        raw = read_wav('voice48.wav')
        ref = sfxlib.speech_loudness(raw) - bus_lift                  # the voice every layer was levelled against
        a.voice_db = ref - sfxlib.speech_loudness(stem)
        print(f'voice: the stem speaks at {sfxlib.speech_loudness(stem):.1f} LUFS, the layers were levelled against '
              f'{ref:.1f} (raw voice {ref + bus_lift:.1f}, sfx_bus_lift {bus_lift}) -> stem {a.voice_db:+.2f} dB')
    voice = stem * np.float32(10 ** (a.voice_db / 20))
    n = min([len(voice)] + [len(x) for _, x in layers.values()])
    mix = voice[:n] + sum(x[:n] for _, x in layers.values())
    audit = sfx_audit(voice[:n], layers, hook_end, P)
    I0 = lufs(mix); G = -14.0 - I0
    for _ in range(3):
        y, g = limit(mix * np.float32(10 ** (G / 20)), a.ceil); G += -14.0 - lufs(y)
    y, g = limit(mix * np.float32(10 ** (G / 20)), a.ceil)
    gr = -20 * np.log10(np.maximum(g, 1e-9)); I = lufs(y); tp = db(tp_env(y).max())
    win = windows(y, hook_end)
    print(f'premix {I0:.2f} LUFS -> {G:+.2f} dB into the limiter -> {I:.2f} LUFS, true peak {tp:.2f} dBTP (ceiling {a.ceil}); '
          f'limiter max {gr.max():.1f} dB, >0.5 dB {100 * (gr > 0.5).mean():.1f}% of the time | {win}')
    sf.write(L + 'premix.wav', mix, SR, subtype='FLOAT'); sf.write(L + 'master.wav', y.astype(np.float32), SR, subtype='PCM_24')
    report(build=dict(voice_db=round(a.voice_db, 2), premix_lufs=round(I0, 2), drive_db=round(G, 2), lufs=round(I, 2),
                      true_peak=round(tp, 2), ceiling=a.ceil, limiter_max_db=round(float(gr.max()), 1),
                      limiter_busy_pct=round(100 * float((gr > 0.5).mean()), 1), sfx=audit, **win))
    print(f'-> {L}premix.wav, {L}master.wav')


# ---------------------------------------------------------------- deliver: mux, measure, fix, re-measure
def probe_dur(p):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=duration',
                          '-of', 'csv=p=0', p], capture_output=True, text=True)
    if not out.stdout.strip(): sys.exit(f'no video stream in {p}: {out.stderr.strip()[:200]}')
    return float(out.stdout.strip())


def decode(p, t=None, d=None):
    cmd = ['ffmpeg', '-v', 'error'] + (['-ss', f'{t:.3f}', '-t', f'{d:.3f}'] if t is not None else []) + \
          ['-i', p, '-vn', '-map', '0:a:0', '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True, check=True).stdout, np.float32).reshape(-1, 2)


def mux(pic, wav, out):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', pic, '-i', wav, '-map', '0:v:0', '-map', '1:a:0', '-c:v', 'copy',
                    '-c:a', 'aac', '-b:a', '384k', '-ar', str(SR), out], check=True)


def cmd_deliver(a):
    m = read_wav(a.master); dur = probe_dur(a.picture); n = int(round(dur * SR))
    m = np.pad(m, ((0, max(0, n - len(m))), (0, 0)))[:n]
    print(f'picture {dur:.3f} s, master {len(m) / SR:.3f} s (padded / trimmed to the picture)')
    # The picture's own (Resolve) audio vs the master. Decoded in full: ffmpeg's fast seek (-ss before -i) on AAC is off
    # by up to ~20 samples, which reads as a false sync error. Band-limited GCC-PHAT gives a sharp peak even on music.
    pa = decode(a.picture).mean(1); lags = []
    for t in (0.1 * dur, 0.3 * dur, 0.5 * dur, 0.7 * dur, 0.9 * dur):
        s, e = int(t * SR), int(min(t + 10.0, dur) * SR); x, y = pa[s:e], m[s:e].mean(1); k = min(len(x), len(y)); x, y = x[:k], y[:k]
        if k < SR or np.sqrt((x ** 2).mean()) < 1e-4: continue       # silence says nothing
        nf = 1 << int(np.ceil(np.log2(2 * k))); f = np.fft.rfftfreq(nf, 1 / SR)
        R = np.fft.rfft(x, nf) * np.conj(np.fft.rfft(y, nf)); R *= ((f > 150) & (f < 6000)) / (np.abs(R) ** 0.7 + 1e-12)
        r = np.fft.irfft(R, nf); r = np.concatenate([r[-4800:], r[:4801]]); lags.append(int(np.argmax(r)) - 4800)
    del pa
    print('sync (samples, 5 windows):', lags)
    if not lags or sorted(abs(v) for v in lags)[len(lags) // 2] > 2 or sum(abs(v) <= 2 for v in lags) < (len(lags) + 1) // 2:
        sys.exit('SYNC: the master does not line up with the picture - check the stem ranges')
    work = L + 'master_deliver.wav'; sf.write(work, m, SR, subtype='PCM_24')
    for rnd in range(4):
        mux(a.picture, work, a.final); y = decode(a.final)
        env = tp_env(y); over = np.where(env > 10 ** (-1.0 / 20))[0]
        I = lufs(y); tp = db(env.max())
        print(f'round {rnd}: final file {I:.2f} LUFS, true peak {tp:.2f} dBTP, {len(over)} samples over -1 dBTP')
        if not len(over) or rnd == 3: break
        ev = np.split(over, np.where(np.diff(over) > SR // 2)[0] + 1)   # one event per cluster of overs
        for e in ev:                                                   # a short dip under each AAC overshoot
            c = e[np.argmax(env[e])]; dip = db(env[c]) + 1.0 + 0.3
            h, f = int(0.25 * SR), int(0.05 * SR); s0, s1 = max(0, c - h), min(len(m), c + h)
            gg = np.full(s1 - s0, 10 ** (-dip / 20), np.float32); r = np.linspace(1, gg[0], min(f, len(gg) // 2), dtype=np.float32)
            gg[:len(r)] = r; gg[-len(r):] = r[::-1]; m[s0:s1] *= gg[:, None]
            print(f'   dip {dip:.1f} dB at {c / SR // 60:.0f}:{c / SR % 60:05.2f}')
        sf.write(work, m, SR, subtype='PCM_24')
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', a.final, '-vn', '-af', 'ebur128=peak=true:framelog=quiet',
                        '-f', 'null', '-'], capture_output=True, text=True).stderr
    lra = re.findall(r'LRA:\s+(-?[\d.]+) LU', r); P = plan(); win = windows(y, float(P.get('hook_end') or 0.0))
    v = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,bit_rate',
                        '-of', 'json', a.final], capture_output=True, text=True).stdout
    vs = json.loads(v)['streams'][0]
    res = dict(file=os.path.abspath(a.final), lufs=round(I, 2), true_peak=round(tp, 2), lra=float(lra[-1]) if lra else None,
               sync_samples=lags, video=f"{vs['width']}x{vs['height']} {vs['r_frame_rate']} {int(vs.get('bit_rate', 0)) / 1e6:.1f} Mb/s",
               size_gb=round(os.path.getsize(a.final) / 1e9, 2), duration_s=round(dur, 3), **win)
    if int(vs.get('bit_rate', 0)) > 30e6:
        print(f"NOTE: the picture is {int(vs['bit_rate']) / 1e6:.0f} Mb/s - the user's YouTube 2160p preset gives ~11; "
              'the preset did not load (rs_picture.py prints it) and the upload will be slow')
    print('FINAL:', json.dumps(res))
    ok = abs(I + 14) <= 0.3 and tp <= -1.0
    print('PASS: ready to upload' if ok else 'CHECK: outside -14 +-0.3 LUFS / -1 dBTP')
    report(final=res, final_pass=ok)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest='cmd', required=True)
    c = sp.add_parser('chain'); c.add_argument('stem'); c.add_argument('--items'); c.add_argument('--raw')
    c.add_argument('--from', dest='t0', type=float, default=0.0); c.add_argument('--tracks', type=int, nargs='+', default=[1])
    c = sp.add_parser('layers'); c.add_argument('--items', default=os.path.join(DLV, 'items.json'))
    c = sp.add_parser('fit'); c.add_argument('--mix', default=os.path.join(DLV, 'mix_resolve.wav'))
    c.add_argument('--stem', default=os.path.join(DLV, 'stem_base.wav'))
    c = sp.add_parser('build'); c.add_argument('--stem', default=os.path.join(DLV, 'stem_base.wav')); c.add_argument('--voice-db', type=float)
    c.add_argument('--ceil', type=float, default=-1.5)
    c = sp.add_parser('deliver'); c.add_argument('picture'); c.add_argument('final'); c.add_argument('--master', default=L + 'master.wav')
    a = ap.parse_args()
    dict(chain=cmd_chain, layers=cmd_layers, fit=cmd_fit, build=cmd_build, deliver=cmd_deliver)[a.cmd](a)
