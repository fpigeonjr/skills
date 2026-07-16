---
name: code-review
description: Reviews a pull request, branch, commit range, or work-in-progress diff for correctness, repository standards, and fidelity to its originating spec. Use when the user asks for a code review, wants changes reviewed since a fixed point, or needs implementation checked against an issue, PRD, or spec.
argument-hint: "[PR, branch, commit, tag, or fixed point]"
allowed-tools: Read Grep Glob Bash
---

# Code Review

Review a change independently along three axes:

- **Correctness** - bugs, regressions, security or data risks, and missing tests.
- **Standards** - documented repository rules plus the heuristic smell baseline.
- **Spec** - missing requirements, scope creep, and incorrect implementation of the requested behavior.

Do not post review comments or modify code. Report findings for a human or another skill to act on.

## 1. Establish the Review Range

Resolve the argument as a PR reference or fixed point. For a local fixed point, verify it and use the merge base:

```bash
git rev-parse <fixed-point>
git diff <fixed-point>...HEAD
git log <fixed-point>..HEAD --oneline
```

For a PR, gather its metadata, commits, and full diff with the repository host's tools. If no target was supplied, infer the current branch's PR and base when possible; otherwise ask for the fixed point.

Stop if the reference is invalid or the diff is empty.

Read the complete diff before assessing individual hunks. For non-trivial changes, inspect the surrounding implementation, tests, interfaces, and callers.

## 2. Find the Spec and Standards

Find the originating spec in this order:

1. Issue references in the PR body or commit messages.
2. A path or issue reference supplied by the user.
3. A matching PRD or spec under the repository's documentation directories.
4. Ask the user. If no spec exists, record that the Spec axis was skipped.

Find the repository's documented standards, including `AGENTS.md`, contribution guides, coding standards, relevant ADRs, and the domain glossary. Repository documentation overrides generic guidance.

Read [SMELL-BASELINE.md](SMELL-BASELINE.md) for the Standards axis. Smells are judgment calls, never hard violations, and anything enforced by tooling should be omitted.

## 3. Run Three Independent Passes

Run each pass independently so one axis does not mask another. Parallelize them when the environment supports isolated workers; otherwise run three separate passes in sequence.

### Correctness

Trace changed behavior through its public interfaces and callers. Look for concrete bugs, regressions, unsafe failure modes, security or data-integrity risks, performance problems with a plausible impact, and missing tests for changed behavior. Do not report speculative failures without a reproducible path.

### Standards

Check every changed area against the documented repository standards. Cite the source and rule for each violation. Then apply the smell baseline, respecting repository overrides and labeling every smell as a non-blocking judgment call.

### Spec

Map the diff to the originating acceptance criteria, user stories, or requirements. Report missing or partial behavior, behavior outside the requested scope, and implementations that appear to satisfy a requirement incorrectly. Cite the relevant spec text for each finding.

## 4. Report Findings

Findings are the primary output. Under `## Correctness`, `## Standards`, and `## Spec`, list each finding with:

- File and line reference.
- Severity: `blocking`, `important`, or `suggestion`.
- The concrete problem and its impact.
- Evidence from the code, standard, or spec.
- A focused remediation when one is clear.

Order findings by severity within each axis. If an axis has no findings, say so explicitly. If the Spec axis was skipped, state why.

End with counts and the worst finding within each axis. Do not collapse the axes into one verdict.
