"""Free the disk space a pro edit used - only after the user has said the video is uploaded and it is safe.
A finished 25-minute 4K edit left ~63 GB behind (last-call, 2026-10-16): every render Resolve links to, the stems and
the picture for the master, the final file, graphics frames, level checks, transcripts and caches.

  $PY "$SKILL/scripts/cleanup.py" "$M"              dry run: what would go and how big it is - nothing is deleted
  $PY "$SKILL/scripts/cleanup.py" "$M" --delete     delete it, then measure again and report what is left

Run it from the skill (not from W/scripts) with a cwd outside W, since W itself is deleted.

What goes:
  - every work dir of this project: each W under the work root whose project.json names this media dir (the clean
    cut's and any "__Recut" one) - caches, transcripts, graphics frames, previews, level checks, stems;
  - everything inside M (pro-edit-media): the renders the Pro Edit timeline links to, review/, _deliver/ and final/ -
    the uploaded file too. Kept: report.md, PUBLISH.md and captions.srt (a few KB; --all removes them as well).
What never goes: the source recordings and anything else outside W and M, the user's Resolve project and timelines
(after the cleanup the Pro Edit timeline's added clips show as media offline - say so before asking), and the shared
caches (the venvs, ~/.cache/pro-edit-models, the skill's SFX library, HyperFrames).
Safety: M must be named "pro-edit-media" and be the media_dir of at least one work dir's project.json; a work dir
must sit directly under the work root and hold project.json. Symlinks are removed, never followed."""
import sys, os, json, shutil, argparse, stat

ap = argparse.ArgumentParser()
ap.add_argument('media'); ap.add_argument('--delete', action='store_true'); ap.add_argument('--all', action='store_true')
a = ap.parse_args()
KEEP = set() if a.all else {'report.md', 'PUBLISH.md', 'captions.srt'}


def norm(p): return os.path.normcase(os.path.realpath(os.path.abspath(p)))


def size(p):
    if os.path.islink(p): return 0
    if os.path.isfile(p): return os.path.getsize(p)
    t = 0
    for root, dirs, files in os.walk(p):
        for f in files:
            fp = os.path.join(root, f)
            if not os.path.islink(fp):
                try: t += os.path.getsize(fp)
                except OSError: pass
    return t


def gb(n): return f'{n / 1e9:.1f} GB' if n >= 1e8 else f'{n / 1e6:.1f} MB'


M = os.path.abspath(a.media)                    # as given, for display; compared through norm()
if os.path.basename(norm(M)) != 'pro-edit-media' or not os.path.isdir(M):
    sys.exit(f'refusing: {a.media} is not a pro-edit-media folder')
roots, seen = [], set()
for r in [os.environ.get('PRO_EDIT_WORK_ROOT') or '',
          os.path.join(os.environ.get('LOCALAPPDATA') or os.path.expanduser('~/.cache'), 'video-pro-edit'),
          os.path.expanduser('~/.cache/video-pro-edit')]:
    if r and os.path.isdir(r) and norm(r) not in seen: roots.append(os.path.abspath(r)); seen.add(norm(r))
works = []
for r in roots:
    for d in sorted(os.listdir(r)):
        w = os.path.join(r, d); pj = os.path.join(w, 'project.json')
        try: md = json.load(open(pj, encoding='utf-8')).get('media_dir')
        except Exception: continue
        if md and norm(md) == norm(M): works.append(w)
if not works: sys.exit(f'refusing: no work dir under {roots} names {M} as its media_dir')
if any(norm(os.getcwd()).startswith(norm(w)) for w in works): sys.exit('refusing: run it with a cwd outside the work dirs')

targets = [(w, size(w)) for w in works]
targets += [(os.path.join(M, n), size(os.path.join(M, n))) for n in sorted(os.listdir(M)) if n not in KEEP]
total = sum(s for _, s in targets)
print(('DELETING' if a.delete else 'DRY RUN - would delete') + f' {gb(total)}:')
for p, s in sorted(targets, key=lambda t: -t[1])[:25]: print(f'  {gb(s):>9}  {p}')
if len(targets) > 25: print(f'  ... and {len(targets) - 25} more items in {M}')
print('keeping in M:', ', '.join(sorted(n for n in os.listdir(M) if n in KEEP)) or 'nothing')
if not a.delete:
    print('nothing deleted - rerun with --delete once the user has confirmed the upload'); sys.exit(0)


def onerr(func, path, exc):                      # read-only files (Windows) - make writable and retry once
    try: os.chmod(path, stat.S_IWRITE); func(path)
    except Exception as e: failed.append((path, str(e)))


failed = []
for p, _ in targets:
    try:
        if os.path.islink(p) or os.path.isfile(p): os.remove(p)
        elif os.path.isdir(p): shutil.rmtree(p, onerror=onerr)
    except Exception as e: failed.append((p, str(e)))
if a.all and os.path.isdir(M) and not os.listdir(M): os.rmdir(M)
left = sum(size(p) for p, _ in targets if os.path.exists(p))
print(f'freed {gb(total - left)}; left behind {gb(left)}')
for p, e in failed[:10]: print('  could not delete', p, '-', e)
# A packaged app's view of AppData is virtualised: it can report a work dir gone while the real folder (made by
# Resolve's renders) is still there - on last-call an empty last-call__Recut/levels was left. Check and finish from
# inside Resolve, which sees the real disk:
print('Confirm from inside Resolve (script_plugin run_inline) - it sees the real disk:\n  import os, shutil\n' +
      ''.join(f"  p = r'{w}'; print(p, os.path.exists(p) and sum(len(f) for _, _, f in os.walk(p)))\n"
              f"  shutil.rmtree(p, ignore_errors=True); print('gone:', not os.path.exists(p))\n" for w in works))
