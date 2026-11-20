---
name: cleanup-machine
description: Runs a periodic, report-first sweep of a developer machine for stale worktrees, merged or abandoned local branches, oversized tool caches, agent session logs, and idle container resources, then removes only exactly approved targets. Use when the user explicitly invokes /skill:cleanup-machine for a weekly cleanup, machine hygiene check, or disk-usage review across repositories and tools.
argument-hint: "[report | category | root path]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
---

# Cleanup machine

Run only on explicit invocation. This is the cross-session counterpart to `cleanup-session`: it finds what has accumulated across many sessions and repositories, not what one session created. Cleanup is destructive: **inventory first, propose exact actions, obtain approval, then revalidate each target immediately before acting.** Read [REFERENCE.md](REFERENCE.md) for the sweep categories, staleness signals, and report format.

## Quick start

- `/skill:cleanup-machine`: run the full sweep, then propose numbered rows for approval.
- `/skill:cleanup-machine report`: inventory and report only; change nothing.
- `/skill:cleanup-machine worktrees` or `/skill:cleanup-machine ~/Code/some-repo`: limit the run to one category or root.

Approve by row, e.g. "approve 1–4, 7". Rows not named stay untouched.

## Workflow

1. **Load the machine profile.** Read the local, uncommitted profile at `${XDG_CONFIG_HOME:-$HOME/.config}/cleanup-machine/profile.md` if present. It may define roots to scan, worktree locations, staleness thresholds, protected paths, private-repository rules, and where to record snapshots. Profile values override the defaults in REFERENCE.md. Treat the profile as local configuration: never copy its contents, private repository names, hostnames, or paths into commits, issues, PRs, or other shared output. If it is absent, use the defaults and say so. If an argument is given, limit the run to that category or root.

2. **Report machine state.** Record date, local timezone, free and used space on the data volume, and which managers are available (`git`, `wt`, Homebrew, npm, a container runtime, agent harnesses). A missing or stopped manager makes its category **unknown**, not empty. Never start a daemon or VM just to inventory it without asking.

3. **Inventory without mutation.** Sweep each in-scope category in REFERENCE.md with read-only commands. Measure sizes, collect staleness evidence, and stop each category at its listed cap. Do not read file contents beyond metadata needed for attribution, and never inspect credential stores, auth files, or browser profiles. Treat command failures, timeouts, permission errors, and uninspected items as **unknown**, never clean.

4. **Classify every candidate.** Use the same categories as `cleanup-session`: **safe to remove**, **needs preservation or publication**, **blocked/unknown**, or **keep**. Staleness alone never makes something safe. A worktree is removable only when it is clean and its commits are reachable from a durable ref (merged, or pushed to a branch that still exists). Being ignored or looking generated is not proof of reproducibility. A shared cache is safe to trim only through its owning tool's command. Principal checkouts, the current working directory, active sessions, and profile-protected paths are always **keep**.

5. **Report, ranked by reclaimable space.** Use the report format in REFERENCE.md: a summary, then one table per category with the target, size, staleness evidence, classification, and proposed command. Compare with the previous snapshot when one exists. With `report` as the argument, stop here.

6. **Obtain explicit approval.** Ask the user to select exact targets by row. Approval covers only listed targets and stated consequences. Require separate approval before: deleting any branch, removing a worktree with ignored files, trimming a shared cache, deleting agent session logs, deleting container images or volumes, or stopping any process. Never push, delete remote branches, close PRs, empty the Trash, run `git clean`, `docker system prune`, `brew autoremove`, or remove a whole cache directory with `rm -rf` unless the user requested that exact action after seeing its targets.

7. **Revalidate and execute narrowly.** Immediately before each approved action, re-check clean state, reachability, holders (open shells, agent panes, running processes in the path), and size. If anything changed, skip that action and report it. Prefer owning managers over raw deletion, using the exact safe forms in REFERENCE.md: for example `wt remove --no-delete-branch --no-hooks --foreground`, so removing a worktree never also deletes a branch or runs hooks. Never use force flags by default.

8. **Verify, record, and report.** Re-measure the affected categories and free space. Report reclaimed space, completed actions, skipped or failed actions, and the remaining blockers. Write a snapshot of sizes and counts only (no file names from private repositories) to the profile's snapshot location, or `${XDG_STATE_HOME:-$HOME/.local/state}/cleanup-machine/snapshots.md` by default. Do not commit anything.

## Hard stops

Stop rather than infer when a candidate has uncommitted or untracked changes, stash entries, initialized submodules, a lock, unique or unpushed commits, an active holder or dependent, disagreement between managers, possible persisted data, uncertain ownership, or a failed inspection. Never sweep outside the configured roots, never touch system directories or other users' files, and never treat a weekly cadence as standing approval: every run needs fresh approval of its own exact targets.
