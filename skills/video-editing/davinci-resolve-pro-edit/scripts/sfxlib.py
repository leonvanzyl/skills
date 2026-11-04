"""The royalty-free SFX library built by sfx_library.py (the skill's own assets/sfx, or $PRO_EDIT_SFX_DIR):
samples by category, rotated so the same sound never plays twice in a row, as 48 kHz stereo float arrays peak-normalised
to 1, with the sample index of each one's loudest moment (whooshes land that peak exactly on the cut).
audio.py uses it when it exists and falls back to its synthesized sounds otherwise."""
import os, json
import numpy as np, soundfile as sf
from scipy.signal import resample_poly

SR = 48000


def root():
    """$PRO_EDIT_SFX_DIR, else the skill's assets/sfx: found from project.json's skill_dir (a work dir, setup.sh writes
    it), from this script's own folder (run inside the skill), or the usual install paths. The first one with a
    manifest wins; with none built yet, the first skill folder found (where `sfx_library.py build` puts it)."""
    env = os.environ.get('PRO_EDIT_SFX_DIR') or os.environ.get('PRO_EDIT_SFX')
    if env: return env
    skills = []
    try: skills.append(json.load(open('project.json', encoding='utf-8'))['skill_dir'])
    except Exception: pass
    skills.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
    skills += [os.path.join(os.path.expanduser('~'), d, 'skills', n) for n in ('davinci-resolve-pro-edit', 'create-video-shorts')
               for d in ('.claude', '.agents')]                 # both video skills ship the same library
    skills = [os.path.normpath(d) for d in skills if os.path.exists(os.path.join(d, 'SKILL.md'))]
    for d in skills:
        if os.path.exists(os.path.join(d, 'assets', 'sfx', 'manifest.json')): return os.path.join(d, 'assets', 'sfx')
    return os.path.join(skills[0], 'assets', 'sfx') if skills else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'assets', 'sfx')


def _entries(man):
    """accepts {'files': [...]}, a plain list, or {category: [...]}"""
    if isinstance(man, dict) and isinstance(man.get('files'), list): return man['files']
    if isinstance(man, list): return man
    if isinstance(man, dict):
        out = []
        for cat, v in man.items():
            if isinstance(v, list): out += [dict(e, category=e.get('category', cat)) for e in v if isinstance(e, dict)]
        return out
    return []


class Library:
    def __init__(self, path=None, prefer=None):
        self.dir = path or root(); self.cats = {}; self.count = {}; self.cache = {}; self.last = {}
        self.prefer = prefer or {}                     # {category: [file stems in order of preference]} from the plan
        mf = os.path.join(self.dir, 'manifest.json')
        if not os.path.exists(mf): return
        for e in _entries(json.load(open(mf, encoding='utf-8'))):
            f = e.get('file') or e.get('path')
            if not f: continue
            p = f if os.path.isabs(f) else os.path.join(self.dir, f)
            if not os.path.exists(p): continue
            self.cats.setdefault(e.get('category', os.path.basename(os.path.dirname(p))), []).append(
                dict(path=p, peak=float(e.get('peak_time', 0.0) or 0.0), dur=float(e.get('duration', 0.0) or 0.0),
                     pick=bool(e.get('pick')), align=e.get('align', 'onset')))
        for c, lst in self.cats.items():
            pref = self.prefer.get(c)
            if pref:                                    # preferred files first, the rest after
                stem = lambda d: os.path.splitext(os.path.basename(d['path']))[0]
                lst.sort(key=lambda d: pref.index(stem(d)) if stem(d) in pref else len(pref))

    def has(self, cat, short=None):
        return bool(self.pick_list(cat, short))

    def pick_list(self, cat, short=None):
        lst = self.cats.get(cat, [])
        if short is not None: return [d for d in lst if d['dur'] and d['dur'] <= short]   # e.g. all single key ticks
        if cat in self.prefer: return lst                                                # the plan's order, all files
        picks = [d for d in lst if d['pick']]
        return picks or lst                                                              # the library's recommended picks

    def load(self, p):
        if p not in self.cache:
            x, sr = sf.read(p, dtype='float32', always_2d=True)
            if sr != SR: x = resample_poly(x, SR, sr, axis=0).astype(np.float32)
            if x.shape[1] == 1: x = np.repeat(x, 2, 1)
            x = x[:, :2]; m = np.abs(x).max()
            self.cache[p] = x / m if m > 0 else x
        return self.cache[p]

    def get(self, cat, short=None, top=None):
        """(stereo samples, index of the loudest moment, name) - rotates over the category's first `top` files"""
        lst = self.pick_list(cat, short)
        if not lst: return None
        if top: lst = lst[:top]
        k = self.count.get(cat, 0); self.count[cat] = k + 1
        d = lst[k % len(lst)]
        if len(lst) > 1 and self.last.get(cat) == d['path']: d = lst[(k + 1) % len(lst)]
        self.last[cat] = d['path']
        x = self.load(d['path'])
        pk = int(d['peak'] * SR) if d['peak'] else int(np.argmax(np.abs(x).mean(1)))
        # the sample index to land on the event: the onset, or the loudest moment when the manifest says align=peak
        return x, (pk if d['align'] == 'peak' else 0), os.path.splitext(os.path.basename(d['path']))[0]


