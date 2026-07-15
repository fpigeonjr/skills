# skills

A personal collection of plain-Markdown agent skills for Pi and OpenCode, covering GitHub/Jira workflow automation and software-engineering practice. There is no build system or tooling — editing `.md` files is the workflow.

## Language

**Skill**:
A single unit of agent capability, defined by a `SKILL.md` plus optional sibling reference files. The `SKILL.md` frontmatter `description` is the only field the agent reads when selecting a skill.
_Avoid_: command, plugin, prompt (reserve "command" for the `/skill:name` invocation).

**Reference file**:
A sibling `.md` next to `SKILL.md` (e.g. `REFERENCE.md`, `ADR-FORMAT.md`) holding bulky or rarely-needed detail, kept at most one level deep. Progressive disclosure: the `SKILL.md` stays focused, references hold the depth.

**Issue**:
A tracked unit of work hosted on GitHub Issues. The default work item for this collection — `to-issues`, `to-prd`, `goal`, and `submit-draft-pr` read from and write to it via the `gh` CLI.
_Avoid_: ticket, when the work item is on GitHub.

**Ticket**:
A tracked unit of work hosted on Jira (the GSA instance). Used only by `start-ticket`, which also accepts GitHub issues. Use "ticket" only for Jira-hosted work or when quoting external systems; everything else is an **Issue**.

**Acceptance criteria (AC)**:
The `## Acceptance criteria` checklist on an **Issue**, defining what "done" means. `goal` drives a loop until every AC item is met with verifiable evidence; `to-issues` writes them.
_Avoid_: requirements, definition of done (reserve "definition of done" for the AC + green-checks pair).

**Integration branch**:
The shared branch a **Feature branch** is cut from and merged back into, named `integration-<PI>.<Sprint>` (e.g. `integration-66.1`, `integration-59.IP`). `start-ticket` picks the highest by PI then sprint (`IP` sorts last).
_Avoid_: main, develop, trunk (this collection branches off integration branches, not a single trunk).

**Feature branch**:
The branch created for one **Issue** or **Ticket**. Jira branches are named exactly after the ticket ID (e.g. `IAEMOD-58792`); GitHub branches are `gh-<number>-<slug>`.
_Avoid_: topic branch.

**Worktree**:
An isolated working directory for one **Feature branch**, managed by the `wt` (worktrunk) CLI. Each ticket gets its own worktree, so in-flight work on other branches is never disturbed.

**Draft PR**:
A pull request opened in draft state by `submit-draft-pr` with the repo template populated. It is not yet requesting review.

**Ready-for-review**:
The state a **Draft PR** is promoted to by `release-pr`, once all CI checks pass and no review threads are unresolved.

**Check**:
A pass/fail verification signal — a CI check on a PR, or a project check command (lint, test, typecheck, build) discovered from `AGENTS.md`, `package.json`, or hook configs. "Green" means all relevant checks exit 0.

**Code review**:
A side-effect-free analysis of a diff along independent Correctness, Standards, and Spec axes, produced by `code-review`. It reports findings but does not post them or reduce the axes to one verdict.
_Avoid_: PR review, when referring to the analysis.

**PR review**:
The GitHub review submitted as Approve or Request Changes by `submit-pr-review`, only after exact human approval of its body and recommendation.
_Avoid_: code review, when referring to the posted GitHub artifact.

**Review thread**:
A single unresolved conversation on a PR. `address-review-comments` collects every open thread, applies valid changes, and replies to each; `release-pr` refuses to mark **Ready-for-review** while any remain unresolved.

## Relationships

- An **Issue** (or **Ticket**) carries many **Acceptance criteria** and gets one **Feature branch**.
- A **Feature branch** is cut from one **Integration branch** and lives in its own **Worktree**.
- A **Feature branch** produces one **Draft PR**, which is promoted to **Ready-for-review** once all **Checks** are green and no **Review thread** is unresolved.
- `code-review` produces a **Code review**; `submit-pr-review` turns it into a **PR review** after human approval.
- `goal` closes the gap between branch and PR: it runs TDD cycles against the **Acceptance criteria** until every item is evidenced and every **Check** is green.

## Flagged ambiguities

- "ticket" vs "issue" — historically used interchangeably across skills. Resolved: GitHub-hosted work is an **Issue**; Jira-hosted work is a **Ticket**. `start-ticket` is the only skill that legitimately spans both because it accepts either source.
- "AFK" / "autonomous" — `goal` was previously framed as an autonomous grind. Resolved: the loop is **human-checkpointed** (approval gate at the start, review handback at the end); it executes an approved plan rather than self-scoping.
- "code review" vs "PR review" — a **Code review** is side-effect-free analysis; a **PR review** is the approved GitHub artifact posted from that analysis.
</content>
</invoke>
