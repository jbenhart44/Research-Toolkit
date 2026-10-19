# Student Toolkit

The full 16-command Research Amp Toolkit: structured planning, verification, documentation, and workflow automation, as its author uses them in PhD research.

## Installation

**Option A — In Claude Code (recommended):**
```
Read student/bootstrap.md and follow the installation instructions.
```

**Option B — Shell script:**
```bash
bash install.sh
```

## Day 1

After installation:
1. Open Claude Code in your project directory
2. Type `/setup` — it asks where your summaries, plans and evidence go and which workstreams you track, then writes `~/.claude/toolkit-config.md`
3. Type `/startup` — it reads your recent work and tells you where you left off

## Commands at a Glance

### Set up once
- `/setup` — Answer a few questions; every other command reads the answers

### Start your day
- `/startup` — Where was I? What should I work on?

### Plan a project
- `/pcv` — Structured planning with charge → clarification → adversarial review → approved plan

### Make a decision
- `/coa` — Get 4-6 specialist perspectives on a research question
- `/pace` — Verify something through parallel redundancy (two players + two coaches)

### Check what you wrote
- `/audit` — Verify every cited figure against the source paper
- `/review` — Read a paper or memo through three expert lenses

### Write and review
- `/quarto` — Generate slide decks from documents
- `/simplify` — Review code for quality issues
- `/readable` — Extract text from PDFs and Word docs

### Stay organized
- `/dailysummary` — Summarize today's work
- `/weeklysummary` — Aggregate the week's progress by workstream
- `/commit` — Create logical, well-organized git commits
- `/improve` — Audit your own Claude Code setup for improvements
- `/runlog` — See how your commands have performed across runs

### Not sure?
- `/help` — Describe the situation in one line; it recommends 1-3 commands

## Tips

- **Run `/setup` first, then start with `/pcv` and `/startup`.** These give you the most immediate value.
- **Run `/dailysummary` at the end of every session.** Your future self will thank you.
- **Use `/coa --quick` for focused questions.** A 3-seat panel is fast and cheap.
- **Run `/improve` monthly.** It catches stale references and missing workflows.
