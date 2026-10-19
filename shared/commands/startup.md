---
allowed-tools: Read, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(date:*), Bash(ps:*), Bash(free:*), Bash(vm_stat:*)
description: Session startup — reads recent daily summaries, derives the active workstreams from them, shows where each left off, what is blocking, and the next action
---

# /startup — Session Startup Briefing

> **When to use**: At the start of every work session. Reads your recent daily summaries and orients you on all active workstreams — what's done, what's next.
>
> **Prerequisite**: Requires daily summaries written by `/dailysummary`. If your summary folder is empty or missing, `/startup` falls back to `git log --oneline -10` and open file context — useful orientation, but not the full workstream picture. Build the habit of running `/dailysummary` at the end of each session first.
>
> **Usage**: `/startup` reports every active workstream. `/startup <keyword>` reports one workstream in depth and the rest in one line each.

You are executing the `/startup` command. Your job is to quickly orient the user on the current state of ALL active workstreams by reading recent daily summaries and project state, then presenting a concise action-ready briefing.

**Goal**: Get from "just opened the terminal" to "working on the right thing" in under 60 seconds of reading.

`/startup` is read-only. The only things it writes are the run report in Step 6 and, if the user says yes, new keys in `~/.claude/toolkit-config.md`.

---

## STEP 0: Read Project Configuration

Read `~/.claude/toolkit-config.md` to load:
- `project_name` — the name of this project
- `project_type` — `research` or `teaching`; sets what counts as outward-facing in Step 3
- `workstreams` — the workstreams the user expects to see (a hint, not the answer — see Step 2)
- `summary_folder` — where daily summaries live (default: `Daily Summary`)
- `weekly_folder` — where weekly summaries live (default: `Weekly Summary`)
- `evidence_dir` — where run evidence is written (default: `.toolkit/evidence`)

Optional keys used by this command:
- `startup_exclude` — workstreams `/startup` never reports (default: none)
- `backlog_file` — a cross-cutting backlog file, relative to the project root (default: look for `BACKLOG.md`, `TODO.md`, or `plans/BACKLOG.md` at the root)
- `scheduled_jobs` — jobs whose logs `/startup` checks, one entry per job as `name | cadence | log path` (default: no check)

If `~/.claude/toolkit-config.md` does not exist, use these defaults and note it in the briefing:
- `summary_folder`: `Daily Summary`
- `weekly_folder`: `Weekly Summary`
- `workstreams`: auto-detect from summary content
- `project_type`: `research`

**Missing optional keys never block the briefing.** If any of `startup_exclude`, `backlog_file`, or `scheduled_jobs` is missing, run with its default, then ask the user once — in a single question after the briefing, never before it — and offer to save the answers to `~/.claude/toolkit-config.md`. If the user has nothing to add, offer to save `[]` or `none` so the question does not come back.

---

## STEP 0b: Resolve the Environment

Do this before anything else. **Never report a workstream, file, or folder as missing until this step is done.**

| What | Where |
|---|---|
| Project root | `git rev-parse --show-toplevel`; if not a git repo, the current directory |
| Daily summaries | `<root>/<summary_folder>/` |
| Weekly summaries | `<root>/<weekly_folder>/` |
| Memory index | `MEMORY.md` at the project root, or `~/.claude/projects/<encoded root>/memory/MEMORY.md`, where `<encoded root>` is the project's absolute path with every character that is not a letter or digit replaced by `-`. If that directory does not exist, list `~/.claude/projects/` and pick the entry that matches the project path. Never read another project's memory. |
| Backlog | `<root>/<backlog_file>`, or the default names above |

If the working directory is not the project root, say so on the **Root** line of the briefing.

**Paths that belong to another machine.** A path in an older document that does not resolve here — a Windows or WSL path such as `/mnt/c/...` on a Mac, or another user's home directory — means the document is stale, not that the work is gone. Look for the same relative path under the current project root before reporting anything missing.

**Large repositories, and repositories on cloud-synced or network drives.** Some git and search operations get slow in predictable ways:
- `git log`, `git show`, and path-scoped `git status` are cheap. Use them freely.
- A whole-tree `git status` or `git diff` can take minutes. Scope it to each workstream's directory: `git status -s -- "<dir>"`.
- `git branch --contains` can time out on a long history. To check whether a commit reached the remote, use `git merge-base --is-ancestor <sha> origin/<branch>`.
- A repo-wide search re-walks every agent worktree under `.claude/worktrees/` and every virtual environment. Scope each search to a workstream directory, or exclude `.claude/worktrees`, `.venv*`, and `node_modules`.

**Settled conditions.** If the memory index records a condition the user has already accepted (a branch that is never pushed, a known divergence from the remote, a tool that is deliberately absent), do not report it as a blocker again.

---

## MODE

- **No argument** — report every workstream with movement in the recent summaries or an open item.
- **A keyword** — report ONE workstream in depth and compress the rest to one line each. Match the keyword against the workstream list derived in Step 2: its name, its directory, the title words of its summary filenames, or a person's name attached to it (a co-author, a client, a course). If nothing matches, say `"No workstream matches '<keyword>' — running full mode."` and run full mode. **Never substitute a different workstream or project for the one asked about.**
- **A keyword that names an excluded workstream** — point at its directory and stop.

