"""Build the review page.   python report.py <report dir>

Reads <report dir>/data.json and writes <report dir>/index.html (images are referenced as img/<file> beside it).
The page is the deliverable Leon reviews, so its order is fixed: what the angle is and who it is for, the three to test
first, the launch and test plan, every concept with its reasoning and checks beside it, what the checks found (and the
reasons to doubt them), what the research did and did not show, the titles, and the open questions.
Every section except the header and the concepts is optional: leave its key out and it is not drawn.
The schema is documented in references/report.md; ~/.yt-packaging/report-example.json, where present, is a complete
worked example (kept outside the published skill).
"""
import json, os, sys, html
R = sys.argv[1] if len(sys.argv) > 1 else "report"
D = json.load(open(os.path.join(R, "data.json"), encoding="utf-8")); e = html.escape
CH = D.get("channel_line", "Leon van Zyl")

def pairs(items, tag="li"): return "".join(f"<{tag}><b>{e(a)}</b> {e(b)}</{tag}>" for a, b in items)
def yt(title, img, w):
    return (f'<figure class="yt" style="--w:{w}px"><img src="{img}" alt="" loading="lazy"><figcaption><span class="av"></span>'
            f'<span class="tt"><b>{e(title)}</b><i>{e(CH)}</i></span></figcaption></figure>')
def row(dt, dd): return f'<div class="row"><dt>{dt}</dt><dd>{dd}</dd></div>'
def chip(cls, label): return f'<span class="chip {cls}">{e(label)}</span>'

def concept(c):
    rows = [row("Words", f'<span class="words">{e(c["words"])}</span>'),
            row("Title it pairs with", e(c["title"]) + (f"<br><span class='also'>also: {e(c['title_alt'])}</span>" if c.get("title_alt") else "")),
            row("One-second read", e(c["one_second"])), row("Why it should win", e(c["why"]))]
    if c.get("evidence"): rows.append(row("Where the idea comes from", e(c["evidence"])))
    # Agents' reads are printed as reads: neutral chips, never a green tick. Only the promise check, which quotes the
    # transcript, carries a colour, and its colour must be amber or red whenever it found a moderate overclaim.
    if c.get("reads"): rows.append(row("What blind viewers expected", '<span class="reads">' + " · ".join("“" + e(r) + "”" for r in c["reads"][:3]) + "</span>"))
    if c.get("panel"):
        p = c["panel"]
        rows.append(row("Blind read test (taps are weak evidence)", f'tapped in {p["picked"]} of {p["shown"]} viewings. <span class="also">{e(p.get("by_viewer", ""))}</span>' + (f' <span class="also">{e(p["note"])}</span>' if p.get("note") else "")))
    if c.get("promise"): rows.append(row("Promise check", chip(c["promise"]["cls"], c["promise"]["label"]) + " " + e(c["promise"]["text"])))
    if c.get("qa"): rows.append(row("Inspection of the final file", chip("info", c["qa"].get("label", "Inspector's read")) + " " + e(c["qa"]["text"])))
    if c.get("likeness"): rows.append(row("Likeness (your call)", chip("info", c["likeness"]["label"]) + " " + e(c["likeness"]["text"])))
    if c.get("caveat"): rows.append(row("Watch for", e(c["caveat"])))
    # The main image is the dark version (Leon, 2026-11-24). An alternate is labelled by what it is: pass "alt_label"
    # ("Bright alternate") so the page never calls a bright ground just "Alternative".
    alt_label = c.get("alt_label") or "Alternative"
    alt = f'<div class="alt"><img src="{c["alt_img"]}" alt="{e(alt_label)} of concept {c["n"]}" loading="lazy"><p><b>{e(alt_label)}.</b> {e(c.get("alt_note", ""))}</p></div>' if c.get("alt_img") else ""
    # Likeness is his call, so he gets the evidence, not only a read of it: "face_img" is the native-size face sheet
    # from `tools.py face` (the face in this thumbnail beside his reference portrait), shown whole and unscaled-up.
    face = f'<figure class="facecmp"><img src="{c["face_img"]}" alt="The face in concept {c["n"]} at full size, beside the reference portrait" loading="lazy"><figcaption><b>Your face at full size, beside your reference portrait.</b> {e(c.get("face_note", ""))}</figcaption></figure>' if c.get("face_img") else ""
    return f'''
<article class="concept" id="c{c["n"]}">
  <header><span class="num">{c["n"]}</span><div><h3>{e(c["name"])}</h3><p class="reason">{e(c["reason"])}</p></div></header>
  <div class="body">
    <div class="art"><img class="main" src="{c["img"]}" alt="Thumbnail concept {c["n"]}: {e(c["words"])}">
      <div class="feed" aria-label="How it looks at feed sizes">{yt(c["title"], c["img"], 246)}{yt(c["title"], c["img"], 168)}<span class="sz">phone feed 246 px · list 168 px</span></div></div>
    <dl class="notes">{"".join(rows)}</dl>
  </div>{face}{alt}
</article>'''

