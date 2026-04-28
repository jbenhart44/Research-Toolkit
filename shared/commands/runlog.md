---
allowed-tools: Read, Bash(cat:*), Bash(head:*), Bash(tail:*), Bash(wc:*), Bash(ls:*), Bash(date:*), Bash(sort:*), Bash(awk:*), Glob
description: Render a cross-command longitudinal table of recent toolkit runs (convergence, tokens, outcomes) from existing CSVs. Read-only aggregation, PLN-verifiable.
---

# /runlog — Longitudinal Toolkit Observability

> **When to use**: After several toolkit runs have accumulated. Want a single table showing which commands you've used, how they performed, and where improvement signals are piling up. Instructor use: verify which verification commands students have actually run over the semester.

**Version**: v1.1 (NEW)

## What It Does

Pure aggregation. Reads three existing CSVs produced by the instrumented commands (/pace, /coa, /pcv-research, /audit, /improve, /dailysummary, /commit, /startup) and renders a longitudinal table. No new data collection. No external services. **PLN-verifiable by construction**: re-running produces the same table modulo new rows appended since last run.

## Inputs (reads only, never writes to)

1. `.toolkit/evidence/run_log.csv` — cross-run index (toolkit master log), appended to by every instrumented command via the `emit_run_report.sh` helper
2. `.toolkit/evidence/command_performance_log.md` — append-only human-readable log (parsed for outcome + improvement signals)
3. `.toolkit/evidence/pace_runs/*/instrumentation.csv` and `.toolkit/evidence/coa_sessions/*/instrumentation.csv` — per-run detail (only read when user invokes `--drill-down <run-id>`)

## Output

A markdown table + optional summary footer. Output paths:
- Displayed in terminal
- Written to `.toolkit/evidence/runlog_reports/runlog_YYYY-MM-DD_HHMMSS.md` (reproducible snapshot)

## Usage

```
/runlog                           # Default: last 14 days, all commands
/runlog --since 2026-01-01        # Date range filter
/runlog --command pace            # Single-command filter
/runlog --command pace --command coa   # Multi-command filter
/runlog --all                     # Full history, no date filter
/runlog --drill-down <run-id>     # Per-run detail for a specific run
/runlog --top-signals             # Show just the recurring improvement signals
```

## Default Output Schema

```markdown
# /runlog — Longitudinal Toolkit Report
**Generated**: YYYY-MM-DD HH:MM:SSZ
**Window**: last 14 days
**Source CSVs read**: .toolkit/evidence/run_log.csv (N rows), command_performance_log.md (M entries)

## Per-Command Summary

| Command | Runs (last 14d) | Avg convergence | Mean tokens | Outcomes (complete/partial/failed) | Last run | Top improvement signal |
|---------|----------------|-----------------|-------------|-------------------------------------|----------|------------------------|
| /pace | 3 | 0.82 | 85K | 3/0/0 | 2026-04-15 | "Verify source data directly" |
| /coa | 2 | 0.75 | 120K | 2/0/0 | 2026-04-16 | "Gemini quota insufficient" |
| /pcv-research | 2 | 0.82 | 200K | 2/0/0 | 2026-04-17 | "Supplementary-question pattern" |
| /dailysummary | 7 | — | 15K | 6/1/0 | 2026-04-16 | "--append-pointer mode needed" |
| /audit | 2 | — | 10K | 2/0/0 | 2026-04-10 | "None" |
| /improve | 2 | — | 45K | 2/0/0 | 2026-04-16 | "Gate Pass-1 reads by session friction" |
| /startup | 5 | — | 8K | 5/0/0 | 2026-04-17 | "None" |
| /commit | 4 | — | 3K | 4/0/0 | 2026-04-15 | "None" |

## Aggregate Statistics

- Total runs: N
- Mean outcome rate: X% complete, Y% partial, Z% failed
- Mean tokens per run (across all commands): M
- Highest-token command: /pcv-research (~200K mean)
- Lowest-convergence command: /coa (0.75) — consider root-cause

## Top Recurring Improvement Signals (frequency >= 2)

1. "Gate historical reads by session friction count" (3 runs)
2. "Gemini free-tier quota insufficient" (3 runs)
3. "--append-pointer mode for dailysummary" (2 runs)

## Evidence Footer

- Command: /runlog v1.1
- Run timestamp: YYYY-MM-DD HH:MM:SSZ
- Inputs:
  - run_log.csv SHA-256: <hash> (N rows)
  - command_performance_log.md SHA-256: <hash> (M entries)
- Window: last 14 days (2026-04-03 to 2026-04-17)
- Reproducibility: re-run this command on the same CSVs → same table.
```

## Execution Sequence

### Step 1: Locate the CSVs

Read `~/.claude/toolkit-config.md` for `evidence_dir` (default: `.toolkit/evidence/`).

```bash
EVIDENCE_DIR="${evidence_dir:-.toolkit/evidence}"
RUN_LOG="$EVIDENCE_DIR/run_log.csv"
PERF_LOG="$EVIDENCE_DIR/command_performance_log.md"
```

If either file is missing: report "No runs logged yet — run at least one instrumented command first" and STOP.

### Step 2: Parse the CSVs — USE A CSV-AWARE PARSER, NOT raw awk

The `run_log.csv` canonical schema (v1.1, 13 columns, unified as of 2026-04-17):

```csv
run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
```

**CRITICAL PARSING CAVEAT** (discovered in T4 verification 2026-04-17):

