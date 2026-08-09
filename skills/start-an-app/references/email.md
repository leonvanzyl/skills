# Transactional email (Resend)

Last verified: 2026-08-09

**Purpose:** Send the emails the app owes people — verify your address, reset your password, here's your receipt, someone invited you. Real delivery in production, and a readable log locally without sending anything to anyone.

> **Hard rule: nothing sends until it's logged.** Every message goes through `src/lib/email.ts`, which writes an `email_log` row first and sends second. That row is what `references/ops.md` renders, what tells the user *why* an email never arrived, and what survives Resend's 30-day retention. Never call `resend.emails.send()` directly from a page, action, or route.
>
> If Resend's documentation and this file disagree on *how to integrate*, this file wins. If they disagree on a DNS record, dashboard path, or API detail, Resend's docs win — update this file afterwards.

**Sign-in is not required.** A contact form or a notification-only app can send email with no accounts at all. But if `references/auth.md` ran, this file also wires up email verification and password reset — Better Auth cannot do either without a sender, so those features simply do not exist until this step runs.

## Install

```bash
pnpm add resend react-email
pnpm add -D @react-email/ui
```

> React Email 6 merged everything into the single `react-email` package. Import components, `render`, and `toPlainText` from `"react-email"` — **not** `@react-email/components`, and not the per-component `@react-email/button` packages. Those still install and still resolve, which is exactly why the mistake is easy to make and hard to spot. `@react-email/ui` is the local preview server only, hence `-D`.

Append to `.env`:

```
RESEND_API_KEY=
EMAIL_FROM="My App <hello@send.example.com>"
```

Leave `RESEND_API_KEY` **empty for now**. An empty key is the local development mode — see *How sending is switched* below — so the app is fully working before the user has an account or a domain.

Add the preview server to `package.json`:

```json
"email:dev": "email dev --dir src/emails"
```

## Set up the Resend account

Do this when the user is ready to send to somebody other than themselves. Say that plainly first, because it decides whether they need a domain today:

> Resend gives you a test address, `onboarding@resend.dev`, that works instantly — but it will **only** deliver to the email address you signed up with. The moment you want to email anyone else, you need to prove you own a domain. That's a DNS change, about ten minutes, and it's free.

Then walk them through it, one step at a time:

1. Open https://resend.com and sign up.
2. **Domains → Add Domain.** Enter a **subdomain**, not the bare domain — `send.theirdomain.com` or `notifications.theirdomain.com`. Explain why in one line: if something ever goes wrong with deliverability, it damages the subdomain's reputation and leaves their main domain, and their normal email, untouched. Pick the region closest to them.
3. Resend shows three DNS records. Add all three at their domain registrar, exactly as shown:
   - an **MX** record on `send` (priority 10) — this is how bounces come back
   - a **TXT** record on `send` — SPF, which says Resend is allowed to send as them
   - a **TXT** record on `resend._domainkey` — DKIM, which signs each message
   Paste the names exactly as Resend gives them (`send`, not `send.theirdomain.com`) — most registrars add the domain themselves. On Cloudflare, set these to **DNS only**, with the orange proxy cloud off.
4. Click **Verify**. It usually completes in under fifteen minutes. If it stalls, the records are almost always right but not yet visible — wait and press it again rather than editing them.
5. Once verified, add one more **TXT** record on `_dmarc` with the value `v=DMARC1; p=none;`. It isn't needed for verification, but Gmail and Outlook increasingly expect it.
6. **API Keys → Create API Key.** Set permission to **Sending access** and restrict it to the domain just added. Copy it — it is shown once.

Fill in `.env`:

```
RESEND_API_KEY=re_<from step 6>
EMAIL_FROM="<App name> <hello@send.theirdomain.com>"
```

Any address at the verified domain works — there is no separate "sender" to create.

**Free tier, so there are no surprises:** 100 emails a day, 3,000 a month, one domain. That is generous for a new app and worth saying out loud.

## Configure

### The send helper

`src/lib/email.ts` is the only file that talks to Resend. It switches on **whether the key is present**, not on a mode flag or `NODE_ENV` — same rule as `references/storage.md`, so nothing has to be remembered at deploy time.