S = []
if D.get("banner"): S.append(f'<div class="banner">{e(D["banner"])}</div>')
S.append(f'''<div class="top"><span class="eyebrow">{e(D.get("eyebrow", "Thumbnail and title packaging"))}</span><h1>{e(D["headline"])}</h1>
<p class="lede">{e(D["lede"])}</p><div class="move">{"".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in D.get("move", []))}</div></div>''')
if D.get("trio"):
    t = "".join(f'<a class="t" href="#c{x["n"]}"><img src="{x["img"]}" alt=""><span class="lab">{e(x["label"])}</span><b>{e(x["title"])}</b><span>{e(x["why"])}</span></a>' for x in D["trio"])
    S.append(f'<section><span class="eyebrow">Test these three first</span><h2>{e(D.get("trio_head", "Three different reasons to click"))}</h2><p class="sub">{e(D.get("trio_note", ""))}</p><div class="trio">{t}</div></section>')
if D.get("plan"):
    P = D["plan"]; stats = "".join(f"<div><b>{e(a)}</b><span>{e(b)}</span></div>" for a, b in P.get("stats", []))
    src = f'<p class="sub">Source: <a href="{P["source_url"]}">{e(P.get("source_label", "YouTube Help"))}</a>.</p>' if P.get("source_url") else ""
    S.append(f'''<section><span class="eyebrow">Launch and test plan</span><h2>{e(P["head"])}</h2><p class="sub">{e(P.get("note", ""))}</p>
<div class="move stats">{stats}</div><div class="two"><div><h3>What to do</h3><ol>{pairs(P.get("steps", []))}</ol></div>
<div><h3>The rules it rests on</h3><ul>{pairs(P.get("facts", []))}</ul>{src}</div></div>{f'<div class="note">{e(P["caveat"])}</div>' if P.get("caveat") else ""}</section>''')
S.append(f'<section><span class="eyebrow">The concepts</span><h2>{e(D.get("concepts_head", "One click reason each, built to be read in a second"))}</h2><p class="sub">{e(D.get("concepts_note", ""))}</p>{"".join(concept(c) for c in D["concepts"])}</section>')
if D.get("checks"):
    C = D["checks"]; head = "".join(f"<th>{e(h)}</th>" for h in C.get("viewers", []))
    body = "".join(f'<tr><td class="k">{c["n"]}</td><td>{e(c["name"])}</td>' + "".join(f'<td class="n">{e(v)}</td>' for v in c.get("seg", [])) + f'<td>{chip(c["promise"]["cls"], c["promise"]["label"]) if c.get("promise") else ""}</td></tr>' for c in D["concepts"])
    S.append(f'''<section><span class="eyebrow">Checks</span><h2>{e(C.get("head", "What tried to knock these down, and what it found"))}</h2><p class="sub">{e(C.get("note", ""))}</p>
<div class="tablewrap"><table><thead><tr><th></th><th>Concept</th>{head}<th>Promise check</th></tr></thead><tbody>{body}</tbody></table></div>
<div class="two"><div><h3>What the checks found</h3><ul>{pairs(C.get("findings", []))}</ul></div><div><h3>Reasons to doubt this page</h3><ul>{"".join(f"<li>{e(x)}</li>" for x in C.get("doubts", []))}</ul></div></div></section>''')
if D.get("research"):
    Rr = D["research"]; tbl = ""
    if Rr.get("table"):
        th = "".join(f"<th>{e(h)}</th>" for h in Rr["table"]["head"])
        tr = "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in r["cells"]) + (f'<td>{chip(r["cls"], r["verdict"])}</td>' if r.get("verdict") else "") + "</tr>" for r in Rr["table"]["rows"])
        tbl = f'<div class="tablewrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>'
    lists = "".join(f'<div><h3>{e(L["title"])}</h3><ul>{pairs(L["items"])}</ul></div>' for L in Rr.get("lists", []))
    take = '<div class="note">' + e(Rr["take"]) + "</div>" if Rr.get("take") else ""
    S.append(f'<section><span class="eyebrow">Research</span><h2>{e(Rr["head"])}</h2><p class="sub">{e(Rr.get("note", ""))}</p>{tbl}<div class="two">{lists}</div>{take}</section>')
