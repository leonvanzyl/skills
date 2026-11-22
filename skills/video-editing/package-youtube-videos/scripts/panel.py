"""Blind read test sheets.   python panel.py <ours.tsv> <panel dir> [--appear 2] [--per 1]

Run from the work folder. ours.tsv: id<TAB>title<TAB>image path (one finished thumbnail per line, with the title it
pairs with). Real competitors come from research/pool.tsv (video id first, title last on each line) with thumbnails
in research/thumbs/.
Each sheet is a dark YouTube home grid of 12 tiles (thumbnail, then its number and title underneath, so nothing covers
a thumbnail): `per` of ours among real videos. Keep `per` at 1: with two of ours on a sheet, each showing the same
man, viewer agents spotted the test items and tapped them 73 to 90% of the time (first run). Every one of ours
appears `appear` times; with per > 1 a sheet never holds two versions of one concept (same first 3 characters of the
id) or two entries with the same title.
Writes <panel dir>/sheets/sheet_N.jpg (the only folder a viewer agent may open) and <panel dir>/key.json (sheet ->
tile number -> our id, or 'real:<video id>'), which stays outside it. Give each viewer agent at most six sheets.
"""
import sys, os, json, random
from PIL import Image, ImageDraw, ImageFont
def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d
def font(sz):
    for p in ("C:/Windows/Fonts/segoeuib.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
def fit169(im):
    w, h = im.size
    if w / h > 16 / 9: nw = int(h * 16 / 9); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < 16 / 9: nh = int(w * 9 / 16); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im
if len(sys.argv) < 3: sys.exit(__doc__)
real = {}
for l in open(os.path.join("research", "pool.tsv"), encoding="utf-8"):
    p = l.rstrip("\n").split("\t")
    if len(p) > 1 and os.path.exists(os.path.join("research", "thumbs", p[0] + ".jpg")): real[p[0]] = p[-1]
ours = [l.rstrip("\n").split("\t") for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
out = sys.argv[2]; sheets_dir = os.path.join(out, "sheets"); os.makedirs(sheets_dir, exist_ok=True)
per = int(opt("--per", 1)); appear = int(opt("--appear", 2)); rnd = random.Random(7)
if len(real) < 12 - per: sys.exit(f"only {len(real)} real videos with thumbnails in the pool; a sheet needs {12 - per}")
if len(real) < 30: print(f"WARNING: only {len(real)} real videos in the pool; 60+ gives a fairer feed")
if per > 1: print("WARNING: more than one of ours per sheet makes the test items easy to spot; taps will not mean much")
n_sheets = (len(ours) * appear + per - 1) // per
for attempt in range(2000):
    left = {o[0]: appear for o in ours}; plan = []; ok = True
    for k in range(n_sheets):
        sheet = []
        for o in sorted(ours, key=lambda o: (-left[o[0]], rnd.random())):
            if len(sheet) == per: break
            if left[o[0]] <= 0 or any(o[0][:3] == m[0][:3] or o[1] == m[1] for m in sheet): continue
            sheet.append(o); left[o[0]] -= 1
        if not sheet: ok = False; break
        plan.append(sheet)
    if ok and all(v == 0 for v in left.values()): break
rnd.shuffle(plan)                                          # so versions of one concept do not land on neighbouring sheets
def wrap(d, text, f, width):
    lines = []; cur = ""
    for w in text.split():
        if d.textlength((cur + " " + w).strip(), font=f) <= width: cur = (cur + " " + w).strip()
        else: lines.append(cur); cur = w
    lines.append(cur); return lines[:2]
key = {}
for k, mine in enumerate(plan):
    reals = rnd.sample(sorted(real), 12 - len(mine))
    tiles = [("ours", m) for m in mine] + [("real", r) for r in reals]; rnd.shuffle(tiles)
    TW = 380; TH = int(TW * 9 / 16); pad = 22; cap = 74
    S = Image.new("RGB", (4 * (TW + pad) + pad, 3 * (TH + cap + pad) + pad), (15, 15, 15)); d = ImageDraw.Draw(S)
    key[f"sheet_{k + 1}"] = {}
    for i, (kind, t) in enumerate(tiles):
        x = pad + (i % 4) * (TW + pad); y = pad + (i // 4) * (TH + cap + pad)
        if kind == "ours": im = Image.open(t[2]); title = t[1]; key[f"sheet_{k + 1}"][str(i + 1)] = t[0]
        else: im = Image.open(os.path.join("research", "thumbs", t + ".jpg")); title = real[t]; key[f"sheet_{k + 1}"][str(i + 1)] = "real:" + t
        im = fit169(im.convert("RGB")).resize((TW, TH), Image.LANCZOS)
        m = Image.new("L", (TW, TH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, TW, TH), radius=12, fill=255); S.paste(im, (x, y), m)
        d.rounded_rectangle((x, y + TH + 9, x + 34, y + TH + 37), radius=7, fill=(62, 66, 74)); d.text((x + (9 if i < 9 else 4), y + TH + 10), str(i + 1), fill=(255, 255, 255), font=font(19))
        for j, line in enumerate(wrap(d, title, font(19), TW - 48)): d.text((x + 44, y + TH + 10 + j * 26), line, fill=(241, 241, 241), font=font(19))
    S.save(os.path.join(sheets_dir, f"sheet_{k + 1}.jpg"), quality=90)
json.dump(key, open(os.path.join(out, "key.json"), "w"), indent=1)
print("sheets:", len(plan), "in", sheets_dir, "| real pool:", len(real), "| at most six sheets per viewer agent")
