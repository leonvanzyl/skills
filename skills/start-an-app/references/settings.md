# Account settings

Last verified: 2026-08-09

**Purpose:** The place a signed-in person manages themselves — their profile, whether their email is confirmed, their password, the devices they're signed in on, and how to leave. Every app with accounts owes people this, and an app without it feels unfinished the first time someone asks "how do I change my password?"

**Prerequisite: sign-in must exist.** If the app has no accounts, skip this file entirely and go straight to `references/ops.md`, which builds the system page on its own.

> **Hard rule: every panel here is built on Better Auth's own API.** Do not write a route that updates the `user` table directly, hashes a password by hand, or deletes a user row with Drizzle. Better Auth owns anything that belongs to a user — the same rule that governs payments — and going around it means sessions that don't get revoked, tokens that don't get cleaned up, and a password hash format that quietly diverges from the one sign-in checks against.
>
> If Better Auth's documentation and this file disagree on *how to structure the page*, this file wins. If they disagree on a method name or option, their docs win — update this file afterwards, because this is the fastest-moving dependency in the stack.

## Two settings that have to change first

Both live in `src/lib/auth.ts`, and both cause bugs that only appear in production if skipped.

```ts
export const auth = betterAuth({
  // ...existing config

  session: {
    freshAge: 0,
  },

  user: {
    additionalFields: {
      role: {
        type: ["user", "admin"],
        required: false,
        defaultValue: "user",
        input: false,
      },
    },
    changeEmail: { enabled: true },
    deleteUser: { enabled: true },
  },

  rateLimit: {
    enabled: true,
    storage: "database",
    customRules: {
      "/send-verification-email": { window: 60, max: 2 },
      "/change-email": { window: 60, max: 3 },
      "/change-password": { window: 60, max: 5 },
      "/delete-user": { window: 60, max: 3 },
    },
  },
});
```

**`freshAge: 0`** — by default Better Auth treats a session older than 24 hours as "not fresh" and refuses to list sessions. The devices panel would then work for a day and start returning 403 to every returning user, while the revoke buttons kept working, which reads as a bug in the page rather than a policy. Turning the gate off and requiring a password on the genuinely dangerous action (deletion) is the clearer trade. Say it in a comment so nobody "fixes" it back.

**`input: false` on `role`** is the security control, not a formality. Without it the role is an ordinary profile field and a user can set their own to `admin` through the normal update call.

`rateLimit` is disabled in development and defaults to in-memory storage, which does nothing across serverless instances — `storage: "database"` is what makes the resend cooldown real.

Adding `additionalFields` and `rateLimit` changes the schema, so regenerate and migrate:

```bash
pnpm dlx @better-auth/cli@latest generate --config src/lib/auth.ts --output src/lib/db/auth-schema.ts -y
pnpm db:generate
pnpm db:migrate
```

## First account becomes the admin

Someone has to be able to see the system page, and asking the user to hand-edit a database row is a bad first experience. The first account created gets `admin`; everyone after gets `user`.

```ts
import { count } from "drizzle-orm";
import { user as userTable } from "@/lib/db/auth-schema";

databaseHooks: {
  user: {
    create: {
      before: async (user) => {
        const [row] = await db.select({ n: count() }).from(userTable);
        return { data: { ...user, role: row.n === 0 ? "admin" : "user" } };
      },
    },
  },
},
```

Then one helper, used by every admin-only page and action:

```ts
// src/lib/auth-guards.ts
import "server-only";
import { headers } from "next/headers";
import { auth } from "@/lib/auth";

export async function requireUser() {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) throw new Error("Not signed in");
  return session;
}

export async function requireAdmin() {
  const session = await requireUser();
  if (session.user.role !== "admin") throw new Error("Not allowed");
  return session;
}
```

Two accounts created in the same instant could both come out as admin. For a new app with one owner that is not worth solving; if the user asks, the answer is a unique partial index or seeding the role deliberately. Mention it only if they ask.

## The shell

`src/app/(dashboard)/settings/layout.tsx` — inside the existing dashboard route group, so it inherits the sign-in check `references/pages.md` already wrote.

```tsx
import Link from "next/link";
import { requireUser } from "@/lib/auth-guards";

export default async function SettingsLayout({ children }: { children: React.ReactNode }) {
  const session = await requireUser();
  const isAdmin = session.user.role === "admin";

  return (
    <div className="mx-auto flex max-w-5xl flex-col gap-8 px-4 py-8 md:flex-row">
      <nav className="flex gap-1 overflow-x-auto md:w-48 md:flex-col">
        <Link href="/settings">Profile</Link>
        <Link href="/settings/account">Account</Link>
        <Link href="/settings/security">Security</Link>
        {/* Notifications — only if email was set up */}
        {/* Billing — only if payments were set up */}
        {isAdmin && <Link href="/settings/system">System</Link>}
      </nav>
      <main className="flex-1 space-y-6">{children}</main>
    </div>
  );
}
```

