"""Synthesized background music for shorts: styled, seeded, never the same twice.
   render(style, seed, dur, drop=None, bpm=None, key=None, mood=None) -> (float32 stereo @48k, params)
Styles (pick to fit the topic; lofi is the default voice-over bed):
  lofi       dusty swung boom-bap drums, Rhodes 7th/9th chords, round bass, vinyl crackle, tape wobble   (70-88 bpm)
  chillhop   crisper swing, Rhodes + nylon-ish plucks, shaker                                           (86-98 bpm)
  ambient    soft pads, sub, air, no drums - serious / reflective / cinematic topics                     (62-76 bpm)
  synthwave  gated-reverb snare, saw pads, octave bass - retro / hype / "the future is here"            (96-112 bpm)
  upbeat     light four-on-the-floor house, offbeat bass, chord stabs - launches, wins, energy          (112-122 bpm)
mood: 'warm' (major) | 'moody' (minor) | None (style default, seeded choice)
drop: seconds where the beat enters on a downbeat (use the hook -> first-point join; the riser lands there too).
      Before it: chords + texture only, low-passed ("filtered intro"); the groove opens up on the drop.
Everything random comes from `seed`, so a short re-renders identically but two shorts never share a track."""
import numpy as np
from scipy import signal

SR = 48000
STYLES = {
    'lofi':      dict(bpm=(70, 88), swing=(0.56, 0.62), kit='dusty', keys='ep', extra=None, bass='round', texture='vinyl', lp=(4300, 6500), prog=('jazz', 'minor'), wow=True),
    'chillhop':  dict(bpm=(86, 98), swing=(0.54, 0.58), kit='crisp', keys='ep', extra='pluck', bass='round', texture='light', lp=(7500, 10000), prog=('jazz',), wow=False),
    'ambient':   dict(bpm=(62, 76), swing=(0.5, 0.5), kit=None, keys='pad', extra=None, bass='sub', texture='air', lp=(6000, 8500), prog=('float', 'minor'), wow=False),
    'synthwave': dict(bpm=(96, 112), swing=(0.5, 0.5), kit='gated', keys='saw', extra='arp', bass='octave', texture=None, lp=(9000, 12000), prog=('minor',), wow=False),
    'upbeat':    dict(bpm=(112, 122), swing=(0.5, 0.52), kit='house', keys='stab', extra=None, bass='offbeat', texture=None, lp=(10000, 13000), prog=('pop', 'jazz'), wow=False),
}
Q = {'maj7': [0, 4, 7, 11], 'maj9': [0, 4, 7, 11, 14], 'm7': [0, 3, 7, 10], 'm9': [0, 3, 7, 10, 14], '7': [0, 4, 7, 10],
     '9': [0, 4, 7, 10, 14], '7sus': [0, 5, 7, 10], '6': [0, 4, 7, 9], 'm6': [0, 3, 7, 9], 'maj': [0, 4, 7], 'min': [0, 3, 7], 'add9': [0, 4, 7, 14]}
PROGS = {
    'jazz':  [[(2, 'm9'), (7, '9'), (0, 'maj9'), (9, 'm7')], [(0, 'maj7'), (9, 'm9'), (2, 'm7'), (7, '7sus')],
              [(5, 'maj9'), (4, 'm7'), (9, 'm9'), (0, 'maj7')], [(9, 'm9'), (5, 'maj7'), (0, 'maj9'), (7, '6')],
              [(5, 'maj7'), (7, '9'), (4, 'm7'), (9, 'm9')], [(0, 'maj9'), (4, 'm7'), (5, 'maj7'), (7, '7sus')]],
    'minor': [[(0, 'm9'), (5, 'm9'), (10, '9'), (3, 'maj7')], [(0, 'm7'), (8, 'maj7'), (5, 'm7'), (7, 'm7')],
              [(0, 'm9'), (10, '6'), (8, 'maj7'), (7, 'm7')], [(0, 'm7'), (3, 'maj7'), (8, 'maj9'), (7, '7sus')]],
    'float': [[(0, 'maj9'), (5, 'maj9'), (9, 'm9'), (7, 'add9')], [(0, 'add9'), (4, 'm7'), (5, 'maj7'), (5, 'maj7')],
              [(9, 'm9'), (5, 'maj9'), (0, 'add9'), (7, '7sus')]],
    'pop':   [[(0, 'add9'), (7, 'maj'), (9, 'm7'), (5, 'maj7')], [(9, 'm7'), (5, 'maj7'), (0, 'add9'), (7, 'maj')],
              [(0, 'maj7'), (5, 'maj7'), (9, 'm7'), (7, '7sus')]],
}
mtof = lambda m: 440.0 * 2 ** ((m - 69) / 12)


