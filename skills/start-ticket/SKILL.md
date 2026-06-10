---
name: start-ticket
description: Start work on a new Jira ticket by creating a worktree and feature branch off the current integration branch, following the team's git branching strategy. Use when the user wants to begin a ticket, start new work, create a feature branch from a Jira ticket, or pastes a Jira ticket URL or ID to branch from.
argument-hint: "[Jira ticket URL or ID]"
allowed-tools: Bash
---

# Start Ticket

Create a worktree and feature branch for a Jira ticket off the latest integration branch, using `wt` (worktrunk) for worktree management.

## Branching strategy

- Integration branches are named `integration-<PI>.<Sprint>`, where `<Sprint>` is `1`, `2`, `3`, or `IP` (the 4th / IP sprint). Example: `integration-59.2`, `integration-59.IP`.
- A feature branch is created off the **current** integration branch for every ticket, named **exactly** after the Jira ticket ID (e.g. `IAEMOD-58792`).

## Process

### 1. Resolve the ticket ID

The argument may be either a Jira URL or a bare ticket ID.

- If it's a URL (e.g. `https://gsa-standard.atlassian-us-gov-mod.net/browse/IAEMOD-58792`), extract the last path segment after `/browse/`, stripping any query string or trailing slash.
- If it's already a bare ID, use it directly.
- If no argument is given, prompt the user for the ticket URL or ID.

Normalize to uppercase and validate against `^[A-Z][A-Z0-9]+-\d+$`. If it doesn't match, stop and report — do not create a branch from a malformed ID.

### 2. Fetch and find the current integration branch

```bash
git fetch origin --prune
git branch -r --list 'origin/integration-*'
```

Parse each branch as `integration-<PI>.<Sprint>` and pick the highest:

- Compare by **PI number** (numeric) first.
- Then by **sprint**: `IP` always sorts last within its PI (after `1`, `2`, `3`).
- Ignore branches that don't match the `integration-<PI>.<Sprint>` shape — never crash on malformed names.

If no matching integration branch is found, **stop** with a clear error listing the `integration-*` branches (if any) that were seen.

Show the chosen integration branch to the user and ask them to confirm or override before proceeding.

### 3. Create the worktree and feature branch

Use `wt` to create the worktree and branch off the chosen remote integration ref in one step:

```bash
wt switch --create IAEMOD-58792 --base origin/integration-59.2
```

`wt` handles worktree creation, directory switching, and any configured project hooks automatically. Because each ticket gets its own worktree, there is no need to check for a dirty working tree — other in-flight work is unaffected.

### 4. Handle an existing branch

- If `wt switch --create` reports the branch already exists locally, offer to switch to its worktree instead: `wt switch IAEMOD-58792`.
- If it exists on remote only, switch without `--create` to check out a local tracking branch: `wt switch IAEMOD-58792`.

### 5. Confirm

Print a confirmation showing the branch and its base, e.g.:

```
Created worktree for IAEMOD-58792 ← origin/integration-59.2
```
