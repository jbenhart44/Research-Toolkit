---
allowed-tools: Read, Write, Edit, Glob, Bash(git:*), Bash(ls:*)
description: One-time setup interview — asks about your project and writes ~/.claude/toolkit-config.md, which every other command reads instead of hard-coded paths
---

# /setup — Toolkit Setup Interview

> **When to use**: Once, right after installing the toolkit, and again whenever your project changes shape (a new workstream, a moved folder). Other commands still work without it; they fall back to defaults and ask for a missing value the first time they need it.

You are executing the `/setup` command. Your job is to interview the user briefly and write `~/.claude/toolkit-config.md`, the one file the other commands read for project-specific values (names, workstreams, folders). Nothing in the toolkit hard-codes these values; this file is where they live.

**Goal**: a complete, correct config in under two minutes, with no question the user has already answered.

---

## STEP 0: Read what already exists

1. If `~/.claude/toolkit-config.md` exists, read it. This run **updates** it: show each current value as the default and change only what the user changes. Never discard a key you do not recognise; carry it over unchanged.
2. If it does not exist, start from the template `toolkit-config.md` in the toolkit repository (or the keys in STEP 1).
3. Look before asking. Offer detected values as defaults:
   - `project_name`: the git repository name (`git rev-parse --show-toplevel`), or the current folder name.
   - `author_name`: `git config user.name`.
   - `workstreams`: the top-level folders of the repository that hold work (`ls -d */`, skipping hidden folders, `node_modules`, build output and the summary folders).
   - `summary_folder` / `weekly_folder`: an existing folder whose name contains "summary", if there is one.

## STEP 1: Ask, in at most three short rounds

Ask with the `AskUserQuestion` tool when available (plain questions otherwise). Put the detected value first and mark it `(detected)`, so a user can accept everything in a few clicks.

| Key | Question | Default |
|---|---|---|
| `project_name` | What is this project called? | detected repo name |
| `author_name` | Whose name goes on summaries and headers? | `git config user.name` |
| `workstreams` | Which folders or threads are separate workstreams? (used by `/commit` to stop cross-workstream commits, and by `/startup` and `/weeklysummary` to organise reports) | detected top-level folders |
| `summary_folder` | Where should daily summaries go? | `Daily Summary` |
| `weekly_folder` | Where should weekly summaries go? | `Weekly Summary` |
| `evidence_dir` | Where should run evidence (run logs, per-run reports) go? | `.toolkit/evidence` |
| `project_type` | Research or teaching? (changes how `/startup` frames its briefing) | `research` |

Round 1: project, author, project type. Round 2: workstreams. Round 3: the three folders, offered as one "accept the defaults?" question first.

Do not ask for anything else. These optional keys are asked by the command that needs them, the first time it needs them, so `/setup` only mentions that they exist:

| Key | Asked by | Meaning |
|---|---|---|
| `startup_exclude` | `/startup` | workstreams never reported |
| `backlog_file` | `/startup` | backlog whose deferred items it checks (`none` disables) |
| `scheduled_jobs` | `/startup` | `name \| cadence \| log path` entries checked for missed runs |
| `extra_repos` | `/dailysummary` | other repositories this project's sessions commit to |
| `commit_mode` | `/commit` | `ask` (default), `auto` or `review` |
| `shared_code_dirs` | `/simplify` | folders checked for cross-file duplication |
| `author_affiliation` | `/quarto` | affiliation under the author name, and a branded footer |
| `quarto_theme_dir` | `/quarto` | folder holding your branded RevealJS theme |
| `slides_folder` | `/quarto` | where decks go when they belong to no project folder |

A command that needs a value not listed anywhere here asks the user once and offers to add the key to this file itself.

## STEP 2: Show the result, then write it

Show the complete file before writing:

```
Here is your config. Say "yes" to save it to ~/.claude/toolkit-config.md, or correct any line.
```

On "yes", write the file in this format (YAML-style `key: value` lines under `##` headings, comments kept), preserving any unknown keys from STEP 0:

```markdown
# Toolkit Configuration
# Written by /setup on <YYYY-MM-DD>. Edit by hand or re-run /setup.

## Project Identity
project_name: <value>
author_name: <value>

## Workstreams
workstreams: [<a>, <b>, <c>]

## Folder Paths
summary_folder: <value>
weekly_folder: <value>
evidence_dir: <value>

## Project Type
project_type: <research|teaching>
```

Create `summary_folder`, `weekly_folder` and `evidence_dir` inside the project if they do not exist, and say so.

## STEP 3: Confirm

Report in three lines: the file written, the folders created, and the next command to try (`/startup` for an orientation, `/help` for a menu).

## Rules

- Never write the file without the user's "yes" on the shown content.
- Never put a secret (API key, token, password) in this file. If the user offers one, say where it belongs instead (an environment variable or the tool's own credential store).
- Paths are written relative to the project root unless the user gives an absolute path on purpose.
