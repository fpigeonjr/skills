---
name: promote-flux-image
description: Safely promote a confirmed container image tag from one Flux HelmRelease environment to another (typically staging to production) by copying only the verified source tag into the target manifest. Use when the user wants to promote an image, bump a production tag to match staging, or says things like "promote this to prod", "sync the prod image tag with staging", or "cut a production release from the staging image".
argument-hint: "[source env] [target env] [HelmRelease path or name]"
allowed-tools: Read Grep Glob Bash Edit
---

# Promote Flux Image

Copy a **confirmed** container image tag from a source Flux `HelmRelease` (e.g. staging) to a target one (e.g. production). This is a copy operation, never an inference — the target gets exactly the source's tag, nothing computed or guessed.

## Inputs / Preconditions

Before starting, resolve:

- **Source environment** and **target environment** (e.g. `staging` → `production`), or their manifest paths.
- **Which HelmRelease / image** to promote, if the repo has more than one.
- Confirmation that the source tag has already been verified/approved for promotion (this skill does not itself judge readiness — if the user hasn't said the source is confirmed-good, ask).

If any of these are ambiguous, ask one question at a time rather than guessing.

## 1. Inspect Source and Target Manifests

Locate both HelmRelease manifests (commonly under `clusters/<env>/...` or similar Flux kustomization layout):

```bash
grep -rl "kind: HelmRelease" --include="*.yaml" <repo-root>
```

Read both the source and target manifest in full. Identify the `spec.values.image.repository` (or equivalent image field — field names vary by chart) and the tag field for each.

**Guard — image repository equality**: the source and target must reference the **same image repository**. If the repositories differ, stop and report — this is not a safe promotion, it's a different image. Do not proceed.

## 2. Copy the Tag — Never Infer

Read the **exact** tag string from the source manifest. Do not:

- Bump a version number yourself
- Infer the "next" tag from a changelog, git log, or naming pattern
- Normalize or reformat the tag string

The target's new tag value is a literal copy-paste of the source's current tag value. If the source tag looks unusual (e.g. a short SHA, `latest`, a dirty/dev suffix), surface that to the user before proceeding rather than silently promoting it.

## 3. Authorization / Deployment Request Guard

Promoting to production is a deployment action. Before editing anything:

- Confirm the user has explicitly asked for this promotion (not just discussion of what the tag is).
- If the target environment is production (or otherwise flagged as sensitive in repo docs/AGENTS.md), explicitly state what will change (image, source tag, target file) and get confirmation before editing.

If there is no clear authorization, stop and ask.

## 4. Existing PR vs New Branch/PR

Check whether a PR already exists for this promotion:

```bash
git status
git branch --show-current
gh pr view --json number,url,headRefName,state 2>/dev/null
```

- If an open PR already targets this promotion (e.g. opened by automation, or a prior attempt), prefer updating that branch/PR over opening a duplicate.
- Otherwise, create a new branch off the correct base and open a new PR following this repo's normal branching convention (see `start-ticket` skill if one is in use).

Do not reuse an unrelated branch or an already-merged/closed PR.

## 5. Minimal Target-Only Edit

Edit **only** the tag field in the **target** manifest. Do not touch:

- The source manifest
- Any other field in the target manifest (replicas, resources, other image fields, etc.)
- Unrelated files

One field, one value, one file (unless the repo structure genuinely requires the same tag in multiple target files — if so, list them explicitly to the user first).

## 6. Validate the Diff

Before committing:

```bash
git diff
```

Confirm the diff shows exactly one tag value change in the target file, old value matches what you read in step 1/2, and new value matches the source tag exactly. Validate YAML structure is intact (no stray indentation/quoting changes):

```bash
python3 -c "import yaml,sys; yaml.safe_load(open(sys.argv[1]))" <target-file>
```

If the diff shows anything beyond the single tag change, or YAML parsing fails, stop and fix before continuing — do not commit a broken or oversized diff.

## 7. Commit, Push, Verify

```bash
git add <target-file>
git commit -m "Promote <image> to <tag> in <target-env>"
git push
```

Verify the push landed and the remote branch reflects the expected single-line change:

```bash
git log -1 --stat
git diff origin/<base-branch>...<branch> -- <target-file>
```

## 8. PR Body Update

If opening a new PR, state clearly in the body:

- Image repository being promoted
- Source environment and the exact tag copied
- Target environment
- A note that the tag was copied verbatim from the already-verified source, not inferred

If updating an existing PR, edit its body/description to reflect the current tag being promoted (don't leave stale tag values in the PR description):

```bash
gh pr edit <PR> --body "<updated body>"
```

## 9. Flux / Production Caveat

Note explicitly in your report (and PR body, if production-facing) that:

- Flux reconciles on its own schedule/trigger — merging this PR does not deploy immediately; the change takes effect once Flux reconciles the target cluster.
- This skill only prepares and submits the manifest change. It does not trigger, force, or verify a Flux reconciliation, and it does not confirm the rollout succeeded in-cluster.
- For production targets, deployment is only as safe as the source tag's verification — this skill trusts that verification, it doesn't redo it.

## Report Template

```
Promotion: <image repository>
Source: <source-env> → tag <exact-tag>
Target: <target-env> (<target-file>)
Repo equality check: OK (same image repository)
Diff: single tag field changed, <old-tag> → <new-tag>
YAML validation: passed
Branch/PR: <new|existing> — <PR URL>
Commit: <sha>
Flux note: change will apply on next Flux reconciliation of <target-env>; not verified in-cluster.
```

## Failure / Stop Conditions

Stop and report (do not guess or work around) if:

- Source and target image repositories differ
- The source tag cannot be found or is ambiguous (e.g. multiple image blocks, unclear which applies)
- No clear authorization for a production/sensitive promotion
- `git diff` shows changes beyond the single target tag field
- YAML validation fails after the edit
- Push fails, or the remote branch doesn't reflect the expected diff
- An existing PR is in a merged/closed state and can't be reused
