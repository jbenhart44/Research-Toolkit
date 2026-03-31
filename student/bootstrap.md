# AI-Assisted Research Toolkit — Student Bootstrap

**Version:** 1.0
**Date:** 2026-03-30

## What This File Does

When you give this file to Claude Code, it installs the full 12-command
research toolkit: structured planning (PCV, PCV-Research), verification
(CoA, PACE), workflow automation (startup, dailysummary, weeklysummary,
commit, simplify, improve), and content generation (quarto, pdftotxt).

## How to Install

1. Start a Claude Code session.
2. Say: `Read [path-to-this-file] and follow the installation instructions.`
3. Claude Code will copy the command files and confirm success.

---

## Instructions for Claude Code

You are reading a toolkit bootstrap file. Follow these steps:

### Step 1: Locate the toolkit

This bootstrap file is inside `ai-research-toolkit/student/`. The command
files are at `ai-research-toolkit/shared/commands/`. The PCV skill files
are at `ai-research-toolkit/pcv/skill/` and agent files at
`ai-research-toolkit/pcv/agents/`.

Determine the absolute path to the `ai-research-toolkit/` directory by
resolving from this file's location (go up one directory from `student/`).

### Step 2: Install command files

Copy each `.md` file from `ai-research-toolkit/shared/commands/` to
`~/.claude/commands/`. Use the Read and Write tools (not shell cp).

Files to install (12 total):
- coa.md
- pace.md
- pcv-research.md
- improve.md
- startup.md
- dailysummary.md
- weeklysummary.md
- commit.md
- simplify.md
- quarto.md
- pdftotxt.md

If any file already exists at the destination, back it up first
(append `.bak` to the existing file).

### Step 3: Install PCV skill

Copy all files from `ai-research-toolkit/pcv/skill/` to
`~/.claude/skills/pcv/`. Files: VERSION, SKILL.md,
planning-protocol.md, construction-protocol.md,
verification-protocol.md, phase-transition-protocol.md.

### Step 4: Install PCV agents

Copy all files from `ai-research-toolkit/pcv/agents/` to
`~/.claude/agents/`. Files: pcv-critic.md, pcv-research.md,
pcv-builder.md, pcv-verifier.md.

### Step 5: Install config template

If `~/.claude/toolkit-config.md` does not exist, copy
`ai-research-toolkit/toolkit-config.md` to `~/.claude/toolkit-config.md`.

If it already exists, do not overwrite — inform the user.

### Step 6: Verify

Read `~/.claude/skills/pcv/VERSION` and confirm it exists.
Glob `~/.claude/commands/*.md` and confirm at least 11 toolkit
command files are present.

### Step 7: Report

> **AI-Assisted Research Toolkit installed.**
>
> **12 commands** installed to `~/.claude/commands/`
> **PCV v3.9** installed to `~/.claude/skills/pcv/`
> **4 PCV agents** installed to `~/.claude/agents/`
>
> **Next steps:**
> 1. Edit `~/.claude/toolkit-config.md` with your project details
> 2. Type `/startup` to get oriented
> 3. Type `/pcv` in any project to start structured planning
