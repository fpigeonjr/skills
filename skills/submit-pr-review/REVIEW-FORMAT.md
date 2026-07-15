# PR Review Format

Use this format when converting a `code-review` output into the GitHub PR review body. The goal is a readable GitHub PR review that tells the author what to do next, not a raw dump of the analysis.

## Principles

- **Author-first hierarchy:** organize by actionability before review taxonomy.
- **No restating the diff:** do not summarize what the author changed. GitHub already shows the diff and file list. The review is the reviewer's output, not an echo of the PR.
- **GitHub-native UX:** use GFM tables, alerts, emoji labels, and `<details>` blocks when they make the review easier to scan.
- **Progressive disclosure:** keep the main body short; hide confirmations, no-finding notes, and optional suggestions behind collapsible sections.
- **One finding, one decision:** every visible finding should make clear whether it blocks merge, needs verification, or is optional.

## Severity and verdict labels

The summary table counts by `code-review` severity, which is the source of truth: `blocking`, `important`, `suggestion`. The emoji category label is an additional, finding-level cue — it is not what the summary counts.

| Summary count | Emoji on the finding | Use for |
| --- | --- | --- |
| ⛔ blocking | 🔴 **Bug** / 🟠 **Missing test** | Concrete bug, regression, broken behavior, security/data-integrity issue, or missing coverage that must be resolved before merge. |
| ⚠️ important | 🟡 **Risk** / 🔴 **Bug** / 🟠 **Missing test** | Risky behavior change, intent that needs confirmation, or a non-blocking defect worth verifying. |
| 💡 suggestion | 🔵 **Suggestion** | Clarity, maintainability, style, docs, or non-blocking smell feedback. |

Each finding is a single emoji-prefixed line plus a short prose paragraph. The section it sits under (`Must fix` / `Should verify` / `Suggestions`) conveys severity, and the emoji conveys the category, so the finding does not repeat the severity word or the review axis. `code-review` owns the Correctness/Standards/Spec axis upstream; `submit-pr-review` does not restate it. A blocking Standards or Spec finding still uses 🔴.

Recommendation labels:

- **✅ Approve** — no blocking findings remain; include the reason in one sentence.
- **🔄 Request Changes** — list the specific blocking issues that must be resolved.

## Skeleton

Use this copyable skeleton for real PR reviews. Replace placeholders and omit empty optional sections.

```markdown
## Review: ✅ Approve | 🔄 Request Changes

| Result | ⛔ blocking | ⚠️ important | 💡 suggestion |
| --- | ---: | ---: | ---: |
| ✅ Approve | 0 | 0 | 0 |

> [!NOTE]
> One sentence on the single most important next step, or omit this alert entirely when there is nothing notable.

### Since the last review

| Status | Finding | Notes |
| --- | --- | --- |
| ✅ Resolved | Previous finding title | What changed |
| 🔄 Still open | Previous finding title | What remains |
| 🆕 New | New finding title | Why it matters |

### Must fix before merge

🔴 **Short finding title** — `path/to/file.ext:123`
One short prose paragraph: what is wrong, its concrete impact, the evidence, and the focused fix, in a sentence or two.

### Should verify before merge

🟡 **Short finding title** — `path/to/file.ext:456`
One short prose paragraph covering impact, evidence, and the action to confirm.

<details>
<summary>💡 Suggestions and notes</summary>

🔵 **Short finding title** — `path/to/file.ext:789`
One short prose paragraph with the impact and the suggested change.

- Spec: no missing or out-of-scope behavior identified.

</details>

### Recommendation

**✅ Approve** — no blocking findings remain.

> This review was drafted by @<github-login>'s coding agent.
```

## Rendered example

This section intentionally renders the GitHub-flavored Markdown components so reviewers can inspect the UX directly in GitHub.

## Review: 🔄 Request Changes

| Result | ⛔ blocking | ⚠️ important | 💡 suggestion |
| --- | ---: | ---: | ---: |
| 🔄 Request Changes | 1 | 1 | 2 |

> [!NOTE]
> One blocking auth bug to fix; the rest are non-blocking.

### Must fix before merge

🔴 **Auth check skipped for expired tokens** — `AuthFilter.java:88`
Expired tokens pass the filter instead of being rejected, so a stale session keeps working past expiry. The `isValid()` branch returns early before the expiry comparison runs. Move the expiry check ahead of the early return, or fold it into `isValid()`.

### Should verify before merge

🟡 **Unauthenticated lookups now return 401 across multiple endpoints** — `ContentUtils.java:129`
Several call sites still have null-fallback branches that are now unreachable. If any of those endpoints were expected to keep their previous unauthenticated response, this silently changes API behavior. Confirm 401 is intended for `CheckAccessService` and `OTPService`, then remove the dead branches so the code reflects the new contract.

<details>
<summary>💡 Suggestions and notes</summary>

🔵 **Exception message dropped from logs** — `ServiceExceptionHandler.java:167`
The SLF4J call has one `{}` placeholder but passes two values, so the exception message never makes it into the log line. Add a second placeholder or pass the exception as the trailing argument.

🔵 **Duplicated user-lookup helpers** — `ContentUtils.java`
`getLoggedInUserDetails()` and `getLoggedInUserDetailsSafe()` are near-identical except for the terminal null-vs-throw behavior. Extract the shared security-context lookup, or have one delegate to the other.

- Spec: no missing or out-of-scope behavior identified.

</details>

### Recommendation

**🔄 Request Changes** — the expired-token auth bypass must be fixed before merge.

> This review was drafted by @fpigeonjr's coding agent.

## Hierarchy rules

