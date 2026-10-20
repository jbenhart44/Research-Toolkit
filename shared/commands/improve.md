---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(mkdir:*), Bash(python3:*)
description: Self-reflective meta-agent — scans conversation context, git history, and infrastructure files to identify improvements to JIT references, slash commands, skills, and CLAUDE.md. Produces a structured report for human review.
---

# /improve — Infrastructure Improvement Scanner

> **When to use**: Periodically (weekly or after major sessions) to audit your Claude Code infrastructure — CLAUDE.md, slash commands, skills, JIT references, settings — and get specific improvement recommendations. After a `/coa` session it also reviews the council's own seat definitions.

You are executing the `/improve` command. Your job is to scan the Claude Code infrastructure (JIT reference files, slash commands, skills, CLAUDE.md, settings) and produce a structured report of specific, actionable improvements. You do NOT auto-edit anything — the user reviews your report and decides what to implement.

**Version**: 1.4 (adds skills and Council-of-Agents files to scope, the `--tools` evidence mode, the luck check, and the promotion step; 1.3 was generalized from project-specific v1.2)

---

## STEP 0: Read Project Configuration

Read `toolkit-config.md` from the project root if it exists, otherwise `~/.claude/toolkit-config.md`, and load:

- `project_name` — for the report header
- `summary_folder` — where daily or session summaries live (default: `Daily Summary`). Used by Priority 3.
- `evidence_dir` — where toolkit run evidence lives (default: `.toolkit/evidence`). Used by Category H and `--tools` mode. Below, `$EVIDENCE_DIR` means this value.

If neither file exists, use the defaults and infer the remaining conventions (where JIT references live, where commands live, where summaries are stored) from what you find in the current project. Do not stop to ask.

---

## SCOPE BOUNDARIES

### In-Scope (can propose changes to)

| Target | Location |
|--------|----------|
| CLAUDE.md | Root directory — hard rules, JIT table, workflow patterns |
| JIT Reference Files | `references/` directory (or project equivalent) — procedural instructions |
| Slash Commands | `.claude/commands/*.md` in the project, and `~/.claude/commands/*.md` (where the toolkit installs) — **including `improve.md` itself** |
| Skill files | `.claude/skills/*/SKILL.md` in the project, and `~/.claude/skills/*/SKILL.md` — the skill instruction bodies |
| CoA council files | `coa/personas/*.md`, `coa/ROSTER.md`, and any seat agent definitions (`.claude/agents/coa-*.md`) — **only when `/coa` ran in this conversation** (see Category H) |
| New JIT Files | Propose creation in the appropriate references directory |
| CLAUDE.md JIT Table | Propose new rows for the JIT Reference Files table |

Files the toolkit installs under `~/.claude/` are replaced when the toolkit is reinstalled. When a recommendation targets one, say so in its Why field.

### Out of Scope: Built-In Commands and Skills

Built-in Claude Code commands and skills (for example `/loop`, `/schedule`, `/code-review`) have no file in the project or under `~/.claude/` and cannot be edited. **Before drafting a change against any command or skill, confirm its file exists.** If a built-in caused friction this session, record it in the report body (Scan Summary or Also Noted) as evidence for a local wrapper command or a CLAUDE.md note. Do not draft an edit to a file that does not exist.

### Read-Only (scan for context, never propose changes)

- Memory files — read for project state context
- Source code files — read for pattern detection only
- Active plan/research directories — read-only
- Daily or session summaries — read for pattern detection
- CoA member files and chair syntheses — the record of what a council said; read as evidence for Category H, never edit

### Off-Limits (never read, never propose changes)

- Binary data files (large datasets, compiled outputs, media files)
- Files explicitly marked read-only in CLAUDE.md
- Git configuration
- Simulation or calibration parameter values (project-specific computed results)

---

## INVOCATION

```
/improve                    # Session scan — only what was touched this conversation
/improve all                # Full codebase scan — all categories, all folders
/improve [topic]            # Focus scan — prioritize [topic]-related infrastructure (e.g. /improve citations)
/improve --tools            # Tool evidence review — read run_log.csv, compute per-command stats, flag improvement candidates
/improve status             # Show previous improve report dates and counts
```

