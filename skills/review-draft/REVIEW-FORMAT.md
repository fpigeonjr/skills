# PR Review Format

Use this format when converting a `code-review` output into the GitHub PR review body. The goal is a readable GitHub PR review that tells the author what to do next, not a raw dump of the analysis.

## Principles

- **Author-first hierarchy:** organize by actionability before review taxonomy.
- **GitHub-native UX:** use GFM tables, task lists, alerts, emoji labels, and `<details>` blocks when they make the review easier to scan.
- **Progressive disclosure:** keep the main body short; hide confirmations, no-finding notes, and optional suggestions behind collapsible sections.
- **One finding, one decision:** every visible finding should make clear whether it blocks merge, needs verification, needs a test, or is optional.

## Severity and verdict labels

Use color and icon labels consistently. Keep the underlying `code-review` severity, but translate it into reviewer-friendly labels in the GitHub body.

| Label | Use for | Usually maps to |
| --- | --- | --- |
| 🔴 **Bug** | Concrete bug, regression, broken behavior, security flaw, or data-integrity issue. | `blocking` or `important` |
| 🟡 **Risk** | Risky behavior change, security/data/performance risk, or intent that needs confirmation. | `important` |
| 🟠 **Missing test** | Changed behavior that lacks meaningful regression or acceptance coverage. | `blocking` or `important` |
| 🔵 **Suggestion** | Clarity, maintainability, style, docs, or non-blocking smell feedback. | `suggestion` |

Recommendation labels:

- **✅ Approve** — no blocking findings remain; include the reason in one sentence.
- **🔄 Request Changes** — list the specific blocking issues that must be resolved.

## Skeleton

Use this copyable skeleton for real PR reviews. Replace placeholders and omit empty optional sections.

```markdown
## Review: ✅ Approve | 🔄 Request Changes

| Result | 🔴 Bugs | 🟡 Risks | 🟠 Missing tests | 🔵 Suggestions |
| --- | ---: | ---: | ---: | ---: |
| ✅ Approve | 0 | 0 | 0 | 0 |

> [!IMPORTANT]
> **Next step:** One sentence describing the most important author action, or omit this alert when there is no notable next step.

### TL;DR

- One sentence on the overall state of the PR.
- One sentence on the highest-risk area, if any.
- One sentence on what the author should do next.

### What changed

- Short, reviewer-friendly summary of area 1.
- Short, reviewer-friendly summary of area 2.

### Reviewed files

| File | Why it mattered |
| --- | --- |
| `path/to/file.ext` | Short description of the changed area. |

### Since the last review

| Status | Finding | Notes |
| --- | --- | --- |
| Resolved | Previous finding title | What changed |
| Still open | Previous finding title | What remains |
| New | New finding title | Why it matters |

### Action checklist

- [ ] Concrete author action or acknowledgement.
- [ ] Another concrete author action.

### Must fix before merge

#### 1. Short finding title

`path/to/file.ext:123` · 🔴 **Bug** · **Correctness** · **blocking**

**Why it matters:**
Concrete impact in one or two sentences.

**Evidence:**
Specific observed behavior, code path, standard, or spec text.

**Suggested fix:**
Focused remediation.

### Should verify before merge

#### 2. Short finding title

`path/to/file.ext:456` · 🟡 **Risk** · **Spec** · **important**

> [!WARNING]
> Optional one-sentence risk callout for high-impact non-blocking findings.

**Why it matters:**
Concrete impact in one or two sentences.

**Evidence:**
Specific observed behavior, code path, standard, or spec text.

**Suggested fix:**
Focused remediation.

<details>
<summary>🔵 Suggestions and notes</summary>

#### 3. Short finding title

`path/to/file.ext:789` · 🔵 **Suggestion** · **Standards** · **suggestion**

**Why it matters:**
Concrete impact in one or two sentences.

**Evidence:**
Specific observed behavior, code path, standard, or spec text.

**Suggested fix:**
Focused remediation.

#### Additional review notes

- Correctness: no additional findings.
- Standards: no documented-standard violations.
- Spec: no missing or out-of-scope behavior identified.

</details>

### Recommendation

**✅ Approve** — no blocking findings remain.

> This review was drafted by @<github-login>'s coding agent.
```

