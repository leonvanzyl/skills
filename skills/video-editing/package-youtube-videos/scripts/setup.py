"""Set up a packaging work folder.   python setup.py <work folder>

Creates the folders the workflow writes to and copies in what every run needs: Leon's two reference portraits, the
official Claude mark, and the prompts. Creates the results ledger (~/.yt-packaging/ledger.md) if it does not exist.
Prints the Python to use and the skill path.
The work folder belongs next to the video (or in ~/Videos/packaging-<slug>), never inside a code or skills repository.
"""
import os, sys, shutil, subprocess
SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if len(sys.argv) < 2: sys.exit(__doc__)
W = os.path.abspath(sys.argv[1])
anc = W                                                    # nearest folder that exists (the work folder may be new)
while not os.path.isdir(anc) and os.path.dirname(anc) != anc: anc = os.path.dirname(anc)
try:
    r = subprocess.run(["git", "-C", anc, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if r.stdout.strip() == "true": sys.exit(f"REFUSED: {W} is inside a git repository. Put it next to the video instead.")
except FileNotFoundError: pass
for d in ("video", "research/thumbs", "refs/leon", "refs/logos", "refs/ui", "briefs", "build", "build/likeness", "out", "panel/sheets",
          "qa/final", "final", "report/img"):
    os.makedirs(os.path.join(W, d), exist_ok=True)
for sub in ("leon", "logos"):
    for f in os.listdir(os.path.join(SKILL, "assets", sub)): shutil.copyfile(os.path.join(SKILL, "assets", sub, f), os.path.join(W, "refs", sub, f))
for f in os.listdir(os.path.join(SKILL, "assets", "prompts")): shutil.copyfile(os.path.join(SKILL, "assets", "prompts", f), os.path.join(W, "briefs", f))
ledger = os.path.join(os.path.expanduser("~"), ".yt-packaging", "ledger.md")
if not os.path.exists(ledger):
    os.makedirs(os.path.dirname(ledger), exist_ok=True)
    open(ledger, "w", encoding="utf-8", newline="\n").write(
        "# Test & Compare results ledger\n\nOne entry per test, newest first (format in the skill's references/test-plan.md).\n"
        "A short list of experiments, never a rule book.\n\n(no entries yet)\n")
    print("ledger created (empty):", ledger)
else: print("ledger:", ledger)
try:
    import PIL, numpy, cv2  # noqa
    print("python ok:", sys.executable)
except ImportError as e:
    print("MISSING python package:", e, "-> pip install pillow numpy opencv-python-headless")
if not shutil.which("codex") and not shutil.which("codex.cmd"): print("WARNING: the Codex CLI is not on PATH; image generation (gen.py) will not run")
print("work:", W); print("skill:", SKILL)
