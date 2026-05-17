---
name: address-review-comments
description: Collect all open PR review comments and unresolved conversations, investigate each one, apply valid changes, push the branch, and reply to each thread with a summary. Use when the user wants to address PR feedback, respond to review comments, resolve review threads, or says things like "fix the review comments", "address feedback", or "respond to the PR review".
argument-hint: "[PR URL or number]"
allowed-tools: Read, Grep, Glob, Bash, Edit, Write
---

# Address Review Comments

## Identify the PR

If `$ARGUMENTS` is provided, treat it as a PR URL or number.

If no argument is given, infer the PR from the current branch:

```bash
# Get current branch
git branch --show-current

# Find associated PR
gh pr view --json number,url,headRefName
```

If the PR cannot be determined confidently, ask for the PR URL instead of guessing.

## Collect All Open Feedback

Fetch every open review comment and unresolved conversation thread:

```bash
gh pr view $PR --json reviews,reviewRequests,comments
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments --jq '[.[] | select(.position != null) | {id, path, line, body, user: .user.login}]'
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews --jq '[.[] | {id, state, body, user: .user.login}]'
```

Group comments by file and line so related feedback is handled together.

## Investigate Before Acting

For each comment:

1. Read the full diff context around the flagged line
2. Understand the reviewer's intent before touching anything
3. Decide: **valid** (apply), **not valid** (decline with explanation), or **blocked** (stop and report)

Do not batch-apply changes. Handle one comment at a time.

## Apply Valid Changes

Make the minimal correct change needed to address the feedback. Do not refactor surrounding code unless the comment explicitly asks for it.

After all changes are applied, run relevant local checks:

```bash
# Examples — adapt to the project
npm test
npm run lint
python -m pytest
make test
```

Fix any regressions before pushing.

## Push the Branch

```bash
git add -p          # Review changes before staging
git commit -m "Address PR review feedback"
git push
```

## Reply to Each Thread

After a successful push, reply to every addressed comment with a concise summary of what changed:

```bash
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies \
  --method POST \
  --field body="Fixed in <commit-sha>: <one-sentence summary of what changed>"
```

For comments you declined to adopt, reply with a clear explanation of why the change was not applied.

Resolve each conversation thread only after the push succeeds:

```bash
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews/$REVIEW_ID/dismissals \
  --method PUT --field message="Addressed"
```

## Edge Cases

- **Conflicting comments**: Surface the conflict to the user before making changes.
- **Comment on deleted line**: Check if the concern still applies in the current diff.
- **Blocked comment**: Stop immediately and report the blocker — do not guess or work around it.
- **PR already merged**: Report the status and stop.
