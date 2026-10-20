---
allowed-tools: Bash(git:*), Bash(date:*), Bash(ls:*), Bash(stat:*), Bash(python3:*), Read, Write, Edit, Grep, Glob, Agent
description: Create a dated summary of today's work in the daily summaries folder
---

# /daily-summary — Daily Work Summary

> **When to use**: At the end of a work session to capture what was done, decisions made, and next steps. Creates a dated record that `/startup` and `/weekly-summary` read later.

## Mode Selection

**Three modes** — pick based on session weight:

- `/daily-summary` or `/daily-summary --full` — **Full mode.** All sections, wiki-links, navigation, numerical verification, `/improve` candidates. Use after heavy sessions (multiple deliverables, code changes, multi-agent runs).
- `/daily-summary --quick` — **Quick mode.** Stripped down: Date, Summary (3-4 sentences), Key Accomplishments (bullets), Next Steps, Commits. No wiki-links, no `/improve` candidates, no numerical verification, no navigation link. Use after light sessions (documentation edits, planning, conversations).
- `/daily-summary --append-pointer` — **Append-pointer mode.** Writes a ≤10-line block APPENDED to an existing same-day summary file. Use for mid-session continuations where a new file would be clutter. Auto-selected when a same-day summary for this session's workstream exists AND `git diff` shows <3 modified files since last write.

**Every mode** runs the commit inventory (Steps 1b–1d) and the saved-file checks (Step 7). The Commits and Next Steps sections appear in every mode, and each check costs one tool call.

**Default behavior**:
1. **Check for an existing same-day file first** (Step 0c). If one exists for this workstream and its mtime is <30 min old → `--append-pointer` unless the user overrides.
2. If `$ARGUMENTS` is empty or `--full`, run full mode.
3. If `$ARGUMENTS` contains `--quick`, run quick mode.
4. **Auto-quick on zero-diff**: If `git diff --stat` (scoped per Step 0b) reports zero modified files AND no new untracked files → automatically run quick mode and flag "Session had no file changes — summary is context-only."
5. If unsure which mode fits, check git diff — if fewer than 5 files changed, suggest quick mode to the user.

---

## Timing Recommendation

**Invoke /daily-summary at the END of a session, not the middle.** Mid-session invocations produce incomplete summaries that require re-running. If you must run mid-session, mark the summary as DRAFT and update before session close.

If this command detects that significant work has occurred AFTER a previous daily summary was written (by checking git status for modified files not covered in the existing summary), it should UPDATE the existing file rather than creating a new one.

**Sessions that cross midnight.** File the summary under the date the session's commits carry, not the wall-clock date. If the work landed on the 8th and it is now the 9th, update the 8th's summary. A summary's date is a claim about when the work happened, and both the `Previous:` chain and the one-file-per-working-day convention depend on it being true.

---

## Step 0: Read Project Configuration

Read `~/.claude/toolkit-config.md` to load:
- `summary_folder` — where to write daily summaries (default: `Daily Summary`)
- `project_name` — context for the writer subagent
- `author_name` — so the writer refers to the author by name (Step 5)
- `workstreams` — to name the session's workstream (Step 0b) and pick the `Previous:` link (Step 4)
- `project_type` — `teaching` turns on the grade-privacy rule (Step 5)
- `evidence_dir` — where the run-log row is written (default: `.toolkit/evidence`; Step 9)
- `extra_repos` — other git repositories this project's sessions commit to (Step 1c)

If `~/.claude/toolkit-config.md` does not exist, use `Daily Summary` as the folder and the defaults above.

If `extra_repos` is missing (or the config file is), ask the user once — *"Does work in this project also get committed to other git repositories, such as a paper's Overleaf clone or a separate data repo?"* — and offer to save the answer to `~/.claude/toolkit-config.md`. An empty list (`extra_repos: []`) is a valid answer and stops the question from recurring.

**Resolve `summary_folder` against the project root** (`git rev-parse --show-toplevel`), not the shell's current directory. A session started in a parent or home directory can find a different, stale folder with the same name, and then both the save path and the `Previous:` link come out wrong. If more than one candidate exists, use the one under the project root and tell the user which one you used.

---

## Step 0b: Session Scope and Date

Decide two things before any git call.

**Scope** — the directory (or directories) this session's work lives in, taken from the session's own record of the files it created or edited. If it corresponds to one of the configured `workstreams`, name that workstream. In a repository that holds several workstreams, every git command below takes the scope as a pathspec, for two reasons:

