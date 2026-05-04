# Research Amp Toolkit

> **⚠️ v0.1 — experimental, no support commitment.** This is an early research release under active development. Breaking changes expected between versions. Issues and pull requests are welcome; responses are best-effort, not guaranteed. If you're looking for a stable production tool, this isn't it yet.

15 Claude Code commands that amplify your research. The tools don't think — they verify, structure, and document. You bring the signal. Validated across hundreds of production sessions.

**Authors:** Jake Benhart & Dr. Michael G. Kay (NC State University — Operations Research)

**Links:** [Landing page](https://jbenhart44.github.io/Research-Toolkit/) · [Download v0.1](https://github.com/jbenhart44/Research-Toolkit/releases) · [Report an issue](https://github.com/jbenhart44/Research-Toolkit/issues) · [Discussions](https://github.com/jbenhart44/Research-Toolkit/discussions) · [Contribute](CONTRIBUTING.md)

Design rationale documented in [DESIGN.md](DESIGN.md).

## Spec-Driven Development

This toolkit is a working implementation of **Spec-Driven Development (SDD)** — the practice of writing the plan, constructing against it, and verifying the result as three separate, auditable steps rather than one conflated "just ask the model" loop. The commands here (`/pcv`, `/pace`, `/audit`, `/readable`, `/coa`) predate the SDD label; they grew out of PhD-research needs where a wrong citation or a hallucinated number is a career cost, not a minor bug. The SDD label is retroactive — the pattern became visible when the broader AI-engineering conversation converged on the same decomposition (peer implementations include GitHub's SpecKit, Obra's Superpowers, and the `agents.md` convention). For the full diagram, per-command narrative, and command-to-stage mapping, see the [landing page](https://jbenhart44.github.io/Research-Toolkit/). This README covers install, the command catalog, and contribution guidelines.

**Design tenet — Text-first architecture.** Every toolkit artifact is plain text (Markdown commands, YAML frontmatter, bash helpers, bundled `.md` protocols). No binary formats in the authoring path. This is not aesthetic — it's what makes Claude Code a first-class participant in the workflow, what makes git history meaningful, and what lets reviewers read artifacts without specialized tools. Per Dr. Kay (2026): *"transparency is structural rather than procedural."* The text-first constraint is what enforces that structural transparency.

---

## Topology

Different problem shapes call for different topologies, and this toolkit bundles commands of two kinds. Hub-spoke commands (Chair-coordinated panels via `/coa`, `/pace`, `/review`) are right for decomposable work where synthesis benefits from orchestrated coherence. Market-shaped commands (`/coa --quick`'s 3-member panel) are right for brittle reasoning where independent retry beats hand-coordinated convergence. Global-state work (refactors, lockfiles, sync edits) stays solo — no agents at all. The choice is task-shape-dependent. See [DESIGN.md](DESIGN.md) `### Topology Selection` for the full taxonomy.

---

## What This Gives You

Reusable Claude Code commands that turn vague "help me with my research" prompts into structured, verifiable workflows. Three problems they solve:

1. **You don't know if the AI's numbers and citations are right.** `/audit` grep-verifies every cited figure against source papers on disk. `/pace` runs two agents in parallel so errors surface as disagreements. `/coa` spawns a panel of experts with different professional lenses.

2. **Your project state vanishes when you close the terminal.** `/startup` shows where every workstream left off. `/dailysummary` captures today's work. `/weeklysummary` aggregates by work area. `/commit` makes clean git history. `/runlog` shows longitudinal patterns across commands over weeks.

3. **You need help without burning tokens.** `/readable` extracts PDF text so you can grep-cite. `/quarto` builds slide decks from your notes. `/improve` scans infrastructure gaps. `/simplify` cleans up working code.

**How to use**: Install once (`bash install.sh`), edit `~/.claude/toolkit-config.md` with your project name and folders, run `/startup` to begin. Each command tells you what it does and when to use it.

> **Skills are patterns to adapt, not install blindly.** (Panjwani 2025, VoxDev AI-Agents-for-Economics-Research.) If a command doesn't fit your workflow, modify its prompt file or skip it — the toolkit is designed to be forked per-user, not black-boxed.

---

## Quick Start

```bash
git clone https://github.com/jbenhart44/Research-Toolkit.git
cd Research-Toolkit
bash install.sh
```

Then in Claude Code: type `/pcv` in any project directory to verify it works.

**Verify your install** (30 seconds):
```bash
cd tests/smoke/
/audit paper.md --sources sources/
# Expected: 1 VERIFIED + 1 MISMATCH + 1 NOT FOUND (1 fabricated citation flagged)
```

If the expected output matches, your install is working. See `tests/README.md` for more fixtures.

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
| **/coa** | Council of Agents — multi-perspective decision support. Use `--quick` for fast/brittle questions (market-shaped); default for synthesis-heavy reviews (hub-spoke). |
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
| **/runlog** | Renders longitudinal table of recent toolkit runs — convergence, tokens, outcomes — from local CSVs. PLN-verifiable observability (NEW in v1.1). |

### Content Layer
| Command | What it does |
|---------|-------------|
| **/quarto** | Generates Quarto RevealJS slide decks from background documents |
| **/readable** | Extracts text from PDF, Word, and HTML files — supports single files or directories |

### Triage Layer
| Command | What it does |
|---------|-------------|
| **/help** | Socratic triage — describe your situation in one line, get 1-3 command recommendations. Traffic cop, not driver. **EXPERIMENTAL (v0.2, 2026-04-19)** — success pending end-of-fall evaluation; see smoke fixture at `tests/smoke/help_triage.md`. |

---

## Directory Reference

| Path | What it holds |
|---|---|
| `shared/commands/` | 14 slash command definitions (one per command); `/pcv` is the 15th, invoked via skills registry from `pcv/agents/` |
| `scripts/` | Shared bash helpers called by commands (e.g., `emit_run_report.sh` for run instrumentation) — see `scripts/README.md` |
| `tests/smoke/` | Fixtures verifying each command works as documented — see `tests/README.md` |
| `references/` | JIT recipe files — workflows that are documents, not commands (e.g., `processing_student_submissions.md`) |
| `instructor/guides/` | Teaching guides for instructors using the toolkit in a classroom |
| `student/` | Student-specific bootstrap (auto-run at install time on student machines) |
| `hooks/` | Optional Claude Code hooks (SessionStart, PreToolUse, etc.) |
| `pcv/` | Kay's PCV v3.14 upstream (bundled for zero-dependency install; refresh via `scripts/refresh-pcv-bundle.sh`) |

---

## Evidence

See [EVIDENCE.md](EVIDENCE.md) for full methodology and metrics.

---

## Citation

If you use or build on this toolkit, please cite:

```bibtex
@software{benhart_kay2026researchamp,
  author = {Benhart, Jake and Kay, Michael G.},
  title = {Research Amp Toolkit: Amplification Commands for AI-Assisted Research with Claude Code},
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
