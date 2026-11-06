---
name: start-an-app
description: Interview the user in depth about what they actually want to build, then scaffold a working full-stack web app around it. Use when the user wants to start a new app, website, prototype, or SaaS; when they don't know what tech stack to pick; or when they want a solid working starting point fast. Covers requirements discovery, project setup, database (SQLite or Postgres in Docker), sign-in, transactional email, file uploads, payments, AI features, background jobs, optional agent access over MCP so tools like Claude can use the app, a real landing page and dashboard, optional public help documentation, a design system agreed with the user and written to DESIGN.md so every page matches, an account settings area with system logs and debugging built in, the legal pages and cookie consent an app of that kind actually owes its users, whether search engines and AI crawlers should find it at all, and a final pass proving the result builds, serves and does what was agreed rather than taking the builder's word for it.
---

# Start an App

Turn an idea into a running web app. Understand the idea properly first, then build. The result is the user's actual app from the first commit — their name, their pages, their data model, only the infrastructure they need. It should never feel like a template.

**Understanding comes before scaffolding.** The interview is the most valuable part of this skill, not a formality to get through. Ten minutes of good questions produces an app the user recognises; skipping them produces a generic CRUD shell they have to rewrite. The only commands before the build sheet is agreed are the skill installs in Step 2a; nothing touches the app itself until Step 3.

## Ground rules

- Explain every choice like you would to a smart friend who doesn't code. Say "a place to store your data" before saying "database". Introduce each technical term once, briefly, then use it normally.
- **Dig until it's clear.** Follow up on vague answers rather than filling the gap with an assumption. "A site for my club" is not yet a spec — what does a member *do* there?
- Ask about one topic at a time. During discovery, follow the conversation rather than reading from a list; for the technical choices, one question at a time with a recommended default so the user can just say "whatever you recommend".
- Surface gaps as suggestions, not interrogation. "Most apps like this need a way to edit an entry after posting it — want that in the first version?" is better than a checklist, and it's where the user learns what they actually want.
- Recommend, then respect. If the user picks the non-recommended option, go with it without relitigating.
- **Never `drizzle-kit push`.** Schema changes always go through `db:generate` then `db:migrate`, every time, from the very first table.
- **Ids are randomly generated UUIDs — except in Better Auth's tables.** Every table you define gets one. The tables Better Auth's CLI generates stay exactly as generated, which also means any column pointing at a user stays `text`, not `uuid`. `references/database.md` has both branches.
- The app is scaffolded **in the current working directory** — that folder is the project root. Never create a subfolder for it and never `cd` into one; the user already chose where the app goes by being there.
- The stack is fixed: Next.js, TypeScript, Tailwind, shadcn/ui, Drizzle, Better Auth. The interview chooses *within* it (which database, what kind of sign-in, email, uploads, payments, AI, background jobs, documentation, whether the app is meant to be found, and how it looks) — it never swaps out these pieces, and it never bolts a second framework alongside them. Documentation is pages in this app, not a docs platform beside it.
- **Better Auth owns anything that belongs to a user.** Where Better Auth has a plugin for an integration — payments above all — use the plugin, never the provider's standalone SDK wired in beside it. One source of truth for the user, one place customer ids and webhooks live.
- **A tool is another caller, never a second way in.** If the app is opened up to AI agents, every tool goes through the same functions, the same ownership checks and the same log as the buttons do, and takes the user from the token rather than from anything the model passed. `references/mcp.md`.
- Prefer choices that survive deployment. Where a feature works differently in production (uploads, Postgres), the local setup and the deployed setup must be the same code switched by an environment variable — never a second code path the user has to remember to change.
- **Every app gets a settings area.** Not as a finishing touch — from the first commit, scaled to what the app has. Accounts mean a profile, verification status, password, devices, and a way to leave. Every app, accounts or not, gets a system view: what's configured, what happened, what's running. `references/settings.md` and `references/ops.md`.
- **What the app owes its users legally is worked out, never asked.** Whether it needs a privacy policy, terms, or a cookie banner follows from what it is and what it loads — a personal journal owes none of them, a public product people sign up for owes the first two, and a banner is owed only where something non-essential actually loads, which the session cookie is not. Decide it, build exactly that, and put the call on the build sheet in one line so the user reads a decision rather than an oversight. `references/legal.md`.
- **Anything the app does out of sight is visible and controllable from inside it.** If the app sends an email, runs work in the background, or acts on a schedule, the user can see it happened, read why it failed, stop it, and try it again — in the app, not by reading logs on a hosting dashboard. Building something the user cannot watch is not finished.
- **Whether the app should be found is asked, and both answers are built.** Only where it could plausibly be found — a public product or a content site. A personal or internal tool is never asked and never gets a sitemap; it gets a real title in the browser tab and a deliberate *keep me out of search results*, which is a deliverable rather than an omission. `references/seo.md`.
- **Documentation is written only for what exists, and only where somebody would read it.** Most apps here need none. Where a product strangers sign up for wants help pages, four honest ones beat twenty, and a page describing a feature the app doesn't have is worse than no page at all — it sends someone looking for a button that isn't there. `references/docs.md`.
- **Every app gets a written design system, and nothing overrides it later.** The look is asked about in the interview like anything else, written to `DESIGN.md` at the project root before the first screen exists, and expressed as theme tokens rather than as advice. From then on it is binding: a colour, a font size or a radius hardcoded into a component is a bug, not a shortcut, and "it looked better this way here" is how an app ends up with five blues. `AGENTS.md` and `CLAUDE.md` both point at it so that the next agent to open the project is held to it too. `references/design.md`.
- **The maintainers' own skills come before searching.** shadcn, Vercel, Better Auth and Anthropic publish agent skills for their own libraries. Step 2a installs them globally, once; from that point they are the first place to look for anything about those libraries, ahead of a search, a blog post, or memory. Reading the file that ships with the API is faster than researching it and is right more often.
- **Never write or accept a version number.** Not in an install command, not in a `package.json` snippet, not in prose, not a Docker image tag. No file in this skill pins one, and none should ever gain one. Every install takes the **current stable** release, and Step 2 is what establishes what that is. A version written into a skill file is a lie with a timestamp on it: it goes stale in silence and builds the app against last year's API.
- **Nothing deprecated, ever.** If the current release deprecates, renames, or supersedes something a reference file uses, use the replacement — not the old path that "still works". Still working is what deprecated means; it is a removal notice with a delay on it, and shipping onto one hands the user a rewrite they didn't ask for.
- **A check that wasn't run is named, never claimed.** Saying the app does something because you wrote the code that should make it do it is recall, not verification. Run the check where you can; where you can't — no browser, no key, no domain yet — say which one you couldn't do and what it would need. The user reads silence as success.
- All commands, package names, and config live in the reference files, never in this file. Load only the references for the branches the user chose.
- If a reference command fails because a tool changed (renamed flag, different init flow), check that tool's official docs, use the current equivalent, finish the job, and tell the user at the end that this skill's reference file needs a refresh.

