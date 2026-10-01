"""Shared helpers: frame-exact source decoding along the program map, colour-exact encoding, eases, the plan.
A V2 render must be pixel-identical to V1 at rest, or every cut in and out of it shows a colour jump, so decode and
encode always use the source's own matrix and range."""
import json, subprocess, functools, os
import numpy as np
import config as C


# ------------------------------------------------------------------ pipes
# Windows gives anonymous pipes a 4 KB buffer, which caps a 4K raw-video pipe at ~60 MB/s (4 fps). A 64 MB pipe
# moves the same frames ~16x faster, so every decoder/encoder here goes through one.
def _bigpipe():
    if os.name != 'nt': return None
    import _winapi, msvcrt
    r, w = _winapi.CreatePipe(None, 64 << 20)
    return msvcrt.open_osfhandle(r, os.O_RDONLY), msvcrt.open_osfhandle(w, 0)


class Proc:
    def __init__(self, p, stdin=None, stdout=None): self.p, self.stdin, self.stdout = p, stdin, stdout
    def wait(self): return self.p.wait()
    def poll(self): return self.p.poll()
    def kill(self): return self.p.kill()


def reader_proc(cmd):
    bp = _bigpipe()
    if bp is None:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0); return Proc(p, stdout=p.stdout)
    rfd, wfd = bp
    p = subprocess.Popen(cmd, stdout=wfd, stderr=subprocess.DEVNULL); os.close(wfd)
    return Proc(p, stdout=os.fdopen(rfd, 'rb', buffering=0))


def writer_proc(cmd):
    bp = _bigpipe()
    if bp is None:
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE); return Proc(p, stdin=p.stdin)
    rfd, wfd = bp
    p = subprocess.Popen(cmd, stdin=rfd); os.close(rfd)
    return Proc(p, stdin=os.fdopen(wfd, 'wb', buffering=0))


def read_exact(f, n):
    buf = bytearray(n); mv = memoryview(buf); got = 0
    while got < n:
        k = f.readinto(mv[got:])
        if not k: return None
        got += k
    return buf


@functools.lru_cache(None)
def probe(path):
    o = json.loads(subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries',
                                   'stream=width,height,color_space,color_range,color_transfer,color_primaries,pix_fmt',
                                   '-of', 'json', path], capture_output=True, text=True).stdout)['streams'][0]
    return o


def color(path):
    """(matrix, range) of a source, defaulting to bt709 / tv like OBS and most cameras."""
    p = probe(path)
    m = p.get('color_space') or 'bt709'
    m = {'bt470bg': 'bt601', 'smpte170m': 'bt601'}.get(m, m)
    if m not in ('bt709', 'bt601', 'bt2020nc'): m = 'bt709'
    r = 'pc' if p.get('color_range') in ('pc', 'full') else 'tv'
    return m, r


def dec_vf(path, extra=''):
    m, r = color(path)
    return (extra + ',' if extra else '') + f'scale=in_color_matrix={m}:in_range={r}:out_color_matrix={m}:out_range=pc,format=rgb24'


@functools.lru_cache(None)
def has_nvenc():
    """NVENC is ~100 fps at 4K; renders are intermediates (Resolve re-encodes on delivery), so it is the default"""
    if os.environ.get('PRO_EDIT_X264'): return False
    r = subprocess.run(['ffmpeg', '-v', 'error', '-f', 'lavfi', '-i', 'color=black:s=256x256:d=0.1', '-c:v', 'h264_nvenc', '-f', 'null', '-'],
                       capture_output=True)
    return r.returncode == 0


def enc_args(path=None, crf=12, nvenc=None, gop=30):
    """encoder args matching the source's colour (or bt709 tv when path is None). nvenc=None: use it when available."""
    if nvenc is None: nvenc = has_nvenc()
    m, r = color(path) if path else ('bt709', 'tv')
    tag = {'bt709': 'bt709', 'bt601': 'smpte170m', 'bt2020nc': 'bt2020nc'}[m]
    vf = ['-vf', f'scale=in_color_matrix={m}:in_range=pc:out_color_matrix={m}:out_range={r},format=yuv420p']
    if nvenc:
        v = ['-c:v', 'h264_nvenc', '-preset', 'p4', '-tune', 'hq', '-rc', 'vbr', '-cq', '15', '-b:v', '0', '-profile:v', 'high']
    else:
        v = ['-c:v', 'libx264', '-preset', 'fast', '-crf', str(crf), '-profile:v', 'high']      # at CRF 12 the preset mostly moves file size
    return vf + v + ['-g', str(gop), '-r', str(C.FPS), '-colorspace', tag, '-color_primaries', 'bt709' if m == 'bt709' else tag,
                     '-color_trc', 'bt709' if m == 'bt709' else tag, '-color_range', r, '-movflags', '+faststart', '-an']


