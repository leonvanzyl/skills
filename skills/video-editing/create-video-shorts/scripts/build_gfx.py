import sys, json, os, time, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_gfx_common as G
# usage: build_gfx.py [tag ...]   (tag = the suffix of scripts/gfx_<tag>.py: a short like s1, or a graphics subagent's
# own module like s1a / s1b). With no tag every scripts/gfx_*.py is built.
which = sys.argv[1:] or sorted(os.path.basename(f)[4:-3] for f in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gfx_*.py')))
for w in which:
    __import__('gfx_' + w).build()
# several graphics subagents build at once: serialise the read-modify-write of the shared events files with a lock dir
lock = 'gfx/.sfx_events.lock'
for _ in range(600):
    try: os.mkdir(lock); break
    except FileExistsError: time.sleep(0.05)
try:
    for f, new in (('gfx/sfx_events.json', G.SFX), ('gfx/thumbs.json', G.THUMBS)):
        old = json.load(open(f)) if os.path.exists(f) else {}
        old.update(new)
        json.dump(old, open(f, 'w'), indent=1)
finally:
    try: os.rmdir(lock)
    except OSError: pass
print('built', list(G.SFX))
