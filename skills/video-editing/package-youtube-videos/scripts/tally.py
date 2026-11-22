"""Tally the blind read test, by viewer.   python tally.py [panel dir = panel]

Reads key.json and every viewer_<persona>.json or viewer_<persona>__<batch>.json in the panel folder (batches of one
persona are added together). Prints, and writes tally.json:
- the CHECK ON THE TEST ITSELF: for each persona, how often ours were tapped against how often the real videos on the
  same sheets were tapped. If ours are tapped at more than about twice the real rate, the viewers probably spotted the
  test items: discard the taps and keep only the reads.
- for each of our thumbnails: taps out of viewings per persona (never one pooled number: a viewer's interests decide
  far more than the thumbnail does), how often the title was needed to understand it, and each persona's read of it.
- the same pooled by concept (the first three characters of the id: c05 and c05_b together), under "concepts".
"""
import sys, os, json, glob, re
P = sys.argv[1] if len(sys.argv) > 1 else "panel"
key = json.load(open(os.path.join(P, "key.json")))
def norm(k): return os.path.splitext(os.path.basename(str(k)))[0]
files = sorted(glob.glob(os.path.join(P, "viewer_*.json")))
if not files: sys.exit("no viewer_*.json files in " + P)
T = {}; base = {}
for vf in files:
    vid = os.path.basename(vf)[7:-5].split("__")[0]; v = {norm(k): a for k, a in json.load(open(vf, encoding="utf-8")).items()}
    b = base.setdefault(vid, {"ours": [0, 0], "real": [0, 0]})
    for sheet, tiles in key.items():
        if sheet not in v: continue                                  # this agent was not given this sheet
        a = v[sheet] or {}; tap = [int(x) for x in a.get("tap", [])]; unclear = [int(x) for x in a.get("unclear", [])]
        for num, cid in tiles.items():
            n = int(num); is_real = cid.startswith("real")
            side = b["real" if is_real else "ours"]; side[0] += n in tap; side[1] += 1
            if is_real: continue
            r = T.setdefault(cid, {"viewers": {}, "unclear": 0, "reads": {}})
            pv = r["viewers"].setdefault(vid, {"shown": 0, "tap": 0, "first": 0})
            pv["shown"] += 1; pv["tap"] += n in tap; pv["first"] += bool(tap) and n == tap[0]; r["unclear"] += n in unclear
            rd = (a.get("reads") or {}).get(str(num))
            if rd: r["reads"].setdefault(vid, []).append(rd)
vids = sorted(base)
print("CHECK ON THE TEST: taps on ours vs taps on the real videos beside them")
suspect = []
for v in vids:
    o, r = base[v]["ours"], base[v]["real"]; ro = o[0] / max(1, o[1]); rr = r[0] / max(1, r[1])
    flag = ro > 2 * rr and o[0] >= 3
    if flag: suspect.append(v)
    print("  %-14s ours %d/%d = %.0f%%   real %d/%d = %.0f%%%s" % (v, o[0], o[1], 100 * ro, r[0], r[1], 100 * rr, "   <-- ours tapped at more than twice the real rate" if flag else ""))
if suspect: print("  WARNING: %s probably spotted the test items. Discard these taps; keep the reads." % ", ".join(suspect))
print("\n%-8s " % "id" + " ".join(v[:12].ljust(12) for v in vids) + " needed title")
def line(name, r): print("%-8s " % name + " ".join(("%d/%d" % (r["viewers"].get(v, {}).get("tap", 0), r["viewers"].get(v, {}).get("shown", 0))).ljust(12) for v in vids) + " %d" % r["unclear"])
for cid in sorted(T): line(cid, T[cid])
C = {}
for cid, r in T.items():
    c = C.setdefault(cid[:3], {"viewers": {}, "unclear": 0, "versions": []}); c["versions"].append(cid); c["unclear"] += r["unclear"]
    for v, pv in r["viewers"].items():
        cv = c["viewers"].setdefault(v, {"shown": 0, "tap": 0, "first": 0})
        for k in cv: cv[k] += pv[k]
print("\nby concept (versions pooled)")
for c in sorted(C): line(c, C[c])
json.dump({"test_check": {"by_viewer": base, "suspect": suspect}, "ours": T, "concepts": C}, open(os.path.join(P, "tally.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("-> " + os.path.join(P, "tally.json"))
