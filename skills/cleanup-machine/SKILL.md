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

Approve by row, e.g. "approve 1–4, 7". Rows not named stay untouched, and so does anything the report did not list.

For worktrees, use the bundled read-only inventory script rather than ad hoc commands (see [REFERENCE.md](REFERENCE.md#worktree-inventory-script)):

```bash
# After the user confirms the integration ref (step 3):
python3 scripts/cleanup_inventory.py scan --root ~/Code --depth 3 \
  --agent-root ~/.herdr/worktrees --integration '<confirmed-ref>'
# prints {"run": "<private temp dir>", "digest": "<sha256>", ...}
python3 scripts/cleanup_inventory.py recheck --run <run> --digest <sha256> --rows 3-40,52 [--approve-ignored]
```

## Workflow

1. **Load the machine profile.** Read the local, uncommitted profile at `${XDG_CONFIG_HOME:-$HOME/.config}/cleanup-machine/profile.md` if present. It may define roots to scan, worktree locations, staleness thresholds, protected paths, private-repository rules, and where to record snapshots. Profile values override the defaults in REFERENCE.md. Resolve `scripts/` relative to this skill's source directory. Treat the profile as local configuration: never copy its contents, private repository names, hostnames, or paths into commits, issues, PRs, or other shared output. If it is absent, use the defaults and say so. If an argument is given, limit the run to that category or root.

2. **Report machine state.** Record date, local timezone, free and used space on the data volume, and which managers are available (`git`, `wt`, Homebrew, npm, a container runtime, agent harnesses). A missing or stopped manager makes its category **unknown**, not empty. Never start a daemon or VM just to inventory it without asking.

3. **Confirm the integration ref.** If the profile defines integration targets other than the default branch, list the candidate refs and ask the user to confirm the current one **before any classification or manifest is produced**. A newest-commit heuristic is a suggestion, not confirmation. Without confirmation, stop the worktree and branch categories; do not fall back to the default branch.

4. **Inventory without mutation.** Sweep each in-scope category in REFERENCE.md with read-only commands; for worktrees, run `scripts/cleanup_inventory.py scan` with the profile's roots, depth, agent roots, stale threshold, and the confirmed `--integration` ref. Measure sizes and collect staleness evidence. Do not read file contents beyond metadata needed for attribution, and never inspect credential stores, auth files, or browser profiles. Treat command failures, timeouts, permission errors, and uninspected items as **unknown**, never clean.

5. **Classify every candidate.** Use the same categories as `cleanup-session`: **safe to remove**, **needs preservation or publication**, **blocked/unknown**, or **keep**. Staleness alone never makes something safe. A worktree is removable only when it is clean and its commits are reachable from a durable ref (merged, or pushed to a branch that still exists). Being ignored or looking generated is not proof of reproducibility: the script calls a worktree `safe` only when it has no ignored files at all. One whose only ignored files are real top-level directories with conventional build-output names (e.g. `node_modules`, `dist`) is `ignored-conventional`: it lists the exact paths and is executable only if the user explicitly accepts losing them; everything else ignored is blocked. The script does not know PR state or protected paths: downgrade both executable classes (`safe` and `ignored-conventional`) with an open PR to **keep**, a closed-unmerged PR to **needs preservation**, and protected paths to **keep**. A shared cache is safe to trim only through its owning tool's command. Principal checkouts, the current working directory, active sessions, and profile-protected paths are always **keep**.

6. **Report, ranked by reclaimable space, and freeze the targets.** Use the report format in REFERENCE.md: a summary, then one table per category with the target, size, staleness evidence, classification, and proposed command. Every proposed row maps to an explicit list of manifest IDs after the downgrades in step 5 (for example "row 3 = manifest 12–40, 44"); never let a grouped row's ID range include a downgraded or non-safe target. Above ~40 targets in a category, group rows by repository, root, and class. Prefix IDs by file (`wt:12`, `x:3`). For non-worktree categories, write the exact targets, actions, and consequences to `extra.tsv` in a private run directory (the script's, or a new one from `mktemp -d`, which is owner-only) and show its SHA-256 (`shasum -a 256`) beside the worktree manifest digest; before executing, re-hash it and stop if either digest changed. State the run directory and both digests in the report. Compare with the previous snapshot when one exists. With `report` as the argument, stop here.

7. **Obtain explicit approval.** Ask the user to select exact targets by row. Approval covers only the targets frozen in the report or its manifest, and the stated consequences. Never re-run a discovery filter at execution time to pick targets: anything that newly qualifies after the report waits for the next run. Require separate approval before: deleting any branch, removing a worktree with ignored files (show the listed paths), trimming a shared cache, deleting agent session logs, deleting container images or volumes, or stopping any process. Never push, delete remote branches, close PRs, empty the Trash, run `git clean`, `docker system prune`, `brew autoremove`, or remove a whole cache directory with `rm -rf` unless the user requested that exact action after seeing its targets.

8. **Revalidate and execute narrowly.** Expand the approved report rows into their manifest IDs, then act only on targets that are both in those IDs and still pass revalidation. For worktrees, run `scripts/cleanup_inventory.py recheck --run <run> --digest <digest> --rows <ids>`, adding `--approve-ignored` only if the user accepted the listed ignored paths; it refuses a changed manifest (whose digest also covers the scan settings), and returns `still-safe` only when path, repository and Git common dir, branch, HEAD, class, and the exact ignored-path set all match the report. Run it immediately before acting, not once for a long batch: re-run it if time passes or the batch is interrupted. Re-apply the step 5 PR and protected-path checks, and check other holders (agent panes, open editors) the script cannot see. If anything changed, skip that action and report it. Prefer owning managers over raw deletion, using the exact safe forms in REFERENCE.md: for example `wt remove --no-delete-branch --no-hooks --foreground`, so removing a worktree never also deletes a branch or runs hooks. Never use force flags by default.

9. **Verify, record, and report.** Re-measure the affected categories and free space. Report reclaimed space, completed actions, skipped or failed actions, and the remaining blockers. Write a snapshot of sizes and counts only (no file names from private repositories) to the profile's snapshot location, or `${XDG_STATE_HOME:-$HOME/.local/state}/cleanup-machine/snapshots.md` by default. Leave the private run directory local (delete it when done); never copy it to shared or synced locations. Do not commit anything.

## Hard stops

Stop rather than infer when a candidate has uncommitted or untracked changes, stash entries, initialized submodules, a lock, unique or unpushed commits, an active holder or dependent, disagreement between managers, possible persisted data, uncertain ownership, or a failed inspection. Never sweep outside the configured roots, never touch system directories or other users' files, and never treat a weekly cadence as standing approval: every run needs fresh approval of its own exact targets.
