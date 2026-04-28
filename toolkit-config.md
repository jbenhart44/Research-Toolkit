# Toolkit Configuration
#
# Edit this file to match your project. Commands read from here
# instead of hardcoded paths.
#
# After editing, copy to ~/.claude/toolkit-config.md so commands
# can find it from any project directory.

## Project Identity
project_name: My Research Project
# Your name (used in commit messages, document headers)
author_name: Your Name

## Workstreams
# List the major threads of your research. /startup and /weeklysummary
# use these to organize status reports.
workstreams: [modeling, writing, experiments]

## Folder Paths
# Where daily summaries are stored (relative to project root)
summary_folder: Daily Summary
# Where weekly summaries are stored (relative to project root)
weekly_folder: Weekly Summary
# Where toolkit run-evidence (run_log.csv, per-run reports) is written.
# Used by /runlog, /audit, /pace, /coa, /pcv-research, /commit, /dailysummary,
# /improve, /startup, /help. Default is project-local; override to centralize
# evidence across multiple projects.
evidence_dir: .toolkit/evidence

## Project Type
# "research" or "teaching" — affects how /startup frames its briefing
project_type: research

# ─────────────────────────────────────────────────────────
# EXAMPLES — Delete everything below and fill in your own.
# ─────────────────────────────────────────────────────────
#
# Example 1 — PhD Research Project
# ─────────────────────────────────
# project_name: Multi-Agent Simulation of Market Dynamics
# author_name: Jane Smith
# workstreams: [modeling, validation, writing, literature-review]
# summary_folder: Daily Summary
# weekly_folder: Weekly Summary
# project_type: research
#
# Example 2 — Graduate Course
# ────────────────────────────
# project_name: Applied Optimization (graduate seminar)
# author_name: Prof. Johnson
# workstreams: [homework, projects, grading]
# summary_folder: Course Notes
# weekly_folder: Weekly Summary
# project_type: teaching