```ts
import "server-only";
import { Resend } from "resend";
import { eq } from "drizzle-orm";
import { db } from "@/lib/db";
import { emailLog } from "@/lib/db/schema";

const apiKey = process.env.RESEND_API_KEY;
export const emailConfigured = Boolean(apiKey);

const resend = apiKey ? new Resend(apiKey) : null;
const from = process.env.EMAIL_FROM ?? "My App <onboarding@resend.dev>";

type SendArgs = {
  to: string;
  subject: string;
  react: React.ReactNode;
  template: string;
};

export async function sendEmail({ to, subject, react, template }: SendArgs) {
  const [row] = await db
    .insert(emailLog)
    .values({ to, subject, template, status: "pending" })
    .returning();

  if (!resend) {
    console.info(
      `\n[email] ${subject}\n[email] to: ${to}\n[email] not sent — RESEND_API_KEY is empty. Logged as ${row.id}.\n`,
    );
    await db
      .update(emailLog)
      .set({ status: "logged" })
      .where(eq(emailLog.id, row.id));
    return { id: row.id };
  }

  const { data, error } = await resend.emails.send(
    { from, to, subject, react },
    { idempotencyKey: `${template}/${row.id}` },
  );

  await db
    .update(emailLog)
    .set(
      error
        ? { status: "failed", error: error.message }
        : { status: "sent", providerId: data!.id },
    )
    .where(eq(emailLog.id, row.id));

  return { id: row.id };
}
```

Three things in there are not optional, and all three are easy to get wrong:

- **`resend.emails.send()` does not throw on an API error.** It returns `{ data, error }`. A `try`/`catch` around it catches network failures only and silently swallows every rejected send — wrong domain, unverified sender, over quota. Check `error`.
- **`idempotencyKey` is the second argument**, not a field in the payload. Put it in the payload and it is ignored, and a retried request sends twice.
- **Parameters are camelCase in the Node SDK** — `replyTo`, `scheduledAt`. The REST API uses snake_case; the SDK does not, and it fails silently rather than erroring.

Anything that sends must run on the Node runtime. In a route handler, say so explicitly:

```ts
export const runtime = "nodejs";
```

### The log table

Add to `src/lib/db/schema.ts` — Postgres branch shown; on SQLite use a `text` id with `$defaultFn(() => crypto.randomUUID())` and `integer` timestamps, exactly as `references/database.md` describes.

```ts
export const emailLog = pgTable("email_log", {
  id: uuid("id").primaryKey().defaultRandom(),
  to: text("to").notNull(),
  subject: text("subject").notNull(),
  template: text("template").notNull(),
  status: text("status").notNull(), // pending | logged | sent | delivered | bounced | complained | failed
  providerId: text("provider_id"),
  error: text("error"),
  createdAt: timestamp("created_at").notNull().defaultNow(),
  updatedAt: timestamp("updated_at").notNull().defaultNow(),
});
```

```bash
pnpm db:generate
pnpm db:migrate
```

### Templates

Templates live in `src/emails/`. One file per message, plain and short — an email is not a landing page.

```tsx
// src/emails/verify-email.tsx
import { Body, Button, Container, Head, Html, Preview, Text } from "react-email";

export default function VerifyEmail({ url, name }: { url: string; name?: string }) {
  return (
    <Html>
      <Head />
      <Preview>Confirm your email address</Preview>
      <Body style={{ fontFamily: "sans-serif", backgroundColor: "#fff" }}>
        <Container style={{ maxWidth: 480, padding: "32px 0" }}>
          <Text>Hi{name ? ` ${name}` : ""},</Text>
          <Text>Confirm your email address to finish setting up your account.</Text>
          <Button href={url} style={{ background: "#000", color: "#fff", padding: "12px 20px", borderRadius: 6 }}>
            Confirm email
          </Button>
          <Text style={{ color: "#666", fontSize: 13 }}>
            If you didn&apos;t create an account, you can ignore this email.
          </Text>
        </Container>
      </Body>
    </Html>
  );
}
```

`pnpm email:dev` opens a preview at http://localhost:3000 with a mobile toggle, the plain-text version, and a spam check. It's the fastest way to iterate, and it sends nothing.

Write the copy for *their* app, in their voice. "Confirm your email to start logging hikes" beats "Verify your account".

### Wiring Better Auth (only if sign-in was chosen)

Extend `src/lib/auth.ts`. This adds to the existing config; it replaces nothing:

```ts
import { sendEmail } from "@/lib/email";
import VerifyEmail from "@/emails/verify-email";
import ResetPassword from "@/emails/reset-password";

export const auth = betterAuth({
  // ...existing config
  emailAndPassword: {
    enabled: true,
    sendResetPassword: ({ user, url }) => {
      void sendEmail({
        to: user.email,
        subject: "Reset your password",
        react: ResetPassword({ url, name: user.name }),
        template: "reset-password",
      });
    },
  },
  emailVerification: {
    sendOnSignUp: true,
    autoSignInAfterVerification: true,
    sendVerificationEmail: ({ user, url }) => {
      void sendEmail({
        to: user.email,
        subject: "Confirm your email address",
        react: VerifyEmail({ url, name: user.name }),
        template: "verify-email",
      });
    },
  },
});
```