## Step 1a — Understand the idea

Start here and stay here until the picture is sharp.

> **"What are you building? Describe it like you'd describe it to a friend."**

Then *follow up*. Listen for the **nouns** (the things the app keeps track of) and the **verbs** (what people do with them) — those become the database tables and the pages. Keep pulling until both are concrete:

- "Walk me through it — someone opens the app for the first time. What do they do?"
- "And then what? What brings them back the next day?"
- "When you say *[their vague word]* — what does that actually look like on screen?"
- "Is there anything like this you already use, that this is better than?"

**Then say the data model back to them in plain words** and let them correct it. This is the highest-value question in the whole skill, because people who can't design a schema can absolutely tell you what's wrong with one:

> So the app keeps a list of **hikes** — each with a date, a trail name, distance, how it felt, and some photos. They're all yours; nobody else sees them. Have I got that right, or is there something else it needs to remember?

## Step 1b — Find the gaps

The user has told you the happy path. Your job is the rest. Run through these silently, and **raise only the ones that genuinely apply** — as a suggestion with a recommendation, not a quiz:

- **Whose data is it?** Private to each user, shared with a team, or public? This decides every query in the app, and it's the one people forget to say.
- **Can things be changed?** Most descriptions only cover creating. Editing and deleting are usually wanted and almost never mentioned.
- **Is anyone special?** An admin, a moderator, an owner who sees more than everyone else.
- **What does day one look like?** The app opens with zero data. What should be on that screen?
- **Anything time-based?** Due dates, reminders, recurring items, "this week" views.
- **Does anyone need telling?** Email on signup, on invite, when something happens. If yes, that's the email question in Step 1c — carry the answer forward rather than asking twice.
- **Does anything take a while?** Work that shouldn't happen while someone waits — importing a file, generating a report, calling a slow service, anything on a schedule. Most apps have none; the ones that do usually mention it here rather than in the happy path.
- **Phone or desktop?** Changes layout decisions early and is cheap to ask.
- **What is deliberately *not* in version one?** Ask directly. Naming what's out is what keeps a first version shippable, and it gives you permission to leave things out instead of guessing.

Two or three of these usually matter. Raising all nine is an interrogation — pick the ones that would change what you build.

