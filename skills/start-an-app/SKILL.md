---
name: start-an-app
description: Interview the user in depth about what they actually want to build, then scaffold a working full-stack web app around it. Use when the user wants to start a new app, website, prototype, or SaaS; when they don't know what tech stack to pick; or when they want a solid working starting point fast. Covers requirements discovery, project setup, database (SQLite, or Postgres on a free hosted branch, in Docker, or fully local), sign-in, file uploads, payments, AI features, an optional DESIGN.md extracted from an existing site's brand, and a real landing page and dashboard.
---

# Start an App

Turn an idea into a running web app. Understand the idea properly first, then build. The result is the user's actual app from the first commit — their name, their pages, their data model, only the infrastructure they need. It should never feel like a template.

**Understanding comes before scaffolding.** The interview is the most valuable part of this skill, not a formality to get through. Ten minutes of good questions produces an app the user recognises; skipping them produces a generic CRUD shell they have to rewrite. Do not run a single command until Step 2 is agreed.

## Ground rules

- Explain every choice like you would to a smart friend who doesn't code. Say "a place to store your data" before saying "database". Introduce each technical term once, briefly, then use it normally.
- **Use their word for the thing.** If they call it a site, a system, or "the booking thing", call it that too. Saying "app" to someone who means a website — or who hears *phone app from the App Store* — quietly tells them this wasn't built for them.
- **Dig until it's clear.** Follow up on vague answers rather than filling the gap with an assumption. "A site for my club" is not yet a spec — what does a member *do* there?
- Ask about one topic at a time. During discovery, follow the conversation rather than reading from a list; for the technical choices, one question at a time with a recommended default so the user can just say "whatever you recommend".
- Surface gaps as suggestions, not interrogation. "Most apps like this need a way to edit an entry after posting it — want that in the first version?" is better than a checklist, and it's where the user learns what they actually want.
- Recommend, then respect. If the user picks the non-recommended option, go with it without relitigating.
- **Never `drizzle-kit push`.** Schema changes always go through `db:generate` then `db:migrate`, every time, from the very first table.
- The app is scaffolded **in the current working directory** — that folder is the project root. Never create a subfolder for it and never `cd` into one; the user already chose where the app goes by being there.
- The stack is fixed: Next.js, TypeScript, Tailwind, shadcn/ui, Drizzle, Better Auth. The interview chooses *within* it (which database, what kind of sign-in, uploads, payments, AI) — it never swaps out these pieces.
- **Better Auth owns anything that belongs to a user.** Where Better Auth has a plugin for an integration — payments above all — use the plugin, never the provider's standalone SDK wired in beside it. One source of truth for the user, one place customer ids and webhooks live.
- Prefer choices that survive deployment. Where a feature works differently in production (uploads, Postgres), the local setup and the deployed setup must be the same code switched by an environment variable — never a second code path the user has to remember to change.
- **Set up what the app needs to run; offer everything beyond that.** The database is needed — wire it up yourself with the `vercel` CLI and don't make it a conversation. Pushing to GitHub and deploying are not needed for a working app, so they are offered at hand-off and never done mid-build. This skill ends with something that runs on their machine, not with their business live on the internet.
- **Do it if you can, guide if you can't, and always say which is happening.** Browser sign-ins can't be automated — `vercel login`, the Google Cloud console, a Polar or Stripe account. Say so plainly and offer to walk through it together, exactly as question 2 does for "Sign in with Google". Never pretend a step was done when the user has to do it.
- **Run commands freely, describe them in outcomes.** *"I've set up your database — it's free, it's yours, and it's already connected to where the app will live"*, never *"running `vercel integration add neon` to provision a Postgres instance"*. Good test: if you can't say what you just did in one plain sentence, don't do it unasked.
- **Four things are never done on your own initiative**, however easy the command is: creating an account or completing a login; anything that costs money, including leaving a free tier or buying a domain; anything that makes something public — the first deploy, a public repository; and attaching a domain, because their live business site is on the other end of that DNS record. Ask first, every time.
- Prefer the `vercel` CLI for Vercel work. Use a Vercel MCP server if this agent has one, but never depend on it — availability differs per user and per tool. Never use raw API calls with a hand-pasted token: it puts a credential in the conversation to do what the CLI already has a session for.
- All commands, package names, and config live in the reference files, never in this file. Load only the references for the branches the user chose.
- If a reference command fails because a tool changed (renamed flag, different init flow), check that tool's official docs, use the current equivalent, finish the job, and tell the user at the end that this skill's reference file needs a refresh.

## Step 1a — Understand the idea

Start here and stay here until the picture is sharp.

> **"What are you building? Describe it like you'd describe it to a friend."**

