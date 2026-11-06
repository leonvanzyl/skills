# Proving it works

Last verified: 2026-08-11

**Purpose:** Turn the end of the build from a list the agent agrees with into commands that either pass or don't, and then look at the result with eyes that didn't build it. Everything before this file is construction. This is the only file that asks whether any of it is true.

> **Hard rule: the gate is passed by fixing the code, never by widening the gate.** No `ignoreBuildErrors`, no `ignoreDuringBuilds`, no `@ts-expect-error` or `eslint-disable` added to quiet a check, and no deleting something the build sheet promised so a check stops asking about it. A gate that can be moved is a gate that will be, at the exact moment it was about to be useful.

Commands here are written for a POSIX shell. On Windows use the Bash tool rather than translating them — `curl`'s cookie jar has no clean PowerShell equivalent, and a translated probe that silently does nothing is worse than one that wasn't run.

## Before you run anything

- **Note the current commit.** `git rev-parse HEAD`. The fix rounds are checked against it, so the gate needs a fixed point to diff from.
- **Check port 3000.** If something is already listening, it is almost certainly the user's own dev server. **Do not kill it.** Ask them to stop it, or run the read-only probes against it and name the production-mode checks as unperformed.
- **Postgres branch: check Docker is up** — `pnpm db:up` then `docker compose ps`. If the daemon isn't running, stop here and say so plainly. Every command below fails identically whether the app is broken or Docker is off, and a fix loop that can't tell those apart will rewrite working code.

## The gate

Run these in order — cheap and diagnostic before expensive and opaque. Read the output of every one. Having written the code that a command tests is not a reason to skip the command; it is the reason the command exists.

### 1 — Types

```bash
pnpm exec tsc --noEmit
```

Seconds, where a build is minutes, so it goes first. `next build` type-checks the same `tsconfig.json` and is the authority, but it obeys `typescript.ignoreBuildErrors` — so check the escape hatches are absent while you're here:

```bash
grep -n "ignoreBuildErrors\|ignoreDuringBuilds" next.config.* || echo "clean"
```

A match is itself the finding: remove it and re-run, rather than reporting around it.

**One known false failure.** If the app uses Next's generated route-type helpers, those types don't exist until a build has written `.next/types`. If the only errors name them, run step 3 once and come back. Never "fix" this by loosening `tsconfig.json`.

### 2 — Schema and migrations

This is the check the skill has never had, and it runs *before* the build for a reason. `pnpm build` is `pnpm db:migrate && next build` — safe when nothing is pending, which is exactly what this step establishes. Reach the build with an ungenerated schema edit outstanding and the gate becomes the thing that drops a column.

```bash
pnpm db:generate
git status --porcelain drizzle
```

Two outcomes, meaning very different things:

- **Nothing new** — the schema file and the migration history agree. This is the pass.
- **A new `.sql` file** — the schema was edited and never generated. **Read it**, as `references/database.md` requires. A `DROP COLUMN`, or a drop-plus-add where a rename was meant, stops the gate and goes to the user. Anything else applies.

```bash
pnpm db:migrate
grep -n '"db:push"\|drizzle-kit push' package.json || echo "clean"
```

No `push` in any script, and `drizzle/` is committed rather than untracked — it is source code.

### 3 — The build, and what its route table tells you

```bash
pnpm build
```

Then read the route table it prints, which is free evidence nothing currently uses: **any route that renders one person's data must be `ƒ` (Dynamic), not `○` (Static).** A `○` on a page showing a user's rows means it was prerendered at build time, so every visitor gets the build machine's copy of somebody's data. That is a real leak the old Verify list could not see, and it costs nothing to look.

**Consent branch: expect everything to be `ƒ`.** A consent banner reads a cookie in the root layout, which makes every route dynamic — so this check finds nothing on those apps. `ƒ` is the safe state, so that is a quiet check rather than a broken one; don't read it as a pass for something it never examined.

### 4 — Lint

```bash
npm pkg get scripts.lint
```

