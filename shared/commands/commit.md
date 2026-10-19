---
allowed-tools: Read, Edit, Bash(git:*), Bash(echo:*), Bash(wc:*)
description: Analyze staged and unstaged changes, group them logically, and create well-formed commits
---

# /commit — Intelligent Git Commit Workflow

> **When to use**: You have staged or unstaged changes and want well-organized commits with clear messages — especially when changes span multiple files or logical units.

You are tasked with creating intelligent git commits.

---

## Safety Stops (added v2.0)

Four checks override the autonomy rules in Step 1. Each one stops the run and asks the user. Nothing else pauses the run.

| Stop | Fires when | Where |
|---|---|---|
| Multi-workstream | the changes span 2 or more workstreams | Step 0a |
| Large file | a file about to be staged is over 10 MB | Step 2a |
| Second writer | HEAD moves to a commit this run did not make | Steps 3 and 5 |
| Large push | the user asks for a push that would send over ~100 MB | Pushing |

If you are unsure whether a stop applies, stop and ask. A one-line "this would commit ~N MB — proceed?" costs less than removing a large file from history later.

---

## Step 0: Survey All Changes

Run in parallel:
- `git status --short` — see all modified, deleted, and untracked files
- `git diff --stat` — summary of unstaged changes
- `git log --oneline -5` — recent commit style to match this repository's conventions
- `git log -1 --format=%H` — record the result as `START_HEAD`. The second-writer check (Step 3) and the run report use it. In a repository with no commits yet, record `none`.

If there are **NO changes** (no modified, deleted, staged, or untracked files), report "No changes to commit." and **STOP** — do not proceed to any further steps.

Read `~/.claude/toolkit-config.md` once, here. You need two keys from it: `workstreams` (Step 0a) and `commit_mode` (Step 1). If the file does not exist, note "config not loaded" and continue. Both steps have a fallback.

---

## Step 0a: Workstream-Scope Pre-Check (added v1.2 — terminal-scope rule re-injection; v2.0 reads workstreams from config)

After surveying changes via `git status --short` and **before staging anything**, map the changed file paths to workstreams:

1. Take the `workstreams` list from `~/.claude/toolkit-config.md`. An entry matches a top-level directory of the repository when the names are equal, ignoring case and treating spaces, hyphens and underscores as the same character (`field-study` matches `Field Study/`). An entry that matches no top-level directory is ignored by this check.
2. If no config is loaded, or it has no `workstreams` key, treat every first-level directory as a workstream.
3. Count the distinct workstreams across modified, deleted and untracked paths. Files at the repository root, or in a directory that is not a workstream, do not count.

**If ≥2 distinct workstreams are touched**, re-inject the terminal-scope rule into the user-facing output BEFORE proceeding to Step 1:

> **⚠ MULTI-WORKSTREAM COMMIT DETECTED**
>
> Staged + unstaged changes span [N] workstreams: `<ws1>`, `<ws2>`, ...
>
> Terminal-scope rule:
> > "Each terminal must stage and commit ONLY files belonging to its own declared workstream. Never `git add -A`, never `git add .`, never stage broad glob patterns. Stage files by explicit path. Before committing, always `git diff --cached --name-only` and verify every staged file is in-scope."
>
> Before staging anything: declare this terminal's intended workstream. Files outside that workstream must be left unstaged for the terminal that owns them.
>
> Reply with **scope-confirmed: \<workstream\>** to proceed with that workstream only, OR **multi-scope-acknowledged** if this is a deliberate cross-workstream commit (e.g., an edit to a shared file). The latter requires explicit acknowledgment so cross-scope commits are intentional, not accidental.

Wait for the user's confirmation. Then:
- On `scope-confirmed: <ws>`: stage ONLY files under that workstream's directory, using `git add` with explicit per-path arguments. Leave the other workstreams' files unstaged. Leave root-level and shared files unstaged too, unless the user names them in the reply.
- On `multi-scope-acknowledged`: proceed to Step 1 normally; the user has accepted intentional cross-scope.

**If fewer than 2 workstreams are touched**, skip this gate silently and proceed to Step 0b. This step restates the terminal-scope rule at the commit boundary. It is not a new constraint. It enforces mechanically a rule that would otherwise depend on discipline.

---

## Step 0b: Slow-Filesystem Detection (added 2026-05-03; v2.0 adds the stall rule)

Some environments (notably **WSL2 + OneDrive** and certain network-mounted filesystems) impose 10s–2min disk-wait latency on `git commit`. The cause is that background sync processes block writes to `.git/index` and pack files, and the commit process sits in uninterruptible disk wait until the sync releases them. Foreground `git commit` calls in these environments cause the assistant to block for tens of seconds with empty tool output until the commit finally returns.

