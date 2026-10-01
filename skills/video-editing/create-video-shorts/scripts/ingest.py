"""The ONE full decode of the master (GPU if available). Writes everything later stages need:
  clean48.wav (24-bit stereo, the edit's audio), clean16.wav (16 kHz mono, ASR), rms10ms.npy (10 ms RMS dBFS),
  proxy1080_10.mp4 (1920-wide, 10 fps: gaze / framing / camera detection read this, never the master), thumbs/ (1 fps).
If project.json names a separate clean-audio file it is used for clean48/clean16 and the camera track is kept as cam16.wav
for the sync cross-correlation (sync.py).  usage: python scripts/ingest.py"""
import subprocess, os, sys, numpy as np, soundfile as sf
sys.path.insert(0, 'scripts'); import config as C

os.makedirs('thumbs', exist_ok=True)
for f in ('ingest_audio.done', 'ingest.done'):          # stage markers: analyze.sh starts transcription / camera detection on them
    if os.path.exists(f): os.remove(f)
hw = ['-hwaccel', 'cuda'] if subprocess.run(['ffmpeg', '-v', 'error', '-hwaccels'], capture_output=True, text=True).stdout.find('cuda') >= 0 else []
clean = C.get('clean_audio')
# The decode of a 4K master is bound by ONE hardware decoder session (~340 fps on an RTX 5090, whatever the filters or
# encoder). Modern GPUs run several NVDEC sessions at once, so the master is decoded as N time slices in parallel
# (whole-second boundaries keep the 10 fps / 1 fps sampling grid identical to a single pass), then stream-copied together.
# 4 slices: ~2.6x faster on an RTX 5090. INGEST_SLICES=1 restores the single pass.
N_SLICES = max(1, int(os.environ.get('INGEST_SLICES', '4' if hw else '1')))
DUR = float(C.get('duration'))
edges = [int(DUR * k / N_SLICES) for k in range(N_SLICES)] + [None]
vids = []
for k in range(N_SLICES):
    a, b = edges[k], edges[k + 1]
    cut = ['-ss', str(a)] + (['-t', str(b - a)] if b is not None else [])
    vids.append(subprocess.Popen(['ffmpeg', '-v', 'error', '-y'] + hw + cut + ['-i', C.SRC,
        '-filter_complex', '[0:v]fps=10,scale=1920:-2:flags=bicubic,split=2[p][t];[t]fps=1,scale=480:-2[tt]',
        '-map', '[p]', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '17', '-g', '10', '-pix_fmt', 'yuv420p', f'_proxy_part{k}.mp4',
        '-map', '[tt]', '-q:v', '4', '-start_number', str(a + 1), 'thumbs/t_%05d.jpg']))
if clean:
    # separate clean recording: find its offset against the camera track (16 kHz mono cross-correlation), then write
    # clean48/clean16 already shifted onto the video's timeline so every later stage uses video time.
    from scipy import signal
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', C.SRC, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', 'cam16.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', clean, '-vn', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', 'rawclean16.wav'], check=True)
    a, _ = sf.read('cam16.wav'); b, _ = sf.read('rawclean16.wav')
    N = min(len(a), len(b), 16000 * 240); a, b = a[:N] - a[:N].mean(), b[:N] - b[:N].mean()
    c = signal.correlate(a, b, mode='full', method='fft'); lags = signal.correlation_lags(len(a), len(b))
    k = int(np.argmax(np.abs(c))); lag = int(lags[k]); peak = float(abs(c[k]) / np.sqrt((a ** 2).sum() * (b ** 2).sum()))
    srt = np.sort(np.abs(c))[::-1]; second = float(srt[int(16000 * 0.05)] / np.sqrt((a ** 2).sum() * (b ** 2).sum()))
    off = lag / 16000.0          # camera[t] ~ clean[t - off]  -> clean must be delayed by off seconds
    C.save(sync={'offset_s': round(off, 5), 'peak': round(peak, 4), 'next_peak': round(second, 4)})
    print(f'sync: clean audio offset {off*1000:.1f} ms, correlation peak {peak:.3f} (next best {second:.3f})')
    af = f'adelay={int(round(off*1000))}:all=1' if off >= 0 else f'atrim=start={-off:.5f},asetpts=PTS-STARTPTS'
    dur = str(C.get('duration'))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', clean, '-vn', '-af', af + ',apad', '-t', dur, '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', 'clean48.wav'], check=True)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'clean48.wav', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', 'clean16.wav'], check=True)
else:
    # one read of the master for both audio outputs (transcription can start the moment clean16.wav lands)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', C.SRC, '-vn', '-map', '0:a:0', '-c:a', 'pcm_s24le', '-ar', '48000', '-ac', '2', 'clean48.wav',
                    '-map', '0:a:0', '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le', 'clean16.wav'], check=True)
    # no separate clean track: confirm the embedded channels line up (zero offset) for the report
    x2, _ = sf.read('clean48.wav', frames=48000 * 60)
    if x2.ndim > 1 and x2.shape[1] > 1:
        from scipy import signal
        L, R = x2[::3, 0], x2[::3, 1]
        c = signal.correlate(L, R, mode='full', method='fft'); lags = signal.correlation_lags(len(L), len(R)); k = int(np.argmax(np.abs(c)))
        C.save(sync={'offset_s': 0.0, 'note': 'embedded track used as clean audio', 'LR_lag_ms': float(lags[k] / 16), 'LR_peak': round(float(abs(c[k]) / np.sqrt((L ** 2).sum() * (R ** 2).sum())), 4)})
x, sr = sf.read('clean48.wav'); m = x.mean(1) if x.ndim > 1 else x
hop = sr // 100; n = len(m) // hop
db = 20 * np.log10(np.sqrt((m[:n * hop].reshape(n, hop) ** 2).mean(1) + 1e-12))
np.save('rms10ms.npy', db.astype(np.float32))
open('ingest_audio.done', 'w').write('clean48.wav clean16.wav rms10ms.npy\n')   # transcription can start now
for v in vids: v.wait()
if N_SLICES == 1:
    os.replace('_proxy_part0.mp4', C.PROXY)
else:
    open('_proxy_parts.txt', 'w').write(''.join(f"file '_proxy_part{k}.mp4'\n" for k in range(N_SLICES)))
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', '_proxy_parts.txt', '-c', 'copy', C.PROXY], check=True)
    for k in range(N_SLICES): os.remove(f'_proxy_part{k}.mp4')
    os.remove('_proxy_parts.txt')
open('ingest.done', 'w').write(C.PROXY + ' thumbs/\n')
print('ingest done: clean48.wav clean16.wav rms10ms.npy', C.PROXY, 'thumbs/', '(gpu decode)' if hw else '(cpu decode)')