def encoder(out, w, h, path=None, **kw):
    return writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}', '-r', str(C.FPS),
                        '-i', '-'] + enc_args(path, **kw) + [out])


def prores4444(out, w, h):
    """alpha overlays: RGBA frames in, ProRes 4444 with alpha out (Resolve composites it on an upper track)."""
    return writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', f'{w}x{h}', '-r', str(C.FPS),
                        '-i', '-', '-c:v', 'prores_ks', '-profile:v', '4444', '-pix_fmt', 'yuva444p10le', '-alpha_bits', '16',
                        '-vendor', 'apl0', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', out])


# ------------------------------------------------------------------ the program map
@functools.lru_cache(None)
def program():
    return json.load(open('program.json', encoding='utf-8'))


@functools.lru_cache(None)
def plan():
    return json.load(open('edit_plan.json', encoding='utf-8'))


def beat(bid):
    return next(b for b in plan()['beats'] if b['id'] == bid)


def frames_of(t0, t1):
    """program frame range [f0, f1) for a beat, snapped to the timeline frame grid"""
    return int(round(t0 * C.FPS)), int(round(t1 * C.FPS))


def source_map(f0, f1):
    """[(file, item, src_frame)] for every program frame in [f0, f1) - follows V1 exactly, jump cuts included.
    Frames on a V1 title/generator/effect (no source media) or in a gap raise: a render cannot follow them."""
    import bisect
    items = program()['items']; starts = [it['rec0'] for it in items]; out = []
    for fx in program().get('nomedia', []):
        if fx['rec0'] < f1 and f0 < fx['rec1']:
            raise SystemExit(f"the beat overlaps V1 item {fx['v1']} '{fx['name']}' ({fx['rec0'] / C.FPS:.2f}-{fx['rec1'] / C.FPS:.2f}s), "
                             'a title/generator/transition the editor added - end the beat before it or start it after')
    for n in range(f0, f1):
        k = bisect.bisect_right(starts, n) - 1
        if k < 0 or n >= items[k]['rec1']:
            raise SystemExit(f'program frame {n} ({n / C.FPS:.2f}s) has no source media on V1 (title/generator/gap) - end the beat before it')
        it = items[k]
        out.append((it['file'], it, it['src0'] + (n - it['rec0'])))
    return out


