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

## Optional (each command asks once, the first time it needs one, and offers to save it here)
# startup_exclude: [old-project]          # /startup: workstreams never reported
# backlog_file: plans/BACKLOG.md          # /startup: backlog whose deferred items it checks; none disables
# scheduled_jobs: [nightly | daily | logs/nightly.log]   # /startup: job | cadence | log path, checked for missed runs
# extra_repos: [../paper-overleaf]        # /dailysummary: other repos this project's sessions commit to
# commit_mode: ask                        # /commit: ask (default) | auto | review
# shared_code_dirs: [src/utils]           # /simplify: folders checked for cross-file duplication
# author_affiliation: Your Department     # /quarto: affiliation under the author, and a branded footer
# quarto_theme_dir: ~/themes/myorg        # /quarto: folder holding your branded RevealJS theme
# slides_folder: Slides                   # /quarto: where decks go when they belong to no project folder

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