- **Speed.** `git status` and `git diff` walk the whole tree. In one large research repository, a repo-wide `git status --porcelain` took 22 s (and timed out on a cold cache); scoped to one directory it took 0.8 s.
- **Attribution.** On a day with several terminals or collaborators, a repo-wide log lists commits that are not this session's work.

Use `.` (the whole repo) when the project is small or the session touched most of it. If the session touched several separate areas, run each scoped command once per area rather than once over the whole tree.

If git is slow even when scoped, count untracked files first:

```bash
git status --porcelain -uall | grep -c '^??'
```

A five-figure answer means some large untracked tree (data, a virtual environment, build output) is walked on every call. Suggest adding it to `.git/info/exclude` — local, unlike `.gitignore`, so it does not decide for anyone whether that tree should ever be committed. It is not a git bug.

**Summary date** — today's date, unless the session crossed midnight (see Timing Recommendation). Confirm against the dated log in Step 1b and correct the filename before saving if needed.

**Shell state does not persist between Bash tool calls.** A variable set in one call is empty in the next, and an empty pathspec silently widens a scoped command to the whole repo — re-creating the cost the scope exists to avoid. Write the literal scope path and date into every command below.

---

## Step 0c: Filename Resolution (do this BEFORE git operations)

Cheap and deterministic. Decides mode + output path before spending tokens on analysis.

```bash
SUMMARY_DIR="Daily Summary"   # literal summary_folder, resolved in Step 0
DAY="YYYY-MM-DD"              # literal summary date from Step 0b
ls -1t "$SUMMARY_DIR/" 2>/dev/null | grep "^${DAY}_"     # same-day summaries, newest first
```

If same-day files exist, pick the one about this session's workstream (match the workstream name in the filename, or read its Summary line). A same-day summary that another terminal wrote about a different workstream does not count as existing here. For the matching file, get its age:

```bash
F="Daily Summary/YYYY-MM-DD_Title.md"                       # the matching file, literal
MTIME=$(stat -c %Y "$F" 2>/dev/null || stat -f %m "$F")     # GNU stat || BSD/macOS stat
echo "age_min=$(( ( $(date +%s) - MTIME ) / 60 ))"
```

| Situation | Mode | Output path |
|---|---|---|
| matching same-day file, modified <30 min ago | `APPEND_POINTER` (same-session continuation, write a short block) | that file |
| matching same-day file, older | `NEW_SESSION_2` (new session today) | `$SUMMARY_DIR/${DAY}_${HHMM}_<TITLE>.md`, `HHMM` from `date +%H%M` |
| no matching same-day file | `NEW` | `$SUMMARY_DIR/${DAY}_<TITLE>.md` |

Report the resolved mode + path to the user BEFORE proceeding to Step 1: `"Mode: <MODE> — writing to <OUTPUT_PATH>"`.

If `$ARGUMENTS` explicitly overrides (`--full`, `--quick`, `--append-pointer`), honor that over the auto-selection — but still print what the auto-selection would have been.

---

<!-- spawn: role=writer model=sonnet site=daily-summary#writer -->
**IMPORTANT**: This summary is written by a **Sonnet** model subagent. Spawn a single Agent with `model: "sonnet"` (the `writer` row of `references/model-roles.md`) and pass it the gathered information (git log, file changes, context) along with the formatting instructions below. The Sonnet agent writes the summary; the main agent saves it.

The reason for Sonnet, and never Haiku: smaller models have been observed to produce inaccurate numerical figures, wrong file orderings, and incorrect parameter values when summarizing technical sessions. Sonnet's accuracy on project-specific details justifies the cost.

<!-- BEGIN MODEL FAILURE -->
**MODEL FAILURE — when an agent cannot run on the model it requested.**
1. **A session or weekly limit** ("You've hit your session limit"). These limits are shared across all models, so another model does not help. Stop starting agents, quote the error and its reset time, and offer two choices: wait, or stop. Do not retry.
2. **An Opus limit, or a model the account cannot use, on the Chair's `opus` request** ("You've hit your Opus limit"; "There's an issue with the selected model"). Retry the Chair once on `sonnet`. Write `fallback_from: opus` and the error text into the run report, and name the model that ran in the printed model line.
3. **Any other error, or any other role.** Stop that role, quote the error, and offer the choices: retry as written, run that role on the session's model, or stop. Never change a role's model on your own; rule 2 is the only exception.
4. Do not rely on a fallback-model setting for this: Claude Code never switches models on an authentication, billing or rate-limit error.
<!-- END MODEL FAILURE -->

