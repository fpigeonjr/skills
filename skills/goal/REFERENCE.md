# Goal — Reference

## Full loop specification

```
resolve_ac()
  → upfront_approval()        ← interactive, once
    → implementation_loop()
        while not (all_ac_met AND all_checks_green):
            gap = pick_next_gap(unmet_ac, failing_checks)
            tdd_cycle(gap)           ← follow explicitly loaded tdd instructions
            run_relevant_checks()
            re_evaluate_ac()         ← evidence only, never self-certify
            if same_check_failed >= 3:
                stop_loop → surface to human
        → exit_summary() → hand back to user
```

## AC resolution precedence

| Source | How |
|---|---|
| Explicit tracked issue URL/number + host/repo | Fetch with explicit `GH_HOST` and `--repo`, verify canonical URL and compare supplied AC with the fetched `## Acceptance criteria`; stop on drift or fetch failure |
| Branch name `gh-<N>-<slug>` | Resolve the intended repo/host, fetch the issue, verify URL → parse `## Acceptance criteria`; stop on ambiguity |
| Inline goal text | Use only if no tracked issue was requested; never substitute for failed issue resolution |
| Ask | If no inline goal, tracked issue or branch number |

## Check command detection precedence

| Priority | Source | What to look for |
|---|---|---|
| 1 | `AGENTS.md` | "Developer commands" / test / lint / build sections |
| 2 | `package.json` | `scripts`: `lint`, `test`, `typecheck`, `build`, `check`, `precommit` |
| 3 | `.pre-commit-config.yaml` | `repos[].hooks` entries |
| 4 | `husky` / `lefthook` | `.husky/pre-commit`, `lefthook.yml` |
| 5 | Ask | If nothing found |

## Implementation preflight

After plan approval, before implementation in each working checkout, verify required dependencies and run the agreed focused baseline using project-discovered commands. Install dependencies only through the project's approved setup; do not bypass dependency constraints or change configuration to make setup pass. Missing tools or unavailable required verification mean **blocked**: report the setup failure and preserve any partial work, rather than hand back an unverified implementation as complete. Record pre-existing baseline failures and seek direction before proceeding; do not mislabel them as a TDD RED. Full repository checks remain at the existing final gate, not before every edit.

## TDD delegation

The `tdd` skill owns the red-green-refactor mechanics. `/goal` owns the outer loop. Load `tdd` via the harness's skill loader, or discover and read its `SKILL.md` and needed sibling references before planning; do not rely on naming the skill to load it.

- `/goal` does TDD's **planning step once upfront** (interface design, behaviour list, user approval).
- After approval, `/goal` feeds each gap to the TDD **tracer bullet + incremental loop**, executing the approved plan and checking in when a gap falls outside it.
- `/goal` enforces: tests use public interfaces only, mock only at system boundaries, never refactor while RED.

## Guard conditions

| Condition | Action |
|---|---|
| Same check fails 3× in a row | Stop loop, report the failure, ask human how to proceed |
| AC item is subjective / manual (e.g. "looks correct in UI") | Flag for human verification, do not auto-check |
| No verifiable signal for an AC item | Stop and ask rather than self-certify |

## Exit checklist

Before handing back, confirm:
- [ ] Every AC item is checked off with an evidence reference (test name, command output)
- [ ] All detected check commands exit 0
- [ ] Flagged subjective AC items are listed for human review
- [ ] No uncommitted changes left dangling

## Composition

```
branch setup       ← repository-approved worktree + branch
    ↓
/goal              ← THIS SKILL: implement + verify loop
    ↓
(manual review)    ← human runs checks, inspects diff
    ↓
submit-draft-pr    ← opens draft PR
    ↓
release-pr         ← promotes to ready after CI passes
```

## Inspiration

Concept inspired by Claude Code's `/goal` and the AFK (fully automated) ticket type introduced in [mattpocock/skills](https://github.com/mattpocock/skills). This implementation is scoped to Pi and OpenCode harnesses as a plain-Markdown skill — no sub-agent spawning or parallel orchestration.
