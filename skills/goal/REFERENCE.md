# Goal — Reference

## Full loop specification

```
resolve_ac()
  → upfront_approval()        ← interactive, once
    → autonomous_loop()
        while not (all_ac_met AND all_checks_green):
            gap = pick_next_gap(unmet_ac, failing_checks)
            tdd_cycle(gap)           ← delegate to tdd skill
            run_relevant_checks()
            re_evaluate_ac()         ← evidence only, never self-certify
            if same_check_failed >= 3:
                stop_loop → surface to human
        → exit_summary() → hand back to user
```

## AC resolution precedence

| Source | How |
|---|---|
| Branch name `gh-<N>-<slug>` | `gh issue view <N> --json body` → parse `## Acceptance criteria` |
| Inline argument | Use as-is if no issue number resolvable |
| Ask | If no argument and no branch number |

## Check command detection precedence

| Priority | Source | What to look for |
|---|---|---|
| 1 | `AGENTS.md` | "Developer commands" / test / lint / build sections |
| 2 | `package.json` | `scripts`: `lint`, `test`, `typecheck`, `build`, `check`, `precommit` |
| 3 | `.pre-commit-config.yaml` | `repos[].hooks` entries |
| 4 | `husky` / `lefthook` | `.husky/pre-commit`, `lefthook.yml` |
| 5 | Ask | If nothing found |

## TDD delegation

The `tdd` skill owns the red-green-refactor mechanics. `/goal` owns the outer loop.

- `/goal` does TDD's **planning step once upfront** (interface design, behaviour list, user approval).
- After approval, `/goal` feeds each gap to the TDD **tracer bullet + incremental loop** autonomously.
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
start-ticket       ← creates worktree + branch
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
