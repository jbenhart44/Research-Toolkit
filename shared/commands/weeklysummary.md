---
allowed-tools: Bash(git:*), Bash(date:*), Bash(ls:*), Bash(python3:*), Read, Write, Glob, Agent
description: Generate an ISO calendar week summary from daily summaries — groups by workstream, carries forward open TODOs, tags MEMORY.md candidates, tracks dormant workstreams, appends the week's toolkit run log
---

# /weeklysummary — Weekly Work Summary

> **When to use**: At the end of a work week (Friday/Saturday) or start of the next (Monday). Consolidates daily summaries into a single weekly view grouped by workstream.
>
> **Prerequisites**: Prefers a Sonnet subagent for the writing step. On plans without Sonnet it uses the best available model plus a verification pass (see below). Re-running overwrites the existing weekly summary for the same ISO week (it is a live document until the week closes).

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
- `evidence_dir` — where toolkit run evidence lives, read in Step 5.5 (default: `.toolkit/evidence`)

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
# ISO week number
ISO_WEEK=$(date '+%V')
```

If today IS Monday, use today as MONDAY. If today is before Sunday, label the output as partial:
> "Week of YYYY-MM-DD to YYYY-MM-DD (through [today])"

`date -d` is GNU syntax (Linux, WSL). On macOS the BSD `date` rejects it. If the lines above fail, compute the same four values with Python, which handles the Monday case without the special rule:

```bash
python3 -c 'import datetime as d; t=d.date.today(); m=t-d.timedelta(days=t.weekday()); print(m, m+d.timedelta(days=6), t, t.isocalendar()[1])'
# prints: MONDAY SUNDAY TODAY ISO_WEEK, e.g. 2026-10-19 2026-10-25 2026-10-21 43
```

Shell variables do not persist between separate Bash calls. Carry MONDAY, SUNDAY and TODAY forward as literal dates in later steps.

---

## Step 2: Find Daily Summaries in Range

Glob `{summary_folder}/YYYY-MM-DD_*.md` for files whose date prefix falls within MONDAY to SUNDAY (inclusive). Same-day second-session files (`YYYY-MM-DD_HHMM_Title.md`) count.

Count only files directly in `{summary_folder}` whose first ten characters are a real date. Skip subfolders, and skip notes, plans or meeting files kept alongside the dailies without a date prefix. Summary folders tend to collect such files over time, and a looser match pulls them into the week. Because the prefix is zero-padded `YYYY-MM-DD`, comparing it as a string against MONDAY and SUNDAY gives the right range.

If no daily summaries are found in the date range:
> "No daily summaries found for the week of [MONDAY] to [SUNDAY]. Nothing to aggregate."
> **STOP.**

---

## Step 3: Read and Extract

Read each daily summary in the date range. Extract:

1. **Workstream mentions**: Look for section headers and recurring topics. Use the `workstreams` list from config as a guide, but also detect any others that appear.

2. **Next Steps / TODO items**: Extract all items from "Next Steps" sections. Note which daily they came from.

3. **Key decisions**: Architectural decisions, milestones, parameter locks, methodology choices.

4. **Any numbered findings or versioned results** referenced in the dailies (e.g. `F12`, `v3 results`). Keep the exact labels the dailies use, and note which workstream each belongs to.

5. **Phase or stage transitions**: Any significant progress markers, completions, or validation milestones.

---

## Step 4: Check Previous Week

Glob `{weekly_folder}/` for the most recent prior weekly summary, meaning the latest one whose range ends before this week's MONDAY. If this week's own file already exists from an earlier run, skip it; comparing the week against itself would report no dormant workstreams. Extract the prior summary's date range for the `Previous:` navigation link and to identify dormant workstreams (those active last week but silent this week).

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
- **Findings**: [[F## Name]], [[F## Name]] [MEMORY?]
  [Numbered findings or versioned results referenced this week. Omit this line if there were none.]
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

The subagent does not write the run-log section. The main agent appends it in Step 5.5.

---

### `[MEMORY?]` Tagging Rules

Tag items with `[MEMORY?]` if they match ANY of these:
- A workstream milestone or phase completion (e.g. "Phase 2 calibration complete")
- A new architectural decision that should be remembered across sessions (e.g. "weekly summaries use ISO calendar weeks")
- A key finding or result confirmed (e.g. "F12 holds in the full-scale run")
- A new tool or workflow established (e.g. "pre-commit hook added")
- Advisor or collaborator feedback received, or a meeting outcome

These are suggestions for manual MEMORY.md update — this command NEVER writes to MEMORY.md automatically.

### Wiki-Link Rules

Use the same convention as `/dailysummary`:
- Regular files: `[[filename.md]]` (bare filename with extension)
- Ambiguous files: `[[parent/filename.md]]` (one parent dir)
- Numbered findings: reuse the exact form the dailies already use (e.g. `[[F12 Name]]`). Never invent a finding number or a title.
- Daily summaries: `[[YYYY-MM-DD_Title.md]]`

### Numerical Accuracy

Same rule as `/dailysummary`: **verify all numbers against source files before writing.** Do NOT approximate from conversation context.

---

## Step 5.5: Append the Toolkit Run Log

After the subagent returns the summary and before saving it, append a table of this week's instrumented toolkit runs. The main agent builds this table, not the subagent. It is copied from a CSV, not summarized, so none of its numbers pass through a model's paraphrase.

The table belongs in the weekly summary rather than the daily one because the run log's useful signals show up across days: convergence drifting down, the same command failing twice, a verification command that stopped being run. One day of rows is too few to show them.

1. **Source**: `{evidence_dir}/run_log.csv` (default `.toolkit/evidence/run_log.csv`). Instrumented toolkit commands append to this file and `/runlog` reads it. Read it only; never write to it.

2. **Parse with a CSV-aware reader.** The `task_summary` and `notes` cells are quoted and can contain commas or JSON, so splitting lines on `,` miscounts fields. Older rows may be column-shifted (a run ID in the `tool` column, a model name in the `date` column). Skip any row whose `date` is not a date or whose `tool` contains one, and report how many were skipped. Substitute the literal values for the three arguments:

```bash
python3 - "<evidence_dir>/run_log.csv" <MONDAY> <SUNDAY> <<'PY'
import csv, re, sys
path, mon, sun = sys.argv[1:4]
day_re = re.compile(r"\d{4}-\d{2}-\d{2}")
def cell(v, width=None):
    v = " ".join((v or "").split()).replace("|", "\\|")
    if width and len(v) > width:
        v = v[:width - 1] + "…"
    return v or "—"