# ---------------- how loud, and how often (both skills) ----------------
# Tuned on Leon's A/B/C test of the Harness Engineering edit (2026-10-16), after a viewer wrote "the new sound effects
# get annoying fast - ding, scribble, ding, ding, ding". Variant C was his pick: "not too distracting, not too dense".
# Levels go by LOUDNESS (the loudest 400 ms, K-weighted like LUFS) against the voice's speaking loudness, never by peak:
# at the same peak a bell or a marker scribble sounds 6-10 dB louder than a click. Targets are LU below the voice as the
# viewer hears it (long-form: master.py mixes the files against the voice outside Resolve's bus, so these are final).
LONGFORM_TARGET = {'sting': -10, 'chime': -10, 'ding': -11, 'notification': -12, 'whoosh': -12, 'whoosh_soft': -11,
                   'pop': -12, 'highlight': -14, 'glitch': -14, 'click': -16, 'key': -16, 'tick': -16}
SHORTS_TARGET = {'whoosh': -12, 'chime': -12, 'ding': -12, 'notification': -12, 'pop': -14, 'highlight': -14,
                 'glitch': -14, 'sting': -16, 'click': -21, 'key': -27, 'tick': -27}   # the shorts' own levels, chimes evened out
# what a crowded moment keeps first (lower = more important)
PRIORITY = {'riser': 0, 'sting': 0, 'chime': 1, 'whoosh': 2, 'whoosh_soft': 2, 'click': 3, 'key': 3, 'tick': 3,
            'notification': 3, 'ding': 4, 'glitch': 5, 'highlight': 5, 'pop': 6}
FAMILY = {'chime': 'accent', 'ding': 'accent', 'sting': 'accent', 'whoosh_soft': 'whoosh', 'tick': 'key'}
# long-form body (variant C): bells and scribbles only where they mean something, every animation still audible
# exclude_types: never played, hook included. Leon (opencode-2.0, 2026-10-20): "The dings / bells / high pitches is a bit
# much. Swooshes, swipes, pops are fine." - box marks and success moments stay silent; a plan can bring them back
# with "sfx_rules": {"exclude_types": []}.
LONGFORM_RULES = dict(first_per_src=('ding', 'highlight'), pop_max=5, pop_gap=0.6,
                      family_gap={'accent': 15.0, 'highlight': 4.0}, min_sep=0.35, density=(7, 15.0),
                      exclude_types=('ding', 'chime'))
# shorts: music runs under them and the format is busier - a safety net only: the approved Harness Engineering shorts
# peaked at 10 sounds in 10 s with accents 11 s+ apart, so nothing they did is dropped
SHORTS_RULES = dict(first_per_src=(), pop_max=None, pop_gap=0.0, family_gap={'accent': 8.0}, min_sep=0.25, density=(10, 10.0))


def _kw(x):
    """the BS.1770 K-weighting (48 kHz)"""
    from scipy.signal import lfilter
    b1, a1 = [1.53512485958697, -2.69169618940638, 1.19839281085285], [1.0, -1.69065929318241, 0.73248077421585]
    b2, a2 = [1.0, -2.0, 1.0], [1.0, -1.99004745483398, 0.99007225036621]
    return lfilter(b2, a2, lfilter(b1, a1, x))


def _momentary(x, win=0.4):
    x = np.asarray(x, np.float64)
    y = _kw(x.mean(axis=1) if x.ndim > 1 else x) ** 2; n = int(win * SR); h = n // 4
    if len(y) < n: y = np.pad(y, (0, n - len(y)))
    cs = np.concatenate([[0.0], np.cumsum(y)]); a = cs[n::h]; b = cs[:-n:h][: len(a)]
    return -0.691 + 10 * np.log10((a[: len(b)] - b) / n + 1e-12)


def loudness(x):
    """a sound's loudness: its loudest 400 ms, K-weighted (LUFS-like)"""
    return float(_momentary(x).max())


def speech_loudness(voice):
    """the voice's typical loudness while speaking: the median 400 ms momentary loudness above -45 LUFS"""
    m = _momentary(voice)
    m = m[m > -45]
    return float(np.median(m)) if len(m) else -23.0


def gain_for(x, target_lu, v_speech):
    """the linear gain that puts sound x at target_lu below (negative) the voice's speaking loudness"""
    return 10 ** ((target_lu - (loudness(x) - v_speech)) / 20)


def tame(x, db=-4.0, fc=7000.0):
    """take the hiss off a bright sound (the marker scribble sits at ~10 kHz): about `db` above fc"""
    from scipy.signal import butter, sosfilt
    x = np.asarray(x, np.float64)
    return x - (1 - 10 ** (db / 20)) * sosfilt(butter(2, fc, 'highpass', fs=SR, output='sos'), x, axis=0)


