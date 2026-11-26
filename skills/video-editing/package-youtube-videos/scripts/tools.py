"""Designer helpers. Run from the work folder:  python <skill>/scripts/tools.py <cmd> ...

  sheet  <out.jpg> <img> [<img> ...]            takes side by side (to compare takes at a glance)
  feed   <img> <out.jpg> [--title "..."]        the thumbnail where it will live: a dark YouTube home row among real
                                                current videos from research/thumbs (hits and flops alike), at 3 sizes
                                                (400 / 246 / 168 px)
  face   <img> <out.jpg> [--ref smile|serious]  likeness check at NATIVE pixels: the image's face, never shrunk, beside
                                                one of Leon's reference portraits scaled to the same face height. Pass
                                                the full-size original (out/<id>_full.png). Without --ref it writes
                                                two sheets, <out>_smile and <out>_serious. Prints the face height.
  logo   <img> <out.png> --logo <png> --box x,y,w,h [--rot deg] [--clear [--clear-pad 8]]
                                                paste an OFFICIAL logo (transparent PNG) over a wrong one; x,y,w,h in
                                                pixels of <img>; the logo is fitted inside the box, centred. --clear
                                                first removes the drawn mark (a logo on open ground only), so the
                                                official one goes in at the same size with no fringe of the old colour
  export <img> <out.jpg>                        the 1280x720 REVIEW file (centre-cropped to 16:9, plain downscale, no
                                                sharpening): what goes on the page and into the feed tests. Not for upload.
  upload <full.png> <out.jpg>                   one 3840x2160 UPLOAD file from a full-size original (plain enlargement)
  finals <report/data.json> [final] [--originals out]
                                                the upload folder, every time: each image on the page at 3840x2160 (made
                                                from its full-size original in out/), named by concept number and the
                                                title it is paired with (03-<title-in-hyphens>.jpg, ...-alt.jpg), plus
                                                TEST_ORDER.txt (which to upload first, each title, and every file's concept)

Nothing here may touch Leon himself: `logo` is the only command that alters pixels, and only for a logo.
"""
import sys, os, glob, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
HERE = os.getcwd()                                                   # the work folder
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def font(sz, bold=True):
    for p in ("C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf"):
        try: return ImageFont.truetype(p, sz)
        except Exception: pass
    return ImageFont.load_default()
def fit169(im):
    w, h = im.size
    if w / h > 16 / 9: nw = int(h * 16 / 9); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    elif w / h < 16 / 9: nh = int(w * 9 / 16); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    return im
def opt(n, d=None): return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d