**If the user chooses to have the summary written on the session's model** (rule 3), add an extra verification step: after the summary is drafted, re-read the source files for any numerical values mentioned and confirm they match. Flag any values that could not be verified with `(unverified)` next to the number.

A capable writer still invents identifiers, rebuilds paths from bare filenames, drops facts it was given, and misreports its own edits. Step 5 lists what the writer must be handed; Step 7 lists what the main agent checks after it returns.

---

## Step 1: Gather Information

### 1a. Fast-path reads (bounded, parallel)

Naive git calls can take 30-120s on slow filesystems (network drives; cloud-synced folders such as OneDrive or Dropbox, whose sync client can also hold locks on `.git/index` for tens of seconds). Bound each call and run them in parallel.

**`timeout` is GNU coreutils and does not exist on stock macOS.** There, `timeout 10 git status` fails instantly with `command not found`, which looks like a git failure. The block below uses `timeout` or `gtimeout` (Homebrew coreutils) if either exists, and otherwise runs git bare — the Bash tool's own timeout then bounds the call.

```bash
SCOPE="path/to/workstream"    # literal, from Step 0b; "." for the whole repo
TO=$(command -v timeout || command -v gtimeout)
D=$(mktemp -d)
{ $TO ${TO:+20} git log -25 --no-merges --date=format:"%Y-%m-%d %H:%M" \
    --pretty=format:"%h|%ad|%an|%s" -- "$SCOPE"; rc=$?; echo; echo "[exit $rc]"; } > "$D/log" 2>&1 &
{ $TO ${TO:+10} git status --porcelain -- "$SCOPE"; rc=$?; echo "[exit $rc]"; } > "$D/status" 2>&1 &
{ $TO ${TO:+10} git diff --stat --no-renames HEAD -- "$SCOPE"; rc=$?; echo "[exit $rc]"; } > "$D/diffstat" 2>&1 &
wait
for f in log status diffstat; do echo "=== $f"; cat "$D/$f"; done
echo "=== timeout wrapper: ${TO:-none, git run bare}"
```

`[exit 124]` means the call timed out — go to Step 1e. A missing `timeout` binary is not a git hang.

**Do NOT** call `git diff` (no `--stat`) — that prints full patches and can be 10x slower. Use `--stat` only.

**Source-file verification discipline**: Read `.qmd`, `.jl`, `.csv`, or other source files ONLY when the summary cites a specific numerical value from them. Do NOT preemptively read source files "just in case" — cross-filesystem reads are the biggest hidden cost. If the session involved no new empirical values (infrastructure work, documentation, planning), skip source-file verification entirely.

### 1b. The commit inventory is the dated log — never `--since="today"`

The dated log from 1a is the commit list. Read the dates off its output and keep every row whose date equals the summary date. Those rows are the **Commits** section.

- **`-25` is a floor, not a ceiling.** If the oldest row printed still carries the summary date, the window may be cutting the day off. Re-run with `-50` (or more) until the oldest row predates it.
- **No row today?** The same output already lists the preceding commits. Use them for context and say in the summary that the newest commit predates this session.

**Never use `git log --since="today"`** (the form this command used through v1.1). Git does not read `today` as 00:00; the filter starts at about the current time of day. Because this command runs at the end of a session, nearly every commit it wants is older than that, so the call exits 0, prints nothing, and looks exactly like a true "no commits today". A bare ISO date fails the same way. Measured in one repository at 13:43 on a day with 4 commits:

| form | commits returned |
|---|---|
| `--since="today"` | 0 |
| `--since="YYYY-MM-DD"` | 0 |
| `--since=midnight` | 4 |
| `--since="YYYY-MM-DD 00:00"` | 4 |

**Optional second opinion** — a count by a different route. Write the pathspec literally:

```bash
git rev-list --count --no-merges --since=midnight HEAD -- "path/to/workstream"
```

- Equal to the number of today's rows in the dated log → say nothing.
- Fewer (including zero) → the dated log wins, and the summary carries one line: *"git `--since=midnight` returned N of M same-day commits; commit list taken from the dated log."* Recording the disagreement is the point; it is the only trace that kind of bug leaves.
- More → the dated-log window is too short. Re-run it with a larger `-N` before writing anything.

