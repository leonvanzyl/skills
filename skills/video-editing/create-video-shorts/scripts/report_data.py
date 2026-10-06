# Prints the numbers a short's report.md needs: lines with source ranges, runs, SFX events (absolute time + level),
# riser, music, final file facts and loudness, the picked thumbnail. usage: python scripts/report_data.py s3
import json, subprocess, sys, re
sk = sys.argv[1]
C = json.load(open('cut.json'))[sk]; S = json.load(open('shorts.json'))[sk]
print(f'# {sk}: {S["title"]}  cover={S.get("cover")}  cta={S.get("cta_keyword")}')
print('\n## lines (source s)')
for L in S['lines']:
    ps = [p for p in C['pieces'] if p['line'] == L['id']]
    print(f"{L['id']} | {min(p['src0'] for p in ps):.2f}-{max(p['src1'] for p in ps):.2f} | pieces={len(ps)} | {L['layout']}"
          f"{' sw=' + str([(s['t'], s['layout']) for s in L.get('switches', [])]) if L.get('switches') else ''} | {L['text']}")
print('\n## runs')
for r in C['runs']:
    print(f"{r['i']} | {r['layout']} | {r['T0']:.3f}-{r['T1']:.3f} | {r['dur']:.2f} | {r.get('text', '')[:90]}")
END = C['runs'][-1]['T1']
print(f'END={END:.3f}')
ev = json.load(open('gfx/sfx_events.json'))
LEVEL = {'click': -10, 'pop': -10, 'chime': -10, 'whoosh': -9, 'key': -16, 'tick': -16}
print('\n## sfx (absolute s, level vs voice peak)')
for r in C['runs']:
    for e in ev.get(f'{sk}_r{r["i"]}', []):
        print(f"{r['T0'] + e['t']:.3f} | {e['type']} | {LEVEL.get(e['type'])} dB | run {r['i']}")
for e in json.load(open(f'{sk}/events_extra.json')):
    print(f"{e['t']:.3f} | {e['type']} | {LEVEL.get(e['type'])} dB | CTA")
print(f"\n## riser: 2.6 s, audible end on the hook join {C['runs'][0]['T1']:.3f} s, -12 dB vs voice peak")
print('## music', json.dumps(json.load(open(f'{sk}/music.json'))))
geo = f'{sk}/cam/split_geom.json'
try:
    g = json.load(open(geo)); print('## split geom', {k: v for k, v in g.items() if k not in ('src',)})
except Exception as e: print('no split geom', e)
p = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_name,profile,width,height,r_frame_rate,nb_frames,sample_rate,channels:format=duration',
                    '-of', 'compact', f'{sk}/final_video.mp4'], capture_output=True, text=True).stdout
print('\n## file\n' + p.strip())
r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f'{sk}/final_video.mp4', '-map', '0:a', '-af', 'ebur128=peak=true', '-f', 'null', '-'],
                   capture_output=True, text=True).stderr
summ = r[r.rfind('Summary:'):]
I = re.search(r'I:\s+(-?[\d.]+) LUFS', summ); TP = re.search(r'Peak:\s+(-?[\d.]+) dBFS', summ)
print(f"## loudness integrated {I.group(1) if I else '?'} LUFS, true peak {TP.group(1) if TP else '?'} dBFS")
try:
    th = json.load(open(f'{sk}/thumbnail.json'))
    print(f"## thumbnail {th['t']} s (run {th['run']}, {th['layout']}), q{th['quality']} {th['bytes'] / 1e6:.2f} MB; candidates: "
          + ', '.join(f"{c['t']} s r{c['run']} sharp {c['sharpness']} {c['mouth']}".rstrip() for c in th.get('candidates', [])))
except Exception as e: print('no thumbnail picked yet', e)
