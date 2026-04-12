# AI-Assisted Research Toolkit

12 Claude Code commands that catch errors, prevent bad plans, and keep complex projects on track. Organized into verification, workflow, and content layers. Validated across 40+ production sessions.

**Authors:** Jake Benhart & Dr. Michael G. Kay (NC State University — Operations Research)

Design rationale documented in [DESIGN.md](DESIGN.md).

---

## What This Solves

AI coding assistants are powerful but unstructured. Three recurring problems when using them for complex work:

1. **Verification gap** — How do you know the AI's output is correct? Especially for citations, numerical results, and analysis?
2. **Planning gap** — Complex multi-component projects need structured planning, not ad-hoc prompting.
3. **Documentation gap** — Research progress disappears when the terminal closes. Session context is ephemeral.

This toolkit addresses all three with reusable Claude Code commands that add structure without adding friction.

---

## Quick Start

```bash
git clone https://github.com/jbenhart44/Research-Toolkit.git
cd Research-Toolkit
bash install.sh
```

Then in Claude Code: type `/pcv` in any project directory to verify it works.

After installation, edit `~/.claude/toolkit-config.md` to match your project:

```markdown
# Toolkit Configuration
project_name: My Research Project
workstreams: [modeling, writing, data-analysis]
summary_folder: Daily Summary
project_type: research
```

---

## Commands

### Verification Layer
| Command | What it does |
|---------|-------------|
| **/pcv** | Plan-Construct-Verify — structured planning with clarification, adversarial review, and human approval gates |
| **/coa** | Council of Agents — spawns specialists with distinct professional perspectives to analyze a question |
| **/pace** | Parallel Agent Consensus Engine — two independent players + two coaches + cross-reviewer |
| **/audit** | Verifies every citation exists on disk and every quoted number matches the source paper |
| **/improve** | Self-reflective meta-agent that audits your Claude Code infrastructure and proposes improvements |
| **/simplify** | Reviews code or documents for redundancy, complexity, and performance issues |

### Workflow Layer
| Command | What it does |
|---------|-------------|
| **/startup** | Reads recent work summaries and orients you on where you left off |
| **/dailysummary** | Creates a dated summary of the day's work with cross-references |
| **/weeklysummary** | Aggregates daily summaries into weekly workstream reports |
| **/commit** | Analyzes staged changes and creates logical separate commits |

### Content Layer
| Command | What it does |
|---------|-------------|
| **/quarto** | Generates Quarto RevealJS slide decks from background documents |
| **/pdftotxt** | Extracts text from PDF, Word, and HTML files — supports single files or directories |

---

## Evidence

See [EVIDENCE.md](EVIDENCE.md) for full methodology and metrics.

---

## Citation

If you use or build on this toolkit, please cite:

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

See [DESIGN.md](DESIGN.md) for the full tradeoff log and v2+ backlog.
