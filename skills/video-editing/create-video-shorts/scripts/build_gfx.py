import sys, json, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_gfx_common as G
which = sys.argv[1:] or ['s1', 's2', 's3']
for w in which:
    __import__('gfx_' + w).build()
old = json.load(open('gfx/sfx_events.json')) if os.path.exists('gfx/sfx_events.json') else {}
old.update(G.SFX)
json.dump(old, open('gfx/sfx_events.json', 'w'), indent=1)
print('built', list(G.SFX))
