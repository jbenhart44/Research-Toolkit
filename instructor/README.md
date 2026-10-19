# Instructor Toolkit

A curated 9-command subset of the Research Amp Toolkit, designed for professors integrating AI-assisted workflows into graduate courses.

## Installation

```bash
bash install.sh --minimal
```

This installs 9 commands: 8 command files plus the `/pcv` skill. Takes under 5 minutes.

## Commands

| Command | What it does | Teaching Guide |
|---------|-------------|----------------|
| `/setup` | Asks about your course and folders; writes the config the other commands read | — |
| `/pcv` | Structured planning with clarification, review, and approval gates | [Using PCV in Courses](guides/using-pcv-in-courses.md) |
| `/coa` | Multi-perspective analysis from different professional viewpoints | [Using CoA for Discussion](guides/using-coa-for-discussion.md) |
| `/pace` | Parallel verification — catches errors through redundancy | [Using PACE for Grading](guides/using-pace-for-grading.md) |
| `/review` | Reads a paper or memo through three expert lenses in parallel | — |
| `/improve` | Self-reflective audit of Claude Code infrastructure | — |
| `/quarto` | Generate slide decks from documents | — |
| `/readable` | Extract text from PDF/Word files | — |
| `/help` | Not sure which command fits? Describe the situation in one line | — |

## Getting Started

1. Install with `bash install.sh --minimal`
2. In Claude Code, run `/setup` and answer its questions about your course
3. Read [Using PCV in Courses](guides/using-pcv-in-courses.md) — it walks through a complete example
4. Try `/pcv` on a small class project to see the workflow

## Upgrading to Full Suite

If you want the workflow commands (daily summaries, session startup, citation audit, etc.):
```bash
bash install.sh   # Re-run without --minimal
```