A `--since` that agrees is not a reason to skip the dated log next time. The dated log is what exposed the `today` defect.

**Scope every negative.** The inventory is pathspec-scoped, so "no commits today" taken from it is a claim about that scope only. Write "no commits under `<scope>` today", or re-run the dated log unscoped before writing the bare claim. Same-day commits elsewhere in the repo may belong to another terminal or another person: attribute them (the `%an` column helps), do not claim them.

**An untracked scope makes the dated log correctly empty.** If the status output from 1a shows `?? <scope>/`, the directory is untracked and the empty log is the right answer, not a bug. Write "no commits under `<scope>` today; the directory is untracked". Only when the scope is tracked, has no rows, and you know work landed are you in the silent-empty case above.

### 1c. Other repositories

The project repo is often not the only place a session's work lands: a paper's Overleaf git clone, a separate data or course-staff repository, a sibling clone. A log in the project repo is silent about all of them, in exactly the way a true "no commits" looks.

Check every path in `extra_repos`, plus any repository outside the project that the session's record shows edits to:

```bash
git -C ~/papers/chapter2 log -10 --no-merges --date=format:"%Y-%m-%d %H:%M" --pretty=format:"%h|%ad|%an|%s"
```

- A listed path that does not exist or is not a git repository is **reported** in the Commits section, never skipped silently. A repository that quietly drops out of the check re-creates the false negative this step exists to prevent.
- Say which repository each commit belongs to, and state a zero in the project repo explicitly rather than leaving it implied.
- These can all be true at once: the scope is untracked in the project repo (so its log is correctly empty), the repo-wide log shows same-day commits by someone else, and the session's real commits are in another repository. Each fact alone gives a wrong answer in a different direction, so the Commits section states all three.

### 1d. Push state is a fact, not an inference

For every repository with a commit in the summary, get its push state and pass it to the writer verbatim (Step 5):

```bash
git -C <repo> remote -v       # blank output: no remote, so nothing can have been pushed
git -C <repo> status -sb      # first line, e.g. "## main...origin/main [ahead 2]"
```

Report one of: *pushed and in sync with `<upstream>`* / *local only, N commits ahead of `<upstream>`* / *no remote*. Do not let the writer decide. "Pushed" is the default-plausible word and gets supplied for free. For a repository with no remote it is impossible, and it hides that the work exists on one machine only.

### 1e. Fallback when git hangs

If a git call times out (`[exit 124]`) or returns nothing within its bound, do not block the summary on git:

- **File list**: use the session's own record of the files it created or edited. The Glob tool on the scope (results come back sorted by modification time) can fill gaps.
- **Commit list**: from the session record only, labelled as such — *"commit list from session record, not git"*. A file list or a recollection is not a commit list and is never presented as one.
- **Diff size**: count lines only for files whose size the summary actually reports.
- Note in Technical Details: "git unavailable (timed out) — file list from session record." git can be retried at the next `/commit`.

---

## Step 2: Analyze Work Done

- Identify all files modified, added, or deleted
- Group changes by logical area (e.g., research, documentation, code, experiments, infrastructure)
- Note any significant functionality added or changed
- Highlight research findings, decisions, or milestones
- Consider the project context from the project's `CLAUDE.md`, if one exists
- Whether to update a same-day summary or write a new one was decided in Step 0c — follow it rather than re-deciding here

### 2a. Close out any tracker the session finished

If this session completed items on a checklist, tracker, or work-plan file, **update that file before writing the summary**, and say in the summary that you did. A tracker nobody updates becomes a false open list, and it is read as current state: a tracker that still shows every box unchecked when every item is done gives the next session — or the next "what is left?" question — a confidently wrong answer.

- **Find it.** A `*TRACKER*`, `WORK_PLAN`, `HANDOFF`, `BACKLOG`, `STATE` or `TODO` file inside the scope (use Glob).
- **Verify before ticking.** Check each item against the artifact (the file, the commit, the test output), not against the session transcript. A box ticked from recollection is the same defect one step later.
- **Tick it, or say why not.** An item that turned out unnecessary gets a line saying so. An item superseded by a decision gets the decision. Silence is what made the list wrong.
- **Leave genuinely open items open.**

### 2b. Derive the outstanding list; never retype it

Every item in **Next Steps** (or any pick-up list) is re-derived from the working tree immediately before saving, after the session's last commit. Not recalled from the session, not carried over from the previous summary, not copied from the plan the session worked to. For each item, name the command whose output says it is still open, run it, and keep the item only if it does.

