"""Generate (or edit) thumbnails with Codex CLI's built-in image tool, several jobs in parallel.

A job is a JSON object: {"id": "v1a", "prompt": "<brief text or @file>", "refs": [["path", "what it is"], ...], "out": "out/v1a.png"}
Ref paths may start with ~ (e.g. the brand folder's avatar). A brief file can pull shared paragraphs from `_common.md` in
its own folder with {NAME} placeholders.
Usage:
  python gen.py jobs.json [--parallel 6] [--model gpt-6-astra]
Each job runs `codex exec` read-only with the refs attached in order, then copies the image Codex saved under
$CODEX_HOME/generated_images/<thread_id>/ to `out`. A log line per job goes to out/<id>.log.json.
"""
import argparse, concurrent.futures as cf, json, os, re, shutil, subprocess, threading, time

CODEX_HOME = os.environ.get('CODEX_HOME') or os.path.join(os.path.expanduser('~'), '.codex')

WRAP = """Use your built-in image generation tool exactly once to create the image described in the brief below.
Do not write code, run shell commands, browse, or ask questions. Pass the brief to the image tool faithfully and in full;
do not shorten, soften or "improve" it. After the image is generated, reply with one line: DONE.

{legend}
BRIEF
{brief}
"""


MAX_REFS = 5                                                    # Codex's image tool fails silently above this
STATE = os.path.join(CODEX_HOME, 'thumbnail_gen_model.txt')   # the last model that worked for this login
BAD = set()                                                     # models this login rejected during this run
LOCK = threading.Lock()


def candidate_models():
    """Models to try, best first: the one that last worked, then everything Codex lists, by priority.
    The cache can list models the login can't use (e.g. API-only on a ChatGPT login), so run() falls through."""
    order = []
    if os.path.exists(STATE):
        order.append(open(STATE).read().strip())
    try:
        d = json.load(open(os.path.join(CODEX_HOME, 'models_cache.json'), encoding='utf-8'))
        ms = sorted((m for m in d.get('models', []) if m.get('visibility') == 'list' and 'image' in m.get('input_modalities', [])),
                    key=lambda m: m.get('priority', 99))
        order += [m['slug'] for m in ms]
    except Exception:
        pass
    seen = set()
    return [m for m in order if m and not (m in seen or seen.add(m))] or [None]


def legend(refs):
    """Every ref description starts with an UPPERCASE LABEL and a colon (AVATAR:, LOGO: CLAUDE:, LAYOUT REFERENCE:, HOUSE STYLE:,
    UI:, THUMBNAIL:). Briefs name refs by label, never by position, so adding or dropping a logo can't shift them."""
    if not refs:
        return ''
    lines = ['ATTACHED REFERENCE IMAGES, in attachment order. The brief refers to each one by its LABEL (the words before the colon):']
    for i, (_, what) in enumerate(refs, 1):
        lines.append(f'{i}. {what}')
    return '\n'.join(lines) + '\n'


def view_data(jobs_file):
    """Video id -> thumbs.json record, from the run's research/thumbs.json (next to the jobs file)."""
    p = os.path.join(os.path.dirname(os.path.abspath(jobs_file)), 'research', 'thumbs.json')
    if not os.path.exists(p):
        return None
    return {t['id']: t for t in json.load(open(p, encoding='utf-8'))}


def check_references(job, views, min_views):
    """Every LAYOUT REFERENCE and HOUSE STYLE thumbnail must come from a video with at least min_views views."""
    bad = []
    for path, what in job.get('refs', []):
        label = what.split(':', 1)[0].strip().upper()
        if label not in ('LAYOUT REFERENCE', 'HOUSE STYLE'):
            continue
        vid = os.path.splitext(os.path.basename(path))[0][-11:]
        rec = (views or {}).get(vid)
        if rec is None:
            bad.append(f'{label} {os.path.basename(path)}: no view data in research/thumbs.json')
        elif (rec.get('views') or 0) < min_views:
            bad.append(f"{label} {os.path.basename(path)}: {rec.get('views'):,} views < {min_views:,}")
    return bad


def sections(text):
    """Brief paragraphs by their UPPERCASE label: {'BACKGROUND AND LIGHT': '...', 'TEXT': '...'}."""
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r'^([A-Z][A-Z /&-]{1,40}?)\s*(?:\([^)]*\))?:\s*(.*)', line)
        if m:
            cur = m.group(1).strip()
            out[cur] = m.group(2)
        elif cur:
            out[cur] += ' ' + line.strip()
    return out


HEX = re.compile(r'#[0-9A-Fa-f]{6}\b')


