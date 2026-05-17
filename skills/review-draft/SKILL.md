---
name: review-draft
description: Review a pull request and produce a draft review for a human to read and post. Does not submit anything. Surfaces concrete bugs, regressions, risks, and missing tests. Ends with a clear Approve or Request Changes recommendation. Use when the user wants a code review drafted, wants to review a PR before posting, or says things like "draft a review", "review this PR", or "write up a review for me to post".
argument-hint: "[PR URL or number]"
allowed-tools: Read, Grep, Glob, Bash
---

# Review Draft

Produce a thorough code review for a human to read and decide whether to post. Do not submit, comment, or post anything to GitHub.

## Identify the PR

If `$ARGUMENTS` is provided, treat it as a PR URL or number.

Otherwise infer from the current branch:

```bash
gh pr view --json number,url,headRefName,baseRefName,title,body
```

If the PR cannot be determined confidently, ask for the PR URL.

## Check for Prior Reviews

```bash
gh pr view $PR --json reviews \
  --jq '.reviews[] | {author: .author.login, state, submittedAt, body}'
```

If prior reviews exist, treat this as a **follow-up review**:
- Check which concerns were raised before
- Verify whether they were addressed in new commits
- Focus on what changed since the last review

## Gather the Diff

```bash
# PR metadata
gh pr view $PR --json title,body,additions,deletions,changedFiles

# Full diff
gh pr diff $PR

# Commits on this branch
gh pr view $PR --json commits --jq '.commits[] | {oid, messageHeadline}'
```

Read the full diff before writing any review comments.

## Explore Relevant Context

For non-trivial changes, read the files being modified to understand the surrounding code:

```bash
# View full file for context around changed sections
gh api repos/{owner}/{repo}/contents/{path}?ref={head-sha} --jq '.content' | base64 -d
```

Look for: existing tests, related modules, interface contracts, documentation.

## Write the Review

Structure the review as follows:

### Summary
One paragraph: what the PR does at a high level.

### Findings

For each finding, include:
- **File and line reference** (e.g. `src/api/orders.py:42`)
- **Severity**: 🔴 Bug / 🟡 Risk / 🟠 Missing test / 🔵 Suggestion
- **Description**: what the problem is and why it matters
- **Suggested fix** (when applicable)

Prioritize in this order:
1. 🔴 Concrete bugs or regressions
2. 🟡 Risks (security, data integrity, performance)
3. 🟠 Missing or inadequate tests for changed behavior
4. 🔵 Suggestions (style, clarity, minor improvements)

Only include 🔵 suggestions if there are no higher-severity findings, or if they are genuinely important.

### Recommendation

End with one of:

> **✅ Approve** — reason in one sentence.

> **🔄 Request Changes** — list the specific blocking issues that must be resolved.

## Output Format

Present the full review as a formatted markdown document the human can copy, edit, and post. Include a note at the end:

> _This review was drafted by your coding agent. Review and edit before posting._
