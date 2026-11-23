"""Image generation through the Codex CLI (ChatGPT image model).

  python gen.py --prompt build/c01/p1.txt --out build/c01/t1.png [--ref LABEL=path ...] [--takes 2] [--aspect 16:9]

- The prompt file is plain text: the art direction. Reference images are attached in order and listed for the model
  as "Image 1: LABEL", "Image 2: LABEL" ... (max 5). To EDIT an existing image, pass it as the first ref
  (e.g. --ref "BASE (the image to edit)=build/c01/t2.png") and write the prompt as an edit instruction.
- --takes N writes <out stem>_1.png ... _N.png in parallel (each an independent generation).
- A machine-wide queue (max 8 generations at once, across every agent) keeps us under rate limits: a call may wait.
- Rate limits (added 2026-11-23, after ten designers starting together got "429 Too Many Requests" on three renders in
  four and retried at once, which kept the limit saturated): starts are spaced SPACING seconds apart machine-wide, and
  a take that is rate-limited sets a machine-wide cooldown, waits, and tries again by itself (up to RETRIES times).
  So a call can take many minutes when the service is busy. Do not re-run it yourself while it is waiting.
- Prints one line per take: path, size, seconds; or "<path>: ERROR ...". ~60-120 s per image. Exits 1 if any take
  failed, 2 on a bad argument: check the output before using a file.
"""
import sys, os, json, glob, shutil, subprocess, time, argparse, random
from concurrent.futures import ThreadPoolExecutor
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CODEX_HOME = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
CODEX = shutil.which("codex") or shutil.which("codex.cmd") or "codex"
STATE = os.path.join(os.path.expanduser("~"), ".yt-packaging")
SLOTS = os.path.join(STATE, "_gen_slots"); MAX = 8
COOL = os.path.join(STATE, "_gen_cooldown")       # epoch seconds: no generation starts before this
LAST = os.path.join(STATE, "_gen_last_start")     # epoch seconds of the last start, machine-wide
STREAK = os.path.join(STATE, "_gen_429_streak")   # rate-limited takes in a row, machine-wide
GATE = os.path.join(STATE, "_gen_gate")           # a short lock, so two processes never take the same turn
SPACING = 25; RETRIES = 10
SHAPE = {"16:9": "one 16:9 landscape image", "1:1": "one square image", "3:2": "one 3:2 landscape image",
         "2:3": "one 2:3 portrait image", "9:16": "one 9:16 portrait image"}

def _read(p):
    try: return float(open(p).read().strip() or 0)
    except Exception: return 0.0
def _write(p, v):
    try: open(p, "w").write("%.0f" % v)
    except OSError: pass

def _gate():
    """Hold the gate file for a moment. Returns True when held (the caller must remove it)."""
    try:
        if os.path.exists(GATE) and time.time() - os.path.getmtime(GATE) > 30: os.remove(GATE)   # stale
        fd = os.open(GATE, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd); return True
    except OSError: return False
def _ungate():
    try: os.remove(GATE)
    except OSError: pass

def wait_turn():
    """Machine-wide pacing: wait out any cooldown a rate-limited take set, and keep starts SPACING seconds apart."""
    os.makedirs(STATE, exist_ok=True)
    while True:
        if not _gate(): time.sleep(0.5 + random.random()); continue
        try:
            now = time.time(); until = max(_read(COOL), _read(LAST) + SPACING)
            if now >= until: _write(LAST, now); return
        finally: _ungate()
        time.sleep(min(10, max(1, until - now)) + random.random() * 2)

def rate_limited():
    """A take came back 429: lengthen the machine-wide cooldown (45 s more for every rate-limited take in a row, up to
    5 minutes) so every waiting generation backs off together."""
    while not _gate(): time.sleep(0.3 + random.random() * 0.5)
    try:
        n = int(_read(STREAK)) + 1; _write(STREAK, n)
        until = time.time() + min(45 * n, 300) + random.random() * 10
        if until > _read(COOL): _write(COOL, until)
    finally: _ungate()