def check_reference_dna(job, brief, jobs_dir):
    """The brief must copy its LAYOUT REFERENCE's measured look, and keep its text legible.
    - refs/dna/<videoId>.json must exist (python dna.py measure <reference>)
    - the brief has a REFERENCE DNA paragraph
    - the BACKGROUND colour it names stays within Delta E 25 of the reference's (a flat field) or keeps its value class
    - every text fill colour has at least 3:1 contrast against that background, or against its own box (4.5:1 recommended)"""
    try:
        import dna
    except ImportError:
        return ['dna.py could not be imported (needs opencv-python-headless in this Python)']
    lay = next((p for p, w in job.get('refs', []) if w.split(':', 1)[0].strip().upper() == 'LAYOUT REFERENCE'), None)
    if not lay:
        return []
    vid = os.path.splitext(os.path.basename(lay))[0][-11:]
    dp = os.path.join(jobs_dir, 'refs', 'dna', vid + '.json')
    if not os.path.exists(dp):
        return [f'no reference DNA for {os.path.basename(lay)}: run  dna.py measure {lay}']
    d = json.load(open(dp))
    sec = sections(brief)
    bad = []
    if not any(k.startswith('REFERENCE DNA') for k in sec):
        bad.append('the brief has no REFERENCE DNA paragraph (the layout reference look to keep: background, outline, type, hero)')
    bg_key = next((k for k in sec if k.startswith('BACKGROUND')), None)
    bg_hex = HEX.findall(sec[bg_key])[:1] if bg_key else []
    bg = bg_hex[0] if bg_hex else d['background']
    if bg_hex:
        de = dna.delta_e(dna.lab([dna.rgb_of(bg)])[0], d['background_lab'])
        cls = dna.value_class(float(dna.lab([dna.rgb_of(bg)])[0][0]))
        step = abs(dna.CLASSES.index(cls) - dna.CLASSES.index(d['background_class']))
        if d['flat'] and (de > dna.BG_DRIFT_FAIL or step):
            bad.append(f"BACKGROUND {bg} drifts from the reference's flat {d['background']} (Delta E {de:.0f}, {cls} vs {d['background_class']}): keep the reference background")
        elif not d['flat'] and step == 2:
            bad.append(f"BACKGROUND {bg} is {cls}; the reference's scene is {d['background_class']} ({d['background']})")
    if 'TEXT' in sec:
        t = sec['TEXT']
        # text on its own box: "<fill hex> ... on a <box hex> box/band/pill/highlight" -> check fill against the box
        boxed = set()
        for m in re.finditer(r'(#[0-9A-Fa-f]{6})[^#]{0,40}?on (?:a |an |the )?(?:solid |flat )?(?:[a-z-]+ ){0,2}(#[0-9A-Fa-f]{6})', t):
            boxed.update((m.group(1).upper(), m.group(2).upper()))
            c = dna.contrast(m.group(1), m.group(2))
            if c < dna.MIN_TEXT_CONTRAST:
                bad.append(f'TEXT {m.group(1)} on its box {m.group(2)} has contrast {c:.1f}:1 (< {dna.MIN_TEXT_CONTRAST}): it will not read')
        for m in HEX.finditer(t):
            h = m.group(0).upper()
            if h in boxed:
                continue
            near = t[max(0, m.start() - 18):m.start()].lower() + ' ' + t[m.end():m.end() + 14].lower()
            if re.search(r'(?<!no )(shadow|stroke|outline|glow|box|highlight|band|pill|underline|bar)', near):
                continue                      # a stroke/shadow/box colour, not a fill
            c = dna.contrast(h, bg)
            if c < dna.MIN_TEXT_CONTRAST:
                bad.append(f'TEXT colour {h} on background {bg} has contrast {c:.1f}:1 (< {dna.MIN_TEXT_CONTRAST}): it will not read')
            elif c < dna.GOOD_TEXT_CONTRAST:
                print(f"{job['id']}: note: TEXT colour {h} on {bg} is {c:.1f}:1 (fine for big bold text with a dark stroke or shadow; weak without one)", flush=True)
    return bad


def check_labels(job):
    bad = [w for _, w in job.get('refs', []) if ':' not in w or not w.split(':', 1)[0].replace(' ', '').isupper()]
    if bad:
        print(f"{job['id']}: WARNING ref descriptions without an UPPERCASE LABEL: prefix: {bad}", flush=True)


def codex(text, refs, model, effort):
    cmd = ['codex', 'exec', '--skip-git-repo-check', '--json', '-s', 'read-only', '-c', f'model_reasoning_effort="{effort}"']
    if model:
        cmd += ['-m', model]
    for path, _ in refs:
        cmd += ['-i', os.path.abspath(os.path.expanduser(path))]
    cmd += ['-']
    p = subprocess.run(cmd, input=text, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=900,
                       shell=(os.name == 'nt'))
    thread, errors = None, []
    for line in p.stdout.splitlines():
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get('type') == 'thread.started':
            thread = e.get('thread_id')
        if e.get('type') in ('error', 'turn.failed'):
            errors.append(str(e.get('message') or e.get('error'))[:400])
        it = e.get('item') or {}
        if it.get('type') == 'agent_message' and it.get('text') and 'DONE' not in it.get('text', ''):
            errors.append('codex said: ' + it['text'][:300])
    return thread, errors


def shared_blocks(prompt_dir):
    """`_common.md` next to the briefs holds paragraphs like `LIKENESS: ...`; a brief pulls one in with {LIKENESS}."""
    p = os.path.join(prompt_dir, '_common.md')
    blocks = {}
    if os.path.exists(p):
        for para in open(p, encoding='utf-8').read().split('\n\n'):
            if ':' in para:
                k, v = para.split(':', 1)
                blocks[k.strip()] = v.strip()
    return blocks


