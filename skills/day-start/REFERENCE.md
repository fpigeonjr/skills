# Day-start collection and Logseq rules

## Prior-workday and evidence scope

- Resolve the machine's local timezone and the intended date first. The prior workday is the latest earlier journal that represents a workday; normally Friday for Monday, but do not invent holiday or leave knowledge. If the nearest journal is absent or ambiguous, say so and ask the user when it affects the plan.
- Read only the relevant prior journal and a bounded slice of today's existing journal. Start with `plan for tomorrow`, then inspect unfinished work, blockers, and the latest stand-up or work-log context needed to interpret it. Do not sweep journal history by default.
- Confirm `gh` identity independently on both hosts with `gh api --hostname HOST user --jq .login`. Never display tokens or read authentication stores. Host identities may differ.
- `gh search` does not accept `--hostname`; select each host with `GH_HOST=github.com` or `GH_HOST=github.helix.gsa.gov`. Use `gh api --hostname HOST` for API calls. Check local command help rather than assuming both hosts expose identical capabilities.
- Keep searches bounded and driven by carryovers: likely repositories, authored or assigned PRs/issues, requested reviews, and items updated since the prior workday. Inspect the actual item or event timestamps before attributing work to a day. Parent `updated_at` timestamps do not prove the user's activity.
- Include only clearly GSA-related repositories. Helix is a strong lead, not blanket scope; public GitHub activity is not automatically work activity. Ask about borderline repositories. Do not persist unrelated personal activity in the work journal.
- Current remote state can invalidate a carryover but does not choose the user's priorities. A merged PR, closed issue, green check, or requested review is evidence to interpret, not automatic proof of completion, importance, or ownership.
- Report host failures, permission gaps, API limitations, pagination or result caps, and stale data. Never present the check as an exhaustive activity audit.

## Morning drafting

- Prefer three to five ranked, outcome-oriented priorities that fit one workday. Carry prior plans forward only when they remain relevant after repository checks. Flag proposed additions that came from GitHub rather than the prior journal.
- Keep the spoken stand-up update near 30 seconds: normally one or two bullets each for **Yesterday**, **Today**, and **Blockers / asks**. Summarize outcomes rather than narrating every commit or review. Preserve uncertainty explicitly.
- “Yesterday” means the prior workday, not necessarily the prior calendar day. Use confirmed journal notes and timestamped activity; do not turn planned work into claimed accomplishments.
- When there is no blocker, say “No known blockers” only if the available evidence and user confirmation support it. Otherwise omit the section's content or phrase the uncertainty honestly.
- The default stand-up destination is a block under `## meeting log`:

```md
	- HHMM: [[SAM Stand Up]]
		- **Yesterday**
			- ...
		- **Today**
			- ...
		- **Blockers / asks**
			- ...
```

  Use a known scheduled time from today's journal or user context. If no time is known, omit `HHMM:` rather than inventing it.

## Logseq file handling

- Journals live at `~/notes/journals/YYYY_MM_DD.md`. The configured Daily Journal template in `~/notes/pages/Templates.md` uses these exact headings: `## fleeting thoughts`, `## meeting log`, `## work log`, `## todays priorities`, and `## plan for tomorrow`.
- Creating the empty five-heading shell is the only pre-approval content write allowed. This makes the journal available for the day without treating proposed priorities or stand-up claims as accepted facts. If the file already exists, do not normalize or recreate it.
- Logseq uses Markdown bullets and tab nesting. Inspect the actual file and match its style. Add a missing target heading only when needed for approved content; never reorder sections or reformat existing blocks.
- Preview only relevant proposed content, not unrelated private notes. Before the approved edit, re-read the journal to catch concurrent Logseq changes. Stop and ask if preserving those changes is uncertain.
- A rerun should replace a still-unmodified generated stand-up draft only with explicit approval; otherwise append or edit only the exact blocks the user approved. Avoid duplicate priorities and duplicate stand-up entries.

## Final report

State the local date and timezone, the prior workday used, hosts checked and coverage gaps, the journal path, sections changed, and any proposed items omitted or qualified because they were not confirmed.