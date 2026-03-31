# Student Toolkit

The full 12-command AI-Assisted Research Toolkit. Everything I actually use in my PhD research — structured planning, verification, documentation, and workflow automation.

## Installation

**Option A — In Claude Code (recommended):**
```
Read ai-research-toolkit/student/bootstrap.md and follow the installation instructions.
```

**Option B — Shell script:**
```bash
cd ai-research-toolkit
bash install.sh
```

## Day 1

After installation:
1. Edit `~/.claude/toolkit-config.md` with your project details
2. Open Claude Code in your project directory
3. Type `/startup` — it reads your recent work and tells you where you left off

## Commands at a Glance

### Start your day
- `/startup` — Where was I? What should I work on?

### Plan a project
- `/pcv` — Structured planning with charge → clarification → adversarial review → approved plan

### Make a decision
- `/coa` — Get 4-6 specialist perspectives on a research question
- `/pace` — Verify something through parallel redundancy (two players + two coaches)
- `/pcv-research` — Run parallel planning experiments (depth-first vs. breadth-first) with instrumentation

### Write and review
- `/quarto` — Generate slide decks from documents
- `/simplify` — Review code for quality issues
- `/pdftotxt` — Extract text from PDFs and Word docs

### Stay organized
- `/dailysummary` — Summarize today's work
- `/weeklysummary` — Aggregate the week's progress by workstream
- `/commit` — Create logical, well-organized git commits
- `/improve` — Audit your own Claude Code setup for improvements

## Tips

- **Start with `/pcv` and `/startup`.** These two commands give you the most immediate value.
- **Run `/dailysummary` at the end of every session.** Your future self will thank you.
- **Use `/coa --quick` for focused questions.** A 3-seat panel is fast and cheap.
- **Run `/improve` monthly.** It catches stale references and missing workflows.