Then *follow up*. Listen for the **nouns** (the things the app keeps track of) and the **verbs** (what people do with them) — those become the database tables and the pages. Keep pulling until both are concrete:

- "Walk me through it — someone opens the app for the first time. What do they do?"
- "And then what? What brings them back the next day?"
- "When you say *[their vague word]* — what does that actually look like on screen?"
- **"What are you doing about this today — a spreadsheet, a notebook, WhatsApp, nothing?"**

That last one earns its place. Anyone running a business already has the process, just badly — and their spreadsheet columns *are* the data model, their WhatsApp group *is* the notification requirement. Ask to see it if they'll show you. You stop guessing at a schema and start reading one.

It has a follow-up that decides whether the result is useful on day one: **"do you want what's already in there brought across?"** A business with four hundred customers opening an empty app has been handed a demo, not a tool. If the answer is yes, say plainly that importing is its own job and offer it as the first thing after the app works.

**Then say the data model back to them in plain words** and let them correct it. This is the highest-value question in the whole skill, because people who can't design a schema can absolutely tell you what's wrong with one:

> So the app keeps a list of **hikes** — each with a date, a trail name, distance, how it felt, and some photos. They're all yours; nobody else sees them. Have I got that right, or is there something else it needs to remember?

## Step 1b — Find the gaps

The user has told you the happy path. Your job is the rest. Run through these silently, and **raise only the ones that genuinely apply** — as a suggestion with a recommendation, not a quiz:

- **Who is this for, and whose data is it?** Their customers, their staff, or just them — and is what's stored private to each person, shared across the team, or public? Those three audiences are wildly different apps, and this is the one people forget to say. **Ask this one nearly always**: it decides every query in the app, and it also answers question 1 in Step 1c, so asking it well here means not asking it twice.
- **Can things be changed?** Most descriptions only cover creating. Editing and deleting are usually wanted and almost never mentioned.
- **Is anyone special?** An admin, a moderator, an owner who sees more than everyone else.
- **What does day one look like?** The app opens with zero data. What should be on that screen?
- **Anything time-based?** Due dates, reminders, recurring items, "this week" views.
- **Does anyone need telling?** Email on signup, on invite, when something happens.
- **Phone or desktop?** Changes layout decisions early and is cheap to ask.
- **Anything sensitive in here?** Health details, children's information, card numbers. Only raise it when the subject matter suggests it — but when it applies it changes real decisions: card numbers are never stored (the payment provider holds them), sign-in defaults get stricter, and a record of who-changed-what starts being worth having in version one.
- **What is deliberately *not* in version one?** Ask directly. Naming what's out is what keeps a first version shippable, and it gives you permission to leave things out instead of guessing.

**Raise at most three.** Not "two or three usually" — three, hard, and the first and last on that list are normally two of them, which leaves you one free choice. Every one of these is a fair question and that is exactly the trap: nine fair questions in a row is an interrogation, and it's where someone who doesn't do this for a living decides the whole thing is too much like hard work. Pick the one that changes what you build; a gap found after the app exists is cheap to fill, and by then they'll be enjoying it.

## Step 1c — Technical choices

Now the branches. One at a time, each with a recommendation. **Don't ask what they've already told you** — if the description made an answer obvious ("a paid newsletter", "a photo journal"), confirm it in passing instead: *"Sounds like people will be paying for this — I'll set that up."*

1. **"Who's this for — your customers, your staff, or just you?"**
   → **Usually already answered** by the first gap-check in Step 1b. If it is, don't ask again — confirm it in passing (*"since this is for your customers, I'll set up the sturdier kind of database"*) and move to question 2. Asking a second time is how someone decides you weren't listening.
   → Just me / trying an idea: recommend **SQLite** ("your data lives in a simple file inside the project — nothing extra to install or run").
   → Other people / production ambitions: recommend **Postgres** ("the database most real apps use — I'll set it up on a free hosted plan, where you get your own private copy to build against, so nothing you do here can touch the real thing").
   → Default to **Neon through the Vercel marketplace**: free, nothing installed, and production and preview deployments are already wired up when you deploy. It needs a Vercel account and an internet connection — check that before promising it.
   → If either is a problem, `references/database.md` has three alternatives that need neither: **Docker**, a **local Postgres server** installed as a package, or **PGlite** (Postgres inside the project, offline, nothing to install). Offer whichever fits their objection; don't make them choose from a menu.

2. **"Do people need their own login?"**
   → No accounts: skip auth entirely.
   → Yes: recommend **email + password** as the default ("works immediately, nothing to configure").
   → If they want "Sign in with Google": say yes, and set expectations — it needs a free Google Cloud setup with a few copy-paste steps; offer to walk through it together or add it later.

