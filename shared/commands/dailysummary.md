---
allowed-tools: Bash(git:*), Read, Write, Glob, Agent
description: Create a dated summary of today's work in the daily summaries folder
---

# /dailysummary — Daily Work Summary

> **When to use**: At the end of a work session to capture what was done, decisions made, and next steps. Creates a dated record that `/startup` and `/weeklysummary` read later.

## Mode Selection

**Three modes** — pick based on session weight:

- `/dailysummary` or `/dailysummary --full` — **Full mode.** All sections, wiki-links, navigation, numerical verification, `/improve` candidates. Use after heavy sessions (multiple deliverables, code changes, multi-agent runs).
- `/dailysummary --quick` — **Quick mode.** Stripped down: Date, Summary (3-4 sentences), Key Accomplishments (bullets), Next Steps, Commits. No wiki-links, no `/improve` candidates, no numerical verification, no navigation link. Use after light sessions (documentation edits, planning, conversations).
- `/dailysummary --append-pointer` — **Append-pointer mode (NEW in v1.1).** Writes a ≤10-line block APPENDED to an existing same-day summary file. Use for mid-session continuations where a new file would be clutter. Auto-selected when an existing same-day summary exists AND `git diff` shows <3 modified files since last write.

**Default behavior**:
1. **Check for existing same-day file first** (Step 0c below). If one exists and mtime is <30 min old → `--append-pointer` unless user overrides.
2. If `$ARGUMENTS` is empty or `--full`, run full mode.
3. If `$ARGUMENTS` contains `--quick`, run quick mode.
4. **Auto-quick on zero-diff**: If `git diff --stat` reports zero modified files AND no new untracked files → automatically run quick mode and flag "Session had no file changes — summary is context-only."
5. If unsure which mode fits, check git diff — if fewer than 5 files changed, suggest quick mode to the user.

---

## Timing Recommendation

**Invoke /dailysummary at the END of a session, not the middle.** Mid-session invocations produce incomplete summaries that require re-running. If you must run mid-session, mark the summary as DRAFT and update before session close.

If this command detects that significant work has occurred AFTER a previous daily summary was written (by checking git status for modified files not covered in the existing summary), it should UPDATE the existing file rather than creating a new one.

---

## Step 0: Read Project Configuration

Read `~/.claude/toolkit-config.md` to load:
- `summary_folder` — where to write daily summaries (default: `Daily Summary`)
- `project_name` — for context when the Sonnet agent writes the summary

If `~/.claude/toolkit-config.md` does not exist, use `Daily Summary` as the folder.

---

## Step 0c: Filename Resolution (NEW in v1.1 — do this BEFORE git operations)

Cheap and deterministic. Decides mode + output path before spending tokens on analysis.

```bash
TODAY=$(date +%Y-%m-%d)
EXISTING=$(ls -1 "$summary_folder/" 2>/dev/null | grep "^${TODAY}_" | head -1)

if [ -n "$EXISTING" ]; then
  EXISTING_PATH="$summary_folder/$EXISTING"
  MTIME=$(stat -c %Y "$EXISTING_PATH" 2>/dev/null)
  AGE_MIN=$(( ( $(date +%s) - MTIME ) / 60 ))
  if [ "$AGE_MIN" -lt 30 ]; then
    MODE="APPEND_POINTER"      # same-session continuation, write short block
    OUTPUT_PATH="$EXISTING_PATH"
  else
    MODE="NEW_SESSION_2"        # new session today, use HHMM suffix
    HHMM=$(date +%H%M)
    OUTPUT_PATH="$summary_folder/${TODAY}_${HHMM}_<TITLE>.md"
  fi
else
  MODE="NEW"
  OUTPUT_PATH="$summary_folder/${TODAY}_<TITLE>.md"
fi
```

Report the resolved mode + path to the user BEFORE proceeding to Step 1: `"Mode: $MODE — writing to $OUTPUT_PATH"`.

If `$ARGUMENTS` explicitly overrides (`--full`, `--quick`, `--append-pointer`), honor that over the auto-selection — but still print what the auto-selection would have been.

---

**IMPORTANT**: This summary should be written by a **Sonnet** model subagent when available. Spawn a single Agent with `model: "sonnet"` and pass it the gathered information (git log, file changes, context) along with the formatting instructions below. The Sonnet agent writes the summary; the main agent saves it.

The reason for preferring Sonnet: smaller models have been observed to produce inaccurate numerical figures, wrong file orderings, and incorrect parameter values when summarizing technical sessions. Sonnet's accuracy on project-specific details justifies the cost.

