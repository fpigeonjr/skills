---
name: copilot-models
description: Polls GitHub Copilot's live model catalog through Pi's stored Copilot token, compares it with what Pi can select, and audits the Copilot model tiers and subagent task-model preferences against it. Use when the user asks what Copilot models are available, wants a fresh model poll, asks whether the Copilot tier list or task-model routing is still right, mentions Copilot billing or limits, or says things like "poll the copilot models" or "check our tiers".
argument-hint: "[--all]"
allowed-tools: Read Grep Glob Bash Edit
---

# Copilot Models

Read-only audit by default. Change config only after explicit approval of the exact change (step 5).

## Quick start

```bash
python3 <skill-dir>/scripts/copilot_models.py --check <model-id>:<thinking> github-copilot/<model-id>
```

Requires `python3` (standard library only). The script reads the Copilot token from `$PI_CODING_AGENT_DIR/auth.json`. It sends the token only to an allowlisted `*.githubcopilot.com` host over HTTPS, refuses redirects, and never prints it.

Rules for the agent:

- Never `cat` or `read` `auth.json`, and never echo or reuse the token.
- Never add `--allow-host` on your own initiative. Add it only for a GitHub Enterprise host the user explicitly names.

Exit codes:

- `2`: auth or config problem. Ask the user to start a Pi session on any `github-copilot` model, which refreshes the token, then rerun.
- `3`: network or response error.

Other flags: `--all` includes unavailable models, `--json` gives machine-readable output, `--no-pi` skips the `pi --list-models` check, and `--agent-dir DIR` overrides the Pi config directory.

## Workflow

1. **Collect current refs.** Each source feeds the `--check` list:
   - **Interactive tiers.** In `$PI_CODING_AGENT_DIR/extensions/model-tiers.ts`, find the family whose `provider` is `github-copilot`. Note each tier's `model` and `thinking`.
   - **Subagent routing.** In `$PI_CODING_AGENT_DIR/herdr-agents/config.json`, record **all** of `models.tasks` (every category, not just Copilot refs) and `models.agents`. An empty `models.tasks` is not a defect, because launches fall back to role defaults, `models.agents`, `models.default`, then the parent model. It only matters if the user launches with `task:<category>` values, which then have nothing to resolve to.
   - **Docs.** Note tier tables in `AGENTS.md` that mirror the tiers.
2. **Run the script** with every Copilot ref as `ID:THINKING` under `--check`.
3. **Triage refs.**
   - Anything other than `ok` needs action or a stated reason to keep it.
   - `UNAVAILABLE`, `MISSING` and `UNSUPPORTED-THINKING` are defects. Pi clamps an unsupported level to a supported one, so the tier silently runs at a different level.
   - `NOT-IN-PI` names its cause:
     - Excluded by Pi's saved account availability: the user should log in to GitHub Copilot in Pi again.
     - Absent from Pi's catalog: run `pi update --models`. Bare `pi update` updates Pi itself; never run it for this.
   - `VERIFY-THINKING` and `PREVIEW` are warnings to raise with the user.
   - If the drift section reports that the Pi registry was not checked or failed, say that selectability is unverified.
4. **Shortlist alternatives provisionally.**
   - Copilot's `category` (`lightweight` / `versatile` / `powerful`) roughly parallels the instant / thinking / pro tiers.
   - Category, vendor, recency, and Pi's list price are shortlisting signals, not evidence of task quality or latency. Present candidates as options, ask for the user's workload preferences, and never call a model "best" on catalog data alone.
   - Task categories (coding, review, recon, qa, architecture, docs) describe the kind of work, not its difficulty. Rank each category by fit for that work.
   - For `review`, include a vendor that differs from the main `coding` choice.
5. **Report, then apply only on approval.**
   - **Report:** the live table trimmed to what matters, billing notes verbatim, drift, ref statuses, and a tier table `| tier | current | status | candidates |`.
   - **Tiers:** edit the Copilot family entry in `model-tiers.ts` (`model`, `thinking`, `short`) and any mirrored `AGENTS.md` table. The user then runs `/reload`.
   - **Task models:** load the `pi-herdr-agents` skill first and follow its write contract. Unless the user approves dropping categories, send the complete merged `tasks` map, because omitted categories are deleted. Include `tasksMeta: {generatedAt, method}`, a `basis` whose `kind` equals `method`, and `expectedConfigRevision` when a revision is available. The user then runs `/reload`.

## Interpreting the output

- **Availability mirrors Pi's own rule.** A model counts as available only if it supports tool calls and is picker-enabled and not policy-disabled, or meets the individual-account policy fallback. Pi's saved `availableModelIds` in `auth.json` is refreshed only at login or token refresh, so "saved account availability differs" means Pi's view is stale.
- **Selectability and thinking levels.** Selectability is checked with `pi --list-models`, run against the same agent directory. Thinking levels apply Pi's supported-level rule to Pi's catalog cache (`models-store.json`), as do prices and limit diffs. When the cache lacks a model, the script reports it as unverified instead of guessing.
- **Limit diffs.** Copilot's limits are authoritative. A diff matters only when Pi's figure is larger than live, and the script marks those rows "Pi larger":
  - **Context:** Pi's compaction may trigger too late.
  - **Output:** Pi may request more output tokens than Copilot advertises.

  Diffs where Pi's figure is smaller are informational. Don't hand-edit Pi's catalog cache.
- **Prices are estimates, not the user's bill.** `Pi list $` columns are list prices per million tokens from Pi's catalog cache, useful for relative comparison only. Org-managed seats may bill in credits at a different rate.
- **Billing notes come from the API.** They are Copilot's own `warning_message` text and show whether premium-request multipliers or usage-based billing apply. Spending caps for org-managed seats appear on the user's GitHub Copilot usage page, not in the API.
