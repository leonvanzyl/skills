"""Every sound the edit adds, synthesized in code (numpy/scipy), levelled against the programme voice, and laid out as
separate clips for three new audio tracks - Resolve's API cannot set clip volume, so each level is baked into its file.

  SFX    one clip per visible event (beats' "sfx", graphics' sfx from build_gfx, overlay events): pop / click / chime /
         whoosh (loudest moment exactly on the whip midpoint) / key ticks (a typing run becomes one clip).
         Which ones play in the body: sfxlib.select with LONGFORM_RULES (plan "sfx_rules" overrides) - only the first
         ding / scribble of a zoom or graphic, at most 5 pops per animation, accents 15 s apart, scribbles 4 s apart,
         at most 7 sounds in any 15 s; the hook, CTA cards and keyword pops always play.
         How loud: by LOUDNESS against the RAW voice's speaking loudness (sfxlib.LONGFORM_TARGET, plan "sfx_levels"),
         e.g. chime -10, ding -11, pop -12, scribble -14 (hiss tamed), click and keys -16 LU, exactly as master.py
         plays them (it sets the user's processed voice back to that reference; "sfx_bus_lift" 0) - the hook +3 LU
         ("sfx_hook_bonus"), music masks it.
         (Leon's A/B/C test, 2026-10-16: peak-based levels made bells and scribbles the loudest sounds in the edit.)
  Music  the HOOK ONLY: a seeded track in the plan's style and mood, filtered intro, beat drops at plan.music.drop,
         about 18 LU under the hook's voice, ducked ~5 dB under speech, fading out over plan.music.fade_out seconds
         from hook_end. Nothing after that.
  Riser  2.6 s low swell whose audible end lands exactly on hook_end (the hook -> content join), -12 dB.

Writes media/sfx/*.wav, media/music_hook.wav, media/riser.wav, audio_clips.json (what goes where, for place.py) and
mix_preview.wav (voice + everything, for checking the balance by ear), and prints the levels.
usage: python scripts/audio.py [--tag v2]   (an edit writes new names - sfx_v2/, music_hook_v2.wav, riser_v2.wav -
       because Resolve holds the imported files open)"""
import json, os, sys, glob, zlib
import numpy as np, soundfile as sf, pyloudnorm as pyln
from scipy import signal
sys.path.insert(0, 'scripts'); import config as C, media as M, music as MUS, sfxlib

TAG = ('_' + sys.argv[sys.argv.index('--tag') + 1]) if '--tag' in sys.argv else ''
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


RISER_DB = -12                    # the riser's peak against the voice's peak (the hook, under music)
HOOK_END = float(PL.get('hook_end') or 0.0)
RULES = dict(sfxlib.LONGFORM_RULES, **PL.get('sfx_rules', {}))
TARGET = dict(sfxlib.LONGFORM_TARGET, **PL.get('sfx_levels', {}))
BUS_LIFT = float(PL.get('sfx_bus_lift', 0.0))          # 0: master.py mixes outside Resolve's bus (it was 4.5 when a bus compressor lifted the SFX)
HOOK_BONUS = float(PL.get('sfx_hook_bonus', 3.0))
VSPEECH = sfxlib.speech_loudness(voice)


def level(s, typ, t):
    """the gain that puts sound s at its loudness target (LU under the voice as heard after the bus)"""
    tgt = TARGET.get(typ, -14) + (HOOK_BONUS if t < HOOK_END else 0.0) - BUS_LIFT
    return sfxlib.gain_for(s, tgt, VSPEECH), round(tgt + BUS_LIFT, 1)
LIB_CAT = {'click': 'click', 'pop': 'pop', 'chime': 'chime', 'whoosh': 'whoosh', 'whoosh_soft': 'whoosh',
           'highlight': 'highlight', 'ding': 'ding', 'sting': 'sting', 'key': 'typing', 'tick': 'typing', 'riser': 'riser'}
