# Deploying to Vercel

Last verified: 2026-07-28

**Purpose:** Take the app that runs on the user's machine and make it work at a real web address, for real people. **Loaded only when the user has said yes to the offer in Step 5** — putting something on the internet is one of the four things this skill never does on its own initiative.

The whole of this file exists because of one asymmetry: the app has been running against environment variables that live in files on the user's laptop, and the deployment cannot see any of them. Everything below is a consequence of that.

## The failure this prevents

A deploy that skips this file does not error. It builds, it goes green, the URL loads, the landing page renders — and then the first click fails, or sign-in refuses every password, or the app quietly reads an empty database. The user is looking at what appears to be a working site, which is the worst possible place to start debugging from.

So: **check before deploying, and verify on the live URL afterwards.** Not locally. Locally it already works; that is the problem.

## If the app was built on the SQLite branch, start here

SQLite lives in a file inside the project. A deployment's filesystem is read-only or ephemeral and every instance gets its own, so the file either cannot be written or silently stops being shared — and data appears to vanish between requests.

**Deploying a SQLite app means moving it to Postgres first**, which is the Postgres branch of `references/database.md` with a hosted connection string: same Drizzle schema, same queries, `pnpm db:generate` and `pnpm db:migrate` against the new database, and the driver swapped in `src/lib/db/index.ts`. Say this plainly and early rather than after a confusing deploy. It is a twenty-minute job, and it is far easier before there is data in the file worth keeping.

## Step 1 — What does the app actually read?

Find every environment variable the source depends on:

```bash
grep -rho "process\.env\.[A-Z0-9_]*" src | sort -u
```

That list — minus anything Vercel sets itself (`VERCEL_*`, `NODE_ENV`) — is what production needs. Then see what is actually there:

```bash
vercel env ls production
```

Compare the two lists by hand. It takes ten seconds and it is the single highest-value check in this file.

What typically has to be added, and why each one is missed:

| Variable | Why it's missing | Where the value comes from |
|---|---|---|
| `DATABASE_URL` | The Neon integration sets `POSTGRES_URL` and `PG*`; `DATABASE_URL` can be development-scoped only | Copy the pooled URL from `.env.local` |
| `BETTER_AUTH_SECRET` | Written into `.env`, which is gitignored and never uploaded | **Generate a fresh one** — see below |
| `BETTER_AUTH_URL` | Same, and its local value is `http://localhost:3000` | The deployed origin — see Step 3 |
| `OPENROUTER_API_KEY`, `POLAR_*`, Google client id/secret | All hand-written into `.env` | The same values, unless the user is going live for real |
| `NEXT_PUBLIC_*` anything | Inlined at **build** time, so it must exist before the build, not just at runtime | Whatever the flag should be in production |

`BLOB_READ_WRITE_TOKEN` is the exception that looks like the rule: connecting a Blob store in the Vercel dashboard sets it for you. `references/storage.md` covers it.

**Generate a new auth secret for production rather than reusing the development one.** It is one command, and it means a secret that has been sitting in a local file, in shell history, and possibly in a screenshot is not the one signing real users' sessions:

```bash
node -e "console.log(require('crypto').randomBytes(32).toString('base64'))"
```

Add each value:

```bash
printf '%s' "<value>" | vercel env add NAME production
```

To **change** one that already exists, remove it first — `add` does not overwrite:

```bash
vercel env rm NAME production --yes
printf '%s' "<new value>" | vercel env add NAME production
```

**Environment variables are read at deploy time, so changing one changes nothing until you redeploy.** Every fix in this file ends with another `vercel deploy --prod`.

### Values added by the CLI do not read back

`vercel env pull` writes an empty string for variables that were added this way — they are stored write-only. `NAME=""` in the pulled file means "cannot be shown", **not** "was saved empty, add it again". Adding them a second time because the pull looked wrong is a loop that can eat twenty minutes and ends where it started.

The way to confirm a value landed is to use the deployed app. That is what Step 5 is for.

## Step 2 — Deploy

```bash
vercel deploy --prod --yes
```

`--prod` puts it on the project's own address rather than a one-off preview URL. Without it the user gets a preview deployment, which is fine for a look on a phone but is protected (see Step 3) and will not be what they mean by "online".

