import sys, os, glob
from PIL import Image, ImageDraw, ImageFont
out=sys.argv[1]; cols=int(sys.argv[2]); pats=sys.argv[3:]
files=[]
for p in pats: files+=sorted(glob.glob(p))
ims=[Image.open(f).convert('RGB') for f in files]; w,h=ims[0].size; rows=(len(ims)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*h)); d=ImageDraw.Draw(S); font=ImageFont.truetype('arial.ttf',16)
for i,(f,im) in enumerate(zip(files,ims)):
    x,y=(i%cols)*w,(i//cols)*h; S.paste(im,(x,y))
    b=os.path.basename(f)[1:].split('.')[0]; a,n=b.split('_'); t=float(a)+int(n)*0.5
    d.text((x+2,y+1),f"{t:.1f}",fill='yellow',font=font,stroke_width=2,stroke_fill='black')
S.save(out)