LIB = sfxlib.Library(prefer=PL.get('sfx_prefer'))
USE_LIB = bool(LIB.cats) and PL.get('sfx_library', True)


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
    ids = {b['id'] for b in PL['beats']}          # a beat removed from the plan leaves its old event files behind
    gfx = json.load(open('gfx/sfx_events.json')) if os.path.exists('gfx/sfx_events.json') else {}
    for bid, es in gfx.items():
        if bid not in ids: continue
        b = M.beat(bid)
        ev += [dict(t=b['t0'] + e['t'], type=e['type'], src=bid) for e in es]
    for f in glob.glob('events/*.json'):          # overlays (CTA cards, keyword pops): rare and deliberate, always play
        bid = os.path.splitext(os.path.basename(f))[0]
        if bid not in ids: continue
        ev += [dict(e, src=bid, keep=True) for e in json.load(open(f))]
    if PL.get('auto_sfx', True): ev += auto_events()
    ev.sort(key=lambda e: e['t'])
    # an optional sound never stacks on another event (a highlight right on a card's pop is just noise)
    main_t = [e['t'] for e in ev if e['type'] not in ('highlight', 'ding', 'whoosh_soft', 'key', 'tick')]
    out = []
    for e in ev:
        if e['type'] in ('highlight', 'ding') and any(abs(e['t'] - t) < 0.15 for t in main_t): continue
        out.append(e)
    return out


def gfx_cfg(bid):
    import re
    try:
        html = open(f'gfx/{bid}.html', encoding='utf-8').read()
        m = re.search(r'window\.CFG=(\{.*?\});</script>', html, re.S)
        return json.loads(m.group(1)) if m else {}
    except (OSError, ValueError):
        return {}


def auto_events():
    """the sound design the plan implies: a highlight swish on every band/underline mark and every highlight-band reveal
    in a graphic, a soft ding on a box mark (not when marks come thick and fast), a soft whoosh peaking on the cut into
    a full-visual graphic (not between two graphics of one continuous world), and a sting on the hook's end"""
    ev, last = [], -9.0
    beats = sorted([b for b in PL['beats'] if 't0' in b], key=lambda b: b['t0'])
    for b in beats:
        if b['kind'] == 'zoom':
            for mk in sorted(b.get('marks', []), key=lambda m: m['t']):
                typ = mk.get('type', 'box'); t = b['t0'] + mk['t']
                if typ == 'spot' or t - last < 0.7: continue
                ev.append(dict(t=round(t, 3), type='highlight' if typ in ('band', 'underline') else 'ding', src=b['id'])); last = t
    vis = [b for b in beats if b['kind'] in ('zoom', 'gfx', 'fix')]
    for b in beats:
        if b['kind'] != 'gfx': continue
        for r in gfx_cfg(b['id']).get('reveals', []):
            if r.get('type') == 'scaleX': ev.append(dict(t=round(b['t0'] + r['t'], 3), type='highlight', src=b['id']))
        prev = next((v for v in vis if abs(v['t1'] - b['t0']) < 1 / 120 and v is not b), None)
        if not (prev and prev['kind'] == 'gfx'): ev.append(dict(t=b['t0'], type='whoosh_soft', src=b['id']))
    if PL.get('hook_end'): ev.append(dict(t=PL['hook_end'], type='sting', src='hook', keep=True))
    return ev


