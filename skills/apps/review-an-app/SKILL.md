---
name: review-an-app
description: Review a web app that already exists and report what is actually wrong with it — security holes checked against the OWASP Top 10:2025, search and AI discoverability that has drifted out of date, and anything the app claims that it no longer does. Use when the user asks to review, audit, or check over an app, wants a security review or vulnerability check of a whole codebase rather than a diff, asks whether their sitemap, robots.txt or llms.txt are still correct, or suspects their landing page, docs or privacy policy have fallen behind the product. Reviews the app as it stands today, not a pull request and not a build sheet, so it catches what was already wrong before the current branch. Read-only by default; gathers evidence once, runs independent lenses over it in parallel, re-checks anything uncertain with a command, and names every check it could not perform rather than implying it passed.
---

# Review an App

Look at an app that already exists and say what is wrong with it. Not what a different, larger, more mature app would have — what this one gets wrong about itself.

**This is not a code review and not a deploy gate.** `/code-review` reads the pending diff and is blind to anything already wrong before this branch. `deploy-an-app` asks whether a deploy will land. `start-an-app`'s critics measure against a build sheet written the day the app was scaffolded. All three are anchored to something other than the app, which is why an app six months in has drifted past all of them. This skill reviews the thing itself, as it is now.

## Ground rules

- **The app is its own spec.** There is no build sheet here and nothing to measure against except the app's own claims — what the landing page sells, what the docs instruct, what the privacy policy promises, what the sitemap invites a crawler to open, what a button implies when it renders. A finding is a **contradiction** between what the app says and what it does. Anything else is a suggestion, and suggestions are not findings.
- **Absence is not a finding.** "No rate limiting", "no tests", "consider adding structured data" — none of these are things the app got *wrong*. They are things a bigger app would have. The single fastest way to make this skill worthless is to let it list what a mature product does; that report gets skimmed once and never again.
- **Read-only.** This skill does not edit the app. It runs commands that read, it may serve the app to probe it, and it changes nothing. Fixing is a separate, explicit ask — Step 6, and only when the user says so.
- **Consequence, not pattern.** Every finding says who is affected and how. "This query isn't scoped by user" is a pattern; "any signed-in account can read every other account's invoices by changing the id in the URL — `src/app/invoices/[id]/page.tsx:14`" is a finding. If the path from the outside world to the flaw can't be described, it isn't one yet.
- **A check that wasn't run is named, never claimed.** The same rule the rest of this family runs on. Where the app wouldn't start, where a key was absent, where a route needed a browser — say which check that cost, and what it would take. Silence reads as a pass.
- **Never conclude that the app is secure.** No review establishes that. The honest closing sentence names what was checked and what wasn't; "no vulnerabilities found" is a sentence this skill must never produce, because it will be quoted back later by someone who has stopped looking.
- **The user's choices are not findings.** A stack you'd have picked differently, a design you don't like, a deliberate decision to keep an app out of search — none of these are wrong. Where a choice looks like an accident, report the *evidence that it was an accident*, not the choice.
- **Never write or accept a version number.** Not in a command, not in prose, not a package pin. Where a check depends on something that moves — AI crawler user-agent tokens, an advisory database, a framework's file conventions — establish it at review time.
- **Lenses get evidence, not access.** They cannot share a port or a browser, and a lens that can run things will spend its budget running things. Capture once in Step 2, hand it over, and let them read.

## Step 1 — Orient

Find out what this app *is* before deciding what to check. Ten minutes here removes most of the noise, because a lens that knows the app has no payments will not go looking for webhook verification.

Establish, from the code rather than from asking:

- **The stack.** `package.json`, the framework, the router, the ORM, the auth library. This skill is written for what `start-an-app` builds — Next.js App Router, Better Auth, Drizzle, Postgres or SQLite. **Where it meets something else, say so plainly in the report and say which checks that weakened.** A review that pretends to full coverage over a stack it doesn't know is worse than a narrower one that says where its edges are.
- **Which branches exist.** Sign-in, email, uploads, payments, AI, background jobs, agent access over MCP, documentation, legal pages, a consent banner. Each one turns on a section of a lens and, more usefully, turns the others *off*.
- **Whether the app is meant to be found.** `robots.ts`, `robots.txt`, and the root layout's metadata. This decides the entire shape of the discoverability lens, and getting it backwards produces a report telling someone to optimise an internal tool.
- **What the app claims.** The landing page, the docs, the legal pages, the pricing. This is the spec, so read it before reviewing against it.

