"""Write project.json for one video (run inside its work folder). Probes the master and looks for a clean-audio file.
usage: python scripts/init_project.py ../<video>"""
import json, os, subprocess, sys, glob

src = sys.argv[1]
p = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate,channels,sample_rate:format=duration',
                               '-of', 'json', src], capture_output=True, text=True).stdout)
v = [s for s in p['streams'] if s['codec_type'] == 'video'][0]
a = [s for s in p['streams'] if s['codec_type'] == 'audio']
num, den = v['r_frame_rate'].split('/')
fps = round(int(num) / int(den))
proj = os.path.dirname(os.path.abspath(src))
stem = os.path.splitext(os.path.basename(src))[0].lower()
aud = [f for e in ('wav', 'm4a', 'mp3', 'flac', 'aac', 'aiff') for f in glob.glob(os.path.join(proj, f'*.{e}'))]
aud.sort(key=lambda f: (stem not in os.path.basename(f).lower(), f))      # a file named like the video wins
cfg = json.load(open('project.json')) if os.path.exists('project.json') else {}
cfg.update({
    'source': src.replace('\\', '/'),
    'source_size': [int(v['width']), int(v['height'])],
    'fps': fps,
    'duration': float(p['format']['duration']),
    'audio_channels': int(a[0]['channels']) if a else 0,
    'clean_audio': ('../' + os.path.basename(aud[0])) if aud else None,
    'clean_audio_candidates': ['../' + os.path.basename(f) for f in aud],
})
cfg.setdefault('camera', {'mode': 'auto'})
cfg.setdefault('asr_prompt', 'Claude, Claude Code, Anthropic, Sonnet, Opus, Haiku, Fable, agentic, Agentic Labs, CLI.')
cfg.setdefault('asr_fixes', {'sonic': 'Sonnet', 'cloud': 'Claude'})
json.dump(cfg, open('project.json', 'w'), indent=1)
print(json.dumps({k: cfg[k] for k in ('source', 'source_size', 'fps', 'duration', 'clean_audio')}))
if fps != 60:
    print(f'NOTE: source is {fps} fps; the deliverable is 60 fps. Camera runs are frame-mapped at the source rate and converted in compose.')
