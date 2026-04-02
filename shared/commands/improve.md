---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(git:*), Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(mkdir:*)
description: Self-reflective meta-agent — scans conversation context, git history, and infrastructure files to identify improvements to JIT references, slash commands, and CLAUDE.md. Produces a structured report for human review.
---

# /improve — Infrastructure Improvement Scanner

> **When to use**: Periodically (weekly or after major sessions) to audit your Claude Code infrastructure — CLAUDE.md, slash commands, JIT references, settings — and get specific improvement recommendations.

You are executing the `/improve` command. Your job is to scan the Claude Code infrastructure (JIT reference files, slash commands, CLAUDE.md, settings) and produce a structured report of specific, actionable improvements. You do NOT auto-edit anything — the user reviews your report and decides what to implement.

**Version**: 1.3 (generalized from project-specific v1.2)

**Project context**: If a `toolkit-config.md` exists in the project root or at `~/.claude/toolkit-config.md`, read it to understand the project's folder conventions (where JIT references live, where commands live, where summaries are stored). If it does not exist, infer conventions from what you find in the current project.

---

## SCOPE BOUNDARIES

### In-Scope (can propose changes to)

| Target | Location |
|--------|----------|
| CLAUDE.md | Root directory — hard rules, JIT table, workflow patterns |
| JIT Reference Files | `references/` directory (or project equivalent) — procedural instructions |
| Slash Commands | `.claude/commands/*.md` — **including `improve.md` itself** |
| New JIT Files | Propose creation in the appropriate references directory |
| CLAUDE.md JIT Table | Propose new rows for the JIT Reference Files table |

### Read-Only (scan for context, never propose changes)

