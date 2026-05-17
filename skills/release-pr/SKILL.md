---
name: release-pr
description: Wait for all CI checks to pass on a draft PR, then convert it to ready-for-review. Polls gh pr checks on a 30-second interval, reports progress, stops on any failure, and checks for unresolved threads before marking ready. Use when the user wants to release a draft PR, mark a PR ready for review, promote a draft, or says things like "release this PR", "mark it ready", or "ship the PR once CI passes".
argument-hint: "[PR URL or number]"
allowed-tools: Bash
---

# Release PR

## Identify the PR

If `$ARGUMENTS` is provided, treat it as a PR URL or number.

Otherwise, infer from the current branch:

```bash
gh pr view --json number,url,state,isDraft
```

If the PR cannot be determined confidently, ask rather than guessing.

## Confirm Draft State

```bash
gh pr view $PR --json isDraft,state --jq '{isDraft, state}'
```

If the PR is not in draft state, report its current state and stop — do not proceed.

If the PR is already merged or closed, report and stop.

## Poll CI Checks

Poll every 30 seconds until all required checks pass or a failure is detected:

```bash
while true; do
  echo "$(date '+%H:%M:%S') — checking CI..."
  gh pr checks $PR --json name,state,conclusion \
    --jq '.[] | {name, state, conclusion}'

  # Check for any failures
  FAILED=$(gh pr checks $PR --json conclusion \
    --jq '[.[] | select(.conclusion == "failure" or .conclusion == "cancelled")] | length')

  # Check if all complete
  PENDING=$(gh pr checks $PR --json state \
    --jq '[.[] | select(.state == "pending" or .state == "queued" or .state == "in_progress")] | length')

  [ "$FAILED" -gt 0 ] && echo "FAILURE DETECTED" && break
  [ "$PENDING" -eq 0 ] && echo "ALL CHECKS COMPLETE" && break

  echo "  $PENDING checks still pending — waiting 30s..."
  sleep 30
done
```

### On failure
Stop immediately. Report which check(s) failed and why. Do not convert to ready on failure.

```bash
gh pr checks $PR --json name,conclusion,detailsUrl \
  --jq '.[] | select(.conclusion == "failure") | {name, detailsUrl}'
```

### If required checks are not configured
Note this explicitly and ask the user to confirm before proceeding.

## Check for Unresolved Threads

Before marking ready, verify there are no unresolved review threads:

```bash
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews \
  --jq '[.[] | select(.state == "CHANGES_REQUESTED")] | length'
```

If unresolved threads exist, report them and ask how to proceed — do not mark ready automatically.

## Convert to Ready for Review

Once all checks are green and no unresolved threads remain:

```bash
gh pr ready $PR
```

Report the final PR URL and confirm it is now ready for review:

```bash
gh pr view $PR --json url,state,isDraft --jq '{url, state, isDraft}'
```
