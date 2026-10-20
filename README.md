# Research Amp Toolkit

[![tests](https://github.com/jbenhart44/Research-Toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/jbenhart44/Research-Toolkit/actions/workflows/tests.yml)

**Verification-first agent engineering for Claude Code: plans that are critiqued before they are built, guards that have been watched failing, and claims that resolve to a file.**

> *Every empirical value cites a file on disk. Every claim survives `grep`. Dissertation-grade, not vibe-grade.*

16 Claude Code commands that amplify your work. The tools don't think — they verify, structure, and document. You bring the signal.

> **Status: v2.0.** Maintained by one author; issues and pull requests are answered best-effort. Every push runs the test suite in CI on Linux and macOS.

**Author:** Jake Benhart (NC State University — Operations Research) · `/pcv` (Plan-Construct-Verify) is the work of Dr. Michael G. Kay, bundled unmodified · Contact: jebenhar@ncsu.edu · [jbenhart44.github.io](https://jbenhart44.github.io)

**Links:** [Landing page](https://jbenhart44.github.io/toolkit/) · [Download v2.0.1](https://github.com/jbenhart44/Research-Toolkit/releases/tag/v2.0.1) · [Report an issue](https://github.com/jbenhart44/Research-Toolkit/issues) · [Discussions](https://github.com/jbenhart44/Research-Toolkit/discussions) · [Contribute](CONTRIBUTING.md)

Design rationale: [DESIGN.md](DESIGN.md). Who this is for and not for: [POSITIONING.md](POSITIONING.md). Error classes the toolkit is built to prevent: [references/preventable_errors.md](references/preventable_errors.md). Consolidated rule index: [references/iron_rules.md](references/iron_rules.md).

## How the toolkit checks itself

The toolkit holds its own release to the standard it asks of your work. Three gates run in CI on every push, and each is proven by a mutation check: a copy of the gate with a defect planted in it must turn its own self-test red.

| Gate | What it refuses | Proof |
|---|---|---|
| `tests/check_toolkit.py` | a command without its contract (frontmatter, "When to use"), an absolute home path, a credential, an email outside the allowlist, and any term in your own private-token file (`~/.claude/toolkit-private-tokens.txt`: project names, course codes, folders that must never ship) | `tests/check_toolkit_mutations.py` |
| `tests/check_claims.py` | a count or version on any page that disagrees with `install.sh` and `VERSION` | `tests/check_claims_mutations.py` |
| `hooks/usage_counter.py` | (a hook, not a gate) a usage counter that drops a call or breaks a session | `hooks/usage_counter_mutations.py` |

```bash
python3 tests/check_toolkit.py && python3 tests/check_claims.py          # the gates
python3 tests/check_toolkit_mutations.py && python3 tests/check_claims_mutations.py && python3 hooks/usage_counter_mutations.py
```

## Spec-Driven Development

This toolkit is a working implementation of **Spec-Driven Development (SDD)** — the practice of writing the plan, constructing against it, and verifying the result as three separate, auditable steps rather than one conflated "just ask the model" loop. The commands here (`/pcv`, `/pace`, `/audit`, `/readable`, `/coa`) predate the SDD label; they grew out of research needs where a wrong citation or a hallucinated number is a career cost, not a minor bug. The SDD label is retroactive — the pattern became visible when the broader AI-engineering conversation converged on the same decomposition (peer implementations include GitHub's SpecKit, Obra's Superpowers, and the `agents.md` convention). For the full diagram, per-command narrative, and command-to-stage mapping, see the [landing page](https://jbenhart44.github.io/toolkit/). This README covers install, the command catalog, and contribution guidelines.

**Design tenet — Text-first architecture.** Every toolkit artifact is plain text (Markdown commands, YAML frontmatter, small helper scripts, bundled `.md` protocols). No binary formats in the authoring path. This is not aesthetic — it's what makes Claude Code a first-class participant in the workflow, what makes git history meaningful, and what lets reviewers read artifacts without specialized tools. Per Dr. Kay (2026): *"transparency is structural rather than procedural."* The text-first constraint is what enforces that structural transparency.

---

## Topology

Different problem shapes call for different topologies, and this toolkit bundles commands of two kinds. Hub-spoke commands (Chair-coordinated panels via `/coa`, `/pace`, `/review`) are right for decomposable work where synthesis benefits from orchestrated coherence. Market-shaped commands (`/coa --quick`'s 3-member panel) are right for brittle reasoning where independent retry beats hand-coordinated convergence. Global-state work (refactors, lockfiles, sync edits) stays solo — no agents at all. The choice is task-shape-dependent. See [DESIGN.md](DESIGN.md) `### Topology Selection` for the full taxonomy.

---

## What This Gives You

Reusable Claude Code commands that turn vague "help me with my research" prompts into structured, verifiable workflows. Three problems they solve:

1. **You don't know if the AI's numbers and citations are right.** `/audit` grep-verifies every cited figure against source papers on disk. `/pace` runs two agents in parallel so errors surface as disagreements. `/coa` spawns a panel of experts with different professional lenses.

2. **Your project state vanishes when you close the terminal.** `/startup` shows where every workstream left off. `/dailysummary` captures today's work. `/weeklysummary` aggregates by work area. `/commit` makes clean git history. `/runlog` shows longitudinal patterns across commands over weeks.

3. **You need help without burning tokens.** `/readable` extracts PDF text so you can grep-cite. `/quarto` builds slide decks from your notes. `/improve` scans infrastructure gaps. `/simplify` cleans up working code.

**How to use**: Install once (`bash install.sh`), run `/setup` to answer a few questions about your project, then run `/startup` to begin. Each command tells you what it does and when to use it.

> **Skills are patterns to adapt, not install blindly.** If a command doesn't fit your workflow, modify its prompt file or skip it — the toolkit is designed to be forked per-user, not black-boxed.

---

## Quick Start

```bash
git clone https://github.com/jbenhart44/Research-Toolkit.git
cd Research-Toolkit
git checkout v2.0.1
bash install.sh            # add --hooks for the optional hooks, including the usage counter
```

Then in Claude Code:

1. **`/setup`** — a two-minute interview that writes `~/.claude/toolkit-config.md`: your project name, workstreams and folders. Every command reads that file instead of hard-coded paths; a command that needs a value you have not given asks once and offers to save it.
2. **`/startup`** — orients you on where each workstream left off.

**Verify your install** (30 seconds):
```bash
cd tests/smoke/
/audit paper.md --sources sources/
# Expected: 1 VERIFIED + 1 MISMATCH + 1 NOT FOUND (1 fabricated citation flagged)
```

If the expected output matches, your install is working. See `tests/README.md` for more fixtures.

**Optional but recommended — cross-model verification for /coa.** `/coa` runs a same-family council by default. Adding a single Gemini cross-check (free, ~2 min) gives you genuine cross-vendor disagreement detection. See [`coa/CROSSMODEL_SETUP.md`](coa/CROSSMODEL_SETUP.md) for the step-by-step — or paste the "TL;DR" prompt at the top of that file into a Claude Code session and let it walk you through the install interactively (you only need to supply the API key when asked). Skip entirely if you don't want it; `/coa` runs cleanly without it (same-model caveat noted in the synthesis).

---

## Commands

### Setup
| Command | What it does |
|---------|-------------|
| **/setup** | One-time interview that writes `~/.claude/toolkit-config.md`, the file every other command reads for project-specific values |

### Verification Layer
| Command | What it does |
|---------|-------------|
| **/pcv** | Plan-Construct-Verify — structured planning with clarification, adversarial review, and human approval gates (by Dr. Michael G. Kay) |
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
| **/commit** | Analyzes changes and creates logical separate commits, refusing to mix workstreams without your say-so |
| **/runlog** | Renders a longitudinal table of recent toolkit runs — convergence, tokens, outcomes — from local CSVs |

### Content Layer
| Command | What it does |
|---------|-------------|
| **/quarto** | Generates Quarto RevealJS slide decks from background documents |
| **/readable** | Extracts text from PDF, Word, and HTML files — supports single files or directories |
| **/review** | Reads a document through three expert lenses in parallel and synthesizes the takeaways |

### Triage Layer
| Command | What it does |
|---------|-------------|
| **/help** | Socratic triage — describe your situation in one line, get 1-3 command recommendations. Traffic cop, not driver. **EXPERIMENTAL** — see the smoke fixture at `tests/smoke/help_triage.md`. |

### Companion tool: captioner

[**captioner**](https://github.com/jbenhart44/captioner) ([landing page](https://jbenhart44.github.io/captioner/)) is a separate Claude Code skill by the same author: it adds a subject-identifying caption under every picture in a PowerPoint deck and can write screen-reader alt-text for images that lack it. It lives in its own repository, which is its source of truth, and installs on its own. It is not counted among the 16 commands above.

---

## Optional: usage counter (hook)

`bash install.sh --hooks` installs `hooks/usage_counter.py`, which records one row per command use (skill call or typed `/command`) in `<evidence_dir>/usage_events.csv`. It never blocks and never prints. `python3 scripts/usage_counts.py` turns the log into per-command counts; a typed command that Claude then runs counts once. Registration lines are in `hooks/README.md`.

## Optional: Proactive Suggestion Fragment

A declarative CLAUDE.md fragment is bundled at `shared/proactive_fragment.md`, with one rule per command. It tells Claude *when* to proactively suggest each command at the moment a user is about to take an action that the command would improve.

**Default-OFF.** The installer does NOT modify your CLAUDE.md. To activate, manually add ONE `@import` line — `bash install.sh` prints the exact line for your installation.

**Why declarative, not runtime?** A runtime, always-on suggestion agent is a hub-spoke router: it adds a coordination step, and its cost, to every turn. Static rules give the same suggestions with no router, no observer and no per-turn cost. A runtime variant is gated behind a falsifiable pilot test; see the pilot-gate spec at the bottom of `shared/proactive_fragment.md`.

**Drift detection**: `bash scripts/audit_pcv_trigger_sync.sh` performs a 4-check structural sync between the bundled `pcv/skill/SKILL.md` and the fragment's `/pcv` row. Exits 0 (clean), 1 (drift detected, with `--fix-list` for actionable items), or 2 (file missing). Run after upstream toolkit refreshes.

---

## Directory Reference

| Path | What it holds |
|---|---|
| `shared/commands/` | 15 slash command definitions (one per command); `/pcv` is the 16th, installed as a skill from `pcv/` |
| `scripts/` | Helpers called by commands (e.g. `emit_run_report.sh` for run instrumentation, `usage_counts.py`) — see `scripts/README.md` |
| `tests/` | The release gates and their mutation checks; `tests/smoke/` holds fixtures for each command — see `tests/README.md` |
| `references/` | JIT recipe files — workflows that are documents, not commands (e.g., `processing_student_submissions.md`) |
| `instructor/guides/` | Teaching guides for instructors using the toolkit in a classroom |
| `student/` | `bootstrap.md`, an in-session installer: give it to Claude Code and it copies the toolkit with the Read and Write tools, no shell needed |
| `hooks/` | Optional Claude Code hooks: usage counter, token budget, summary-folder guard |
| `pcv/` | Dr. Kay's PCV v3.14 upstream (bundled for zero-dependency install; refresh via `scripts/refresh-pcv-bundle.sh`) |
| `shared/proactive_fragment.md` | Optional declarative CLAUDE.md fragment with per-command proactive-suggestion rules. Default-OFF; opt-in via `@import`. |

---

## Evidence

See [EVIDENCE.md](EVIDENCE.md) for methodology and what each claim rests on.

---

## Citation

If you use or build on this toolkit, please cite:

```bibtex
@software{benhart2026researchamp,
  author  = {Benhart, Jake},
  title   = {Research Amp Toolkit: Verification-First Commands for AI-Assisted Research with Claude Code},
  year    = {2026},
  version = {2.0.1},
  url     = {https://github.com/jbenhart44/Research-Toolkit},
  note    = {Bundles PCV (Plan-Construct-Verify) by Michael G. Kay}
}
```

See [CITATION.md](CITATION.md) for full attribution details.

---

## License

MIT License. See [LICENSE](LICENSE).

---

## Roadmap

See [DESIGN.md](DESIGN.md) for the full tradeoff log and backlog.