def _lp(x, fc, o=2): b, a = signal.butter(o, min(fc, SR * 0.45) / (SR / 2), 'low'); return signal.lfilter(b, a, x, axis=0)   # axis 0 = time
def _hp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x, axis=0)
def _bp(x, f0, f1, o=2): b, a = signal.butter(o, [f0 / (SR / 2), min(f1, SR * 0.45) / (SR / 2)], 'band'); return signal.lfilter(b, a, x, axis=0)
def _env(n, a, d):
    t = np.arange(n) / SR; e = np.exp(-t / d); na = max(1, int(a * SR)); e[:na] *= np.linspace(0, 1, na); return e


class Mix:
    def __init__(self, n): self.L = np.zeros(n); self.R = np.zeros(n); self.n = n
    def add(self, x, t, g=1.0, pan=0.5):
        i = int(round(t * SR))
        if i >= self.n or len(x) == 0: return
        if i < 0: x = x[-i:]; i = 0
        m = min(len(x), self.n - i)
        self.L[i:i + m] += x[:m] * g * np.cos(pan * np.pi / 2); self.R[i:i + m] += x[:m] * g * np.sin(pan * np.pi / 2)
    def st(self): return np.stack([self.L, self.R], 1)


# ---------------- instruments ----------------
def rhodes(f, dur, vel, rng):
    n = int((dur + 0.6) * SR); t = np.arange(n) / SR
    idx = (1.6 + 1.2 * vel) * np.exp(-t / 0.28) + 0.25
    y = np.sin(2 * np.pi * f * t + idx * np.sin(2 * np.pi * f * t))
    y += 0.06 * np.sin(2 * np.pi * f * 14.0 * t) * np.exp(-t / 0.04)          # tine "bark"
    e = _env(n, 0.004, 1.7); rel = np.clip((dur + 0.6 - t) / 0.35, 0, 1); y *= e * rel
    return y * (0.55 + 0.45 * vel)

def pluck(f, dur, vel, rng):
    n = int((dur + 0.4) * SR); N = max(2, int(SR / f))
    x = np.zeros(n); x[:N] = _lp(rng.standard_normal(N), 3000 + 3000 * vel)
    a = np.zeros(N + 2); a[0] = 1; a[N] = -0.4985; a[N + 1] = -0.4985
    y = signal.lfilter([1.0], a, x)
    return _lp(y, 4500) * (0.5 + 0.5 * vel)

def pad(f, dur, vel, rng, bright=False):
    n = int((dur + 1.2) * SR); t = np.arange(n) / SR; y = np.zeros(n)
    for det in (-0.09, 0.0, 0.11):
        ph = (f * (1 + det / 100) * t + rng.random()) % 1
        y += (2 * ph - 1) if bright else np.sin(2 * np.pi * f * (1 + det / 100) * t)
    y = _lp(y, 2400 if bright else 1800)
    a = np.minimum(1, t / 0.7); r = np.clip((dur + 1.2 - t) / 1.1, 0, 1)
    return y * a * r * 0.35