**Argument:** `$ARGUMENTS`

- If `$ARGUMENTS` is `status` → skip to STATUS MODE.
- If `$ARGUMENTS` is `--tools` → skip to TOOLS EVIDENCE MODE.
- If `$ARGUMENTS` is `all` → **full codebase scan**. Scan all JIT files, all commands, all skills, all project folders, git history, summaries. Use for periodic deep audits, not after every session.
- If `$ARGUMENTS` is not empty (and not `status`, `--tools`, or `all`) → treat as a **focus hint**. Prioritize recommendations related to this topic. Still scan session context, but rank focus-related findings higher.
- If `$ARGUMENTS` is empty → **session-only scan** (default). Scope is limited to exactly what was worked on in the current conversation. Do NOT scan commands, skills, JIT files, or project folders that were not touched this session.

---

## FIRST-TIME SETUP DETECTION

Before starting the scan, check if a `CLAUDE.md` file exists in the project root directory.

**If no CLAUDE.md is found:**

Present to the user:

> "No CLAUDE.md found in this project. CLAUDE.md helps Claude Code understand your project — it's where you define hard rules, link reference files, and describe project conventions.
>
> Want me to create a starter template? It will include:
> - A JIT reference table (empty, ready to fill)
> - A hard rules section (empty)
> - A project priority note
>
> This takes 30 seconds and makes every future Claude Code session more effective."

If the user says yes, create a minimal `CLAUDE.md`:

```markdown
# CLAUDE.md

## JIT Reference Files — Read When Needed

| When you need to... | Read this file |
|---|---|
| (add rows as you create reference files) | |

## Hard Rules

- (add project-specific rules here)

## Priority

(describe your primary work focus)
```

Then continue with the improve scan as normal — the scan will naturally identify that the CLAUDE.md is sparse and suggest additions.

**If CLAUDE.md exists:** Skip this section and proceed to the scan.

---

## CONVERSATION-FIRST PHILOSOPHY

**/improve is primarily a session retrospective, not a broad infrastructure audit.** Its highest-value signal comes from what actually happened in the current conversation:

- **What commands and skills were invoked** — did they work well? Where did they produce friction, wrong results, or waste tokens?
- **What JIT files were referenced** — were they complete and accurate? Did the user or agent have to work around missing information?
- **What project rules were tested** — did any rule cause ambiguity?
- **What files were edited** — do the patterns suggest a missing workflow or JIT reference?

The broad infrastructure scan (git history, summaries, all commands) is secondary. It catches recurrent issues and staleness, but the **conversation is the primary evidence source**. Every /improve invocation should produce at least one recommendation directly tied to something that happened in the current session.

**When to invoke /improve**: After any significant session — especially after using /pace, /coa, /pcv, or other complex multi-agent workflows. The more complex the workflow, the more improvement opportunities exist.

---

## EXECUTION: FOUR-PASS SCAN

### Pass 1: Intake — Gather Context

**Priority 1 — Session Context (ALWAYS do this first):**

1. **Analyze the current conversation** — This is the primary evidence source. Identify:
   - Which slash commands and skills were invoked
   - Which JIT reference files were read or should have been read
   - Which project rules were applied or caused friction
   - What files were created, edited, or read
   - Where friction occurred: errors, retries, ambiguity, wasted work, divergence between agents
   - What worked well and should be preserved

2. **Read the commands and skills that were used** — Read the command file (`.claude/commands/*.md` or `~/.claude/commands/*.md`) or skill file (`.claude/skills/*/SKILL.md` or `~/.claude/skills/*/SKILL.md`) for every command or skill invoked in this session. These are the highest-priority improvement targets. If no file exists, it is a built-in — see Out of Scope above.

3. **Read the JIT files that were referenced** — Read any reference files that were loaded or should have been loaded during this session.

