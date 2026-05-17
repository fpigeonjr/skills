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
git clone https://github.com/fpigeon/skills ~/Code/skills
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
| [`submit-draft-pr`](skills/submit-draft-pr/SKILL.md) | Create a draft PR with the repo's template fully populated, labels applied, and PR assigned to you. |
| [`release-pr`](skills/release-pr/SKILL.md) | Poll CI on a draft PR until all checks pass, then convert it to ready-for-review. |
| [`review-draft`](skills/review-draft/SKILL.md) | Draft a thorough code review for a human to read and post — never submits anything automatically. |
| [`tdd`](skills/tdd/SKILL.md) | Test-driven development with red-green-refactor loop, vertical slices, and behavior-focused tests. |
| [`grill-me`](skills/grill-me/SKILL.md) | Interview-style session that stress-tests a plan, resolving each branch of the decision tree one question at a time. |
| [`grill-with-docs`](skills/grill-with-docs/SKILL.md) | Like `grill-me`, but challenges your plan against the existing domain model and updates `CONTEXT.md` and ADRs inline. |
| [`zoom-out`](skills/zoom-out/SKILL.md) | Map all relevant modules and callers for an unfamiliar area of code, using the project's domain vocabulary. |
| [`handoff`](skills/handoff/SKILL.md) | Compact the current conversation into a handoff document for a fresh agent session to pick up. |
| [`to-prd`](skills/to-prd/SKILL.md) | Synthesize the current conversation context into a PRD and publish it to the project issue tracker. |
| [`to-issues`](skills/to-issues/SKILL.md) | Break a plan or PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices. |
| [`write-a-skill`](skills/write-a-skill/SKILL.md) | Create new agent skills with proper structure, progressive disclosure, and bundled reference files. |

## Credits

`tdd`, `grill-me`, `grill-with-docs`, `zoom-out`, `handoff`, `to-issues`, `to-prd`, and `write-a-skill` are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) and used under the MIT License.

Skills conform to the [Agent Skills standard](https://agentskills.io/specification).
