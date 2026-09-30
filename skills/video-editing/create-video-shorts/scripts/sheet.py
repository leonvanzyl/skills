import sys, glob
from PIL import Image, ImageDraw, ImageFont
files = sorted(glob.glob(sys.argv[1])); out = sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv)>3 else 6
ims = [Image.open(f).convert('RGB') for f in files]
w, h = ims[0].size; rows = (len(ims)+cols-1)//cols
sheet = Image.new('RGB', (cols*w, rows*h), 'black'); d = ImageDraw.Draw(sheet)
try: font = ImageFont.truetype('arial.ttf', max(14, h//10))
except: font = None
for i,(f,im) in enumerate(zip(files, ims)):
    x, y = (i%cols)*w, (i//cols)*h; sheet.paste(im, (x,y))
    lab = __import__('os').path.basename(f).rsplit('.',1)[0].split('_',1)[-1]
    d.text((x+4,y+2), lab, fill='yellow', font=font, stroke_width=2, stroke_fill='black')
sheet.save(out); print(out, sheet.size)
