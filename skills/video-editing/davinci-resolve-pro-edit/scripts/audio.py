"""Every sound the edit adds, synthesized in code (numpy/scipy), levelled against the programme voice, and laid out as
separate clips for three new audio tracks - Resolve's API cannot set clip volume, so each level is baked into its file.

  SFX    one clip per visible event (beats' "sfx", graphics' sfx from build_gfx, overlay events): pop / click / chime /
         whoosh (loudest moment exactly on the whip midpoint) / key ticks (a typing run becomes one clip).
         Peaks against the voice's peak: click, pop, chime -10 dB; whoosh -9 dB; keys and ticks -16 dB.
  Music  the HOOK ONLY: a seeded track in the plan's style and mood, filtered intro, beat drops at plan.music.drop,
         about 18 LU under the hook's voice, ducked ~5 dB under speech, fading out over plan.music.fade_out seconds
         from hook_end. Nothing after that.
  Riser  2.6 s low swell whose audible end lands exactly on hook_end (the hook -> content join), -12 dB.

Writes media/sfx/*.wav, media/music_hook.wav, media/riser.wav, audio_clips.json (what goes where, for place.py) and
mix_preview.wav (voice + everything, for checking the balance by ear), and prints the levels.
usage: python scripts/audio.py"""
import json, os, sys, glob, zlib
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy import signal
sys.path.insert(0, 'scripts'); import config as C, media as M, music as MUS

SR = 48000
rng = np.random.default_rng(7)
P = M.program(); PL = M.plan()
FPS = C.FPS
voice, _ = sf.read('voice48.wav', dtype='float32', always_2d=True)
N = len(voice)
# robust voice peak: the 99th percentile of 100 ms window peaks (one shout or laugh must not set every level)
win = SR // 10; pk = np.abs(voice.mean(1))[:len(voice) // win * win].reshape(-1, win).max(1)
VPEAK = float(np.percentile(pk[pk > 1e-4], 99))
meter = pyln.Meter(SR)


def env_exp(n, tau): return np.exp(-np.arange(n) / (tau * SR))
def nrm(x): m = np.abs(x).max(); return x / m if m > 0 else x
def lp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'low'); return signal.lfilter(b, a, x)
def hp(x, fc, o=2): b, a = signal.butter(o, fc / (SR / 2), 'high'); return signal.lfilter(b, a, x)
def bp(x, f0, f1, o=2): b, a = signal.butter(o, [f0 / (SR / 2), f1 / (SR / 2)], 'band'); return signal.lfilter(b, a, x)


# ---------------- sound designs (same as the shorts skill: clean, modern, premium, never cartoony) ----------------
def click():
    n = int(0.09 * SR); t = np.arange(n) / SR
    f = 1250 * np.exp(-t / 0.018) + 620
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.016)
    s += 0.35 * np.sin(2 * np.pi * np.cumsum(1.5 * f) / SR) * env_exp(n, 0.008)
    s[:24] *= np.linspace(0, 1, 24)
    return nrm(lp(s, 5000))


def key(i):
    n = int(0.05 * SR); t = np.arange(n) / SR
    s = bp(rng.standard_normal(n), 1800 + 300 * (i % 3), 5200) * env_exp(n, 0.004)
    s += 0.6 * np.sin(2 * np.pi * (170 + 15 * (i % 4)) * t) * env_exp(n, 0.010)
    s[:8] *= np.linspace(0, 1, 8)
    return nrm(s)


def pop():
    n = int(0.22 * SR); t = np.arange(n) / SR
    f = 150 * np.exp(-t / 0.04) + 62
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(n, 0.055)
    s += 0.25 * lp(rng.standard_normal(n), 900) * env_exp(n, 0.012)
    s[:48] *= np.linspace(0, 1, 48)
    return nrm(lp(s, 1800))


def chime():
    n = int(1.1 * SR); out = np.zeros(n)
    for k, (f, t0) in enumerate([(1318.5, 0.0), (1760.0, 0.13)]):
        i0 = int(t0 * SR); m = n - i0; t = np.arange(m) / SR
        tone = np.sin(2 * np.pi * f * t) + 0.28 * np.sin(2 * np.pi * 2.01 * f * t) * env_exp(m, 0.12) + 0.12 * np.sin(2 * np.pi * 3.02 * f * t) * env_exp(m, 0.06)
        e = env_exp(m, 0.35); e[:96] *= np.linspace(0, 1, 96)
        out[i0:] += tone * e * (0.85 if k == 0 else 1.0)
    return nrm(out)


