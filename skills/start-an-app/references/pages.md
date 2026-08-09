# Landing page and dashboard

Last verified: 2026-07-27

**Purpose:** Give the app a real front door and, when there are accounts, a real place to land after signing in. This is the step that decides whether the result looks like *their app* or like a scaffold with the boxes ticked.

## First: what is the front door?

Do not reflexively build a marketing landing page. Pick from what the interview established:

| The app is… | Front door | Dashboard |
| --- | --- | --- |
| A product other people will sign up for (SaaS, marketplace, community) | Full landing page: what it is, who it's for, how it works, call to action | Yes — everything real lives behind sign-in |
| A personal tool, one user, no sign-up flow | **No marketing page.** `/` *is* the app — the list, the board, the log | Not separately; `/` is already it |
| An internal or team tool | A short signed-out screen: name, one line, sign-in button | Yes |
| A public site where content is the point (blog, directory, portfolio) | The content itself, on `/` | Only if there's an author/admin side |

A hiking journal for one person does not need a hero section and a pricing table. Building one is the single fastest way to make the result feel like a template. If the interview said "just me", skip straight to the app.

## Styling: pick a direction, then be consistent

Choose **one** visual direction that fits what the app is, and say what you picked and why in one line. A developer tool, a children's reading tracker, and an invoicing app should not look alike.

Set it in **one place** — the CSS variables shadcn wrote into `src/app/globals.css` — never by scattering one-off colours through components:

- `--primary` (and `--primary-foreground`): the app's colour. This one variable does most of the work.
- The neutral base (`--background`, `--foreground`, `--muted`, `--border`): warm neutrals read friendly and editorial; cool greys read technical; near-black reads premium.
- `--radius`: `0.3rem` is precise and serious, `0.625rem` is the default, `1rem` is soft and approachable.

Change the font if the default doesn't fit — `next/font/google` in `src/app/layout.tsx` is a one-line change and shifts the whole character more than any colour will.

Both the `:root` and `.dark` blocks exist. Whatever you change, check the app in both — a primary colour that's legible on white and invisible on near-black is a bug users will hit.

Rules that hold regardless of direction:

- Use shadcn components (`pnpm dlx shadcn@latest add ...`) rather than hand-rolling buttons and inputs. Add only what the pages actually use.
- Give the app real spacing. Cramped, full-width, edge-to-edge content is the clearest tell of a scaffold: constrain the content width and let it breathe.
- Every list needs an **empty state** — the first thing the user sees is zero rows, and "nothing here yet, add your first hike" is the difference between working and broken-looking.
- Responsive from the start. Check one narrow viewport before calling it done.

## Landing page

Write it about *their* product, from the interview. Structure that works for almost any app:

1. **Header** — name, and either Sign in / Get started or nothing at all if there are no accounts.
2. **Hero** — what it is in one sentence a stranger understands, one supporting line, one primary action. Their words from the interview, not "Welcome to MyApp".
3. **What you can do** — three or four real capabilities, named concretely ("Log a hike with photos and notes"), not adjectives ("Powerful. Fast. Simple.").
4. **Pricing** — only if payments were set up, showing the real product name and price from `references/payments.md`.
5. **Footer** — name, year, and only links that exist.

**Never fabricate credibility.** No invented testimonials, customer quotes, company logos, star ratings, user counts, "trusted by 10,000 teams", or press mentions. The app has no users yet and everyone reading the page knows it. If a section would need social proof to work, leave the section out — an honest page with three real features beats a fake one, and fake reviews are the kind of thing that gets a real product in real trouble later.

Same rule for screenshots: show the actual UI or show nothing. No stock mockups.

## Dashboard

Only when sign-in was chosen. This is what proves auth actually works end to end, so build it even if it starts small.

Put it in a route group so the protection is written once, in `src/app/(dashboard)/layout.tsx`:

```tsx
import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { auth } from "@/lib/auth";

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth.api.getSession({ headers: await headers() });
  if (!session) redirect("/sign-in");

  return (
    <div className="min-h-screen">
      {/* nav + signed-in user + sign-out */}
      <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
    </div>
  );
}
```

**Check the session on the server, in the layout or page.** Middleware is fine as an optimistic redirect to keep signed-out users from seeing a flash of the dashboard, but it is not the security boundary — a client-side or middleware-only check can be bypassed. Anything that reads or writes user data re-checks the session where it runs.

Leave room in the navigation for **Settings** — `references/settings.md` builds it next and hangs it off whatever nav you write here. It needs a place to live, not a placeholder page.

The dashboard page itself shows **their real data**, scoped to the signed-in user — the nouns from the interview, filtered by `userId`, with the primary action ("Log a hike") in reach. A page that only says "Welcome back, user@example.com" proves auth works and nothing else; go one step further and render the actual thing the app is for.

Scope every query by the session user. On a multi-user app, a query that forgets `where(eq(table.userId, session.user.id))` shows everyone each other's data — check each one.

## Verify

- Signed out, `/` renders the right front door for this app, and every visible string is about their product.
- No invented testimonials, logos, ratings, or user numbers anywhere.
- Signed out, visiting `/dashboard` redirects to sign-in.
- Signing in lands on the dashboard, which shows the signed-in user and their own data.
- Sign out returns to the signed-out state, and `/dashboard` is protected again.
- One user's data is not visible to another (create a second account and confirm).
- Empty states read as intentional, not broken.
- The app looks right in both light and dark mode, and at a narrow viewport.