## Step 1c — Technical choices

Now the branches. One at a time, each with a recommendation. **Don't ask what they've already told you** — if the description made an answer obvious ("a paid newsletter", "a photo journal"), confirm it in passing instead: *"Sounds like people will be paying for this — I'll set that up."*

1. **"Who's going to use it — just you for now, or other people / the public?"**
   → Just me / trying an idea: recommend **SQLite** ("your data lives in a simple file inside the project — nothing extra to install or run").
   → Other people / production ambitions: recommend **Postgres** ("the database most real apps use — it runs in Docker on your machine, so it's one command to start and nothing is installed permanently, and it's the same database you'll use in production").
   → Postgres needs Docker Desktop installed and running. Check before promising it; if they don't have it and don't want it, offer SQLite or a free hosted Postgres instead.

2. **"Do people need to sign in?"**
   → No accounts: skip auth entirely.
   → Yes: recommend **email + password** as the default ("works immediately, nothing to configure").
   → If they want "Sign in with Google": say yes, and set expectations — it needs a free Google Cloud setup with a few copy-paste steps; offer to walk through it together or add it later.

3. **"Does the app need to send any email — confirming an address, resetting a password, telling someone something happened?"**
   → No: skip email entirely. Sign-in still works; there's just no verification or password reset until it's added.
   → Yes: recommend **Resend**. Set expectations honestly and early, because this is the one component that needs something they may not have: "It works straight away for sending to yourself. To email anyone else you'll need a domain name, and a few DNS records — about ten minutes, and free." If they don't have a domain, take it anyway and say the sending step waits for one — everything else works in the meantime, with emails printed to the terminal.
   → If they said no to sign-in but yes to email, that's fine — a contact form or a notification doesn't need accounts.

4. **"Will people upload anything — photos, documents, a profile picture?"**
   → No: skip file storage entirely.
   → Yes: no decision to make, so don't offer one. Say what happens: "While you're building, uploads save into a folder in the project. When you deploy, they'll go to proper cloud storage automatically — same code, you just connect a store." Only mention Vercel Blob by name if they ask.

5. **"Will people pay for anything — a subscription, or a one-off purchase?"**
   → No: skip payments entirely.
   → Yes: recommend **Polar** ("they handle sales tax and VAT worldwide for you, which is the part that usually bites"), with **Stripe** as the option if they already use it or need it.
   → Payments need accounts. If they said no to sign-in, say so plainly and add it: "we'll need accounts too, so the app knows whose subscription is whose."
   → Set expectations: everything is set up in test mode, no real money, and going live is a key swap later.

6. **"Should the app have any AI features — like a chat, or generating text or content?"**
   → Only include AI plumbing if yes. If yes, mention they'll need an OpenRouter API key (free to create) and you'll show them where to get it — one key, many models.

7. **"Does anything need to keep running on its own — work that carries on after they close the tab, or happens on a schedule?"**
   → Default is **no**, and most apps should stay there. A server action handles saving a record, sending one email, or resizing one image perfectly well; adding a job system for that is overhead with a dashboard attached.
   → Yes when work must survive a restart, retry itself after a failure, run on a schedule, fan out over many items, or wait minutes to days for something. Importing a spreadsheet, generating a report, calling a slow external service, a nightly digest.
   → If yes: recommend **Inngest** ("it runs the work outside the app, picks up where it left off if something crashes, retries on its own, and you can watch every step of it happen while you build"). It's free to start and needs no account at all during development.

8. **"Should other software be able to use this on your behalf — so you could ask Claude to add an entry or pull a summary without opening the app yourself?"**
   → A genuine either/or, so ask it that way and don't lean. Yes means the app's main actions also become tools an AI agent can call, behind the same sign-in and the same permissions — it works from Claude Code straight away, and from Claude.ai or ChatGPT once the app is deployed somewhere public. No means the app is used by people in a browser, which is a perfectly good answer, and this can be added later without changing anything built before it.
   → Worth saying if they're unsure: the tools end up being the same handful of things the app already does, so the cost is mostly the sign-in plumbing, and there's a page listing every agent that has access with a button to cut it off.
   → Needs accounts, the same way payments do. If they said no to sign-in, say it in one sentence — "an agent has to sign in as you, so the app knows whose data it's touching" — rather than treating it as a blocker.

9. **"When someone lands on the app signed out, what should they see?"**
   → Decides the front door: a real landing page for something other people will sign up for, or straight into the app for a personal tool. Don't assume a marketing page — `references/pages.md` has the call.

