# AGENTS.md

## What this repo is

A collection of plain-Markdown agent skills for OpenCode and Pi. No build system, no tests, no CI — editing `.md` files IS the workflow.

## Repo structure

```
skills/
└── skills/
    ├── <skill-name>/SKILL.md        # required entry point for every skill
    └── <skill-name>/                # optional reference files alongside SKILL.md
```

No `package.json`, no manifests, no lockfiles, no tooling of any kind.

## Developer commands

None. All work is editing Markdown files.

## Skill file format

Every skill directory must contain a `SKILL.md` with YAML frontmatter:

```yaml
---
name: skill-name
description: What it does. Use when <specific triggers>.
argument-hint: "[optional]"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---
```

- **Description** is the only field an agent reads when selecting a skill — max 1024 chars, third person, triggers must be explicit.
- **`SKILL.md` should stay under 100 lines.** Split large content into sibling reference files (e.g., `REFERENCE.md`, `EXAMPLES.md`).
- References must be **at most one level deep** from `SKILL.md`.
- No time-sensitive content in skill files.
- `disable-model-invocation: true` frontmatter field is valid (used by `zoom-out`); it means the skill body is a direct instruction, not a workflow.

## Installing skills

**OpenCode** — `~/.config/opencode/opencode.json`:
```json
{ "skills": { "paths": ["~/Code/skills/skills"] } }
```

**Pi** — `~/.config/pi/agent/settings.json`:
```json
{ "skills": ["~/Code/skills/skills"] }
```

## Key non-obvious conventions

**TDD skill** (`skills/tdd/`): tests use public interfaces only — never test internals, never query the DB directly to verify state, mock only at system boundaries (external APIs, DB, time/randomness). Vertical slices: one test → one implementation → repeat. Never refactor while RED.

**grill-with-docs skill** (`skills/grill-with-docs/`): `CONTEXT.md` is a glossary only — no specs, no implementation notes. ADRs live in `docs/adr/` with sequential numbering (`0001-slug.md`), created lazily on first use. Create an ADR only when the decision is hard-to-reverse, surprising without context, and the result of a real trade-off.

**submit-draft-pr skill**: After creating the PR, always print a manual action note — Copilot reviews cannot be requested via the API.

**to-prd skill**: Requires `docs/agents/issue-tracker.md` to exist in the target project before publishing.

**to-issues skill**: Issues are typed as HITL (human-in-the-loop) or AFK (fully automated). Publish in dependency order so real issue IDs can be referenced in "Blocked by" fields.

## Credits

`tdd`, `grill-me`, `grill-with-docs`, `zoom-out`, `handoff`, `to-issues`, `to-prd`, and `write-a-skill` are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT). Skills conform to the [Agent Skills standard](https://agentskills.io/specification).