def bassnote(f, dur, vel, kind='round'):
    n = int((dur + 0.15) * SR); t = np.arange(n) / SR
    y = np.sin(2 * np.pi * f * t) + (0.35 if kind != 'sub' else 0.08) * np.sin(4 * np.pi * f * t)
    e = np.minimum(1, t / 0.008) * np.clip((dur + 0.15 - t) / 0.12, 0, 1)
    if kind != 'sub': e *= 0.55 + 0.45 * np.exp(-t / 0.5)
    return _lp(np.tanh(1.4 * y) * e, 420 if kind != 'octave' else 900) * (0.6 + 0.4 * vel)

def kick(kit, rng):
    n = int(0.45 * SR); t = np.arange(n) / SR
    f0, f1, dk = {'dusty': (95, 46, 0.32), 'crisp': (120, 50, 0.28), 'gated': (130, 52, 0.30), 'house': (140, 48, 0.36)}[kit]
    f = f1 + (f0 - f1) * np.exp(-t / 0.045)
    y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / dk)
    y += 0.25 * _hp(rng.standard_normal(n), 2000) * np.exp(-t / 0.004)
    return np.tanh(1.6 * y)

def snare(kit, rng):
    n = int(0.5 * SR); t = np.arange(n) / SR
    nz = rng.standard_normal(n)
    if kit == 'dusty':  y = _bp(nz, 900, 5200) * np.exp(-t / 0.13) + 0.5 * np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.05); y = _lp(y, 5000)
    elif kit == 'gated': y = _bp(nz, 700, 9000) * np.exp(-t / 0.35) * (t < 0.26) + 0.6 * np.sin(2 * np.pi * 200 * t) * np.exp(-t / 0.06)
    elif kit == 'house': y = _bp(nz, 1200, 9000) * (np.exp(-t / 0.09) + 0.6 * np.exp(-np.abs(t - 0.012) / 0.006))   # clap-ish
    else:                y = _bp(nz, 1500, 9000) * np.exp(-t / 0.10) + 0.4 * np.sin(2 * np.pi * 210 * t) * np.exp(-t / 0.04)
    return y

def hat(open_, kit, rng):
    n = int((0.25 if open_ else 0.06) * SR); t = np.arange(n) / SR
    y = _hp(rng.standard_normal(n), 7000 if kit != 'dusty' else 6000) * np.exp(-t / (0.12 if open_ else 0.018))
    return _lp(y, 9000 if kit == 'dusty' else 14000)


