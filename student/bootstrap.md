# Research Amp Toolkit — Student Bootstrap

**Version:** 1.0
**Date:** 2026-03-30

## What This File Does

When you give this file to Claude Code, it installs the full 15-command
research toolkit: structured planning (PCV), verification (CoA, PACE, audit,
review), workflow automation (startup, dailysummary, weeklysummary, commit,
simplify, improve, help, runlog), and content generation (quarto, readable).

## How to Install

1. Start a Claude Code session.
2. Say: `Read [path-to-this-file] and follow the installation instructions.`
3. Claude Code will copy the command files and confirm success.

---

## Instructions for Claude Code

You are reading a toolkit bootstrap file. Follow these steps:

### Step 1: Locate the toolkit

This bootstrap file is inside `Research-Toolkit/student/`. The command
files are at `Research-Toolkit/shared/commands/`. The PCV skill files
are at `Research-Toolkit/pcv/skill/` and agent files at
`Research-Toolkit/pcv/agents/`.

Determine the absolute path to the `Research-Toolkit/` directory by
resolving from this file's location (go up one directory from `student/`).

### Step 2: Install command files

Copy each `.md` file from `Research-Toolkit/shared/commands/` to
`~/.claude/commands/`. Use the Read and Write tools (not shell cp).

Files to install (14 total — /pcv is installed as a skill, see Step 3):
- coa.md
- pace.md
- audit.md
- review.md
- improve.md
- startup.md
- dailysummary.md
- weeklysummary.md
- commit.md
- simplify.md
- help.md
- runlog.md
- quarto.md
- readable.md

If any file already exists at the destination, back it up first
(append `.bak` to the existing file).

### Step 3: Install PCV skill

Copy all files from `Research-Toolkit/pcv/skill/` to
`~/.claude/skills/pcv/`. Files: VERSION, SKILL.md,
planning-protocol.md, construction-protocol.md,
verification-protocol.md, phase-transition-protocol.md.

### Step 4: Install PCV agents

Copy all files from `Research-Toolkit/pcv/agents/` to
`~/.claude/agents/`. Files: pcv-critic.md, pcv-research.md,
pcv-builder.md, pcv-verifier.md.

### Step 5: Install config template

If `~/.claude/toolkit-config.md` does not exist, copy
`Research-Toolkit/toolkit-config.md` to `~/.claude/toolkit-config.md`.

If it already exists, do not overwrite — inform the user.

### Step 6: Verify

Read `~/.claude/skills/pcv/VERSION` and confirm it exists.
Glob `~/.claude/commands/*.md` and confirm at least 14 toolkit
command files are present.

### Step 7: Report

> **Research Amp Toolkit installed.**
>
> **15 commands** installed (/pcv as skill + 14 as command files)
> **PCV v3.14** installed to `~/.claude/skills/pcv/`
> **4 PCV agents** installed to `~/.claude/agents/`
>
> **Next steps:**
> 1. Restart Claude Code so it picks up the newly installed commands.
> 2. Edit `~/.claude/toolkit-config.md` with your project details.
> 3. Type `/startup` to get oriented.
> 4. Type `/pcv` in any project to start structured planning.
