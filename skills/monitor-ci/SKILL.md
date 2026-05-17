---
name: monitor-ci
description: Check or monitor GitHub Actions CI for the current project. Supports instant status snapshots, polling a run until completion, and E2E test monitoring. Use when the user wants to check CI status, watch a build, poll a run, monitor GitHub Actions, or says things like "is CI passing?", "watch the build", or "check CI on this branch".
argument-hint: "[run-id | branch-name | 'e2e <run-id>']"
allowed-tools: Bash
---

# Monitor CI

## Interpret Arguments

### No argument — quick snapshot of current branch

```bash
BRANCH=$(git branch --show-current)
gh run list --branch "$BRANCH" --limit 1 --json databaseId,status,conclusion,name,headSha \
  --jq '.[0]'
```

Report status clearly. If the run is in progress and the user wants to wait, get the run ID and switch to polling mode.

### Numeric run ID — poll until completion

```bash
RUN_ID=$ARGUMENTS

while true; do
  STATUS=$(gh run view "$RUN_ID" --json status,conclusion,jobs \
    --jq '{status: .status, conclusion: .conclusion, jobs: [.jobs[] | {name, conclusion, status}]}')
  echo "$STATUS"

  DONE=$(echo "$STATUS" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['status'] in ['completed','failure','cancelled'])")
  [ "$DONE" = "True" ] && break

  echo "Still running — checking again in 60s..."
  sleep 60
done
```

Report progress at each interval. When complete, summarize: conclusion, total elapsed time, any failed jobs.

### Branch name — instant snapshot of latest run on that branch

```bash
gh run list --branch "$ARGUMENTS" --limit 1 \
  --json databaseId,status,conclusion,name,workflowName,createdAt \
  --jq '.[0]'
```

### `e2e <run-id>` — monitor E2E tests, exit on first failure

```bash
RUN_ID=$(echo "$ARGUMENTS" | awk '{print $2}')

gh run view "$RUN_ID" --json jobs \
  --jq '.jobs[] | select(.name | test("e2e|playwright|cypress"; "i")) | {name, status, conclusion, steps: [.steps[] | select(.conclusion == "failure") | .name]}'
```

Poll every 30 seconds. Exit immediately and report as soon as any E2E job fails — do not wait for the full run.

## Reporting

### ✅ All checks passed
Confirm and report total elapsed time.

### ❌ Failure detected
List failed jobs/steps by name, include the Actions run URL, and ask if you should investigate the failure logs:

```bash
gh run view "$RUN_ID" --log-failed
```

### ⏳ Still in progress
Report elapsed time and offer to keep watching.

## Getting the Run URL

```bash
gh run view "$RUN_ID" --json url --jq '.url'
```

Always include the run URL in failure reports so the user can open it directly.
