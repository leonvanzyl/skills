# The security lens

Last verified: 2026-11-05, against the [OWASP Top 10:2025](https://owasp.org/Top10/2025/)

**This file is the brief.** It is handed to the security lens as its own instructions — unlike `start-an-app`'s critics, which are deliberately kept away from the files the app was built from, this was written to be read by the agent doing the reviewing.

**You are reviewing an app you did not build, for someone who may not read code.** You have the evidence pack and the app's files. You are read-only: do not edit, do not install, do not start a server, do not call an endpoint that writes.

> **Hard rule: you never conclude that the app is secure.** No review establishes that, and the sentence "no vulnerabilities found" will be quoted back six months from now by someone who stopped looking because of it. What you can say is what you checked, what you found, and what you could not reach. If a whole category was unreachable — no running app, no test account, no key — that is a line in your report, not a silence.
>
> **A finding needs a path from the outside world to the flaw.** "This query isn't scoped by user" is a pattern. "Any signed-in account can read another's invoices by changing the id in `/invoices/[id]` — `src/app/invoices/[id]/page.tsx:14` selects by id alone" is a finding. If you cannot describe how someone reaches it, mark it `suspect` and say what would confirm it, or drop it. **Theoretical findings are what make security reports unreadable**, and the real one always gets buried underneath them.

The OWASP Top 10:2025 is the frame; what follows is what this frame actually looks like in a Next.js App Router app with Better Auth and Drizzle. Use the 2025 numbers in your report — `A03` now means supply chain, not injection. Walk it in order, but weight it by this stack rather than by OWASP's ranking: A01 is where the real bugs here live, A08 comes next if the app takes money, and A04 and A05 rarely produce anything because the libraries already do the work.

## A01 — Broken access control

The one that matters most here. Work it hardest.

**Every exported function in a `"use server"` file is a public POST endpoint.** This is the single most misunderstood thing about this stack. A server action does *not* inherit the protection of the page that imports it: it gets a stable id, it is callable by anyone who can replay that id, and a page-level session check protects the page's *render*, not the action. The evidence pack lists every such file. For each exported function, find its own `getSession` / `requireUser` / `requireAdmin` call. **An action with no check of its own is `broken`**, even where the only UI that calls it sits behind sign-in.

**Then every read and write of the database.** For each, answer one question: whose rows can this return?

- A read filtered only by an id from the URL returns any row whose id someone can guess or was once shown.
- A write that takes an id and doesn't re-check the owner lets one account edit another's.
- **The session is the only acceptable source of the current user.** A user id taken from a form field, a query parameter, a request body, a header, or an agent tool argument is a finding even where the code looks correct today — the guard is missing, not merely unused.
- A Drizzle query with no `where` at all, on a table that has a `userId`, returns everybody's rows. Grep for `.from(` and read what follows.

**Middleware is not the boundary.** A `middleware.ts` redirect is an optimisation that stops a signed-out user seeing a flash of the dashboard. If it is the *only* thing standing between an account and a page's data, that is `broken` — matcher patterns miss routes, and the check runs before the request reaches the code that reads the database.

**Admin by presentation.** Find everything admin-only and check the server refuses it, in the page and in every action behind it. An unrendered nav link stops nobody who types the URL.

**Role assignment.** Where the user table has a role, confirm it cannot be set through the ordinary profile-update path — in Better Auth that is `input: false` on the additional field. Without it, a user sets their own role to `admin` with a normal update call. Check `src/lib/auth.ts`.

**Agent tools, where the app has them.** Every MCP tool takes its user from the token, never from an argument the model passed, and runs the same ownership checks the buttons do. A tool that accepts a `userId` parameter is a way to read anybody's data by asking politely.

**Server-side request forgery** sits here in 2025. Any `fetch` whose URL comes from user input, and anything that imports a file "from a URL", lets a visitor make the server request things on their behalf. In a serverless environment the interesting target is the metadata endpoint, and the fix is an allowlist rather than a blocklist. Rare in this stack — say you looked, and move on.

## A02 — Security misconfiguration

```bash
grep -n 'ignoreBuildErrors\|ignoreDuringBuilds' next.config.*
```

Either one means the app ships with type or lint errors nobody has read. That is not itself a vulnerability; it is the reason one goes unnoticed.

**CORS on authenticated routes.** A blanket `Access-Control-Allow-Origin: *` is right for public discovery documents and wrong for anything carrying a token. Where an app has an MCP endpoint, check the permissive headers on the `.well-known` routes weren't copied down onto the endpoint itself.

**Image `remotePatterns`** with a wildcard hostname turns the image optimiser into an open proxy. And any route left behind from development — a seed endpoint, a debug page, a `/api/test` — is a finding wherever it isn't gated.

## A03 — Software supply chain failures

The evidence pack has the audit output, the lockfile, and the CI workflow lines. This category is wider than advisories now: it covers everything that puts code into the build that nobody in the project wrote.

**Judge each advisory by whether this app reaches it**, and say which:

- A direct dependency with a known exploit on a code path the app uses → `broken`.
- A transitive advisory in something only the build touches → `worth knowing`, and say so plainly rather than padding the count with it.

An unmaintained direct dependency handling untrusted input is worth naming even without an advisory. A version being merely old is not a finding.

Then the parts the audit can't see:

- **No lockfile committed** means every install resolves fresh, so the build that ships is not the one anyone tested. `at risk`.
- **Install scripts.** pnpm 10 and later blocks dependency install scripts unless they are allowlisted (`onlyBuiltDependencies`, in `package.json` or `pnpm-workspace.yaml`). Read what is on that list and why; a package there runs its own code on every install, including in CI where the secrets are.
- **GitHub Actions pinned to a tag** (`uses: some/action@v3`) run whatever that tag points to today, with the workflow's secrets. Third-party actions in a workflow that can deploy or holds a production secret should be pinned to a full commit SHA. GitHub's own `actions/*` on a tag is `worth knowing` at most.
- **A script loaded from a third-party CDN** in the root layout runs on every page with the session cookie in reach. Name it, and whether it carries an `integrity` hash.

## A04 — Cryptographic failures

Mostly about what leaks, not about algorithms.

```bash
grep -rn 'NEXT_PUBLIC_' src/
```

**That prefix ships the value to the browser.** Anything behind one that looks like a secret — a key, a token, a connection string, a webhook signing secret — is already public, and rotating it is the fix. Read every hit.

**A secret passed into a client component is in the page source**, whether or not it is rendered. Props to a `"use client"` component are serialized into the payload the browser receives. Follow anything read from `process.env` in a server component and check where it goes.

Then the ordinary ones: `.env` committed to git (`git log --all --full-history -- .env`), a session cookie without `httpOnly` and `secure`, a password hashed by hand rather than by the auth library, a token stored in `localStorage` where a cookie belongs.

## A05 — Injection

Drizzle's query builder parameterises, so the classic case is narrow and specific:

```bash
grep -rn 'sql.raw\|sql`\|execute(' src/
```

A `sql.raw` with a template interpolation carrying user input is `broken`. A `sql` tagged template with `${}` is parameterised and is *not* a finding — read which one it is rather than matching on the word.

```bash
grep -rn 'dangerouslySetInnerHTML' src/
```

Legitimate on `JSON.stringify`'d structured data. A finding on anything derived from user input, from a database column, or from markdown rendered without sanitising.

Also: `child_process` with an interpolated argument, and a redirect built from a user-supplied `next` or `returnTo` parameter without checking it is a relative path — an open redirect is the phishing half of a credential attack.

**Where the app has AI features with tool access, prompt injection belongs here.** If untrusted content — a user's uploaded document, a scraped page, another account's data — reaches a model that can then call tools, describe what the model is allowed to do with what it was told. This is not a hypothetical category in an app with an MCP surface.

## A06 — Insecure design

**Rate limiting on the auth endpoints.** Better Auth's is disabled in development and defaults to in-memory storage, which does nothing across serverless instances. `storage: "database"` in `src/lib/auth.ts` is what makes it real in production. Sign-in, password reset and email-resend without it are a credential-stuffing surface.

**Account enumeration.** A sign-in that says "no such user" and a password reset that says "that address isn't registered" both tell an attacker who has an account. Better Auth's defaults are deliberately vague here; check nothing in the app has helpfully improved on them.

**Password reset tokens** — single use, short-lived, and invalidated when the password changes.

## A07 — Authentication failures

- **Changing a password revokes other sessions.** Otherwise the person who had the old one still has access, which is usually the exact reason it was changed.
- **Deleting an account revokes its tokens** — with agent access, an OAuth token outliving its user is a working credential for an account that no longer exists.
- **OAuth `redirect_uri` is validated against a registered list**, not merely received. An open redirect here is an account takeover.
- **Email verification actually gates something**, or the app doesn't claim it does. A "verified" badge that no code checks is a claim, and it belongs in the drift lens as well.

## A08 — Software or data integrity failures

**Webhook signature verification. Check this first if the app takes money.**

Every inbound webhook — payments, background jobs, email delivery — must verify its signature before acting on the body. An unverified payment webhook means anyone who finds the URL can POST a "subscription created" event and get a paid account for free, and it fails silently forever because the legitimate events keep working.

Find each webhook route and confirm three things: that it verifies, that it verifies against the **raw** body rather than a re-serialised one, and that a verification failure returns without touching the database.

## A09 — Security logging and alerting failures

The stack this reviews usually has an activity log, which is good, and which is also a place secrets go to live.

- Nothing writes a password, a token, a full request body, or an API key into a log row's detail.
- Auth events — sign-in, password change, deletion, revoked sessions — are recorded, or the app can't answer "when did that happen?"
- No admin-facing page prints a key or part of one. A masked tail is still a key with fewer characters to guess. **Check the rendered HTML in the evidence pack, not just the component source.**
- **Someone finds out.** 2025 renamed this category for a reason: a log nobody reads is a record for afterwards, not a defence. Look for anything that tells a person when something goes wrong — an error tracker wired in, an email to the owner on an admin role change or a burst of failed sign-ins, a failed webhook verification that reaches anyone. Where there is nothing, that is one `worth knowing` line, not a finding per event.

## A10 — Mishandling of exceptional conditions

New in 2025: what the app does when something fails. Two shapes matter in this stack.

**Failing open.** A `try`/`catch` around an auth or ownership check whose `catch` carries on, a `getSession()` that throws and leaves `user` as a default, a permission helper that returns `true` when the database call errors, a payment check that treats "the provider timed out" as "paid". Read every `catch` that sits in or near an authorization decision and answer: when this throws, does the request get *less* access or *more*? More is `broken`, and it is the kind that only shows up on a bad day.

```bash
grep -rn 'catch' src/app src/lib src/actions 2>/dev/null
```

**Saying too much.** A production build that returns a stack trace, a database error message, or a file path to the browser hands over the app's internals. Check the error boundaries (`error.tsx`, `global-error.tsx`) and any `catch` that returns `error.message` straight to the client — a server action returning `{ error: e.message }` puts a raw Postgres message in front of whoever triggered it.

Also: an action that does two writes without a transaction and leaves half a record when the second fails, where the half matters (a charge recorded with no order, a credit granted with no debit).

## Outside the Top 10, but this stack's own

**File uploads**, where the app has them: a type check that trusts the client-supplied MIME type, no size cap, or a filename used to build a path without stripping `../`. And whether files that should be private are served from a public URL that only needs guessing.

**The build route table**, in the evidence pack: a route rendering one account's data as `○` (Static) was prerendered at build time, so every visitor gets one person's rows. This is a real leak that reads as a performance detail.

## Your report

At most eight findings, ordered by consequence. **Never drop a confirmed `broken` finding to fit that** — if there are nine real ones, file nine and say the app needs more than a review.

Each finding: what, where (`path:line`), the OWASP 2025 category, the path from outside to the flaw, how sure (`saw it` / `suspect`), severity (`broken` / `at risk` / `worth knowing`).

Then close with what you could not check and why — no running app, no test account, no browser, no way to reach an endpoint safely. **That list is part of the finding, not an apology for it.**