def load_brief(spec):
    if not spec.startswith('@'):
        return spec
    path = spec[1:]
    text = open(path, encoding='utf-8').read()
    for k, v in shared_blocks(os.path.dirname(os.path.abspath(path))).items():
        text = re.sub(r'(?m)^\{' + re.escape(k) + r'\}\s*$', lambda _m, k=k, v=v: f'{k}: {v}', text)   # keep the label on its own line
        text = text.replace('{' + k + '}', v)
    return text


def run(job, models, effort):
    brief = load_brief(job['prompt'])
    refs = job.get('refs', [])
    text = WRAP.format(legend=legend(refs), brief=brief.strip())
    for stale in (job['out'], os.path.splitext(job['out'])[0] + '.log.json'):
        if os.path.exists(stale):
            os.remove(stale)
    t0 = time.time()
    thread, errors, model = None, [], None
    for model in models:
        with LOCK:
            if model in BAD:
                continue
        thread, errors = codex(text, refs, model, effort)
        if any('not supported' in e or 'does not exist' in e for e in errors):
            with LOCK:
                BAD.add(model)
            continue
        if thread and not errors:
            with LOCK:
                open(STATE, 'w').write(model or '')
        break
    img = None
    if thread:
        d = os.path.join(CODEX_HOME, 'generated_images', thread)
        if os.path.isdir(d):
            pngs = sorted((os.path.join(d, f) for f in os.listdir(d)), key=os.path.getmtime)
            if pngs:
                img = pngs[-1]
    out = job['out']
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    if img:
        shutil.copy(img, out)
    log = dict(id=job['id'], ok=bool(img), out=out if img else None, thread=thread, secs=round(time.time() - t0, 1),
               model=model, refs=[r[0] for r in refs], labels=[r[1].split(':', 1)[0].strip() for r in refs],
               ref_notes=[r[1] for r in refs], brief=job['prompt'], errors=errors, prompt=text)
    json.dump(log, open(os.path.splitext(out)[0] + '.log.json', 'w', encoding='utf-8'), indent=1)
    return log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('jobs')
    ap.add_argument('--parallel', type=int, default=6)
    ap.add_argument('--model', default=None)
    ap.add_argument('--effort', default='low')
    ap.add_argument('--only', default=None, help='comma-separated job ids')
    ap.add_argument('--check', action='store_true', help='validate labels, ref files, brief placeholders and reference views; render nothing')
    ap.add_argument('--no-dna', action='store_true', help='skip the reference-DNA checks (edit jobs have no layout reference anyway)')
    ap.add_argument('--min-views', type=int, default=100000,
                    help='LAYOUT REFERENCE and HOUSE STYLE thumbnails must come from videos with at least this many views (0 = off)')
    a = ap.parse_args()
    jobs = json.load(open(a.jobs, encoding='utf-8'))
    if a.only:
        keep = set(a.only.split(','))
        jobs = [j for j in jobs if j['id'] in keep]
    problems = 0
    views = view_data(a.jobs)
    for j in jobs:
        check_labels(j)
        missing = [p for p, _ in j.get('refs', []) if not os.path.exists(os.path.expanduser(p))]
        if len(j.get('refs', [])) > MAX_REFS:
            missing.append(f"{len(j['refs'])} reference images: Codex's image tool takes at most {MAX_REFS}. Merge the logos into one PNG, or drop the HOUSE STYLE reference")
        unfilled = re.findall(r'\{[A-Z][A-Z ]*\}', load_brief(j['prompt']))
        low = check_references(j, views, a.min_views) if a.min_views else []
        drift = check_reference_dna(j, load_brief(j['prompt']), os.path.dirname(os.path.abspath(a.jobs))) if not a.no_dna else []
        for what, items in (('missing ref files', missing), ('unfilled {BLOCKS} (not in _common.md)', unfilled),
                            (f'references under the {a.min_views:,}-view minimum', low),
                            ('does not follow its LAYOUT REFERENCE', drift)):
            if items:
                problems += 1
                print(f"{j['id']}: {what}: {items}", flush=True)
    if a.check:
        print(f'check: {len(jobs)} jobs, {problems} problem(s)')
        raise SystemExit(1 if problems else 0)
    if problems:
        raise SystemExit(f'{problems} problem(s): fix them (see above) before rendering; nothing was rendered')
    models = [a.model] if a.model else candidate_models()
    print(f'{len(jobs)} jobs, models to try={models[:3]}, parallel={a.parallel}', flush=True)
    with cf.ThreadPoolExecutor(a.parallel) as ex:
        futs = {ex.submit(run, j, models, a.effort): j['id'] for j in jobs}
        for f in cf.as_completed(futs):
            try:
                r = f.result()
                print(f"{r['id']}: {'ok' if r['ok'] else 'FAILED'} {r['secs']}s {r['out'] or r['errors']}", flush=True)
            except Exception as e:
                print(f'{futs[f]}: EXCEPTION {e}', flush=True)


if __name__ == '__main__':
    main()
