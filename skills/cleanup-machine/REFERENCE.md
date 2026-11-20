# Cleanup machine reference

## Default scope

Use these defaults when the profile does not override them. Expand `~` and environment variables, and skip paths that do not exist.

| Setting | Default |
|---|---|
| Code roots | `~/Code` (depth 2), plus each repository's registered worktrees |
| Agent worktree roots | locations reported by installed harnesses (e.g. `~/.herdr/worktrees`) and configured `wt` worktree paths |
| Stale worktree / branch | no commits and no file changes for 14 days |
| Stale session log | older than 60 days |
| Large item threshold | 500 MB, for anything reported outside a table |
| Per-category cap | ~40 candidates; report the remainder as a count |

## Sweep categories

Run in this order, because the first ones usually reclaim the most space. For each category, use the listed read-only commands and staleness signals.

### 1. Worktrees

- Enumerate with `git worktree list --porcelain` from each principal checkout, `wt list` where configured, and the harness's own listing for agent-managed worktrees. Sibling directories named `<repo>.<branch>` are worktrees only if Git registers them.
- Collect: branch, upstream, ahead/behind, whether the branch is merged into its integration target, dirty/untracked/ignored file counts, stash entries for that branch, initialized submodules, locks (`git worktree list --porcelain` reports `locked`), last commit date, last modification time, size (`du -sh`), and holders (processes whose cwd is inside the path via `lsof -a -d cwd`, open terminal or agent panes; avoid `lsof +D` on large trees).
- PR state (`gh pr list --head <branch> --state all`) is supporting evidence only. A closed-unmerged PR means "needs preservation or publication" unless the user says the work is abandoned.
- Removal goes through the owning manager, removing only the worktree:
  - `wt remove --no-delete-branch --no-hooks --foreground <branch>`. By default `wt remove` also deletes the branch using its own default-branch and squash-equivalence rules, runs configured pre/post-remove hooks (which can run arbitrary commands, including remote ones), and returns before removal finishes. Run hooks only if the user approved their enumerated effects as a separate row.
  - `git worktree remove <path>` (no `--force`) for plain Git worktrees; the owning harness's tool for agent-managed ones.
  - Branch deletion is always a separate row in category 2, never a side effect.
- Prunable (missing-directory) registrations are reported. `git worktree prune` is repository-wide, so run it only when `git worktree prune --dry-run --verbose` lists exactly the approved set, and never for a path that may be on an unmounted volume.

### 2. Local branches without worktrees

- Per repository: `git for-each-ref --format='%(refname:short) %(upstream:short) %(upstream:track) %(committerdate:short)' refs/heads` for upstream tracking (`[gone]`) and last commit date, plus `git branch --merged <integration-ref>` against an explicitly pinned integration ref. Run `git fetch` only with approval; otherwise say remote-tracking refs may be stale.
- Propose `git branch -d` (never `-D`) only for branches whose tip is reachable from the pinned integration ref or from a remote branch that still exists. `git branch -d` itself checks against the upstream or HEAD, not the integration target, so its success is not the evidence.
- Squash- or rebase-merged branches may not be reachable. Classify unreachable ones **blocked/unknown** and keep them. Confirming that the PR merged does not waive the reachability or unique-commit hard stops; deleting such a branch needs `-D`, which this skill never proposes.

### 3. Build output in inactive checkouts

- In stale checkouts only: `node_modules`, `dist`, `coverage`, `.angular/cache`, `.nx/cache`, `target`, `.gradle`, `build`, and similar candidates.
- Being ignored or having a conventional name is **not** evidence of reproducibility. Classify as safe only with positive evidence that the exact directory is generated: the build/package configuration writes it, and a lockfile or build command can recreate it. Mixed or unexplained content is **blocked/unknown**.
- Report size per checkout. Never remove from the active checkout, a checkout with a running process, or a directory another checkout links to.

### 4. Shared tool caches

- npm (`~/.npm`), Homebrew (`brew cleanup -n`), Playwright browsers (`~/Library/Caches/ms-playwright`), pip/uv, Gradle/Maven, node-gyp, fnm or nvm Node versions not referenced by any `.nvmrc`/`.node-version`/`engines` under the code roots.
- Shared caches may have consumers outside the scanned roots; a cwd check is not a dependency check. Shared caches are never session-owned. Propose only tool-owned commands: `brew cleanup` (show `brew cleanup -n` first and run only if the real target list still matches the approved one), `npm cache verify` (it garbage-collects, so it is an action, not an inventory step), Playwright's own `uninstall` run from the project that installed a revision (not `--all`), `fnm uninstall <version>`. Deleting a cache directory outright needs explicit approval of that exact command.

### 5. Agent session logs and state

- Pi session directories (`~/.config/pi/agent/sessions` or the configured session dir), other harness logs, and orphaned agent worktree records.
- Report count, total size, and age distribution. Sessions for directories that still exist are **keep** by default. A missing working directory does not prove a session is inactive: the current session and any recently modified file are always **keep**. Sessions whose working directory no longer exists and that are older than the stale threshold may be proposed for archival or removal, but only after separate approval, because they are the evidence for `retro`.
- Never read transcript contents during this sweep.

### 6. Containers and VMs

- If the runtime is running: `docker system df -v`, `docker ps -a`, `docker volume ls`, and Compose project labels. If it is stopped, report the VM disk size (e.g. Colima, Docker Desktop) and mark the category **unknown**. Ask before starting it.
- Dangling images may be proposed individually. Stopped containers (writable layers) and volumes may hold data: always **needs preservation**, even if their owning project is gone, unless the user confirms the data is disposable.

### 7. Large or old files in personal folders (report only)

- `~/Downloads` and `~/Desktop`: items over the large threshold, or older than 90 days, sorted by size. Report only; never propose deletion here. The user decides by hand.

## Report format

Start with a summary block:

- date, timezone, free/used space, and the change since the previous snapshot;
- categories inspected, skipped, or unknown, with the reason;
- total reclaimable space from **safe to remove** rows only.

Then one table per category, sorted by size:

| # | Target | Size | Evidence | Class | Proposed action |
|---|---|---|---|---|---|

- **Target** is the exact path or ref. **Evidence** gives the facts that drove the class (for example "merged into integration, clean, last commit 41d ago").
- Number rows across the whole report so the user can approve them as, for example, "approve 1–4, 7".
- List **needs preservation**, **blocked/unknown**, and notable **keep** items below each table with a one-line reason.

## Snapshot format

Append one block per run. Use counts and sizes only. Use category names, not the names of private repositories or branches.

```md
## YYYY-MM-DD (local timezone)
- free: 120 GiB (+8 GiB since last run)
- worktrees: 12 (30 GB), removed 3 (6.2 GB)
- branches: 25 local, removed 7
- caches: npm 10 GB, Homebrew 1 GB, Playwright 1.5 GB
- sessions: 200 (400 MB)
- containers: unknown (runtime stopped)
```

## Profile template

The profile is local to the machine and is never committed with this skill. Every field is optional.

```md
# cleanup-machine profile

## Roots
- ~/Code (depth 2)

## Agent worktree roots
- ~/.herdr/worktrees

## Thresholds
- stale worktree/branch: 14 days
- stale session log: 60 days

## Protected (always keep)
- ~/Code/some-principal-checkout

## Private repositories
- Pattern or host whose names must not appear in snapshots or shared output, e.g. `internal-*` or a private Git host.

## Integration targets
- How to tell which branch a feature branch merges into, if not the default branch.

## Snapshots
- ~/.local/state/cleanup-machine/snapshots.md
```
