---
name: start-ticket
description: Start work on a new Jira or GitHub issue by creating a worktree and feature branch off the current integration branch, following the team's git branching strategy. Use when the user wants to begin a ticket, start new work, create a feature branch from a Jira ticket or GitHub issue, or pastes a Jira ticket URL/ID or GitHub issue URL (github.com or GitHub Enterprise) to branch from.
argument-hint: "[Jira ticket URL/ID or GitHub issue URL]"
allowed-tools: Bash
---

# Start Ticket

> ⚠️ This skill is org-specific: it assumes the GSA Jira instance (`gsa-standard.atlassian-us-gov-mod.net`) and the `wt` (worktrunk) CLI for worktree management. GitHub support works with both `github.com` and GitHub Enterprise instances.

Create a worktree and feature branch for a Jira ticket or GitHub issue off the latest integration branch, using `wt` (worktrunk) for worktree management.

## Branching strategy

- Integration branches are named `integration-<PI>.<Sprint>`, where `<Sprint>` is `1`, `2`, `3`, or `IP` (the 4th / IP sprint). Example: `integration-66.1`, `integration-59.IP`.
- Jira feature branches are named **exactly** after the ticket ID (e.g. `IAEMOD-58792`).
- GitHub issue branches are named `gh-<number>-<slug>` where `<slug>` is the issue title lowercased, with non-alphanumeric characters replaced by hyphens, truncated to 50 characters (e.g. `gh-90-fix-login-redirect`).

## Process

### 1. Detect the input type and resolve the branch name

**Jira URL** (e.g. `https://gsa-standard.atlassian-us-gov-mod.net/browse/IAEMOD-58792`):
- Extract the last path segment after `/browse/`, strip any query string or trailing slash.
- Normalize to uppercase and validate against `^[A-Z][A-Z0-9]+-\d+$`. Stop and report if invalid.
- Branch name = the ticket ID, e.g. `IAEMOD-58792`.

**Bare Jira ID** (e.g. `IAEMOD-58792`):
- Validate against `^[A-Z][A-Z0-9]+-\d+$`. Stop and report if invalid.
- Branch name = the ticket ID.

**GitHub issue URL** (e.g. `https://github.helix.gsa.gov/mcaas-iae/iae-sam-front-end/issues/90` or `https://github.com/org/repo/issues/90`):
- Extract the hostname, org/repo, and issue number from the URL.
- If the hostname is anything other than `github.com`, pass `--hostname <hostname>` to `gh`.
- Fetch the issue title:
  ```bash
  # GitHub.com
  gh issue view 90 --repo org/repo --json title --jq '.title'

  # GitHub Enterprise
  gh issue view 90 --repo org/repo --hostname github.helix.gsa.gov --json title --jq '.title'
  ```
- Slugify the title: lowercase, replace non-alphanumeric runs with `-`, strip leading/trailing `-`, truncate to 50 chars.
- Branch name = `gh-<number>-<slug>`, e.g. `gh-90-fix-login-redirect`.

**No argument**: prompt the user for a Jira ticket URL/ID or GitHub issue URL.

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

Show the chosen integration branch and resolved branch name to the user and ask them to confirm or override before proceeding.

### 3. Create the worktree and feature branch

Use `wt` to create the worktree and branch off the chosen remote integration ref:

```bash
# Jira example
wt switch --create IAEMOD-58792 --base origin/integration-66.1

# GitHub issue example
wt switch --create gh-90-fix-login-redirect --base origin/integration-66.1
```

`wt` handles worktree creation, directory switching, and any configured project hooks automatically. Because each ticket gets its own worktree, there is no need to check for a dirty working tree — other in-flight work is unaffected.

### 4. Handle an existing branch

- If `wt switch --create` reports the branch already exists locally, offer to switch to its worktree instead: `wt switch <branch>`.
- If it exists on remote only, switch without `--create` to check out a local tracking branch: `wt switch <branch>`.

### 5. Confirm

Print a confirmation showing the branch and its base, e.g.:

```
Created worktree for gh-90-fix-login-redirect ← origin/integration-66.1
```