def said_rate_limited(stdout):
    """True when the tool reported a rate limit. Everything in its output counts EXCEPT what the model itself wrote
    (its messages and reasoning): a thumbnail ABOUT rate limits can make the model write "429 Too Many Requests", and
    a failed render must not then be mistaken for a refusal and retried ten times with everyone held back."""
    kept = []
    for line in stdout.splitlines():
        try: e = json.loads(line)
        except Exception: e = None
        if isinstance(e, dict):
            item = e.get("item") if isinstance(e.get("item"), dict) else {}
            if item.get("type") in ("agent_message", "reasoning") or e.get("type") in ("agent_message", "reasoning"): continue
        kept.append(line)
    text = "\n".join(kept)
    return ("429" in text and "Too Many Requests" in text) or "rate limit" in text.lower()

def acquire():
    os.makedirs(SLOTS, exist_ok=True)
    while True:
        for i in range(MAX):
            p = os.path.join(SLOTS, f"slot{i}")
            try:
                if os.path.exists(p) and time.time() - os.path.getmtime(p) > 1200: os.remove(p)   # stale
                fd = os.open(p, os.O_CREAT | os.O_EXCL | os.O_WRONLY); os.close(fd); return p
            except FileExistsError: continue
            except OSError: continue
        time.sleep(3 + random.random() * 3)

def one(prompt, refs, out, aspect):
    legend = ""
    if refs:
        legend = "Attached images, in order:\n" + "\n".join(f"Image {i+1}: {l}" for i, (l, _) in enumerate(refs)) + "\n\n"
    full = legend + prompt.strip() + f"\n\nUse your image generation tool once and output exactly {SHAPE[aspect]}. Do not ask questions; do not write files; just generate the image."
    cmd = [CODEX, "exec", "--json", "--skip-git-repo-check", "-s", "read-only"]
    for _, f in refs: cmd += ["-i", os.path.abspath(f)]
    cmd += ["-"]
    log = os.path.splitext(out)[0] + ".log.jsonl"; t0 = time.time()
    for attempt in range(1, RETRIES + 1):
        wait_turn(); slot = acquire()
        try:
            r = subprocess.run(cmd, input=full, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
        except Exception as e:
            return f"{out}: ERROR {e}"
        finally:
            try: os.remove(slot)
            except OSError: pass
        open(log, "w", encoding="utf-8").write(r.stdout + ("\n# STDERR\n" + r.stderr if r.stderr else ""))
        tid = None
        for line in r.stdout.splitlines():
            try: e = json.loads(line)
            except Exception: continue
            if e.get("type") == "thread.started": tid = e.get("thread_id"); break
        found = sorted(glob.glob(os.path.join(CODEX_HOME, "generated_images", tid, "*.png")), key=os.path.getmtime) if tid else []
        if found:
            _write(STREAK, 0)
            shutil.copyfile(found[-1], out)
            from PIL import Image
            w, h = Image.open(out).size
            return f"{out} {w}x{h} {time.time()-t0:.0f}s" + (f" (after {attempt - 1} rate-limited tries)" if attempt > 1 else "")
        if said_rate_limited(r.stdout):
            rate_limited(); continue                       # back off with everyone else, then try again
        if not tid: return f"{out}: ERROR no thread id (exit {r.returncode}), see {log}"
        return f"{out}: ERROR no image generated, see {log}"
    return f"{out}: ERROR still rate-limited (429) after {RETRIES} tries over {time.time()-t0:.0f}s, see {log}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--ref", action="append", default=[]); ap.add_argument("--takes", type=int, default=1)
    ap.add_argument("--aspect", default="16:9")
    a = ap.parse_args()
    prompt = open(a.prompt, encoding="utf-8").read()
    refs = []
    for r in a.ref:
        l, _, f = r.partition("=")
        if not os.path.exists(f): print(f"MISSING ref {f}"); sys.exit(2)
        refs.append((l, f))
    if len(refs) > 5: print("TOO MANY refs (max 5)"); sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    stem, ext = os.path.splitext(a.out)
    outs = [a.out] if a.takes == 1 else [f"{stem}_{k}{ext}" for k in range(1, a.takes + 1)]
    failed = 0
    with ThreadPoolExecutor(len(outs)) as ex:
        for msg in ex.map(lambda o: one(prompt, refs, o, a.aspect), outs):
            print(msg, flush=True); failed += ": ERROR" in msg
    if failed: print(f"{failed} of {len(outs)} takes FAILED"); sys.exit(1)

if __name__ == "__main__": main()