**Do not assume `pnpm lint` exists.** The base project is scaffolded with an ESLint config, but whether a `lint` script is written — and what it runs — moves between Next versions. Run whatever script is actually there; if there is none, run the project's ESLint directly; if there is neither, say so rather than inventing one.

Errors block, warnings don't — that is already ESLint's exit-code behaviour, so take it and don't add `--max-warnings 0`. A fix loop grinding on unused imports is the failure mode here.

Then one grep, because the design system is only real if the components obey it:

```bash
grep -rEn '#[0-9a-fA-F]{3,8}|rgb\(|oklch\(' src --include='*.tsx'
```

Every hit is a colour that escaped the theme — it will look wrong in the other mode and it will not follow if `DESIGN.md` changes. Move it to a token. The one sanctioned exception in the whole app is the unfilled-field marker `references/legal.md` builds, which is hardcoded on purpose so it cannot blend in.

### 5 — Serve it in production mode

```bash
pnpm start
```

Production on purpose: it is the mode `references/ops.md` already asks about, and it exposes the prerender problems `pnpm dev` hides. Start it in the background so the probes below can run against it.

**Jobs branch: this does not exercise jobs.** The Inngest dev server is wired into `dev`, not `start`, so background work is not running here. Name that as unperformed rather than letting the passing routes imply it.

### 6 — Every route answers

List the app's real pages — every `page.tsx` under `src/app`, with route groups stripped and dynamic segments left out — and ask each one for a status:

```bash
for r in / /sign-in /dashboard /settings /settings/system; do
  printf '%-28s %s\n' "$r" \
    "$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' "http://localhost:3000$r")"
done
```

**No 500s.** `200`, or `307` to `/sign-in` for anything inside the dashboard group. Keep this output — it is the app's actual surface area, which is the one thing nobody could see before, and the promise-keeping critic is given it verbatim.

**Do not blind-probe `route.ts` handlers.** A POST with side effects is not a check. The `.well-known` discovery documents from `references/mcp.md` are the exception and are safe to GET.

**Legal branch: the pages answer signed out, and no blank shipped.** Whatever `references/legal.md` decided this app owes has to be reachable by a stranger — `200` from a cold client with no cookie, not a redirect to sign-in — and the ones it decided against must be absent rather than present and empty. Then read what the page actually served, because an unfilled detail renders as a marker that is easy to stop seeing:

```bash
for r in /privacy /terms /cookies; do
  printf '%-12s %s\n' "$r" "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:3000$r")"
done
curl -s http://localhost:3000/privacy http://localhost:3000/terms \
  | grep -o "Needs your details[^<]*" | sort -u
```

**`404` is the pass for a page this app was never going to have.** A `200` on `/terms` for a one-person tool is the finding, not the reassurance — something got built on spec.

Every line the grep prints is a field in `src/lib/legal.ts` nobody set. **That is not a gate failure** — only the user can supply a contact address or a governing jurisdiction. It is the hand-off list, and it is a failure only if it goes unnamed. What *is* a gate failure is a plausible placeholder that the grep can't see: check for one, because `[Your Company Name]` in a live privacy policy is what this marker exists to prevent.

```bash
grep -rniE '\[your |lorem ipsum|company name\]|example\.com' src/app/\(legal\) src/lib/legal.ts || echo "clean"
```

**Every app: the title in the tab.** One line, and it catches the single most template-smelling artefact a build can ship:

```bash
curl -s http://localhost:3000/ | grep -o '<title>[^<]*'
```

`Create Next App` is a failure, not a note.

**Discoverability, whichever branch ran.** `references/seo.md` builds one of two opposite things, so check the one this app was meant to get:

```bash
for r in /robots.txt /sitemap.xml /llms.txt; do
  printf '%-14s %s\n' "$r" "$(curl -s -o /dev/null -w '%{http_code}' "http://localhost:3000$r")"
done
curl -s http://localhost:3000/robots.txt
curl -s http://localhost:3000/sitemap.xml | grep -oE '<loc>[^<]+' | sed 's/<loc>//'
```