> **`void`, not `await`.** This is Better Auth's own instruction and it is a security rule, not a style preference: awaiting the send makes the response measurably slower when the account exists than when it doesn't, which tells an attacker who has an account. Fire it and return.

**Leave `requireEmailVerification` off.** Blocking sign-in on verification turns one mistyped address into a support request the user cannot answer. `references/settings.md` builds the banner-and-resend pattern instead, which nags without locking anyone out.

Adding these hooks does not change the schema, so there is no Better Auth CLI regeneration here.

### Delivery status (optional, worth it)

Resend can tell the app what happened after the send. Add `src/app/api/webhooks/resend/route.ts`:

```ts
import { NextRequest, NextResponse } from "next/server";
import { Resend } from "resend";
import { db } from "@/lib/db";
import { emailLog } from "@/lib/db/schema";
import { eq } from "drizzle-orm";

export const runtime = "nodejs";

const resend = new Resend(process.env.RESEND_API_KEY);

export async function POST(req: NextRequest) {
  const payload = await req.text(); // raw body — parsing it breaks the signature

  let event;
  try {
    event = resend.webhooks.verify({
      payload,
      headers: {
        id: req.headers.get("svix-id")!,
        timestamp: req.headers.get("svix-timestamp")!,
        signature: req.headers.get("svix-signature")!,
      },
      webhookSecret: process.env.RESEND_WEBHOOK_SECRET!,
    });
  } catch {
    return new NextResponse("Invalid signature", { status: 400 });
  }

  const status = event.type.replace("email.", "");
  await db
    .update(emailLog)
    .set({ status, updatedAt: new Date() })
    .where(eq(emailLog.providerId, event.data.email_id));

  return new NextResponse(null, { status: 200 });
}
```

Register it under **Webhooks → Add Endpoint** at `https://<their-domain>/api/webhooks/resend`, and put the signing secret in `.env` as `RESEND_WEBHOOK_SECRET`. Signature verification needs the **raw** body — reading it as JSON and re-serialising changes the bytes and every request fails.

Resend keeps 30 days of history. `email_log` is the app's own record and keeps whatever the user wants, which is the point of writing it first.

## Testing locally

With `RESEND_API_KEY` empty, nothing leaves the machine: the message is logged to the terminal with the link clickable, and a row lands in `email_log`. That is the normal way to develop, and it means signup and password reset work end to end on day one.

To test real delivery, set the key and send to Resend's simulation addresses — these are real, documented, and safe:

| Address | What it simulates |
| --- | --- |
| `delivered@resend.dev` | a successful delivery |
| `bounced@resend.dev` | a hard bounce |
| `complained@resend.dev` | the recipient marking it as spam |
| `suppressed@resend.dev` | a previously-bounced address |

The first three accept a label, so `delivered+alice@resend.dev` and `delivered+bob@resend.dev` are distinct test users. `suppressed@` does not.

Do **not** test with `@example.com` or `@test.com` — Resend rejects them with a 422 rather than letting them damage the account's bounce rate.

## Going to production

Nothing in the code changes. Set `RESEND_API_KEY` and `EMAIL_FROM` in the host's environment variables and the same code sends for real. Tell the user that at hand-off, along with the two limits that actually bite: 100 emails a day on the free plan, and 10 API requests per second.

If they ever add marketing email — a newsletter, product updates — send it from a **different** subdomain than this one. Campaign complaints must never be able to affect whether password resets arrive.

## Verify

- `pnpm email:dev` opens the preview and each template renders, on desktop and mobile widths.
- With `RESEND_API_KEY` empty: triggering an email prints it to the terminal, the link in it works when pasted into the browser, and a row appears in `email_log` with status `logged`.
- With a real key: sending to `delivered@resend.dev` returns success and the row reaches status `sent`, visible in `pnpm db:studio` or in the app's own email log.
- Sign-in branch only: signing up sends a verification email and clicking the link marks the account verified; "forgot password" sends a reset link that actually resets the password.
- Every email's wording is about *their* app — no "My App", no placeholder addresses.
- With `.env` values absent, the app still starts and email degrades to the log instead of crashing.