10. **"Should it come with a few help pages people can read without signing in?"**
    → **Ask only if the answer to 9 was a real landing page** — a product strangers sign up for, most of all one that takes money. A personal tool has one user who already knows how it works, and an internal tool's documentation is usually a message to three colleagues; asking there invites a yes to something nobody will read. Don't ask, don't build, don't mention it.
    → Default is **no**. Say what a yes actually costs: four to six short pages that have to stay true every time a screen changes. If they want it, name the pages you'd write from what they've already told you — "getting started, how it works, plans and billing, connecting Claude" — so they're agreeing to something concrete rather than to the idea of documentation.

11. **"Should search engines — and AI assistants — be able to find this?"**
    → **Ask only where the app is public**: a product people sign up for, or a site whose content is the point. For a personal or internal tool, don't ask. Say what you're doing instead, in one line: "nobody's meant to find this, so I'll give it a proper name in the browser tab and keep it out of search results" — that's the deliverable, not the absence of one.
    → Where it applies, default is **yes**, and it's cheap: a sitemap, a `robots.txt`, an `llms.txt`, and a preview card for when the link gets shared. If the docs question above was a yes, mention those pages get indexed too — for most products that's the half people actually search for.
    → One sub-question, and only where the app's *content* is the product (a blog, a directory): whether AI crawlers may train on it. Search and citation crawlers are a different thing and worth allowing — that's how an assistant recommends the app with a link. `references/seo.md` splits the two.

12. **"How should it look?"**
    → **Asked of every app**, and asked *last* — a proposal is only worth making once you know what the app is, and a personal tool deserves a point of view as much as a product does. This is the one answer that touches every screen.
    → Offer the three ways to answer in one breath, because people don't know which is allowed: *"Describe it however you like — 'calm and minimal', 'looks like Linear', 'warm, like paper'. Or paste in what you've already got — brand colours, a font, a whole design document, a style guide. Or say 'you pick' and I'll propose something for you to shoot down."*
    → **If they paste something, it wins outright** — colours, fonts, spacing, tone, component conventions, all of it, used as given rather than as inspiration. Where it doesn't cover something the app needs (usually dark mode, or a radius), fill the gap in its spirit and say which parts were yours.
    → **If they answer in words, play it back as decisions, not adjectives.** "Calm and minimal" becomes a named neutral base, one accent, a generous radius, a specific font — so they're correcting something concrete instead of agreeing with a mood.
    → **If they say "you pick", propose — don't ask a second time.** Two or three directions with real names, one line each, drawn from what the app *is*: a developer tool, a children's reading tracker and an invoicing app should not look alike. Recommend one. `references/design.md` has how to choose.
    → Whichever route it took, the answer becomes **`DESIGN.md` at the project root** in Step 4, and every page built afterwards is held to it.

## Step 2 — Get the current facts

The branches are chosen, so now find out what building them actually involves *today*. Two halves, in this order: **install the skills the maintainers of these libraries publish, then research only what those skills don't already answer.** Doing it the other way round spends a research round rediscovering what was one install away.

### Step 2a — Install the official skills

shadcn, Vercel, Better Auth and Anthropic each publish an agent skill for their own library. They are the instructions of the people whose API it is, kept current by them, and between them they cover most of what this build is made of — components, React and Next patterns, sign-in, the AI SDK, MCP tools. An agent that skips them spends the build searching for documentation that is already sitting on disk, and lands on blog posts that were written against an older release.

**Install the whole set globally, before the research below and before the build sheet.** Globally — `-g` — for two reasons. The folder the user is standing in is about to become the app, and `create-next-app .` refuses to run in a directory that isn't empty; a project-level install would put `.claude/` and `skills-lock.json` there and force a workaround on every single build. And these are documentation for a fixed stack, not for one app: installed once, they are there for the next app, and for every session that opens this one afterwards.

Say what you're doing in one line first, because six installs is a visible pause: "Before I plan this out, I'm pulling in the instruction manuals the people behind these tools publish — it saves me guessing at their documentation later." Then run them.

```bash
npx skills add https://github.com/shadcn-ui/ui --skill shadcn -g --agent claude-code -y
npx skills add https://github.com/vercel-labs/agent-skills --skill vercel-react-best-practices -g --agent claude-code -y
npx skills add https://github.com/vercel-labs/agent-skills --skill deploy-to-vercel -g --agent claude-code -y
npx skills add https://github.com/better-auth/skills --skill better-auth-best-practices -g --agent claude-code -y
npx skills add https://github.com/vercel/ai --skill ai-sdk -g --agent claude-code -y
npx skills add https://github.com/anthropics/skills --skill mcp-builder -g --agent claude-code -y
```

