---
name: submit-draft-pr
description: Create a draft GitHub pull request with the repo's PR template fully populated. Analyzes the branch diff, fills every template section, applies labels, and assigns the PR to the authenticated user. Use when the user wants to open a PR, create a pull request, submit their branch for review, or says things like "make a PR", "open a PR", "submit this for review", or "I'm ready to create a pull request".
argument-hint: "[issue-number] [--base base-branch]"
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

Collect the full scope of changes since the branch diverged from the base. If `$ARGUMENTS` includes `--base <branch>`, use that branch as the PR base. Otherwise use the repo default branch:

```bash
# Optional: parse --base <branch> from ARGUMENTS; ARGUMENTS may also include an issue number
BASE="$(gh repo view --json defaultBranchRef --jq '.defaultBranchRef.name')"

# If the user provided --base, override BASE with that branch
# Example parser for shell workflows:
while [ "$#" -gt 0 ]; do
  case "$1" in
    --base)
      BASE="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

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

## Fetch the Repo PR Template

Always use the repository's PR template as the starting point for the body. Prefer the template that exists in the working tree or on the PR base branch; only fall back to a free-form body if no template can be found.

Check all standard GitHub template locations, including template directories:

```bash
# First try templates present in the checked-out repo
find .github docs -maxdepth 2 \
  \( -iname 'pull_request_template.md' -o -path '.github/PULL_REQUEST_TEMPLATE/*.md' \) \
  -type f 2>/dev/null

# Then try the base branch, in case the file is not present locally
for path in \
  .github/pull_request_template.md \
  .github/PULL_REQUEST_TEMPLATE.md \
  docs/pull_request_template.md
  do
    git show "$BASE:$path" 2>/dev/null && break
  done

# Also list directory-style templates on the base branch, if any
git ls-tree -r --name-only "$BASE" .github/PULL_REQUEST_TEMPLATE 2>/dev/null
```

If multiple templates exist, choose the one that matches the change type. If the correct choice is not obvious, ask the user which template to use.

If the template is only available from GitHub, fetch it from the base branch ref:

```bash
OWNER_REPO="$(gh repo view --json nameWithOwner --jq '.nameWithOwner')"
gh api "repos/$OWNER_REPO/contents/.github/pull_request_template.md?ref=$BASE" \
  --jq '.content' | base64 -d 2>/dev/null \
|| gh api "repos/$OWNER_REPO/contents/.github/PULL_REQUEST_TEMPLATE.md?ref=$BASE" \
  --jq '.content' | base64 -d 2>/dev/null \
|| gh api "repos/$OWNER_REPO/contents/docs/pull_request_template.md?ref=$BASE" \
  --jq '.content' | base64 -d 2>/dev/null
```

Save the selected template to a temporary file and populate that file. Do not pass a hand-written body directly to `gh pr create` unless no repo template exists.

If no template exists, write a concise description covering what changed, why, and any relevant context.

## Populate the Template

Fill **every section** of the template. Do not submit a blank or partially filled template.

### Typical sections

**What changed** — high-level summary of what the PR does and why, followed by a breakdown by file or area. Focus on *what* changed and *why*, not line-by-line narration.

**Issue / Closes** — if `$ARGUMENTS` includes a numeric issue number, append `Closes #<issue-number>` in the linked issues section (or at the end if no such section exists). Ignore `--base <branch>` when extracting the issue number.

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

Write the populated template body to a file so Markdown, checkboxes, and comments survive unchanged:

```bash
BODY_FILE="$(mktemp -t pr-body.XXXXXX.md)"
cat >"$BODY_FILE" <<'EOF'
<populated repo template body>
EOF
```

Confirm with the user before creating — show the base branch, selected template path (or "none found"), title, labels, and a brief summary of what the body will contain. Ask "Ready to create?"

```bash
gh pr create \
  --draft \
  --base "$BASE" \
  --title "the pr title" \
  --assignee "@me" \
  --body-file "$BODY_FILE"
```

Use `--body-file`, not inline `--body`, for reliability. Do not use `--template` for the final create command because the body has already been populated from the repo template.

Report the PR URL when done.

## Note on Copilot Reviews

Print this exact note after creating the PR:

> **ACTION REQUIRED:** GitHub does not support requesting a Copilot review via the API. Please open the PR in your browser and add Copilot as a reviewer manually from the Reviewers panel.