def decode(seq, w, h, vf='', yuv=False):
    """yield frames for seq = [(file, item, src_frame)], decoding each contiguous run once.
    RGB: (h, w, 3) uint8 through the source's own matrix. yuv=True: the source's native planes untouched, as
    (Y (h, w), U (h/2, w/2), V (h/2, w/2)) - no colour conversion at all, so a frame at rest is bit-identical to V1.
    vf: a filter before the conversion (e.g. a crop); w/h are that chain's output size."""
    fsize = w * h * 3 // 2 if yuv else w * h * 3
    k = 0
    while k < len(seq):
        f, it, a = seq[k]; j = k
        while j + 1 < len(seq) and seq[j + 1][0] == f and seq[j + 1][2] == seq[j][2] + 1: j += 1
        n = j - k + 1
        chain = ((vf + ',') if vf else '') + 'format=yuv420p' if yuv else dec_vf(f, vf)
        p = reader_proc(['ffmpeg', '-v', 'error', '-ss', f'{max(0.0, (a - 0.25) / C.FPS):.5f}', '-i', f, '-frames:v', str(n),
                         '-vf', chain, '-f', 'rawvideo', '-pix_fmt', 'yuv420p' if yuv else 'rgb24', '-'])
        got = 0
        try:
            while got < n:
                b = read_exact(p.stdout, fsize)
                if b is None: break
                a_ = np.frombuffer(b, np.uint8)
                if yuv:
                    q = w * h // 4
                    yield (a_[:w * h].reshape(h, w), a_[w * h:w * h + q].reshape(h // 2, w // 2), a_[w * h + q:].reshape(h // 2, w // 2))
                else:
                    yield a_.reshape(h, w, 3)
                got += 1
        finally:                                   # a preview that stops early closes the pipe quietly
            p.stdout.close(); p.kill() if p.poll() is None else None; p.wait()
        if got < n:
            raise SystemExit(f'decode: only {got}/{n} frames from {os.path.basename(f)} @ {a}')
        k = j + 1


def decode_at(seq, n, w, h, vf='', yuv=False):
    """the single program frame seq[n], decoded exactly as a full render decodes it: from the start of the contiguous
    source run it belongs to, counting forward. A time seek straight to one frame can land a frame late on OBS
    recordings (millisecond timestamps), so previews use this to show what the render will show."""
    import itertools
    j = n
    while j > 0 and seq[j - 1][0] == seq[j][0] and seq[j - 1][2] == seq[j][2] - 1: j -= 1
    return next(itertools.islice(decode(seq[j:n + 1], w, h, vf, yuv), n - j, None))


def yuv_encoder(out, w, h, path=None, nvenc=None, crf=12, gop=30):
    """raw yuv420p in, H.264 out, tagged with the source's own colour - no conversion anywhere"""
    args = enc_args(path, crf=crf, nvenc=nvenc, gop=gop)
    args = args[2:]                                # drop the -vf colour conversion: the planes are already right
    return writer_proc(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'yuv420p', '-s', f'{w}x{h}', '-r', str(C.FPS),
                        '-i', '-'] + args + ['-pix_fmt', 'yuv420p', out])


# ------------------------------------------------------------------ colour maths for drawing on YUV planes
_KR = {'bt709': (0.2126, 0.0722), 'bt601': (0.299, 0.114), 'bt2020nc': (0.2627, 0.0593)}


def rgb2yuv(rgb, m='bt709', r='tv'):
    """RGB (0-255, (..., 3)) -> YCbCr code values in the source's matrix and range"""
    kr, kb = _KR[m]; kg = 1 - kr - kb
    x = np.asarray(rgb, np.float32) / 255
    y = kr * x[..., 0] + kg * x[..., 1] + kb * x[..., 2]
    cb = (x[..., 2] - y) / (2 * (1 - kb)); cr = (x[..., 0] - y) / (2 * (1 - kr))
    if r == 'tv': return np.stack([16 + 219 * y, 128 + 224 * cb, 128 + 224 * cr], -1)
    return np.stack([255 * y, 128 + 255 * cb, 128 + 255 * cr], -1)


def yuv2rgb(Y, U, V, m='bt709', r='tv'):
    """planes -> RGB uint8 (previews and small regions only)"""
    kr, kb = _KR[m]; kg = 1 - kr - kb
    import cv2
    U = cv2.resize(U, (Y.shape[1], Y.shape[0]), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    V = cv2.resize(V, (Y.shape[1], Y.shape[0]), interpolation=cv2.INTER_LINEAR).astype(np.float32)
    Y = Y.astype(np.float32)
    if r == 'tv': y, cb, cr = (Y - 16) / 219, (U - 128) / 224, (V - 128) / 224
    else: y, cb, cr = Y / 255, (U - 128) / 255, (V - 128) / 255
    R = y + 2 * (1 - kr) * cr; B = y + 2 * (1 - kb) * cb; G = (y - kr * R - kb * B) / kg
    return np.clip(np.stack([R, G, B], -1) * 255 + 0.5, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------ the webcam PiP
def pip_mask(w, h):
    """alpha for pasting the PiP window: rounded like the recording's own window and inset a few px, so none of the
    screen behind its corners or its edge line comes along. project.json: pip_radius (fraction of the width, default
    0.056), pip_inset (px, default 3)."""
    import cv2
    r = int(round(C.get('pip_radius', 0.056) * w)); ins = int(C.get('pip_inset', 3))
    ss = 4; m = np.zeros((h * ss, w * ss), np.uint8)
    x0, y0, x1, y1 = ins * ss, ins * ss, (w - ins) * ss - 1, (h - ins) * ss - 1; rr = r * ss
    cv2.rectangle(m, (x0 + rr, y0), (x1 - rr, y1), 255, -1); cv2.rectangle(m, (x0, y0 + rr), (x1, y1 - rr), 255, -1)
    for cx, cy in ((x0 + rr, y0 + rr), (x1 - rr, y0 + rr), (x0 + rr, y1 - rr), (x1 - rr, y1 - rr)):
        cv2.circle(m, (cx, cy), rr, 255, -1)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


# ------------------------------------------------------------------ eases (GSAP names)
def ease(name):
    def power_in(p, n): return p ** n
    def power_out(p, n): return 1 - (1 - p) ** n
    def power_inout(p, n): return 0.5 * (2 * p) ** n if p < 0.5 else 1 - 0.5 * (2 - 2 * p) ** n
    n = {'power1': 2, 'power2': 3, 'power3': 4, 'power4': 5}
    if name in ('linear', 'none'): return lambda p: p
    if name == 'sine.inOut': return lambda p: -(np.cos(np.pi * p) - 1) / 2
    if name == 'sine.out': return lambda p: np.sin(np.pi * p / 2)
    base, kind = name.split('.')
    e = n[base]
    return {'in': lambda p: power_in(p, e), 'out': lambda p: power_out(p, e), 'inOut': lambda p: power_inout(p, e)}[kind]
