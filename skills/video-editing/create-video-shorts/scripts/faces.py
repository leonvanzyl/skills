"""Face boxes anywhere in a frame (small webcam windows included) with OpenCV's YuNet detector (bundled model)."""
import cv2, numpy as np
_det = {}
def detect(bgr, min_score=0.7):
    """bgr uint8 image -> list of (x, y, w, h, score), largest first"""
    h, w = bgr.shape[:2]
    d = _det.get((w, h))
    if d is None:
        d = cv2.FaceDetectorYN.create('face_detection_yunet_2023mar.onnx', '', (w, h), min_score, 0.3, 50)
        _det[(w, h)] = d
    _, f = d.detect(bgr)
    if f is None: return []
    out = [(float(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[14])) for r in f]
    return sorted(out, key=lambda r: -r[2] * r[3])