def whoosh(variant, dur_out=0.45, dur_in=0.6):
    pre, post = dur_out + 0.12, dur_in + 0.25
    n = int((pre + post) * SR); t = np.arange(n) / SR; tm = pre
    nz = rng.standard_normal(n)
    lo, hi, q = [(180, 700, 1.2), (140, 560, 1.4), (220, 820, 1.1), (160, 640, 1.3)][variant % 4]
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
    nz = rng.standard_normal(n); w = p ** 2
    air = (1 - w) * bp(nz, 180, 500) + w * bp(nz, 900, 2600) * 0.7
    s = (0.8 * lp(tone, 400) + 0.45 * air) * p ** 2.4
    s[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))   # audible end exactly on the join
    return nrm(s)


LEVEL = {'click': -10, 'pop': -10, 'chime': -10, 'whoosh': -9, 'key': -16, 'tick': -16}


def write(path, x):
    x = np.asarray(x, np.float32)
    if x.ndim == 1: x = np.stack([x, x], 1)
    spf = SR // FPS                                          # pad to whole frames, so every frame range exists in Resolve
    if len(x) % spf: x = np.pad(x, ((0, spf - len(x) % spf), (0, 0)))
    sf.write(path, x, SR, subtype='PCM_24')
    return path


def frames(nsamples):
    return int(np.ceil(nsamples / SR * FPS))


# ---------------- events ----------------
def collect_events():
    ev = []
    for b in PL['beats']:
        for e in b.get('sfx', []):
            ev.append(dict(t=b['t0'] + e['t'], type=e['type'], src=b['id']))
    gfx = json.load(open('gfx/sfx_events.json')) if os.path.exists('gfx/sfx_events.json') else {}
    for bid, es in gfx.items():
        b = M.beat(bid)
        ev += [dict(t=b['t0'] + e['t'], type=e['type'], src=bid) for e in es]
    for f in glob.glob('events/*.json'):
        bid = os.path.splitext(os.path.basename(f))[0]
        ev += [dict(e, src=bid) for e in json.load(open(f))]
    return sorted(ev, key=lambda e: e['t'])


