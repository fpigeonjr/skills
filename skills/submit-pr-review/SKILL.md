---
name: submit-pr-review
description: Turns a code review into an approved GitHub PR review and submits it only after exact human approval. Use when the user wants to post or submit a PR review, approve a PR, request changes on GitHub, or says "write up a review for me to post".
argument-hint: "[PR URL or number]"
allowed-tools: Read Grep Glob Bash
---

# Submit PR Review

GitHub submission wrapper for the `code-review` skill. Identify the PR, run the review, turn its findings into an Approve or Request Changes draft, and submit only the exact text the human approves.

Do not submit, comment, approve, request changes, or otherwise post anything to GitHub until the human explicitly approves the exact review body and recommendation.

## Identify the PR

If `$ARGUMENTS` is provided, treat it as a PR URL or number.

Otherwise infer from the current branch:

```bash
gh pr view --json number,url,headRefName,baseRefName,title,body
```

If the PR cannot be determined confidently, ask for the PR URL.

## Check for Prior Reviews

```bash
gh pr view $PR --json reviews,comments \
  --jq '{
    reviews: [.reviews[] | {author: .author.login, state, submittedAt, body}],
    comments: [.comments[] | {author: .author.login, createdAt, body}]
  }'
```

If prior reviews or PR comments exist, treat this as a **follow-up review**:
- Check which concerns and findings were raised before
- Verify whether they were addressed in new commits
- Focus on what changed since the last review

## Run the Code Review

Run the `code-review` skill with the PR as its review target. It owns diff collection, spec discovery, standards discovery, smell-baseline checks, and the independent Correctness, Standards, and Spec passes.

For a follow-up review, provide the prior review findings as additional context. Verify each prior concern against the new commits and distinguish resolved findings from findings that remain. Still inspect the complete current diff for regressions and new issues.

## Write the Review

Read [REVIEW-FORMAT.md](REVIEW-FORMAT.md) and use it to turn the `code-review` output into a human-readable PR review.

The posted review is not a raw dump of the three review axes, and it does not restate the diff. `code-review` owns the Correctness/Standards/Spec axis upstream; the posted review drops the axis and organizes the GitHub body by what the author needs to do:

1. **Must fix before merge** - blocking findings only.
2. **Should verify before merge** - important non-blocking findings and intent checks.
3. **Suggestions and notes** - suggestions, smells, confirmations, skipped axes, and no-finding notes in a collapsed `<details>` block.

Start with a verdict heading and a severity summary table, optionally one short alert for the single most important next step, then list findings by the hierarchy above. Put the final recommendation at the end. Do not add `What changed`, `Reviewed files`, `TL;DR`, or `Action checklist` sections - GitHub already shows the diff, and the findings already carry the actions.

The summary table counts by `code-review` severity (`⛔ blocking`, `⚠️ important`, `💡 suggestion`), which is the source of truth. Each finding is a single emoji-prefixed line plus a short prose paragraph. For example: 🔴 **Auth check skipped for expired tokens** — `AuthFilter.java:88`. The section supplies the severity and the emoji (🔴 Bug, 🟡 Risk, 🟠 Missing test, 🔵 Suggestion) supplies the category, so a finding does not repeat the severity word or the axis. The prose must still cover impact, evidence, and a fix. End with ✅ Approve or 🔄 Request Changes.

Do not promote code-smell judgments into blocking findings unless a documented repository standard independently makes them blocking.

End with one of:

> **✅ Approve** - no blocking correctness, standards, or spec findings remain.

> **🔄 Request Changes** - list the specific blocking findings that must be resolved.

Suggestions alone do not justify Request Changes.

An Approve draft may include important non-blocking findings when the recommendation clearly states that they are not blockers.

## Reviewer Attribution

Resolve the authenticated GitHub login before presenting or posting a draft:

```bash
gh api user --jq '.login'
```

Use that login in a blockquote footer as `@<github-login>` so the review identifies whose coding agent drafted it.

## Approval Gate

Present the full review as a formatted markdown document for the human to inspect. Do not post it yet.

Ask the human to approve, edit, or reject the draft. Only post the review after the human explicitly approves the exact review body and recommendation to submit.

## Post the Approved Review

After approval, save the exact approved review body to a temporary file and submit it with the matching recommendation:

```bash
REVIEW_FILE=$(mktemp -t submit-pr-review-XXXXXX.md)

# Use exactly one after writing the approved body to $REVIEW_FILE
gh pr review $PR --approve --body-file "$REVIEW_FILE"
gh pr review $PR --request-changes --body-file "$REVIEW_FILE"
```

If the human asks for edits before approval, revise the draft and repeat the approval gate.

## Output Format

Present the draft review as markdown. Include a note at the end:

> This review was drafted by @<github-login>'s coding agent.
>
> Approve it to have the agent post it to GitHub.