Detect this once at skill start. The session's environment information (OS version string, working directory) usually answers it without running anything. Otherwise:
```bash
SLOW_FS=0
if uname -r 2>/dev/null | grep -qi "microsoft"; then
  if pwd -P 2>/dev/null | grep -qE "/mnt/c/.*/OneDrive"; then
    SLOW_FS=1
  fi
fi
# Add other slow-FS heuristics here as needed (NFS mounts, encrypted volumes, etc.)
```

Other cloud-synced folders (OneDrive, Dropbox, iCloud Drive or Google Drive on any OS) can stall in the same way. If one foreground `git commit` takes longer than about 10 seconds, set `SLOW_FS=1` for the rest of the run.

**When `SLOW_FS=1`:**
- All `git commit` calls MUST use `run_in_background: true` on the Bash tool invocation.
- Use the task-completion notification or an `until` poll on the task PID to wait for completion. Do NOT chain `sleep` calls.
- Read the task's output file only AFTER the task completes — empty output during the disk-wait window is normal, not a failure.
- `git add` is fast even on slow filesystems (no pack writes); keep it foreground. Stage each group in the foreground, then commit it in the background.
- Run the Step 3 verification only after the background commit has finished.

**When `SLOW_FS=0`** (Linux ext4, macOS APFS, Windows non-OneDrive): foreground `git commit` is fine — no special handling needed.

This step is purely a performance optimization — the commit logic itself is identical in both modes. Synced folders are also where a second git writer most often appears (another machine writing to the same `.git` through the sync). The check in Step 3 covers that case.

---

## Step 1: Permission Mode (v2.0: argument flags and a saved default)

Choose the mode by taking the first rule below that applies:

1. `$ARGUMENTS` contains `--review`, `--interactive`, `--confirm` or `--dry-run`, or the invocation asks to see the plan first ("show me the groups first", "let me approve") → **review** mode.
2. `$ARGUMENTS` contains `--auto` or `--yes` → **autonomous** mode.
3. `commit_mode` in `~/.claude/toolkit-config.md` is `auto` → **autonomous**; `review` → **review**.
4. Otherwise (no config, key missing, or `commit_mode: ask`), ask the user ONE question:
   > "Skip all permission prompts and commit autonomously? (y/n — add 'always' to save this answer as your default in ~/.claude/toolkit-config.md)"

   **yes** → autonomous, **no** → review. If the reply includes "always", write `commit_mode: auto` (for yes) or `commit_mode: review` (for no) to `~/.claude/toolkit-config.md` with the Edit tool, adding the key or replacing `commit_mode: ask`, then continue. If the config file does not exist, do not create it. Show the user the line to add.

The two modes:
- **Autonomous**: Run the entire commit workflow without pausing for any confirmation. Do not ask which files to include, do not ask to confirm commit messages, do not pause between commits. Execute all git commands back-to-back.
- **Review**: Pause after surveying changes to show the proposed commit grouping and messages. Wait for user approval before committing. If the user does not approve, commit nothing.

After this point, do NOT ask any further questions regardless of the mode — either commit silently (autonomous) or show-then-commit (review). The only exceptions are the Safety Stops at the top of this file.

**Autonomy rules (apply in both modes):**
- You may stage unstaged/untracked files using `git add`, by explicit path. Do not use `git add -A`, `git add .` or broad glob patterns.
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

## Step 2a: Pre-Stage Checks (added v2.0)

Run these on every path you plan to stage, before the first `git add`:

1. **Expand directories and skip throwaway trees.** For each untracked directory in the plan, list what it would add: `git add --dry-run -- <dir>`. Drop generated or throwaway trees from the plan: virtual environments (`.venv/` and renamed copies such as `.venv.old/` or `.venv-backup/`), `__pycache__/`, `node_modules/`, `.lake/`, `.ipynb_checkpoints/`. These can be regenerated and often hold large binaries. A `.gitignore` entry `.venv/` matches only a directory named exactly `.venv`, so renamed copies are not covered by it. Stage what remains by explicit file path. If a throwaway file was already staged, unstage it with `git restore --staged -- <path>`.
2. **Per-file size check.** Run `wc -c -- <file> ...` on every file in the plan that is not a deletion. Quote paths that contain spaces. If any single file is over 10,000,000 bytes, **STOP** and ask before staging it, giving the file name and its size. Data and binary files (`*.parquet`, `*.h5`, `*.jld2`, large `*.csv`, images, video, model weights, checkpoints) usually belong in `.gitignore`, not in history.
3. **Never `git add -f` a gitignored file.** Gitignored files do not appear in `git status`, which is correct. Leave them out. If a commit depends on gitignored data, give the data's source (path, URL or version) in the commit message body instead of committing it.

