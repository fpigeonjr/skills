---
name: goal
description: Drive a single GitHub issue to completion through a human-checkpointed red-green loop — reads acceptance criteria from the issue, confirms the test plan and definition of "green" with you upfront, then runs TDD cycles until all AC are met and project checks pass, and hands back for your review before any PR is opened. Use when the user wants to work a ticket to completion, mentions "/goal", or says things like "work this ticket until it's done" or "keep going until AC pass".
argument-hint: "[issue number or goal description]"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# Goal

Single-ticket implementation loop, gated by **your approval at the start** and **your review at the end**. Drives a ticket from "branch exists" to "AC met + checks green" — you set the plan, the loop executes it and reports back.

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

### 4. Implementation loop

Repeat until all AC are met AND all checks pass. The plan is fixed by the approval gate in step 3 — the loop executes that plan, it does not silently re-scope it:

1. **Pick the next gap** — one unmet AC item or one failing check
2. **Implement** — satisfy it via a TDD red→green cycle (delegate to `tdd` skill)
3. **Re-run checks** relevant to the change
4. **Re-evaluate AC** — mark an item done only on verifiable evidence (passing test, observable behaviour). Never self-certify.
5. **Surface, don't grind** — if a gap can't be closed within the approved plan (new ambiguity, an AC that needs reinterpreting, a design choice the plan didn't cover), stop and check in rather than improvising scope.

### 5. Exit

When all AC are evidenced and all checks are green:

- Print a summary of what was built and which checks passed
- **Stop.** Do not open a PR.
- Prompt the user to run manual checks, then `submit-draft-pr` when ready.

---

> **Guards**: If the same check fails 3 times in a row, stop the loop and surface the failure for human review. If an AC item is inherently subjective or manual, flag it for human verification rather than marking it done.
