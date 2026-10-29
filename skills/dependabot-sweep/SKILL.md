---
name: dependabot-sweep
description: Sweeps open Dependabot PRs across the GSA design-library fleet, classifies CI and Angular compatibility, and submits approvals only after human confirmation. Use when the user asks to sweep Dependabot PRs, triage fleet dependency updates, or approve eligible Dependabot updates in GSA design-library repositories.
allowed-tools: Read Bash
---

# Dependabot Sweep

## Run the sweep

Use the existing script in `~/Code/gsa-angular-upgrade-dashboard`; do not reimplement the sweep. If the repo or script is missing, report the missing path and stop. On execution failure, report the error and stop rather than substituting an ad hoc sweep.

```bash
cd ~/Code/gsa-angular-upgrade-dashboard &&
  test -f dashboard/dependabot-sweep.mjs &&
  node dashboard/dependabot-sweep.mjs --json
```

CLI: `node dashboard/dependabot-sweep.mjs [--json] [--max-angular <N>]`. The default ceiling is 21, matching the fleet's Angular pin. Do not raise the ceiling to make blocked PRs eligible; an override requires explicit confirmation of a changed pin.

The fleet comes from the dashboard repo's `dashboard/lib.mjs` and appears in the script output; do not enumerate repositories manually.

## Present the results

Use the script's buckets, not a replacement classification. Here, green means every check is `SUCCESS`, `NEUTRAL`, or `SKIPPED`; no checks is pending, not green.

- **`candidate`** — green, no Angular-family major above the ceiling. Present repo/number, title, URL, base branch, mergeability, review decision, and `mergeStateStatus`. `BLOCKED` usually means a required review or a required check that hasn't reported; the script only sees reported checks. Candidates are eligible for consideration, not automatic approval.
  - Skip PRs with `reviewDecision: APPROVED`; list them as already approved.
  - Flag `mergeable: UNKNOWN` for human judgement; do not treat it as mergeable. Surface other mergeability or review concerns too.
  - Flag semver-major non-Angular updates (e.g. Babel 8 or postcss-import 17) for a human look. Use titles and, where needed, `gh pr view <n> -R GSA/<repo> --json title,body` or `gh pr diff` for evidence. The JSON has no general non-Angular bump list; label unclear versions unverified rather than guessing.
- **`angular-blocked`** — green but bumps an Angular-family package above the ceiling. List offending packages and `from` → `to` versions from `angularBumps`, including `source` when useful. Never approve while pinned. Mention these as possible later close/ignore decisions; an Angular-major Dependabot ignore rule is a suggestion only, not an action.
- **`pending`** — checks running or absent. List briefly; do not approve.
- **`red`** — failing checks. Group PR links by `failingChecks` name and summarize recurring patterns (e.g. DAST, E2E, Lint). Do not diagnose each PR or infer causes from names alone; offer diagnosis as a follow-up.

JSON fields: `repo`, `number`, `title`, `url`, `baseRefName`, `mergeable`, `mergeStateStatus`, `reviewDecision`, `bucket`, `failingChecks`, and `angularBumps[{name,from,to,source}]`.

## Human-gated PR reviews

Propose the exact candidate list as `GSA/<repo>#<number>` with URLs and any judgement flags. Ask for explicit human approval of that exact list before posting any PR review; a general request to run a sweep is not approval. Omit already-approved PRs. Get explicit confirmation of flagged judgement items, not blanket assumed consent.

For each authorized PR only:

```bash
gh pr review <n> -R GSA/<repo> --approve -b '<evidence-based approval summary>'
```

Keep the body factual: CI status and Angular ceiling compatibility are not proof of full correctness. Report successful approvals and any failures without claiming unposted reviews succeeded.

Never merge, enable auto-merge, rerun CI, close PRs, or edit Dependabot configuration without separate explicit approval for that action. End with bucket counts, PR links, approvals posted/skipped, and outstanding human decisions.
