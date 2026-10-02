"""Build thumbnails/report.html: a self-contained page that shows, for every delivered variant, the outlier it borrowed
from, the house-style thumbnail, the decisions behind it and its full lineage. Everything is read from the run's own
records, never typed by hand:

  thumbnails/manifest.json (qa.py norm) -> *.stamp.json (stamp.py) -> out/**/*.log.json (gen.py: refs, labels, thread)
  concepts.json, research/thumbs.json, brief.md, research/niche.md

  python report.py [work-folder] [--min-views 100000] [--title "Video title"] [--url https://youtu.be/...]
"""
import argparse, base64, datetime, glob, html, io, json, os, re
from PIL import Image

E = html.escape


def load(p, default=None):
    try:
        return json.load(open(p, encoding='utf-8'))
    except (OSError, ValueError):
        return default


def data_uri(path, width):
    try:
        im = Image.open(os.path.expanduser(path))
    except OSError:
        return ''
    if im.mode in ('RGBA', 'LA', 'P'):   # logos: flatten onto light grey, not black
        im = im.convert('RGBA')
        bg = Image.new('RGBA', im.size, (236, 236, 236, 255))
        bg.alpha_composite(im)
        im = bg
    im = im.convert('RGB')
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=84)
    return 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()


def vid_of(path):
    return os.path.splitext(os.path.basename(path))[0][-11:]


def k(n):
    if n is None:
        return '?'
    return f'{n / 1e6:.1f}M' if n >= 1e6 else f'{n / 1e3:.0f}k' if n >= 1e3 else str(n)


def infer_label(path):
    """Labels for logs written before gen.py recorded them."""
    b = os.path.basename(path).lower()
    if path.replace('\\', '/').startswith('out/') and b.endswith('.png'):
        return 'THUMBNAIL'
    if b.startswith('bo'):
        return 'LAYOUT REFERENCE'
    if b.startswith(('owntop', 'ownrecent', 'leontop', 'leonrecent')):
        return 'HOUSE STYLE'
    if 'avatar' in path.replace('\\', '/') or b == 'leon.jpg':
        return 'AVATAR'
    if 'ui' in b:
        return 'UI'
    return 'LOGO'


def labelled(log):
    labels = log.get('labels') or [infer_label(p) for p in log['refs']]
    return list(zip(log['refs'], [l.upper() for l in labels]))


def lineage(source):
    """Walk back from a deliverable's source file to the original render: stamps, edits, render."""
    steps, cur = [], source
    for _ in range(12):
        stem = os.path.splitext(cur)[0]
        st = load(stem + '.stamp.json')
        if st:
            steps.append(('stamp', cur, st))
            cur = st['src']
            continue
        log = load(stem + '.log.json')
        if log:
            thumb = next((p for p, l in labelled(log) if l == 'THUMBNAIL'), None)
            if thumb:
                steps.append(('edit', cur, log))
                cur = thumb
                continue
            steps.append(('render', cur, log))
            break
        steps.append(('unknown', cur, None))
        break
    return list(reversed(steps))


def edit_changes(log):
    txt = log.get('prompt', '')
    return [m.strip() for m in re.findall(r'^\s*\d+\.\s+(.+)$', txt.split('BRIEF', 1)[-1], re.M)]