rows, skipped = [], 0
with open(path, newline="", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        day, tool = (r.get("date") or "")[:10], (r.get("tool") or "").strip()
        if not day_re.fullmatch(day) or not tool or day_re.search(tool):
            skipped += 1                      # legacy or column-shifted row
            continue
        if mon <= day <= sun:
            rows.append((day, tool, r))
rows.sort(key=lambda x: x[0])
if not rows:
    print("No instrumented toolkit runs this week.")
else:
    print("| date | tool | outcome | convergence_rate | task_summary |")
    print("|---|---|---|---|---|")
    for day, tool, r in rows:
        print(f"| {day} | {cell(tool)} | {cell(r.get('outcome'))} "
              f"| {cell(r.get('convergence_rate'))} | {cell(r.get('task_summary'), 80)} |")
if skipped:
    print(f"\n_Skipped {skipped} malformed row(s) in run_log.csv._")
PY
```

   If `python3` is not available, Read the CSV and build the same table by hand: same columns, same date filter, same skip rule, quoted cells kept whole.

3. **Append** the output as the last section of the summary, after `/improve` Candidates:

   ```markdown
   ---

   ## Toolkit Run Log (this week)

   [table printed by the script, OR "No instrumented toolkit runs this week."]

   For per-command totals and recurring improvement signals over the same window, run `/runlog --since YYYY-MM-DD` (this week's Monday).
   ```

4. **If `run_log.csv` does not exist**, append the section anyway with this note in place of the table:
   `_No run_log.csv in {evidence_dir}. Toolkit commands that emit run reports write it there; nothing to show yet._`

This section is informational. It does not change the summary's prose, its workstream classification, or its carried-forward items.

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
> Toolkit runs this week: [N, or 'none', or 'no run_log.csv']
>
> Saved to: `{weekly_folder}/YYYY-MM-DD_to_YYYY-MM-DD.md`"

**STOP and wait.**

---

## BEHAVIORAL CONSTRAINTS

- **Sonnet subagent for the writing step** when available; otherwise the best available model plus the numerical verification pass
- **Never modify daily summaries** — this command reads them, never writes to them
- **Never modify MEMORY.md** — `[MEMORY?]` tags are suggestions only
- **Never modify run_log.csv** — the run-log table is copied from it by the parser, never written by the subagent
- **Overwrite on re-run** — the weekly summary for a given week is a live document
- **Wiki-links throughout** — use `[[filename.md]]` format consistently
- **ISO calendar week** — Monday to Sunday, non-overlapping
- **Active workstreams only** — do not create sections for workstreams with zero mentions this week
- **Dormant tracking** — compare against the prior week's active workstreams, never against this week's own earlier file

> **What next?** Run `/commit` to save the weekly summary file — it won't appear in next week's git history unless it's committed.

$ARGUMENTS