`--agent claude-code -y` is what makes each one non-interactive; without both flags the command stops on a prompt with nobody there to answer it. Install all six even where a branch wasn't chosen — they are inert until something reads them, and the two branch-specific ones are exactly what the user will need the week they add AI or agent access.

**Run all six even if some are already installed from a previous app.** A re-add is a refresh, not a duplicate, and it is cheaper than checking. What is *not* acceptable is assuming they're there because this skill ran before — read them from disk during the build rather than from memory of the last one.

Nothing lands in the project. They install under the user's own `~/.claude/skills/`, so the folder Step 4 scaffolds into stays empty and `create-next-app .` behaves.

Which one answers what:

| Skill | Read it when |
| --- | --- |
| `shadcn` | Adding, composing or theming any component — `references/stack.md`, `pages.md`, `settings.md`, `docs.md` |
| `vercel-react-best-practices` | Any React or Next code at all: server vs client components, data fetching, forms, caching, Step 5's real pages |
| `better-auth-best-practices` | `references/auth.md`, and everything that extends `src/lib/auth.ts` afterwards — payments, agent access, settings |
| `ai-sdk` | `references/ai.md` |
| `mcp-builder` | `references/mcp.md` — tool design, naming, what a tool hands back |
| `deploy-to-vercel` | Not during the build. It is installed for the hand-off in Step 8 and for whoever deploys the app later |

**Precedence, when a skill and a reference file disagree.** The same split the research uses below. **The official skill wins on API detail and on its own library's idiom** — names, signatures, imports, options, which hook, which component, what the current recommended pattern is. **This skill's reference files win on how the piece wires into this app** — which file owns what, how it meets the schema, the session, the log and the settings area. Where a reference file hand-rolls something the official skill shows a first-class way to do, take the skill's way and delete the workaround, then say so at hand-off.

**They set no scope.** An official skill will cheerfully recommend a feature, a provider or an extra package. What the app contains is Step 3's, agreed with the user, and a skill's enthusiasm is not a reason to widen it.

### Step 2b — Check what's left

Nothing in this skill names a version, deliberately — this half is where the versions come from. It costs one round of parallel subagents and prevents the expensive failure: an app built confidently against an API that moved.

**Dispatch one subagent per chosen branch, all in a single message so they run at once.** Only the branches the interview selected — there is no sense researching payments for an app that takes no money. The base project, the database, the pages step and discoverability always count as branches here.

Each gets the same brief with its own packages filled in, and — where the table in Step 2a names a skill for that branch — the path to it:

> Read the `<skill>` skill first, if one is named for this branch — it is installed under `~/.claude/skills/`, it is the maintainer's own documentation, and it outranks anything you find by searching. Research only what it does not answer, and mark which of your findings came from it. Then: find the current stable release of `<packages>`. Report: the latest stable version of each; anything deprecated, renamed, moved to a different package, or removed within the last two majors; the current import paths and function signatures for `<the specific things this reference file uses>`; **any capability added since that would replace hand-written code in `references/<file>.md`**; and any migration note that would break what's in there. Prefer the package's own docs and changelog over blog posts or search summaries, and check what is actually published on the registry rather than what a docs page claims. Say plainly what you verified against a primary source and what you inferred.

**The agent-access branch gets one extra sentence in its brief**, because packages are not the only thing that moves under it: *establish the current revision of the Model Context Protocol specification, and check `references/mcp.md`'s assumptions against that revision's changelog and its registry of deprecated features.* A protocol revision can deprecate something the file relies on without any package changing its name or its signature, and the brief above would sail straight past it. No other branch sits on a spec that versions independently of its libraries.

**The discoverability branch installs no packages and researches conventions instead**, so give it its own brief: *confirm Next's current `MetadataRoute` file conventions for `sitemap`, `robots` and `opengraph-image`; and — only where the app is meant to be found — establish the current user-agent tokens for AI crawlers, split into training, search/citation, and user-initiated, and whether `llms.txt` has moved past a proposal toward anything a named crawler documents reading.* Crawler names change without notice, and a wrong one in `robots.ts` is not an error, it is a rule that silently matches nothing.

Each reference file carries a `Last verified` date at the top. Use it to size the effort: a file verified recently needs a confirmation pass, one verified a year ago needs the assumption that something has moved.

Then reconcile, before installing anything:

- **Latest stable only.** Not release candidates, not betas, not `next` or `canary` tags — unless the user asks for one specifically and knows why.
- **Take the new capability when there is one.** Reference files sometimes hand-roll something because the library couldn't do it yet. If it can now, use the built-in and delete the workaround — `references/mcp.md` says exactly where this is likely.
- **On API detail the research wins; on how the pieces fit together this skill wins.** Names, signatures, import paths, options, flags: take what the research found. Which piece owns what, and how it wires into the rest of the app: the reference file. Most reference files restate this split at the top for their own dependency.
- **Where the research and an installed skill disagree, look at what kind of disagreement it is.** On what is published *right now* — a version, a package that split, a signature that changed — the registry is the fact and the research wins, because a skill is a file and files go stale. On which pattern to use among several that all work, the official skill wins; that is its author speaking about their own library. If the skill describes something the registry says no longer exists, say so at hand-off — it is worth knowing that the maintainer's skill has drifted.
- **If a reference file's approach is now deprecated, take the replacement** and finish the job with it. Don't split the difference.
- **Say something to the user only when something changed.** One line, plain: "Better Auth moved that into a separate package since this was written — I'm using the new one." Never narrate research that found everything was fine; it reads as filler.
- **Write down what's stale.** Anything the research contradicted goes in the hand-off at the end, so this skill can be corrected.

## Step 3 — Build sheet

Restate the plan in plain words before touching anything. Example shape:

> Here's what I'll set up: **"TrailLog"** — a hiking journal, just for you.
>
> **What it remembers:** hikes — date, trail, distance, how it felt, and photos.
> **What you can do:** log a hike, edit it later, delete one, see them newest-first.
> **Signing in:** email and password, so it's yours alone.
> **How it'll look:** quiet and outdoorsy — a warm off-white background, a deep green accent, soft corners, and a serif for headings. Written down in `DESIGN.md` so every screen matches.
> **Photos:** saved in the project while you build; they move to cloud storage when you deploy.
> **From Claude:** you'll be able to log a hike or ask about past ones from Claude itself, without opening the app — and see and revoke that access from inside it.
> **Also included:** a settings page where you can change your password and delete your account, and a system page showing what's set up and what's happened.
> **Legal:** nothing needed — it's just you, and nothing here tracks anyone, so no privacy policy, no terms, no cookie banner.
> **Being found:** nothing to index — it's just you, so I'll give it a proper name in the browser tab and keep it out of search results.
> **Not in version one:** sharing hikes with friends, maps, and the stats page — easy to add once the basics feel right.
>
> Sound right?

Include the data model and the explicit **not in version one** list — those two lines are what stop a rewrite later. The **legal** line goes in either way and is a statement, not a question: this example says nothing is needed and why, and a public product would name the pages it gets instead. `references/legal.md` makes the call. The **being found** line goes in either way too, and this example shows the harder half — the app that is deliberately kept out of search still gets a line, because "no SEO" read as silence looks like something forgotten. A public product names what it gets instead: sitemap, `robots.txt`, `llms.txt`, and a preview card for shared links. A **help pages** line appears only where the docs question was asked and answered yes, and it names the pages rather than promising documentation. The **how it'll look** line goes in every sheet and is where a design gets corrected cheaply: name the actual decisions — background, accent, corners, font — not a mood, because "clean and modern" is something nobody can disagree with and therefore nothing they have agreed to. Where they pasted a design system in, say you're using theirs and name anything you had to fill in yourself. Also mention anything that needs something from them before it can work (Docker running, an API key, a domain for email, a provider account), so there are no surprises mid-build.

Get a clear go-ahead. Adjust anything they push back on. If the answer reopens what the app *is* rather than tweaking a detail, go back to Step 1a — that's cheaper now than after the schema exists.

## Step 4 — Scaffold

Work through these in order. Each reference has a **Verify** section — complete it before moving on. Those are your own check as you go; Step 6 is the one that has to survive a command. Every path in them is relative to the current working directory.

**The skills installed in Step 2a are read alongside these files, not after a build fails.** The table there says which one belongs beside which step: `shadcn` and `vercel-react-best-practices` apply across almost all of them, `better-auth-best-practices` from sign-in onward, `ai-sdk` and `mcp-builder` at their own steps. Read the relevant one *before* writing that file's code. Searching the web for an answer that is already installed on this machine is the specific waste this step is arranged to avoid.

**And from step 2 onward, `DESIGN.md` governs every screen any of these steps builds** — the settings area, the emails, the consent screen, the legal pages, the docs. None of them re-decides how the app looks, and none of them writes a colour, a font size or a radius into a component.