def main():
    os.makedirs(f'{C.MEDIA}/sfx{TAG}', exist_ok=True)
    clips = []; sfx_mix = np.zeros((N, 2), np.float32)
    ev_all = collect_events()
    ev, dropped = sfxlib.select(ev_all, RULES, start=HOOK_END)
    lib = {}
    wv = 0
    k = 0
    while k < len(ev):
        e = ev[k]; typ = e['type']
        lib_ok = USE_LIB and LIB.has(LIB_CAT.get(typ, typ), short=0.35 if typ in ('key', 'tick') else None)
        hook = '_hook' if e['t'] < HOOK_END else ''          # the hook's level differs, so its files are separate
        if typ in ('key', 'tick'):          # a typing run -> one clip
            run = [e]
            while k + 1 < len(ev) and ev[k + 1]['type'] in ('key', 'tick') and ev[k + 1]['t'] - run[-1]['t'] < 0.35:
                k += 1; run.append(ev[k])
            t0 = run[0]['t']; n = int((run[-1]['t'] - t0 + 0.4) * SR); s = np.zeros((n, 2))
            for j, r in enumerate(run):
                kk = LIB.get('typing', short=0.35)[0] if lib_ok else np.repeat(key(j)[:, None], 2, 1)
                i0 = int((r['t'] - t0) * SR); m = min(len(kk), n - i0); s[i0:i0 + m] += kk[:m] * (0.8 + 0.2 * ((j * 7) % 3) / 2)
            name = f"typing_{e['src']}_{len(clips):03d}.wav"; i0 = int(round(t0 * SR))
        elif lib_ok:                        # a recorded sample from the library; whooshes land their peak on the cut
            x, pk, stem = LIB.get(LIB_CAT.get(typ, typ))
            s = x; name = f'{typ}__{stem}{hook}.wav'
            i0 = int(round(e['t'] * SR)) - pk                    # pk = 0 for onset-aligned sounds
        elif typ in ('highlight', 'ding', 'sting', 'whoosh_soft'):     # no library: synthesized stand-ins
            s, mid = (whoosh(wv) if typ in ('whoosh_soft', 'highlight') else (chime(), 0)); wv += 1
            name = f'{typ}_{wv % 4}{hook}.wav'; i0 = int(round(e['t'] * SR)) - mid
        elif typ == 'whoosh':
            s, mid = whoosh(wv); wv += 1
            name = f'whoosh_{wv % 4}{hook}.wav'; i0 = int(round(e['t'] * SR)) - mid
        else:
            s = {'click': click, 'pop': pop, 'chime': chime}.get(typ, pop)()
            name = f'{typ}{hook}.wav'; i0 = int(round(e['t'] * SR))
        if typ == 'highlight': s = sfxlib.tame(s)            # the marker scribble's hiss off
        g, lu = level(s, typ, e['t']); s = s * g
        path = f'{C.MEDIA}/sfx{TAG}/{name}'
        if name not in lib: lib[name] = write(path, s)
        cut = max(0, -i0); i0 = max(0, i0)                  # a sound that would start before 0 is trimmed
        n = len(s) - cut; m = min(n, N - i0)
        if m > 0:
            seg = np.asarray(s[cut:cut + m], np.float32)
            sfx_mix[i0:i0 + m] += seg if seg.ndim == 2 else seg[:, None]
            clips.append(dict(track='sfx', file=os.path.abspath(path), type=typ, src=e['src'], t=round(e['t'], 3), lu=lu,
                              record_frame=int(round(i0 / SR * FPS)), start_frame=int(round(cut / SR * FPS)),
                              end_frame=int(round(cut / SR * FPS)) + frames(m)))
        k += 1
    sfx_audit = sfxlib.audit(ev, N / SR, start=HOOK_END)

    # ---- hook music + riser
    hook_end = PL['hook_end']; mp = PL.get('music', {})
    ris_mix = np.zeros((N, 2), np.float32); mus_mix = np.zeros((N, 2), np.float32)
    if USE_LIB and LIB.has('riser') and PL.get('riser_from_library', True):
        x, pk, stem = LIB.get('riser'); pk = pk or int(np.argmax(np.abs(x).mean(1)))
        rs = x[:pk + int(0.012 * SR)].copy()                                           # cut right after its peak
        rs[-int(0.012 * SR):] *= np.linspace(1, 0, int(0.012 * SR))[:, None]
        rs *= VPEAK * 10 ** (RISER_DB / 20)
    else:
        rs = riser(2.6) * VPEAK * 10 ** (RISER_DB / 20)
    i1 = int(round(hook_end * SR)); i0 = i1 - len(rs); cut = max(0, -i0)
    write(f'{C.MEDIA}/riser{TAG}.wav', rs)
    ris_mix[max(0, i0):i1] += rs[cut:] if rs.ndim == 2 else rs[cut:, None]
    clips.append(dict(track='riser', file=os.path.abspath(f'{C.MEDIA}/riser{TAG}.wav'), record_frame=int(round(max(0, i0) / SR * FPS)),
                      start_frame=int(round(cut / SR * FPS)), end_frame=frames(len(rs))))
    fade_out = float(mp.get('fade_out', 2.5)); dur = hook_end + fade_out
    KEYS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']
    key_ = mp.get('key'); key_ = KEYS.index(key_) if isinstance(key_, str) and key_ in KEYS else key_
    seed = int(mp.get('seed', zlib.crc32((str(P.get('timeline')) + '|hook').encode()) % 1000003))
    drop = mp.get('drop')
    if drop is None:                        # default: the end of the hook's first sentence
        drop = next((s['e'] for s in P['sentences'] if s['e'] > 2.0), 0.0)
    if mp.get('file'):                      # a generated / licensed track instead of the synthesized bed
        x, sr = sf.read(mp['file'], dtype='float32', always_2d=True)
        if sr != SR:
            from scipy.signal import resample_poly
            x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
        if x.shape[1] == 1: x = np.repeat(x, 2, 1)
        off = int(float(mp.get('file_offset', 0.0)) * SR)
        mus = x[off:off + int(dur * SR), :2]
        if len(mus) < int(dur * SR): mus = np.pad(mus, ((0, int(dur * SR) - len(mus)), (0, 0)))
        params = dict(style='file', family=os.path.basename(mp['file']), key='-', bpm=float(mp.get('bpm') or 0), seed=mp.get('seed', '-'),
                      file=mp['file'], file_offset=float(mp.get('file_offset', 0.0)))
    else:
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
    if mp.get('off'):                       # no hook music (plan music.off): the riser and the sting stay
        params['style'] = 'off'
    else:
        write(f'{C.MEDIA}/music_hook{TAG}.wav', mus)
        mus_mix[:len(mus)] += mus.astype(np.float32)
        clips.append(dict(track='music', file=os.path.abspath(f'{C.MEDIA}/music_hook{TAG}.wav'), record_frame=0, start_frame=0, end_frame=frames(len(mus))))
    params.update(level_lufs=round(target, 1), hook_voice_lufs=round(hook_lufs, 1), fade_out=fade_out, hook_end=hook_end)
    sfx_info = dict(rules=RULES, levels_lu=TARGET, bus_lift_db=BUS_LIFT, hook_bonus_lu=HOOK_BONUS,
                    voice_speech_lufs=round(VSPEECH, 1), body=sfx_audit, events=len(ev_all), dropped=len(dropped),
                    dropped_why=dict(__import__('collections').Counter(d['why'].split(' of ')[0] for d in dropped).most_common()))
    json.dump(dict(clips=clips, music=params, voice_peak_db=round(20 * np.log10(VPEAK), 2), sfx=sfx_info),
              open('audio_clips.json', 'w'), indent=1)

    mix = voice + sfx_mix + mus_mix + ris_mix
    sf.write('mix_preview.wav', mix, SR, subtype='PCM_24')
    tp = 20 * np.log10(np.abs(mix).max() + 1e-9)
    print(f"voice: {P['voice']['lufs']:.1f} LUFS (hook {hook_lufs:.1f}), robust peak {20 * np.log10(VPEAK):.1f} dBFS")
    print(f"music: {params['style']} {params.get('family')} {params['key']} {params['bpm']:.0f} bpm seed {params['seed']}, drop {drop:.2f}s, "
          f"{target:.1f} LUFS, fades out {hook_end:.2f} -> {hook_end + fade_out:.2f}s")
    a = sfx_audit
    print(f"sfx in the body: {a['sounds']} sounds, {a['per_min']}/min (reference ~10.5), accents {a['accents']} "
          f"(closest {a['closest_accents_s']} s), busiest 15 s: {a['busiest_15s']}, same family within 8 s: "
          f"{a['same_family_within_8s']} | {len(dropped)} of {len(ev_all)} events not played: {sfx_info['dropped_why']}")
    print(f"sfx levels: by loudness vs the voice ({VSPEECH:.1f} LUFS speaking), bus lift {BUS_LIFT} dB, hook +{HOOK_BONUS} LU: "
          + ', '.join(f'{t} {v}' for t, v in sorted(TARGET.items(), key=lambda kv: -kv[1])))
    print(f"riser ends at {hook_end:.3f}s | {sum(1 for c in clips if c['track'] == 'sfx')} sfx clips from {len(ev)} events | "
          f"{'SFX library ' + LIB.dir + ' (' + ', '.join(f'{c} {len(v)}' for c, v in sorted(LIB.cats.items())) + ')' if USE_LIB else 'synthesized SFX (no library)'}")
    print(f"mix preview: {meter.integrated_loudness(mix):.1f} LUFS, peak {tp:.1f} dBFS -> mix_preview.wav (listen to the hook)")


if __name__ == '__main__':
    main()
