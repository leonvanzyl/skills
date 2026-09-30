"""Publishing files for the long-form upload, from the programme's word timings and edit_plan.json:
  <media_dir>/captions.srt   YouTube captions (verbatim minus fillers and noise tags; "five point five" -> "5.5"; the plan's
                             "caption_fixes" phrases applied; <= 2 lines of 42 chars, <= 6 s per cue)
  <media_dir>/PUBLISH.md     SEO title, description, YouTube chapters, and the two community links exactly as written
The title and description come from edit_plan.json -> "publish": {"title": ..., "description": ...}; write them
from what the final edit actually says. Chapters come from edit_plan.json -> "chapters" and are checked against
YouTube's rules (first at 0:00, at least 3, each at least 10 s).
usage: python scripts/publish.py"""
import sys, os, re, json
sys.path.insert(0, 'scripts'); import config as C, media as M

LINKS = ['🎁 Get the resources from this video + my free AI builder course: https://skool.com/leonvanzyl',
         '🚀 Go deeper inside Agentic Labs: AI coding courses, live Q&A, weekly challenges, and direct access to me: https://skool.com/agentic-labs']
FILLERS = {'um', 'uh', 'erm', 'hmm', 'mm'}


def srt_tc(t):
    ms = int(round(t * 1000)); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def yt_tc(t):
    t = int(t); h, r = divmod(t, 3600); m, s = divmod(r, 60)
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'


NUM = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen '
                                   'sixteen seventeen eighteen nineteen twenty'.split())}


def _bare(w):
    return re.sub(r"[^a-z0-9'-]", '', w.lower())


def merge_words(words, phrases):
    """verbatim tokens -> readable tokens, BEFORE cues are cut (so a phrase never straddles two cues):
    'five point five' -> '5.5', then the plan's caption_fixes (multi-word phrases welcome) -> their replacement"""
    ws = [dict(w) for w in words]
    fixes = [([_bare(t) for t in a.split()], b) for a, b in phrases.items()]
    out, k = [], 0
    while k < len(ws):
        w = ws[k]
        if k + 2 < len(ws) and _bare(w['w']) in NUM and _bare(ws[k + 1]['w']) == 'point' and _bare(ws[k + 2]['w']) in NUM:
            tail = re.sub(r'^.*?([.,?!]*)$', r'\1', ws[k + 2]['w'])
            out.append(dict(w, w=f"{NUM[_bare(w['w'])]}.{NUM[_bare(ws[k + 2]['w'])]}{tail}", e=ws[k + 2]['e'])); k += 3; continue
        hit = None
        for toks, rep in fixes:
            if [_bare(x['w']) for x in ws[k:k + len(toks)]] == toks: hit = (toks, rep); break
        if hit:
            last = ws[k + len(hit[0]) - 1]
            tail = re.sub(r'^.*?([.,?!]*)$', r'\1', last['w'])
            out.append(dict(w, w=hit[1] + tail, e=last['e'])); k += len(hit[0]); continue
        out.append(w); k += 1
    return out


def split2(text, width=42):
    """one line, or two balanced lines of at most `width` characters (None if it can't fit)"""
    if len(text) <= width: return text
    ws = text.split(); best = None
    for k in range(1, len(ws)):
        a, b = ' '.join(ws[:k]), ' '.join(ws[k:])
        if len(a) <= width and len(b) <= width and (best is None or abs(len(a) - len(b)) < best[0]): best = (abs(len(a) - len(b)), a + '\n' + b)
    return best[1] if best else None


def cues(words, fixes):
    ws = merge_words([w for w in words if not w.get('tag') and re.sub(r'[^a-z]', '', w['w'].lower()) not in FILLERS], fixes)
    out, cur = [], []
    txt = lambda ws_: ' '.join(w['w'] for w in ws_)

    def flush():
        if cur: out.append(dict(s=cur[0]['s'], e=cur[-1]['e'], text=split2(txt(cur)) or txt(cur)))
    for w in ws:
        if cur and (w['s'] - cur[-1]['e'] > 0.6 or w['e'] - cur[0]['s'] > 6.0 or split2(txt(cur + [w])) is None):
            flush(); cur = []
        cur.append(w)
        if re.search(r'[.?!]$', w['w']) and len(txt(cur)) > 20:
            flush(); cur = []
    flush()
    return out


def main():
    P = M.program(); PL = M.plan()
    fixes = PL.get('caption_fixes', {})               # phrase -> replacement, e.g. {"agent-decoding": "agentic coding"}
    cs = cues(P['words'], fixes)
    os.makedirs(C.MEDIA, exist_ok=True)
    with open(os.path.join(C.MEDIA, 'captions.srt'), 'w', encoding='utf-8') as f:
        for k, c in enumerate(cs, 1):
            f.write(f"{k}\n{srt_tc(c['s'])} --> {srt_tc(max(c['e'], c['s'] + 0.5))}\n{c['text']}\n\n")
    ch = sorted(PL.get('chapters', []), key=lambda c: c['t'])
    problems = []
    if ch and ch[0]['t'] > 0.01: problems.append('the first chapter must start at 0:00')
    if 0 < len(ch) < 3: problems.append('YouTube needs at least 3 chapters')
    for a, b in zip(ch, ch[1:] + [dict(t=P['dur'])]):
        if b['t'] - a['t'] < 10: problems.append(f"chapter '{a['title']}' is under 10 s")
    pub = PL.get('publish', {})
    title = pub.get('title', 'TODO: SEO title (<= 60 chars, main search term first)')
    desc = pub.get('description', 'TODO: 2-3 line SEO description of what the viewer learns')
    lines = [f"# Publishing copy: {PL.get('new_timeline', P.get('timeline'))}", '', '**Title**', '```', title, '```', '', '**Description**', '```', desc, '']
    if ch:
        lines += ['Chapters:'] + [f"{yt_tc(c['t'])} {c['title']}" for c in ch] + ['']
    lines += [LINKS[0], '', LINKS[1], '```', '', f'Captions: `captions.srt` ({len(cs)} cues) - upload it in YouTube Studio > Subtitles.']
    open(os.path.join(C.MEDIA, 'PUBLISH.md'), 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print(f"captions.srt: {len(cs)} cues | PUBLISH.md: {len(ch)} chapters | title {len(title)} chars")
    for p in problems: print('  PROBLEM', p)


if __name__ == '__main__':
    main()
