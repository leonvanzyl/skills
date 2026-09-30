"""video-edit helper: transcript-driven clean cuts for DaVinci Resolve timelines.

Run with the CrisperWhisper environment's Python (it has torch, transformers, crisperwhisper, numpy):
    <venv>/Scripts/python.exe vedit.py <command> --work <dir> [...]   (Windows; <venv>/bin/python on macOS/Linux)

Commands
    prepare      --structure FILE [--track 1]   parse a probe_timeline_structure dump, extract 16 kHz audio
    sample       [--n 30]                       quick transcript of clips spread across the timeline (for hotwords)
    transcribe   [--hotwords "A,B"] [--force]   CrisperWhisper per clip -> segments.json + listing.txt (resumable)
    listing                                     rebuild listing.txt from segments.json
    verify       [--keep keep.json]             transcription-verified cut points -> edl.json + cut_report.txt
    qa                                          re-transcribe every kept range -> qa.txt (flags at the top)
    probe        --clip I --from S --to S       END/START transcripts + loudness around a spot (manual fixes)
    clipinfos                                   edl.json -> clip_infos.json (for Resolve) + markers.json
    check-build  --structure FILE               compare the built timeline with clip_infos.json

Work-dir files: structure.json items.json audio/*.wav hotwords.txt segments.json listing.txt keep.json
                edl.json cut_report.txt qa.json qa.txt clip_infos.json markers.json
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import warnings
import wave
from difflib import SequenceMatcher
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")          # the model is cached; never re-download silently
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
os.environ.setdefault("TQDM_DISABLE", "1")
warnings.filterwarnings("ignore")
try:
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
except Exception:
    pass

import numpy as np

SR = 16000
MODEL_ID = "nyralabs/CrisperWhisper2.0_large"
_MODEL = None


# ----------------------------------------------------------------------------- helpers

def model():
    global _MODEL
    if _MODEL is None:
        from crisperwhisper import CrisperWhisperModel
        try:
            _MODEL = CrisperWhisperModel(MODEL_ID, backend="transformers")
        except Exception as e:  # most likely: cache missing and HF_HUB_OFFLINE=1
            sys.exit(f"Could not load {MODEL_ID}: {e}\n"
                     "If the model cache was deleted, re-run once with HF_HUB_OFFLINE=0 to download it (~2.9 GB).")
    return _MODEL


def transcribe(audio, hotwords=None, language="en", words=False):
    if len(audio) < int(0.05 * SR):
        return "", []
    r = model().transcribe(audio, sr=SR, language=language, word_timestamps=words, hotwords=hotwords or None)
    ws = [{"w": w.word, "s": round(float(w.start), 3), "e": round(float(w.end), 3)} for w in (r.words or [])] if words else []
    return r.text.strip(), ws


def toks(text):
    """Normalised tokens; filler/event tags kept as '[um]', hyphens and punctuation dropped."""
    return re.findall(r"\[[a-z]+\]|[a-z0-9']+", text.lower())


def sim(a, b):
    return SequenceMatcher(None, a, b).ratio()


def load_json(p, default=None):
    p = Path(p)
    if not p.exists():
        return default
    return json.load(open(p, encoding="utf-8"))


def save_json(obj, p):
    tmp = Path(str(p) + ".tmp")
    json.dump(obj, open(tmp, "w", encoding="utf-8"), indent=1)
    os.replace(tmp, p)


def load_wav(p):
    with wave.open(str(p)) as w:
        return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768.0


class Work:
    def __init__(self, d):
        self.d = Path(d)
        self.d.mkdir(parents=True, exist_ok=True)
        self._audio = {}

    def p(self, name):
        return self.d / name

    @property
    def meta(self):
        m = load_json(self.p("items.json"))
        if m is None:
            sys.exit("items.json missing - run `prepare` first")
        return m

    def items(self):
        return {it["i"]: it for it in self.meta["items"]}

    def hotwords(self, override=None):
        if override is not None:
            hw = [h.strip() for h in override.split(",") if h.strip()]
            self.p("hotwords.txt").write_text(", ".join(hw), encoding="utf-8")
            return hw
        f = self.p("hotwords.txt")
        return [h.strip() for h in f.read_text(encoding="utf-8").split(",") if h.strip()] if f.exists() else []

    def audio(self, file_path):
        if file_path not in self._audio:
            self._audio[file_path] = load_wav(self.d / self.meta["audio"][file_path])
        return self._audio[file_path]

    def clip_audio(self, it, t0=0.0, t1=None):
        """Audio of clip `it` between clip-relative seconds t0..t1 (clamped to the clip)."""
        a = self.audio(it["audio_file"])
        t1 = it["dur"] if t1 is None else t1
        t0, t1 = max(0.0, t0), min(it["dur"], t1)
        base = it["audio_t0"]
        return a[int((base + t0) * SR):int((base + max(t0, t1)) * SR)]


def env_db(x, hop=160):
    n = len(x) // hop
    if n < 3:
        return np.full(max(n, 1), -120.0)
    rms = np.sqrt((x[:n * hop].reshape(n, hop) ** 2).mean(axis=1))
    rms = np.convolve(rms, np.ones(3) / 3, mode="same")
    return 20 * np.log10(rms + 1e-9)


def rms_db(x):
    return round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)), 1) if len(x) else -120.0


def tc(frames, fps):
    s = frames / fps
    return f"{int(s // 60):02d}:{s % 60:05.2f}"


# ----------------------------------------------------------------------------- prepare

def cmd_prepare(a):
    W = Work(a.work)
    st = load_json(a.structure)
    st = st.get("result", st)
    save_json(st, W.p("structure.json"))
    vtracks = [t for t in st["tracks"]["video"]["tracks"] if t["track_index"] == a.track]
    if not vtracks or not vtracks[0]["items"]:
        sys.exit(f"video track {a.track} has no items")
    vt = vtracks[0]["items"]
    by_pos = {}
    for t in st["tracks"]["audio"]["tracks"]:
        for it in t["items"]:
            by_pos.setdefault((it["start"], it["end"]), []).append(it)

    items, warn = [], []
    for k, v in enumerate(vt):
        cands = by_pos.get((v["start"], v["end"]), [])
        au = next((x for x in cands if x["media_pool_item_id"] == v["media_pool_item_id"]), cands[0] if cands else None)
        if au is None:
            warn.append(f"clip {k} ({v['name']} @ {v['start']}): no audio item at the same position - using the video file's audio")
        elif au["media_pool_item_id"] != v["media_pool_item_id"]:
            warn.append(f"clip {k}: audio is a different media item ({au['name']}) - separate audio; the linked build would use the camera audio")
        elif (au["source_start"], au["source_end"]) != (v["source_start"], v["source_end"]):
            warn.append(f"clip {k}: audio source range differs from video (slipped audio)")
        src = au or v
        rec_dur, src_dur = v["end"] - v["start"], v["source_end"] - v["source_start"]
        if rec_dur != src_dur:
            warn.append(f"clip {k}: record length {rec_dur} != source length {src_dur} (source fps differs from timeline fps)")
        items.append({
            "i": k, "name": v["name"], "media_pool_item_id": v["media_pool_item_id"], "file": v["file_path"],
            "rec_in": v["start"], "rec_out": v["end"], "src_in": v["source_start"], "src_out": v["source_end"],
            "fps": v["source_fps"], "audio_file": src["file_path"],
            "audio_t0": src["source_start"] / src["source_fps"], "dur": round(src_dur / v["source_fps"], 4),
        })
    gaps = sum(1 for p, n in zip(vt, vt[1:]) if p["end"] != n["start"])
    if gaps:
        warn.append(f"{gaps} gaps between clips on V{a.track} (fine, but the new timeline will be gap-free)")

    (W.d / "audio").mkdir(exist_ok=True)
    audio_map, offsets = {}, {}
    for f in sorted({it["audio_file"] for it in items}):
        out = W.d / "audio" / (re.sub(r"[^A-Za-z0-9_.-]", "_", Path(f).stem)[:40] + "_" + hashlib.md5(f.encode()).hexdigest()[:6] + ".wav")
        if not out.exists():
            print("extracting", f)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vn", "-ac", "1", "-ar", str(SR), "-c:a", "pcm_s16le", str(out)], check=True)
        audio_map[f] = str(out.relative_to(W.d))
        try:
            st_ = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a:0", "-show_entries", "stream=start_time",
                                  "-of", "csv=p=0", f], capture_output=True, text=True).stdout.strip()
            offsets[f] = float(st_) if st_ not in ("", "N/A") else 0.0
        except Exception:
            offsets[f] = None

    meta = {"timeline": st.get("name"), "timeline_id": st.get("id"), "start_frame": st.get("start_frame"),
            "start_timecode": st.get("start_timecode"), "track": a.track, "items": items, "audio": audio_map,
            "audio_start_offsets": offsets, "warnings": warn}
    save_json(meta, W.p("items.json"))
    total = sum(it["dur"] for it in items)
    print(f"{st.get('name')}: {len(items)} clips on V{a.track}, {total / 60:.2f} min, {len(audio_map)} source file(s)")
    for f, o in offsets.items():
        if o:
            print(f"  audio start offset {o:+.3f}s in {Path(f).name} (AAC priming; ~1 frame, normally ignore)")
    for w in warn[:20]:
        print("  WARN", w)
    if len(warn) > 20:
        print(f"  ... {len(warn) - 20} more warnings in items.json")


# ----------------------------------------------------------------------------- transcription

def cmd_sample(a):
    W = Work(a.work)
    its = [it for it in W.meta["items"] if it["dur"] >= 1.5]
    pick = [its[round(k * (len(its) - 1) / max(1, a.n - 1))] for k in range(min(a.n, len(its)))]
    for it in pick:
        text, _ = transcribe(W.clip_audio(it), language=a.language)
        print(f"{it['i']:4d} | {text}")


def write_listing(W):
    segs = load_json(W.p("segments.json"), [])
    its = W.items()
    first = min(it["rec_in"] for it in its.values())
    lines = []
    for s in segs:
        it = its[s["i"]]
        ws = " ".join(f"{k}:{w['w']}" for k, w in enumerate(s["words"])) or "(no speech)"
        lines.append(f"{s['i']:4d} {tc(it['rec_in'] - first, it['fps'])} {it['dur']:5.2f}s {s['rms_db']:6.1f}dB | {ws}")
    W.p("listing.txt").write_text("\n".join(lines), encoding="utf-8")
    return len(lines)


def clip_key(it):
    return f"{it['media_pool_item_id']}:{it['src_in']}:{it['src_out']}"


def cmd_transcribe(a):
    W = Work(a.work)
    hot = W.hotwords(a.hotwords)
    # cache by what the clip IS (media + source range) and the hotwords used - clip numbers shift when the
    # timeline is re-cut, and a transcript made with other hotwords may spell names differently
    cache = {} if a.force else {s["key"]: s for s in load_json(W.p("segments.json"), []) if s.get("key")
                                and s.get("hotwords") == hot}
    done, todo = {}, []
    for it in W.meta["items"]:
        s = cache.get(clip_key(it))
        if s:
            done[it["i"]] = dict(s, i=it["i"])
        else:
            todo.append(it)
    print(f"{len(done)} clips reused from cache, {len(todo)} to transcribe. Hotwords: {', '.join(hot) or '(none)'}")
    t0 = time.time()
    for n, it in enumerate(todo, 1):
        x = W.clip_audio(it)
        text, ws = transcribe(x, hot, a.language, words=True)
        done[it["i"]] = {"i": it["i"], "key": clip_key(it), "hotwords": hot, "text": text, "words": ws,
                         "rms_db": rms_db(x)}
        if n % 25 == 0 or n == len(todo):
            save_json([done[k] for k in sorted(done)], W.p("segments.json"))
            el = time.time() - t0
            print(f"  {n}/{len(todo)}  {el:.0f}s elapsed, ~{el / n * (len(todo) - n):.0f}s left")
    save_json([done[k] for k in sorted(done)], W.p("segments.json"))
    print(f"listing.txt: {write_listing(W)} clips")


def cmd_listing(a):
    print(f"listing.txt: {write_listing(Work(a.work))} clips")


# ----------------------------------------------------------------------------- verified cuts

def parse_keep(p):
    k = load_json(p)
    if k is None:
        sys.exit(f"{p} not found")
    dec = k.get("decisions", k)
    out = {}
    for seg, v in dec.items():
        if v == "all" or v is None:
            out[int(seg)] = "all"
        else:
            rs = []
            for ra, rb in v:
                conv = lambda x: None if x is None else (float(x[:-1]) if isinstance(x, str) and x.endswith("s") else int(x))
                rs.append((conv(ra), conv(rb)))
            out[int(seg)] = rs
    return out


FILLER_WORDS = {"uh", "um", "er", "ah", "eh", "hmm", "mm", "well", "oh"}


def norm(t):
    """Compare words without contractions: "we've"/"we", "i'm"/"i" (the model varies between them)."""
    return re.sub(r"'(ve|m|s|re|ll|d|t)$", "", t)


def match(t, w):
    """Does transcribed token t stand for expected word w?  Short words must match exactly
    ("well" is not "we", "to" is not "so"); longer ones fuzzily ("jeff"/"jev" is fine); a piece of a word
    with digits counts ("n eight n" is how "n8n" comes back)."""
    t, w = norm(t), norm(w)
    if t == w:
        return True
    if any(ch.isdigit() for ch in w) and t in w:
        return True
    if t in FILLER_WORDS or min(len(t), len(w)) < 4:
        return False
    return sim(t, w) >= 0.6


class CutFinder:
    """Find a cut time inside a clip whose kept side reads as expected, with no filler or extra word at the cut."""

    def __init__(self, W, it, seg, hot, language):
        self.W, self.it, self.hot, self.lang = W, it, hot, language
        self.words = seg["words"]
        self.wt = [toks(w["w"]) for w in self.words]
        self.fps = it["fps"]
        self.cache = {}

    def q(self, t):  # quantise to the frame grid - the check must hear exactly what Resolve will play
        return round(t * self.fps) / self.fps

    def text(self, t0, t1):
        key = (round(t0, 4), round(t1, 4))
        if key not in self.cache:
            self.cache[key] = toks(transcribe(self.W.clip_audio(self.it, t0, t1), self.hot, self.lang)[0])
        return self.cache[key]

    def expected(self, side, idx, other_idx):
        lo, hi = (idx, other_idx) if side == "start" else (other_idx, idx)
        lo = 0 if lo is None else lo
        hi = len(self.words) - 1 if hi is None else hi
        return [t for w in self.wt[lo:hi + 1] for t in w if not t.startswith("[")]

    def removed(self, side, idx):
        """Removed tokens right at the cut (up to 4, fillers excluded)."""
        span = self.wt[max(0, idx - 4):idx] if side == "start" else self.wt[idx + 1:idx + 5]
        return [t for w in span for t in w if not t.startswith("[")]

    def check(self, side, c, other_t, exp, rem):
        if side == "start":
            T = self.text(c, min(c + 2.0, other_t))
            edge, eedge = (T[0], exp[0]) if T and exp else (None, None)
            seq_exp, near_exp = exp[:len(T)], exp[:2]
        else:
            T = self.text(max(c - 2.0, other_t), c)
            edge, eedge = (T[-1], exp[-1]) if T and exp else (None, None)
            seq_exp, near_exp = exp[-len(T):] if T else [], exp[-2:]
        if not T:
            return False, T, "no speech"
        if edge.startswith("["):
            return False, T, "edge is a filler/noise tag"
        if not match(edge, eedge):
            return False, T, f"edge word {edge!r} != {eedge!r}"
        # full-clip and snippet transcripts differ ("now when you decide" vs "now we need to decide"): be lenient
        nT, nE = [norm(x) for x in T], [norm(x) for x in seq_exp]
        if SequenceMatcher(None, nT, nE).ratio() < 0.5:
            return False, T, "word sequence differs"
        # catch one extra word at the cut ("and one and one cool" for "and one cool", "agent you" for "agent"):
        # if the snippet lines up better once its edge word is dropped, and that word isn't expected there
        ratio = lambda x, y: SequenceMatcher(None, [norm(v) for v in x], [norm(v) for v in y]).ratio()
        if side == "start" and len(T) > 1 and ratio(T[1:5], exp[:4]) > ratio(T[:4], exp[:4]) + 0.2                 and not (len(exp) > 1 and match(T[0], exp[0]) and match(T[1], exp[1])):
            return False, T, f"extra word {T[0]!r} at the start"
        if side == "end" and len(T) > 1 and ratio(T[-5:-1], exp[-4:]) > ratio(T[-4:], exp[-4:]) + 0.2                 and not (len(exp) > 1 and match(T[-1], exp[-1]) and match(T[-2], exp[-2])):
            return False, T, f"extra word {T[-1]!r} at the end"
        # repeat guard: when the kept phrase repeats words that were just removed ("And one, | and one cool",
        # "I'm not going, | I'm not going to"), a snippet can't tell the copies apart - so the removed copy must
        # actually be audible on the other side of the cut
        if rem and any(match(a_, b_) for a_ in near_exp for b_ in rem):
            R = self.text(max(0.0, c - 2.5), c) if side == "start" else self.text(c, min(self.it["dur"], c + 2.5))
            near = R[-4:] if side == "start" else R[:4]
            if not any(match(x, r) or sim(norm(x), norm(r)) >= 0.75 for x in near for r in rem):
                return False, T, f"repeat guard: removed side {' '.join(near)!r} lacks {' '.join(rem)!r}"
        return True, T, ""

    def find(self, side, idx, other_idx, other_t, bound):
        """bound = (earliest, latest) clip time this cut may take (neighbouring ranges in the same clip)."""
        W = self.words
        guess = W[idx]["s"] if side == "start" else W[idx]["e"]
        dur = self.it["dur"]
        if side == "start":
            lo, hi = max(bound[0], guess - 0.5), min(other_t - 0.3, guess + 0.5)
        else:
            lo, hi = max(other_t + 0.3, guess - 0.5), min(bound[1], dur, guess + 0.5)
        exp, rem = self.expected(side, idx, other_idx), self.removed(side, idx)
        log = []
        if hi <= lo:
            return self.q(min(max(guess, bound[0]), bound[1])), False, None, [f"window collapsed around {guess:.2f}s"]
        a = self.W.clip_audio(self.it, lo, hi)
        e = env_db(a)
        mins = [k for k in range(1, len(e) - 1) if e[k] <= e[k - 1] and e[k] <= e[k + 1]]
        # real pauses (< -48 dB) first, deepest first; shallow dips between run-together words only after
        mins = sorted(mins, key=lambda k: (e[k] >= -48, e[k]))[:10]
        seen = set()
        for k in mins:  # 1) cut in the MIDDLE of the pause (the whole quiet stretch), like an editor would
            thr = -48 if e[k] < -48 else e[k] + 3
            l, r = k, k
            while l > 0 and e[l - 1] <= thr:
                l -= 1
            while r < len(e) - 1 and e[r + 1] <= thr:
                r += 1
            c = self.q(lo + ((l + r) / 2 + 0.5) * 0.01)
            if c in seen or not (lo <= c <= hi) or not (0 < c < dur):
                continue
            seen.add(c)
            ok, T, why = self.check(side, c, other_t, exp, rem)
            log.append(f"{c:6.3f}s {e[k]:5.0f}dB {'OK ' if ok else 'no '} {' '.join(T)[:80]}  {why}")
            if ok:
                return c, True, float(e[k]), log
        # 2) no pause: scan frame by frame (fused filler, words run together); need two passing frames in a row
        step = 1.0 / self.fps
        grid = [self.q(t) for t in np.arange(max(lo, guess - 0.4), min(hi, guess + 0.4), step)]
        passes = []
        for c in grid:
            ok, T, why = self.check(side, c, other_t, exp, rem)
            passes.append(ok)
            log.append(f"{c:6.3f}s  scan  {'OK ' if ok else 'no '} {' '.join(T)[:80]}  {why}")
        pick = None
        if side == "start":
            for k in range(len(grid) - 1):
                if passes[k] and passes[k + 1]:
                    pick = grid[k + 1]
                    break
        else:
            for k in range(len(grid) - 1, 0, -1):
                if passes[k] and passes[k - 1]:
                    pick = grid[k - 1]
                    break
        if pick is not None:
            return pick, True, None, log
        return self.q(guess), False, None, log


def cmd_verify(a):
    W = Work(a.work)
    its, hot = W.items(), W.hotwords()
    segs = {s["i"]: s for s in load_json(W.p("segments.json"), [])}
    keep = parse_keep(a.keep or W.p("keep.json"))
    edl, report, n_cuts, n_bad = [], [], 0, 0
    t_start = time.time()
    for i in sorted(keep):
        it, seg = its[i], segs[i]
        nw = len(seg["words"])
        rngs = [(None, None)] if keep[i] == "all" else keep[i]
        cf = CutFinder(W, it, seg, hot, a.language)
        prev_end = 0.0  # ranges in one clip are resolved in order and may never overlap
        for n_r, (ra, rb) in enumerate(rngs):
            ends = {}
            # word index 0 / last word = the clip's own edge (the editor's original cut) - no new cut needed
            ra = None if ra == 0 else ra
            rb = None if (isinstance(rb, int) and rb >= nw - 1) else rb
            t_in = 0.0 if ra is None else (ra if isinstance(ra, float) else seg["words"][ra]["s"])
            t_out = it["dur"] if rb is None else (rb if isinstance(rb, float) else seg["words"][rb]["e"])
            nxt = rngs[n_r + 1][0] if n_r + 1 < len(rngs) else None
            latest = (nxt if isinstance(nxt, float) else seg["words"][nxt]["e"]) if nxt is not None else it["dur"]
            bound = (prev_end + 1.0 / it["fps"], latest)
            for side, idx in (("start", ra), ("end", rb)):
                if idx is None:
                    ends[side] = {"kind": "edge", "t": 0.0 if side == "start" else it["dur"]}
                    continue
                if isinstance(idx, float):
                    ends[side] = {"kind": "manual", "t": cf.q(idx)}
                    continue
                n_cuts += 1
                other_idx = rb if side == "start" else ra
                other_t = t_out if side == "start" else t_in
                t, ok, db, log = cf.find(side, idx, other_idx if isinstance(other_idx, int) else None, other_t, bound)
                n_bad += not ok
                ends[side] = {"kind": "word", "word": idx, "t": t, "verified": ok, "db": db}
                if side == "start":
                    t_in = t
                else:
                    t_out = t
                w = seg["words"][idx]["w"]
                report.append(f"#{i} {side:5s} word {idx} {w!r} -> {'OK' if ok else 'UNVERIFIED'} at {t:.3f}s\n    " + "\n    ".join(log))
            f_in = it["src_in"] + round(ends["start"]["t"] * it["fps"])
            f_out = it["src_in"] + round(ends["end"]["t"] * it["fps"])
            f_in, f_out = max(it["src_in"], f_in), min(it["src_out"], f_out)
            if edl and edl[-1]["seg"] == i and f_in < edl[-1]["end_frame"]:  # safety net: never overlap
                report.append(f"#{i} range ({ra}, {rb}) overlapped the previous range - start moved to its end")
                f_in = edl[-1]["end_frame"]
            prev_end = (f_out - it["src_in"]) / it["fps"]
            if f_out - f_in < 3:
                report.append(f"#{i} range ({ra}, {rb}) is < 3 frames after verification - dropped")
                continue
            edl.append({"seg": i, "start_frame": f_in, "end_frame": f_out, "start": ends["start"], "end": ends["end"]})
    save_json(edl, W.p("edl.json"))
    W.p("cut_report.txt").write_text("\n".join(report), encoding="utf-8")
    orig = sum(it["src_out"] - it["src_in"] for it in its.values())
    new = sum(r["end_frame"] - r["start_frame"] for r in edl)
    fps = next(iter(its.values()))["fps"]
    print(f"{len(edl)} ranges, {new / fps / 60:.2f} min kept of {orig / fps / 60:.2f} ({100 * (orig - new) / orig:.0f}% removed). "
          f"{n_cuts - n_bad}/{n_cuts} internal cuts verified in {time.time() - t_start:.0f}s.")
    for line in report:
        if "UNVERIFIED" in line.split("\n")[0]:
            print("  UNVERIFIED:", line.split("\n")[0], "-> probe it (see cut_report.txt)")


# ----------------------------------------------------------------------------- QA

def cmd_qa(a):
    W = Work(a.work)
    its, hot = W.items(), W.hotwords()
    edl = load_json(W.p("edl.json"))
    for r in edl:
        it = its[r["seg"]]
        t0, t1 = (r["start_frame"] - it["src_in"]) / it["fps"], (r["end_frame"] - it["src_in"]) / it["fps"]
        r["qa"] = transcribe(W.clip_audio(it, t0, t1), hot, a.language)[0]
    save_json(edl, W.p("qa.json"))
    flags = []
    for k, r in enumerate(edl):
        q = r["qa"]
        if "[" in q:
            flags.append(f"{k:4d} #{r['seg']}: filler/noise tag  | {q}")
        if re.search(r"\w-(?=\s|$|[.,?!])", q):
            flags.append(f"{k:4d} #{r['seg']}: cut-off word     | {q}")
        m = re.search(r"\b(\w+)[,.]?\s+\1\b", q, re.I)
        if m:
            flags.append(f"{k:4d} #{r['seg']}: repeated '{m.group(1)}' (natural or stutter?) | {q}")
        if k and toks(edl[k - 1]["qa"])[-1:] == toks(q)[:1] and toks(q):
            flags.append(f"{k:4d} #{edl[k - 1]['seg']}->#{r['seg']}: same word both sides of the cut | "
                         f"...{edl[k - 1]['qa'][-40:]} || {q[:40]}...")
        if not toks(q):
            flags.append(f"{k:4d} #{r['seg']}: no speech in kept range")
    lines = [f"QA of {len(edl)} kept ranges. {len(flags)} flag(s).",
             "Note: a clipped word at the very end of a range can be 'completed' by the model (e.g. 'a l-' -> 'a little bit'),",
             "so a phrase that seems duplicated across a cut may be an artifact - confirm with `probe` before re-cutting.", ""]
    lines += flags + ["", "---- full cut, in order ----"]
    lines += [f"{k:4d} #{r['seg']:<4d} {(r['end_frame'] - r['start_frame']) / its[r['seg']]['fps']:5.2f}s | {r['qa']}" for k, r in enumerate(edl)]
    W.p("qa.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:4 + len(flags)]))


# ----------------------------------------------------------------------------- probe

def cmd_probe(a):
    W = Work(a.work)
    it, hot = W.items()[a.clip], W.hotwords()
    seg = {s["i"]: s for s in load_json(W.p("segments.json"), [])}.get(a.clip)
    if seg:
        print("words:", " ".join(f"{k}:{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for k, w in enumerate(seg["words"])
                                 if a.frm - 0.5 <= w["s"] <= a.to + 0.5))
    e = env_db(W.clip_audio(it, a.frm, a.to), hop=320)
    print(f"loudness (dB, 20 ms steps from {a.frm:.2f}s):", " ".join(f"{v:.0f}" for v in e))
    q = lambda t: round(t * it["fps"]) / it["fps"]
    for t in np.arange(a.frm, a.to, a.step):
        t = q(t)
        end = transcribe(W.clip_audio(it, t - 2.0, t), hot, a.language)[0]
        start = transcribe(W.clip_audio(it, t, t + 1.8), hot, a.language)[0]
        print(f"  {t:6.3f}s  END ...{end[-38:]:38s} | START {start[:44]}")


# ----------------------------------------------------------------------------- build helpers

def cmd_clipinfos(a):
    W = Work(a.work)
    its = W.items()
    segs = {s["i"]: s for s in load_json(W.p("segments.json"), [])}
    edl = load_json(W.p("edl.json"))
    infos, markers, rec = [], [], 0
    for k, r in enumerate(edl):
        it = its[r["seg"]]
        ratio = (it["rec_out"] - it["rec_in"]) / (it["src_out"] - it["src_in"])
        infos.append({"media_pool_item_id": it["media_pool_item_id"], "start_frame": r["start_frame"],
                      "end_frame": r["end_frame"], "record_frame": rec})
        if k:
            p = edl[k - 1]
            words = segs[r["seg"]]["words"]
            pw = segs[p["seg"]]["words"]
            note = None
            if "manual" in (p["end"]["kind"], r["start"]["kind"]):
                note = ("Listen: hand-placed cut", "Cut point set manually after probing.")
            elif p["seg"] == r["seg"] and (r["start_frame"] - p["end_frame"]) < 0.5 * it["fps"]:
                note = ("Listen: micro-cut", "Short piece removed inside continuous speech.")
            elif p["end"]["kind"] == "word" and not re.search(r"[.?!]$", pw[p["end"]["word"]]["w"]) and p["seg"] != r["seg"]:
                note = ("Listen: spliced takes", "Sentence joined across two takes.")
            if False in (p["end"].get("verified", True), r["start"].get("verified", True)):
                note = ("Check: unverified cut", "Automatic verification failed here; placed at the model timestamp.")
            if note:  # quote the words either side of the cut, found by time (works for hand-placed cuts too)
                pit = its[p["seg"]]
                p_end = (p["end_frame"] - pit["src_in"]) / pit["fps"]
                r_in = (r["start_frame"] - it["src_in"]) / it["fps"]
                if p["end"]["kind"] == "word":  # word positions are exact; timestamps are only approximate
                    bw = pw[max(0, p["end"]["word"] - 3):p["end"]["word"] + 1]
                else:
                    bw = [w for w in pw if w["s"] < p_end - 0.05][-4:]
                if r["start"]["kind"] == "word":
                    aw = words[r["start"]["word"]:r["start"]["word"] + 4]
                else:
                    aw = [w for w in words if w["e"] > r_in + 0.05][:4]
                before, after = " ".join(w["w"] for w in bw), " ".join(w["w"] for w in aw)
                markers.append({"frame": rec, "color": "Yellow", "name": note[0], "duration": 1,
                                "note": f"{note[1]} '...{before}' | '{after}...'"})
        rec += round((r["end_frame"] - r["start_frame"]) * ratio)
    save_json(infos, W.p("clip_infos.json"))
    save_json(markers, W.p("markers.json"))
    fps = next(iter(its.values()))["fps"]
    print(f"clip_infos.json: {len(infos)} clips, {rec} frames ({rec / fps / 60:.2f} min). markers.json: {len(markers)} review markers.")


def cmd_check_build(a):
    W = Work(a.work)
    st = load_json(a.structure)
    st = st.get("result", st)
    plan = load_json(a.clip_infos or W.p("clip_infos.json"))
    S = st["start_frame"]
    v = next(t for t in st["tracks"]["video"]["tracks"] if t["track_index"] == 1)["items"]
    au = next(t for t in st["tracks"]["audio"]["tracks"] if t["track_index"] == 1)["items"]
    print(f"{st['name']}: V1 {len(v)} items, A1 {len(au)} items, plan {len(plan)} clips, "
          f"frames {st['end_frame'] - S} vs planned {plan[-1]['record_frame'] + plan[-1]['end_frame'] - plan[-1]['start_frame']}")
    exact, off1, bad = 0, [], []
    for n, p in enumerate(plan):
        exp = (p["media_pool_item_id"], p["start_frame"], p["end_frame"], S + p["record_frame"],
               S + p["record_frame"] + p["end_frame"] - p["start_frame"])
        for track in (v, au):
            if n >= len(track):
                bad.append((n, "missing"))
                continue
            x = track[n]
            got = (x["media_pool_item_id"], x["source_start"], x["source_end"], x["start"], x["end"])
            if got == exp:
                exact += 1
            elif got[0] == exp[0] and got[3:] == exp[3:] and abs(got[1] - exp[1]) == 1 and got[2] - got[1] == exp[2] - exp[1]:
                off1.append(n)
            else:
                bad.append((n, x["track_type"], exp, got))
    offline = [x["name"] for x in v + au if x.get("media_status") not in (None, "Online")]
    print(f"exact {exact}/{2 * len(plan)} items; 1-frame source readback shifts: {sorted(set(off1))}; mismatches: {len(bad)}; offline: {len(offline)}")
    for b in bad[:10]:
        print("  MISMATCH", b)
    if off1:
        print("  (a +-1 source-frame readback with correct length and position is a known Resolve reporting quirk)")


# ----------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, **kw):
        p = sub.add_parser(name, **kw)
        p.add_argument("--work", required=True, help="work directory for this timeline")
        p.add_argument("--language", default="en")
        p.set_defaults(fn=fn)
        return p

    p = add("prepare", cmd_prepare); p.add_argument("--structure", required=True); p.add_argument("--track", type=int, default=1)
    p = add("sample", cmd_sample); p.add_argument("--n", type=int, default=30)
    p = add("transcribe", cmd_transcribe); p.add_argument("--hotwords"); p.add_argument("--force", action="store_true")
    add("listing", cmd_listing)
    p = add("verify", cmd_verify); p.add_argument("--keep")
    add("qa", cmd_qa)
    p = add("probe", cmd_probe); p.add_argument("--clip", type=int, required=True)
    p.add_argument("--from", dest="frm", type=float, required=True); p.add_argument("--to", type=float, required=True)
    p.add_argument("--step", type=float, default=0.04)
    add("clipinfos", cmd_clipinfos)
    p = add("check-build", cmd_check_build); p.add_argument("--structure", required=True); p.add_argument("--clip-infos")
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