## Rendered example

This section intentionally renders the GitHub-flavored Markdown components so reviewers can inspect the UX directly in GitHub.

## Review: ✅ Approve

| Result | 🔴 Bugs | 🟡 Risks | 🟠 Missing tests | 🔵 Suggestions |
| --- | ---: | ---: | ---: | ---: |
| ✅ Approve | 0 | 1 | 0 | 2 |

> [!IMPORTANT]
> **Next step:** Confirm the remaining unauthenticated paths should now return 401. No blocking changes requested.

### TL;DR

- The main implementation looks solid and is covered by relevant tests.
- The highest-risk area is the broad auth behavior change.
- I would approve after the non-blocking verification below is acknowledged.

### What changed

- Added the new role/function/permission path behind the feature toggle.
- Changed unauthenticated user lookup from null-returning to 401-throwing behavior.
- Added the safe lookup helper for call sites that still need null-tolerant behavior.

### Reviewed files

| File | Why it mattered |
| --- | --- |
| `ContentUtils.java` | Changes unauthenticated user lookup behavior and adds the safe helper. |
| `ServiceExceptionHandler.java` | Maps the new unauthenticated exception to HTTP 401 and logs it. |
| `V55.2.1__IAEMOD-integrity-records-roles.sql` | Adds the integrity-records function, permissions, role, and mappings. |

### Action checklist

- [ ] Verify the remaining unauthenticated call sites should now return 401.
- [ ] Fix or accept the log-message formatting issue.
- [ ] Optional: de-duplicate the two user lookup helpers.

### Must fix before merge

No blocking findings.

### Should verify before merge

#### 1. Confirm remaining unauthenticated paths should now return 401

`ContentUtils.getLoggedInUserDetails()` · 🟡 **Risk** · **Correctness** · **important**

> [!WARNING]
> This is a behavior change across multiple endpoints. It appears intentional, but should be explicitly confirmed before merge.

**Why it matters:**
Several call sites still contain null-fallback branches that are now unreachable. If any of those endpoints were expected to keep their previous unauthenticated response, this PR changes API behavior.

**Evidence:**

| Location | Previous behavior | New behavior to confirm |
| --- | --- | --- |
| `CheckAccessService.java:129-132` | Returned empty `UserAttributes()` | Throws mapped 401 |
| `OTPService.java:119` | Threw `500 "Invalid Session (2)"` | Throws mapped 401 |

**Suggested fix:**
Confirm 401 is intended for these paths. If it is, remove the dead null-fallback branches in a follow-up or in this PR so the code reflects the new contract.

<details>
<summary>🔵 Suggestions and notes</summary>

#### 2. Preserve the unauthenticated exception message in logs

`ServiceExceptionHandler.java:167` · 🔵 **Suggestion** · **Correctness** · **suggestion**

**Why it matters:**
The SLF4J call has one `{}` placeholder but passes two values, so the exception message is not logged as intended.

**Evidence:**

```java
LOGGER.info("{} UnauthenticatedAccessException:", SERVICE_NAME, exception.getMessage())
```

**Suggested fix:**
Add a second `{}` placeholder or pass the exception object as the trailing argument.

#### 3. Consider de-duplicating user lookup logic

`ContentUtils.java` · 🔵 **Suggestion** · **Standards** · **suggestion**

**Why it matters:**
`getLoggedInUserDetails()` and `getLoggedInUserDetailsSafe()` are nearly identical except for the terminal null-vs-throw behavior.

**Evidence:**
Both helpers perform the same security-context extraction and differ only in whether the unauthenticated terminal path throws or returns `null`.

**Suggested fix:**
Extract the shared security-context lookup or have one method delegate to the other.

#### Additional review notes

