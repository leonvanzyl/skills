# Base project

Last verified: 2026-07-21

**Purpose:** Create the Next.js project that everything else builds on: TypeScript, Tailwind, App Router, shadcn/ui components.

## Install

**The app is created in the current working directory, never in a subfolder.** The user is already standing in the folder they want the app to live in, so `package.json`, `src/`, and `next.config.ts` belong at its top level. Passing `.` as the project name does this — and there is no `cd` afterwards.

**Use pnpm if available, otherwise npm** — and if it's npm, drop `--use-pnpm` from the commands below and read every later `pnpm x` in this skill as `npm run x` (`pnpm dlx` becomes `npx`). The commands are written for pnpm because it's the recommended path; they are not a requirement, and a Verify step that checks `pnpm dev` on an npm project is checking the wrong thing.

**Check the folder name first.** `.` makes `create-next-app` derive the package name from the folder, and npm rejects names with **capital letters**, spaces, or a leading dot — so in `H:\GroomRoom` or `~/MyApp` the command fails outright with *"name can no longer contain capital letters"* before anything is created. Folders named after the app are exactly the common case, so check rather than discover.

If the folder name is already lowercase and npm-legal:

```bash
npx create-next-app@latest . --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --turbopack --use-pnpm
```

Otherwise scaffold into a lowercase temporary directory and move the result up — the folder keeps its name, the package gets a legal one:

```bash
npx create-next-app@latest scaffold-tmp --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --turbopack --use-pnpm
shopt -s dotglob && mv scaffold-tmp/* . && rmdir scaffold-tmp
```

(The temp directory must be `scaffold-tmp`, not `.scaffold-tmp` — npm rejects a leading dot too, so the dotted version fails the same way.)

If a prompt still appears for an option not covered by flags, accept the default.

Then set the package name either way, because the derived one is the folder, which is rarely the app's name:

```bash
npm pkg set name=my-app   # kebab-case version of the user's app name
```

**pnpm under an agent needs `CI=true`.** With no TTY, `pnpm install` aborts with `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY` rather than prompting, and `pnpm add` can silently do nothing. Prefix pnpm commands with `CI=true` for the whole build, and don't debug the package that "didn't install" — check for that error first.

**If the command refuses because the directory isn't empty, check what's in it first.**

If the folder already holds a project — a `package.json`, a `src/`, a `.git` with commits — **stop.** Do not scaffold over it, and do not work around it. Name the folder, say what you found, and ask the user to open an empty folder and start again. Merging a fresh Next.js app into someone's existing repo is the one mistake in this skill that can't be undone.

If it refused over **stray files** — a `README.md`, notes, a `.gitignore`, nothing that constitutes a project — carry on. Do *not* fall back to a subfolder; use the same `scaffold-tmp` route as above:

```bash
npx create-next-app@latest scaffold-tmp --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --turbopack --use-pnpm
```

**Look before you move.** `mv` silently overwrites, so decide about collisions while both files still exist — not afterwards, when the user's version is already gone:

```bash
shopt -s dotglob
for f in scaffold-tmp/*; do [ -e "./$(basename "$f")" ] && echo "COLLIDES: $(basename "$f")"; done
```

Move the non-colliding files, then handle each collision deliberately: keep the user's file where it has content worth keeping (their `README.md`), take the scaffold's otherwise, and merge `.gitignore` by hand if both exist. Only then:

```bash
rmdir scaffold-tmp
```

Initialize shadcn/ui with defaults:

```bash
pnpm dlx shadcn@latest init -d
```

Add components on demand as pages need them (start small):

```bash
pnpm dlx shadcn@latest add button card input label
```

## Configure

Project layout to follow for everything added later — all paths are relative to the current working directory, which *is* the project root:

```
src/
├── app/           # routes: page.tsx, layout.tsx, api/
├── components/    # shared React components (shadcn/ui lands in components/ui)
└── lib/           # db, auth, utilities
```

Create `.env` at the project root now (empty is fine) and confirm `.env*` is in `.gitignore` — later steps append to it.

## Verify

- `package.json` sits in the current working directory — there is no nested project folder.
- `pnpm dev` starts without errors and http://localhost:3000 renders.
- A shadcn `Button` imported into `src/app/page.tsx` renders styled.