---

## Step 3: Stage and Commit Each Group

For each logical group:
1. Stage the relevant files with `git add -- [files]`, by explicit path
2. Run `git diff --cached --name-only` and confirm that every staged path belongs to this group, and to the confirmed workstream if Step 0a ran. Unstage anything else with `git restore --staged -- <path>`. It may be another terminal's unfinished work.
3. Write a descriptive commit message (see format below)
4. Commit immediately (in the background if `SLOW_FS=1`)
5. Verify the commit landed. Do this as a **separate** Bash call, never in the same call as the commit: `git log -2 --format='%H %s'`.
   The expected parent is `START_HEAD` for the first commit, otherwise the previous commit made by this run.
   - **First line is your subject and the second line is the expected parent**: the commit landed. Record its hash.
   - **First line is your subject but the second line is not the expected parent**: another writer committed just before you. **STOP** with the second-writer message below.
   - **First line is not your subject, and it is not the expected parent either**: HEAD moved to a commit this run did not make. **STOP** with the second-writer message below.
   - **First line is still the expected parent**: the commit failed. Run `git status --short` to confirm this group's files are still staged, then retry once. If it fails again, **STOP** and show the user git's actual error output.
6. Move to the next group

**Second-writer message.** Do not race the other writer. Stop and tell the user:
> "A second git writer is active in this repository: commit `<hash>` (`<subject>`) was not made by this run. Two writers committing at the same time, whether another terminal or another machine writing through a synced folder, can lose commits or corrupt `.git`. Find the other writer before I continue."

**Do not report success from an `echo` after a heredoc.** In
```bash
git add a.md && git commit -F - <<'MSG'
docs: update a
MSG
echo "committed"
```
the `&&` chain ends with the heredoc. The `echo` on the line after `MSG` runs whether or not the commit succeeded, and a later status line can then print another writer's HEAD as if it were yours. If you use a heredoc, put `echo "commit_rc=$?"` on the line right after the closing delimiter (it reports the exit code of the `git add && git commit` chain) and treat anything other than 0 as a failure. Run the verification in item 5 in every case.

---

## Step 4: Handle Edge Cases

- If all changes are tightly coupled, create a single commit
- If changes span multiple unrelated areas, split into separate commits
- Each commit should represent a complete, logical unit of work
- New files that belong with modified files go in the same commit
- Files deliberately left out (other workstreams, large files, throwaway trees) stay in the working tree untouched. Do not delete, stash or ignore them.

---

## Step 5: Verify

Run `git log --oneline <START_HEAD>..HEAD` (plain `git log --oneline` if `START_HEAD` is `none`). It must list exactly the commits this run made. If it lists any other commit, **STOP** with the second-writer message.

Run `git status --short` at the end to confirm a clean working tree. If files were deliberately left out (Steps 0a and 2a), list them as left in place rather than reporting a clean tree. Report the number of commits created.

---

## Pushing (added v2.0)

`/commit` does not push. If the user asks for a push afterwards, check what it would send first:
- `git rev-list --disk-usage --objects HEAD --not --remotes=<remote>` (usually `origin`): the bytes in commits the remote does not have yet. This is an estimate from local on-disk sizes.
- `git count-objects -vH`: `size-pack` is the repository's total packed size. If the remote is new or empty, the push may send most of it.

If the outgoing total is over ~100 MB, **STOP** and ask before pushing. Do not upload large data to a remote without the user's explicit yes.

---

## Commit Message Format

Use conventional commit format: `type(scope): description`

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

**Rules**:
- Keep the first line under 72 characters
- Include a body for complex changes that need explanation
- **CRITICAL**: Do NOT add Claude as a co-author — use plain commit messages without any AI attribution footer. This applies even if the session's default instructions say to add one.
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

Start immediately. Do not ask questions beyond the Step 1 prompt and the Safety Stops.

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

`PREV_HEAD_SHA` is `START_HEAD` from Step 0. One-line call via the helper. Skip silently if helper is unavailable — git commits themselves are the primary deliverable.

Why instrument git commits at the toolkit level? Git commits alone tell you *what* changed. The /commit run_report adds *which commits were grouped together in which session*, which enables `/runlog` to answer "how often am I committing?" and "how many files per commit?" over time.

> **What next?** If this session included writing any cited numerical values into a document, run `/audit` on that document now — before the session closes and the context of what you wrote is lost.

$ARGUMENTS