- Memory files — read for project state context
- Source code files — read for pattern detection only
- Active plan/research directories — read-only
- Daily or session summaries — read for pattern detection

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
/improve [topic]            # Focus scan — prioritize [topic]-related infrastructure
/improve status             # Show previous improve report dates and counts
```

**Argument:** `$ARGUMENTS`

- If `$ARGUMENTS` is `status` → skip to STATUS MODE (end of this file).
- If `$ARGUMENTS` is `all` → **full codebase scan**. Scan all JIT files, all commands, all project folders, git history, summaries. Use for periodic deep audits, not after every session.
- If `$ARGUMENTS` is not empty (and not `status` or `all`) → treat as a **focus hint**. Prioritize recommendations related to this topic. Still scan session context, but rank focus-related findings higher.
- If `$ARGUMENTS` is empty → **session-only scan** (default). Scope is limited to exactly what was worked on in the current conversation. Do NOT scan commands, JIT files, or project folders that were not touched this session.

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

- **What commands were invoked** — did they work well? Where did they produce friction, wrong results, or waste tokens?
- **What JIT files were referenced** — were they complete and accurate? Did the user or agent have to work around missing information?
- **What project rules were tested** — did any rule cause ambiguity?
- **What files were edited** — do the patterns suggest a missing workflow or JIT reference?

The broad infrastructure scan (git history, summaries, all commands) is secondary. The **conversation is the primary evidence source**. Every /improve invocation should produce at least one recommendation directly tied to something that happened in the current session.

**When to invoke /improve**: After any significant session — especially after using /pace, /coa, or other complex multi-agent workflows.

---

## EXECUTION: FOUR-PASS SCAN

### Pass 1: Intake — Gather Context

**Priority 1 — Session Context (ALWAYS do this first):**

1. **Analyze the current conversation** — This is the primary evidence source. Identify:
   - Which slash commands were invoked
   - Which JIT reference files were read or should have been read
   - Which project rules were applied or caused friction
   - What files were created, edited, or read
   - Where friction occurred: errors, retries, ambiguity, wasted work, divergence between agents
   - What worked well and should be preserved

2. **Read the commands that were used** — Read the `.claude/commands/*.md` files for every command invoked in this session. These are the highest-priority improvement targets.

3. **Read the JIT files that were referenced** — Read any reference files that were loaded or should have been loaded during this session.

**Priority 1b — Session Folder Scan:**

4. **List session directories** — For every directory created in or written to during this conversation, run `ls` to see its current contents. Note new files, pre-existing files, and whether the directory structure supports discoverability.

**Priority 2 — Infrastructure Baseline (session-scoped by default):**

5. **Read CLAUDE.md** — note current hard rules, JIT Reference Files table, and workflow patterns.

6. **Read only the JIT files and commands used this session** — Do NOT read all JIT files and commands unless `/improve all` was invoked.

7. **Read toolkit-config.md** (if present) — understand project conventions.

8. **Read `.claude/settings.local.json`** (if present) — note current settings.

**Priority 2b — Full Baseline (only when `/improve all` is invoked):**

If and only if `$ARGUMENTS` is `all`:

9. **Read ALL remaining JIT reference files** — Glob the references directory and read any not already read.

10. **Read ALL remaining slash commands** — Glob `.claude/commands/*.md` and read any not already read. Note structural patterns.

**Priority 3 — Historical Context:**

11. **Check for previous improve reports** — Glob for `improve_*.md` in the improve_reports directory (typically `workflow/improve_reports/` or similar — infer from project structure). If any exist, read the most recent one.

12. **Scan git history** — run:
    ```bash
    git log --oneline -15
    git diff --stat HEAD~10
    ```

13. **Scan recent summaries** — Only when `/improve all` is invoked. Glob for the last 5 daily or session summaries. Look for friction signals.

14. **Declare scan scope** — record what you read and what you skipped. This goes in the report header.

### Pass 2: Analyze — Identify Gaps Across Seven Categories

For each category, compare what you found in Pass 1 against what *should* exist. **Categories are ordered by priority — session-specific findings come first.**

#### Category A (HIGHEST PRIORITY): Session-Specific Findings

This is where the conversation-first philosophy lives. For each command/JIT/rule touched in this session:
- **Commands used**: Did the command produce the right result? Where did it waste tokens, cause friction, or produce ambiguous outputs?
- **JIT files referenced**: Were they complete? Did the agent have to work around missing info?
- **Project rules tested**: Did any rule cause ambiguity or divergence between subagents?
- **Patterns observed**: Did the session reveal a workflow pattern that should be codified?
- **Every /improve invocation MUST produce at least one Category A finding.** If nothing needs improvement, explain why (forces engagement with session context rather than defaulting to the broad scan).

#### Category B: JIT Reference File Updates
- Are there procedures described in CLAUDE.md that are long enough to warrant their own JIT file but don't have one?
- Are existing JIT files stale (content doesn't match current practice)?
- Did session notes or summaries describe lessons that should be codified as JIT references?
- Were the same types of errors fixed multiple times in git (pattern = needs a JIT file)?

#### Category C: Slash Command Improvements
- Do any commands have outdated version numbers or missing frontmatter fields?
- Are there inconsistent patterns across commands?
- Did any commands fail or produce suboptimal results recently?
- Are there missing edge case handlers?

#### Category D: CLAUDE.md Updates
- Are there new workflow patterns that emerged from recent work but aren't documented?
- Is the JIT Reference Files table missing entries for files that exist?
- Are there implicit "rules" being followed that should be explicit hard rules?
- Is any section of CLAUDE.md stale or contradicted by current practice?

#### Category E: New Infrastructure Proposals
- Are there recurring topics (3+ touches in git/summaries) that deserve their own JIT reference file?
- Are there project areas without command coverage that would benefit from a slash command?
- Should any settings be different?

#### Category F (optional): Memory/State Staleness
- Is the project's memory or state index outdated based on recent git activity?
- Are there memory files that reference stale information?
- **Note**: Flag staleness only. Do NOT propose detailed rewrites.

#### Category G: Folder Organization (session directories only)

For each directory created in or written to during the session:

1. **Discoverability audit** — Can a future session find these artifacts?
   - Are new files in logical locations relative to existing project structure?
   - Are there orphaned files not referenced by any parent document or index?
   - Are plans, research runs, or reports in their expected directories?

2. **Naming consistency** — Do new files follow the project's naming conventions?
   - Date-prefixed summaries, descriptive plan names, etc.

3. **Index/pointer check** — Are new artifacts referenced from somewhere discoverable?
   - Does the session summary mention them?
   - Are they in a JIT reference, CLAUDE.md, or memory file?

4. **Propose reorganization** only when:
   - Files are in clearly wrong locations
   - A new subdirectory would make a cluttered folder navigable (5+ new files of the same type)
   - An existing folder structure has a gap this session's work revealed

**Constraints**:
- Never move files without proposing the move in the report first
- Never rename files that other documents reference (check for inbound references first)
- When `/improve all` is invoked, expand this to cover ALL project directories

### Pass 3: Synthesize — Build Recommendation List

For each finding from Pass 2, create a recommendation entry:

1. **Priority assignment** — Three tiers:
   - **Critical**: Recurrent friction (multiple sessions or git commits) OR high error risk. Costs >30 min cumulative if not fixed.
   - **Useful**: Appeared at least once with a clear fix. Saves time or improves consistency. 5-30 min savings.
   - **Nice-to-have**: Speculative improvement. No evidence of actual pain. Minor polish.

2. **Recurrence check** — If this recommendation also appeared in a previous improve report and hasn't been implemented, tag it `[RECURRENT]`.

3. **Action type** — Classify each recommendation:
   - `CREATE` — new file that doesn't exist yet
   - `INSERT` — add new content to an existing file
   - `REPLACE` — change existing content in a file
   - `APPEND` — add to the end of an existing file

4. **Draft the change** — For every recommendation, write the exact proposed text. No vague suggestions. The draft should be copy-pasteable.

5. **Cap at 10 recommendations**. If you find more than 10, keep the top 10 by priority. List overflow as one-line mentions in an "Also Noted" section.

6. **If `$ARGUMENTS` provided a focus hint**, boost focus-related recommendations by one priority tier.

### Pass 4: Quality Gate + Output

Before finalizing, review each recommendation:

- [ ] **Specific**: Names an exact file path and location within the file
- [ ] **Actionable**: Includes a draft that could be applied without additional research
- [ ] **Non-duplicative**: Not already covered by an existing JIT file, command, or CLAUDE.md section
- [ ] **In-scope**: Target file is in the In-Scope list above
- [ ] **Non-conflicting**: Does not contradict a CLAUDE.md hard rule

**Drop any recommendation that fails criteria 1-3 after one revision attempt.**

---

## REPORT FORMAT

Generate the report in this exact format:

```markdown
# /improve Report — YYYY-MM-DD

## Scan Summary
- **Session context**: [commands used, JIT files referenced, project rules tested, key friction points]
- **Git activity**: [N] commits scanned, [key patterns]
- **Summaries read**: [list with dates]
- **Infrastructure baseline**: [N] JIT files, [N] commands
- **Previous /improve report**: [date or "None — first run"]
- **User focus**: [focus hint or "Full scan"]

---

## Critical

### 1. [Title] [RECURRENT]?
- **Category**: [JIT Reference / Command / CLAUDE.md / New File / Memory Staleness]
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

## Also Noted

[One-line mentions of items that didn't make the top 10, if any]

---

## Summary
- Critical: [N] items
- Useful: [N] items
- Nice-to-have: [N] items
- Recurrent: [N] items from previous reports
- To implement: say "apply recommendation [N]" or "apply 1, 3, 5"
```

---

## SAVE THE REPORT

After generating the report:

1. Get today's date: `date '+%Y-%m-%d'`
2. Determine the improve_reports directory: check for `workflow/improve_reports/`, `workflow/improve_reports/`, or `.claude/improve_reports/`. If none exists, create `improve_reports/` in the project root.
3. Save the report to `[improve_reports_dir]/improve_YYYY-MM-DD.md`
4. If a report with today's date already exists, append a sequence number: `improve_YYYY-MM-DD_2.md`
5. Display the full report in conversation AND save to file.

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

1. Find the improve_reports directory (check `workflow/improve_reports/`, `workflow/improve_reports/`, `improve_reports/`)
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

## BEHAVIORAL CONSTRAINTS

- **Never auto-edit files.** The report is advisory. Changes require explicit user approval.
- **Self-improvement allowed.** This command CAN propose improvements to itself (`improve.md`) when evidence warrants it.
- **Never modify files in the Off-Limits list.**
- **The report is the deliverable.** Do not produce side-effect files beyond the report itself.
- **Be honest about uncertainty.** If you're unsure whether a recommendation is valid, say so in the "Why" field.
- **Respect Occam's razor.** Each recommendation should pass: "Would this save the user time or prevent errors?"
- **Verify empirical claims in drafts.** If a recommendation draft contains specific numbers (percentages, token counts, timing), verify against source data before presenting.

$ARGUMENTS