- **Kept-out-of-search branch:** `robots.txt` says `Disallow: /`, and `/sitemap.xml` and `/llms.txt` are `404`. A `200` on either means something got built on spec, the same finding as an orphan `/terms`.
- **Public branch:** all three answer `200`, and **no line of that sitemap contains `/dashboard`, `/settings` or `/api`.** Those are pages a stranger is being invited to open; every one that redirects to sign-in is an error the user has to learn to ignore. Compare the list both ways against the route sweep above — a public page missing from the sitemap is the more common miss, and the sweep is the only place it shows.
- Every `<loc>` is absolute and shares one origin. A mix of `http` and `https`, or a bare path, is a finding.
- Neither `public/robots.txt` nor `public/sitemap.xml` exists — a static file silently shadows the generated one, and the generated one is the one with the right absolute URL in it.

**Docs branch: the pages answer signed out, and nothing leaked into them.** They are public forever and indexed by the step above.

```bash
grep -rniE 'sk-|pk_|api[_-]?key|postgres://|localhost:[0-9]|\.vercel\.app' src/app/\(docs\) || echo "clean"
```

Then confirm the manifest and the files agree: every entry in `src/lib/docs.ts` has a `page.mdx`, and every `page.mdx` has an entry. One without the other is a dead sidebar link or a page nobody can reach.

### 7 — Two accounts

Skip this and the next step entirely if the app has no sign-in.

**Ask the user to create their own account first**, before any probe account exists:

> Open http://localhost:3000 and sign up — the first account becomes the admin. Tell me when it's done and I'll finish the checks.

This is not politeness. `references/settings.md` makes the first account created the admin, so a fixture signed into an empty database becomes the admin — and deleting it afterwards can leave the user locked out of their own system page. Asking costs thirty seconds, makes both fixtures ordinary users (which is what the isolation probe needs), and puts the human in the loop at the one moment it genuinely helps.

Then work over Better Auth's own REST surface, which is scriptable in a way server actions are not:

```bash
JAR=$(mktemp -d)

for u in a b; do
  curl -s -c "$JAR/$u.jar" -X POST http://localhost:3000/api/auth/sign-up/email \
    -H 'content-type: application/json' \
    -d "{\"name\":\"Check $u\",\"email\":\"check-$u@example.test\",\"password\":\"check-passphrase-$u\"}"
done

curl -s -b "$JAR/a.jar" http://localhost:3000/api/auth/get-session
curl -s -o /dev/null -w '%{http_code}\n' http://localhost:3000/dashboard
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/a.jar" http://localhost:3000/dashboard
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/b.jar" http://localhost:3000/settings/system
curl -s -b "$JAR/a.jar" -X POST http://localhost:3000/api/auth/sign-out
curl -s -b "$JAR/a.jar" http://localhost:3000/api/auth/get-session
```

Signed out, `/dashboard` is a `307`; with A's jar it is `200`; after sign-out the session is empty again. That turns three prose assertions into status codes.

**On `/settings/system` as a non-admin: anything other than `200` is the pass, but a `500` is worth noting.** `requireAdmin()` throws, and an uncaught throw in a server component is a stack trace rather than a refusal. That is a gap in `references/settings.md`, not a bug for the fix loop to chase.

### 8 — One account's data, seen from the other

The read path is where leaks live, and it is mechanically checkable. Seed one row owned by A directly at the database layer, then ask for it as B over HTTP:

```bash
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/a.jar" "http://localhost:3000/<route>/<rowId>"   # 200
curl -s -o /dev/null -w '%{http_code}\n' -b "$JAR/b.jar" "http://localhost:3000/<route>/<rowId>"   # 404, never 200
```

**The write path stays out of the gate.** Server actions need a `Next-Action` id and an RSC-encoded body; scripting that is brittle enough to produce false failures, which cost more than the check is worth. Creating a record through the UI stays a browser check or a named unperformed one.