- Historical rows may have older schemas (9 column, column-shifted, or mis-aligned columns from pre-2026-04-10 runs).
- The `task_summary` and `notes` cells are CSV-quoted and may contain embedded commas — `awk -F','` WILL MISCOUNT fields on those rows.
- The `notes` cell in v1.1 rows contains JSON with its own `,` separators (even though it's CSV-quoted, naive awk splits on every comma).

**Use Python's `csv` module**, not raw awk:

```bash
python3 <<'PY'
import csv, sys
with open(".toolkit/evidence/run_log.csv") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

# Filter + normalize: drop rows where the `tool` column looks like a run_id
# (column-shifted malformed rows) — heuristic: tool column contains a date
# pattern like "2026-04-" or starts with "pcv_" etc.
valid = [r for r in rows if r.get("tool", "") and not r["tool"].startswith(("2026-", "2025-", "pace_", "coa_", "pcv_"))]

# Aggregation
from collections import Counter
tool_counts = Counter(r["tool"] for r in valid)
for tool, n in tool_counts.most_common():
    print(f"{tool}\t{n}")
PY
```

This approach:
- Handles CSV quoting correctly (no false splits on embedded commas)
- Detects column-shifted rows via heuristic and skips them with a warning (reported in the evidence footer as "Skipped N malformed rows")
- Accepts both the 13-column canonical schema AND legacy 9-column rows (the `csv` module tolerates row length variance via DictReader)

**Fallback: if Python is not available**, use awk with a safer field extraction via `--csv` aware tools like `csvtool` or `mlr`. Raw `awk -F','` is REJECTED for the final /runlog implementation — it produced miscounts during T4 verification.

### Step 3: Apply filters

Filter by `--since`, `--command`, `--all` flags. Default: last 14 days.

### Step 4: Compute aggregations per command

For each command appearing in the filtered set:
- Count runs
- Compute mean convergence from `fields_json` if the command emits it (pace/coa/pcv-research)
- Compute mean tokens if present in fields or notes
- Tally outcomes (complete/partial/failed)
- Find most recent run
- For each command, open the last N `command_performance_log.md` entries and extract the "Improvement signal" line — tally which signals appear >=2 times (recurring friction)

### Step 5: Render the table + footer

Compute SHA-256 of `run_log.csv` and `command_performance_log.md` for the evidence footer:

```bash
RUN_LOG_SHA=$(sha256sum "$RUN_LOG" 2>/dev/null | awk '{print $1}')
PERF_LOG_SHA=$(sha256sum "$PERF_LOG" 2>/dev/null | awk '{print $1}')
```

Output the table + aggregate stats + top signals + evidence footer to stdout AND write to `$EVIDENCE_DIR/runlog_reports/runlog_$(date +%Y-%m-%d_%H%M%S).md`.

### Step 6: Drill-down mode

If `--drill-down <run-id>` was passed:
1. Find the run_id in `run_log.csv`
2. Locate the per-run directory (e.g., `pace_runs/<run-id>/` or `council_sessions/<run-id>/`)
3. Render that run's `run_report.md` + `instrumentation.csv` detail

### Step 7: Emit its own run_report (recursive self-observability)

`/runlog` itself emits a run_report — otherwise we have an "observer with no logs" anti-pattern.

```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command runlog \
  --run-dir "$EVIDENCE_DIR/runlog_reports/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Longitudinal toolkit report (last $WINDOW_DAYS days)" \
  --fields "window_days=$WINDOW_DAYS rows_aggregated=$N_ROWS commands_covered=$N_COMMANDS recurring_signals=$N_RECURRING run_log_sha=$RUN_LOG_SHA"
```

## Important Constraints

- **Read-only**: NEVER write to `run_log.csv` or `command_performance_log.md`. These are append-only artifacts produced by other commands.
- **No network**: `/runlog` never calls external services. All data is local.
- **Deterministic**: Re-running with the same CSVs produces the same table. This is the PLN verifiability guarantee.
- **Silent on missing data**: If a command has no runs in the window, it's omitted from the table (not "N/A" row). Transparent about absence.
- **Never break on malformed rows**: If a CSV row has wrong column count or unparseable values, skip it and continue; include a note in the evidence footer: "Skipped N malformed rows."

## Classroom Use Case

Instructor / cohort grading use case:

```bash
cd student_name_submission/
/runlog --since 2026-09-01 --all
```

Output answers: Did this student run `/audit`? How many times? Which commands did they converge on? Is there a pattern of `/improve` findings they ignored?

This is direct input to the grading loop — NOT a replacement for judgment, but a structured evidence base.

## Smoke Test

From a fresh clone of the toolkit:

```bash
# Populate some fake rows
printf 'test1,pace,v1.1,2026-04-17,"fake",complete,opus,2026-04-17T00:00:00Z,"{}"\n' > /tmp/test_run_log.csv
/runlog --since 2026-04-17 --evidence-dir /tmp
# Expected: table with one /pace row, outcome complete.
```

## Limitations

- `fields_json` parsing is regex-based (no JSON library in bash). Complex nested fields may not parse cleanly — fields at the top level work fine.
- Very old v1.0 rows may lack `fields_json` entirely; the table falls back to per-command defaults for missing data.
- If the toolkit evidence-dir is stored on a slow filesystem (WSL↔OneDrive), large `run_log.csv` reads may take 1-3 seconds. Runtime bounded at 10s via a `timeout` wrapper.