- Migration inserts are idempotent.
- Toggle-off behavior degrades gracefully if migrated records are absent.
- No missing or out-of-scope behavior identified against the referenced acceptance criteria.

</details>

### Recommendation

**✅ Approve** — no blocking findings remain.

> This review was drafted by @fpigeonjr's coding agent.

## Hierarchy rules

Use this visible hierarchy in the posted PR review:

1. `## Review: ✅ Approve` or `## Review: 🔄 Request Changes`
2. Summary table with emoji severity counts.
3. Optional GFM alert for the single most important next step.
4. `### TL;DR`
5. `### What changed`
6. Optional `### Reviewed files` table for non-trivial PRs.
7. Optional `### Since the last review` for follow-up reviews.
8. `### Action checklist`
9. `### Must fix before merge`
10. `### Should verify before merge`
11. Collapsed `<details>` for `🔵 Suggestions and notes`.
12. `### Recommendation`

Group by actionability before axis:

- **Must fix before merge** — blocking findings only. These justify 🔄 Request Changes.
- **Should verify before merge** — important findings, intent checks, and behavior changes that do not justify Request Changes alone.
- **Suggestions and notes** — suggestions, smell findings, confirmations, skipped axes, and no-finding notes.

Preserve each finding's review axis (`Correctness`, `Standards`, `Spec`) as compact metadata on the finding line. Do not use the axes as the top-level PR review structure.

## Copilot code review deltas

GitHub Copilot code review is useful prior art, but `review-draft` should be more explicit about verdict and hierarchy.

Borrow these patterns from Copilot reviews:

- Start with a concise pull request overview before detailed findings.
- Include a compact `Reviewed files` table when it helps the author understand review coverage.
- Keep feedback concrete and tied to changed code.
- Prefer small, actionable comments over broad observations.
- Include focused suggested fixes whenever the remediation is clear.
- Treat review comments as normal GitHub review conversations that humans can reply to and resolve.

Differentiate `review-draft` from Copilot reviews:

- Copilot always leaves a **Comment** review; `review-draft` may submit ✅ Approve or 🔄 Request Changes after human approval.
- Copilot feedback often appears as inline comments; `review-draft` currently posts a top-level review body, so the body must summarize priority and next actions clearly.
- Copilot can provide one-click suggested changes in inline comments. Do not put GitHub ```suggestion fences in the top-level review body because they will not be applyable there. If `review-draft` later supports inline review comments, use suggestion fences only for small, directly replaceable code changes.
- Copilot may repeat comments on re-review; follow-up `review-draft` output should use `### Since the last review` to separate resolved, still-open, and new findings.

## GFM components to use

### Tables

Use tables for compact summaries and side-by-side comparisons. Good uses:

- Review result and severity counts.
- Reviewed files and why each file mattered.
- Before/after behavior.
- Affected endpoints or files.
- Follow-up review status.

Keep tables narrow. If a table needs paragraph-length cells, use bullets instead.

### Task lists

Use task lists only for concrete actions the author can complete or acknowledge.

```markdown
- [ ] Add a regression test for unauthenticated access.
- [ ] Confirm 401 is intended for the remaining call sites.
```

Do not create checkbox noise for observations that require no action.

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
<summary>🔵 Suggestions and notes</summary>

...

</details>
```

## Finding format

Each finding should be self-contained:

```markdown
#### N. Short finding title

`path/to/file.ext:123` · 🔴 **Bug** · **Correctness** · **blocking**

> [!WARNING]
> Optional one-sentence risk callout for high-impact non-blocking findings.

**Why it matters:**
Concrete impact in one or two sentences.

**Evidence:**
Specific observed behavior, code path, standard, or spec text.

**Suggested fix:**
Focused remediation.
```

Use descriptive finding titles. Do not start headings with file names unless the file name is the clearest title.

## Follow-up reviews

For follow-up PR reviews, add this section after `### What changed`:

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
- If the Spec axis was skipped, mention that once in `🔵 Suggestions and notes` with the reason.
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