Then remove the fixtures and prove they're gone — the remaining account should be the user's own, still `admin`. A stray `check-a@example.test` sitting in someone's brand-new app is exactly what makes a scaffold feel like a scaffold.

### 9 — With the keys taken away

**Never blank environment variables in the shell.** Emptying a variable and letting `.env` repopulate it is the check passing while testing nothing, and on Windows assigning an empty string deletes the variable outright. Use Next's own file precedence instead: `.env.production.local` loads before `.env`, and nothing overwrites a key that is already set, so an empty value there is what every `Boolean(process.env.X)` guard in the app actually reads.

- **Only create the file if it doesn't already exist.** If it does, skip this check and say so.
- **Never write to `.env`.**
- Write each integration key the app uses, present and empty. Restart in production mode, re-run the route sweep, stop.
- **Delete it, then assert it is gone before anything else happens.** A leftover blanking file disables the user's integrations in every future production build — worse than skipping the check entirely.

Every route still answers, nothing 500s, and each affected surface says what to set. Pair it with the static half, which is free and catches the bug class that matters — a module that throws at import time:

```bash
grep -rn "process\.env\.[A-Z_]*!" src/ || echo "clean"
grep -rn "NEXT_PUBLIC_" src/ || echo "clean"
```

The first finds non-null assertions on keys that may be absent. The second finds anything shipped to the browser — that prefix makes a value public, so a secret behind one is already leaked.

### 10 — Stop what you started

Stop the server the gate started, and only that one. `pnpm` spawns `next`, which spawns `node`, so killing the `pnpm` process orphans the server still holding port 3000 — go by what owns the port. Confirm nothing is listening before moving on.

## What a command can't prove

The gate stops at what a status code can answer. The rest needs a browser, a provider round trip, or a human, and it is where most of the app's actual behaviour lives. If a browser tool is available, use it: load `/` and the main page, capture light and dark, capture one narrow viewport, and read the console on each.

If the project already uses agent-qa, or the user selected it for these checks, read [browser-flow evidence with agent-qa](agent-qa.md). Use it for the selected flows from the agreed build sheet. Its results join the evidence capture; they do not replace the gate, the remaining browser checks, or the fresh-eyes review. Do not add a test framework merely because this reference exists.

Then **name every check still not performed.** Do not omit them and do not claim them:

- The app in dark mode, and at a phone-width viewport.
- Creating a record through the app's own UI rather than the database, and editing and deleting one.
- Uploads: putting a file through the UI and seeing it render after a refresh.
- Email: a test send reaching `delivered@resend.dev` with a key set, and — with sign-in — signing up sending a confirmation and "forgot password" actually resetting a password.
- Payments: the test-mode checkout completing and the paid state showing server-side.
- AI: the feature working against a real key, and being the feature the interview asked for rather than a bare chat box.
- Jobs: a run and its steps at http://localhost:8288, a deliberate failure retrying visibly, and the job's row ending in the right state — all of which need `pnpm dev` rather than `pnpm start`.
- Agent access: adding the server in Claude Code, going through the app's own sign-in and consent screen, and revoking the connection in settings stopping the next call.
- Cookie consent, where a banner was built: that no third-party script is in the served HTML before a choice is made, that Reject is one click at the same visual weight as Accept, that no non-essential category starts ticked, and that the choice survives a reload and can be withdrawn from settings afterwards.
- Discoverability, public branch: that the Open Graph image renders as an image rather than an error, and what a shared link actually looks like in a chat app. `/opengraph-image` returning `200` proves the route works, not that the picture is right — and this is the check a browser tool can close cheaply, so run it if one is available.
- Discoverability: whether the sitemap and canonical URLs are correct for the **real** domain. Everything the gate reads locally says `localhost`, which is expected here and wrong in production — it is proven by `APP_URL` on the host, not by anything runnable now.

These become a short "when you open it, check these" list at hand-off. **A check that was skipped and not named is a false pass**, and it is worse than never having listed it — the user reads silence as success.

