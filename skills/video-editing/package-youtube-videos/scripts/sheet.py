"""Contact sheet with captions.  sheet.py out.jpg cols tile_w list.tsv dir   (tsv: id<TAB>caption...)"""
import sys, os
from PIL import Image, ImageDraw, ImageFont
out, cols, w, tsv, d = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
rows = [l.rstrip("\n").split("\t") for l in open(tsv, encoding="utf-8") if l.strip()]
h = int(w*9/16); pad = 8; lab = 34
try: font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 13)
except Exception: font = ImageFont.load_default()
n = len(rows); R = (n+cols-1)//cols
S = Image.new("RGB", (cols*(w+pad)+pad, R*(h+lab+pad)+pad), (15,15,15)); dr = ImageDraw.Draw(S)
for i, r in enumerate(rows):
    f = os.path.join(d, r[0]+".jpg")
    x = pad+(i%cols)*(w+pad); y = pad+(i//cols)*(h+lab+pad)
    try:
        im = Image.open(f).convert("RGB")
        iw, ih = im.size
        if abs(iw/ih-16/9) > .05:  # hqdefault 4:3 letterbox -> crop centre 16:9
            nh = int(iw*9/16); im = im.crop((0,(ih-nh)//2,iw,(ih-nh)//2+nh))
        S.paste(im.resize((w,h), Image.LANCZOS), (x,y))
    except Exception as e:
        dr.text((x+4,y+4), "missing "+r[0], fill=(255,80,80), font=font)
    cap = " | ".join(r[1:])
    dr.text((x+2,y+h+2), cap[:int(w/6.6)], fill=(235,235,235), font=font)
    dr.text((x+2,y+h+17), cap[int(w/6.6):int(w/6.6)*2], fill=(170,170,170), font=font)
S.save(out, quality=86); print(out, S.size)