1. Base project → `references/stack.md`
2. Design system → `references/design.md` (always; writes `DESIGN.md`, the theme tokens, `AGENTS.md` and `CLAUDE.md`)
3. Database (SQLite or Postgres-in-Docker branch) → `references/database.md`
4. Sign-in, if chosen (email+password, optionally Google) → `references/auth.md`
5. Email, if chosen → `references/email.md` (also wires verification and password reset, if sign-in ran)
6. File uploads, if chosen → `references/storage.md`
7. Payments, if chosen → `references/payments.md` (requires sign-in)
8. AI features, if chosen → `references/ai.md`
9. Background jobs, if chosen → `references/jobs.md`
10. Landing page and dashboard → `references/pages.md`
11. Agent access, if chosen → `references/mcp.md` (requires sign-in)
12. Public documentation, if chosen → `references/docs.md` (rarely; only a public product that was asked and said yes)
13. Legal pages and cookie consent, as much as this app owes → `references/legal.md` (decided, never asked; often nothing)
14. Account settings → `references/settings.md` (requires sign-in; skip only if there is no sign-in)
15. System visibility → `references/ops.md` (always)
16. Discoverability → `references/seo.md` (always, but for most apps this means a real title and staying out of search)

**The design system comes second, immediately after the scaffold, because it is the only step every later one reads from.** It needs the project to exist — `globals.css` and `layout.tsx` are what it edits — and it needs to be in place before a single screen is built, because retrofitting a theme onto pages already written means editing all of them. It is also where `AGENTS.md` and `CLAUDE.md` get written, so every step after it, and every agent that opens this project later, is held to the same document.

The rest of the order matters too: payments, uploads and agent access all extend what sign-in built; the pages step needs the lot in place; and settings and system visibility hang off the navigation the pages step creates. Agent access sits after the pages step because its consent screen has to look like the rest of the app, and before the rest because each grows a section only if it ran. Documentation comes next because it can only describe branches that exist, and before legal so that legal's pass over the footer sees the docs link already there. Legal comes after every feature branch for the same reason in reverse — the privacy page has to describe all of them — and before settings, which grows a cookie-preferences section only if a banner was built. Anything that changes `src/lib/auth.ts` means regenerating the Better Auth schema and running `db:generate` + `db:migrate` again — the reference files say where.

**Discoverability is last because it is the only step that has to know every public page.** It writes the sitemap and `llms.txt` from one list, and legal and documentation both add pages to it — a sitemap written before them is wrong the moment they run.

The last three are not a polish pass to drop if time is short. Two of them turn a scaffold into something the user can operate, and the third decides whether anyone will ever find it.

## Step 5 — Make it theirs

This is not a polish pass; it is most of the value. The scaffold in Step 4 is infrastructure — here the app becomes recognisably theirs.

- Name the project after their idea (package name, page titles, visible branding).
- The schema tables are the **nouns** from Step 1a, each with a UUID primary key, and the ownership rule from Step 1b applied — a `userId` column (`text`, matching Better Auth) and every query scoped to it if data is private.
- Build the real pages: the front door and dashboard from `references/pages.md`, real navigation, and the **verbs** from Step 1a wired up — including editing and deleting if the gap-check said so. This is the densest React in the app and where `vercel-react-best-practices` earns its install — server versus client components, where data is fetched, what a form does. Compose the screens from `shadcn` components rather than hand-writing markup that approximates them, and build them to `DESIGN.md` — the decisions were made and agreed already, so this step spends its judgement on the app, not on picking colours again.
- Seed nothing generic: every visible string should make sense for *their* app. No "Item", no "Welcome to Next.js", no lorem ipsum. This includes the settings area, the emails, the legal pages, any documentation, and **the browser tab** — a section called "Notifications" listing categories the app never sends, an email signed "My App", a privacy policy about "user-generated items" in an app whose every other screen says "hikes", or a tab still reading "Create Next App", are all the same failure as a page of lorem ipsum.
- Build only the settings sections this app has. An empty Billing tab or a Notifications tab for an app that sends no email is worse than a missing one.
- If agent access was chosen, the tools are named for the **verbs** too — `log_hike`, not `create_item` — and they are the handful of things someone would actually ask for, not one per table.
- Done when: someone opening the app would know what it is without being told, and the user can do the main thing the app exists for, end to end.

## Step 6 — Prove it

The app is built. Nothing has established that it works. Every Verify section you just completed was confirmed by the same agent that wrote the code it checks, and recall is not evidence — an app can satisfy every one of them while failing to compile.

`references/verify.md` has the commands: types, schema drift, the build, lint, the app served in production mode, every route answering, two accounts against each other, and the app with its keys taken away. Read the output of each. Having written the code a command tests is the reason to run it, not a reason to skip it.

Two points of order matter enough to say here, because getting either wrong does damage:

- **Schema before build.** `build` runs `db:migrate` first, so reaching it with an ungenerated schema edit outstanding applies SQL nobody read — the one thing `references/database.md` says never to do, performed by the step meant to catch it.
- **The user signs up before any probe account exists.** The first account created becomes the admin. A fixture that takes that place, and is then deleted, locks the user out of their own system page.