def md(text):
    """Small Markdown -> HTML (headings, lists, tables, bold, code, links, paragraphs)."""
    def inline(s):
        s = E(s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', s)
        s = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', s)
        return s
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip():
            i += 1
            continue
        m = re.match(r'^(#{1,4})\s+(.*)', ln)
        if m:
            n = min(len(m.group(1)) + 2, 6)
            out.append(f'<h{n}>{inline(m.group(2))}</h{n}>')
            i += 1
            continue
        if ln.lstrip().startswith('|'):
            rows = []
            while i < len(lines) and lines[i].lstrip().startswith('|'):
                cells = [c.strip() for c in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-{2,}:?', c) for c in cells if c):
                    rows.append(cells)
                i += 1
            if rows:
                head = ''.join(f'<th>{inline(c)}</th>' for c in rows[0])
                body = ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
                out.append(f'<div class="tablewrap"><table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>')
            continue
        if re.match(r'^\s*([-*]|\d+\.)\s+', ln):
            items = []
            while i < len(lines) and (re.match(r'^\s*([-*]|\d+\.)\s+', lines[i]) or (lines[i].startswith('  ') and lines[i].strip())):
                mm = re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)', lines[i])
                if mm:
                    items.append((len(mm.group(1)) // 2, inline(mm.group(3))))
                elif items:
                    items[-1] = (items[-1][0], items[-1][1] + ' ' + inline(lines[i].strip()))
                i += 1
            out.append('<ul>' + ''.join(f'<li style="margin-left:{d * 18}px">{t}</li>' for d, t in items) + '</ul>')
            continue
        para = [ln.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,4}\s|\s*([-*]|\d+\.)\s|\s*\|)', lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append(f'<p>{inline(" ".join(para))}</p>')
    return '\n'.join(out)


CSS = """
:root{--bg:#f6f5f2;--card:#ffffff;--ink:#16161a;--muted:#5d5d66;--line:#e3e1dc;--ok:#1f7a3f;--okbg:#e4f4e9;--bad:#b3261e;
--badbg:#fbe5e3;--accent:#c4562b;--chip:#efede8;--shadow:0 1px 2px rgba(0,0,0,.05),0 8px 24px rgba(0,0,0,.06)}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#111113;--card:#1b1b1f;--ink:#ededef;--muted:#a1a1aa;
--line:#2c2c33;--ok:#6fd497;--okbg:#16301f;--bad:#ff8a80;--badbg:#3a1714;--accent:#f08a5d;--chip:#26262c;--shadow:none}}
:root[data-theme="dark"]{--bg:#111113;--card:#1b1b1f;--ink:#ededef;--muted:#a1a1aa;--line:#2c2c33;--ok:#6fd497;--okbg:#16301f;
--bad:#ff8a80;--badbg:#3a1714;--accent:#f08a5d;--chip:#26262c;--shadow:none}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:1240px;margin:0 auto;padding:32px 16px 80px}h1{font-size:28px;line-height:1.2;margin:0 0 6px}
h2{font-size:21px;margin:0}h3{font-size:15px;margin:18px 0 8px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
a{color:var(--accent)}img{max-width:100%;height:auto;display:block;border-radius:8px}
.sub{color:var(--muted);margin:0}.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:22px;margin:22px 0;box-shadow:var(--shadow)}
.strip{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px;margin-top:18px}.strip figure{margin:0}
figcaption{font-size:13px;color:var(--muted);margin-top:6px}
.trio{display:grid;grid-template-columns:1.25fr 1fr .8fr;gap:18px;align-items:start;margin-top:16px}
@media (max-width:900px){.trio{grid-template-columns:1fr}}
.label{font-size:12px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;color:var(--muted);margin-bottom:6px}
.badge{display:inline-block;font-size:12px;font-weight:700;padding:2px 8px;border-radius:99px}
.ok{background:var(--okbg);color:var(--ok)}.bad{background:var(--badbg);color:var(--bad)}
.tag{display:inline-block;font-size:12px;padding:2px 9px;border-radius:99px;background:var(--chip);color:var(--muted);margin-left:8px;vertical-align:middle}
.meta{font-size:13.5px;margin-top:8px}.meta div{margin:2px 0}.why{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:900px){.why{grid-template-columns:1fr}}
ol.steps{padding-left:20px;margin:6px 0}ol.steps li{margin:6px 0}.refs{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.refs figure{margin:0;width:124px}.refs img{border-radius:6px;width:124px;height:70px;object-fit:contain;background:var(--chip)}.refs figcaption{font-size:11px;margin-top:3px;overflow-wrap:anywhere;line-height:1.3}
code{font:12.5px ui-monospace,SFMono-Regular,Consolas,monospace;background:var(--chip);padding:1px 5px;border-radius:5px;overflow-wrap:anywhere}
details{margin-top:12px}summary{cursor:pointer;color:var(--accent);font-weight:600}pre{white-space:pre-wrap;font:12.5px ui-monospace,Consolas,monospace;
background:var(--chip);padding:12px;border-radius:8px;overflow-wrap:anywhere}
.pool{display:grid;grid-template-columns:repeat(auto-fill,minmax(190px,1fr));gap:12px}.pool figure{margin:0}
.pool .used img{outline:3px solid var(--accent);outline-offset:2px}.pool .low{opacity:.42}
.tablewrap{overflow-x:auto}table{border-collapse:collapse;font-size:13.5px;width:100%}th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.rule{border-left:4px solid var(--ok);padding:10px 14px;background:var(--okbg);border-radius:8px;margin-top:16px}
.rule.fail{border-color:var(--bad);background:var(--badbg)}
.warn{background:#fff3cd;color:#8a5a00}.fid{display:grid;grid-template-columns:1fr 1fr;gap:18px}@media (max-width:900px){.fid{grid-template-columns:1fr}}
.pal{display:flex;height:26px;border-radius:6px;overflow:hidden;border:1px solid var(--line)}.sw{display:inline-block;width:14px;height:14px;border-radius:3px;vertical-align:-2px;border:1px solid var(--line)}
"""


def ref_block(label, path, rec, min_views, used_for=''):
    vid = vid_of(path)
    views = (rec or {}).get('views')
    ok = views is not None and views >= min_views
    bo = (rec or {}).get('breakout')
    subs = (rec or {}).get('subs')
    badge = (f'<span class="badge ok">{views:,} views</span>' if ok else
             f'<span class="badge bad">{"no view data" if views is None else f"{views:,} views"}: under {min_views:,}</span>')
    lines = [f'<div><strong>{E((rec or {}).get("channel", "").strip() or "?")}</strong>' + (f' &middot; {k(subs)} subscribers' if subs else '') + '</div>',
             f'<div>&ldquo;{E((rec or {}).get("title", os.path.basename(path)))}&rdquo;</div>',
             f'<div>{badge}' + (f' &middot; breakout <strong>{bo:.1f}&times;</strong>' if bo else '') + '</div>',
             f'<div><a href="https://youtu.be/{vid}">youtu.be/{vid}</a></div>']
    return (f'<div><div class="label">{E(label)}</div><img src="{data_uri(path, 520)}" alt="{E(label)} thumbnail">'
            f'<div class="meta">{"".join(lines)}</div></div>'), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('work', nargs='?', default='.')
    ap.add_argument('--min-views', type=int, default=100000)
    ap.add_argument('--title', default=None)
    ap.add_argument('--url', default=None)
    a = ap.parse_args()
    os.chdir(a.work)

    manifest = load('thumbnails/manifest.json', {})
    concepts = load('concepts.json', [])
    concepts = concepts if isinstance(concepts, list) else concepts.get('concepts', [])
    cmap = {c.get('id'): c for c in concepts}
    thumbs = load('research/thumbs.json', [])
    tmap = {t['id']: t for t in thumbs}
    current = sorted(glob.glob('competitors/CURRENT_*.jpg'))
    cur_id = vid_of(current[0]) if current else None
    title = a.title or next((t['title'] for t in thumbs if t.get('group') == 'current' or t['id'] == cur_id), None) or os.path.basename(os.getcwd())
    title = re.sub(r'\s*\[current\]\s*$', '', title, flags=re.I)
    url = a.url or (f'https://youtu.be/{vid_of(current[0])}' if current else None)

    stranger_post = load('qa/stranger_post.json', {})
    stranger_pre = load('qa/stranger_pre.json', {})
    try:
        import dna as dnamod
    except ImportError:
        dnamod = None
    cards, used, violations, delivered_concepts, strip = [], set(), [], set(), []
    fid_fails, stranger_fails = [], []
    for name in sorted(manifest):
        src = manifest[name]['source']
        steps = lineage(src)
        render = next((s for s in steps if s[0] == 'render'), None)
        log = render[2] if render else {}
        rid = log.get('id', '')
        cid = (re.match(r'^(v\d+)', rid) or re.match(r'(.*)', rid)).group(1)
        delivered_concepts.add(cid)
        c = cmap.get(cid, {})
        refs = labelled(log) if log else []
        lay = next((p for p, l in refs if l == 'LAYOUT REFERENCE'), None)
        house = next((p for p, l in refs if l == 'HOUSE STYLE'), None)
        final = f'thumbnails/{name}.jpg'
        strip.append(f'<figure><a href="#{E(name)}"><img src="{data_uri(final, 440)}" alt="{E(name)}"></a><figcaption><strong>{E(name.split("_")[0])}</strong> &middot; {E(c.get("text", ""))}</figcaption></figure>')
        blocks = []
        if lay:
            used.add(vid_of(lay))
            b, ok = ref_block('Borrowed layout from (competitor outlier)', lay, tmap.get(vid_of(lay)), a.min_views)
            blocks.append(b)
            if not ok:
                violations.append(f'{name}: layout reference {os.path.basename(lay)}')
        else:
            blocks.append('<div><div class="label">Borrowed layout from</div><p class="sub">No layout reference was attached to this render.</p></div>')
            violations.append(f'{name}: no layout reference attached')
        if house:
            b, ok = ref_block('House style (your own thumbnail)', house, tmap.get(vid_of(house)), a.min_views)
            blocks.append(b)
            if not ok:
                violations.append(f'{name}: house-style reference {os.path.basename(house)}')
        # did it follow the reference? (measured, dna.py)
        fid_html = ''
        if lay and dnamod and os.path.exists(os.path.expanduser(lay)):
            f = dnamod.fidelity(final, os.path.expanduser(lay))
            if f['verdict'] == 'FAIL':
                fid_fails.append(name)
            cls = {'PASS': 'ok', 'WARN': 'warn', 'FAIL': 'bad'}[f['verdict']]
            def strip_of(d):
                return ''.join(f'<span style="flex:{max(1, int(sh * 100))};background:{h}" title="{h} {sh:.0%}"></span>' for h, sh in d['palette'])
            notes = ''.join(f'<li>{E(x)}</li>' for x in f['problems'] + f['warnings'])
            fid_html = (f'<h3>Did it follow the reference? <span class="badge {cls}">{f["verdict"]}</span></h3>'
                        f'<div class="fid"><div><div class="label">Reference</div><div class="pal">{strip_of(f["reference"])}</div>'
                        f'<div class="meta">background <span class="sw" style="background:{f["reference"]["background"]}"></span> {f["reference"]["background"]} '
                        f'({f["reference"]["background_class"]}, {"flat" if f["reference"]["flat"] else "scene"})</div></div>'
                        f'<div><div class="label">Ours</div><div class="pal">{strip_of(f["render"])}</div>'
                        f'<div class="meta">background <span class="sw" style="background:{f["render"]["background"]}"></span> {f["render"]["background"]} '
                        f'({f["render"]["background_class"]}) &middot; &Delta;E {f["background_delta_e"]} &middot; palette distance {f["palette_distance"]}</div></div></div>'
                        + (f'<ul>{notes}</ul>' if notes else ''))
        dna_d = c.get('dna') or {}
        dna_html = ('<div class="meta">' + ''.join(f'<div><strong>{E(str(kk).replace("_", " ").title())}:</strong> {E(str(vv))}</div>' for kk, vv in dna_d.items()) + '</div>') if dna_d else ''
        # the stranger test (review.md)
        sp = stranger_post.get(name) or {}
        pre = stranger_pre.get(cid) or {}
        def stranger_block(r, when):
            if not r:
                return ''
            v = (r.get('verdict') or '').upper()
            badge = f' <span class="badge {"ok" if v == "PASS" else "bad"}">{E(v)}</span>' if v else ''
            return (f'<div><div class="label">{when}{badge}</div><div class="meta"><div><strong>Thinks it is about:</strong> {E(r.get("about", ""))}</div>'
                    f'<div><strong>Expects:</strong> {E(r.get("expect", ""))}</div><div><strong>Would click:</strong> {E(str(r.get("click", "?")))}/5</div>'
                    + (f'<div><strong>Noticed first:</strong> {E(r.get("first_noticed", ""))}</div>' if r.get('first_noticed') else '')
                    + (f'<div><strong>Confused by:</strong> {E(r.get("confusing", ""))}</div>' if r.get('confusing') else '') + '</div></div>')
        if (sp.get('verdict') or '').upper() == 'FAIL':
            stranger_fails.append(name)
        stranger_html = ''
        if sp or pre:
            stranger_html = ('<h3>The stranger test: title + thumbnail, nothing else</h3><div class="why">'
                             + stranger_block(pre, 'Before rendering (the concept)') + stranger_block(sp, 'After rendering (the image)') + '</div>')
        ptitle = c.get('title') or c.get('best_title') or ''
        # lineage
        st_html = []
        for kind, path, rec in steps:
            if kind == 'render':
                chips = ''.join(f'<figure><img src="{data_uri(p, 240)}" alt=""><figcaption>{E(l.title())}<br>{E(os.path.basename(p))}</figcaption></figure>' for p, l in refs)
                brief = f'. Brief <code>{E(rec["brief"])}</code>' if rec.get('brief') else ''
                st_html.append(f'<li><strong>Render</strong> <code>{E(rec.get("id", ""))}</code> with Codex ({E(rec.get("model") or "")}, '
                               f'{rec.get("secs", "?")} s, thread <code>{E((rec.get("thread") or "")[:23])}</code>){brief}. '
                               f'Attached:<div class="refs">{chips}</div></li>')
            elif kind == 'edit':
                ch = ''.join(f'<li>{E(x)}</li>' for x in edit_changes(rec)) or '<li>(see brief)</li>'
                st_html.append(f'<li><strong>Edit pass</strong> <code>{E(rec.get("id", ""))}</code>, changing only:<ul>{ch}</ul></li>')
            elif kind == 'stamp':
                st_html.append(f'<li><strong>Logo stamp</strong>: the official <code>{E(os.path.basename(rec["logo"]))}</code> composited over the model\'s redrawn version &rarr; <code>{E(path)}</code></li>')
            else:
                st_html.append(f'<li>Source <code>{E(path)}</code> (no render log found)</li>')
        st_html.append(f'<li><strong>Delivered</strong> as <code>{E(final)}</code> (1280&times;720, plus a 1920 master)</li>')
        claims = ''.join(f'<li>{E(x)}</li>' for x in c.get('claims', [])) or '<li>(none recorded)</li>'
        why = f"""<div class="why"><div><h3>Why this concept</h3><p>{E(c.get('why', '(not recorded)'))}</p>
<h3>What it borrows</h3><p>{E(c.get('borrows', '(not recorded)'))}</p></div>
<div><h3>Claims, and what backs them</h3><ul>{claims}</ul>
<h3>Design</h3><div class="meta"><div><strong>Text:</strong> {E(c.get('text', ''))}</div><div><strong>Face:</strong> {E(c.get('face', ''))}</div>
<div><strong>Hero:</strong> {E(c.get('hero', ''))}</div><div><strong>Palette:</strong> {E(c.get('palette', ''))}</div></div></div></div>"""
        brief_txt = (log.get('prompt') or '').split('BRIEF', 1)[-1].strip()
        cards.append(f"""<section class="card" id="{E(name)}"><h2>{E(name.split('_')[0])} &middot; {E(c.get('text', name))}<span class="tag">{E(c.get('mechanic') or c.get('angle') or '')}</span></h2>
{f'<p class="sub">Pairs with the title: <strong>{E(ptitle)}</strong></p>' if ptitle else ''}
<div class="trio"><div><div class="label">Ours</div><img src="{data_uri(final, 760)}" alt="{E(name)}"></div>{''.join(blocks)}</div>
{stranger_html}{fid_html}{('<h3>Reference DNA it was told to keep</h3>' + dna_html) if dna_html else ''}
{why}<h3>How it was made</h3><ol class="steps">{''.join(st_html)}</ol>
<details><summary>The exact brief sent to the image model</summary><pre>{E(brief_txt)}</pre></details></section>""")

    spares = [c for c in concepts if c.get('id') not in delivered_concepts]
    dropped = load('concepts_dropped.json', [])
    dropped = dropped if isinstance(dropped, list) else dropped.get('concepts', [])
    drop_html = ''.join(f'<li><strong>{E(c.get("id", ""))}</strong> &middot; {E(c.get("text", ""))} <span class="sub">({E(c.get("why_dropped") or c.get("reason") or "")})</span></li>' for c in dropped)
    spare_html = ''.join(f'<li><strong>{E(c.get("id", ""))}</strong> &middot; {E(c.get("text", ""))} <span class="sub">({E(c.get("mechanic", ""))}; borrows {E(c.get("borrows", ""))})</span></li>' for c in spares)

    pool = sorted((t for t in thumbs if t.get('group') == 'niche'), key=lambda t: -(t.get('breakout') or 0))
    pool_html = ''.join(
        f'<figure class="{"used" if t["id"] in used else ""} {"low" if (t.get("views") or 0) < a.min_views else ""}">'
        f'<a href="https://youtu.be/{t["id"]}"><img src="{data_uri("competitors/" + t["file"], 380)}" alt=""></a>'
        f'<figcaption><strong>{k(t.get("views"))}</strong> views &middot; {(t.get("breakout") or 0):.0f}&times; &middot; {E(t["channel"].strip()[:24])}'
        f'{" &middot; <strong>used</strong>" if t["id"] in used else ""}{" &middot; under " + k(a.min_views) if (t.get("views") or 0) < a.min_views else ""}</figcaption></figure>'
        for t in pool if os.path.exists('competitors/' + t['file']))
    n_ok = sum(1 for t in pool if (t.get('views') or 0) >= a.min_views)

    checks = []
    if dnamod:
        checks.append(f'<div class="rule{" fail" if fid_fails else ""}"><strong>Reference fidelity:</strong> '
                      + ('every variant kept its reference&rsquo;s background and palette (measured).' if not fid_fails else
                         'these left their reference&rsquo;s look: ' + ', '.join(E(x) for x in fid_fails)) + '</div>')
    if stranger_post:
        checks.append(f'<div class="rule{" fail" if stranger_fails else ""}"><strong>Stranger test:</strong> '
                      + ('a viewer who saw only the title and thumbnail named the video&rsquo;s real subject every time.' if not stranger_fails else
                         'a viewer could not tell what these were about: ' + ', '.join(E(x) for x in stranger_fails)) + '</div>')
    rule = (f'<div class="rule"><strong>Reference rule met:</strong> every layout and house-style reference comes from a video with at least {a.min_views:,} views.</div>'
            if not violations else
            '<div class="rule fail"><strong>Reference rule broken</strong> (minimum ' + f'{a.min_views:,} views):<ul>' + ''.join(f'<li>{E(v)}</li>' for v in violations) + '</ul></div>')
    cur_html = (f'<figure style="max-width:300px;margin:0"><img src="{data_uri(current[0], 440)}" alt="current thumbnail"><figcaption>Current thumbnail</figcaption></figure>' if current else '')
    appendix = ''
    for label, p in (('The video brief (brief.md)', 'brief.md'), ('Full niche research (research/niche.md)', 'research/niche.md'), ('Asset sources (refs/assets.md)', 'refs/assets.md')):
        if os.path.exists(p):
            appendix += f'<details><summary>{E(label)}</summary>{md(open(p, encoding="utf-8").read())}</details>'

    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thumbnail Report</title><style>{CSS}</style></head><body><main>
<p class="sub">Thumbnail report &middot; generated {datetime.datetime.now():%Y-%m-%d %H:%M}</p>
<h1>{E(title)}</h1>{f'<p class="sub"><a href="{E(url)}">{E(url)}</a></p>' if url else ''}
<section class="card"><div style="display:flex;gap:24px;flex-wrap:wrap;align-items:flex-start"><div style="flex:1;min-width:260px">
<p><strong>{len(manifest)} variants</strong>, each a different concept, ranked A first. Every card below shows our thumbnail next to the competitor outlier it borrowed from and your own thumbnail used for house style, then the reasoning and the exact steps that made it. All of it is read from the run's render logs, not written by hand.</p>
{rule}{''.join(checks)}</div>{cur_html}</div><div class="strip">{''.join(strip)}</div></section>
{''.join(cards)}
{f'<section class="card"><h2>Spare concepts (planned, not delivered)</h2><ul>{spare_html}</ul></section>' if spares else ''}
{f'<section class="card"><h2>Dropped before rendering (failed the stranger test or the rules)</h2><ul>{drop_html}</ul></section>' if dropped else ''}
<section class="card"><h2>The research pool</h2><p class="sub">Every niche outlier the research collected, by breakout score. {n_ok} of {len(pool)} have at least {a.min_views:,} views and could be used; faded ones could not. Outlined ones were used.</p>
<div class="pool" style="margin-top:14px">{pool_html}</div></section>
<section class="card"><h2>Appendix</h2>{appendix or '<p class="sub">No brief or research notes found.</p>'}</section>
</main></body></html>"""
    os.makedirs('thumbnails', exist_ok=True)
    open('thumbnails/report.html', 'w', encoding='utf-8').write(page)
    print(f'thumbnails/report.html  {len(page) / 1e6:.1f} MB  {len(manifest)} variants  violations: {len(violations)}')
    for v in violations:
        print('  RULE:', v)


if __name__ == '__main__':
    main()