**If Sonnet is unavailable** (e.g., user's plan does not include it), use the best available model but add an extra verification step: after the summary is drafted, re-read the source files for any numerical values mentioned and confirm they match. Flag any values that could not be verified with `(unverified)` next to the number.

---

## Step 1: Gather Information (FAST-PATH, v1.1)

Naive git calls can take 30-120s on slow filesystems (e.g., network drives, OneDrive-synced WSL). Use timeouts + parallel reads to bound the worst case.

```bash
# All three git reads in parallel, each bounded at 5s
timeout 5 git log --since="today" --pretty=format:"%h %s" --no-merges > /tmp/ds_commits.txt 2>/dev/null &
timeout 5 git status --porcelain > /tmp/ds_status.txt 2>/dev/null &
timeout 5 git diff --stat --no-renames HEAD > /tmp/ds_diffstat.txt 2>/dev/null &
wait
```

**If `git status` does not return in 5s** (the `timeout` triggers): proceed without it. Note in the Technical Details section: "git status unavailable — summary derived from session context only."

**Do NOT** call `git diff` (no `--stat`) — that prints full patches and can be 10x slower. Use `--stat` only.

**Source-file verification discipline**: Read `.qmd`, `.jl`, `.csv`, or other source files ONLY when the summary cites a specific numerical value from them. Do NOT preemptively read source files "just in case" — cross-filesystem reads are the biggest hidden cost. If the session involved no new empirical values (infrastructure work, documentation, planning), skip source-file verification entirely.

---

## Step 2: Analyze Work Done

- Identify all files modified, added, or deleted
- Group changes by logical area (e.g., research, documentation, code, experiments, infrastructure)
- Note any significant functionality added or changed
- Highlight research findings, decisions, or milestones
- Check whether any prior daily summary in `summary_folder` from today already exists — if so, update it rather than creating a duplicate

---

## Step 3: Create the Summary Document

**Filename format**: `YYYY-MM-DD_Brief_Title.md` (e.g., `2025-10-13_Model_Calibration_Complete.md`)

**Write to**: the `summary_folder` from config (default: `Daily Summary`)

**Sections to include**:

- **Date**: Full date
- **Summary**: 2-3 sentence overview of the day's work
- **Key Accomplishments**: Bulleted list of main achievements
- **Files Modified/Added**: Organized by category
- **Technical Details**: Important implementation details, parameter values, or findings
- **Next Steps**: TODOs or follow-up items (if apparent from context)
- **Commits**: List of commit messages made today (if any)

---

## Step 4: Format Guidelines

- Use clear markdown formatting
- Keep it concise but informative
- Focus on WHAT was done and WHY (not just a file list)
- Include relevant code snippets or key findings if significant
- Make it useful for future reference and for the weekly summary aggregation

**CROSS-REFERENCE FORMAT (Wiki-Links)**: When referencing files, findings, or other summaries, use `[[filename.md]]` syntax. Ambiguous names include one parent directory: `[[subfolder/filename.md]]`. This is a formatting convention — just write links this way instead of backtick paths.

**NAVIGATION LINK**: When gathering git info in Step 1, also run `ls -1 "summary_folder/" | grep "^202" | sort | tail -1` to find the most recent prior summary. Add `Previous: [[filename]]` as the first line of the document. Skip if no prior summary exists.

**NUMERICAL ACCURACY IS CRITICAL**: When reporting parameter values, thresholds, metrics, or any empirical figures — verify against the actual source files before writing. Do NOT approximate from memory or conversation context. If a value cannot be verified from files, write it as approximate and flag it.

**Title Selection**: Choose a descriptive 3-5 word title that captures the essence of the day's work. Examples: `Model_Calibration_Complete`, `Documentation_Restructure`, `Experiment_Results_Analyzed`.

---

## Step 5: Infrastructure Improvement Candidates (full mode only)

After writing the summary, review the session's work for `/improve` candidates. Look for:
- **Commands used** — did any slash command produce friction, ambiguity, or suboptimal results?
- **Reference files** — were any missing information that the user had to provide manually?
- **CLAUDE.md rules tested** — did any rule cause confusion or need clarification?
- **Recurring patterns** — did the same type of fix or workaround happen multiple times?
- **New workflows** — did the session establish a pattern that should be codified?

Add a final section to the summary:
- **`/improve` Candidates**: Bulleted list of specific improvement suggestions (command name + what to fix), or "None identified" if the session was clean. Keep to 1-3 items max — only flag things with clear evidence from this session.

After saving, if candidates were identified, suggest:
> "I identified [N] potential infrastructure improvements. Run `/improve` to generate a detailed report, or address them next session."

---

Start by gathering information in Step 1, then synthesize into a well-organized daily summary document.

---

## Step 6: Evidence Footer (NEW in v1.1 — append to every summary)

Every summary — full, quick, or append-pointer — ends with a standardized footer block. This converts the summary from OPAQUE prose into a locally-verifiable record (PLN verifiability principle).

```markdown
---

## Evidence Footer

- Command version: v1.1
- Run timestamp: YYYY-MM-DD HH:MM:SSZ (UTC)
- Mode: full / quick / append-pointer
- Inputs read: git log (N lines), git status (M files), git diff --stat (K files)
- Output path: Daily Summary/YYYY-MM-DD_Title.md
- Git SHA at session start: <sha> (from `git rev-parse HEAD` at session start if captured, else "not captured")
- Git SHA at summary write: <sha>
- Unverified values: N (count of empirical figures not cross-checked against source files)
- Subagent: sonnet (or haiku/opus if overridden)
```

Any user re-running the command at the same time with the same git state should get the same table modulo timestamps.

## Step 7: Emit run_report (NEW in v1.1 — instrumentation)

After writing the summary, emit a structured run_report for observability via `/runlog`:

```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command dailysummary \
  --run-dir "$summary_folder/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Daily summary for $TODAY ($MODE mode)" \
  --fields "mode=$MODE files_touched_count=$FILES_TOUCHED git_sha_start=$SHA_START git_sha_end=$SHA_END unverified_count=$UNVERIFIED_N"
```

This is a ONE-LINE call. The helper handles YAML formatting, CSV append, and atomicity.

If the helper is not available (e.g., toolkit not installed at expected path), skip this step silently. The primary summary output must NEVER be blocked by instrumentation failure.

---

> **What next?** If the summary flagged any `/improve` candidates, run `/improve` at the start of your next session to action them while the context is warm.

$ARGUMENTS