3b. **CoA check (feeds Category H)** — Determine from this conversation whether `/coa` was invoked here. If it was, locate the session directory that run wrote (`coa/council_sessions/coa_<date>_<slug>/`, in the project root or in the workflow directory where `/coa` saved it) and read its `member_<seat>.md` files, `chair_synthesis.md`, the session file's YAML frontmatter, and the persona files for the seats that were used. If `/coa` did not run in this conversation, skip this step; Category H will not fire. Do not identify the session by date alone — see the Category H trigger.

**Priority 1b — Session Folder Scan:**

4. **List session directories** — For every directory created in or written to during this conversation, run `ls` to see its current contents. Note new files, pre-existing files, and whether the directory structure supports discoverability. This feeds Category G.

**Priority 2 — Infrastructure Baseline (session-scoped by default):**

5. **Read CLAUDE.md** — note current hard rules, JIT Reference Files table, and workflow patterns.

6. **Read only the JIT files, commands, and skills used this session** — Do NOT read all of them unless `/improve all` was invoked.

7. **Read toolkit-config.md** (if present and not already read in Step 0) — understand project conventions.

7b. **Read the memory index** (if present — e.g. `MEMORY.md` at the project root or `~/.claude/projects/*/memory/MEMORY.md`) — scan for project state and feedback memories. READ-ONLY.

8. **Read `.claude/settings.local.json`** (if present) — note current settings.

**Priority 2b — Full Baseline (only when `/improve all` is invoked):**

If and only if `$ARGUMENTS` is `all`:

9. **Read ALL remaining JIT reference files** — Glob the references directory and read any not already read. Note coverage gaps.

10. **Read ALL remaining slash commands and skills** — Glob the command and skill locations listed in the In-Scope table and read any not already read. Note structural patterns.

**Priority 3 — Historical Context (GATED — see rule below):**

**GATING RULE (v1.1)**: For session-only mode (no `$ARGUMENTS`), FIRST count the session friction signals you gathered in Priority 1. If **fewer than 3** session-specific friction signals were identified, SKIP items 11-13 entirely. Historical reads (git log, previous reports, summaries) are expensive on slow filesystems and add limited value when the session was already clean. Token budget: skipping Priority 3 saves ~40K tokens/run on light-session invocations.

If `$ARGUMENTS` is `all` or a focus topic, ignore the gate and run the full Priority 3 sweep.

**Gate self-test (v1.1 calibration)**: On every scan invocation (not `status` or `--tools`), append a single line to `.gate_log.txt` in the improve_reports directory (see SAVE THE REPORT for how it is found) in the format:
```
YYYY-MM-DD HH:MM | friction_count=N | gate_fired=true/false | mode=session|all|focus
```
This is a 1-line append, silent (do NOT show to user). After 5 session-mode invocations have been logged, review the distribution of `friction_count` values. If most sessions have friction_count >= 3, the threshold is too low — the gate rarely fires and the P3 savings are unrealized. Raise threshold to 5. If most sessions have friction_count < 3, the threshold is correctly calibrated. Without this log, the gate is untested in the wild and its effectiveness is speculative.

Items 11-13 (only run when gate passes OR `/improve all`):

11. **Check for previous improve reports** — Glob for `improve_*.md` in the improve_reports directory. If any exist, read the most recent one. Note which recommendations have been implemented.

12. **Scan git history** — run:
    ```bash
    git log --oneline -15
    git diff --stat HEAD~10
    ```

13. **Scan recent summaries** — Only when `/improve all` is invoked. List `summary_folder` and read the 5 most recent summaries by date. Look for friction signals.

14. **Declare scan scope** — record what you read and what you skipped. This goes in the report header. If Priority 3 was gated off, note it explicitly: "Priority 3 historical reads skipped (session had <3 friction signals; `all` override not used)."

### Pass 2: Analyze — Identify Gaps Across Eight Categories

For each category, compare what you found in Pass 1 against what *should* exist. **Categories are ordered by priority — session-specific findings come first.** Category H fires only when `/coa` ran in this conversation.

#### Category A (HIGHEST PRIORITY): Session-Specific Findings

