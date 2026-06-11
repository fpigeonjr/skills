---
name: init
description: Create or update AGENTS.md for the current repository by exploring the codebase and extracting high-signal guidance for future agent sessions. Use when user wants to initialise a repo for AI agents, create an AGENTS.md, improve an existing one, or says things like "/init", "set up AGENTS.md", or "bootstrap this repo for agents".
argument-hint: "[focus area or constraints]"
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
---

Create or update `AGENTS.md` for this repository.

The goal is a compact instruction file that helps future agent sessions avoid mistakes and ramp up quickly. Every line should answer: "Would an agent likely miss this without help?" If not, leave it out.

If the user passed focus or constraints after the command, honour them and scope the investigation accordingly.

## How to investigate

Read the highest-value sources first:

- `README*`, root manifests, workspace config, lockfiles
- build, test, lint, formatter, typecheck, and codegen config
- CI workflows and pre-commit / task runner config
- existing instruction files (`AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`, `.cursorrules`, `.github/copilot-instructions.md`)

If architecture is still unclear after reading config and docs, inspect a small number of representative code files to find the real entrypoints, package boundaries, and execution flow. Prefer files that explain how the system is wired together over random leaf files.

Prefer executable sources of truth over prose. If docs conflict with config or scripts, trust the executable source and only keep what you can verify.

## What to extract

Look for the highest-signal facts for an agent working in this repo:

- Exact developer commands, especially non-obvious ones
- How to run a single test, a single package, or a focused verification step
- Required command order when it matters (e.g. `lint → typecheck → test`)
- Monorepo or multi-package boundaries, ownership of major directories, real entrypoints
- Framework or toolchain quirks: generated code, migrations, codegen, build artifacts, special env loading, dev servers, infra deploy flow
- Repo-specific style or workflow conventions that differ from defaults
- Testing quirks: fixtures, integration test prerequisites, snapshot workflows, required services, flaky or expensive suites
- Important constraints from existing instruction files worth preserving

Good `AGENTS.md` content is usually hard-earned context that took reading multiple files to infer.

## Questions

Only ask the user questions if the repo cannot answer something important. Ask at most one short batch.

Good questions:
- Undocumented team conventions
- Branch / PR / release expectations
- Missing setup or test prerequisites that are known but not written down

Do not ask about anything the repo already makes clear.

## Writing rules

Include only high-signal, repo-specific guidance:

- Exact commands and shortcuts the agent would otherwise guess wrong
- Architecture notes that are not obvious from filenames
- Conventions that differ from language or framework defaults
- Setup requirements, environment quirks, and operational gotchas

Exclude:

- Generic software advice
- Long tutorials or exhaustive file trees
- Obvious language conventions
- Speculative claims or anything you could not verify

When in doubt, omit. Prefer short sections and bullets. If the repo is simple, keep the file simple.

## Create vs. improve

- If `AGENTS.md` does **not** exist: create it from scratch using the investigation above.
- If `AGENTS.md` **already exists**: improve it in place. Preserve verified useful guidance, delete fluff or stale claims, and reconcile it with the current codebase. Do not rewrite blindly.