3. **"Will people upload anything — photos, documents, a profile picture?"**
   → No: skip file storage entirely.
   → Yes: no decision to make, so don't offer one. Say what happens: "While you're building, uploads save into a folder in the project. When you deploy, they'll go to proper cloud storage automatically — same code, you just connect a store." Only mention Vercel Blob by name if they ask.

4. **"Will customers pay you through this — a subscription, or a one-off purchase?"**
   → No: skip payments entirely.
   → Yes: recommend **Polar** ("they handle sales tax and VAT worldwide for you, which is the part that usually bites"), with **Stripe** as the option if they already use it or need it.
   → Payments need accounts. If they said no to sign-in, say so plainly and add it: "we'll need accounts too, so the app knows whose subscription is whose."
   → Set expectations: everything is set up in test mode, no real money, and going live is a key swap later.

5. **"Should it do anything with AI — like answering questions, or writing text for you?"**
   → Only include AI plumbing if yes. If yes, mention they'll need an OpenRouter API key (free to create) and you'll show them where to get it — one key, many models.

6. **"When someone who's never used this before arrives, what should they see first — a page explaining what it is, or straight into the thing itself?"**
   → Decides the front door: a real landing page for something other people will sign up for, or straight into the app for a personal tool. Don't assume a marketing page — `references/pages.md` has the call.

7. **"Do you already have a website? Paste the address and I'll match your colours and fonts. If not — is there a site whose look you like?"** *(optional — one ask, then move on)*
   → A URL: extract the palette, type, shape and density from it and write them into a `DESIGN.md` the rest of the build obeys. `references/design.md`.
   → A vibe instead ("like Linear", "warm and friendly", "expensive and quiet"): equally good input — same file, skip the extraction.
   → Nothing, or "you decide": don't push. Write a short `DESIGN.md` from what the app *is*, which is what `references/pages.md` would have made you decide anyway.
   → If they name someone else's site, say once that you'll take the feel and not the identity — no logo, images, copy or stylesheet — and carry on. Don't turn it into a lecture.

## Step 2 — Build sheet

Restate the plan in plain words before touching anything. Example shape:

> Here's what I'll set up: **"TrailLog"** — a hiking journal, just for you.
>
> **Where it goes:** `H:\TrailLog` — that folder is empty, so the app will be created there.
>
> **What it remembers:** hikes — date, trail, distance, how it felt, and photos.
> **What you can do:** log a hike, edit it later, delete one, see them newest-first.
> **Signing in:** email and password, so it's yours alone.
> **Photos:** saved in the project while you build; they move to cloud storage when you deploy.
> **Look:** warm and quiet, built from the colours and type on your own site — written down in `DESIGN.md` so it stays consistent.
> **Not in version one:** sharing hikes with friends, maps, and the stats page — easy to add once the basics feel right.
>
> Sound right?

The example above is a personal tool. **When the app is for customers or staff, add the help line too** — *"a `?` in the corner opens a short guide, written from what you've just told me, so new staff can work it out without asking you"* — as something they can decline rather than something you ask about. `references/help.md` explains why it isn't a question.

Include the data model and the explicit **not in version one** list — those two lines are what stop a rewrite later. Also mention anything that needs something from them before it can work (a Vercel account, Docker running, an API key, a provider account), so there are no surprises mid-build.

**Say the full path, and say what is already in it.** Don't ask them to choose a folder — the app is created where the session already is, and an agent can't reliably write outside it. But they can't confirm a location they were never shown, and "wherever you happened to open the terminal" is not the same as a decision. One line, as above.

If the folder already contains a project — a `package.json`, a `src/`, a `.git` with history — **stop and say so.** Do not scaffold over it. Ask them to open a new, empty folder and start again there. A few stray files (a `README.md`, notes, a `.gitignore`) are fine and `references/stack.md` handles them; an existing app is not, and merging into one is unrecoverable in a way nothing else in this skill is.

Get a clear go-ahead. Adjust anything they push back on. If the answer reopens what the app *is* rather than tweaking a detail, go back to Step 1a — that's cheaper now than after the schema exists.

## Step 3 — Scaffold

Work through these in order. Each reference has a **Verify** section — complete it before moving on. Every path in them is relative to the current working directory.

1. Base project → `references/stack.md`
2. Database (SQLite or Postgres branch) → `references/database.md`
3. Sign-in, if chosen (email+password, optionally Google) → `references/auth.md`
4. File uploads, if chosen → `references/storage.md`
5. Payments, if chosen → `references/payments.md` (requires step 3)
6. AI features, if chosen → `references/ai.md`
7. Design system → `references/design.md`
8. Landing page and dashboard → `references/pages.md`
9. In-app help guide, if the app is for customers or staff → `references/help.md`

