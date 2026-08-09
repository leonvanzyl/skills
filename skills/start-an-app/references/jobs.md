# Background processing (Inngest)

Last verified: 2026-08-09

**Purpose:** Run work that shouldn't happen inside a web request — anything slow, anything that has to retry itself, anything on a schedule, anything that must survive the server restarting mid-way. And make all of it visible from inside the app.

> **Hard rule: the app keeps its own record of every job.** A row goes into the `jobs` table *before* the event is sent, and the function updates it as it goes. Inngest is the engine and the live detail view; the `jobs` table is the record. This is not belt-and-braces — Inngest's free plan keeps 24 hours of history, and its API is account-wide rather than scoped to one of the app's users, so it can be neither the archive nor the thing a user is allowed to query. `references/ops.md` renders this table.
>
> If Inngest's documentation and this file disagree on *how to structure this*, this file wins. If they disagree on an API shape or dashboard path, their docs win — update this file afterwards.

**Only open this file if the interview genuinely called for it.** Sending one email, resizing one image, or writing one row does not need a job queue; a server action does that fine. This earns its place when work must survive a restart, retry on failure, run on a schedule, fan out over many items, or wait for something that takes minutes to days. If none of that came up, close this file — an unused job system is pure overhead.

> Inngest's SDK v4 changed enough that older examples are actively wrong: triggers moved *inside* the config object, `EventSchemas` was replaced, and the SDK now assumes production unless told otherwise. Almost every tutorial and blog post online is still v3. Use what's below; if something doesn't compile, check Inngest's current docs rather than a search result.

## Install

```bash
pnpm add inngest
pnpm add -D inngest-cli concurrently
```

Append to `.env`:

```
INNGEST_DEV=1
```

That one line is the whole local setup. `INNGEST_DEV=1` tells the SDK to talk to the local dev server and skip signature checks — without it, v4 assumes production and demands a signing key. Production keys come later, at deploy time.

Change the `dev` script in `package.json` so both processes start together:

```json
"dev": "concurrently -n next,inngest -c cyan,magenta \"next dev\" \"inngest-cli dev -u http://localhost:3000/api/inngest\"",
```

`concurrently` rather than `&` or `&&`: those behave differently across shells and don't work on Windows at all.

## Configure

### The client

`src/lib/inngest/client.ts`:

```ts
import { Inngest } from "inngest";

export const inngest = new Inngest({
  id: "my-app", // kebab-case app name; this id is what production syncs against
  checkpointing: { maxRuntime: "200s" },
});
```

`maxRuntime` must sit comfortably below the hosting platform's function timeout. On Vercel that's 300 seconds, so 200 is a safe margin — the SDK wraps up and hands back before the platform kills the request.

### The endpoint

`src/app/api/inngest/route.ts`:

```ts
import { serve } from "inngest/next";
import { inngest } from "@/lib/inngest/client";
import { functions } from "@/lib/inngest/functions";

export const maxDuration = 300;

export const { GET, POST, PUT } = serve({ client: inngest, functions });
```

All three verbs are required: `PUT` registers the app, `POST` runs functions, `GET` is introspection. Miss one and the dev server finds the app but can't do anything with it.

### A function

`src/lib/inngest/functions.ts`. Name the function after the real work from the interview — `generate-monthly-report`, `import-csv`, `send-digest` — not `process-task`.

```ts
import { NonRetriableError } from "inngest";
import { eq } from "drizzle-orm";
import { inngest } from "./client";
import { db } from "@/lib/db";
import { jobs } from "@/lib/db/schema";

export const generateReport = inngest.createFunction(
  {
    id: "generate-report",
    triggers: { event: "app/report.requested" },
    retries: 4,
    onFailure: async ({ event, error }) => {
      await db
        .update(jobs)
        .set({ status: "failed", error: error.message, finishedAt: new Date() })
        .where(eq(jobs.id, event.data.event.data.jobId));
    },
  },
  async ({ event, step }) => {
    const { jobId } = event.data;

    await step.run("mark-running", async () => {
      await db.update(jobs).set({ status: "running" }).where(eq(jobs.id, jobId));
    });

    const rows = await step.run("gather-data", async () => {
      // Throwing here retries. Throwing NonRetriableError gives up immediately.
      return gatherRowsFor(event.data.userId);
    });

    const file = await step.run("render-pdf", async () => renderPdf(rows));

    await step.run("finish", async () => {
      await db
        .update(jobs)
        .set({ status: "completed", result: { file }, finishedAt: new Date() })
        .where(eq(jobs.id, jobId));
    });
  },
);

export const functions = [generateReport];
```

**How the durability actually works, so the code is written correctly:** each `step.run` result is saved. If the function fails or the server restarts, it runs again from the top — but every step that already finished returns its saved value instead of re-executing. That has two consequences worth stating to the user:

- Code *outside* a step re-runs every time. Anything with a side effect belongs inside a `step.run`.
- Step ids must be stable and unique within the function. Renaming one mid-flight orphans its saved result.

Throw `NonRetriableError` when retrying cannot help — a missing record, invalid input. Plain errors retry with backoff.

### The jobs table

Postgres branch shown; on SQLite use a `text` id with `$defaultFn(() => crypto.randomUUID())` and `integer` timestamps, per `references/database.md`.

