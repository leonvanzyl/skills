import subprocess, sys, json, os
from PIL import Image, ImageDraw, ImageFont
f=sys.argv[1]; out=sys.argv[2]
p=subprocess.run(['ffprobe','-v','error','-show_entries','stream=codec_name,profile,width,height,r_frame_rate,nb_frames,sample_rate,channels,duration','-of','json',f],capture_output=True,text=True).stdout
print(p)
ln=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af','ebur128=peak=true','-f','null','-'],capture_output=True,text=True).stderr
print('\n'.join(l for l in ln.splitlines()[-12:] if 'I:' in l or 'Peak:' in l or 'LRA:' in l))
dur=float(json.loads(p)['streams'][0]['duration'])
ts=[i*2.0 for i in range(int(dur//2)+1)]+[dur-0.05]
os.makedirs('chk/final',exist_ok=True); ims=[]; font=ImageFont.truetype('arial.ttf',24)
for t in ts:
    fn=f'chk/final/{t:06.2f}.png'
    subprocess.run(['ffmpeg','-v','error','-y','-ss',f'{t:.3f}','-i',f,'-frames:v','1','-vf','scale=216:384',fn])
    if os.path.exists(fn):
        im=Image.open(fn).convert('RGB'); ImageDraw.Draw(im).text((4,2),f'{t:.1f}',fill='red',font=font); ims.append(im)
cols=10; rows=(len(ims)+cols-1)//cols; S=Image.new('RGB',(216*cols,384*rows))
for i,im in enumerate(ims): S.paste(im,((i%cols)*216,(i//cols)*384))
S.save(out); print(out,S.size)
