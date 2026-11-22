"""Image generation through the Codex CLI (ChatGPT image model).

  python gen.py --prompt build/c01/p1.txt --out build/c01/t1.png [--ref LABEL=path ...] [--takes 3] [--aspect 16:9]

- The prompt file is plain text: the art direction. Reference images are attached in order and listed for the model
  as "Image 1: LABEL", "Image 2: LABEL" ... (max 5). To EDIT an existing image, pass it as the first ref
  (e.g. --ref "BASE (the image to edit)=build/c01/t2.png") and write the prompt as an edit instruction.
- --takes N writes <out stem>_1.png ... _N.png in parallel (each an independent generation).
- A machine-wide queue (max 8 generations at once, across every agent) keeps us under rate limits: a call may wait.
- Prints one line per take: path, size, seconds; or "<path>: ERROR ...". ~60-120 s per image. Exits 1 if any take
  failed, 2 on a bad argument: check the output before using a file.
"""
import sys, os, json, glob, shutil, subprocess, time, argparse, random
from concurrent.futures import ThreadPoolExecutor
if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CODEX_HOME = os.environ.get("CODEX_HOME") or os.path.join(os.path.expanduser("~"), ".codex")
CODEX = shutil.which("codex") or shutil.which("codex.cmd") or "codex"
SLOTS = os.path.join(os.path.expanduser("~"), ".yt-packaging", "_gen_slots"); MAX = 8
SHAPE = {"16:9": "one 16:9 landscape image", "1:1": "one square image", "3:2": "one 3:2 landscape image",
         "2:3": "one 2:3 portrait image", "9:16": "one 9:16 portrait image"}

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
    slot = acquire(); t0 = time.time()
    try:
        r = subprocess.run(cmd, input=full, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
    except Exception as e:
        return f"{out}: ERROR {e}"
    finally:
        try: os.remove(slot)
        except OSError: pass
    log = os.path.splitext(out)[0] + ".log.jsonl"
    open(log, "w", encoding="utf-8").write(r.stdout + ("\n# STDERR\n" + r.stderr if r.stderr else ""))
    tid = None
    for line in r.stdout.splitlines():
        try: e = json.loads(line)
        except Exception: continue
        if e.get("type") == "thread.started": tid = e.get("thread_id"); break
    if not tid: return f"{out}: ERROR no thread id (exit {r.returncode}), see {log}"
    found = sorted(glob.glob(os.path.join(CODEX_HOME, "generated_images", tid, "*.png")), key=os.path.getmtime)
    if not found: return f"{out}: ERROR no image generated, see {log}"
    shutil.copyfile(found[-1], out)
    from PIL import Image
    w, h = Image.open(out).size
    return f"{out} {w}x{h} {time.time()-t0:.0f}s"

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