if D.get("titles"):
    tr = "".join(f'<tr><td class="k">{e(a)}</td><td>{e(b)}</td><td>{e(c)}</td></tr>' for a, b, c in D["titles"])
    S.append(f'<section><span class="eyebrow">Titles</span><h2>{e(D.get("titles_head", "Titles to test"))}</h2><div class="tablewrap"><table><thead><tr><th></th><th>Title</th><th>Why</th></tr></thead><tbody>{tr}</tbody></table></div></section>')
if D.get("open"):
    S.append(f'<section><span class="eyebrow">Still open</span><h2>Decisions that are yours</h2><ul>{"".join(f"<li>{e(x)}</li>" for x in D["open"])}</ul></section>')

CSS = '''
:root { --bg:#F5F6F8; --surface:#FFFFFF; --ink:#14171C; --muted:#5A6472; --line:#DDE1E7; --accent:#1F4FD8; --accent-soft:#E7EDFC;
  --good:#187A4E; --ok-soft:#E1F3EA; --warn:#8A5A00; --warn-soft:#FBEFD5; --bad:#B3261E; --bad-soft:#FBE4E2; --yt:#0F0F0F; --yt-ink:#F1F1F1; --yt-muted:#AAAAAA;
  --display:"Space Grotesk","Segoe UI",system-ui,sans-serif; --text:"Inter","Segoe UI",system-ui,sans-serif; --ytfont:"Roboto","Segoe UI",Arial,sans-serif; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg:#0E1013; --surface:#171A1F; --ink:#ECEEF1; --muted:#9BA4B0; --line:#2A2F38; --accent:#86A8FF; --accent-soft:#1B2540; --good:#5FD19B; --ok-soft:#12301F; --warn:#F1C56B; --warn-soft:#33270C; --bad:#FF8A80; --bad-soft:#3A1614; color-scheme:dark } }
:root[data-theme="dark"] { --bg:#0E1013; --surface:#171A1F; --ink:#ECEEF1; --muted:#9BA4B0; --line:#2A2F38; --accent:#86A8FF; --accent-soft:#1B2540; --good:#5FD19B; --ok-soft:#12301F; --warn:#F1C56B; --warn-soft:#33270C; --bad:#FF8A80; --bad-soft:#3A1614; color-scheme:dark }
body { background:var(--bg); color:var(--ink); font:400 16px/1.55 var(--text); }
.wrap { max-width:1180px; margin:0 auto; padding-block:36px 72px; padding-left:max(16px, env(safe-area-inset-left, 0px)); padding-right:max(16px, env(safe-area-inset-right, 0px)); display:flex; flex-direction:column; gap:56px; }
h1,h2,h3 { font-family:var(--display); text-wrap:balance; margin:0; letter-spacing:-0.01em; }
h1 { font-size:clamp(30px,4.6vw,50px); line-height:1.05; font-weight:700; } h2 { font-size:clamp(22px,2.6vw,30px); line-height:1.15; font-weight:600; } h3 { font-size:20px; line-height:1.2; font-weight:600; }
p { margin:0; } a { color:var(--accent); }
.eyebrow { font:600 12px/1 var(--text); letter-spacing:.09em; text-transform:uppercase; color:var(--muted); }
.lede { font-size:18px; max-width:68ch; } .top { display:flex; flex-direction:column; gap:16px; }
.move { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
.move > div { border-top:2px solid var(--ink); padding-top:10px; display:flex; flex-direction:column; gap:4px; min-width:0; }
.move b { font-family:var(--display); font-size:17px; } .move span { color:var(--muted); font-size:14.5px; } .stats b { font-size:26px; font-variant-numeric:tabular-nums; }
section { display:flex; flex-direction:column; gap:18px; } .sub { color:var(--muted); max-width:72ch; }
.trio { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:18px; }
.t { display:flex; flex-direction:column; gap:6px; text-decoration:none; color:inherit; min-width:0; }
.t img { width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:12px; display:block; }
.t .lab { font:600 12px/1 var(--text); letter-spacing:.08em; text-transform:uppercase; color:var(--accent); margin-top:6px; }
.t b { font-family:var(--display); font-size:17px; line-height:1.25; } .t span:last-child { color:var(--muted); font-size:14.5px; }
.t:focus-visible, a:focus-visible { outline:2px solid var(--accent); outline-offset:4px; border-radius:12px; }
.concept { display:flex; flex-direction:column; gap:16px; padding-top:22px; border-top:1px solid var(--line); scroll-margin-top:16px; }
.concept header { display:flex; gap:14px; align-items:baseline; } .num { font:700 30px/1 var(--display); color:var(--muted); font-variant-numeric:tabular-nums; }
.reason { color:var(--muted); font-size:15px; }
.body { display:grid; grid-template-columns:minmax(0,1.25fr) minmax(0,1fr); gap:28px; align-items:start; }
.art { display:flex; flex-direction:column; gap:12px; min-width:0; } .main { width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:14px; display:block; }
.feed { background:var(--yt); border-radius:14px; padding:16px; display:flex; flex-wrap:wrap; gap:18px; align-items:flex-start; }
.yt { margin:0; width:var(--w); max-width:100%; display:flex; flex-direction:column; gap:8px; } .yt img { width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:10px; display:block; }
.yt figcaption { display:flex; gap:8px; } .av { flex:none; width:24px; height:24px; border-radius:50%; background:#3A3F47; }
.tt { display:flex; flex-direction:column; gap:2px; min-width:0; font-family:var(--ytfont); }
.tt b { color:var(--yt-ink); font-weight:500; font-size:13.5px; line-height:1.3; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }
.tt i { color:var(--yt-muted); font-style:normal; font-size:11.5px; } .sz { flex-basis:100%; color:var(--yt-muted); font:400 11.5px/1 var(--ytfont); }
.notes { margin:0; display:flex; flex-direction:column; gap:12px; min-width:0; } .row { display:flex; flex-direction:column; gap:2px; }
dt { font:600 11.5px/1.2 var(--text); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); } dd { margin:0; font-size:15px; }
.words { font:600 19px/1.25 var(--display); } .also, .reads { color:var(--muted); font-size:14px; }
.meter { display:inline-block; width:90px; height:8px; border-radius:4px; background:var(--line); vertical-align:1px; margin-right:8px; overflow:hidden; } .meter span { display:block; height:100%; background:var(--good); }
.chip { font:600 11px/1 var(--text); letter-spacing:.06em; text-transform:uppercase; padding:4px 7px; border-radius:6px; margin-right:6px; white-space:nowrap; }
.chip.ok { background:var(--ok-soft); color:var(--good); } .chip.late { background:var(--warn-soft); color:var(--warn); } .chip.bad { background:var(--bad-soft); color:var(--bad); }
.chip.info { background:var(--line); color:var(--ink); }
.banner { background:var(--warn-soft); color:var(--warn); border-radius:12px; padding:12px 16px; font-weight:600; }
.alt { display:grid; grid-template-columns:minmax(0,300px) minmax(0,1fr); gap:16px; align-items:center; background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px; }
.alt img { width:100%; aspect-ratio:16/9; object-fit:cover; border-radius:8px; display:block; } .alt p { font-size:14.5px; color:var(--muted); }
.facecmp { margin:0 0 12px; background:var(--surface); border:1px solid var(--line); border-radius:12px; padding:12px; }
.facecmp img { width:100%; max-width:1120px; height:auto; border-radius:8px; display:block; margin:0 auto; } .facecmp figcaption { font-size:14.5px; color:var(--muted); margin-top:8px; }
.tablewrap { overflow-x:auto; } table { border-collapse:collapse; width:100%; font-size:14.5px; min-width:560px; }
th,td { text-align:left; padding:9px 12px 9px 0; border-bottom:1px solid var(--line); vertical-align:top; }
th { font:600 11.5px/1.2 var(--text); letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }
td.n { font-variant-numeric:tabular-nums; white-space:nowrap; font-weight:600; } td.k { font-weight:600; white-space:nowrap; color:var(--muted); }
ul { margin:0; padding-left:20px; display:flex; flex-direction:column; gap:8px; max-width:78ch; } ol { margin:0; padding-left:22px; display:flex; flex-direction:column; gap:10px; max-width:78ch; }
.two { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:28px; } .two > div { display:flex; flex-direction:column; gap:12px; min-width:0; }
.note { background:var(--accent-soft); border-radius:12px; padding:14px 16px; font-size:15px; max-width:80ch; }
@media (max-width:860px) { .body,.two,.move,.trio { grid-template-columns:minmax(0,1fr); } .alt { grid-template-columns:minmax(0,1fr); } }
'''
page = (f'<title>{e(D.get("page_title", "Video Packaging"))}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
        '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=Roboto:wght@400;500&display=swap">\n'
        f'<style>\n/* Layout: a review desk. The angle first, then each concept as a wide thumbnail beside its reasoning. */{CSS}</style>\n<div class="wrap">\n' + "\n".join(S) + "\n</div>\n")
open(os.path.join(R, "index.html"), "w", encoding="utf-8", newline="\n").write(page)
print(os.path.join(R, "index.html"), len(page) // 1024, "KB,", len(D["concepts"]), "concepts")