Use this visible hierarchy in the posted PR review:

1. `## Review: ✅ Approve` or `## Review: 🔄 Request Changes`
2. Summary table with `code-review` severity counts (`⛔ blocking`, `⚠️ important`, `💡 suggestion`).
3. Optional GFM alert for the single most important next step.
4. Optional `### Since the last review` for follow-up reviews.
5. `### Must fix before merge`
6. `### Should verify before merge`
7. Collapsed `<details>` for `💡 Suggestions and notes`.
8. `### Recommendation`

Do not add `What changed`, `Reviewed files`, `TL;DR`, or `Action checklist` sections. The severity table and the findings already carry the summary and the actions; anything else restates the diff or duplicates the findings.

Group by actionability. The section supplies the severity, so findings do not repeat it:

- **Must fix before merge** — blocking findings only. These justify 🔄 Request Changes.
- **Should verify before merge** — important findings, intent checks, and behavior changes that do not justify Request Changes alone.
- **Suggestions and notes** — suggestions, smell findings, confirmations, skipped axes, and no-finding notes.

`code-review` owns the Correctness/Standards/Spec axis upstream. Do not carry the axis into the posted PR review — the section and the finding's prose already tell the author what they need.

## Copilot code review deltas

GitHub Copilot code review is useful prior art, but `submit-pr-review` should be more explicit about verdict and hierarchy.

Borrow these patterns from Copilot reviews:

- Keep feedback concrete and tied to changed code.
- Prefer small, actionable comments over broad observations.
- Include focused suggested fixes whenever the remediation is clear.
- Treat review comments as normal GitHub review conversations that humans can reply to and resolve.

Do not borrow Copilot's `Reviewed files` / `Pull request overview` summary sections; they restate the diff and add length without reviewer value.

Differentiate `submit-pr-review` from Copilot reviews:

- Copilot always leaves a **Comment** review; `submit-pr-review` may submit ✅ Approve or 🔄 Request Changes after human approval.
- Copilot feedback often appears as inline comments; `submit-pr-review` currently posts a top-level review body, so the body must summarize priority and next actions clearly.
- Copilot can provide one-click suggested changes in inline comments. Do not put a `suggestion` code fence in the top-level review body because it will not be applicable there. If `submit-pr-review` later supports inline review comments, use `suggestion` fences only for small, directly replaceable code changes.
- Copilot may repeat comments on re-review; follow-up `submit-pr-review` output should use `### Since the last review` to separate resolved, still-open, and new findings.

## GFM components to use

### Tables

Use tables for compact summaries and side-by-side comparisons. Good uses:

- Review result and severity counts.
- Before/after behavior inside a finding's evidence.
- Follow-up review status.

Keep tables narrow. If a table needs paragraph-length cells, use bullets instead.

### Alerts

Use GFM alerts sparingly:

- `[!IMPORTANT]` for the one most important next step.
- `[!WARNING]` for a non-blocking but risky behavior change.
- `[!NOTE]` for helpful context that prevents misunderstanding.

Do not stack multiple alerts in a row. If everything is highlighted, nothing is highlighted.

### Collapsible details

Use `<details>` for lower-priority material:

- 🔵 Suggestions.
- No-finding notes.
- Evidence that is useful but lengthy.
- Prior-review resolution detail.

The summary line should tell the reader exactly what is inside.

```markdown
<details>
<summary>💡 Suggestions and notes</summary>

...

</details>
```

## Finding format

Each finding is one emoji-prefixed title line plus a short prose paragraph:

```markdown
🔴 **Short finding title** — `path/to/file.ext:123`
One short paragraph that covers the impact, the evidence, and the focused fix. Keep it to a sentence or two.
```

Rules:

- Lead with the emoji category (🔴 / 🟡 / 🟠 / 🔵), then a bold descriptive title, then an em dash and the `file:line` location.
- The prose must still cover impact, evidence, and a fix — just without labeled `Why it matters` / `Evidence` / `Suggested fix` headers.
- Do not include the review axis or the severity word; the section supplies severity and `code-review` owns the axis.
- Use a fenced code block or a small table inside a finding only when the evidence genuinely needs it. Prefer prose.
- For a high-impact non-blocking finding, an optional `> [!WARNING]` line may follow the finding, but use it sparingly.

## Follow-up reviews

For follow-up PR reviews, add this section directly after the summary table (or its optional alert):

```markdown
### Since the last review

| Status | Finding | Notes |
| --- | --- | --- |
| ✅ Resolved | Missing auth regression test | Added coverage in `...` |
| 🔄 Still open | 401 behavior verification | Still needs author confirmation |
| 🆕 New | Log message placeholder mismatch | Introduced in latest commit |
```

Only include categories that exist. Keep the rest of the review focused on current state, not review history.

## Empty-state rules

- If there are no blocking findings, write `No blocking findings.` under `Must fix before merge`.
- If there are no important findings, omit `Should verify before merge`.
- If there are no suggestions or notes, omit the `<details>` block.
- If the Spec axis was skipped, mention that once in `💡 Suggestions and notes` with the reason.
- Do not include “no finding” items in the main findings lists.

## Attribution footer

Resolve the authenticated GitHub login with `gh api user --jq '.login'` and end every draft with:

```markdown
> This review was drafted by @<github-login>'s coding agent.
```

Do not hard-code the login except in rendered examples.

## Tone

- Sound like a helpful teammate reviewing a PR.
- Be direct about risk, but do not overstate uncertainty.
- Prefer short paragraphs and bullets.
- Use “please” sparingly.
- Approve reviews can include follow-ups, but must clearly say they are non-blocking.