def sheet(out, files):
    ims = [fit169(Image.open(f).convert("RGB")) for f in files]; w = 900; h = int(w * 9 / 16); pad = 10; lab = 30
    cols = 2 if len(ims) > 1 else 1; rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + lab + pad) + pad), (20, 20, 20)); d = ImageDraw.Draw(S)
    for i, im in enumerate(ims):
        x = pad + (i % cols) * (w + pad); y = pad + (i // cols) * (h + lab + pad)
        S.paste(im.resize((w, h), Image.LANCZOS), (x, y)); d.text((x + 4, y + h + 4), os.path.basename(files[i]), fill=(240, 240, 240), font=font(18))
    S.save(out, quality=90); print(out, S.size)

def feed(img, out, title):
    me = fit169(Image.open(img).convert("RGB"))
    pool = sorted(glob.glob(os.path.join(HERE, "research", "thumbs", "*.jpg")))
    if not pool: sys.exit("feed: no thumbnails in research/thumbs/ yet (fetch the research pool first)")
    random.seed(os.path.basename(img)); others = random.sample(pool, 5) if len(pool) >= 5 else [pool[i % len(pool)] for i in range(5)]
    BG = (15, 15, 15); W = 1320; S = Image.new("RGB", (W, 1010), BG); d = ImageDraw.Draw(S)
    # row 1: desktop home, 3 x 400px tiles; ours in the middle
    def tile(im, x, y, w, t):
        h = int(w * 9 / 16); r = fit169(im).resize((w, h), Image.LANCZOS)
        m = Image.new("L", (w, h), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, w, h), radius=max(6, w // 30), fill=255)
        S.paste(r, (x, y), m)
        if t: d.text((x + 2, y + h + 8), t[: int(w / 8.6)], fill=(241, 241, 241), font=font(max(12, w // 24)))
        return h
    row = [Image.open(others[0]).convert("RGB"), me, Image.open(others[1]).convert("RGB")]
    for i, im in enumerate(row): tile(im, 30 + i * 430, 24, 400, title if i == 1 else "")
    d.text((30, 300), "desktop home, 400 px", fill=(140, 140, 140), font=font(14, False))
    row = [Image.open(others[2]).convert("RGB"), Image.open(others[3]).convert("RGB"), me, Image.open(others[4]).convert("RGB"), Image.open(others[0]).convert("RGB")]
    for i, im in enumerate(row): tile(im, 30 + i * 256, 340, 246, title if i == 2 else "")
    d.text((30, 520), "mobile feed, 246 px", fill=(140, 140, 140), font=font(14, False))
    row = [Image.open(o).convert("RGB") for o in others[:3]] + [me] + [Image.open(o).convert("RGB") for o in others[3:]]
    for i, im in enumerate(row): tile(im, 30 + i * 178, 560, 168, "")
    d.text((30, 664), "sidebar / phone list, 168 px", fill=(140, 140, 140), font=font(14, False))
    # light mode strip
    L = Image.new("RGB", (W, 290), (255, 255, 255)); S.paste(L, (0, 720)); 
    for i, im in enumerate([Image.open(others[1]).convert("RGB"), me, Image.open(others[4]).convert("RGB")]):
        h = int(400 * 9 / 16); S.paste(fit169(im).resize((400, h), Image.LANCZOS), (30 + i * 430, 750))
    S.save(out, quality=88); print(out, S.size)

def face(img, out, which):
    """The image's face at its NATIVE pixels (never shrunk: a shrunk face hides what Leon sees at once), beside one
    reference portrait scaled to the same face height. One reference per sheet, so the sheet stays small enough to be
    viewed without being downscaled. Pass the full-size original (out/<id>_full.png), not the 1280 export."""
    import cv2, numpy as np
    model = os.path.join(SKILL, "assets", "models", "face_detection_yunet_2023mar.onnx")
    def crop(path, scale_to=None):
        im = Image.open(path).convert("RGB"); a = cv2.cvtColor(np.array(im), cv2.COLOR_RGB2BGR); h, w = a.shape[:2]
        det = cv2.FaceDetectorYN.create(model, "", (w, h), 0.6); _, f = det.detect(a)
        if f is None or len(f) == 0: return None, None, None
        x, y, fw, fh = max(f, key=lambda r: r[2] * r[3])[:4]
        m = 0.30; box = (int(max(0, x - fw * m)), int(max(0, y - fh * (m + 0.30))), int(min(w, x + fw * (1 + m))), int(min(h, y + fh * (1 + m))))
        c = im.crop(box); s = 1.0
        if scale_to: s = scale_to / fh; c = c.resize((max(1, int(c.width * s)), max(1, int(c.height * s))), Image.LANCZOS)
        return c, fh, 100 * fh / h
    refs = {"smile": os.path.join(HERE, "refs", "leon", "leon_front.jpg"), "serious": os.path.join(HERE, "refs", "leon", "leon_serious.png")}
    mine, fh, pct = crop(img)
    if mine is None: print(out, "NO FACE DETECTED in", img); sys.exit(1)
    stem, ext = os.path.splitext(out)
    for k in (["smile", "serious"] if which == "both" else [which]):
        ref, rfh, _ = crop(refs[k], scale_to=fh)
        tiles = [(mine, "THIS IMAGE, native pixels (100%)"), (ref, "REFERENCE (%s), scaled x%.2f to match" % (k, fh / rfh))]
        H = max(t.height for t, _ in tiles)
        S = Image.new("RGB", (sum(t.width for t, _ in tiles) + 30, H + 50), (20, 20, 20)); d = ImageDraw.Draw(S); x = 10
        for t, lab in tiles: S.paste(t, (x, 10)); d.text((x + 4, H + 16), lab, fill=(240, 240, 240), font=font(20)); x += t.width + 10
        o = out if which != "both" else f"{stem}_{k}{ext}"
        S.save(o, quality=95)
        warn = "  WARNING: larger than 2000 px, a viewer may shrink it; crop tighter or view in halves" if max(S.size) > 2000 else ""
        print(o, S.size, "face height = %.0f%% of the frame (%d px), shown at native size%s" % (pct, fh, warn))

def logo(img, out):
    base = Image.open(img).convert("RGBA"); lg = Image.open(opt("--logo")).convert("RGBA")
    x, y, w, h = [int(float(v)) for v in opt("--box").split(",")]; rot = float(opt("--rot", 0))
    if "--clear" in sys.argv:
        # Remove the mark the image model drew before pasting the official one, so no fringe of the old colour shows
        # and the official mark can go in at the drawn mark's own size. Works on a plain or smoothly shaded ground:
        # everything inside the box (plus a margin) that is not ground colour is filled in from its surroundings.
        # Never point this at anything but a logo on open ground: it must not reach his face, hair, body or any text.
        import numpy as np, cv2
        pad = int(opt("--clear-pad", 8)); W_, H_ = base.size
        x0, y0, x1, y1 = max(0, x - pad), max(0, y - pad), min(W_, x + w + pad), min(H_, y + h + pad)
        a = np.array(base.convert("RGB")); reg = a[y0:y1, x0:x1].astype(np.int32)
        ring = np.concatenate([reg[:3].reshape(-1, 3), reg[-3:].reshape(-1, 3), reg[:, :3].reshape(-1, 3), reg[:, -3:].reshape(-1, 3)])
        ground = np.median(ring, axis=0)
        if (np.abs(ring - ground).sum(axis=1) < 40).mean() < 0.6: sys.exit("logo --clear: the box is not on open ground (less than 60% of its border is one colour). Paste without --clear.")
        # the old mark's colour: the commonest non-ground colour in the middle of the box
        mid = a[y + h // 4: y + 3 * h // 4, x + w // 4: x + 3 * w // 4].reshape(-1, 3).astype(np.int32)
        mid = mid[np.abs(mid - ground).sum(axis=1) > 60]
        if len(mid) < 50: sys.exit("logo --clear: found no mark in the middle of the box; check --box.")
        d = np.median(mid, axis=0) - ground; v = reg - ground
        t = (v * d).sum(axis=2) / float((d * d).sum()); resid = np.sqrt(((v - t[..., None] * d) ** 2).sum(axis=2))
        # only pixels that lie on the line from ground colour to mark colour (the mark and its soft edge): text, other
        # shapes and anything of another colour inside the box are left alone
        soft = ((t > 0.12) & (resid < 45)).astype(np.uint8); core = (t > 0.6) & (resid < 45)
        # keep only the pieces that contain solid mark colour. The soft edges of neighbouring letters and shapes also
        # pass the colour test at their darkest pixels, and filling those in nibbles the neighbours (it did, once).
        n, lab = cv2.connectedComponents(soft, connectivity=8)
        keep = np.unique(lab[core]); mask = (np.isin(lab, keep[keep > 0])).astype(np.uint8) * 255
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1); mask[:2] = 0; mask[-2:] = 0; mask[:, :2] = 0; mask[:, -2:] = 0
        full = np.zeros(a.shape[:2], np.uint8); full[y0:y1, x0:x1] = mask
        a = cv2.inpaint(cv2.cvtColor(a, cv2.COLOR_RGB2BGR), full, 5, cv2.INPAINT_TELEA)
        base = Image.fromarray(cv2.cvtColor(a, cv2.COLOR_BGR2RGB)).convert("RGBA")
        print("cleared %d px of the old mark inside %d,%d,%d,%d (ground %s)" % (int((full > 0).sum()), x0, y0, x1 - x0, y1 - y0, [int(v) for v in ground]))
    s = min(w / lg.width, h / lg.height); lg = lg.resize((max(1, int(lg.width * s)), max(1, int(lg.height * s))), Image.LANCZOS)
    if rot: lg = lg.rotate(rot, expand=True, resample=Image.BICUBIC)
    base.alpha_composite(lg, (x + (w - lg.width) // 2, y + (h - lg.height) // 2)); base.convert("RGB").save(out); print(out)

def export(img, out):
    im = fit169(Image.open(img).convert("RGB")).resize((1280, 720), Image.LANCZOS)   # no sharpening: it made skin look crunchy
    im.save(out, quality=93, subsampling=0); print(out, im.size, "%d KB" % (os.path.getsize(out) // 1024))

UPLOAD = (3840, 2160)   # YouTube's recommended thumbnail size. Leon, 2026-11-23: "We need the 4K versions ... every time"
def upload(img, out):
    """The upload file: 3840x2160, a plain enlargement of the full-size original. No sharpening and no AI upscaler (an
    upscaler redraws his face). Kept under 2 MB, the limit for uploading from a phone."""
    im = fit169(Image.open(img).convert("RGB"))
    if im.width < 1600: print(f"WARNING: {img} is only {im.width} px wide. Pass the full-size original, not the 1280 export.")
    big = im.resize(UPLOAD, Image.LANCZOS); q = 92
    while True:
        big.save(out, quality=q, subsampling=0)
        if os.path.getsize(out) <= 1_950_000 or q <= 76: break
        q -= 4
    print(out, "%dx%d" % big.size, "%.2f MB" % (os.path.getsize(out) / 1e6), f"(enlarged from {im.width}x{im.height}, quality {q})")

def finals(data, out, originals="out"):
    """The upload folder: only the current files, at 3840x2160, named by number and paired title, with the test order.
    Built from the page's own data, so what he uploads is what he reviewed: each image on the page is matched, byte for
    byte, to its export in out/, and the upload file is made from that export's full-size original. Stops if any page
    image has no original, so a 4K file is never silently missing. Clears what it wrote before."""
    import json, re, hashlib
    D = json.load(open(data, encoding="utf-8")); src = os.path.dirname(os.path.abspath(data)); os.makedirs(out, exist_ok=True)
    for f in glob.glob(os.path.join(out, "*.jpg")) + glob.glob(os.path.join(out, "TEST_ORDER.txt")): os.remove(f)
    def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()
    exports = {md5(f): f[:-4] + "_full.png" for f in glob.glob(os.path.join(originals, "*.jpg"))}
    def full_of(page_img):
        k = exports.get(md5(os.path.join(src, page_img)))
        if not k or not os.path.exists(k):
            sys.exit(f"finals: {page_img} on the page is not an unchanged copy of an export in {originals}/ with its full-size "
                     f"original ({originals}/<id>_full.png) beside it. Every delivered image needs that original: the 3840x2160 "
                     "upload file is made from it. Nothing was written.")
        return k
    def slug(s, n=80):                                        # "It's "Fixed"" -> its-fixed: lower case, hyphens, ASCII only
        import unicodedata
        s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower().replace("&", " and ")
        s = re.sub(r"[^a-z0-9]+", "-", re.sub(r"['\"`]", "", s)).strip("-")
        return s if len(s) <= n else s[:n].rsplit("-", 1)[0]
    # File names carry the number and the TITLE the thumbnail is paired with (Leon, 2026-11-23: "The file names for the
    # thumbnails need to include the video's title ... you can keep the number, like 01"). A thumbnail in the test trio
    # takes the title the test plan pairs it with; the others take their concept's own title.
    trio_title = {t["n"]: t["title"] for t in D.get("trio", [])}
    names = {}; jobs = []; index = []
    for c in D["concepts"]:                                   # resolve every original first: all or nothing
        title = trio_title.get(c["n"]) or c["title"]; base = f'{c["n"]}-{slug(title)}'
        names[c["n"]] = base + ".jpg"; jobs.append((full_of(c["img"]), names[c["n"]])); index.append((names[c["n"]], c["name"], title))
        if c.get("alt_img"):                                  # "alt_suffix": "bright" names the file -bright.jpg (the main file is the dark one)
            suf = slug(c.get("alt_suffix") or "alt", 20) or "alt"; label = c.get("alt_label") or "alternative version"
            jobs.append((full_of(c["alt_img"]), f"{base}-{suf}.jpg")); index.append((f"{base}-{suf}.jpg", c["name"] + f" ({label.lower()})", title))
    if len({n for _, n in jobs}) < len(jobs): sys.exit("finals: two upload files would get the same name; give the concepts different numbers. Nothing was written.")
    for full, name in jobs: upload(full, os.path.join(out, name))
    lines = ["Every file here is 3840x2160, YouTube's recommended thumbnail size.", "",
             "Test & Compare: upload in this order. With no clear winner, YouTube keeps the FIRST one.", ""]
    titles = [t["title"] for t in D.get("trio", [])]
    if len(set(titles)) < len(titles): print("WARNING: two packages in the trio share a title; a combined test needs a different title for each")
    for k, t in enumerate(D.get("trio", [])):
        lines += [f'{"ABC"[k] if k < 3 else k + 1}. {names.get(t["n"], "?")}', f'   Title: {t["title"]}', ""]
    lines += ["", "Every file, by concept (the file name is the concept's number, then the title it is paired with):", ""]
    for name, concept, title in index: lines += [f"{name}", f"   {concept}  |  {title}", ""]
    open(os.path.join(out, "TEST_ORDER.txt"), "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print(out, sorted(os.listdir(out)))

if __name__ == "__main__":
    c = sys.argv[1] if len(sys.argv) > 1 else ""
    if c == "sheet": sheet(sys.argv[2], sys.argv[3:])
    elif c == "feed": feed(sys.argv[2], sys.argv[3], opt("--title", ""))
    elif c == "face": face(sys.argv[2], sys.argv[3], opt("--ref", "both"))
    elif c == "logo": logo(sys.argv[2], sys.argv[3])
    elif c == "export": export(sys.argv[2], sys.argv[3])
    elif c == "upload": upload(sys.argv[2], sys.argv[3])
    elif c == "finals": finals(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else "final", opt("--originals", "out"))
    else: print(__doc__)
