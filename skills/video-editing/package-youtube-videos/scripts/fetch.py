"""Download YouTube thumbnails for research.   python fetch.py <ids.tsv> [out dir = research/thumbs]

ids.tsv: one video per line, the video id first (anything after a tab is ignored). Saves <id>.jpg (maxres, falling
back to hq). Skips files that already exist. These are other people's thumbnails: use them to look and compare,
never as assets.
"""
import sys, os, urllib.request
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else os.path.join("research", "thumbs"); os.makedirs(out, exist_ok=True)
n = 0
for line in open(src, encoding="utf-8"):
    vid = line.strip().split("\t")[0]
    if not vid or os.path.exists(os.path.join(out, vid + ".jpg")): continue
    for q in ("maxresdefault", "hqdefault"):
        try:
            data = urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/{q}.jpg", timeout=20).read()
            if len(data) > 2000: open(os.path.join(out, vid + ".jpg"), "wb").write(data); n += 1; break
        except Exception: continue
    else: print("failed", vid)
print("fetched", n, "into", out)
