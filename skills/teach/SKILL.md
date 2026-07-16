---
name: teach
description: Run a stateful, multi-session teaching workspace — creates HTML lessons, reference cheat sheets, and learning records tailored to a user's mission. Use when the user wants to learn a new topic, asks to be taught something, mentions "teach me", "I want to learn", or wants lessons, exercises, or a structured learning plan.
argument-hint: "What would you like to learn about?"
allowed-tools: Read Bash Write Edit
disable-model-invocation: true
---

# Teach

The user wants to learn something. This is stateful — learning continues across sessions.

## Workspace layout

Treat the current directory as the teaching workspace:

| Path | Purpose |
|---|---|
| `MISSION.md` | Why the user is learning — grounds every decision. Format: [MISSION-FORMAT.md](./MISSION-FORMAT.md) |
| `NOTES.md` | Scratchpad for user preferences and working notes |
| `RESOURCES.md` | Curated high-trust sources. Format: [RESOURCES-FORMAT.md](./RESOURCES-FORMAT.md) |
| `reference/*.html` | Beautiful, print-friendly cheat sheets — raw units of knowledge |
| `lessons/*.html` | Self-contained HTML lessons, titled `0001-<dash-case-name>.html` |
| `learning-records/*.md` | ADR-style insights that set the zone of proximal development. Format: [LEARNING-RECORD-FORMAT.md](./LEARNING-RECORD-FORMAT.md) |

## First session checklist

- [ ] Is `MISSION.md` populated? If not, interview the user — never skip this step.
- [ ] Is `RESOURCES.md` seeded with at least one high-trust source? If not, find one.
- [ ] Identify zone of proximal development from existing learning records.
- [ ] Create the first (or next) lesson.

## Lessons

- One tightly-scoped HTML file per lesson, saved to `./lessons/`
- Beautiful typography (think Tufte) — users return to these later
- Short: completable in a single sitting; one tangible win per lesson
- Include: citations, links to related lessons/reference docs, a primary source recommendation, and a prompt encouraging the user to ask follow-up questions
- After writing, open the file with a CLI command (e.g. `open lessons/0001-*.html`)

## Reference documents

Create alongside lessons. Compressed essence of the lesson — glossaries, syntax sheets, algorithms, pose guides. Designed for quick lookup, not reading.

## See also

Full teaching philosophy (fluency vs storage strength, retrieval practice, spacing, interleaving, wisdom via community): [REFERENCE.md](./REFERENCE.md)

---

*Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT).*
