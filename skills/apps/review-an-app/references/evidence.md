# Gathering evidence

Last verified: 2026-08-13

**Purpose:** Capture everything the three lenses need, once, before any of them start. They run at the same time and cannot share a port, a database or a browser between them — so whatever isn't captured here is a thing three agents will each try to find out for themselves, badly.

> **Hard rule: no secret enters the pack.** Variable *names* from `.env`, never values. Never paste `.env` itself, a `git diff` that touches it, or a block of served HTML without reading it first. This pack goes to subagents and gets quoted in a report; a review that leaks the key it was checking on has done more damage than the bug it found.

Commands are written for a POSIX shell. **On Windows use the Bash tool** rather than translating — a mistranslated probe that silently does nothing is worse than one that was never run.

## Before anything

**This is somebody's working app, not a scaffold.** Leave it exactly as found.

- **Note the commit.** `git rev-parse HEAD`, and `git status --porcelain` to record what was already dirty. If a fix round follows in Step 6, this is the fixed point it diffs from.
- **Never modify a file to make a check work.** No `.env` edits, no config changes, no installs, no migrations. If a check needs something the app doesn't have, that check is unperformed and gets named.
- **Check port 3000 before serving anything.** If something is already listening it is almost certainly the user's own dev server. **Do not kill it.** Probe against it and note that the app was reviewed in whatever mode they were running.

## The route inventory — always

The spine of the whole review. Two lenses diff against it and neither can build it themselves.

```bash
find src/app -name 'page.tsx' -o -name 'page.mdx' -o -name 'route.ts' | sort
```

Turn that into real paths: strip `src/app`, drop the filename, remove route groups (`(dashboard)`, `(legal)`), and keep dynamic segments marked rather than guessed. Then sort each one into a bucket, because every lens needs to know which:

| Bucket | How you can tell |
| --- | --- |
| **Public** | no session check in the page, its layout, or any layout above it |
| **Behind sign-in** | a `getSession` / `requireUser` in the page or an ancestor layout, or it sits in a protected route group |
| **Admin only** | `requireAdmin`, or a role comparison |
| **Handler, not a page** | `route.ts` — never blind-probed, see below |

**Getting this wrong poisons two lenses at once.** A public page filed as protected reads as a missing sitemap entry; a protected page filed as public reads as a leak. Where a route's status is genuinely unclear from reading, mark it unknown and say so rather than picking.

## Does it run?

Try, once. What the rest of this file can capture depends entirely on the answer.

```bash
pnpm build 2>&1 | tail -40
```

A failing build is itself the first finding, and it stops the probe half of the review — say so plainly rather than reporting around it. Where it succeeds, read the route table it prints: **a route rendering one person's data must be `ƒ` (Dynamic), not `○` (Static).** A `○` there means it was prerendered at build time and every visitor gets the build machine's copy of somebody's data. Capture the table either way; the security lens reads it.

An app with a consent banner reads a cookie in the root layout, which makes everything `ƒ`. That is the safe state, so on those apps this check finds nothing — record that it was quiet rather than that it passed.

Then serve it:

```bash
pnpm start
```

**If it won't build or won't start, the review continues read-only.** That is a legitimate mode and roughly half the value; what it costs is every probe below, and the report has to say so.

## The probe sweep

Ask every real page for a status. Route groups stripped, dynamic segments left out, handlers excluded.

```bash
for r in / /sign-in /dashboard /settings /pricing /docs /privacy; do
  printf '%-28s %s\n' "$r" \
    "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "http://localhost:3000$r")"
done
```

Keep this output verbatim — it is the app's actual surface area and all three lenses are given it. `200` for public, `307` to sign-in for protected. **A `500` is a finding on its own**, whatever else the review turns up.

**Do not blind-probe `route.ts` handlers.** A POST with side effects is not a check; it is a write to somebody's database. The exceptions, safe to GET, are `/.well-known/*`, `/robots.txt`, `/sitemap.xml` and `/llms.txt`.

## The discoverability capture