"In depth" means: the full workstream block, its entries from the last three summaries that mention it, every open item from its work lists and the backlog, and its scoped `git log` and `git status`.

### Abandon cleanly when the user redirects mid-briefing

This command runs several gather steps before it outputs anything, so a redirect that arrives mid-run leaves a half-built briefing. Say one line and drop it:

> `"Stopping the briefing here — <new task> takes priority. Nothing from the startup gather is written anywhere, so there is no partial state to clean up."`

Then switch to the new task. Do not finish the briefing first, and do not offer to resume it. Without that line, a reader of the transcript cannot tell an abandoned briefing from one that failed silently.

**A partial gather is not evidence.** Step 3's ranking is what makes a gathered fact meaningful, and an abandoned run never reached it. Never quote a workstream status collected for an unfinished briefing; anything worth keeping gets re-checked in the new task's own terms.

---

## EXECUTION

### Step 1: Gather Context (run in parallel where possible)

1. **The recent daily summaries** — the primary evidence source; everything else is corroboration. Read the 10–15 most recent files in `summary_folder`, ordered by the `YYYY-MM-DD` date at the start of the filename (fall back to `ls -t` for files without one — modification times are unreliable on synced drives). Also list, without reading, every summary filename from the last six weeks; Step 2 uses them.
2. **The latest weekly summary** in `weekly_folder`, if one exists — for its carried-forward TODOs and its dormant-workstream list.
3. **The memory index** (path from Step 0b) — for current project state, key decisions, and settled conditions. Read any memory file it points to that bears on today's work.
4. **Git, scoped.** `git log --oneline -10` and `git rev-parse --abbrev-ref HEAD`. Then `git status -s -- "<dir>"` for each workstream that looks active. Use a whole-tree `git status -s` only on a small repository.
5. **Work lists written to disk.** Audit findings and task lists usually live in dated files, not in a transcript. Look for recently modified files with a date in the name (`*_YYYY-MM-DD*.md`) inside the directories the active workstreams' summaries name under Files Modified/Added.
6. **The backlog** (`backlog_file`), and any backlog inside a workstream's directory. Check whether a deferred item's stated re-trigger (a date, an event, "after X ships") has now fired — that is the cheapest ready work there is.
7. **Scheduled jobs** (`scheduled_jobs`). For each job, find when its log last recorded a run — prefer the newest timestamp written inside the log (read only its last lines), and fall back to the file's modification time, saying so. Mark the job **MISSED** if that is older than one cadence period plus one day. A missing log means the job never ran or logs elsewhere; say you cannot tell which. Never assume a job ran because it is scheduled.
8. **System.** `ps aux`, filtered for long-running language runtimes (Python, Julia, R, Node, etc.) that may be sweeps or servers still active from a prior session. Report PID and command; do not stop anything. Report available memory if one command gives it (`free -h` on Linux; `vm_stat` on macOS, converting pages with the page size it prints); otherwise write `not checked`.

**Do not read code or data files** — only summaries, status documents, plans, backlogs, logs, and MEMORY.md.

### Step 2: Derive the Active Workstream List — Do Not Hardcode It

**A roster typed in once goes stale and then misleads.** Derive the list at run time from the summaries over roughly the last six weeks:
- the title words of each summary filename (`2026-03-12_Calibration_Sweep_Done.md` → calibration),
- the section headers and recurring topics inside the summaries you read,
- the `workstreams` list from config, used to name and order what you find, not to limit it.

Then:
- **Drop every workstream in `startup_exclude`.** Its summaries may sit in the same folder as everyone else's; seeing them is not a reason to report them. Filter silently.
- A workstream in `workstreams` with no summary in the window goes under Stale Workstreams in one line.
- A workstream found in the summaries but missing from `workstreams` is reported normally; add it to the single config question at the end.

For each workstream, extract:
- **Last touched** — date, and what was done (1–2 sentences)
- **Left off at** — the specific next step from the summary's "Next Steps" section
- **Blocking** — any decision or external dependency needed before proceeding
- **Open** — the one file to read or command to run to resume
- **Directory** — where its work lives, from the paths its summaries name

A workstream with nothing open gets one line or is omitted.

**Work with no summary behind it.** The newest summary is not reliably the newest work. For each active workstream, compare its newest summary date with its newest commit date: `git log -1 --date=short --format=%cd -- "<dir>"`. If the commit is newer, label the workstream **UNDOCUMENTED**, name the gap (dates and commit count), and offer to write the missing summary with `/dailysummary`. Undocumented output ranks high because the record is what makes a claim checkable later.

**No summaries at all.** Derive workstreams from `git log` commit messages and the top-level directories they touch, and head the briefing with `Derived from git history only — no daily summaries found.`

### Step 3: Assess Priority