Then say in two lines what you're about to review and which lenses will run. If the user asked for only one lens, run only that one.

## Step 2 — Gather evidence, once

`references/evidence.md` has the commands: the route inventory, whether the app runs, the probe sweep, and what to capture. Three lenses read the same capture, so it is gathered once and it has to be complete before any of them start.

> **Hard rule: no secret enters the evidence pack.** It is handed to subagents and quoted in a report. Variable *names* from `.env`, never values; `git diff` and served HTML get read for leaks, never pasted wholesale. A review that leaks the key it was checking on is the only way this skill can do real damage.

## Step 3 — Run the lenses

**Dispatch them in a single message so they run at once.** Each is read-only, gets the evidence pack, and gets its own brief. The briefs are in the reference files:

| Lens | Reference | Covers |
| --- | --- | --- |
| Security | `references/security.md` | OWASP Top 10:2025, grounded in what this stack actually gets wrong |
| Discoverability | `references/seo.md` | sitemap, `robots.txt`, `llms.txt`, metadata — correct and current, or not |
| Drift | `references/drift.md` | what the app claims, against what it does |

**Each lens gets its own reference file as its brief, and nothing else** — not this file, and not another lens's output. A lens that can see another's findings starts agreeing with them, and three agreeing agents read as corroboration when they are only an echo.

The reference files here are written to be handed over, which is the opposite of `start-an-app`'s rule that its critics never see the files the app was built from. The difference is what the file *is*: those are build instructions, so giving them to a critic turns it back into a checklist-runner. These were written for the reviewer.

Every finding comes back in the same shape, whichever lens filed it:

> **What** — one sentence: what is wrong.
> **Where** — `path:line`, or the route and what it answered.
> **The contradiction** — what the app claims, and where it claims it. For security, the path from the outside world to the flaw instead.
> **How sure** — `saw it` if a file, a command or a response proves it; `suspect` if it reads that way and couldn't be confirmed.
> **Severity** — `broken` (wrong right now, someone is affected), `at risk` (works today, but by accident — the guard that should hold it is missing), or `worth knowing` (true, small, no action needed).

**Cap the small findings, never the serious ones.** More than about eight `worth knowing` items from one lens means it ran out of real material and started filling. A confirmed `broken` finding is never dropped to fit a limit.

## Step 4 — Reconcile

The lenses are done and none of them is right yet.

- **Re-check every `suspect` with a command before it goes in the report.** This is the step that separates a review from a guess, and the evidence pack already contains most of what's needed. If the command disagrees, drop the finding and say in one line that it was checked and cleared.
- **Deduplicate across lenses.** A privacy policy promising deletion that nothing performs is one finding, not a drift finding and a security finding. Keep the one that names the consequence best.
- **Drop anything that can't name its contradiction or its path.** By this point a finding either has a `path:line`, a response, or a quote from the app's own pages. If it has none, it was an opinion wearing a template.
- **Two lenses that disagree:** the one holding a `path:line` wins. Where both do, it's genuine ambiguity and it goes in the report as one.
- **Rank by consequence, not by lens.** The report is one ordered list. An unverified payment webhook and a stale `llms.txt` do not belong in the same section just because they came from different agents.

## Step 5 — Report

Ordered worst-first, in plain language, for someone who may not read code.

Lead with the count and the shape of it — "four things are wrong, one seriously" — then the findings. Each one gets what it is, where, why it matters to a person, and what fixing it involves. No severity table with nothing in it; if a lens found nothing, that is one line, and it is a result rather than a failure.

Then, and this is the part that makes the report honest:

- **What was checked, and how.** Whether the app was served or only read — the two produce very different confidence, and the reader cannot tell them apart from the findings alone.
- **What was not checked, and what it would need.** A browser, a key, a live payment, a production domain. Name each one.
- **The closing sentence never says the app is secure.** It says what this review looked at.

Where the list runs long or the user will share it, offer to publish it as a page rather than leaving it in terminal scrollback.

## Step 6 — Fix, only if asked

The review ends at Step 5. If the user then asks for fixes:

- **Confirmed `broken` findings first**, one at a time, each verified after.
- **Fixes touch only the files the finding names.** No refactors, no tidying, no "while I'm in here" — this is somebody's working app, not a scaffold.
- **A fix that needs a schema change goes through `db:generate`, a read of the generated SQL, then `db:migrate`.** Never `push`, never an edit to a migration already applied.
- **Nothing on the `worth knowing` list gets fixed** unless the user picks it out by name.
- **Re-run the relevant checks after each fix**, and say plainly if one broke something else.