## Fresh eyes

The gate proves the app builds, serves and answers. It is structurally blind to whether the app *does anything*: an entirely empty project passes every command above, because nothing leaks when there is nothing to leak. That gap is what this phase is for.

**Dispatch the critics in a single message so they run at once.** Four when there is sign-in, three without.

| Lens | Runs when | Covers |
| --- | --- | --- |
| Promise-keeping | always | the build sheet in both directions, dead controls |
| Ownership | sign-in exists | isolation, the admin boundary, rendered secrets |
| Looks like theirs | always | anti-template, empty states, the front door |
| Operability | always, scaled to branches | activity log, system panels, degradation |

Three rules make this work, and each of them is load-bearing:

- **Critics get evidence, not access.** They cannot share port 3000 or a browser between them, and a critic that can run things will spend an hour running things. Capture everything once during the gate and hand it over as text and images. Critics read files; they do not start servers, install anything, or write.
- **Critics do not get the reference files.** Handing them over turns a critic back into a runner of the same checklist that just failed to catch anything. Where a critic needs a rule, it is quoted inside its brief.
- **Promise-keeping is two-sided in one head.** Split "did you build it" from "did you build too much" across two agents and the gap-hunter always wins, because finding things is what agents are rewarded for — and the *not in version one* list ends up with nobody enforcing it.

### What every critic is told