| Item shape | Run before writing it |
|---|---|
| "commit X" | `git status --porcelain -- X` lists it, or `git log -1 -- X` prints nothing |
| "push X" | `git rev-list --left-right --count HEAD...@{upstream}` shows a nonzero left count |
| "fix / finish X" | the test or check that reports X still exits nonzero |
| "waiting on a person" | not derivable — say who and since when |

The failure this prevents: a summary listed "commit directory X" as a next step, and X went into the same commit that carried the summary. The list was written from the session's memory of not having done it yet; the doing happened between the writing and the commit. A fabricated open item is a true statement about the past presented as current state, and the next session pays for it by looking for work that is already done. If the summary will be committed together with X, X is not outstanding.

A pick-up list is a measurement and is stamped like one (see STAMP EVERY COUNT in Step 4). An item that cannot be re-derived is written as what it is: *"as of 22:14, the tree showed …"*.

---

## Step 3: Create the Summary Document

**Filename format**: `YYYY-MM-DD_Brief_Title.md` (e.g., `2025-10-13_Model_Calibration_Complete.md`), or `YYYY-MM-DD_HHMM_Brief_Title.md` for a second session the same day (Step 0c).

**Write to**: the `summary_folder` from config (default: `Daily Summary`), resolved against the project root.

**Sections to include**:

- **Date**: Full date
- **Summary**: 2-3 sentence overview of the day's work
- **Key Accomplishments**: Bulleted list of main achievements
- **Files Modified/Added**: Organized by category
- **Technical Details**: Important implementation details, parameter values, or findings
- **Next Steps**: TODOs or follow-up items, each re-derived per Step 2b
- **Commits**: Today's commits per repository from Step 1b–1c, each repository with its push state from Step 1d (or the scoped "none" statement)

**Optional subsections** — add only when they apply:

- **Execution Plan for Later**: for sessions that end with work to be run later (a pre-registered analysis, a pending verdict, a long sweep). A step-by-step playbook with copy-paste-ready commands. Each step points to the authoritative procedure document rather than duplicating its thresholds, and the plan ends at a checkable handoff point ("Step A — verify X finished", "Step B — run Y", "Step C — post-commit check").
- **Discussion Items for `<Name>`**: for design choices made in the session that need a named expert (advisor, co-author, committee member) to review before a deadline. For each: the choice made, the alternative considered and rejected, and the specific question to ask. Not a general "things to discuss" bucket — use it when agreement among AI agents or passes is not independent validation.
- **Deferred to Next /commit Pass**: for multi-terminal sessions where this terminal touched files that also hold another terminal's uncommitted work. A table `| File | This terminal added | Note |`, so the next `/commit` does not lose those rows.
- **Blocked on Purchase or Approval**: for anything shipped in a reduced form because the full version needs a paid API key, a subscription, a credential only a third party can issue, or a licence decision that is not the user's to make. Each entry states what was shipped instead, what that substitute costs, and what the full version would buy. If nothing was shipped instead, say so — an unmitigated gap is more urgent than a mitigated one. Keep these out of the ordinary backlog: a backlog item can be unblocked by more work, these only by someone spending money or signing something. Do not contact a vendor to resolve one; record the unblock path.

**Append-pointer mode**: write only a ≤10-line block at the end of the existing file — a timestamped heading, what changed since the main body, any new commits with push state, and corrected Next Steps.

---

## Step 4: Format Guidelines

- Use clear markdown formatting
- Keep it concise but informative
- Focus on WHAT was done and WHY (not just a file list)
- Include relevant code snippets or key findings if significant
- Make it useful for future reference and for the weekly summary aggregation

**CROSS-REFERENCE FORMAT (Wiki-Links)**: When referencing files, findings, or other summaries, use `[[filename.md]]` syntax. Ambiguous names include one parent directory: `[[subfolder/filename.md]]`. This is a formatting convention — just write links this way instead of backtick paths.

**NAVIGATION LINK**: When gathering git info in Step 1, also list recent summaries:

```bash
ls -1t "Daily Summary/" | grep "^20" | head -20     # literal summary_folder; newest-modified first
```