def main():
    os.makedirs(f'{C.MEDIA}/sfx', exist_ok=True)
    clips = []; sfx_mix = np.zeros((N, 2), np.float32)
    ev = collect_events()
    lib = {}
    wv = 0
    k = 0
    while k < len(ev):
        e = ev[k]; typ = e['type']; g = VPEAK * 10 ** (LEVEL[typ] / 20)
        if typ in ('key', 'tick'):          # a typing run -> one clip
            run = [e]
            while k + 1 < len(ev) and ev[k + 1]['type'] in ('key', 'tick') and ev[k + 1]['t'] - run[-1]['t'] < 0.35:
                k += 1; run.append(ev[k])
            t0 = run[0]['t']; n = int((run[-1]['t'] - t0 + 0.1) * SR); s = np.zeros(n)
            for j, r in enumerate(run):
                kk = key(j); i0 = int((r['t'] - t0) * SR); m = min(len(kk), n - i0); s[i0:i0 + m] += kk[:m]
            s = s / (np.abs(s).max() + 1e-9) * g
            name = f"typing_{e['src']}_{len(clips):03d}.wav"; i0 = int(round(t0 * SR))
        elif typ == 'whoosh':
            s, mid = whoosh(wv); wv += 1; s = s * g
            name = f'whoosh_{wv % 4}.wav'; i0 = int(round(e['t'] * SR)) - mid
        else:
            s = {'click': click, 'pop': pop, 'chime': chime}[typ]() * g
            name = f'{typ}.wav'; i0 = int(round(e['t'] * SR))
        path = f'{C.MEDIA}/sfx/{name}'
        if name not in lib: lib[name] = write(path, s)
        cut = max(0, -i0); i0 = max(0, i0)                  # a sound that would start before 0 is trimmed
        n = len(s) - cut; m = min(n, N - i0)
        if m > 0:
            sfx_mix[i0:i0 + m] += np.asarray(s[cut:cut + m], np.float32)[:, None]
            clips.append(dict(track='sfx', file=os.path.abspath(path), type=typ, src=e['src'], t=round(e['t'], 3),
                              record_frame=int(round(i0 / SR * FPS)), start_frame=int(round(cut / SR * FPS)),
                              end_frame=int(round(cut / SR * FPS)) + frames(m)))
        k += 1

    # ---- hook music + riser
    hook_end = PL['hook_end']; mp = PL.get('music', {})
    ris_mix = np.zeros((N, 2), np.float32); mus_mix = np.zeros((N, 2), np.float32)
    rs = riser(2.6) * VPEAK * 10 ** (-12 / 20)
    i1 = int(round(hook_end * SR)); i0 = i1 - len(rs); cut = max(0, -i0)
    write(f'{C.MEDIA}/riser.wav', rs)
    ris_mix[max(0, i0):i1] += rs[cut:, None]
    clips.append(dict(track='riser', file=os.path.abspath(f'{C.MEDIA}/riser.wav'), record_frame=int(round(max(0, i0) / SR * FPS)),
                      start_frame=int(round(cut / SR * FPS)), end_frame=frames(len(rs))))
    fade_out = float(mp.get('fade_out', 2.5)); dur = hook_end + fade_out
    KEYS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    key_ = mp.get('key'); key_ = KEYS.index(key_) if isinstance(key_, str) and key_ in KEYS else key_
    seed = int(mp.get('seed', zlib.crc32((str(P.get('timeline')) + '|hook').encode()) % 1000003))
    drop = mp.get('drop')
    if drop is None:                        # default: the end of the hook's first sentence
        drop = next((s['e'] for s in P['sentences'] if s['e'] > 2.0), 0.0)
    mus, params = MUS.render(mp.get('style', 'lofi'), seed, dur, drop=drop, bpm=mp.get('bpm'), key=key_, mood=mp.get('mood'))
    mus = mus.astype(np.float64)[:int(dur * SR)]
    fi = int(0.8 * SR); mus[:fi] *= np.linspace(0, 1, fi)[:, None]
    fo = int(fade_out * SR); mus[-fo:] *= (np.cos(np.linspace(0, np.pi / 2, fo)) ** 2)[:, None]   # gone by hook_end + fade_out
    hv = voice[:int(hook_end * SR)]
    hook_lufs = float(meter.integrated_loudness(hv)) if len(hv) > SR else P['voice']['lufs']
    target = hook_lufs - float(mp.get('under_voice_lu', 18))
    mus *= 10 ** ((target - meter.integrated_loudness(mus[:int(hook_end * SR)])) / 20)
    venv = np.abs(voice[:len(mus)].mean(1)); venv = signal.filtfilt(*signal.butter(1, 6 / (SR / 2)), venv)
    duck = 1 - 0.45 * np.clip(venv / (np.percentile(venv, 90) + 1e-9), 0, 1)
    mus *= duck[:, None]
    write(f'{C.MEDIA}/music_hook.wav', mus)
    mus_mix[:len(mus)] += mus.astype(np.float32)
    clips.append(dict(track='music', file=os.path.abspath(f'{C.MEDIA}/music_hook.wav'), record_frame=0, start_frame=0, end_frame=frames(len(mus))))
    params.update(level_lufs=round(target, 1), hook_voice_lufs=round(hook_lufs, 1), fade_out=fade_out, hook_end=hook_end)
    json.dump(dict(clips=clips, music=params, voice_peak_db=round(20 * np.log10(VPEAK), 2)), open('audio_clips.json', 'w'), indent=1)

    mix = voice + sfx_mix + mus_mix + ris_mix
    sf.write('mix_preview.wav', mix, SR, subtype='PCM_24')
    tp = 20 * np.log10(np.abs(mix).max() + 1e-9)
    print(f"voice: {P['voice']['lufs']:.1f} LUFS (hook {hook_lufs:.1f}), robust peak {20 * np.log10(VPEAK):.1f} dBFS")
    print(f"music: {params['style']} {params.get('family')} {params['key']} {params['bpm']:.0f} bpm seed {params['seed']}, drop {drop:.2f}s, "
          f"{target:.1f} LUFS, fades out {hook_end:.2f} -> {hook_end + fade_out:.2f}s")
    print(f"riser ends at {hook_end:.3f}s | {sum(1 for c in clips if c['track'] == 'sfx')} sfx clips from {len(ev)} events")
    print(f"mix preview: {meter.integrated_loudness(mix):.1f} LUFS, peak {tp:.1f} dBFS -> mix_preview.wav (listen to the hook)")


if __name__ == '__main__':
    main()
