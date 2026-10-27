---
name: cleanup-session
description: Inventories and safely removes disposable resources left by a coding session, including generated files, caches, temporary handoffs, stopped-agent worktrees, eligible local branches, containers, volumes, and local services. Use when the user explicitly invokes /skill:cleanup-session or asks to clean up after completed development work, remove session leftovers, or dispose of retained development resources.
argument-hint: "[repository or session scope]"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash
---

# Cleanup session

Run only on explicit invocation. Cleanup is destructive: **inventory first, propose exact actions, obtain approval, then revalidate each target immediately before acting.** This skill disposes of completed session leftovers; it does not decide that unfinished work is safe to discard.

## Workflow

1. **Establish scope.** Default to the current repository and local resources attributable to the current coding session. Accept an explicitly named repository, worktree, branch, or session scope. Report the principal checkout, Git common directory, current branch, and cleanup managers available (for example, harness-managed worktrees, `wt`, plain Git, a project task runner, or a container runtime). Do not sweep unrelated repositories, global temporary directories, all agent sessions, or remote/shared infrastructure. If attribution or scope is ambiguous, ask one clarifying question and stop.

2. **Inventory without mutation.** Inspect, as applicable:
   - the principal checkout and registered worktrees;
   - current and candidate branches, their upstreams, ahead/behind state, merged state, and reachability from a durable ref;
   - tracked, untracked, ignored, conflicted, staged, and unstaged files in each candidate worktree;
   - retained agent-managed worktrees and their reported cleanup blockers;
   - temporary artifacts demonstrably created by this session, such as handoff files whose exact paths were reported in the conversation;
   - project-generated build output, test output, coverage, logs, sockets, PID files, tool caches, and temporary databases attributable to this session;
   - local development processes and services started for the session, including servers, watchers, emulators, and port forwards;
   - containers, images, networks, volumes, and orchestration resources attributable to the repository/session through labels, project names, compose metadata, or recorded commands;
   - active agents, panes, locks, mounts, or submodules that make removal unsafe.

   Use read-only manager commands where available. Prefer repository manifests, recorded session commands, process working directories, runtime labels, ownership metadata, and exact paths as attribution evidence. Treat “not inspected” and command failure as **unknown**, never clean. Do not classify a file or runtime resource as disposable merely because it is untracked, ignored, stopped, dangling, under `/tmp`, or resembles generated output. Shared dependency caches, package stores, base images, volumes, databases, and services are **not** session-owned without stronger evidence. Do not inspect file contents unnecessarily or search credential stores.

3. **Classify every candidate.** Put each exact path or ref in one category:
   - **Safe to remove:** attributable to this scope, no live holder, no unresolved changes, and either reproducible/disposable or preserved on a verified durable ref.
   - **Needs preservation or publication:** unique commits, dirty files, review evidence, or other work that may still matter.
   - **Blocked/unknown:** active holder, conflict, lock, detached state, initialized submodule, failed inspection, uncertain ownership, or ambiguous user intent.
   - **Keep:** principal checkout, active work, user-designated retention, or artifacts required by another workflow.

   A merged branch is not automatically deletable: verify the intended integration target and remote state. A clean worktree can still contain unpushed commits. Ignored files are not proof of safety and may not be preserved by worktree tooling.

4. **Propose an exact cleanup plan.** Show each proposed destructive action separately with target, command/tool, reason it is safe, and consequence. Group related resources only when one repository-defined teardown command owns them and enumerate what that command affects. Separately list keep, preserve, blocked, and unknown items. Prefer the owning manager or repository-defined teardown (`worktree_remove`, `wt`, Compose, a project task, or equivalent) over raw filesystem or runtime deletion; use `git worktree remove` only for ordinary Git-managed worktrees. Never propose recursive deletion of a repository root or principal checkout. Do not combine approval for stopping active agents, stopping services, preserving dirty work, deleting worktrees, deleting branches, deleting runtime resources, and deleting artifacts into one vague “clean everything” action.

5. **Obtain explicit approval.** Ask the user to approve the exact proposed actions. Approval applies only to listed targets and consequences. Require separate explicit approval before:
   - stopping or cancelling a live agent/process;
   - creating a preservation/WIP commit;
   - force-removing a dirty worktree or file;
   - deleting any local or remote branch;
   - deleting containers, images, volumes, networks, databases, or caches that may hold data or be shared;
   - deleting an artifact whose ownership or reproducibility is not certain.

   Never push, merge, close issues/PRs, delete remote branches, alter cloud or shared infrastructure, prune an entire container runtime or shared cache, empty trash, or run broad clean commands such as `git clean`, `docker system prune`, or their equivalents unless the user explicitly requested that exact action after seeing its target list.

6. **Revalidate and execute narrowly.** Immediately before each approved action, repeat the relevant clean-state, holder, reachability, upstream, path, process-identity, port, runtime-label, and dependency checks. Stop that action if state changed or evidence is unknown; do not broaden or substitute targets. Use manager safety checks, graceful shutdown, and non-force operations by default. Never kill by process name or port alone, and never manually close or kill an agent pane when its harness provides lifecycle tools. Stopping an agent or service and deleting its persisted resources are distinct actions.

7. **Verify and report.** Re-run the bounded inventory. Report actions completed, targets retained, preservation commit SHAs if explicitly approved, failures, and remaining blockers. Confirm that the principal checkout and all kept work remain intact. Do not claim the session is clean while approved targets failed or unknown items remain; describe the residual state instead.

## Hard stops

Stop rather than infer when a candidate has uncommitted changes, untracked files, unique or unpushed commits, an active holder or dependent, possible persisted data, uncertain ownership, an unknown inspection result, or disagreement between managers. Never use cleanup as an implicit authorization to discard work retained by `implement-spec`, a subagent, or another workflow. Never clean remote, shared, production, or otherwise non-local resources under a generic session-cleanup approval.