Add `Previous: [[filename]]` as the first line of the document, pointing to the latest earlier summary **on this session's workstream**: among files that match the workstream (name in the filename, or Summary line), take the latest date prefix and break same-day ties by modification time. Exclude the file being written. Plain alphabetical order is wrong when parallel terminals write same-day summaries: it picks a same-day neighbour on an unrelated topic. If workstreams cannot be told apart, take the latest date prefix. Skip if no prior summary exists.

**NUMERICAL ACCURACY IS CRITICAL**: When reporting parameter values, thresholds, metrics, or any empirical figures — verify against the actual source files before writing. Do NOT approximate from memory or conversation context. If a value cannot be verified from files, write it as approximate and flag it. Common errors:
- A parameter written as a rounded guess (e.g., "reservation prices of about $10/$20/$30" when the configuration says $5/$12/$25)
- An ordering taken from conversation (which paper or chapter comes first) instead of from the document that defines it
- A distribution described loosely — state it exactly (e.g., "θ ~ N(5, 1.5) truncated to [2, 8]"), not "around 5"

**STAMP EVERY COUNT THAT CAME FROM A RUN OR SCAN.** A figure produced by running something — "a dry run found 21 stale files", "30,886 untracked files", "3 configs still queued" — is a measurement at a moment, not a durable fact. It decays as work continues, and a later reader cannot tell a live number from a dead one. Attach when it was measured and how to re-derive it:
- ✅ `21 files stale (dry run, 2026-08-02 morning — re-check with <the command>)`
- ❌ `A dry run confirmed exactly 21 files.`

This matters most in Next Steps and handoff sections, which are read as current state by definition. In one case a handoff file said "a dry run confirmed exactly 21 files"; when the sync ran hours later the count was 17, because four files had converged in between, and nothing in the text signalled the number could move.

**Title Selection**: Choose a descriptive 3-5 word title that captures the essence of the day's work. Examples: `Model_Calibration_Complete`, `Documentation_Restructure`, `Experiment_Results_Analyzed`. When `workstreams` has more than one entry, include the workstream name in the title so `/startup`, `/weekly-summary` and the next `Previous:` link can match it.

---

## Step 5: Brief the Writer, Then Save

Pass the Sonnet writer the gathered information, the section and format rules from Steps 3–4, and the following.

**1. A verified-fact list.** Every identifier, figure, title, path and status the summary will state, in a block the writer copies verbatim:

```
# Verified facts — copy verbatim; do not recall any of these from memory
- Commits, project repo (scope analysis/): a1b2c3d "Add fare sweep" — pushed, in sync with origin/main
- Commits, ~/papers/chapter2: 4e5f6a7 "Revise section 3" — no remote (local only)
- Calibration RMSE: 0.0412 (results/calibration.csv, row "base")      MUST APPEAR
- Survey responses: 41 (spring pilot) — not the 120 planned for fall
- File: analysis/sweeps/fare_sweep.jl (full relative path; copy exactly)
- arXiv ID for <paper>: <id, copied from your verification log>
```

- **Identifiers and figures** (arXiv IDs, DOIs, exact values, paper titles, `file:line` citations): even when the right value is on disk, a writer left to recall one will sometimes substitute a plausible-looking wrong one. An arXiv ID is the typical case.
- **File paths**: give each one's full relative path. Given a bare filename, the writer rebuilds a path and can put the file in the wrong directory.
- **A number and its scope are one fact.** When the prompt holds more than one count of the same kind (this term's enrolment and next term's, a pilot and the full study), put the scope label in the list entry itself, not in surrounding prose. A writer given both numbers with labels only in prose will reattach them wrongly.
- **Commits and push state** for every repository, from Steps 1b–1d.
- **Mark load-bearing facts `MUST APPEAR`.** A writer omits facts without flagging it, and a fact list only protects the facts that make it into the file. Evidence that a change broke nothing (test results, a diffstat) is load-bearing.

**2. Names, not pronouns.** Instruct the writer to refer to every person by name — the author (`author_name`), advisors, collaborators, students — and never by he/she/him/his/her. Scoping the instruction to one group lets the writer use pronouns for everyone else.

**3. Plain characters.** Instruct the writer to write `&`, `<` and `>` literally, never `&amp;`, `&lt;`, `&gt;`. This instruction alone fails often enough that Step 7 checks the saved file for it.

**Save.** The main agent writes the returned text to the output path from Step 0c (or appends it, in append-pointer mode).

