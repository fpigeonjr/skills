---
name: write-adr
description: Draft an Architecture Decision Record (ADR) for a significant technical decision, checking existing decisions, choosing the owning repository, and following its ADR conventions. Use when the user asks to write, draft, document, or update an ADR or architecture decision; not for general design brainstorming.
argument-hint: "[decision or existing ADR path]"
allowed-tools: Read Grep Glob Bash Edit Write
---

# Write an ADR

1. **Establish the decision.** Read the supplied context and relevant repository docs (`AGENTS.md`, ADR guidance/template, existing ADRs, and any domain glossary). Distinguish what was decided from what is still proposed; don't invent agreement, options, rationale, dates, or ticket links. Ask one focused question at a time if the decision or its trade-off is unclear. If the user wants to explore alternatives rather than record a decision, offer to do that first; don't fabricate an outcome.
2. **Check that an ADR is warranted.** Prefer ADRs for consequential, costly-to-reverse or non-obvious choices with a meaningful rationale or competing options. Skip routine, easily reversible, or already-documented decisions; explain why and suggest a more suitable place if appropriate. Search for an existing ADR before creating another; update or supersede it rather than silently contradicting it.
3. **Choose the owner and format.** Follow the target repository's documented ADR location, numbering, statuses, and template. For decisions spanning repositories, ask which repository owns the decision rather than assuming a central home. If no convention exists, use `docs/adr/NNNN-slug.md` with the next unused sequential number; create the directory only when needed. Keep the record as short as the decision allows: title, context, choice, and why; include alternatives or consequences only where useful. Do not write to another repository without confirming the destination with the user.
4. **Draft, don't ratify.** Record concrete context, real alternatives, reasoning, and consequences where known. Use the project's draft status if it has one; otherwise leave status out rather than implying approval. When superseding a decision, preserve the old record and link both records according to project convention. Do not claim approval, merge, push, or open a PR unless separately requested.
5. **Review the draft.** Check it against the source discussion, current ADRs, and any project template. Remove placeholders and unsupported claims; report the path, status (if any), and open questions or next review step. If key facts are missing, ask for them rather than guessing.

`grill-with-docs` can surface ADR-worthy decisions during an interview; this skill handles a direct ADR-writing request.