def _units(ev):
    """events -> sounds: a typing run (key / tick strokes under 0.35 s apart) is one sound"""
    out, i = [], 0
    while i < len(ev):
        u = [ev[i]]
        if ev[i]['type'] in ('key', 'tick'):
            while i + 1 < len(ev) and ev[i + 1]['type'] in ('key', 'tick') and ev[i + 1]['t'] - u[-1]['t'] < 0.35:
                i += 1; u.append(ev[i])
        out.append(dict(t=u[0]['t'], type=u[0]['type'], src=u[0].get('src'), keep=any(e.get('keep') for e in u), ev=u))
        i += 1
    return out


def select(ev, rules, start=0.0):
    """Which sounds play. Events before `start` (the long-form hook, music under it) and events marked keep=True (CTA
    cards, the hook hit) always play. After that, in order:
      first_per_src  only the first ding / scribble of a zoom or graphic sounds
      pop_max/gap    an animation's pops: at most pop_max, pop_gap seconds apart
      family_gap     the same family not again within N s (accents = chime / ding / sting)
      min_sep        never two sounds on top of each other (the more important one stays)
      density        at most n sounds in any w seconds (the least important go first)
    Returns (kept events, dropped events with a 'why').
      exclude_types  types that never play, the hook and keep=True events included (first, before everything else)"""
    excl = set(rules.get('exclude_types', ()))
    gone = [dict(e, why='excluded type ' + e['type']) for e in ev if e['type'] in excl]
    ev = sorted([e for e in ev if e['type'] not in excl], key=lambda e: e['t'])
    units = _units(ev)
    fixed = [u for u in units if u['t'] < start or u['keep']]
    cand = [u for u in units if not (u['t'] < start or u['keep'])]
    dropped = list(gone)
    def drop(u, why):
        for e in u['ev']: dropped.append(dict(e, why=why))
    keep, firsts, pops = [], set(), {}
    for u in cand:                                            # per animation
        t, s = u['type'], u['src']
        if t in rules.get('first_per_src', ()):
            if (s, t) in firsts: drop(u, 'not the first ' + t + ' of ' + str(s)); continue
            firsts.add((s, t))
        if t == 'pop' and rules.get('pop_max'):
            p = pops.setdefault(s, [])
            if len(p) >= rules['pop_max'] or (p and u['t'] - p[-1] < rules.get('pop_gap', 0)): drop(u, 'pop budget of ' + str(s)); continue
            p.append(u['t'])
        keep.append(u)
    out, body_fixed = [], [u for u in fixed if u['t'] >= start]     # the hook is its own world
    for u in sorted(keep, key=lambda u: (PRIORITY.get(u['type'], 3), u['t'])):
        f = FAMILY.get(u['type'], u['type']); gap = rules.get('family_gap', {}).get(f, 0)
        if gap and any(FAMILY.get(o['type'], o['type']) == f and abs(o['t'] - u['t']) < gap for o in out + body_fixed):
            drop(u, f'{f} within {gap:g} s'); continue
        if any(abs(o['t'] - u['t']) < rules.get('min_sep', 0) for o in out + body_fixed):
            drop(u, 'on top of another sound'); continue
        out.append(u)
    n, w = rules.get('density', (99, 1.0))
    while True:
        allu = sorted(out + body_fixed, key=lambda u: u['t'])
        crowded = next(([o for o in allu if u['t'] <= o['t'] < u['t'] + w] for u in allu
                        if sum(1 for o in allu if u['t'] <= o['t'] < u['t'] + w) > n), None)
        movable = [o for o in (crowded or []) if o in out]
        if not movable: break
        worst = max(movable, key=lambda o: (PRIORITY.get(o['type'], 3), o['t']))
        out.remove(worst); drop(worst, f'more than {n} sounds in {w:g} s')
    kept = [e for u in sorted(out + fixed, key=lambda u: u['t']) for e in u['ev']]
    return kept, dropped


def audit(ev, duration, start=0.0):
    """the numbers to keep an eye on (and to put in the report): sounds per minute after `start`, by type, the closest
    accents, the busiest 15 s, and how often a family repeats within 8 s"""
    units = [u for u in _units(sorted(ev, key=lambda e: e['t'])) if u['t'] >= start]
    mins = max((duration - start) / 60, 1e-6)
    ts = [u['t'] for u in units]
    acc = [u['t'] for u in units if FAMILY.get(u['type'], u['type']) == 'accent']
    rep = sum(1 for a, b in zip(units, units[1:])
              if FAMILY.get(a['type'], a['type']) == FAMILY.get(b['type'], b['type']) and b['t'] - a['t'] < 8 and a['type'] != 'key')
    busiest = max((sum(1 for o in ts if t <= o < t + 15) for t in ts), default=0)
    from collections import Counter
    return dict(sounds=len(units), per_min=round(len(units) / mins, 1), by_type=dict(Counter(u['type'] for u in units).most_common()),
                accents=len(acc), closest_accents_s=round(min(np.diff(acc)), 1) if len(acc) > 1 else None,
                busiest_15s=busiest, same_family_within_8s=rep)
