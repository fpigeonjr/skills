# PR Review Format

Use this format when converting a `code-review` output into the GitHub PR review body. The goal is a readable GitHub PR review that tells the author what to do next, not a raw dump of the analysis.

## Principles

- **Author-first hierarchy:** organize by actionability before review taxonomy.
- **GitHub-native UX:** use GFM tables, task lists, alerts, and `<details>` blocks when they make the review easier to scan.
- **Progressive disclosure:** keep the main body short; hide confirmations, no-finding notes, and optional suggestions behind collapsible sections.
- **One finding, one decision:** every visible finding should make clear whether it blocks merge, needs verification, or is optional.

## Template

```markdown
## Review: Approve | Request Changes

| Result | Blocking | Needs verification | Suggestions |
| --- | ---: | ---: | ---: |
| Approve | 0 | 1 | 2 |

> [!IMPORTANT]
> **Next step:** Confirm the unauthenticated paths below should now return 401. No blocking changes requested.

### TL;DR

- The main implementation looks solid and is covered by relevant tests.
- The highest-risk area is the broad auth behavior change.
- I would approve after the non-blocking verification below is acknowledged.

### What changed

- Added the new role/function/permission path behind the feature toggle.
- Changed unauthenticated user lookup from null-returning to 401-throwing behavior.
- Added the safe lookup helper for call sites that still need null-tolerant behavior.

### Action checklist

- [ ] Verify the remaining unauthenticated call sites should now return 401.
- [ ] Fix or accept the log-message formatting issue.
- [ ] Optional: de-duplicate the two user lookup helpers.

### Must fix before merge

No blocking findings.

### Should verify before merge

#### 1. Confirm remaining unauthenticated paths should now return 401

`ContentUtils.getLoggedInUserDetails()` · **Correctness** · **important**

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
<summary>Suggestions and notes</summary>

#### 2. Preserve the unauthenticated exception message in logs

`ServiceExceptionHandler.java:167` · **Correctness** · **suggestion**

**Why it matters:**
The SLF4J call has one `{}` placeholder but passes two values, so the exception message is not logged as intended.

**Suggested fix:**
Add a second `{}` placeholder or pass the exception object as the trailing argument.

#### 3. Consider de-duplicating user lookup logic

`ContentUtils.java` · **Standards** · **suggestion**

**Why it matters:**
`getLoggedInUserDetails()` and `getLoggedInUserDetailsSafe()` are nearly identical except for the terminal null-vs-throw behavior.

**Suggested fix:**
Extract the shared security-context lookup or have one method delegate to the other.

#### Additional review notes

- Migration inserts are idempotent.
- Toggle-off behavior degrades gracefully if migrated records are absent.
- No missing or out-of-scope behavior identified against the referenced acceptance criteria.

</details>

### Recommendation

**Approve** — no blocking findings remain.
```

## Hierarchy rules

Use this visible hierarchy in the posted PR review:

1. `## Review: <verdict>`
2. Summary table with counts.
3. Optional GFM alert for the single most important next step.
4. `### TL;DR`
5. `### What changed`
6. Optional `### Since the last review` for follow-up reviews.
7. `### Action checklist`
8. `### Must fix before merge`
9. `### Should verify before merge`
10. Collapsed `<details>` for `Suggestions and notes`.
11. `### Recommendation`

Group by actionability before axis:

- **Must fix before merge** — blocking findings only. These justify Request Changes.
- **Should verify before merge** — important findings, intent checks, and behavior changes that do not justify Request Changes alone.
- **Suggestions and notes** — suggestions, smell findings, confirmations, skipped axes, and no-finding notes.

Preserve each finding's review axis (`Correctness`, `Standards`, `Spec`) as compact metadata on the finding line. Do not use the axes as the top-level PR review structure.

## GFM components to use

### Tables

Use tables for compact summaries and side-by-side comparisons. Good uses:

- Review result/counts.
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

- Suggestions.
- No-finding notes.
- Evidence that is useful but lengthy.
- Prior-review resolution detail.

The summary line should tell the reader exactly what is inside.

```markdown
<details>
<summary>Suggestions and notes</summary>

...

</details>
```

## Finding format

Each finding should be self-contained:

```markdown
#### N. Short finding title

`path/to/file.ext:123` · **Correctness** · **blocking|important|suggestion**

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
| Resolved | Missing auth regression test | Added coverage in `...` |
| Still open | 401 behavior verification | Still needs author confirmation |
| New | Log message placeholder mismatch | Introduced in latest commit |
```

Only include categories that exist. Keep the rest of the review focused on current state, not review history.

## Empty-state rules

- If there are no blocking findings, write `No blocking findings.` under `Must fix before merge`.
- If there are no important findings, omit `Should verify before merge`.
- If there are no suggestions or notes, omit the `<details>` block.
- If the Spec axis was skipped, mention that once in `Suggestions and notes` with the reason.
- Do not include “no finding” items in the main findings lists.

## Tone

- Sound like a helpful teammate reviewing a PR.
- Be direct about risk, but do not overstate uncertainty.
- Prefer short paragraphs and bullets.
- Use “please” sparingly.
- Approve reviews can include follow-ups, but must clearly say they are non-blocking.