```ts
export const jobs = pgTable("jobs", {
  id: uuid("id").primaryKey().defaultRandom(),
  kind: text("kind").notNull(),
  userId: text("user_id").references(() => user.id, { onDelete: "cascade" }),
  status: text("status").notNull().default("queued"), // queued | running | completed | failed | cancelled
  eventId: text("event_id"),
  runId: text("run_id"),
  input: jsonb("input"),
  result: jsonb("result"),
  error: text("error"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  finishedAt: timestamp("finished_at"),
});
```

`userId` is `text`, not `uuid`, because it points at a Better Auth table — the trap `references/database.md` warns about. Drop the column entirely if the app has no sign-in.

```bash
pnpm db:generate
pnpm db:migrate
```

### Starting a job

One helper, so the row always exists before the event fires:

```ts
// src/lib/inngest/enqueue.ts
import "server-only";
import { inngest } from "./client";
import { db } from "@/lib/db";
import { jobs } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export async function enqueue(
  kind: string,
  eventName: string,
  input: Record<string, unknown>,
  userId?: string,
) {
  const [job] = await db
    .insert(jobs)
    .values({ kind, userId, input, status: "queued" })
    .returning();

  const { ids } = await inngest.send({
    name: eventName,
    data: { ...input, jobId: job.id, userId },
  });

  await db.update(jobs).set({ eventId: ids[0] }).where(eq(jobs.id, job.id));
  return job;
}
```

Storing the returned event id is what later lets the app ask Inngest what happened to this exact run.

## Watching it work locally

`pnpm dev` starts Next.js and the Inngest dev server together. The dev server's UI is at **http://localhost:8288** — no Docker, no account, no signup.

It shows every event, every run, and every run's steps with timings, inputs, outputs, and retry attempts. Show it to the user: for most people this is the first time background work has been anything other than invisible.

Trigger something from the app and watch it appear. Then make a step throw on purpose and watch it retry — that demonstration is worth more than any explanation of what "durable" means.

## Going to production

1. Sign up at https://app.inngest.com.
2. **Vercel**: install the Inngest integration from the Vercel marketplace. It sets both keys and re-syncs the app on every deploy, which is the part people otherwise forget.
3. **Anywhere else** (Railway, Fly, Render, a container): copy the **Event Key** and **Signing Key** from the environment's settings into the host's environment variables as `INNGEST_EVENT_KEY` and `INNGEST_SIGNING_KEY`, deploy, then use **Apps → Sync New App** in the Inngest dashboard with the URL `https://<their-domain>/api/inngest`. Re-sync after any deploy that adds or changes a function.

Do **not** set `INNGEST_DEV` in production — v4 already defaults to cloud mode, and setting it to `0` is unnecessary noise.

Two things that waste an afternoon if unmentioned:

- On a custom domain, set `INNGEST_SERVE_ORIGIN` to it. Otherwise Inngest syncs the `*.vercel.app` deployment URL and calls the wrong host.
- Vercel's **Deployment Protection** blocks Inngest from reaching the endpoint, so syncs fail with an authentication error that looks like a key problem. Either disable it or configure a protection bypass.

**Free tier:** 50,000 function executions a month, 5 running at once, and 24 hours of history. The execution count is per *step*, not per job — a five-step function burns five. Say this at hand-off so nobody is surprised.

## Controlling jobs from inside the app

`references/ops.md` builds the page. This file provides what it calls. Add `src/lib/inngest/admin.ts`:

```ts
import "server-only";

const API = "https://api.inngest.com/v2";
const key = process.env.INNGEST_API_KEY;

async function call(path: string, init?: RequestInit) {
  if (!key) return null;
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: { Authorization: `Bearer ${key}`, "Content-Type": "application/json" },
    cache: "no-store",
  });
  return res.ok ? res.json() : null;
}

export const getRun = (runId: string) => call(`/runs/${runId}?includeOutput=true`);
export const getTrace = (runId: string) => call(`/runs/${runId}/trace`);
export const cancelRun = (runId: string) => call(`/runs/${runId}/cancel`, { method: "POST" });
export const rerunRun = (runId: string) => call(`/runs/${runId}/rerun`, { method: "POST" });
export const runsForEvent = (eventId: string) => call(`/events/${eventId}/runs`);
```

`INNGEST_API_KEY` is a separate key, created under the account menu → **API Keys** (it starts `sk-inn-api-`), not the event or signing key.

**This module is server-only and must stay that way.** The key is account-wide and not scoped to a user — anything it can read, it can read for every customer. The app's own pages query the `jobs` table (scoped by `userId`), and only reach for these functions to show live detail on a job the current user is already allowed to see.

Cancelling takes effect at the next step boundary, not mid-step. Say that in the UI — "cancelling" is an honest label, "cancelled" the instant the button is clicked is not.

## Verify

- `pnpm dev` starts both processes and the dev server at http://localhost:8288 lists the app and its functions.
- Triggering the real feature from the app's own UI creates a `jobs` row, then a run appears in the dev server with each step and its timing.
- A step made to throw retries, is visible retrying, and the `jobs` row ends as `failed` with the error recorded.
- The `jobs` row reaches `completed` on a successful run, and the app shows that state without the user refreshing something obscure.
- Job rows are scoped to the user who created them — a second account cannot see the first account's jobs.
- With `INNGEST_API_KEY` absent, the live detail view degrades to what the `jobs` table knows instead of crashing.
- With all Inngest env vars absent, the app still starts and the affected feature shows a friendly "background jobs aren't configured yet" notice.
