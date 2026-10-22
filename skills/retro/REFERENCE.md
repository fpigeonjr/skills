# Retro lenses and output

Examine these seven environment lenses, only where evidence warrants it:

- **Navigation:** Did finding the right files require avoidable exploration? Prefer a precise pointer over duplicating documentation.
- **Automated checks:** Which observed error could a deterministic check have caught? Inspect existing scripts, hooks and CI first; repair an existing unwired/broken check before adding a duplicate.
- **Coding standards:** Mechanical rules belong in checks where economical; judgment-based consistency belongs in review guidance, not a brittle linter. Don't assume a `CODING_STANDARDS.md` exists.
- **Global AGENTS.md:** Is costly, repeated global steering better scoped to a project or a check? Inspect only relevant accessible guidance, not unrelated private configuration.
- **Tool economy:** Did a repeated expensive tool call have a simpler equivalent already available?
- **No-ops:** Did a steering instruction fail to affect behavior? Look for actual recurrence, not just long files.
- **Information access:** Did a missing *safe, read-only* source block a decision? Propose the narrowest access, never default to broad logs or credentials.

A session may yield no proposal. Avoid treating an absence of CI as an automatic defect, particularly in plain-Markdown repositories. Consider context pressure: an implementation agent needs concise navigational pointers; reviewer judgment may be better deferred to review. Never claim a category was inspected if it was not.

## Report

Start with scope, repository, local date/timezone for daily mode, discovery method, sessions seen/sampled/omitted or unknown, and access gaps, including unreviewed sibling-worktree groups. State what current guidance and checks were inspected. For each prioritized candidate (up to 3–5):

1. **Proposal / lens / priority / scope** (repository or global).
2. **Session evidence** (sanitized session ID + turn or bounded location; observed fact, not raw sensitive text) **and environment evidence** (current file/check and location or its verified absence).
3. **Cause** (observed or inferred, explicitly labeled), **smallest proposed change**, **expected benefit**, and **validation** after approval.
4. **Uncertainty/tradeoff**, including overlap with existing checks/docs.

End with what needs the human's exact selection; for global changes request separate approval. If no candidates survive, say “No changes proposed” and explain the evidence gap or why current safeguards suffice. For partial reports, clearly distinguish unreviewed sessions/categories from reviewed ones.
