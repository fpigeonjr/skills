---
name: start-ticket
description: Start work on a new Jira ticket by creating a feature branch off the current integration branch, following the team's git branching strategy. Use when the user wants to begin a ticket, start new work, create a feature branch from a Jira ticket, or pastes a Jira ticket URL or ID to branch from.
argument-hint: "[Jira ticket URL or ID]"
allowed-tools: Bash
---

# Start Ticket

Create a feature branch for a Jira ticket off the latest integration branch, following the team's branching strategy.

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

### 2. Check the working tree is clean

Run `git status --porcelain`. If there is any output, **stop and report** the dirty files. A new ticket must start from a clean tree. Do not auto-stash or auto-commit.

### 3. Fetch and find the current integration branch

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

### 4. Handle an existing feature branch

- **Exists locally**: don't recreate. Offer to check it out instead.
- **Exists on remote but not locally**: check out a local tracking branch off the remote (resumes existing work) rather than branching off integration.
- **Doesn't exist anywhere**: create it (next step).

### 5. Create the feature branch

Branch off the chosen **remote** integration ref so it starts from the true latest tip:

```bash
git checkout -b IAEMOD-58792 origin/integration-59.2
```

Leave the branch **local** — do not push or set upstream.

### 6. Confirm

Print a confirmation showing the branch and its base, e.g.:

```
Created IAEMOD-58792 ← origin/integration-59.2
```

Suggest (but do not run) the push command for when the user is ready:

```
git push -u origin IAEMOD-58792
```