One route per section, one shadcn `Card` per concern, each card with its own save button. Never one giant form with a single Save — the user has no idea what they're about to change, and one validation error blocks everything.

**Build only the sections this app has.** A personal tool with no payments has no Billing tab; an app that never chose email has no Notifications tab. An empty section is worse than a missing one.

## Profile — `/settings`

Name and avatar. `authClient.updateUser({ name, image })`. If the app took uploads (`references/storage.md`), the avatar goes through the existing upload route rather than a second one.

If the interview turned up profile fields that belong to *their* app — a display handle, a default currency, a home trail — add them as `additionalFields` and put them here. This is the section that stops the settings area feeling generic.

## Account — `/settings/account`

**Email and verification status.** Show the address with a badge, and the resend control only when it's needed:

```tsx
"use client";
import { useEffect, useState } from "react";
import { authClient } from "@/lib/auth-client";

export function VerifyEmailCard({ email, verified }: { email: string; verified: boolean }) {
  const [cooldown, setCooldown] = useState(0);

  useEffect(() => {
    if (!cooldown) return;
    const t = setTimeout(() => setCooldown((c) => c - 1), 1000);
    return () => clearTimeout(t);
  }, [cooldown]);

  if (verified) return <Badge variant="secondary">Email confirmed</Badge>;

  return (
    <div>
      <p>We sent a confirmation link to {email}.</p>
      <Button
        disabled={cooldown > 0}
        onClick={() =>
          authClient.sendVerificationEmail(
            { email, callbackURL: "/settings/account" },
            {
              onSuccess: () => setCooldown(60),
              onError: (ctx) => {
                const retry = Number(ctx.response.headers.get("X-Retry-After"));
                setCooldown(retry || 60);
              },
            },
          )
        }
      >
        {cooldown > 0 ? `Resend in ${cooldown}s` : "Resend confirmation"}
      </Button>
    </div>
  );
}
```

Hide the button entirely once verified — the endpoint returns a 400 for an already-verified user, and surfacing that error where a success message belongs is confusing.

**Changing email** needs a sender. `changeEmail.enabled: true` on its own returns a 400 unless `emailVerification.sendVerificationEmail` is also configured, which only happens if `references/email.md` ran.

- **Email was set up:** `authClient.changeEmail({ newEmail, callbackURL: "/settings/account" })`. A link goes to the *new* address and the change applies when it's clicked. Word the confirmation as "check your new inbox", never "email changed" — Better Auth deliberately returns success even when the address already belongs to somebody else, so that the page can't be used to discover who has an account.
- **Email was not set up:** render the field disabled with one honest line — "changing your email needs email sending set up first" — rather than a button that 400s.

**Linked sign-in methods** — only if Google sign-in was chosen. `authClient.listAccounts()` to show what's connected, `linkSocial` and `unlinkAccount` for the buttons. Keep `account.accountLinking.allowUnlinkingAll` at its default `false` so nobody can remove their last way in. A row with `providerId: "credential"` means they have a password.

## Security — `/settings/security`

**Change password:**

```ts
await authClient.changePassword({
  currentPassword,
  newPassword,
  revokeOtherSessions: true,
});
```

`currentPassword` is required. `revokeOtherSessions: true` should be checked by default — changing a password usually means "someone might have it".

**Set a password**, for accounts created through Google that have never had one. `auth.api.setPassword` is server-only, so it goes in a server action. It throws if a password already exists — use `listAccounts()` to decide which card to render rather than calling it and catching.

**Active sessions and devices.** `authClient.listSessions()` returns each session with `ipAddress`, `userAgent`, `createdAt` and `token`. Render one row each: a readable device line, the IP, when it was last active, and a **Revoke** button calling `authClient.revokeSession({ token })`. Mark the row whose token matches the current session as **This device** and don't offer to revoke it. Add "Sign out everywhere else" wired to `revokeOtherSessions()`.

Parse the user-agent into something human — "Chrome on Windows" — rather than printing the raw string. A small lookup is fine; a dependency is fine too.

## Notifications — `/settings/notifications`

Only if `references/email.md` ran. Otherwise there is nothing to opt out of and the tab should not exist.

A small table, following the id conventions in `references/database.md`:

