---
allowed-tools: Bash(git:*), Read, Write, Glob, Agent
description: Create a dated summary of today's work in the daily summaries folder
---

# /dailysummary — Daily Work Summary

## Mode Selection

**Two modes** — pick based on session weight:

- `/dailysummary` or `/dailysummary --full` — **Full mode.** All sections, wiki-links, navigation, numerical verification, `/improve` candidates. Use after heavy sessions (multiple deliverables, code changes, multi-agent runs).
- `/dailysummary --quick` — **Quick mode.** Stripped down: Date, Summary (3-4 sentences), Key Accomplishments (bullets), Next Steps, Commits. No wiki-links, no `/improve` candidates, no numerical verification, no navigation link. Use after light sessions (documentation edits, planning, conversations).

**Default**: If `$ARGUMENTS` is empty or `--full`, run full mode. If `$ARGUMENTS` contains `--quick`, run quick mode. If unsure which mode fits, check git diff — if fewer than 5 files changed, suggest quick mode to the user.

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

**IMPORTANT**: This summary should be written by a **Sonnet** model subagent when available. Spawn a single Agent with `model: "sonnet"` and pass it the gathered information (git log, file changes, context) along with the formatting instructions below. The Sonnet agent writes the summary; the main agent saves it.

The reason for preferring Sonnet: smaller models have been observed to produce inaccurate numerical figures, wrong file orderings, and incorrect parameter values when summarizing technical sessions. Sonnet's accuracy on project-specific details justifies the cost.

**If Sonnet is unavailable** (e.g., user's plan does not include it), use the best available model but add an extra verification step: after the summary is drafted, re-read the source files for any numerical values mentioned and confirm they match. Flag any values that could not be verified with `(unverified)` next to the number.

---

## Step 1: Gather Information

Run these in parallel:
- `git log --since="today" --pretty=format:"%h - %s (%ar)" --no-merges` — today's commits
- `git status` — current working state
- `git diff --stat` — modified file statistics
- List any new untracked files relevant to the session
- If today's commits are empty, review commits from the last 24 hours

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

$ARGUMENTS