> You are reviewing an app you did not build, for someone who cannot read code. You have the build sheet they approved, the app's files, and the transcript of the checks run against it. You do not have the reasoning behind any decision and should not ask for it — if a choice only makes sense once someone explains it, that is itself worth reporting.
>
> **The build sheet is the only bar.** Not what a mature product would have, not your own preferences, not production readiness. A first version is meant to be small.
>
> **Every finding names the promise it breaks** — a line of the sheet, a string the app puts on screen, or a rule quoted in your brief. If you cannot name one, you have an opinion rather than a finding. Drop it.
>
> **The user chose these things.** A decision you would have made differently is not a finding, and neither is anything on the sheet's *not in version one* list.
>
> **Never in scope:** tests, CI, error boundaries, performance, rate limiting, monitoring, refactors, folder structure, naming, comments, accessibility or search visibility beyond what the sheet says, or any sentence beginning "consider adding". A sheet line about being found — or about deliberately not being — is in scope like any other promise; *how well it would rank* is not.
>
> You are read-only. Do not run the app, start a server, or install anything. If you find yourself wanting to fix something, that is a finding, not a task.
>
> **At most five findings, most serious first.** If you have more than five, the extra ones weren't important. If the app keeps the sheet, say so in one line and stop — finding nothing is a result, not a failure.
>
> Each finding, exactly:
> **What** — one sentence: what the app does or doesn't do.
> **Where** — `path:line`, or the route and what it answered.
> **Which promise** — the sheet line, the on-screen string, or the rule.
> **How sure** — `saw it` if you read the code or response that proves it, `suspect` if it reads that way but you couldn't confirm.
> **Severity** — `broken` (the sheet says it works and it doesn't, or it leaks), `missing` (promised, not there), or `worth knowing` (true, small, not worth a round trip).

### Promise-keeping

> You are checking one thing: does the app do what the sheet says, and nothing the sheet ruled out?
>
> The sheet the user approved: `<paste the Step 3 build sheet verbatim, including the "Not in version one" line>`
> The app: `<project root>`. The routes that exist and what each answered: `<paste the route sweep output>`. The tables and columns: `<paste the schema file>`.
>
> Work the sheet line by line. For each noun under *what it remembers*, find the table. For each verb under *what you can do*, find the code that performs it and say where. A promise with no file behind it is `missing`.
>
> **A promise with a page but nothing behind it is `broken`, and it is the more dangerous kind** — a button that renders and calls nothing, a form that posts to a stub, a list of rows nothing ever writes. Follow one verb the whole way from the control to the database and say what you found.
>
> Then go the other way, with equal weight. List anything the app has that the sheet never asked for. **Everything on the *not in version one* list that exists anyway is a finding of the same severity as a missing promise** — the user said no to those, and building them anyway isn't generosity, it's scope they now have to maintain.
>
> Do not evaluate quality, structure, or approach. "This works, but I'd have done it differently" is not a finding.

### Ownership

Only when there is sign-in.

> You are checking who can reach whose data.
>
> The app: `<project root>`. The sheet says the data is `<private to each user / shared with a team / public>`. The probe transcript: `<paste the two-account and isolation output>`.
>
> Find every place the database is read or written — `src/lib/db`, then every `page.tsx`, every server action, every route handler, and every agent tool if the app has them. For each, answer one question: **whose rows can this return?**
>
> - A read filtered only by an id from the URL returns any row whose id someone can guess or was once shown.
> - A write that takes an id and doesn't re-check the owner lets one account edit another's.
> - **The session is the only acceptable source of the current user.** A user id taken from a form field, a query parameter, a request body, a header, or a tool argument is a finding even if the code looks correct today.
>
> Then the boundary. Everything admin-only is refused on the server, in the page and in every action behind it. Hiding a link is presentation — if the only thing stopping a normal account is an unrendered link, that is `broken`.
>
> Then secrets. Nothing renders an API key, token, or connection string, or any part of one — including masked tails, `title` and `data-` attributes, and anything passed as a prop into a client component. Any `NEXT_PUBLIC_` variable ships its value to the browser, so a secret behind one is already public.
>
> Report by what is exposed, not by how the code reads. A query that looks careless but cannot return another person's row is not a finding.

### Looks like theirs

> You are the first stranger to open this app. Read every string a person will see.
>
> The sheet: `<paste>`. The nouns and verbs it uses: `<list>`. The pages: `<paste the route list>`. The design system the app was built to: `<paste DESIGN.md>`. `<If screenshots were captured: light and dark, desktop and narrow, attached.>`
>
> Start at the front door and answer in one sentence what this app is for. **If you can't, that is the finding and everything else is detail.**
>
> The tells, worst first:
>
> - The browser tab. Read the `<title>` the app actually serves: a framework default there is the first thing anyone sees and the last thing anyone checks.
> - A framework word where the app has its own — "Item", "Entry", "Record", or a page titled "Dashboard" in an app whose sheet calls it something else.
> - A heading describing the software rather than what the person does.
> - An empty state that reads as breakage rather than a beginning, or a list with no empty state at all.
> - A settings section for something this app doesn't have — a Billing tab with no payments, Notifications in an app that sends no email.
> - An email signed with anything other than the app's own name.
> - A landing page section that would need customers to be true: testimonials, logos, ratings, user counts, press. The app has no users and everyone reading knows it.
> - A legal page with a blank nobody filled in, a clause about something the app doesn't do, or a footer link to a page that isn't there. Read any privacy or terms page the same way you read the rest: if it describes a different product, say so.
> - A documentation page describing a control that isn't in the app, a page for a feature the sheet ruled out, or a "coming soon". Follow one page's instructions through the code and say whether every button it names exists. Docs that describe a different product are the same finding as a privacy policy that does, and they cost the user a support email.
>
> If the app calls a noun or verb something different on screen than the sheet does, say where and what it calls it — that is usually a real disagreement rather than a synonym.
>
> - A page that contradicts `DESIGN.md`: a colour, font size or radius written into a component instead of taken from a token, a font that isn't one of the two the file names, a list with no empty state where the file requires one. Quote the line of `DESIGN.md` it breaks.
>
> **You are not a designer.** `DESIGN.md` is the only design standard here, and it was agreed with the user. Whether it is a *good* design is not your question — do not report colour choices, spacing or component selection that the file permits, and do not propose a different direction. `<From the screenshots, report only what is illegible, overlapping, or cut off — not taste.>`

### Operability

> The app does things the user cannot watch. You are checking that it doesn't.
>
> The rule this app was built to: *anything the app does out of sight is visible and controllable from inside it — the user can see it happened, read why it failed, stop it, and try again, in the app rather than on a hosting dashboard.*
>
> This app has: `<email / background jobs / agent access / uploads / payments / none of these>`. **Judge only those** — a panel for something the app doesn't do is a finding in the other direction.
>
> - **The activity log exists in every app.** Does the app's main action write a row, in the app's own words — `hike.created` rather than a route or table name? Find any write path that logs nothing.
> - For each branch above, does its panel read the app's **own** table rather than calling the provider to render a list, and does a failed row show a reason a person could act on?
> - **Degradation:** for each integration, find the one module that reads the key. It must not be able to throw when the key is absent — no non-null assertion at module scope, no client constructed unconditionally — and the surface must name what to set. The run with every key blanked: `<paste>`.
> - Nothing on the system page prints a key or part of one. Check the page source, not just the transcript.
>
> Not in scope: alerting, retention, metrics, or a dashboard for anything the app doesn't do.

## What comes back

- **Only `broken` and `missing` enter the fix loop.** `worth knowing` goes into the hand-off verbatim and is never fixed now. This is the valve that stops a thorough critic setting the agenda.
- **A `suspect` finding is re-checked with a command before it is fixed.** If the command disagrees, drop it, with one line in the hand-off saying so.
- **Fixes touch only the files the finding names.** No refactors, no tidying, no "while I'm in here".
- **No fix widens the gate.** Never `ignoreBuildErrors`, never `ignoreDuringBuilds`, never a new `@ts-expect-error` or `eslint-disable`, and never deleting something the sheet promised to make a check stop asking. `git diff` against the commit noted at the start confirms no suppression was added.
- **No fix is a spec change.** Anything that would add a feature, reverse a decision the user made, or reach into the *not in version one* list is one line at hand-off, not a fix. Step 3 stays the only place scope is set.
- **Schema fixes are the sharpest edge.** `db:generate`, read the generated SQL, `db:migrate`, and say out loud that you did. Never `push`. Never edit a migration that has already been applied — a mistake becomes a new migration, because editing applied SQL leaves the journal describing a file that no longer exists. Never edit `auth-schema.ts`; a finding about auth columns means re-running the Better Auth CLI.
- **Re-run the gate after every round**, not just at the end. A fix that breaks the build is worse than the finding it closed.
- **Round two re-dispatches only the critics that filed a blocking finding**, and asks them only to re-check those findings. Otherwise a critic finds fresh material every pass, indefinitely.
- **Two rounds, then stop and report.** Round three is where an agent starts changing code it doesn't understand to make a report go away.

### When a critic is wrong

> **On what the app does the critic wins; on why it is that way the builder wins.** A critic quoting a file or a response is reporting evidence — take it, even where you remember writing it differently, because what you remember writing is not what is on disk. A critic explaining what the user must have meant is guessing at a conversation it wasn't in: the build sheet decides, and where the sheet is silent, the user does, at hand-off. **Where a finding can be settled by a command, run the command — it outranks both of you.**

A finding you disagree with is downgraded, never deleted: it goes into the hand-off in one line with why you think it's wrong. Marking your own homework is the failure this whole step exists to fix.

Two critics contradicting each other: the one with a `path:line` wins. If both have one, it's a genuine ambiguity and goes to the user. A critic reporting outside its own lens is out of scope — that needs to be a rule rather than a judgement call, or the phase sprawls.

## Verify

- Every command in the gate was run and its output read — not one was assumed from having written the code it tests.
- Every check that could not be performed is named in the hand-off, with what would be needed to perform it.
- `.env` is byte-for-byte what it was before the gate ran, and no `.env.production.local` is left behind.
- No probe account, cookie jar, or seeded row survives the gate. The user's own account is still the admin.
- No suppression, ignore flag, or deleted promise appears in `git diff` across the fix rounds.
- Findings that were disagreed with appear in the hand-off with the reason, rather than silently.
