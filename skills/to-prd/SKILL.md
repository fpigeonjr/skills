---
name: to-prd
description: Turn the current conversation context into a PRD and publish it to the project issue tracker. Use when user wants to create a PRD from the current context, write a product requirements document, or formalize a feature spec.
---

# To PRD

Turn the current conversation context and codebase understanding into a PRD. Do NOT interview the user — just synthesize what you already know.

The issue tracker should have been provided to you via `docs/agents/issue-tracker.md`. If that file doesn't exist in the current project, either run `/setup-matt-pocock-skills` (if installed) or create `docs/agents/issue-tracker.md` manually — see the [GitHub template](https://github.com/mattpocock/skills/blob/main/skills/engineering/setup-matt-pocock-skills/issue-tracker-github.md) as a starting point.

## Process

### 1. Explore the codebase

If you haven't already, explore the repo to understand the current state of the codebase. Use the project's domain glossary vocabulary throughout the PRD (from `CONTEXT.md` if it exists), and respect any ADRs in the area you're touching (`docs/adr/`).

### 2. Sketch major modules

Identify the major modules you will need to build or modify to complete the implementation. Actively look for opportunities to extract **deep modules** — ones that encapsulate a lot of functionality behind a simple, testable interface that rarely changes — as opposed to shallow pass-through modules.

Check with the user that these modules match their expectations, and confirm which modules they want tests written for.

### 3. Write and publish the PRD

Write the PRD using the template below, then publish it to the project issue tracker.

<prd-template>

## Problem Statement

The problem that the user is facing, from the user's perspective.

## Solution

The solution to the problem, from the user's perspective.

## User Stories

A numbered list of user stories covering all aspects of the feature. Each in the format:

1. As a `<actor>`, I want `<feature>`, so that `<benefit>`

This list should be extensive — err on the side of too many rather than too few.

## Implementation Decisions

A list of implementation decisions, including:

- The modules that will be built or modified
- The interfaces of those modules
- Technical clarifications from the developer
- Architectural decisions
- Schema changes
- API contracts
- Specific interactions

Do NOT include specific file paths or code snippets — they go stale fast.

Exception: if a prototype produced a snippet that encodes a decision more precisely than prose can (state machine, reducer, schema, type shape), inline it within the relevant decision and note briefly that it came from a prototype. Trim to the decision-rich parts — not a working demo, just the important bits.

## Testing Decisions

A list of testing decisions, including:

- What makes a good test for this feature (only test external behavior, not implementation details)
- Which modules will be tested
- Prior art for the tests (similar test patterns already in the codebase)

## Out of Scope

Explicit list of things that are out of scope for this PRD.

## Further Notes

Any further notes about the feature.

</prd-template>
