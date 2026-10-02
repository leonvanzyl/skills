"""Thumbnail QA: normalise to YouTube spec, then build the sheets you LOOK at before calling anything done.

  python qa.py contact <out.png> <thumbs.json> <dir> [--group niche] [--width 480]
        -> research contact sheet: labelled grid (rank, views, breakout, channel, title). --width 246 = real mobile-feed size
  python qa.py compare <out.png> <jobs.json>
        -> one row per concept: its LAYOUT REFERENCE outlier, then every render of it
  python qa.py faces <out.png> <avatar> <img>:<x0,y0,x1,y1> [...] [--avatar-box x0,y0,x1,y1]
        -> the avatar next to a face crop (fractions of the frame) of each render, for the likeness check
  python qa.py ladder <out.png> <img> [<img> ...] [--dur 10:44]
        -> each candidate at 480 / 246 (mobile feed) / 168 (sidebar) px + greyscale, with the duration badge
  python qa.py feed <out.png> --cands a.jpg [b.jpg] --field DIR [--pattern 'bo*.jpg'] [--title T] [--channel C] [--dur 10:44]
        -> a dark-mode YouTube feed mock: each candidate dropped between real niche thumbnails at desktop-home size (360 px),
           plus a mobile search / sidebar row (168 px)
  python qa.py card <out.png> <thumbnail> --title "<title>" [--channel C] [--dur 10:44]
        -> one feed card (thumbnail at 480 px, title and channel underneath) for the stranger test (review.md)
  python qa.py norm <in.png> <out-stem>
        -> <out-stem>.jpg (1280x720, <2 MB) + <out-stem>_master.png (1920x1080)
"""
import argparse, glob, io, json, os, random
from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIRS = [os.path.join(HERE, '..', 'assets', 'fonts'), 'C:/Windows/Fonts', '/usr/share/fonts/truetype/dejavu', '/Library/Fonts']


def font(size, bold=False):
    names = (['Poppins-SemiBold.ttf', 'segoeuib.ttf', 'arialbd.ttf', 'DejaVuSans-Bold.ttf'] if bold
             else ['Poppins-Regular.ttf', 'segoeui.ttf', 'arial.ttf', 'DejaVuSans.ttf'])
    for d in FONT_DIRS:
        for n in names:
            p = os.path.join(d, n)
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def fit169(im, w, h=None):
    """Centre-crop to exactly 16:9, then Lanczos-resize."""
    h = h or round(w * 9 / 16)
    return ImageOps.fit(im.convert('RGB'), (w, h), Image.LANCZOS, centering=(0.5, 0.5))


def badge(im, text, scale=1.0):
    """YouTube's duration badge, bottom-right, so you see what it covers. Like the real one it has a minimum size,
    so on a 168 px sidebar thumbnail it covers more than the 18% x 15% keep-clear zone. That is real, not a bug."""
    d = ImageDraw.Draw(im)
    f = font(max(9, int(12 * scale)), True)
    tw = d.textlength(text, font=f)
    pad, bh = 4 * scale, 18 * scale
    x1, y1 = im.width - 6 * scale, im.height - 6 * scale
    d.rounded_rectangle([x1 - tw - 2 * pad, y1 - bh, x1, y1], radius=4 * scale, fill=(0, 0, 0, 220))
    d.text((x1 - pad - tw, y1 - bh + 1 * scale), text, font=f, fill='white')
    return im


def norm(src, stem):
    im = Image.open(src)
    fit169(im, 1920).save(stem + '_master.png')
    small = fit169(im, 1280)
    for q in (95, 92, 90, 87, 85, 80):
        buf = io.BytesIO()
        small.save(buf, 'JPEG', quality=q, optimize=True, progressive=True)
        if buf.tell() < 2_000_000:
            break
    open(stem + '.jpg', 'wb').write(buf.getvalue())
    print(f'{stem}.jpg  1280x720  q{q}  {buf.tell() / 1e6:.2f} MB   (source {im.size[0]}x{im.size[1]})')
    # provenance for report.py: deliverable -> the file it was made from
    man = os.path.join(os.path.dirname(os.path.abspath(stem)), 'manifest.json')
    m = json.load(open(man, encoding='utf-8')) if os.path.exists(man) else {}
    m[os.path.basename(stem)] = dict(source=src.replace('\\', '/'))
    json.dump(m, open(man, 'w', encoding='utf-8'), indent=1)


def ladder(out, imgs, dur='10:44'):
    sizes = [480, 246, 168]
    rows = []
    for p in imgs:
        im = Image.open(p)
        tiles = [badge(fit169(im, w), dur, w / 360) for w in sizes]
        tiles.append(ImageOps.grayscale(fit169(im, 246)).convert('RGB'))
        rows.append((os.path.basename(p), tiles))
    W = 24 + sum(t.width + 24 for t in rows[0][1])
    H = sum(48 + max(t.height for t in r[1]) + 24 for r in rows)
    sheet = Image.new('RGB', (W, H), (15, 15, 15))
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, tiles in rows:
        d.text((24, y + 12), f'{name}    480 / 246 (mobile feed) / 168 (sidebar) / greyscale', font=font(20, True), fill=(240, 240, 240))
        x = 24
        for t in tiles:
            sheet.paste(t, (x, y + 48))
            x += t.width + 24
        y += 48 + max(t.height for t in tiles) + 24
    sheet.save(out)
    print(out, sheet.size)