Expect to deploy **twice**: the first one tells you the address, and the address is what `BETTER_AUTH_URL` has to be. That is not a mistake in the process, it is the process — say so rather than letting it look like a retry.

## Step 3 — The address, and why it might not be public

Two things surprise people here, and both look like the app is broken.

**The name may be taken.** `<project>.vercel.app` is global across every Vercel account, not per-user. If someone else has it, the CLI silently assigns a variant — `<project>-alpha.vercel.app` — and reports it in one line of output that is easy to read past. Read the `Aliased` line; that is the real address.

**Only the project's own production domain is public.** Deployment Protection covers everything else, including a domain attached by hand with `vercel alias set`: it answers `302` to `vercel.com/sso-api`, so it works perfectly for the signed-in owner and shows a Vercel login to everybody they send it to. This is a genuinely nasty one — the person who tests it is the one person who cannot reproduce the problem.

Check with a request, not a browser you happen to be logged into:

```bash
curl -s -o /dev/null -w "%{http_code}\n" https://<domain>/
```

`200` is public. `302` is protected.

To get a different name, change what the production domain follows — the project name — rather than bolting an alias on the side:

```bash
vercel project rename <old-name> <new-name>
vercel domains add <new-name>.vercel.app <new-name>
```

Then redeploy, and the `Aliased` line will show the new address.

**Renaming a project is the user's call, not yours.** It is their project, the old address stops being canonical, and anyone they have already sent a link to is affected. Ask, offer the alternative of living with the assigned name, and do not treat a cosmetic URL as worth a surprise.

## Step 4 — Sign-in after the move

Better Auth checks the origin of every sign-in request against its configured URL. `references/auth.md` documents this as a localhost port problem; deployment is the same failure with a different cause, and the message — `Invalid origin` — still says nothing about what is actually wrong.

- `BETTER_AUTH_URL` must be the deployed origin, exactly: scheme, host, no trailing slash.
- If **more than one hostname** serves the app — the assigned name and a renamed one, a custom domain alongside the `.vercel.app` — the extras need to be trusted explicitly, or a sign-in from the one the user actually typed is refused:

  ```ts
  export const auth = betterAuth({
    // ...
    trustedOrigins: [
      "https://<the app's domain>",
      "https://<any other domain that serves it>",
    ],
  });
  ```

- Google sign-in, if it was set up, needs the production callback URL added in the Google console: `https://<domain>/api/auth/callback/google`. Google matches exactly, and nothing in `redirect_uri_mismatch` mentions that the deployment is new.

## Step 5 — Verify, on the live URL

Locally proves nothing here. Every check below is against the deployed address.

- `curl -s -o /dev/null -w "%{http_code}" https://<domain>/` returns **200**, not a 302 to Vercel SSO.
- The front door renders, and any `NEXT_PUBLIC_` flag has taken effect (those are baked in at build time — if one is wrong, no amount of redeploying without a rebuild fixes it).
- **Sign up with a new account on the live site, sign out, sign back in.** This is the check that exercises `DATABASE_URL`, `BETTER_AUTH_SECRET` and `BETTER_AUTH_URL` in one action — if all three are right, it works, and if any one is wrong, it doesn't.
- **Create one real record through the app's own UI and reload the page.** That proves the deployment is talking to the database the migrations ran on, which a page that merely renders does not.
- Uploads, if set up: upload a file and confirm it renders after a refresh — this is where a missing Blob store shows up.
- Payments, if set up: the test-mode checkout still completes from the deployed origin.
- `vercel logs <deployment-url>` is clean of runtime errors after all of the above.

## Hand off

Tell the user, in plain words:

- The address, and that anyone with the link can open it.
- That the database behind it is the **live** one — the one their local app has been carefully kept away from. Anything they do on the live site is real.
- Which environment variables now exist in two places (their machine and Vercel), and that changing one on Vercel needs a redeploy to take effect.
- That a preview deployment happens for every future push, at its own URL, and those are private to them.

**A real launch is still a separate conversation** — a custom domain, payments out of test mode, search engines. Deploying is where this skill stops.