**Grade privacy (teaching projects).** When `project_type` is `teaching`, or the summary names any student, a summary that puts a student's name next to a grade, score or evaluation is never committed to a shared repository. Write class-level figures without names, or keep that summary out of version control (add it to `.git/info/exclude` so a later `/commit` cannot sweep it in). Before the first commit, read every line that carries a score and confirm no student name is on it or next to it. A class average with no names is fine.

---

## Step 6: Infrastructure Improvement Candidates (full mode only)

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

## Step 7: Check the Saved File (all modes)

The writer's text and the writer's closing message are both unverified. Run these against the **saved file**, not the returned text. Each is one Grep or Read.

1. **Entities.** Grep for `&amp;|&lt;|&gt;`. Replace each with the literal character; if a `<token>` could then be read as HTML, put it in backticks. Re-grep until there are none.
2. **Load-bearing facts.** Grep for each `MUST APPEAR` item. Add any that are missing.
3. **The writer's account of its own edits.** When the writer updated an existing summary and reports "every place that said X now says Y" or "N occurrences corrected", grep for X and read every hit in context. Do not accept the count. In one case the writer reported that every remaining mention of an old value was framed as historical; eight of nine were, and the ninth stated it as current fact in Technical Details — the line most likely to be quoted later. The fact list cannot catch this, because the error is in the writer's description of what it did.
4. **Pronouns.** Grep case-insensitively for `\b(he|she|him|his|her|hers)\b`. Replace each hit that refers to a person with the person's name.
5. **Duplicate headings.** Grep `^#+ `. Two sibling headings that match case-insensitively (`## Next Steps` beside `## Next steps`) are merged or renamed. A long session edits a summary repeatedly, and each edit looks fine alone.
6. **Paths.** Each file path in the summary matches the path from the fact list.

A failed check is fixed before the footer is written. Record the results in the footer's "Post-save checks" line.

---

Start by gathering information in Step 1, then synthesize into a well-organized daily summary document.

---

## Step 8: Evidence Footer (append to every summary)

Every summary — full, quick, or append-pointer — ends with a standardized footer block. The main agent writes it, not the writer subagent, after Step 7. This converts the summary from opaque prose into a locally verifiable record: every claim in the footer can be checked against files on disk.

```markdown
---

## Evidence Footer

- Command version: v2.0
- Run timestamp: YYYY-MM-DD HH:MM:SSZ (UTC)
- Mode: full / quick / append-pointer
- Scope: <pathspec> (or "whole repo")
- Inputs read: git log (N lines), git status (M files), git diff --stat (K files)
- Commit inventory: dated log, depth -N; today: M commits; --since=midnight: agrees / returned X of M / not run
- Repositories checked: <repo>: M commits, <push state>; ... (unreachable: <path> / none)
- Output path: Daily Summary/YYYY-MM-DD_Title.md
- Git SHA at session start: <sha> (from `git rev-parse HEAD` at session start if captured, else "not captured")
- Git SHA at summary write: <sha>
- Unverified values: N (count of empirical figures not cross-checked against source files)
- Post-save checks: entities fixed N; MUST-APPEAR facts K/K present; pronouns replaced N; duplicate headings none
- Subagent: sonnet (or haiku/opus if overridden)
```

Any user re-running the command at the same time with the same git state should get the same table modulo timestamps.

## Step 9: Emit run_report (instrumentation)

After writing the summary, emit a structured run_report for observability via `/run-log`. Substitute literal values — variables from earlier Bash calls are gone:

```bash
python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py" \
  --command daily-summary \
  --run-dir "Daily Summary/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --evidence-dir ".toolkit/evidence" \
  --tool-version v2.0 \
  --outcome complete \
  --task-summary "Daily summary for YYYY-MM-DD (<mode> mode)" \
  --fields "mode=<mode> files_touched_count=<N> commits_today=<M> repos_checked=<R> git_sha_start=<sha> git_sha_end=<sha> unverified_count=<U>"
```

`--run-dir` uses `summary_folder`; `--evidence-dir` uses `evidence_dir` from config. This is a ONE-LINE call. The helper handles YAML formatting, CSV append, and atomicity.

If the helper is not available (e.g., toolkit not installed at expected path), skip this step silently. The primary summary output must NEVER be blocked by instrumentation failure.

---

> **What next?** If the summary flagged any `/improve` candidates, run `/improve` at the start of your next session to action them while the context is warm. Run `/commit` to save the summary — if the Next Steps list was derived in Step 2b, it is still true when the commit lands.

$ARGUMENTS
