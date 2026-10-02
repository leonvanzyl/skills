"""Synthesize every sound for a short (numpy/scipy only) and write the stems + mix.
usage: python audio.py s1  -> reads cut.json, gfx/sfx_events.json, <sk>/events_extra.json ; writes <sk>/stems/*.wav"""
import json, sys, os, numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy import signal
SR = 48000
sk = sys.argv[1]
C = json.load(open('cut.json'))[sk]
END = C['END']; N = int(round(END * SR))
rng = np.random.default_rng(7)
voice, _ = sf.read(f'{sk}/voice.wav'); voice = voice.astype(np.float32)
if len(voice) < N: voice = np.pad(voice, ((0, N - len(voice)), (0, 0)))
voice = voice[:N]
vpeak = np.abs(voice).max()

def env_exp(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))

def norm(x):
    m = np.abs(x).max(); return x / m if m > 0 else x

def lp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'low'); return signal.lfilter(b, a, x)

def hp(x, fc, order=2):
    b, a = signal.butter(order, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)

def bp(x, f0, f1, order=2):
    b, a = signal.butter(order, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)

# ---------------- sound designs (mono, peak-normalised) ----------------
def click():
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 1250 * np.exp(-t / 0.018) + 620          # bubbly downward chirp
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = np.sin(ph) * env_exp(n, 0.016)
    s += 0.35 * np.sin(2 * np.pi * np.cumsum(1.5 * f) / SR) * env_exp(n, 0.008)
    s[:24] *= np.linspace(0, 1, 24)
    return norm(lp(s, 5000))

def key(i):
    n = int(0.05 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    s = bp(nz, 1800 + 300 * (i % 3), 5200) * env_exp(n, 0.004)
    s += 0.6 * np.sin(2 * np.pi * (170 + 15 * (i % 4)) * t) * env_exp(n, 0.010)
    s[:8] *= np.linspace(0, 1, 8)
    return norm(s)

def pop():
    n = int(0.22 * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t / 0.04) + 62
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.055)
    s += 0.25 * lp(rng.standard_normal(n), 900) * env_exp(n, 0.012)
    s[:48] *= np.linspace(0, 1, 48)
    return norm(lp(s, 1800))

def chime():
    n = int(1.1 * SR); out = np.zeros(n)
    for k, (f, t0) in enumerate([(1318.5, 0.0), (1760.0, 0.13)]):
        i0 = int(t0 * SR); m = n - i0; t = np.arange(m) / SR
        tone = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * 2.01 * f * t) * env_exp(m, 0.12) + 0.12 * np.sin(2 * np.pi * 3.02 * f * t) * env_exp(m, 0.06)
        e = env_exp(m, 0.35); e[:96] *= np.linspace(0, 1, 96)
        out[i0:] += tone * e * (0.85 if k == 0 else 1.0)
    return norm(out)

def whoosh(variant, dur_out=0.45, dur_in=0.6):
    """low airy whoosh whose loudest moment is exactly at dur_out (the whip midpoint)"""
    pre, post = dur_out + 0.12, dur_in + 0.25
    n = int((pre + post) * SR); t = np.arange(n) / SR; tm = pre
    nz = rng.standard_normal(n)
    lo, hi, q = [(180, 700, 1.2), (140, 560, 1.4), (220, 820, 1.1), (160, 640, 1.3)][variant % 4]
    # centre frequency rises into the midpoint and falls after it
    x = np.clip((t - (tm - dur_out)) / dur_out, 0, 1); y = np.clip((t - tm) / dur_in, 0, 1)
    fc = np.where(t < tm, lo + (hi - lo) * x ** 1.6, hi - (hi - lo) * y ** 0.8)
    w = np.clip((fc - lo) / (hi - lo), 0, 1)
    s = (1 - w) * bp(nz, lo * 0.55, lo * 1.7) + w * bp(nz, hi * 0.55, hi * 1.5) * 0.8
    e = np.where(t < tm, (np.clip((t - (tm - pre)) / pre, 0, 1)) ** 2.2, np.exp(-(t - tm) / (0.22 + 0.05 * variant)))
    s = lp(s * e, 1400)
    s = s / np.abs(s[int((tm - 0.03) * SR):int((tm + 0.03) * SR)]).max()
    return np.clip(s, -1.2, 1.2) / 1.2, int(tm * SR)

def riser(dur=2.6):
    n = int(dur * SR); t = np.arange(n) / SR; p = t / dur
    f = 48 * 2 ** (1.1 * p ** 1.3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f) / SR + 0.3)
    nz = rng.standard_normal(n)
    w = p ** 2
    air = (1 - w) * bp(nz, 180, 500) + w * bp(nz, 900, 2600) * 0.7
    s = 0.8 * lp(tone, 400) + 0.45 * air
    e = p ** 2.4
    s *= e
    s[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))   # audible end exactly on the join
    return norm(s)

# ---------------- events ----------------
ev = []
gfx_ev = json.load(open('gfx/sfx_events.json'))
for r in C['runs']:
    rid = f"{sk}_r{r['i']}"
    for e in gfx_ev.get(rid, []): ev.append(dict(t=r['T0'] + e['t'], type=e['type']))
