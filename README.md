# AI-Assisted Research Toolkit

> **By Jake Benhart & Dr. Michael G. Kay**
> **NC State University — Operations Research & Industrial and Systems Engineering**

A battle-tested collection of Claude Code commands for structured AI-assisted research workflows. Built during a PhD in Operations Research and validated across 40+ sessions, 14 PCV-Research runs, 3 CoA contamination tests, and 20+ PACE verification tasks. Design rationale documented in [DESIGN.md](DESIGN.md).

---

## What This Solves

AI coding assistants are powerful but unstructured. Researchers face three recurring problems:

1. **Verification gap** — How do you know the AI's output is correct? Especially for analysis, citations, and numerical results?
2. **Planning gap** — Complex multi-component projects need structured planning, not ad-hoc prompting.
3. **Documentation gap** — Research progress disappears when the terminal closes. Session context is ephemeral.

This toolkit addresses all three with reusable Claude Code commands that add structure without adding friction.

---

## Two Products

### Instructor Toolkit (`instructor/`)
For professors integrating AI-assisted workflows into graduate courses. Start with one command, add more as you get comfortable.

**6 curated commands:** PCV (structured planning), CoA (multi-perspective analysis), PACE (parallel verification), /improve (infrastructure auditing), /quarto (slide generation), /pdftotxt (document extraction).

**3 teaching guides:** How to use PCV for class projects, CoA for research discussions, and PACE for grading consistency.

### Student Toolkit (`student/`)
For PhD and MS students doing computational research. The full suite — "here's what I actually use every day."

**12 commands:** Everything in the instructor toolkit plus /pcv-research (parallel planning experiments), /startup (session continuity), /dailysummary (documentation discipline), /weeklysummary (weekly aggregation), /commit (intelligent git commits), /simplify (code review).

---

## Quick Start

### Professors (5 minutes)
```bash
git clone https://github.com/[TBD]/ai-research-toolkit.git
cd ai-research-toolkit
bash install.sh --minimal
```
Then in Claude Code: type `/pcv` in any project directory.

### Students (2 minutes)
In a Claude Code session:
```
Read ai-research-toolkit/student/bootstrap.md and follow the installation instructions.
```

---

## Core Commands

### Verification Layer
| Command | What it does | Evidence |
|---------|-------------|----------|
| **PCV** | Plan-Construct-Verify workflow with sequential clarification, adversarial review, and human approval gates | [Kay's PCV v3.9](https://mgkay.github.io/pcv/) — multi-phase support, agent configuration |
| **PCV-Research** | Parallel depth-first vs. breadth-first planning experiments with instrumentation | 14 runs with cross-mode convergence analysis |
| **CoA** | Council of Agents — spawns specialists with distinct professional perspectives to analyze a question | 3 contamination tests, ECL-lite empirical validation |
| **PACE** | Parallel Agent Consensus Engine — 4-agent (2 players + 2 coaches) verification through redundancy | 20+ verification tasks with documented convergence rates |

### Workflow Layer
| Command | What it does |
|---------|-------------|
| **/startup** | Reads recent work summaries and orients you on where you left off |
| **/dailysummary** | Creates a dated summary of the day's work with cross-references |
| **/weeklysummary** | Aggregates daily summaries into weekly workstream reports |
| **/commit** | Analyzes staged changes and creates logical separate commits |
| **/simplify** | Reviews code for redundancy, complexity, and performance issues |
| **/improve** | Self-reflective meta-agent that audits your own Claude Code infrastructure |

### Content Layer
| Command | What it does |
|---------|-------------|
| **/quarto** | Generates Quarto RevealJS slide decks from background documents |
| **/pdftotxt** | Extracts text from PDF and Word files |

---

## Configuration

After installation, edit `~/.claude/toolkit-config.md` to match your project:

```markdown
# Toolkit Configuration
project_name: My Research Project
workstreams: [modeling, writing, data-analysis]
summary_folder: Daily Summary
project_type: research
```

Commands read from this file instead of hardcoded paths.

---

## Evidence

See [EVIDENCE.md](EVIDENCE.md) for full methodology and metrics.

**Highlights:**
- PCV-Research protocol (N=14 runs): depth-first mode produces 42-83% cross-instance convergence; breadth-first reveals path dependencies in cascading architecture decisions
- CoA contamination tests (N=3): independent council members produce genuinely distinct perspectives, not echo-chamber agreement
- PACE verification catches errors that single-agent workflows miss (arithmetic errors on 48+ item scoring, circular logic in model code)
- Daily/weekly summary workflow prevents knowledge loss across sessions — documented in 40+ session summaries

---

## Citation

If you use this toolkit in your research, please cite:

```bibtex
@software{benhart_kay2026toolkit,
  author = {Benhart, Jake and Kay, Michael G.},
  title = {AI-Assisted Research Toolkit for Claude Code},
  year = {2026},
  url = {https://github.com/jbenhart44/Research-Toolkit}
}
```

See [CITATION.md](CITATION.md) for full attribution details.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Roadmap

See [DESIGN.md](DESIGN.md) for the full tradeoff log and v2+ backlog with reasoning for each deferral.