def card(thumb, w, title, channel, dur, scale):
    th = badge(fit169(thumb, w), dur, w / 360)
    tf, cf = font(int(15 * scale) + 1, True), font(int(13 * scale) + 1)
    h = th.height + int(70 * scale)
    c = Image.new('RGB', (w, h), (15, 15, 15))
    c.paste(th, (0, 0))
    d = ImageDraw.Draw(c)
    words, line, lines = title.split(), '', []
    for wd in words:
        if d.textlength((line + ' ' + wd).strip(), font=tf) > w - 8:
            lines.append(line)
            line = wd
        else:
            line = (line + ' ' + wd).strip()
    lines.append(line)
    y = th.height + int(8 * scale)
    for ln in lines[:2]:
        d.text((0, y), ln, font=tf, fill=(241, 241, 241))
        y += int(20 * scale)
    d.text((0, y + 2), channel, font=cf, fill=(170, 170, 170))
    return c


def feed(out, cands, field, title, channel, dur, pattern='*.jpg'):
    pool = sorted(p for p in glob.glob(os.path.join(field, pattern)) if 'CURRENT' not in os.path.basename(p))
    random.Random(7).shuffle(pool)
    W, cw, gap = 24 * 4 + 360 * 3, 360, 24
    rows = []
    for i, c in enumerate(cands):
        others = pool[i * 5:(i * 5) + 5] or pool[:5]
        cells = [(Image.open(o), '…niche video', os.path.basename(o).split('_')[1] if '_' in os.path.basename(o) else '', '12:03') for o in others]
        cells.insert(1, (Image.open(c), title, channel, dur))
        rows.append((os.path.basename(c), cells))
    blocks = []
    for name, cells in rows:
        cards = [card(im, cw, t, ch, du, 1.0) for im, t, ch, du in cells[:6]]
        grid_h = 2 * (cards[0].height + gap)
        mob = [card(im, 168, '', '', du, 0.47) for im, t, ch, du in cells[:6]]
        b = Image.new('RGB', (W, 44 + grid_h + 40 + mob[0].height + 24), (15, 15, 15))
        d = ImageDraw.Draw(b)
        d.text((24, 10), f'{name}: desktop home (360 px) and mobile search / sidebar (168 px). Candidate is 2nd.', font=font(18, True), fill=(255, 210, 120))
        for k, cd in enumerate(cards):
            b.paste(cd, (24 + (k % 3) * (cw + gap), 44 + (k // 3) * (cd.height + gap)))
        y = 44 + grid_h + 40
        for k, m in enumerate(mob):
            b.paste(m.crop((0, 0, 168, 95)), (24 + k * (168 + 16), y))
        blocks.append(b)
    sheet = Image.new('RGB', (W, sum(b.height for b in blocks)), (15, 15, 15))
    y = 0
    for b in blocks:
        sheet.paste(b, (0, y))
        y += b.height
    sheet.save(out)
    print(out, sheet.size)


def grid(out, tiles, cols, gap=16):
    """tiles: [(label, image)] -> labelled grid on dark grey."""
    tw = tiles[0][1].width
    lab = font(max(14, tw // 26), True)
    lh = lab.size + 10
    rows = (len(tiles) + cols - 1) // cols
    th = max(t.height for _, t in tiles)
    sheet = Image.new('RGB', (gap + cols * (tw + gap), gap + rows * (th + lh + gap)), (15, 15, 15))
    d = ImageDraw.Draw(sheet)
    for k, (label, t) in enumerate(tiles):
        x, y = gap + (k % cols) * (tw + gap), gap + (k // cols) * (th + lh + gap)
        d.text((x, y), label, font=lab, fill=(255, 210, 120))
        sheet.paste(t, (x, y + lh))
    sheet.save(out)
    print(out, sheet.size)


def contact(out, thumbs, folder, group, width):
    items = [t for t in json.load(open(thumbs, encoding='utf-8')) if not group or t.get('group') == group]
    items.sort(key=lambda t: (t.get('group', ''), t.get('rank', 0)))
    tiles = []
    for t in items:
        p = os.path.join(folder, t['file'])
        if not os.path.exists(p):
            continue
        im = fit169(Image.open(p), width)
        if width >= 360:
            bo = t.get('breakout')
            label = f"#{t.get('rank', '')} {t.get('views', 0) / 1000:.0f}k | BO {bo:.1f}x | {t.get('channel', '')}" if bo else \
                    f"#{t.get('rank', '')} {t.get('views', 0) / 1000:.0f}k | {t.get('channel', '')}"
            cap = Image.new('RGB', (width, 28), (15, 15, 15))
            ImageDraw.Draw(cap).text((0, 4), t.get('title', '')[:70], font=font(15), fill=(200, 200, 200))
            full = Image.new('RGB', (width, im.height + 28), (15, 15, 15))
            full.paste(im, (0, 0)); full.paste(cap, (0, im.height))
            tiles.append((label, full))
        else:
            tiles.append((f"#{t.get('rank', '')}", badge(im, '12:03', width / 360)))
    grid(out, tiles, 4 if width >= 360 else 6)


def compare(out, jobs_file):
    """One row per concept: the LAYOUT REFERENCE it borrows from, then each of its renders."""
    jobs = json.load(open(jobs_file, encoding='utf-8'))
    base = os.path.dirname(os.path.abspath(jobs_file))
    rows = {}
    for j in jobs:
        key = j['id'].rstrip('ab') if j['id'][-1] in 'ab' else j['id']
        ref = next((r[0] for r in j.get('refs', []) if r[1].upper().startswith('LAYOUT')), None)
        row = rows.setdefault(key, [('LAYOUT REF', ref)] if ref else [])
        row.append((j['id'], j['out']))
    tiles, cols = [], max(len(r) for r in rows.values())
    for row in rows.values():
        for k in range(cols):
            if k < len(row) and os.path.exists(os.path.join(base, row[k][1])):
                tiles.append((row[k][0], fit169(Image.open(os.path.join(base, row[k][1])), 600)))
            else:
                tiles.append(('', Image.new('RGB', (600, 338), (15, 15, 15))))
    grid(out, tiles, cols)


def faces(out, avatar, specs, avatar_box=None):
    H = 420
    av = Image.open(avatar).convert('RGB')
    if avatar_box:
        x0, y0, x1, y1 = (float(v) for v in avatar_box.split(','))
        av = av.crop((int(x0 * av.width), int(y0 * av.height), int(x1 * av.width), int(y1 * av.height)))
    elif av.width > av.height:   # a landscape portrait: keep the centre, where the face is
        av = av.crop((int(av.width * 0.3), 0, int(av.width * 0.7), av.height))
    ims = [('avatar', av.resize((int(av.width * H / av.height), H), Image.LANCZOS))]
    for s in specs:
        path, box = s.rsplit(':', 1)
        x0, y0, x1, y1 = (float(v) for v in box.split(','))
        im = Image.open(path).convert('RGB')
        c = im.crop((int(x0 * im.width), int(y0 * im.height), int(x1 * im.width), int(y1 * im.height)))
        ims.append((os.path.basename(path), c.resize((int(c.width * H / c.height), H), Image.LANCZOS)))
    sheet = Image.new('RGB', (sum(i.width + 12 for _, i in ims) + 12, H + 44), (15, 15, 15))
    d = ImageDraw.Draw(sheet)
    x = 12
    for label, i in ims:
        d.text((x, 8), label, font=font(18, True), fill=(255, 210, 120))
        sheet.paste(i, (x, 40))
        x += i.width + 12
    sheet.save(out)
    print(out, sheet.size)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['contact', 'compare', 'faces', 'ladder', 'feed', 'card', 'norm'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--cands', nargs='+')
    ap.add_argument('--field')
    ap.add_argument('--title', default='(your video title)')
    ap.add_argument('--channel', default='(your channel)')
    ap.add_argument('--dur', default='10:44')
    ap.add_argument('--pattern', default='*.jpg', help='which field thumbnails to use, e.g. "bo*.jpg" for niche outliers only')
    ap.add_argument('--group', default=None)
    ap.add_argument('--width', type=int, default=480)
    ap.add_argument('--avatar-box', default=None, help='faces: crop of the avatar, fractions x0,y0,x1,y1 (default: centre 40%% of a landscape photo)')
    a = ap.parse_args()
    if a.cmd == 'contact':
        contact(a.args[0], a.args[1], a.args[2], a.group, a.width)
    elif a.cmd == 'compare':
        compare(a.args[0], a.args[1])
    elif a.cmd == 'faces':
        faces(a.args[0], a.args[1], a.args[2:], a.avatar_box)
    elif a.cmd == 'card':
        c = card(Image.open(a.args[1]), 480, a.title, a.channel, a.dur, 480 / 360)
        os.makedirs(os.path.dirname(os.path.abspath(a.args[0])), exist_ok=True)
        c.save(a.args[0])
        print(a.args[0], c.size)
    elif a.cmd == 'norm':
        norm(a.args[0], a.args[1])
    elif a.cmd == 'ladder':
        ladder(a.args[0], a.args[1:], a.dur)
    else:
        feed(a.args[0], a.cands, a.field, a.title, a.channel, a.dur, a.pattern)
