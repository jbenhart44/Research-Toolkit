# Research Amp Toolkit — Student Bootstrap

**Version:** 2.2.0
**Date:** 2026-10-20

## What This File Does

When you give this file to Claude Code, it installs the full 24-command
research toolkit: setup (/setup), structured planning (PCV, quick-ten),
verification (CoA, PACE, audit, acquire, review, bulletproof, guard-hook),
workflow automation (startup, daily-summary, weekly-summary, commit, simplify,
improve, help, run-log, list-maker, step-by-step, meeting-breakdown, automate), and
content generation (quarto, readable), plus the council seat agents that
/coa starts.

## How to Install

1. Start a Claude Code session.
2. Say: `Read [path-to-this-file] and follow the installation instructions.`
3. Claude Code will copy the files and confirm success.

---

## Instructions for Claude Code

You are reading a toolkit bootstrap file. Follow these steps. **Never work
from a typed list of files: glob the folder and copy what is there**, so a
file added in a later release is installed too.

### Step 1: Locate the toolkit

This bootstrap file is inside `Research-Toolkit/student/`. Determine the
absolute path to the `Research-Toolkit/` directory by resolving from this
file's location (go up one directory from `student/`). Then:

- command files: `Research-Toolkit/shared/commands/*.md`
- PCV skill: everything under `Research-Toolkit/pcv/skill/`, including its
  subfolders (`handlers/`, `hooks/`, `planning/`, `construction/`,
  `verification/`, `transition/`, `bundled/`)
- PCV agents: `Research-Toolkit/pcv/agents/*.md`
- skills: each folder in `Research-Toolkit/shared/skills/`
- council seat agents: `Research-Toolkit/coa/agents/*.md`

### Step 2: Install command files

Glob `Research-Toolkit/shared/commands/*.md`. Copy every file it returns to
`~/.claude/commands/` with the Read and Write tools (not shell cp). Remember
the list: Step 6 checks it.

If any file already exists at the destination, back it up first
(append `.bak` to the existing file).

### Step 3: Install the PCV skill

Glob `Research-Toolkit/pcv/skill/**/*` and copy every file to
`~/.claude/skills/pcv/`, **keeping its path below `pcv/skill/`**: for
example `pcv/skill/handlers/plan-tier.sh` goes to
`~/.claude/skills/pcv/handlers/plan-tier.sh`. The skill calls its
`handlers/` and `hooks/` scripts by those paths, so copying only the
top-level files leaves `/pcv` broken at its first step.

If `~/.claude/skills/pcv/` already has files, copy the whole folder to
`~/.claude/toolkit-backups/<today's date>/skills/pcv/` first. Never put a
backup inside `~/.claude/skills/`, where it could load as a second skill.

### Step 4: Install PCV agents

Glob `Research-Toolkit/pcv/agents/*.md` and copy every file to
`~/.claude/agents/`.

### Step 4b: Install the runtime scripts

Some commands end by calling a helper script at
`$HOME/.claude/toolkit/scripts/<name>.py` (the run-report helper, for one).
Search the command files from Step 2, and the `SKILL.md` of every skill
Step 4c installs, for `.claude/toolkit/scripts/` and note each `<name>.py`
they call. Copy each one from `Research-Toolkit/scripts/` to
`~/.claude/toolkit/scripts/`, creating the folder if needed. Copy only the
files the commands call: never a `_selftest.py` or `_mutations.py` file.

### Step 4c: Install the skills

For each folder in `Research-Toolkit/shared/skills/`, copy its `SKILL.md`,
and any files in its `assets/` folder except `_selftest.py` and
`_mutations.py` files, to `~/.claude/skills/<folder name>/`. If that folder
already exists, copy it to `~/.claude/toolkit-backups/<today's date>/skills/`
first. If `~/.claude/commands/<folder name>.md` also exists, tell the user that
the skill takes precedence, and remove nothing.

### Step 4d: Install the council seat agents

Glob `Research-Toolkit/coa/agents/*.md` and copy every file to
`~/.claude/agents/`, backing up any existing file first (append `.bak`).
Only if the user asks for the add-on seats, do the same for
`Research-Toolkit/coa/agents/addon/*.md`.
`/coa` starts these seats by name; without them it falls back to its
built-in template.

### Step 5: Install the config template

If `~/.claude/toolkit-config.md` does not exist, copy
`Research-Toolkit/toolkit-config.md` to `~/.claude/toolkit-config.md`.
If it already exists, do not overwrite it; `/setup` will update it.

### Step 6: Verify

- Every file from the Step 2 glob is present in `~/.claude/commands/`.
- `~/.claude/skills/pcv/` holds as many files as the Step 3 glob returned,
  and `~/.claude/skills/pcv/VERSION` exists.
- Every file from the Step 4 glob is present in `~/.claude/agents/`.
- Every script noted in Step 4b is present in `~/.claude/toolkit/scripts/`.
- Every skill from Step 4c has its `SKILL.md` in `~/.claude/skills/<name>/`.
- Every file from the Step 4d glob is present in `~/.claude/agents/`.

If anything is missing, copy it again and re-check. Do not report success
until all six hold.

### Step 7: Report

Fill in the numbers from the globs; do not type them from this file.

> **Research Amp Toolkit installed.**
>
> **{C + K + 1} commands**: {C} command files, {K} skills and the `/pcv` skill
> **PCV v{contents of VERSION}**: {S} files in `~/.claude/skills/pcv/`
> **{A} PCV agents** and **{E} council seat agents** in `~/.claude/agents/`
> **{R} runtime scripts** in `~/.claude/toolkit/scripts/`
>
> **Next steps:**
> 1. Restart Claude Code so it picks up the newly installed commands and agents.
> 2. Type `/setup` and answer its questions about your project.
> 3. Type `/startup` to get oriented.
> 4. Type `/pcv` in any project to start structured planning.
>
> Optional: the hooks (including the usage counter) install only through
> `bash install.sh --hooks`.