Where a check needs a browser, a provider, or a person, `references/verify.md` lists it. Name what you couldn't run.

## Step 7 — Fresh eyes

The gate proves the app builds, serves and answers. It cannot tell whether the app *does* anything — an empty project passes every command in it, because nothing leaks when there is nothing to leak. So the last check is the one the builder cannot perform on itself.

**Dispatch the critics in a single message so they run at once**, the same way Step 2 does: promise-keeping and looks-like-theirs always, ownership wherever there is sign-in, operability scaled to the branches that ran. The briefs are in `references/verify.md`.

**They check the app against the Step 3 build sheet, and against nothing else.** That sheet is the only bar here, because it is the one thing the user actually approved — and they approved a description of an app without being able to read the code they were handed. Closing exactly that gap is the whole job. Critics report where the app diverges from the sheet; they never propose a different sheet. Anything that would change what the app *is* goes to the user at hand-off, the same as it would have gone to them at Step 3.

They read evidence, not the running app. Four agents cannot share a port or a browser between them, so capture everything once during Step 6 and hand it over. Findings come back as `broken`, `missing` or `worth knowing`; only the first two are fixed now, and no fix widens the gate or changes scope.

**Two rounds, then stop and report what's left.** A third round is where an agent starts editing code it doesn't understand to make a report go away. Tell the user this step is happening, in one line — otherwise they are watching a terminal do nothing.

## Step 8 — Hand off

- Every check that could not be run is named, with what it would need — a browser, a domain, a payment key — as a short list they can work through in a minute once the app is open. Findings left unfixed after Step 7, and any finding you disagreed with, go here too, one line each with the reason.
- Anything Step 2's research contradicted, or any reference command that had to be changed on the fly, is named at the end — which file, what was wrong — so this skill can be corrected. Say it to the user in one line; they may be the person who fixes it.
- Legal branch: say once, plainly, that the privacy and terms pages are a first draft assembled from what the app actually does rather than legal advice. Then list the fields in `src/lib/legal.ts` that only they can fill — usually a contact address and whose law governs the terms — as a short thing they can clear in a minute. Where there is no cookie banner, give the one-line reason and what would change it: "nothing here tracks anyone, so there's nothing to consent to — add analytics later and it'll need one."
- Discoverability, kept out of search: name the two places the switch lives — `robots: { index: false }` in `src/app/layout.tsx` and `src/app/robots.ts` — as the thing to change if the app ever goes public. Left in place on a launched product it costs them every visitor they were expecting, and it is invisible.
- Discoverability, public: say plainly that a sitemap is an invitation and not a ranking, that `llms.txt` is a proposed convention no major AI crawler has committed to reading, and that what a crawler is actually *permitted* to do lives in `robots.txt` alone. Point them at the preview card once — it is what a shared link looks like, and it is the first thing they'll see the app judged by.
- Docs branch: say how many pages there are and that they are true today, which makes them the first thing to go stale. If writing any page was hard because the flow needed explaining, say which one — that is a finding about the app, not about the page.
- Say once, in a line, that this build read from the maintainers' own skills — shadcn's, Vercel's, Better Auth's, the AI SDK's and MCP's — installed once at Step 2a and now available in every project on this machine, refreshed with `npx skills update -g`. Nothing was added to the app's own folder. Name `deploy-to-vercel` as the one that hasn't been used yet: it is what puts the app online when they're ready.
- Close with a plain-language summary: how to start the app (including `pnpm db:up` if Postgres is in Docker), what each entry in `.env` is for, and two or three sensible next steps.
- Point at `DESIGN.md` in one line: it's the app's look written down, `AGENTS.md` and `CLAUDE.md` point any agent at it, and changing a colour there and in `globals.css` restyles every page at once. Say which parts came from them and which you proposed — those are the ones most likely to want changing.
- Show them the system page and say what it's for. It is the answer to "why didn't that email arrive?" and "is that still running?", and they will not find it on their own.
- Where local and production differ, spell out the one-time switch: connect a Blob store for uploads, point `POSTGRES_URL` at a hosted database, swap payment keys out of test mode, add the Resend key once the domain is verified, add the Inngest keys and sync the app, point `BETTER_AUTH_URL` at the real domain so agent tokens are issued for it, and set `APP_URL` to the same real domain so the sitemap, canonical links and preview card aren't full of `localhost`. Each is a setting on the host, not a code change — say that, because it's the part people expect to be hard. The two that also need an action outside the host are verifying the email domain in DNS and syncing the app with Inngest after the first deploy; call those out by name.
