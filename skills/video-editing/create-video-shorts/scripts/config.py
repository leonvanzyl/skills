"""Per-video settings, read from project.json in the work directory (the cwd every script runs in).
Written by init_project.py, completed by detect_camera.py. Edit it by hand to override anything."""
import json, os

_P = 'project.json'
_cfg = json.load(open(_P)) if os.path.exists(_P) else {}


def get(key, default=None):
    return _cfg.get(key, default)


def save(**kw):
    _cfg.update(kw)
    json.dump(_cfg, open(_P, 'w'), indent=1)


SRC = _cfg.get('source', '../original.mov')             # master video, relative to the work dir
SRC_W, SRC_H = _cfg.get('source_size', [3840, 2160])
FPS = _cfg.get('fps', 60)
PROXY = 'proxy1080_10.mp4'                               # 10 fps proxy written by ingest.py
PROXY_FPS = 10
PROXY_W = 1920
PSCALE = PROXY_W / SRC_W                                 # source px -> proxy px

# camera geometry (source px). mode: 'pip' (webcam window inside a screen recording) or 'full' (the frame is the camera)
CAM = _cfg.get('camera', {'mode': 'full'})
MODE = CAM.get('mode', 'full')
WINDOW = CAM.get('window') or [0, 0, SRC_W, SRC_H]       # x, y, w, h of the camera picture
SAFE = CAM.get('safe') or WINDOW                          # inset region free of borders / rounded corners
# 9:16 centre slice used when a finished edit cuts to a full-frame camera shot (lines with "cam": "fullframe")
_sw = int(round(SRC_H * 9 / 16 / 2)) * 2
FULL_SLICE = CAM.get('fullframe_slice') or [(SRC_W - _sw) // 2, 0, _sw, SRC_H]

ASR_PROMPT = _cfg.get('asr_prompt', 'Claude, Claude Code, Anthropic, agentic, Agentic Labs, CLI.')
ASR_FIXES = {k.lower(): v for k, v in _cfg.get('asr_fixes', {'sonic': 'Sonnet', 'cloud': 'Claude'}).items()}


def crop_arg(r):
    x, y, w, h = [int(v) for v in r]
    return f'crop={w}:{h}:{x}:{y}'
