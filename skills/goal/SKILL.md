---
name: goal
description: Drive a single GitHub ticket to completion using an autonomous red-green loop — reads acceptance criteria from the issue, runs TDD cycles until all AC are met and project checks pass, then hands back for manual review before the PR is opened. Use when the user wants to iterate on a ticket until done, mentions "/goal", wants to grind a ticket autonomously, or says things like "work this ticket until it's done" or "keep going until AC pass".
argument-hint: "[issue number or goal description]"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# Goal

Autonomous single-ticket implementation loop. Drives a ticket from "branch exists" to "AC met + checks green", then stops for your manual review.

Designed to run **after** `start-ticket` and **before** `submit-draft-pr`.

See [REFERENCE.md](REFERENCE.md) for the full loop spec and guard details.

## Workflow

### 1. Resolve acceptance criteria

- Parse the current branch name (`gh-<number>-<slug>`) to extract the issue number.
- Fetch the issue and read the `## Acceptance criteria` checklist.
- If no issue is resolvable, use the inline argument as the goal; if none provided, ask.

### 2. Detect check commands (upfront, once)

Discover the project's verification commands in this order:
1. **AGENTS.md** — read "Developer commands", build, test, lint sections
2. **`package.json` scripts** — `lint`, `test`, `typecheck`, `build`, `check`, `precommit`
3. **`.pre-commit-config.yaml`** / husky / lefthook hook configs
4. **Ask** if nothing discoverable

### 3. Upfront approval gate (interactive — one time only)

Present to the user:
- The resolved AC checklist
- The test plan derived from the AC (following the `tdd` skill's planning step)
- The discovered check commands that define "green"

**Wait for approval or edits before proceeding.** Do not begin implementation until the user confirms.

### 4. Autonomous loop

Repeat until all AC are met AND all checks pass:

1. **Pick the next gap** — one unmet AC item or one failing check
2. **Implement** — satisfy it via a TDD red→green cycle (delegate to `tdd` skill)
3. **Re-run checks** relevant to the change
4. **Re-evaluate AC** — mark an item done only on verifiable evidence (passing test, observable behaviour). Never self-certify.

### 5. Exit

When all AC are evidenced and all checks are green:

- Print a summary of what was built and which checks passed
- **Stop.** Do not open a PR.
- Prompt the user to run manual checks, then `submit-draft-pr` when ready.

---

> **Guards**: If the same check fails 3 times in a row, stop the loop and surface the failure for human review. If an AC item is inherently subjective or manual, flag it for human verification rather than marking it done.