# ---------------- render ----------------
def render(style='lofi', seed=0, dur=60.0, drop=None, bpm=None, key=None, mood=None):
    st = STYLES.get(style, STYLES['lofi']); rng = np.random.default_rng(seed)
    bpm = float(bpm or round(rng.uniform(*st['bpm'])))
    swing = float(rng.uniform(*st['swing']))
    key = int(key if key is not None else rng.integers(0, 12))
    fam = 'minor' if mood == 'moody' else ('jazz' if mood == 'warm' and 'jazz' in PROGS else None)
    fam = fam or st['prog'][int(rng.integers(0, len(st['prog'])))]
    prog = PROGS[fam][int(rng.integers(0, len(PROGS[fam])))]
    beat = 60 / bpm; bar = 4 * beat
    drop = float(drop if drop is not None else 0.0)
    g0 = drop - np.ceil(drop / bar) * bar if drop > 0 else 0.0                 # grid start so a downbeat lands on the drop
    nb = int(np.ceil((dur - g0) / bar)) + 1
    n = int(dur * SR); mel = Mix(n); drm = Mix(n); bas = Mix(n)
    root_m = 48 + key                                                           # chord register
    prev = None; kickt = []
    kick_pat = [[0, 2.5], [0, 1.75, 2.5], [0, 0.75, 2.5], [0, 2.25, 2.75]][int(rng.integers(0, 4))]
    hat_16 = st['kit'] in ('crisp', 'house') or rng.random() < 0.3
    use_mel = style in ('lofi', 'chillhop') and rng.random() < 0.8
    scale = [0, 2, 4, 7, 9] if fam != 'minor' else [0, 3, 5, 7, 10]
    motif = [int(rng.integers(0, 5)) for _ in range(4)]
    K, SN = (kick(st['kit'], rng), snare(st['kit'], rng)) if st['kit'] else (None, None)
    HC, HO = (hat(False, st['kit'], rng), hat(True, st['kit'], rng)) if st['kit'] else (None, None)

    unit = 0.25 if hat_16 else 0.5                                             # swing the off-16ths (or off-8ths)
    def sw(pos):
        k = pos / unit
        return pos + (swing - 0.5) * 2 * unit if abs(k - round(k)) < 1e-6 and int(round(k)) % 2 == 1 else pos

    for b in range(nb):
        t0 = g0 + b * bar
        if t0 > dur: break
        deg, q = prog[b % 4]
        chord = [root_m + deg + i for i in Q[q]]
        # voice-lead: shift by octaves toward the previous chord's centre, drop the root in the upper voicing
        up = [m for m in chord[1:]] if len(chord) > 3 else chord
        if prev is not None:
            c = np.mean(prev); up = [m - 12 if m - c > 6 else (m + 12 if c - m > 6 else m) for m in up]
        up = sorted(up); prev = up
        post = t0 >= drop - 1e-6
        vel = 0.55 + 0.25 * rng.random()
        if st['keys'] == 'ep':
            hits = [0, 2.5 * beat] if rng.random() < 0.5 else [0]
            for h in hits:
                for j, m in enumerate(up):
                    mel.add(rhodes(mtof(m), bar - h - 0.05, vel * (0.9 if h else 1.0), rng), t0 + h + j * 0.012 + rng.normal(0, 0.004), 0.16, 0.3 + 0.4 * j / len(up))
        elif st['keys'] in ('pad', 'saw'):
            for j, m in enumerate(up): mel.add(pad(mtof(m), bar, vel, rng, bright=st['keys'] == 'saw'), t0, 0.22, 0.2 + 0.6 * j / len(up))
        elif st['keys'] == 'stab':
            for k in range(4):
                for j, m in enumerate(up): mel.add(rhodes(mtof(m + 12), 0.22, vel, rng), t0 + (k + 0.5) * beat, 0.12 if post else 0.06, 0.3 + 0.4 * j / len(up))
            for j, m in enumerate(up): mel.add(pad(mtof(m), bar, vel, rng), t0, 0.10, 0.5)
        if st['extra'] == 'pluck' and post:
            for k in range(8):
                m = up[(k * 2 + b) % len(up)] + 12
                mel.add(pluck(mtof(m), 0.4, 0.6, rng), t0 + sw(k / 2) * beat, 0.10, 0.25 + 0.5 * (k % 2))
        if st['extra'] == 'arp' and post:
            for k in range(16):
                m = up[k % len(up)] + (12 if k % 8 >= 4 else 0)
                mel.add(pad(mtof(m), 0.12, 0.7, rng, bright=True), t0 + k * beat / 4, 0.12, 0.35 + 0.3 * (k % 2))
        if use_mel and post and b % 2 == 1:
            for k, d in enumerate(motif):
                m = root_m + 24 + scale[(d + b // 2) % 5]
                mel.add(rhodes(mtof(m), beat * 0.9, 0.5, rng), t0 + sw(1 + k * 0.5 + (0.25 if k == 3 else 0)) * beat, 0.07, 0.6)
        # bass
        rf = mtof(root_m + deg - 24)
        if post or st['bass'] == 'sub':
            if st['bass'] == 'round':
                bas.add(bassnote(rf, 1.6 * beat, 0.9), t0, 0.5); bas.add(bassnote(rf * (1.5 if rng.random() < 0.5 else 1), 0.9 * beat, 0.7), t0 + sw(2.5) * beat, 0.42)
            elif st['bass'] == 'sub':
                bas.add(bassnote(rf, bar, 0.7, 'sub'), t0, 0.45)
            elif st['bass'] == 'octave':
                for k in range(8): bas.add(bassnote(rf * (2 if k % 2 else 1), 0.45 * beat, 0.8, 'octave'), t0 + k * beat / 2, 0.36)
            elif st['bass'] == 'offbeat':
                for k in range(4): bas.add(bassnote(rf, 0.4 * beat, 0.85), t0 + (k + 0.5) * beat, 0.45)
        # drums (after the drop only)
        if K is not None and post:
            ks = [0, 1, 2, 3] if st['kit'] == 'house' else kick_pat
            for p in ks:
                tt = t0 + sw(p) * beat + rng.normal(0, 0.004); drm.add(K, tt, 0.55); kickt.append(tt)
            for p in (1, 3):
                drm.add(SN, t0 + p * beat + rng.normal(0, 0.005), 0.30 if st['kit'] != 'gated' else 0.26, 0.52)
            if st['kit'] == 'dusty' and rng.random() < 0.5: drm.add(SN, t0 + sw(3.75) * beat, 0.08, 0.5)     # ghost
            steps = 16 if hat_16 else 8
            for k in range(steps):
                pos = k * 4 / steps
                if st['kit'] == 'house' and k % (steps // 4) == 0: continue
                o = (k == steps - 2 and b % 4 == 3) or (st['kit'] == 'house' and k % (steps // 4) == steps // 8)
                drm.add(HO if o else HC, t0 + sw(pos) * beat + rng.normal(0, 0.003), (0.10 if o else 0.07) * (1 if k % 2 == 0 else 0.7), 0.62)
    # texture
    tex = np.zeros(n)
    if st['texture'] == 'vinyl':
        imp = (rng.random(n) < 14 / SR) * rng.uniform(0.2, 1.0, n) * rng.choice([-1, 1], n)
        tex = _bp(imp, 1200, 7000) * 0.5 + _lp(rng.standard_normal(n), 3500) * 0.012
    elif st['texture'] == 'light':
        tex = _lp(rng.standard_normal(n), 4000) * 0.006
    elif st['texture'] == 'air':
        tex = _bp(rng.standard_normal(n), 300, 2500) * 0.02
    x = mel.st() + bas.st() + drm.st() + tex[:, None]
    # filtered intro -> opens on the drop
    t = np.arange(n) / SR
    lo, hi = st['lp']; lp_cut = float(rng.uniform(lo, hi))
    if drop > 0:
        pre = _lp(_lp(x, 1400), 1400); w = np.clip((t - (drop - 0.25)) / 0.25, 0, 1)[:, None]
        x = pre * (1 - w) + x * w
    x = _lp(x, lp_cut, 2)
    # tape wobble (lofi)
    if st['wow']:
        rate, depth = rng.uniform(0.35, 0.6), rng.uniform(0.0012, 0.0024)
        idx = t - depth * (1 + np.sin(2 * np.pi * rate * t))
        x = np.stack([np.interp(idx, t, x[:, 0]), np.interp(idx, t, x[:, 1])], 1)
    # gentle sidechain from the kicks, glue saturation, room
    if kickt:
        sc = np.ones(n)
        for kt in kickt:
            i = int(kt * SR); m = min(n - i, int(0.22 * SR))
            if i >= 0 and m > 0: sc[i:i + m] = np.minimum(sc[i:i + m], 1 - 0.28 * np.exp(-np.arange(m) / (0.07 * SR)))
        if style != 'ambient': x = x * sc[:, None]
    irn = int(1.4 * SR); ir = rng.standard_normal((irn, 2)) * np.exp(-np.arange(irn) / (0.38 * SR))[:, None]
    ir = _lp(ir, 5000); ir /= np.abs(ir).sum(0) / 6
    wet = np.stack([signal.fftconvolve(x[:, c], ir[:, c])[:n] for c in range(2)], 1)
    x = np.tanh(1.2 * (x + (0.22 if style != 'ambient' else 0.4) * wet))
    x /= np.abs(x).max() + 1e-9
    params = dict(style=style, seed=int(seed), bpm=bpm, key=['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B'][key],
                  family=fam, progression=[f'{d}:{q}' for d, q in prog], swing=round(swing, 3), drop=round(drop, 3), melody=bool(use_mel))
    return x.astype(np.float32), params
