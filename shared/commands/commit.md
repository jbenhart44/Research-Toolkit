---
allowed-tools: Bash(git:*), Bash(echo:*), Bash(wc:*)
description: Analyze staged and unstaged changes, group them logically, and create well-formed commits
---

# /commit — Intelligent Git Commit Workflow

> **When to use**: You have staged or unstaged changes and want well-organized commits with clear messages — especially when changes span multiple files or logical units.

You are tasked with creating intelligent git commits.

---

## Step 0: Survey All Changes

Run in parallel:
- `git status --short` — see all modified, deleted, and untracked files
- `git diff --stat` — summary of unstaged changes
- `git log --oneline -5` — recent commit style to match this repository's conventions

If there are **NO changes** (no modified, deleted, staged, or untracked files), report "No changes to commit." and **STOP** — do not proceed to any further steps.

---

## Step 1: Permission Mode Prompt

Ask the user ONE question:
> "Skip all permission prompts and commit autonomously? (y/n)"

- If **yes**: Run the entire commit workflow without pausing for any confirmation. Do not ask which files to include, do not ask to confirm commit messages, do not pause between commits. Execute all git commands back-to-back.
- If **no**: Pause after surveying changes to show the proposed commit grouping and messages. Wait for user approval before committing.

After this single prompt, do NOT ask any further questions regardless of the answer — either commit silently (yes) or show-then-commit (no).

**Autonomy rules (apply in both modes):**
- You may stage unstaged/untracked files using `git add`
- You may create as many logical commits as needed
- Use your judgment to group logically related changes
- Do NOT add pauses or confirmations between git commands — run them back-to-back

---

## Step 2: Categorize Changes

Group files by:
- **Project folder or subsystem** — changes that belong to the same logical component
- **File type or purpose** — documentation, code, tests, configuration, infrastructure
- **Logical feature or fix boundaries** — a complete unit of work that stands on its own

---

## Step 3: Stage and Commit Each Group

For each logical group:
1. Stage the relevant files with `git add [files]`
2. Write a descriptive commit message (see format below)
3. Commit immediately
4. Move to the next group

---

## Step 4: Handle Edge Cases

- If all changes are tightly coupled, create a single commit
- If changes span multiple unrelated areas, split into separate commits
- Each commit should represent a complete, logical unit of work
- New files that belong with modified files go in the same commit

---

## Step 5: Verify

Run `git status --short` at the end to confirm a clean working tree. Report the number of commits created.

---

## Commit Message Format

Use conventional commit format: `type(scope): description`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Rules**:
- Keep the first line under 72 characters
- Include a body for complex changes that need explanation
- **CRITICAL**: Do NOT add Claude as a co-author — use plain commit messages without any AI attribution footer
- Scope is optional but helpful for multi-project repositories (e.g., `feat(modeling): ...`, `docs(experiments): ...`)

**Examples**:
```
feat(modeling): add heterogeneous initialization to agent spawning
docs(experiments): update parameter sweep results for phase 3
fix(data): correct off-by-one in date range filter
chore(infra): update toolkit configuration template
```

---

## Example Grouping Logic

```
Infrastructure / config changes     → separate commit (chore)
Documentation-only changes          → separate commit (docs)
Code changes per subsystem          → one commit per subsystem (feat/fix)
New features with supporting tests  → single commit (feat)
```

---

Start immediately. Do not ask questions beyond the Step 1 prompt.

---

## Instrumentation (v1.1 — one-line emit at end of run)

After all commits are made, emit a structured run_report for observability via `/runlog`:

```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command commit \
  --run-dir ".claude/.run_reports/commit/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Session commit batch" \
  --fields "commits_made=$N_COMMITS files_total=$N_FILES branch=$CURRENT_BRANCH head_sha=$NEW_HEAD_SHA prev_head_sha=$PREV_HEAD_SHA"
```

One-line call via the helper. Skip silently if helper is unavailable — git commits themselves are the primary deliverable.

Why instrument git commits at the toolkit level? Git commits alone tell you *what* changed. The /commit run_report adds *which commits were grouped together in which session*, which enables `/runlog` to answer "how often am I committing?" and "how many files per commit?" over time.

$ARGUMENTS
