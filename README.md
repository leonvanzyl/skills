# Leon's Agent Skills

A collection of agent skills by [Leon van Zyl](https://github.com/leonvanzyl). Skills work with Claude Code, Cursor, Codex, OpenCode, and any other agent supported by the [`skills` CLI](https://github.com/vercel-labs/skills).

## Install

Install all skills from this repo:

```bash
npx skills add leonvanzyl/skills
```

Browse what's available first:

```bash
npx skills add leonvanzyl/skills --list
```

Install a specific skill:

```bash
npx skills add leonvanzyl/skills --skill <skill-name>
```

## Skills

| Skill | Description |
| ----- | ----------- |
| [start-an-app](skills/start-an-app) | Interview-driven app scaffolder: asks what you're building in plain language, recommends the right options (SQLite vs Postgres in Docker, sign-in, transactional email, file uploads, payments, AI features, background jobs), and builds a working Next.js app that's yours from the first commit — not a template. Every app ships with account settings and a system page for logs and debugging. |

## Adding a new skill

1. Copy [`TEMPLATE.md`](TEMPLATE.md) to `skills/<skill-name>/SKILL.md` (folder name should match the skill name: lowercase, hyphens).
2. Fill in the frontmatter (`name`, `description`) and write the instructions.
3. Commit and push — that's it. The `skills` CLI discovers everything under `skills/` automatically; no registry or manifest to update.

A skill can also ship supporting files (scripts, references, examples) alongside its `SKILL.md` in the same folder.
