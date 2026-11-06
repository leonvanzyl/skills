# Leon's Agent Skills

Skills by [Leon van Zyl](https://github.com/leonvanzyl) that take a web app from idea to production in three steps: start it, review it, deploy it. They work with Claude Code, Cursor, Codex, OpenCode, and any other agent supported by the [`skills` CLI](https://github.com/vercel-labs/skills).

## Install

One command installs every skill in this repo:

```bash
npx skills add leonvanzyl/skills
```

Or skip the terminal and paste this straight into your coding agent:

> Please install the start, review, and deploy an app skills by running `npx skills add leonvanzyl/skills`.

You can also browse first with `npx skills add leonvanzyl/skills --list`, or install a single skill with `npx skills add leonvanzyl/skills --skill <skill-name>`.

## The three steps

### 1. Start an app

Always your first step. Describe the app you want to build in plain language. The agent asks clarifying questions until it understands what you actually need, then picks a tech stack that is scalable, easy to deploy, and secure. You end up with a working Next.js app that is yours from the first commit, with sign-in, a database, a landing page, a dashboard, and the legal pages an app of its kind owes its users. The build ends by proving itself with commands that pass or fail.

> Use the start-an-app skill. I want to build...

For projects using [agent-qa](https://github.com/vostride/agent-qa), the verification step includes an [optional browser-flow reference](skills/apps/start-an-app/references/agent-qa.md). It connects natural-language tests, advanced memidex memory, and self-improvement to evidence for the flows you agreed to build. It uses an initialized project and its configured browser and model provider; live runs can change test data and incur provider costs.

### 2. Review an app

Once the app exists, have it checked. This skill reviews the whole app as it stands today and reports on three things: security against the OWASP Top 10, SEO and AI discoverability (is your sitemap, robots.txt, and llms.txt still true?), and drift, meaning anything your landing page, docs, or privacy policy claim that the app no longer does. Read-only by default, and it re-checks anything uncertain with a command instead of guessing.

> Use the review-an-app skill on this project.

### 3. Deploy an app

Takes your project and puts it live on services like Vercel. It provisions the database, file storage, and every other prerequisite automatically, sets all environment variables before the first build so there is one deploy instead of a fix-and-redeploy loop, and ends by checking the live site with real commands.

> Use the deploy-an-app skill to take this app live.

## Everything is customizable

Each skill has a `references` folder. Every component of the app and its tech stack lives there as a separate file: auth, database, email, payments, storage, and so on. Each file can be modified.

Want a different auth provider? Ask your coding agent to swap it out in `references/auth.md`. Don't want to deploy to Vercel? Open deploy-an-app's references and swap Vercel for Cloudflare Workers, Hostinger, or whatever you prefer. As long as the service has a CLI the agent can drive, you should be fine.

## Bonus: create a brand kit

Need a logo? The create-brand-kit skill runs a full brand-identity process from any starting point, even just a name. You get a logomark, wordmark, lockups, a design system, icons, social icons, favicons, app icons, and a generated guidelines page. Useful right after starting an app, before you show it to anyone.

> Use the create-brand-kit skill for my app.

## Build a game

Have a game idea? The build-a-game skill takes it from a few sentences to a finished 3D browser game, live on the web. It's the process that built LAST CALL, a 25-minute cozy horror game made entirely with Claude Code. Every model, animation and effect is written in code with Three.js, and the voices, sound and music are made ahead of time with ElevenLabs (or for free, with sound made in code and subtitles instead of voices).

There are 10 steps, and the agent checks in with you after each one. It locks the story, builds a tool that lets it see and measure every frame, and shows you three art styles to pick from. Then it casts the voices, makes a talking-character demo, and builds a playable five-minute slice with a small team of reviewer agents. You play the slice before it builds the rest, then it polishes the game and deploys it to the host you choose (Hostinger, Vercel, itch.io or any static host). You make the creative calls. Anything that costs money waits for your yes, and progress is saved in `docs/HANDOFF.md`, so a new session picks up where the last one stopped.

> Use the build-a-game skill. I have a game idea...
