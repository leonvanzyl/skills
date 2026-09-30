"""Build the HyperFrames pages for every gfx beat: imports scripts/gfx_<name>.py modules and calls their build().
usage: python scripts/build_gfx.py [name ...]      (default: every scripts/gfx_*.py)"""
import sys, json, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_gfx_common as G
names = sys.argv[1:] or [os.path.basename(f)[4:-3] for f in glob.glob('scripts/gfx_*.py')]
for n in names:
    __import__('gfx_' + n).build()
old = json.load(open('gfx/sfx_events.json')) if os.path.exists('gfx/sfx_events.json') else {}
old.update(G.SFX)
json.dump(old, open('gfx/sfx_events.json', 'w'), indent=1)
print('built', list(G.SFX))
