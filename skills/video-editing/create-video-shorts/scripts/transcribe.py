import os, sys, json, glob, site
# make CUDA DLLs from pip nvidia packages visible
for sp in site.getsitepackages():
    for d in glob.glob(os.path.join(sp, 'nvidia', '*', 'bin')):
        os.add_dll_directory(d); os.environ['PATH'] = d + os.pathsep + os.environ['PATH']
from faster_whisper import WhisperModel
def _wm():
    try: return WhisperModel('large-v3', device='cuda', compute_type='float16')
    except Exception as e:
        print('no CUDA for Whisper (' + str(e)[:60] + ') - using CPU int8 (slower)'); return WhisperModel('large-v3', device='cpu', compute_type='int8')
sys.path.insert(0, 'scripts'); import config as _C; ASR_PROMPT = _C.ASR_PROMPT
src, out = sys.argv[1], sys.argv[2]
m = _wm()
segs, info = m.transcribe(src, language='en', word_timestamps=True, vad_filter=False,
                          condition_on_previous_text=False, beam_size=5,
                          initial_prompt=ASR_PROMPT)
res = []
for s in segs:
    res.append({'start': s.start, 'end': s.end, 'text': s.text,
                'words': [{'w': w.word, 's': w.start, 'e': w.end, 'p': w.probability} for w in s.words]})
    print(f"[{s.start:7.2f}-{s.end:7.2f}] {s.text}", flush=True)
json.dump(res, open(out, 'w'), indent=1)