if os.path.exists(f'{sk}/events_extra.json'):
    ev += json.load(open(f'{sk}/events_extra.json'))
LEVEL = {'click': -10, 'pop': -10, 'chime': -10, 'whoosh': -9, 'key': -16, 'tick': -16}
sfx = np.zeros(N); keyi = 0; wv = 0
for e in sorted(ev, key=lambda e: e['t']):
    g = vpeak * 10 ** (LEVEL[e['type']] / 20)
    if e['type'] == 'whoosh':
        s, mid = whoosh(wv); wv += 1
        i0 = int(round(e['t'] * SR)) - mid          # loudest moment exactly on the whip midpoint
    else:
        s = {'click': click, 'pop': pop, 'chime': chime}.get(e['type'], None)
        s = s() if s else key(keyi); keyi += 1
        i0 = int(round(e['t'] * SR))
    i0c = max(0, i0); s = s[i0c - i0:]
    m = min(len(s), N - i0c)
    sfx[i0c:i0c + m] += g * s[:m]
sfx2 = np.stack([sfx, sfx], 1)

# riser: audible end exactly on the hook -> first point join (end of run 0)
join = C['runs'][0]['T1']
rs = riser(2.6); i1 = int(round(join * SR)); i0 = i1 - len(rs)
ris = np.zeros((N, 2)); a = max(0, i0)
ris[a:i1, 0] = rs[a - i0:] * vpeak * 10 ** (-12 / 20); ris[:, 1] = ris[:, 0]

# music bed: a styled, seeded track that fits this short (shorts.json -> "music"), beat drops on the hook join,
# sidechain-ducked under the voice, ends exactly on END. Never the same track twice: the seed defaults to the title hash.
import zlib
sys.path.insert(0, 'scripts'); import music as MUS
SH = json.load(open('shorts.json'))[sk]; mp = SH.get('music', {})
KEYS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
key = mp.get('key'); key = KEYS.index(key) if isinstance(key, str) and key in KEYS else key
seed = int(mp.get('seed', zlib.crc32((SH.get('title', '') + '|' + sk).encode()) % 1000003))
mus, mparams = MUS.render(mp.get('style', 'lofi'), seed, END, drop=join, bpm=mp.get('bpm'), key=key, mood=mp.get('mood'))
mus = mus.astype(np.float64)[:N]
if len(mus) < N: mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
fi = int(0.8 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
fo = int(1.2 * SR); mus[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
meter = pyln.Meter(SR)
mus *= 10 ** ((-31 - meter.integrated_loudness(mus)) / 20)
venv = np.abs(voice.mean(1)); venv = signal.filtfilt(*signal.butter(1, 6 / (SR / 2)), venv)
duck = 1 - 0.45 * np.clip(venv / (np.percentile(venv, 90) + 1e-9), 0, 1)
mus *= duck[:, None]
json.dump(mparams, open(f'{sk}/music.json', 'w'), indent=1)
print('music:', mparams)

os.makedirs(f'{sk}/stems', exist_ok=True)
for nm, x in [('voice', voice), ('sfx', sfx2), ('riser', ris), ('music', mus)]:
    sf.write(f'{sk}/stems/{nm}.wav', x[:N].astype(np.float32), SR, subtype='PCM_24')
mix = voice + sfx2 + ris + mus
# true-peak limiter (spec: final mix <= -1 dBFS true peak). 4x oversampled peak detection, 1.5 ms look-ahead (minimum
# filter), smoothed gain; touches only the few hot transients, so the integrated loudness stays ~-14 LUFS. (A plain
# sample-peak rescale to 0.95 let a less-compressed voice through at -0.4 dBTP.)
from scipy.ndimage import minimum_filter1d, uniform_filter1d
TP_THR = 10 ** (-1.3 / 20)
for _ in range(3):
    os_pk = np.max(np.abs(np.stack([signal.resample_poly(mix[:, c], 4, 1) for c in range(mix.shape[1])], 1)), 1)
    n4 = len(os_pk) // 4 * 4
    pk_n = os_pk[:n4].reshape(-1, 4).max(1)
    pk_n = np.pad(pk_n, (0, max(0, len(mix) - len(pk_n))), mode='edge')[:len(mix)]
    g = np.minimum(1.0, TP_THR / np.maximum(pk_n, 1e-9))
    if g.min() >= 0.9999: break
    la = int(0.0015 * SR)
    g = minimum_filter1d(g, size=4 * la + 1)
    g = uniform_filter1d(g, size=2 * la + 1)
    mix = mix * g[:, None]
tp = np.max(np.abs(np.stack([signal.resample_poly(mix[:, c], 4, 1) for c in range(mix.shape[1])], 1)))
print(f'{sk}: true peak after limiter {20 * np.log10(tp):.2f} dBTP')
sf.write(f'{sk}/mix.wav', mix.astype(np.float32), SR, subtype='PCM_24')
print(f'{sk}: END={END:.3f}s N={N} events={len(ev)} voice_peak={20*np.log10(vpeak):.1f}dBFS mix_peak={20*np.log10(np.abs(mix).max()):.1f} mix_lufs={meter.integrated_loudness(mix):.1f} music_lufs={meter.integrated_loudness(mus+1e-9):.1f}')
