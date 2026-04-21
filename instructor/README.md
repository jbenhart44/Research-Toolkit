# Instructor Toolkit

A curated 6-command subset of the Research Amp Toolkit, designed for professors integrating AI-assisted workflows into graduate courses.

## Installation

```bash
cd ai-research-toolkit
bash install.sh --minimal
```

This installs 6 commands + PCV. Takes under 5 minutes.

## Commands

| Command | What it does | Teaching Guide |
|---------|-------------|----------------|
| `/pcv` | Structured planning with clarification, review, and approval gates | [Using PCV in Courses](guides/using-pcv-in-courses.md) |
| `/coa` | Multi-perspective analysis from different professional viewpoints | [Using CoA for Discussion](guides/using-coa-for-discussion.md) |
| `/pace` | Parallel verification — catches errors through redundancy | [Using PACE for Grading](guides/using-pace-for-grading.md) |
| `/improve` | Self-reflective audit of Claude Code infrastructure | — |
| `/quarto` | Generate slide decks from documents | — |
| `/pdftotxt` | Extract text from PDF/Word files | — |

## Getting Started

1. Install with `bash install.sh --minimal`
2. Edit `~/.claude/toolkit-config.md` with your course details
3. Read [Using PCV in Courses](guides/using-pcv-in-courses.md) — it walks through a complete example
4. Try `/pcv` on a small class project to see the workflow

## Upgrading to Full Suite

If you want the workflow commands (daily summaries, session startup, etc.):
```bash
bash install.sh   # Re-run without --minimal
```
