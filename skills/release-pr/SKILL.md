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

Resolve the repository once and use it on every command, so a bare PR number never targets another checkout's repo (set `GH_HOST` for GitHub Enterprise):

```bash
PR_NUMBER=$(gh pr view "$PR" --json number --jq .number)
OWNER_REPO=$(gh pr view "$PR" --json url --jq '.url | split("/") | .[3] + "/" + .[4]')
OWNER=${OWNER_REPO%/*}; REPO=${OWNER_REPO#*/}
```

## Confirm Draft State

```bash
gh pr view "$PR_NUMBER" -R "$OWNER_REPO" --json isDraft,state --jq '{isDraft, state}'
```

If the PR is not in draft state, report its current state and stop — do not proceed.

If the PR is already merged or closed, report and stop.

## Poll CI Checks

Poll every 30 seconds. Take **one snapshot per iteration** and derive every count from it, so a check cannot change between the failure and pending counts. The loop ends with an explicit `STATUS`; only `COMPLETE` may continue.

```bash
STATUS=
while :; do
  echo "$(date '+%H:%M:%S') — checking CI..."
  ERR=$(mktemp) || { STATUS=ERROR; echo "mktemp failed"; break; }
  # Capture rc without tripping set -e; gh exits 1 on API errors and on "no checks"
  RC=0; OUT=$(gh pr checks "$PR_NUMBER" -R "$OWNER_REPO" --json name,state,bucket,link 2>"$ERR") || RC=$?
  if [ "$RC" -ne 0 ] || [ -z "$OUT" ]; then
    # Only gh's exact no-checks diagnostic with empty stdout means NO_CHECKS; anything else is ERROR
    if [ -z "$OUT" ] && grep -qxE "no checks reported on the '.*' branch" "$ERR"; then STATUS=NO_CHECKS
    else STATUS=ERROR; cat "$ERR"; echo "gh rc=$RC"; fi
    rm -f "$ERR"; break
  fi
  rm -f "$ERR"
  # Every entry must have a known bucket; unknown data is ERROR, never a pass
  jq -e 'type == "array" and all(.[]; type == "object" and (.bucket | IN("pass","fail","pending","skipping","cancel")))' >/dev/null 2>&1 <<<"$OUT" \
    || { STATUS=ERROR; echo "unexpected checks JSON"; break; }
  jq -r '.[] | "\(.bucket)\t\(.state)\t\(.name)"' <<<"$OUT"
  TOTAL=$(jq 'length' <<<"$OUT")
  FAILED=$(jq '[.[] | select(.bucket == "fail" or .bucket == "cancel")] | length' <<<"$OUT")
  PENDING=$(jq '[.[] | select(.bucket == "pending")] | length' <<<"$OUT")
  [[ $TOTAL =~ ^[0-9]+$ && $FAILED =~ ^[0-9]+$ && $PENDING =~ ^[0-9]+$ ]] || { STATUS=ERROR; echo "bad counts"; break; }
  [ "$TOTAL" -eq 0 ] && { STATUS=NO_CHECKS; break; }
  [ "$FAILED" -gt 0 ] && { STATUS=FAILED; break; }
  PASSED=$(jq '[.[] | select(.bucket == "pass" or .bucket == "skipping")] | length' <<<"$OUT")
  [ "$PENDING" -eq 0 ] && [ "$PASSED" = "$TOTAL" ] && { STATUS=COMPLETE; break; }
  echo "  $PENDING checks still pending — waiting 30s..."
  sleep 30
done
echo "STATUS=$STATUS"
```

Run the block with bash (macOS `/bin/bash` 3.2 is fine). Buckets are `pass`, `fail`, `pending`, `skipping` and `cancel`; `skipping` is not a failure, and `COMPLETE` requires every check to be `pass` or `skipping`. `state` values are uppercase. In `--json` mode gh exits 0 even with failing or pending checks; a nonzero exit means an API error or no checks.

- `FAILED`: stop. Report each failing check with its `link`; do not convert to ready.

  ```bash
  jq -r '.[] | select(.bucket == "fail" or .bucket == "cancel") | "\(.name)\t\(.state)\t\(.link)"' <<<"$OUT"
  ```

- `ERROR`: stop and report the gh error. Never treat it as zero checks or as a pass.
- `NO_CHECKS`: stop and ask the user; no checks is not a pass.
- `COMPLETE`: continue.

### If required checks are not configured
Check with `gh pr checks "$PR_NUMBER" -R "$OWNER_REPO" --required`. If it reports `no required checks` (it exits nonzero), note explicitly that every check is advisory, and ask the user to confirm before proceeding.

## Check for Unresolved Threads

Use `OWNER`, `REPO` and `PR_NUMBER` from Identify the PR.

Count unresolved threads across all pages, and keep the separate changes-requested review check:

```bash
set -o pipefail # Do not hide API errors behind jq
gh api graphql --paginate --slurp \
  -f owner="$OWNER" -f repo="$REPO" -F number="$PR_NUMBER" \
  -f query='query($owner:String!,$repo:String!,$number:Int!,$endCursor:String){repository(owner:$owner,name:$repo){pullRequest(number:$number){reviewThreads(first:100,after:$endCursor){nodes{isResolved}pageInfo{hasNextPage endCursor}}}}}' \
  | jq '[.[].data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)] | length'

# Count each reviewer's latest decision only, so a later approval supersedes a change request
gh api "repos/$OWNER/$REPO/pulls/$PR_NUMBER/reviews" --paginate --slurp \
  | jq '[.[][] | select(.state == "APPROVED" or .state == "CHANGES_REQUESTED" or .state == "DISMISSED")]
        | group_by(.user.login) | map(last) | [.[] | select(.state == "CHANGES_REQUESTED")] | length'
```

If either query errors, stop and report. If unresolved threads or changes-requested reviews exist, report them and ask how to proceed — do not mark ready automatically.

## Convert to Ready for Review

Once `STATUS=COMPLETE`, any advisory-check confirmation is obtained, and review blockers are cleared, re-check immediately before marking ready. Someone may have marked the PR ready, or pushed and restarted CI, while you were checking:

```bash
gh pr view "$PR_NUMBER" -R "$OWNER_REPO" --json isDraft,state --jq '{isDraft, state}'
```

If it is no longer draft or is merged/closed, report its state and stop. Run the poll loop once more; if it no longer ends `COMPLETE`, handle that status as above. Only if the PR is still open and draft and CI is still complete:

```bash
gh pr ready "$PR_NUMBER" -R "$OWNER_REPO"
```

Report the final PR URL and confirm it is now ready for review:

```bash
gh pr view "$PR_NUMBER" -R "$OWNER_REPO" --json url,state,isDraft --jq '{url, state, isDraft}'
```