Rank workstreams by:
1. **Blocking or overdue** — a running process or pending decision, a MISSED scheduled job, a dated item due within seven days or already past due, a decision the user has already been asked about.
2. **Outward-facing** — anything another person will read or rely on; these carry the highest cost of being wrong. For `project_type: research`: drafts for an advisor, co-author, or committee; journal or conference submissions; reviewer responses. For `project_type: teaching`: anything going to students (assignments, solutions, grades, feedback, posted materials) and course-calendar dates.
3. **Recency** — what the user actually had open last session.
4. **Momentum** — a workstream with clear documented next steps is ready to resume.
5. **Work with no summary behind it.**

Break ties by the order of `workstreams` in config.

### Step 4: Present the Briefing

Output the briefing in this exact format:

```
# Session Startup — YYYY-MM-DD (Day)

## System Status
- **Project**: [project_name] ([project_type])
- **Root**: [project root; note if the working directory is elsewhere]
- **Git**: [branch] — [N uncommitted files, scoped to <dirs> / whole tree / not a git repo]
- **Processes / memory**: [None / description + PID]; [X.XG available / not checked]
- **Scheduled**: [All ran on time / MISSED: job (last ran YYYY-MM-DD) / not configured]

---

## Active Workstreams

### 1. [Workstream Name] — [One-line status]
- **Last touched**: [Date] — [What was done]
- **Left off at**: [Specific next step]
- **Blocking**: [None / Decision needed: ...]
- **Open**: [Specific file to read or command to run]

### 2. [Next workstream...]
[...]

[Quiet workstreams with an open item: one line each]

---

## Calendar
- [YYYY-MM-DD] — [what is due, overdue, or upcoming] ([source file])

## Recommended Focus

**[Workstream Name]** — [Why this one, 1 sentence]

**First action**: [Exact first action — e.g., "Read `file.md` then run the sweep" or "Draft the next section"]

## Decisions Waiting on You
- [Decision] — open since [date] ([source file]), oldest first

---

## Stale Workstreams (>7 days inactive)
- [Workstream]: Last active [date]. [One-line status.]
```

### Status Labels
- Active (worked on in last 3 days): no label needed
- Ready to resume (clear next steps): no label needed
- **BLOCKED** — waiting on a decision or external dependency
- **OVERDUE** — a dated item or scheduled job is past due
- **UNDOCUMENTED** — commits newer than its latest summary
- **STALE** — no activity in >7 days

### Formatting Rules
- Keep the briefing under 60 lines, not counting the Evidence Footer
- No filler — every line should help the user decide what to work on
- Include file paths and exact commands so the user can jump straight to the relevant context
- If a workstream has no clear next step, say so explicitly rather than inventing one
- **Quote figures from the document that owns them; never recompute one in the briefing.** If two documents disagree, say so and name both — do not silently pick one
- Every Calendar entry names the file its date came from. If nothing dated was found, write `Nothing dated in the sources read.`
- Carry unresolved decisions forward: a decision stays open until a later summary or the backlog records it settled
- State what you did not check. A briefing that hides its own gaps is worse than a shorter one
- Do NOT read the actual code/data files — only the sources listed in Step 1

---

## Step 5: Evidence Footer (append to briefing)

End the briefing with a standardized footer that makes the startup read locally verifiable: every line can be checked against files on disk. This lets instructors diagnose "did the student write summaries this week?" vs "did /startup miss them?".

```markdown
---

## Evidence Footer

- Command version: v2.0
- Run timestamp: YYYY-MM-DD HH:MM:SSZ (UTC)
- Mode: full / keyword "<kw>" / keyword "<kw>" not matched → full
- Summaries read: N (oldest: date, newest: date); filenames scanned for derivation: M (since date)
- Weekly summary: <file> / none
- MEMORY.md: <path> / not found (mtime: ...)
- Backlog: <path> / not found
- Scheduled jobs: N checked, M missed / not configured
- Git branch: main / feature-branch / detached / not a git repo
- Git status: N uncommitted files (scope: <dirs> / whole tree)
- Workstreams detected: N (from summaries) + M (from config.workstreams only); K excluded
- Undocumented workstreams: N
- Config loaded: ~/.claude/toolkit-config.md / defaults-only; missing keys: [...]
- Background processes: N long-running
- Not checked: [list / nothing skipped]
```

If any optional key was missing, or a workstream was found that is not in `workstreams`, ask the single config question here, after the footer.

## Step 6: Emit run_report (instrumentation)

After presenting the briefing, emit a structured run_report for observability via `/runlog`:

```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command startup \
  --tool-version v2.0 \
  --evidence-dir "$evidence_dir" \
  --run-dir "$summary_folder/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Session startup briefing" \
  --fields "mode=$MODE summaries_read_count=$N_SUMMARIES oldest_summary_date=$OLDEST newest_summary_date=$NEWEST workstreams_detected=$N_WORKSTREAMS undocumented_count=$N_UNDOCUMENTED missed_jobs=$N_MISSED git_head_sha=$HEAD_SHA memory_found=$MEMORY_FOUND"
```

One-line call via the helper. Skip silently if the helper is unavailable — the user's briefing output must NEVER be blocked by instrumentation.

> **What next?** Plan to run `/dailysummary` at the end of this session — that's what makes the next `/startup` useful. Without a closing summary, today's work won't appear in tomorrow's briefing.

$ARGUMENTS
