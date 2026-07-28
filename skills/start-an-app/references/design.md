# Design system (DESIGN.md)

Last verified: 2026-07-27

**Purpose:** Decide what the app looks like *once*, write it down as `DESIGN.md` at the project root, and have every page built afterwards obey it. Optional — but when the user has an existing site, a brand, or a look in mind, this is what stops the result reading as "shadcn defaults with their words in it".

Format and anti-pattern rules are adapted from [taste-skill](https://github.com/Leonxlnx/taste-skill) (MIT, © Leonxlnx) — specifically its `stitch-skill` `DESIGN.md` export shape and the three dials. This file stands alone; taste-skill does not need to be installed. Pairing them is covered at the bottom.

## When this runs

Only if question 7 in the interview got an answer. Three ways in, strongest first:

| The user said | Do this |
| --- | --- |
| "Here's a site — make it look like that" (theirs, a competitor's, or one they admire) | **Extract** — the protocol below |
| "Make it feel like Linear / warm and friendly / expensive and quiet" — a vibe, no URL | Skip extraction. Write `DESIGN.md` from the vibe plus the design read |
| Nothing, or "you decide" | Write a short `DESIGN.md` from the interview alone — what the app *is* picks the direction |

Never make this a hurdle. One question, and silence is a valid answer.

## Extracting from a URL

**Load the page properly.** Use a real browser (Playwright, or whatever browsing tool is available) — a raw HTML fetch misses everything, because the values that matter are computed, not written in the markup. If no browser tool exists, say so and fall back to the vibe path rather than guessing from HTML.

Look at **two pages**: the home page and one interior page (pricing, a blog post, a product). The home page shows the brand at full volume; the interior page shows what the system actually does at rest, which is closer to what this app needs.

Run this on each and keep the output:

```js
(() => {
  const tally = (xs) =>
    Object.entries(xs.reduce((a, x) => (x && (a[x] = (a[x] || 0) + 1), a), {}))
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6);
  const nodes = [...document.querySelectorAll("body *")].slice(0, 4000);
  const s = (el) => getComputedStyle(el);
  const opaque = (c) => c && c !== "rgba(0, 0, 0, 0)";
  return {
    background: tally(nodes.map((el) => s(el).backgroundColor).filter(opaque)),
    text: tally(nodes.map((el) => s(el).color)),
    accent: tally(
      [...document.querySelectorAll("a,button,[role=button]")]
        .map((el) => s(el).backgroundColor)
        .filter(opaque)
    ),
    fontFamily: tally(nodes.map((el) => s(el).fontFamily)),
    fontWeight: tally(nodes.map((el) => s(el).fontWeight)),
    radius: tally(nodes.map((el) => s(el).borderRadius).filter((r) => r !== "0px")),
    shadow: tally(nodes.map((el) => s(el).boxShadow).filter((v) => v !== "none")),
    container: tally(nodes.map((el) => s(el).maxWidth).filter((w) => w !== "none")),
    headings: [...document.querySelectorAll("h1,h2")].slice(0, 4).map((el) => ({
      tag: el.tagName,
      size: s(el).fontSize,
      weight: s(el).fontWeight,
      tracking: s(el).letterSpacing,
      leading: s(el).lineHeight,
    })),
  };
})();
```

**The values come back as `lab()` and `oklab()` on any current site**, not `rgb()` — Tailwind v4 and most modern CSS emit them, and `getComputedStyle` hands them back unconverted. Do not regex the numbers out of them: `lab(94.2 0.69 2.96)` read as RGB gives a dark red where the real colour is near-white, and the whole palette comes out wrong while looking entirely plausible. Convert through a canvas, which does the colour maths for you:

```js
const c = document.createElement("canvas"); c.width = c.height = 1;
const ctx = c.getContext("2d", { willReadFrequently: true });
const hex = (css) => {
  ctx.clearRect(0, 0, 1, 1); ctx.fillStyle = "#000"; ctx.fillStyle = css;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
  return "#" + [r, g, b].map((v) => v.toString(16).padStart(2, "0")).join("") +
    (a < 255 ? ` (a=${(a / 255).toFixed(2)})` : "");
};
```

Then **take a screenshot of each page** and read what the numbers can't tell you: how much air the layout has, whether sections are symmetric or offset, whether it feels warm or clinical, how loud the type is against everything else. Check whether the site has a dark mode (toggle `prefers-color-scheme`) — if it does, capture both.

Numbers give you the palette and the type. The screenshot gives you the density and variance dials. You need both.

### What to take, and what to leave

**Take:** colour roles, font families and weights, corner radius, shadow depth, container width, spacing rhythm, density, layout temperament.

**Leave:** the logo, the images, the copy, the icon set, and the CSS itself. Never copy a stylesheet, and never rebuild a page section-for-section.

Three rules that are not negotiable:

- **If it isn't the user's own site, it is reference, not a target.** Match the *feel*; do not reproduce the layout, wording, or identity. A site's look-and-feel is part of how its owner is recognised, and cloning it is a problem for the user later, not for you. Say this once, plainly, and move on — it isn't a lecture, it's the reason the output will be better anyway.
- **Fonts have licences.** If the site uses a Google font or a system stack, use it. If it uses a commercial webfont, do not lift the font files or hotlink them — pick the closest open alternative, and record both the original and the substitute in `DESIGN.md` so the user can buy a licence later if they want the real thing.
- **Record where it came from.** The provenance section at the bottom of `DESIGN.md` is not optional.

### Extracted values are a starting point, not a verdict

A tally counts pixels, not intent. Three things to fix by hand every time:

- The most-used background is usually white and tells you nothing — the *second* one is the surface colour that matters.
- The most-used "accent" is often a link colour on a grey button. Pick the colour the site uses for its primary action, by eye, from the screenshot.
- Sites carry drift — an old section with an old blue in it. Take the coherent system, not the archaeology.

## Writing DESIGN.md

Write it to the project root. Keep it short enough that it gets read: one page, concrete values, no prose about brand philosophy.

```md
# DESIGN.md — <App name>

Source: <URL, or "no reference — direction chosen from the brief">
Written: <date>

**Design read:** <one line — "a hiking journal for one person, with a warm editorial
language, leaning toward generous whitespace and a single earthy accent">

**Dials:** VARIANCE <1-10> · MOTION <1-10> · DENSITY <1-10>
<one line on why — high variance suits a marketing page, low suits a data tool>

## 1. Tokens
The values below go straight into `src/app/globals.css`. Nothing in this app sets a
colour anywhere else.

| Token | Light | Dark | Role |
| --- | --- | --- | --- |
| `--background` | | | page surface |
| `--foreground` | | | primary text |
| `--card` | | | raised surface |
| `--muted` / `--muted-foreground` | | | secondary text, quiet fills |
| `--border` | | | 1px structure |
| `--primary` / `--primary-foreground` | | | the app's colour — primary actions only |
| `--destructive` | | | delete, danger |
| `--radius` | | | corner radius |

## 2. Typography
- **Display:** <family, weights, tracking, leading, clamp() scale>
- **Body:** <family, weight, leading, max measure>
- **Loaded via:** `next/font/google` in `src/app/layout.tsx`
- **Substituted:** <original commercial font → open replacement, or "none">

## 3. Elevation & shape
Radius, border treatment, shadow (or the deliberate absence of one), and when a card
is used at all.

## 4. Layout & density
Container width, section rhythm, whether feature rows are symmetric or offset, how
much air sits between things.

## 5. Motion
What moves, how far, how fast, and what stays still. Animate `transform` and
`opacity` only. If the answer is "almost nothing", write that — it is a valid system
and a better one than most.

## 6. Components
Anything that differs from a shadcn default: button shape and weight, input style,
nav treatment, empty-state tone, loading treatment.

## 7. Banned in this project
The list below is enforced on every page. Extend it with anything specific to this
brand.

## 8. Provenance
Where each of the above came from, what was substituted and why, and an explicit note
that no assets, copy, or CSS were copied from the source.
```

### The default banned list

Carry these into section 7 unless the brand contradicts one. They are the difference between "designed" and "generated":

- No purple-to-blue neon gradient — the default AI look.
- No pure `#000000` or pure `#FFF` text on saturated fills; use a near-black and check contrast.
- No three equal feature cards in a row. Offset the grid or use two columns.
- No fabricated proof: testimonials, logos, star ratings, user counts. (`references/pages.md` already forbids this; it belongs here too.)
- No filler chrome: "Scroll to explore", bouncing chevrons, "Discover more below".
- No AI copy clichés: "Elevate", "Seamless", "Unleash", "Next-Gen", "Revolutionize".
- No emoji as UI iconography.
- No `h-screen` — `min-h-[100dvh]`, or iOS Safari's address bar clips it.
- No untouched shadcn defaults: if `--radius`, `--primary` and the font are all still stock, no design decision was made.
- No round fake numbers in sample data (`99.99%`, `10,000 users`).

### When the brand and the rules disagree

**Brand facts win on identity; these rules win on craft.** If the user's own site uses a font one of these lists would ban, keep the font — it is their brand, and fidelity beats taste here. If their site centres every hero and uses three equal cards, that is *layout*, not identity: build it better and say why in one line.

The test: would changing it make the app stop looking like *them*? Then keep it. Otherwise improve it.

## Making the rest of the skill obey it

Writing `DESIGN.md` and then ignoring it is worse than not writing it. Concretely:

1. **Immediately after writing it,** apply section 1 to `src/app/globals.css` (both `:root` and `.dark`) and section 2 to `src/app/layout.tsx`. Do this before any page exists, so every component inherits it for free.
2. `references/pages.md` builds the front door and dashboard **from this file** — it defers to `DESIGN.md` wherever the two overlap.
3. Every shadcn component added later gets checked against sections 3 and 6, and customised once, in `src/components/ui`, rather than per-page.
4. At hand-off, tell the user `DESIGN.md` exists and that changing a colour there and re-applying section 1 restyles the whole app.

## Pairing with taste-skill (optional)

[taste-skill](https://github.com/Leonxlnx/taste-skill) is a separate, more opinionated frontend skill. It goes deeper on layout variance, motion choreography and anti-slop enforcement than this file does, and it is worth installing when the app's front door is doing real marketing work:

```bash
npx skills add https://github.com/Leonxlnx/taste-skill --skill "design-taste-frontend"
```

If it's installed, the division of labour is: **`DESIGN.md` owns the facts** (this app's palette, type, tokens, brand constraints), **taste-skill owns the craft** (how a hero is composed, how motion is orchestrated, what reads as templated). Feed it the `DESIGN.md` rather than letting it invent a palette, and set its three dials from the ones recorded at the top of the file.

## Verify

- `DESIGN.md` exists at the project root, and every token table cell has a real value — no blanks, no placeholders.
- `src/app/globals.css` matches section 1 in **both** `:root` and `.dark`, and the app is legible in both.
- The font in section 2 is actually loaded in `layout.tsx` — not just named in the doc.
- No component sets a colour outside the tokens. Grep for hex codes in `src/` and expect none.
- If a URL was used: `DESIGN.md` names it, records any font substitution, and no logo, image, copy or CSS from it exists in the project.
- Someone reading `DESIGN.md` and someone looking at the app would describe them the same way.
