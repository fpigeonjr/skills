---
name: submit-draft-pr
description: Create a draft GitHub pull request with the repo's PR template fully populated. Analyzes the branch diff, fills every template section, applies labels, and assigns the PR to the authenticated user. Use when the user wants to open a PR, create a pull request, submit their branch for review, or says things like "make a PR", "open a PR", "submit this for review", or "I'm ready to create a pull request".
argument-hint: "[issue-number]"
allowed-tools: Read, Grep, Glob, Bash
---

# Submit Draft PR

## Check for Existing PR

Before creating anything, check if a PR already exists for this branch:

```bash
gh pr view --json number,url,state 2>/dev/null
```

If a PR exists, report its URL and state — do not create a duplicate.

## Gather Branch Context

Collect the full scope of changes since the branch diverged from the base:

```bash
# Determine base (default: main)
BASE="${ARGUMENTS:-main}"
# If ARGUMENTS looks like an issue number (numeric), base is main
BASE="main"

# All commits on this branch
git log "$BASE"..HEAD --oneline

# Changed files with stats
git diff "$BASE"..HEAD --stat

# Full diff
git diff "$BASE"..HEAD

# Recent merged PRs for style reference
gh pr list --state merged --limit 5 --json title,body
```

Read the full diff carefully before writing anything.

## Fetch the PR Template

```bash
# Try lowercase first, then uppercase
gh api repos/{owner}/{repo}/contents/.github/pull_request_template.md \
  --jq '.content' | base64 -d 2>/dev/null \
|| gh api repos/{owner}/{repo}/contents/.github/PULL_REQUEST_TEMPLATE.md \
  --jq '.content' | base64 -d 2>/dev/null
```

If no template exists, write a concise description covering what changed, why, and any relevant context.

## Populate the Template

Fill **every section** of the template. Do not submit a blank or partially filled template.

### Typical sections

**What changed** — high-level summary of what the PR does and why, followed by a breakdown by file or area. Focus on *what* changed and *why*, not line-by-line narration.

**Issue / Closes** — if `$ARGUMENTS` is a numeric issue number, append `Closes #$ARGUMENTS` in the linked issues section (or at the end if no such section exists).

**How to test** — concrete, actionable steps a reviewer can follow to verify the change. Include specific test commands. If there are UI changes, include manual verification steps too.

**Checklist / Definition of Done** — check items you can verify from the diff. Leave others for the author to confirm.

**Screenshots** — if backend-only, write "N/A — backend changes only". If there are UI changes, note that screenshots should be added.

## Detect and Apply Labels

```bash
# List available labels
gh label list --json name,description

# Apply relevant labels based on change type
gh pr create ... --label "bug" --label "enhancement"
```

Skip labeling if the right labels cannot be determined with confidence.

## Create the Draft PR

Extract a short PR title (under 70 characters) from the changes.

Confirm with the user before creating — show the title and a brief summary of what the body will contain. Ask "Ready to create?"

```bash
gh pr create \
  --draft \
  --title "the pr title" \
  --assignee "@me" \
  --body "$(cat <<'EOF'
<populated template body>
EOF
)"
```

Report the PR URL when done.

## Note on Copilot Reviews

Print this exact note after creating the PR:

> **ACTION REQUIRED:** GitHub does not support requesting a Copilot review via the API. Please open the PR in your browser and add Copilot as a reviewer manually from the Reviewers panel.
