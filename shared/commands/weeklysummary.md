---
allowed-tools: Bash(git:*), Bash(date:*), Bash(ls:*), Read, Write, Glob, Agent
description: Generate an ISO calendar week summary from daily summaries — groups by workstream, carries forward open TODOs, tags MEMORY.md candidates, tracks dormant workstreams
---

# /weeklysummary — Weekly Work Summary

> **When to use**: At the end of a work week (Friday/Saturday) or start of the next (Monday). Consolidates daily summaries into a single weekly view grouped by workstream.

## Timing Recommendation

**Invoke /weeklysummary at the END of a work week (Friday/Saturday) or at the START of a new week (Monday).** Mid-week invocations produce partial summaries, which are labeled as such.

If a weekly summary already exists for the current ISO week, this command OVERWRITES it (the weekly summary is a live document until the week closes).

---

**IMPORTANT**: This summary should be written by a **Sonnet** model subagent when available. Spawn a single Agent with `model: "sonnet"` and pass it the gathered information along with the formatting instructions below. The Sonnet agent writes the summary; the main agent saves it.

The reason for preferring Sonnet: smaller models have been observed to produce inaccurate numerical figures and wrong orderings when summarizing technical sessions. Sonnet's accuracy on project-specific details justifies the cost.

**If Sonnet is unavailable**, use the best available model but add a verification step: after the summary is drafted, cross-check all numerical values (metrics, counts, dates) against the source daily summaries. Flag any unverifiable values with `(unverified)`.

---

## Step 0: Read Project Configuration

Read `~/.claude/toolkit-config.md` to load:
- `summary_folder` — where daily summaries live (default: `Daily Summary`)
- `weekly_folder` — where weekly summaries are written (default: `Weekly Summary`)
- `workstreams` — the known workstream list, used for dormant-workstream detection
- `project_name` — for context in the generated document

If `~/.claude/toolkit-config.md` does not exist, use the defaults above.

---

## Step 1: Determine ISO Week Boundaries

Calculate the current ISO week (Monday–Sunday):

```bash
# Get Monday of current ISO week
MONDAY=$(date -d "last monday" '+%Y-%m-%d' 2>/dev/null || date -dlast-monday '+%Y-%m-%d')
# Get Sunday of current ISO week
SUNDAY=$(date -d "$MONDAY + 6 days" '+%Y-%m-%d')
# Get today
TODAY=$(date '+%Y-%m-%d')
```

If today IS Monday, use today as MONDAY. If today is before Sunday, label the output as partial:
> "Week of YYYY-MM-DD to YYYY-MM-DD (through [today])"

---

## Step 2: Find Daily Summaries in Range

Glob `{summary_folder}/YYYY-MM-DD_*.md` for files whose date prefix falls within MONDAY to SUNDAY (inclusive).

If no daily summaries are found in the date range:
> "No daily summaries found for the week of [MONDAY] to [SUNDAY]. Nothing to aggregate."
> **STOP.**

---

## Step 3: Read and Extract

Read each daily summary in the date range. Extract:

1. **Workstream mentions**: Look for section headers and recurring topics. Use the `workstreams` list from config as a guide, but also detect any others that appear.

2. **Next Steps / TODO items**: Extract all items from "Next Steps" sections. Note which daily they came from.

3. **Key decisions**: Architectural decisions, milestones, parameter locks, methodology choices.

4. **Any numbered findings or versioned results** referenced in the dailies.

5. **Phase or stage transitions**: Any significant progress markers, completions, or validation milestones.

---

## Step 4: Check Previous Week

Glob `{weekly_folder}/` for the most recent prior weekly summary. Extract its date range for the `Previous:` navigation link and to identify dormant workstreams (those active last week but silent this week).

---

## Step 5: Generate Weekly Summary

Spawn a **Sonnet** subagent (`model: "sonnet"`) with all extracted data. The subagent writes the summary using this template:

