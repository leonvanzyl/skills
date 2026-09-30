"""Per-project settings, read from project.json in the work dir (the cwd every script runs in).
Written by setup.sh / program.py / scenes.py. Edit it by hand to override anything."""
import json, os

_P = 'project.json'
_cfg = json.load(open(_P, encoding='utf-8')) if os.path.exists(_P) else {}


def get(key, default=None):
    return _cfg.get(key, default)


def save(**kw):
    _cfg.update(kw)
    json.dump(_cfg, open(_P, 'w', encoding='utf-8'), indent=1)


FPS = _cfg.get('fps', 60)                                  # timeline frame rate
TW, TH = _cfg.get('timeline_size', [3840, 2160])          # timeline resolution: every render is made at this size
LAYOUT_W, LAYOUT_H = 1920, 1080                            # layout units used by the spec, graphics and overlays
UNIT = TW / LAYOUT_W                                       # output px per layout px (2.0 on a UHD timeline)
MEDIA = _cfg.get('media_dir', 'media')                     # where finished renders go (Resolve imports them from here)
HOOK_END = _cfg.get('hook_end')                            # program seconds, set when the plan is written

# fonts and models are copied into the work dir by setup.sh
FONTS = 'fonts/'
YUNET = 'models/face_detection_yunet_2023mar.onnx'
LANDMARKER = 'models/face_landmarker.task'

INK = (17, 17, 17); CLAY = (217, 119, 87); CLAY_T = (178, 87, 48); HL_YELLOW = (255, 255, 0)
SHADOW = [(60, 120, .16), (24, 48, .10), (4, 10, .06)]    # (dy, blur, alpha) in layout px: the spec's three-layer shadow