This is where the conversation-first philosophy lives. For each command, skill, JIT file, or rule touched in this session:
- **Commands and skills used**: Did they produce the right result? Where did they waste tokens, cause friction, or produce ambiguous outputs? What would make the next invocation smoother?
- **JIT files referenced**: Were they complete? Did the agent have to work around missing info? Should content learned this session be added?
- **Project rules tested**: Did any rule cause ambiguity or divergence between subagents (for example, a "check the file exists" rule that does not say whether the search is recursive)? Should the rule be more specific?
- **Patterns observed**: Did the session reveal a workflow pattern that should be codified? Did an agent discover something out of its scope that suggests a new JIT reference?
- **Every /improve invocation MUST produce at least one Category A finding.** If nothing needs improvement, explain why (forces engagement with session context rather than defaulting to the broad scan).

#### Category B: JIT Reference File Updates
- Are there procedures described in CLAUDE.md that are long enough to warrant their own JIT file but don't have one?
- Are existing JIT files stale (content doesn't match current practice)?
- Did session notes or summaries describe lessons that should be codified as JIT references?
- Were the same types of errors fixed multiple times in git (pattern = needs a JIT file)?

#### Category C: Slash Command and Skill Improvements
<!-- spawn: none reason="a checklist question that mentions the Agent tool" -->
- Do any commands or skills have outdated version numbers or missing frontmatter fields?
- Are there inconsistent patterns across commands (e.g., one uses the Agent tool, another doesn't, for similar tasks)?
- Did any commands or skills fail or produce suboptimal results recently (visible from git fixes or summary mentions)?
- Are there missing edge case handlers (e.g., what happens when a command finds no files)?
- **Does any command or skill resolve a path from `BASH_SOURCE`, `$0`, or "this file's directory"?** A command or skill body is prose loaded into a prompt, not a script being sourced, so those variables do not point at the file and the path resolves somewhere unrelated. Paths must come from the project root, a config key, or an absolute location the user chose.
- **Has the same instruction been corrected more than once and broken again?** An instruction that keeps failing as prose should become a mechanism — a script the command runs, a hook, or a check — rather than gain more prose. Propose the mechanism, not another paragraph.

#### Category D: CLAUDE.md Updates
- Are there new workflow patterns that emerged from recent work but aren't documented?
- Is the JIT Reference Files table missing entries for files that exist?
- Are there implicit "rules" being followed that should be explicit hard rules?
- Is any section of CLAUDE.md stale or contradicted by current practice?

#### Category E: New Infrastructure Proposals
- Are there recurring topics (3+ touches in git/summaries) that deserve their own JIT reference file?
- Are there project areas without command coverage that would benefit from a slash command or skill?
- Should any settings be different?

#### Category F (optional): Memory/State Staleness
- Is the project's memory or state index outdated based on recent git activity?
- Are there memory files that reference stale information?
- **Note**: Flag staleness only. Do NOT propose detailed rewrites.

#### Category G: Folder Organization (session directories only)

**Purpose**: Make sure the directories touched during this session are organized so their artifacts can be found in future sessions. This is not a full codebase reorganization.

For each directory created in or written to during the session:

1. **Discoverability audit** — Can a future session find these artifacts?
   - Are new files in logical locations relative to existing project structure?
   - Are there orphaned files (created this session but not referenced by any parent document, index, or summary)?
   - Are plans, research runs, or reports in their expected directories (e.g., a plan file in the project's plans directory rather than the root)?
   - Are figures, data, and supporting files co-located with the documents that reference them?

2. **Naming consistency** — Do new files follow the project's naming conventions?
   - Date-prefixed summaries (`YYYY-MM-DD_Title.md`), descriptive plan names
   - Figures named for their content (not `output1.png`)

3. **Index/pointer check** — Are new artifacts referenced from somewhere discoverable?
   - Does the session summary mention them?
   - Are they in a JIT reference, CLAUDE.md, or memory file?
   - If a plans or run-output directory was created, is there a pointer to it from the parent project folder?

4. **Propose reorganization** only when:
   - Files are in clearly wrong locations
   - A new subdirectory would make a cluttered folder navigable (5+ new files of the same type)
   - An existing folder structure has a gap this session's work revealed

**Constraints**:
- Never move files without proposing the move in the report first
- Never rename files that other documents reference (check for inbound references first)
- When `/improve all` is invoked, expand this to cover ALL project directories

#### Category H: Council of Agents (fires only when `/coa` ran in this conversation)

**Purpose**: `/coa` reviews the user's work; this category reviews the council. When this conversation ran `/coa`, look at how each seat actually performed and propose specific, evidence-backed changes to the seat definitions.

**Trigger**: Fire only if `/coa` was invoked in this conversation. A session directory dated today is not sufficient: if more than one Claude Code session works in the same project, today's `coa_<date>_*` directories may belong to another session. Confirm from the conversation's own record which session directory this run wrote. If `/coa` did not run here, skip Category H and say so in the Scan Summary, even when directories dated today exist. Do not propose council changes from earlier runs or from another session's runs.

**Inputs** (read-only as evidence; the seat definitions are in scope for proposals):
- This session's `member_<seat>.md` files and `chair_synthesis.md`
- The session file's YAML frontmatter (`session_summary.md` in the session directory, or `coa_<date>_<slug>.md`): `outcome`, `seats`, `self_audit_verdict`, `gemini_crosscheck`
- The persona files for the seats used: `coa/personas/<seat>.md` in the project, or the built-in roster in `/coa` when the project has none
- `coa/ROSTER.md`, if present
- Any agent definitions the project uses for seats (`.claude/agents/coa-*.md` or `~/.claude/agents/coa-*.md`), if present
- The `/coa` entries in `$EVIDENCE_DIR/command_performance_log.md` and `$EVIDENCE_DIR/crossmodel_attempts.csv`, if present

**What to look for** (each finding cites the member file or log line from this session):
1. **A seat that under-performed its job** — a member the Clerk flagged `REASONING_GAP`, `STANCE_VIOLATION`, or `FORMAT_MISSING`; a member file that is missing or under the size floor; or a member whose output could pass for another seat's (the seats did not differentiate). Propose a sharper persona, required output, or self-check for that seat so it does not recur.
2. **A recurring dispatch or tooling failure** — e.g., a seat whose agent definition lacks the Write tool, so the orchestrator had to save that seat's member file for it (propose adding Write to that agent's tool list); or the cross-model check failed or fell back (`gemini_crosscheck: false`, `cross_check=local_fallback`, or `truncated`/`error` rows in `crossmodel_attempts.csv`). Record a one-off failure; if it recurs across the log, propose standing handling (such as stating the same-model caveat up front) instead of a silent miss.
3. **A persona blind spot the session exposed** — a seat repeatedly missed a class of issue the Chair had to raise, or one seat invented a useful framing device that should become part of that persona's standing output structure.
4. **Seating heuristics** — if the same panel was convened several times this conversation for the same kind of question, propose a default in `coa/ROSTER.md` (or a precedent note) so seating is faster next time.

**Constraints**:
- Propose changes only to persona files, `coa/ROSTER.md`, and seat agent definitions. Never rewrite a member's analysis or a chair synthesis; those are the session's evidence record, not infrastructure.
- **Agent definitions are loaded when a session starts.** An edit to an agent file under `.claude/agents/` may not take effect until the next Claude Code session. Any Category H recommendation that touches one MUST say so, so the user does not expect the current session's council to change. Persona files are read by `/coa` when it convenes, so persona edits apply to the next `/coa` run.
- No speculative "the persona could be richer" proposals without evidence from this session.

### Pass 3: Synthesize — Build Recommendation List

For each finding from Pass 2, create a recommendation entry:

1. **Priority assignment** — Three tiers:
   - **Critical**: Recurrent friction (multiple sessions or git commits) OR high error risk (a missing rule that causes mistakes). Costs >30 min cumulative if not fixed.
   - **Useful**: Appeared at least once with a clear fix. Saves time or improves consistency. 5-30 min savings.
   - **Nice-to-have**: Speculative improvement. No evidence of actual pain. Minor polish.

2. **Recurrence check** — If this recommendation also appeared in a previous improve report and hasn't been implemented, tag it `[RECURRENT]`.

3. **Luck check** — If the evidence shows a workflow succeeded by accident — a parallel race that happened to resolve the right way, a missing validation step that did not bite this time, an agent whose output landed correctly despite ambiguous instructions — tag the recommendation `[LUCK]` in its Why field. A `[LUCK]` item that recurs across reports means the workflow needs a structural fix, not more documentation. Example: "The synthesizer happened to address all six Critic findings, but it never read the Critic's review. [LUCK]"

4. **Action type** — Classify each recommendation:
   - `CREATE` — new file that doesn't exist yet
   - `INSERT` — add new content to an existing file
   - `REPLACE` — change existing content in a file
   - `APPEND` — add to the end of an existing file

5. **Draft the change** — For every recommendation, write the exact proposed text. No vague suggestions. The draft should be copy-pasteable.

6. **Cap at 10 recommendations**. If you find more than 10, keep the top 10 by priority. List overflow as one-line mentions without drafts in an "Also Noted" section.

7. **If `$ARGUMENTS` provided a focus hint**, boost focus-related recommendations by one priority tier (Nice-to-have → Useful, Useful → Critical). Still include non-focus findings at their natural priority.

### Pass 4: Quality Gate + Output

Before finalizing, review each recommendation:

- [ ] **Specific**: Names an exact file path and location within the file
- [ ] **Actionable**: Includes a draft that could be applied without additional research
- [ ] **Non-duplicative**: Not already covered by an existing JIT file, command, skill, or CLAUDE.md section
- [ ] **In-scope**: Target file is in the In-Scope list above, and the file exists (or the action is `CREATE`)
- [ ] **Non-conflicting**: Does not contradict a CLAUDE.md hard rule

**Drop any recommendation that fails criteria 1-3 after one revision attempt.** Do not pad the report with weak items.

---

## REPORT FORMAT

Generate the report in this exact format:

```markdown
# /improve Report — YYYY-MM-DD

## Scan Summary
- **Session context**: [commands and skills used, JIT files referenced, project rules tested, key friction points, built-in friction if any]
- **Git activity**: [N] commits scanned, [key patterns]
- **Summaries read**: [list with dates]
- **Infrastructure baseline**: [N] JIT files, [N] commands, [N] skills
- **Previous /improve report**: [date or "None — first run"]
- **CoA this session**: [session directory — Category H ran / "No /coa in this conversation — Category H skipped"]
- **User focus**: [focus hint or "Full scan"]

---

## Critical

### 1. [Title] [RECURRENT]? [LUCK]?
- **Category**: [JIT Reference / Command / Skill / CLAUDE.md / New File / Memory Staleness / CoA Council]
- **Action**: [CREATE / INSERT / REPLACE / APPEND] in `[file path]`
- **Why**: [1-2 sentences citing specific evidence — git commits, session observations, or observed gaps]
- **Draft**:
```[language]
[exact proposed content]
```

[repeat for each Critical item]

---

## Useful

[same format as Critical]

---

## Nice-to-Have

[same format, but drafts are optional at this tier — a one-line description suffices]

---

## Folder Organization (Session Directories)

[For each directory touched in this session:]

### [Directory path]
- **Files created/modified**: [list]
- **Discoverability**: [OK / Issue — describe]
- **Naming**: [OK / Issue — describe]
- **Index pointers**: [OK / Missing — where should a pointer be added?]
- **Proposed moves**: [None / list of proposed file moves with rationale]

---

## Where Each Item Lands

| # | Item | Surface if applied (A mechanical / B loaded instructions / C memory) | Promote or drop |
|---|------|------------------------------------------------------------------------|-----------------|
| 1 | [title] | [A/B/C — file] | [Promote / Drop — reason] |

---

## Also Noted

[One-line mentions of items that didn't make the top 10, if any]

---

## Summary
- Critical: [N] items
- Useful: [N] items
- Nice-to-have: [N] items
- Recurrent: [N] items from previous reports
- Luck: [N] items tagged [LUCK]
- To implement: say "apply recommendation [N]" or "apply 1, 3, 5"
```

---

## SAVE THE REPORT

After generating the report:

1. Get today's date: `date '+%Y-%m-%d'`
2. Determine the improve_reports directory: check for `workflow/improve_reports/` or `.claude/improve_reports/`. If none exists, create `improve_reports/` in the project root.
3. Save the report to `[improve_reports_dir]/improve_YYYY-MM-DD.md`
4. If a report with today's date already exists, append a sequence number: `improve_YYYY-MM-DD_2.md`
5. Display the full report in conversation AND save to file.

### A saved report is evidence, not an applied lesson

Saving the report creates an audit trail. It does not change what any future session reads, so a lesson that exists only in the improve_reports directory has been filed, not learned — and those reports accumulate unread. That is why the report carries the **Where Each Item Lands** section. For each Critical and Useful item, name the surface it would land on if applied:

- **Tier A — mechanical**: a hook, a script, or a check a command runs. It fires whether or not anyone remembers the rule. Prefer this for anything that has already failed as prose.
- **Tier B — loaded instructions**: a CLAUDE.md rule, a rule file scoped to the paths it governs, or a reference file indexed in the CLAUDE.md JIT table, so a future session reads it when it is relevant.
- **Tier C — memory**: a memory file. The weakest surface; it is read only if it is recalled.

Then say which items are worth promoting and which should be dropped. Drop an item on purpose and say so in the report; an explicit drop is better than filing the same item again next time. A `[RECURRENT]` item that is neither applied nor dropped is the case this section exists to stop.

---

## AFTER THE REPORT

Present the report and then say:

> "Infrastructure scan complete. [N] recommendations ([N] critical, [N] useful, [N] nice-to-have).
>
> To implement changes:
> - Say **'apply [N]'** to implement a specific recommendation
> - Say **'apply all critical'** to implement all critical items
> - Say **'apply 1, 3, 5'** to implement specific items
> - Say **'skip'** to review the report later (it's saved to `[improve_reports_dir]/`)
>
> Report saved to: `[improve_reports_dir]/improve_YYYY-MM-DD.md`"

**STOP and wait for the user's direction.** Do not implement any changes until explicitly asked.

When the user asks to apply a recommendation:
1. Read the recommendation from the report
2. Use the Edit or Write tool to apply the proposed change
3. Confirm what was changed
4. Move to the next requested item

---

## STATUS MODE

When invoked with `/improve status`:

1. Find the improve_reports directory (check `workflow/improve_reports/`, `.claude/improve_reports/`, `improve_reports/`)
2. Glob for `improve_*.md`
3. For each report found, read the Summary section
4. Display:

```
/improve — Report History
=========================
Total reports: [N]

| Date | Critical | Useful | Nice-to-have | Recurrent |
|------|----------|--------|-------------|-----------|
| [date] | [N] | [N] | [N] | [N] |
| ... | ... | ... | ... | ... |

Most recent: [date]
```

5. **STOP.**

---

## TOOLS EVIDENCE MODE

When invoked with `/improve --tools`. This mode looks for things to fix in the toolkit's own commands. For a plain longitudinal table of runs and recurring improvement signals, use `/runlog`.

1. **Read** `$EVIDENCE_DIR/run_log.csv`. If it does not exist, report "No runs logged yet — run at least one instrumented command first" and **STOP**.
2. **Parse it with Python's `csv` module** (`python3`), not by splitting on commas: the `task_summary` and `notes` cells are quoted and can contain commas. The current schema is `run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes`; older rows may be shorter or column-shifted. Skip rows that do not parse and count them.
3. **Scan for orphaned run reports** (reports with no CSV row):
   - Glob `$EVIDENCE_DIR/pace_runs/pace_*`
   - Glob `coa/council_sessions/coa_*` (directories, or `.md` files with YAML frontmatter)
   - Glob any `run_report.md` under `$EVIDENCE_DIR` or under a `.run_reports/` directory (this command writes its own under the improve_reports directory)
   - For each, read its `run_id` from the frontmatter and check whether it exists in the CSV. Flag orphans.
4. **Compute per-command statistics** from the CSV:
   - Run count, outcome distribution (complete/partial/failed), most recent run, date range
   - Mean `convergence_rate` for commands that record it (e.g. /pace, /coa)
   - Any command-specific fields the rows carry (e.g. council size for /coa, errors caught for /pace, input shape for /help)
5. **Compute trends** (only for a command with 10+ runs):
   - Compare the last 5 runs to the previous 5: is convergence trending up, down, or stable?
   - Flag any command with 3+ consecutive partial or failed outcomes
6. **Check changelogs**, if the project keeps them (e.g. `$EVIDENCE_DIR/changelogs/`): find entries whose after-metric is still a placeholder (e.g. `METRIC AFTER: [to be measured]`) and that now have 5+ runs since the version change. List them as ready to fill.
7. **Display**:

```
/improve --tools — Evidence Review
====================================
Total runs: [N] | Date range: [first] to [last] | Skipped rows: [N]

/[command]: [N] runs | Mean convergence: [X]% or — | [command-specific stat]
  Latest: [date] | Outcome: [X] complete, [Y] partial, [Z] failed
  [Trend line if 10+ runs]

[repeat for each command in the CSV]

Orphaned reports (no CSV entry): [list or "None"]
Changelog items ready for an after-metric: [list or "None"]

Improvement candidates:
[Runs with convergence < 0.30, failed outcomes, 3+ consecutive partial/failed, or recurring patterns]
```

8. **If orphaned reports were found**, offer to reconcile: parse their YAML frontmatter and append one CSV row each, using the schema above and proper CSV quoting. Do this only if the user says yes.
9. **Save the report** to `[improve_reports_dir]/improve_tools_YYYY-MM-DD.md` (same directory rules and sequence numbering as SAVE THE REPORT).
10. **STOP and wait for the user's direction.**

---

## BEHAVIORAL CONSTRAINTS

- **Never auto-edit files.** The report is advisory. Changes require explicit user approval.
- **Self-improvement allowed.** This command CAN propose improvements to itself (`improve.md`) when evidence warrants it. Self-improvement recommendations follow the same report format and require user approval like any other change.
- **Never modify files in the Off-Limits list.** Not even to "fix" something obvious.
- **The report is the deliverable.** Do not produce side-effect files beyond the report, the one-line gate log entry, and the run report written by the instrumentation step.
- **Be honest about uncertainty.** If you're unsure whether a recommendation is valid, say so in the "Why" field. Don't manufacture confidence.
- **Respect Occam's razor.** Don't propose complexity for its own sake. Each recommendation should pass: "Would this save the user time or prevent errors?"
- **Verify empirical claims in drafts.** If a recommendation draft contains specific numbers (percentages, token counts, timing), verify against source data before presenting. Do not carry unverified figures from conversation context into JIT reference proposals.

---

## Instrumentation (v1.1 — one-line emit at end of run)

After writing the improve report (or the `--tools` report, with `SCOPE_MODE=tools`), emit a structured run_report for observability via `/runlog`:

```bash
python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py" \
  --command improve \
  --run-dir "$improve_reports_dir/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Improve scan ($SCOPE_MODE mode)" \
  --fields "scope=$SCOPE_MODE findings_critical=$N_CRITICAL findings_useful=$N_USEFUL findings_nice=$N_NICE recurrent_count=$N_RECURRENT files_scanned=$N_FILES priority3_gated=$P3_GATED"
```

This is a ONE-LINE call. The helper handles YAML formatting, CSV append, and atomicity. If the helper is not available at the toolkit path, skip silently — the improve report itself is the user-facing deliverable.

> **What next?** After actioning any findings from this report, run `/commit` to checkpoint the infrastructure changes — improve findings applied but not committed are easy to lose across sessions.

$ARGUMENTS