```bash
for r in /robots.txt /sitemap.xml /llms.txt /opengraph-image; do
  printf '%-18s %s\n' "$r" "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:3000$r")"
done

curl -s http://localhost:3000/robots.txt
curl -s http://localhost:3000/llms.txt
curl -s http://localhost:3000/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's/<loc>//' | sort
```

And the head of every public page, which is where the metadata lens actually lives:

```bash
for r in / /pricing /docs; do
  echo "--- $r"
  curl -s "http://localhost:3000$r" \
    | grep -oE '<title>[^<]*|<meta name="description"[^>]*|<link rel="canonical"[^>]*|<meta property="og:[^>]*'
done
```

Where the app didn't start, take these statically instead — `src/app/sitemap.ts`, `src/app/robots.ts`, `src/app/layout.tsx` — and mark every finding from them `suspect`, because a file that generates a sitemap is not a sitemap.

## The two-account probe

Only where there is sign-in, and **only with the user's agreement** — this creates rows in a real database.

Ask first, in one line: *"I'd like to create two throwaway accounts to check that one can't see the other's data. They get deleted afterwards. Is that OK on this database?"* If the answer is no, or the app is pointed at production, skip it and name it as unperformed. **Never run this against a production database.** Check what `POSTGRES_URL` points at before asking — the name only, never the value.

```bash
JAR=$(mktemp -d)

for u in a b; do
  curl -s -c "$JAR/$u.jar" -X POST http://localhost:3000/api/auth/sign-up/email \
    -H 'content-type: application/json' \
    -d "{\"name\":\"Review $u\",\"email\":\"review-$u@example.test\",\"password\":\"review-passphrase-$u\"}"
done

curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/dashboard
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/a.jar" http://localhost:3000/dashboard
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/b.jar" http://localhost:3000/settings/system
```

Then, where a row belonging to A can be identified, ask for it as B — `200` there is the finding the whole probe exists for.

**Remove both accounts afterwards and confirm they're gone.** A review that leaves `review-a@example.test` in somebody's user table has made a mess to prove a point.

## Static captures

Cheap, always available, and they don't need the app to run:

```bash
git log -1 --format='%H %ad %s'
cat package.json
ls src/lib/db/*.ts src/lib/*.ts 2>/dev/null
grep -rlE '"use server"' src/ | sort
grep -rn 'NEXT_PUBLIC_' src/ | sort
grep -oE '[A-Z][A-Z0-9_]{3,}' .env 2>/dev/null | sort -u    # NAMES only — never the file
```

The `"use server"` list matters more than it looks: **every exported function in those files is a public POST endpoint**, and the security lens is going to want the list rather than to go find it.

Dependency advisories are worth one command, since it is the only check here that reaches a database this skill cannot carry:

```bash
pnpm audit --prod 2>&1 | tail -30
```

Read it rather than pasting it. A transitive advisory with no path from this app's code is `worth knowing`, not `broken`, and the lens needs to be told which.

The rest of the supply chain is two more cheap reads — which lockfile is committed, which packages may run install scripts, and what the CI workflows pull in:

```bash
git ls-files | grep -E '(^|/)(pnpm-lock\.yaml|package-lock\.json|yarn\.lock|bun\.lockb?)$'
grep -n -A10 'onlyBuiltDependencies' package.json pnpm-workspace.yaml 2>/dev/null
grep -rn 'uses:' .github/workflows/ 2>/dev/null
```

## Stop what you started

Stop only the server this file started, and go by what owns the port — `pnpm` spawns `next`, which spawns `node`, so killing the `pnpm` process orphans the server still holding 3000. Confirm nothing is listening before the lenses are dispatched.

## What the pack contains

Hand every lens the same thing:

1. The route inventory, bucketed.
2. The probe sweep output, verbatim.
3. The build route table, or the build failure.
4. Which branches the app has, from Step 1.
5. `package.json`, the schema files, and the `"use server"` file list.
6. The audit summary, the committed lockfile, the install-script allowlist and the workflow `uses:` lines.
7. The discoverability capture, or the static files where the app didn't run.
8. **Which mode this review ran in** — served and probed, or read only. Every lens has to know how much its own evidence is worth.

And tell each lens plainly what is *not* in the pack, so it reports the gap instead of assuming it away.