```ts
export const notificationPreference = pgTable("notification_preference", {
  id: uuid("id").primaryKey().defaultRandom(),
  userId: text("user_id").notNull().references(() => user.id, { onDelete: "cascade" }),
  category: text("category").notNull(),
  enabled: boolean("enabled").notNull().default(true),
});
```

The categories are the ones this app actually sends — the emails named in the interview, not a generic list.

> **Transactional email ignores these preferences.** Password resets, email confirmation, receipts, and account-security notices always send, and never carry an unsubscribe link. Only optional mail — digests, product updates, activity summaries — checks the table. Putting an unsubscribe link on a password reset is how people lock themselves out.

## Billing — `/settings/billing`

Only if payments were set up. There is nothing to build: show the current plan from the server-side subscription state, then link to the provider's hosted portal that `references/payments.md` already wired (`authClient.customer.portal()` for Polar, the Stripe equivalent otherwise). Do not rebuild cancel, invoice, or card-change screens.

## Danger zone — bottom of `/settings/account`

A separate card, visually distinct, with real whitespace between it and anything harmless above it. Deletion is immediate and permanent — there is no grace period and no undo, so the confirmation has to carry the weight.

Configure it in `src/lib/auth.ts`:

```ts
user: {
  deleteUser: {
    enabled: true,
    deleteTokenExpiresIn: 60 * 60,
    sendDeleteAccountVerification: ({ user, url }) => {
      void sendEmail({
        to: user.email,
        subject: "Confirm deleting your account",
        react: ConfirmDeleteEmail({ url }),
        template: "confirm-delete",
      });
    },
    beforeDelete: async (user) => {
      // Payments branch only: cancel the subscription here, BEFORE the row goes.
      // Doing it after means a failure leaves a live subscription with no account.
    },
    afterDelete: async (user) => {
      // Uploads branch only: delete their files from storage.
    },
  },
},
```

Without `sendDeleteAccountVerification`, `deleteUser()` deletes immediately on the API call — which is why the email step matters even though deletion itself is immediate.

The dialog, in order:

1. Say exactly what disappears, counted from their real data: "This deletes your account and all 47 hikes. This cannot be undone."
2. If they're paying, say so: "Your Pro subscription will be cancelled."
3. Offer **Download my data** first.
4. Require them to **type their email address** to enable the button. Typing their own address beats typing "DELETE" — it's harder to do by reflex and it restates whose account this is.
5. Require their password.
6. `authClient.deleteUser({ password, callbackURL: "/goodbye" })` → they get an email → clicking the link deletes the account, clears every session, and lands on `/goodbye`.

**Download my data** is a small server action, not a job: read the signed-in user's own rows and return JSON.

```ts
export async function exportMyData() {
  const session = await requireUser();
  const data = {
    exportedAt: new Date().toISOString(),
    user: { name: session.user.name, email: session.user.email, createdAt: session.user.createdAt },
    // ...their rows from this app's tables, scoped by userId
  };
  return new Response(JSON.stringify(data, null, 2), {
    headers: {
      "Content-Type": "application/json",
      "Content-Disposition": 'attachment; filename="my-data.json"',
    },
  });
}
```

Include the things they created. Never include password hashes, OAuth tokens, or anything belonging to another user.

## The unverified-email banner

In the dashboard layout, above the content, whenever `session.user.emailVerified` is false:

> **Confirm your email.** We sent a link to you@example.com. [Resend] [Change email]

Do not lock the app. Let people look around, and gate only the things that would embarrass them or the app if done from an unconfirmed address — inviting others, sending outbound email, publishing something public, paying. That list comes from the interview, not from a default.

## Verify

- `/settings` is reachable from the app's navigation, not just by typing the URL.
- Changing a name saves and the new name shows in the header without a hard refresh.
- A brand-new account shows the unverified banner; confirming the email clears it and the badge flips.
- The resend button disables for 60 seconds and disappears entirely once verified.
- Changing a password works, and with "sign out other devices" checked, a second browser's session is actually ended.
- The devices list shows the current session marked as this device, and revoking another session signs it out — confirm in a second browser, and confirm the list still loads for an account signed in more than a day ago.
- Deleting a test account sends the confirmation email, the link removes the account and its data, and signing in with it afterwards fails.
- A second account cannot see the first account's data anywhere in the settings area, and `/settings/system` is not in its navigation.
- Every section that exists corresponds to something this app actually has — no empty Billing tab, no Notifications tab without email.
- With `.env` values absent, the settings pages still render and the affected controls show a friendly "not configured yet" note instead of crashing.
