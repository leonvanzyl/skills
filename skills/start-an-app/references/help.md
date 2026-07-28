# In-app help guide

Last verified: 2026-07-27

**Purpose:** A `?` in the navbar opens a guide that explains the app in the owner's own words. Built for the people who will use the app but never sat in this interview — the receptionist hired next spring, the volunteer who took over the roster, the customer who signed up at 11pm.

## When to build it

**Decided, not asked.** Question 1 of Step 1c already tells you:

| Question 1 answered | Build the guide? |
| --- | --- |
| Their customers | **Yes** |
| Their staff | **Yes** — this is where it matters most |
| Just them | No. They just spent twenty minutes explaining the app to you; they don't need it explained back |

Put it on the build sheet as a line they can decline, not as a question:

> **Built-in help:** a `?` in the corner opens a short guide, written from what you've just told me — so new staff can work it out without asking you.

## The content is already in the interview

This is the part no bolt-on help widget can do, and the reason this belongs in the skill rather than in a component library. Step 1a produced a description of the app in the owner's words, its **nouns**, its **verbs**, and a walkthrough of someone's first visit. That's a user guide with the labels changed.

Map it directly:

| From the interview | Becomes |
| --- | --- |
| "Walk me through it — someone opens it for the first time" | **Getting started** — the first chapter, always |
| Each **verb** ("log a hike", "invoice a client", "book a slot") | One chapter each |
| The **nouns** and how they relate | **How it's organised** — only if there's more than one, and only if the relationship isn't obvious |
| The ownership answer from Step 1b | **Who sees what** — essential the moment staff and customers share the app |
| Sign-in, if chosen | **Your account** — signing in, signing out, forgotten passwords |

Four to seven chapters. A guide nobody finishes is a guide nobody reads.

**Write it in their words, not the interface's.** *"Log a hike when you get back, and add the photos then — you can edit it later if you forget something"* teaches the workflow. *"Click the Submit button to submit the form"* teaches nothing and reads as filler. If a sentence would be true of any app, delete it.

## Chapters

Plain typed data — no MDX pipeline in a scaffold.

`src/content/help/chapters.ts`:

```ts
export type HelpChapter = {
  id: string;           // stable, url-safe: used for deep links
  title: string;
  intro: string;        // one or two sentences
  steps?: string[];     // numbered, only where order matters
  notes?: string[];     // the "you can also…" and the gotchas
};

export const helpChapters: HelpChapter[] = [
  {
    id: "getting-started",
    title: "Getting started",
    intro: "…",
  },
];
```

Deep-link with `?help=<id>` so the app can point at a chapter from an empty state — *"nothing here yet. [How logging a hike works]"* is worth more than any tooltip.

## The window

Build on shadcn's `Dialog`. **Do not hand-roll the modal** — whichever primitive shadcn generates for the project (currently Base UI; older projects have Radix) gives you the focus trap, Esc, `aria-modal` and scroll locking for free, and losing those is invisible until a keyboard or screen-reader user hits it. Add dragging and resizing to the content wrapper; keep the primitive underneath.

```tsx
// src/components/help/help-dialog.tsx  (shape, not gospel — adapt to the project)
const MIN = { w: 380, h: 320 };

function clampToViewport(box: Box): Box {
  const w = Math.min(Math.max(box.w, MIN.w), window.innerWidth);
  const h = Math.min(Math.max(box.h, MIN.h), window.innerHeight);
  return {
    w, h,
    x: Math.min(Math.max(box.x, 0), window.innerWidth - w),
    y: Math.min(Math.max(box.y, 0), window.innerHeight - h),
  };
}

function defaultBox(): Box {
  const w = window.innerWidth * 0.8;
  const h = window.innerHeight * 0.8;
  return { w, h, x: (window.innerWidth - w) / 2, y: (window.innerHeight - h) / 2 };
}
```

**Two things in shadcn's `DialogContent` will silently break the window**, and both cost an hour if you meet them by surprise:

- It centres itself with `-translate-x-1/2 -translate-y-1/2`, which in **Tailwind v4 compiles to the `translate` property, not `transform`.** Setting `transform: "none"` inline therefore does nothing and the window opens half its own size off the top-left corner. Set **`translate: "none"`** as well.
- Its open animation (`zoom-in-95`) leaves a **permanent `scale(0.95)`** on the element. The painted box and the layout box then disagree by 5%, so every drag and resize drifts. Kill it with `!animate-none` on the desktop variant — which also suits a system whose motion dial is near zero.

Both are invisible until measured: the window looks roughly right and behaves subtly wrong. Check `getBoundingClientRect()` against the intended box rather than trusting your eyes.

- **80% of the viewport is the starting size, not a fixed one.** `defaultBox()` on first open; after that, whatever the user left it as.
- **Persist position and size** to `localStorage` under one key, and **clamp on every open**. A box saved on a 32-inch monitor must not open off-screen on a laptop the next morning — this is the bug that makes people stop using the feature, and it only shows up on the second device.
- **Drag from the header only**, with `pointerdown` → `setPointerCapture` → `pointermove`. Capturing the pointer is what stops the drag dying when the cursor outruns the header.
- **Resize from the bottom-right corner**, same pointer-capture pattern, floored at `MIN`.
- **Set `touch-action: none` on the drag and resize handles only.** On the whole dialog it kills scrolling inside the guide.
- Offer a **Reset size** item so a user who has dragged it somewhere useless can recover without clearing storage.

## On a phone, none of the above

Below `md`, render a full-screen sheet with no drag and no resize. Touch-dragging a window fights the scroll gesture and the scroll gesture should win. A `?` that opens a small draggable panel on a 390px screen is worse than no help at all.

## Keyboard and screen readers

- `?` opens the guide from anywhere except while typing in an input or textarea.
- Esc closes it; focus returns to the `?` button that opened it.
- The chapter list is a real list of buttons, arrow-navigable, with the current chapter marked `aria-current`.
- **Nothing may require dragging.** Drag and resize are conveniences; every chapter must be reachable and readable in the default box.

## Keeping it true

A guide that describes the app as it was on day one is worse than none, because it is confidently wrong.

- **Step 4 is not done until every verb from Step 1a appears in a chapter.** That is the check that stops this shipping as a stub with "Getting started" and nothing else.
- Say at hand-off, in one line, that `src/content/help/chapters.ts` is a plain text file they can edit themselves — for many owners this is the first part of their own app they'll change, and it's a good first thing to change.
- When a feature is added later, the guide is part of that feature, not a follow-up task.

## Verify

- `?` in the navbar opens the guide; Esc closes it; focus lands back on the `?` button.
- Every verb from the interview has a chapter, and every chapter is in the owner's language — no "click the button to submit the form".
- Move and resize the window, close it, reopen it: it comes back where it was left.
- Measure it: `getBoundingClientRect()` matches the intended box and `transform` computes to `none`. A window that looks fine but reports 95% of its size will drift on every drag.
- Save a large box, then narrow the browser to a laptop width and reopen: the guide is fully on screen.
- At 390px wide it is a full-screen sheet, scrolls normally, and has no drag handles.
- An empty state somewhere links into a chapter with `?help=<id>` and opens on that chapter.
