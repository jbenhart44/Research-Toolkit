---
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(date:*)
description: Session startup — reads recent daily summaries, identifies all active workstreams, shows where each left off and what to do next
---

# /startup — Session Startup Briefing

> **When to use**: At the start of every work session. Reads your recent daily summaries and orients you on all active workstreams — what's done, what's next.

You are executing the `/startup` command. Your job is to quickly orient the user on the current state of ALL active workstreams by reading recent daily summaries and project state, then presenting a concise action-ready briefing.

**Goal**: Get from "just opened the terminal" to "working on the right thing" in under 60 seconds of reading.

---

## STEP 0: Read Project Configuration

Read `~/.claude/toolkit-config.md` to load:
- `project_name` — the name of this project
- `workstreams` — the list of active workstreams
- `summary_folder` — where daily summaries live (default: `Daily Summary`)
- `weekly_folder` — where weekly summaries live (default: `Weekly Summary`)

If `~/.claude/toolkit-config.md` does not exist, use these defaults and note it in the briefing:
- `summary_folder`: `Daily Summary`
- `weekly_folder`: `Weekly Summary`
- `workstreams`: auto-detect from summary content

---

## EXECUTION

### Step 1: Gather Context (run in parallel where possible)

1. **List and read the 8 most recent daily summaries** from `summary_folder` — use `ls -t` to sort by modification time, then read them. These are the primary evidence source for workstream status.
2. **Read MEMORY.md** (if present at project root or `~/.claude/projects/*/memory/MEMORY.md`) — for current project state and key architectural decisions.
3. **Check git status** — `git status` to see uncommitted changes from a previous session.
4. **Check for running background processes** — `ps aux | grep -v grep` filtered for any long-running language runtimes (Python, Julia, R, Node, etc.) that may be sweeps or servers still active from a prior session.

### Step 2: Extract Workstream Status

From the daily summaries (and the `workstreams` list from config), identify every distinct workstream that has been active in the past 30 days.

For each workstream found, extract:
- **Last activity date**
- **What was done last** (1-2 sentences)
- **Where it left off** (specific next step documented in the summary's "Next Steps" section)
- **Blocking decisions** (any user input needed before proceeding)
- **Key files** (the most important file to open or read to resume)

### Step 3: Assess Priority

Rank workstreams by:
1. **Recency** — more recent = higher priority (the user was actively working on it)
2. **Blocking status** — if a process is running or a decision is pending, flag it first
3. **Momentum** — if a workstream has clear documented next steps, it is ready to resume
4. **Config priority** — if `workstreams` in config is ordered, treat earlier items as higher priority

### Step 4: Present the Briefing

Output the briefing in this exact format:

```
# Session Startup — YYYY-MM-DD

## System Status
- **Project**: [project_name from config]
- **Uncommitted changes**: [Yes (N files) / No]
- **Running background processes**: [None / process description + PID]

---

## Active Workstreams

### 1. [Workstream Name] — [One-line status]
- **Last session**: [Date] — [What was done]
- **Left off at**: [Specific next step]
- **Blocking**: [None / Decision needed: ...]
- **Resume**: [Specific file to read or command to run]

### 2. [Next workstream...]
[...]

---

## Recommended Focus

Based on recency and priority, I recommend starting with:

**[Workstream Name]** — [Why this one, 1 sentence]

**To resume**: [Exact first action — e.g., "Read `file.md` then run the sweep" or "Draft the next section"]

---

## Stale Workstreams (>7 days inactive)
- [Workstream]: Last active [date]. [One-line status.]
```

### Status Labels
- Active (worked on in last 3 days): no label needed
- Ready to resume (clear next steps): no label needed
- **BLOCKED** — waiting on a decision or external dependency
- **STALE** — no activity in >7 days

### Formatting Rules
- Keep the entire briefing under 80 lines
- No filler — every line should help the user decide what to work on
- If a workstream has no clear next step, say so explicitly
- Include file paths so the user can jump straight to the relevant context
- Do NOT read the actual code/data files — only summaries and MEMORY.md

$ARGUMENTS