```markdown
Previous: [[YYYY-MM-DD_to_YYYY-MM-DD.md]]

# Weekly Summary: YYYY-MM-DD to YYYY-MM-DD

**ISO Week**: [week number]
**Status**: [Complete / Partial (through YYYY-MM-DD)]
**Daily Summaries Aggregated**: [N] ([[YYYY-MM-DD_Title.md]], [[YYYY-MM-DD_Title.md]], ...)

---

## Active Workstreams

### [Workstream Name]
- **Status**: [1-2 sentence summary of where this workstream stands at week's end]
- **Accomplished**:
  - [Bulleted accomplishments, linked to source dailies via [[daily_filename.md]]]
- **Next Steps**:
  - [Aggregated from dailies, deduplicated]
  - [Items from early in the week that weren't resolved get a [carried] tag]
- **Key Decisions**: [Any architectural or strategic decisions] [MEMORY?]

[Repeat for each active workstream]

---

## Dormant Workstreams

[Workstreams that were active in the PRIOR weekly summary but had zero mentions this week]

- **[Workstream]**: Last active [[YYYY-MM-DD_Title.md]]. [One-line status from last mention.]

[If no dormant workstreams, omit this section]

---

## Open Items Carried Forward

[Items from "Next Steps" in early dailies that were NOT resolved by week's end]

- [ ] [Item] — first appeared [[YYYY-MM-DD_Title.md]]
- [ ] [Item] — first appeared [[YYYY-MM-DD_Title.md]]

---

## Key Decisions Made This Week

- [Decision] — [[source_daily.md]] [MEMORY?]
- [Decision] — [[source_daily.md]] [MEMORY?]

---

## `/improve` Candidates

[Aggregated from daily summaries' /improve sections, deduplicated]

- [Candidate] — from [[YYYY-MM-DD_Title.md]]
```

---

### `[MEMORY?]` Tagging Rules

Tag items with `[MEMORY?]` if they match ANY of these:
- A workstream milestone or phase completion
- A new architectural decision that should be remembered across sessions
- A key finding or result confirmed
- A new tool or workflow established
- Advisor or collaborator feedback received

These are suggestions for manual MEMORY.md update — this command NEVER writes to MEMORY.md automatically.

### Wiki-Link Rules

Use the same convention as `/dailysummary`:
- Regular files: `[[filename.md]]` (bare filename with extension)
- Ambiguous files: `[[parent/filename.md]]` (one parent dir)
- Daily summaries: `[[YYYY-MM-DD_Title.md]]`

### Numerical Accuracy

Same rule as `/dailysummary`: **verify all numbers against source files before writing.** Do NOT approximate from conversation context.

---

## Step 6: Save the Summary

Write to `{weekly_folder}/YYYY-MM-DD_to_YYYY-MM-DD.md` (Monday date to Sunday date).

If the file already exists for this week, overwrite it (it is a live document until the week closes).

---

## Step 7: Report

> "Weekly summary generated for [MONDAY] to [SUNDAY] ([N] daily summaries aggregated).
>
> Active workstreams: [list]
> Dormant workstreams: [list or 'none']
> Open items carried forward: [N]
> MEMORY? candidates: [N]
>
> Saved to: `{weekly_folder}/YYYY-MM-DD_to_YYYY-MM-DD.md`"

**STOP and wait.**

---

## BEHAVIORAL CONSTRAINTS

- **Sonnet subagent required** for the writing step
- **Never modify daily summaries** — this command reads them, never writes to them
- **Never modify MEMORY.md** — `[MEMORY?]` tags are suggestions only
- **Overwrite on re-run** — the weekly summary for a given week is a live document
- **Wiki-links throughout** — use `[[filename.md]]` format consistently
- **ISO calendar week** — Monday to Sunday, non-overlapping
- **Active workstreams only** — do not create sections for workstreams with zero mentions this week
- **Dormant tracking** — compare against prior week's active workstreams

$ARGUMENTS
