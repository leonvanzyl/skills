"""Program map of the clean-cut timeline: every V1 item on record time, every word on program time, and the program
voice exactly as the timeline plays it. Everything downstream (plan, renders, audio, placement) reads program.json.

Reads items.json + segments.json, written in this same work dir by `vedit prepare` + `vedit transcribe` on the
clean-cut timeline. Writes:
  program.json    fps, size, items (rec/src frames, V1 item index), words (program seconds), sentences, voice levels
  voice48.wav     the program voice, 48 kHz stereo (source audio assembled per item)
  rms10ms.npy     its RMS in dBFS per 10 ms
  transcript.txt  one line per item: index, program time, duration, scene (after scenes.py), text
usage: python scripts/program.py [--size 3840x2160]      (size/fps default to project.json, else 3840x2160)"""
import json, os, re, subprocess, sys, hashlib
import numpy as np, soundfile as sf, pyloudnorm as pyln
sys.path.insert(0, 'scripts'); import config as C

SR = 48000


def tc(t):
    return f'{int(t // 60):02d}:{t % 60:05.2f}'


def audio48(path):
    os.makedirs('audio48', exist_ok=True)
    out = 'audio48/' + re.sub(r'[^A-Za-z0-9_.-]', '_', os.path.splitext(os.path.basename(path))[0])[:40] + '_' + hashlib.md5(path.encode()).hexdigest()[:6] + '.wav'
    if not os.path.exists(out):
        print('extracting 48 kHz audio from', path)
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', path, '-vn', '-ac', '2', '-ar', str(SR), '-c:a', 'pcm_s24le', out], check=True)
    return out


def sentences(words):
    out, cur = [], []
    for k, w in enumerate(words):
        if w.get('tag'):
            continue
        if cur and w['s'] - words[cur[-1]]['e'] > 1.5:
            out.append(cur); cur = []
        cur.append(k)
        if re.search(r'[.?!]["\')]?$', w['w']):
            out.append(cur); cur = []
    if cur: out.append(cur)
    return [dict(s=words[c[0]]['s'], e=words[c[-1]]['e'], w0=c[0], w1=c[-1], text=' '.join(words[k]['w'] for k in c)) for c in out]


def write_transcript(P):
    sc = json.load(open('scenes.json')) if os.path.exists('scenes.json') else {}
    lines = []
    for it in P['items']:
        ws = [w['w'] for w in P['words'] if w['i'] == it['v1']]
        s = sc.get('items', {}).get(str(it['v1']), {}).get('scene', '')
        lines.append(f"{it['v1']:4d} {tc(it['t0'])} {it['t1'] - it['t0']:5.2f}s {s:7s}| {' '.join(ws)}")
    open('transcript.txt', 'w', encoding='utf-8').write('\n'.join(lines))


def main():
    meta = json.load(open('items.json', encoding='utf-8'))
    segs = {s['i']: s for s in json.load(open('segments.json', encoding='utf-8'))}
    its = meta['items']
    fps = its[0]['fps']
    if '--size' in sys.argv:
        tw, th = [int(v) for v in sys.argv[sys.argv.index('--size') + 1].split('x')]
    else:
        tw, th = C.get('timeline_size', [3840, 2160])
    start = meta.get('start_frame') or 0
    items, words = [], []
    for it in its:
        k = it['i']                                              # the V1 item index in Resolve (0-based)
        rec0, rec1 = it['rec_in'] - start, it['rec_out'] - start
        # a clip next to a transition reports its handle in the source range; what plays is src_in + (n - rec_in)
        items.append(dict(v1=k, name=it['name'], file=it['file'], mpi=it['media_pool_item_id'], rec0=rec0, rec1=rec1,
                          src0=it['src_in'], src1=it['src_in'] + (rec1 - rec0), t0=round(rec0 / fps, 4), t1=round(rec1 / fps, 4),
                          audio_file=it['audio_file'], audio_t0=it['audio_t0']))
        vis = (rec1 - rec0) / fps
        for w in segs.get(it['i'], {}).get('words', []):
            if w['s'] >= vis - 0.02: continue                    # said inside a transition handle: not heard here
            s, e = w['s'], min(w['e'], vis)
            d = dict(w=w['w'], s=round(rec0 / fps + s, 3), e=round(rec0 / fps + e, 3), i=k)
            if w['w'].startswith('['): d['tag'] = True
            words.append(d)
    nomedia = [dict(v1=x['i'], name=x['name'], rec0=x['rec_in'] - start, rec1=x['rec_out'] - start) for x in meta.get('nomedia', [])]
    end = max([items[-1]['rec1']] + [x['rec1'] for x in nomedia])
    # program voice
    N = int(round(end / fps * SR)); voice = np.zeros((N, 2), np.float32)
    cache = {}
    for it in items:
        f = cache.setdefault(it['audio_file'], audio48(it['audio_file']))
        a0 = int(round(it['audio_t0'] * SR)); n = int(round((it['rec1'] - it['rec0']) / fps * SR))
        x, _ = sf.read(f, start=a0, stop=a0 + n, dtype='float32', always_2d=True)
        if x.shape[1] == 1: x = np.repeat(x, 2, 1)
        i0 = int(round(it['rec0'] / fps * SR)); m = min(len(x), N - i0)
        voice[i0:i0 + m] = x[:m, :2]
    sf.write('voice48.wav', voice, SR, subtype='PCM_24')
    mono = voice.mean(1); hop = SR // 100; nn = len(mono) // hop
    db = 20 * np.log10(np.sqrt((mono[:nn * hop].reshape(nn, hop) ** 2).mean(1)) + 1e-9)
    np.save('rms10ms.npy', db.astype(np.float32))
    meter = pyln.Meter(SR)
    lufs = float(meter.integrated_loudness(voice)); peak = float(20 * np.log10(np.abs(voice).max() + 1e-9))
    P = dict(timeline=meta.get('timeline'), fps=fps, size=[tw, th], start_frame=start, frames=end, dur=round(end / fps, 4),
             items=items, nomedia=nomedia, words=words, sentences=sentences(words), voice=dict(lufs=round(lufs, 2), peak_db=round(peak, 2)))
    json.dump(P, open('program.json', 'w', encoding='utf-8'), indent=1)
    C.save(fps=fps, timeline_size=[tw, th], timeline=meta.get('timeline'), start_frame=start)
    write_transcript(P)
    print(f"{meta.get('timeline')}: {len(items)} items, {len(words)} words, {len(P['sentences'])} sentences, {tc(end / fps)} "
          f"| voice {lufs:.1f} LUFS, peak {peak:.1f} dBFS | size {tw}x{th} @ {fps}")


if __name__ == '__main__':
    main()