The order matters: payments and uploads both extend what step 3 built, step 7 must land before any page exists so everything inherits the tokens, step 8 needs all of it in place, and step 9 documents what step 8 actually built rather than what was planned. Anything that changes `src/lib/auth.ts` means regenerating the Better Auth schema and running `db:generate` + `db:migrate` again — the reference files say where.

## Step 4 — Make it theirs

This is not a polish pass; it is most of the value. The scaffold in Step 3 is infrastructure — here the app becomes recognisably theirs.

- Name the project after their idea (package name, page titles, visible branding).
- The schema tables are the **nouns** from Step 1a, with the ownership rule from Step 1b applied — a `userId` column and every query scoped to it if data is private.
- Build the real pages: the front door and dashboard from `references/pages.md`, real navigation, and the **verbs** from Step 1a wired up — including editing and deleting if the gap-check said so. Everything visual comes from `DESIGN.md`; no page invents a colour.
- Seed nothing generic: every visible string should make sense for *their* app. No "Item", no "Welcome to Next.js", no lorem ipsum.
- If the help guide was built, its chapters are written here too — from the interview, in their words. Done when every **verb** from Step 1a has one.
- Done when: someone opening the app would know what it is without being told, and the user can do the main thing the app exists for, end to end.

## Step 5 — Verify and hand off

- The dev server starts cleanly and the home page renders.
- `pnpm lint` passes. Next no longer runs ESLint as part of `next build`, so a build that goes green is not evidence of a clean project — a broken hook rule sails straight through it. If anything is left failing, name it at hand-off rather than leaving it to be found later.
- `drizzle/` contains generated migration files, `pnpm db:migrate` has been run, and creating one real record works end to end. No schema was ever pushed.
- If sign-in was chosen: signing up, signing out, and signing back in works; `/dashboard` redirects when signed out and shows their own data when signed in.
- If uploads were chosen: uploading a file through the app's own UI saves it and it renders after a refresh.
- If payments were chosen: the test-mode checkout completes and the paid state is visible server-side.
- `DESIGN.md` exists, `globals.css` matches it in both light and dark, and no component sets a colour outside the tokens.
- If the help guide was built: `?` opens it, every verb from Step 1a has a chapter, and it reopens where the user left it.
- **Missing keys degrade, never crash — for *optional* features.** With `.env` values absent, the app still starts and the affected feature (payments, AI, cloud storage, Google sign-in) shows a friendly "not configured yet" notice.
- **The database is not optional, so it does not degrade.** With `DATABASE_URL` missing the app fails immediately and says what's wrong in one plain sentence — *"the database isn't connected yet: run `vercel env pull .env.local`"*. An app that starts, looks fine, and then errors on the first click is worse than one that refuses to start, because it sends the user looking in the wrong place.
- Close with a plain-language summary: how to start the app (including `pnpm db:up` or `pnpm db:local` if the database runs on their machine), what each entry in `.env` is for, and two or three sensible next steps.
- Where local and production differ, spell out the one-time switch: connect a Blob store for uploads, point `DATABASE_URL` at a hosted database if it isn't already, swap payment keys out of test mode. Each is a setting on the host, not a code change — say that, because it's the part people expect to be hard.
- **Then offer the two things you deliberately didn't do**, one line each, and do neither without a clear yes:
  - *"Want me to put this on GitHub, so there's a backup and a history of every change?"* → **private by default**, and say the visibility out loud before creating it: *"I'll make it private — only you can see it."* `gh repo create <name> --private --source . --push`. If they want it public, that's their call, but it should be a decision they made rather than a default they inherited.
  - *"Want me to put it online so you can look at it on your phone?"* → `references/deploy.md`. Say what a preview URL is in one sentence: a real web address, live now, that anyone with the link can open. That last part matters to a business owner and takes four words.
    **Don't deploy from memory, however familiar the command looks.** Everything the app reads from `.env` — the auth secret, the API keys, often `DATABASE_URL` itself — exists only on the user's machine, and a deploy that doesn't carry them across produces a site that builds, goes green, loads, and then fails on the first click. That reference is a checklist for exactly that, and it verifies against the live URL rather than the one that already worked.
  - If the reason for putting it online is to **show** the app to someone — a client, a prospect, a colleague — rather than to use it, that is a different job: `references/demo.md` adds a way in that doesn't hand over the user's own data. Load it *before* `deploy.md`, because it introduces a build-time variable that has to be set before the build runs. Offer it only when the user says the deployment is for showing; a demo nobody asked for is scaffolding to delete later.
- Deploying is where this skill stops. A real launch — a custom domain, going live with payments, search engines finding it — is its own conversation, and saying so is more useful than half-doing it.
