# skills

My personal collection of agent skills for [Pi](https://github.com/badlogic/pi-mono) and [OpenCode](https://github.com/sst/opencode). These are skills I use daily for GitHub workflow automation and software engineering.

## Installation

### Pi

Add to `~/.config/pi/agent/settings.json`:

```json
{
  "skills": ["~/Code/skills/skills"]
}
```

Then clone this repo:

```bash
git clone https://github.com/fpigeonjr/skills ~/Code/skills
```

Skills are auto-discovered at startup. Use `/skill:name` to invoke any skill explicitly.

### OpenCode

Add to `~/.config/opencode/opencode.json`:

```json
{
  "skills": {
    "paths": ["~/Code/skills/skills"]
  }
}
```

## Skills

| Skill | Description |
|---|---|
| [`address-review-comments`](skills/address-review-comments/SKILL.md) | Collect all open PR review threads, investigate each one, apply valid changes, push, and reply to every thread with a summary. |
| [`monitor-ci`](skills/monitor-ci/SKILL.md) | Check or poll GitHub Actions CI — instant snapshot, run polling, or E2E-specific monitoring. |
| [`submit-draft-pr`](skills/submit-draft-pr/SKILL.md) | Create a draft PR using the repo template, with a visual summary, before/after evidence, merge danger, labels, and assignment. |
| [`release-pr`](skills/release-pr/SKILL.md) | Poll CI on a draft PR until all checks pass, then convert it to ready-for-review. |
| [`code-review`](skills/code-review/SKILL.md) | Review any diff independently for correctness, repository standards, and fidelity to its originating spec. |
| [`submit-pr-review`](skills/submit-pr-review/SKILL.md) | Turn a code review into an approved GitHub PR review, require exact human approval, then submit it. |
| [`tdd`](skills/tdd/SKILL.md) | Test-driven development with red-green-refactor loop, vertical slices, and behavior-focused tests. |
| [`grill-me`](skills/grill-me/SKILL.md) | Interview-style session that stress-tests a plan, resolving each branch of the decision tree one question at a time. |
| [`grill-with-docs`](skills/grill-with-docs/SKILL.md) | Like `grill-me`, but challenges your plan against the existing domain model and updates `GLOSSARY.md` and ADRs inline. |
| [`zoom-out`](skills/zoom-out/SKILL.md) | Map all relevant modules and callers for an unfamiliar area of code, using the project's domain vocabulary. |
| [`handoff`](skills/handoff/SKILL.md) | Compact the current conversation into a handoff document for a fresh agent session to pick up. |
| [`to-prd`](skills/to-prd/SKILL.md) | Synthesize the current conversation context into a PRD and publish it to the project issue tracker. |
| [`to-issues`](skills/to-issues/SKILL.md) | Break a plan or PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices. |
| [`write-a-skill`](skills/write-a-skill/SKILL.md) | Create new agent skills with proper structure, progressive disclosure, and bundled reference files. |
| [`start-ticket`](skills/start-ticket/SKILL.md) | Create a worktree and feature branch off the current integration branch for a Jira ticket, using `wt` (worktrunk) and following the team's sprint branching strategy. |
| [`goal`](skills/goal/SKILL.md) | Drive a GitHub issue to completion through a human-checkpointed red-green loop — confirms the test plan upfront, runs TDD cycles until all AC are met and checks are green, then hands back for review before any PR is opened. |
| [`implement-spec`](skills/implement-spec/SKILL.md) | Coordinate a GitHub spec's dependency graph on an isolated spec branch, with human gates and sequential execution by default. |
| [`init`](skills/init/SKILL.md) | Create or update `AGENTS.md` for a repository by exploring the codebase and extracting high-signal guidance for future agent sessions. |
| [`retro`](skills/retro/SKILL.md) | Review a session or today's repo sessions and propose evidence-backed environment improvements; apply only the changes you select. |
| [`teach`](skills/teach/SKILL.md) | Run a stateful, multi-session teaching workspace — creates HTML lessons, reference cheat sheets, and learning records tailored to a user's mission. |

## Whole-spec implementation

In Pi, invoke `/skill:implement-spec <spec-path-or-URL>` with the associated GitHub issues. The skill first proposes the dependency graph, a pinned base, a dedicated `spec/<slug>` branch, test plans, and dispatch/merge permissions for approval. It does not start implementation merely because it was loaded.

Execution is sequential by default. Optional parallel workers require explicit approval and approved per-issue test plans; HITL checkpoints remain human decisions. This complements `/goal` rather than replacing it. The first version supports GitHub issues through the project's tracker configuration; it stops for unsupported trackers instead of treating Jira tickets as GitHub issues.

The result is a verified local spec branch and review handback, not automatic publication. Pushes, PRs, issue closure, and worktree cleanup require separate instructions.

## Daily retrospective

In Pi, run `/skill:retro daily` at the end of the day. Use `/skill:retro` for the current session, or `/skill:retro <session-path>` for a specific one. In OpenCode, explicitly load the `retro` skill and provide the same scope.

Daily mode samples up to five accessible sessions with activity today for the current repository, reports coverage gaps, and presents at most five prioritized improvements. It does not schedule itself or change files until you select proposals. Global changes require separate explicit approval.

## Domain documents and skill dependencies

`GLOSSARY.md` is the canonical domain glossary; multi-context projects use `GLOSSARY-MAP.md`. If a target project still uses `CONTEXT.md` or `CONTEXT-MAP.md`, agree a coordinated rename and update consumers together rather than creating duplicate glossaries.

Skills that depend on another skill explicitly load its instructions through the harness's loader or by reading its discovered `SKILL.md` and needed sibling references. A literal `Skill` tool is not required. User-invoked-only dependencies remain human invocation boundaries.

## Credits

`code-review`, `tdd`, `grill-me`, `grill-with-docs`, `zoom-out`, `handoff`, `to-issues`, `to-prd`, `retro`, `implement-spec`, and `write-a-skill` are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) and used under the MIT License.

The review-at-a-glance PR-body guidance is adapted from Matt Pocock's `pr`, whose visual-summary guidance credits [Dex Horthy's show-me](https://github.com/humanlayer/skills/blob/main/plugins/show-me/skills/show-me/SKILL.md).

Skills conform to the [Agent Skills standard](https://agentskills.io/specification).
