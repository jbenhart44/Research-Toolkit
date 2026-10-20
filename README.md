# Research Amp Toolkit

[![tests](https://github.com/jbenhart44/Research-Toolkit/actions/workflows/tests.yml/badge.svg)](https://github.com/jbenhart44/Research-Toolkit/actions/workflows/tests.yml)

**Verification-first agent engineering for Claude Code: plans that are critiqued before they are built, guards that have been watched failing, and claims that resolve to a file.**

> *Every empirical value cites a file on disk. Every claim survives `grep`. Dissertation-grade, not vibe-grade.*

24 Claude Code commands that amplify your work. The tools don't think — they verify, structure, and document. You bring the signal.

> **Status: v2.0.** Maintained by one author; issues and pull requests are answered best-effort. Every push runs the test suite in CI on Linux and macOS.

**Author:** Jake Benhart (NC State University — Operations Research) · `/pcv` (Plan-Construct-Verify) is the work of Dr. Michael G. Kay, bundled unmodified · Contact: jebenhar@ncsu.edu · [jbenhart44.github.io](https://jbenhart44.github.io)

**Links:** [Landing page](https://jbenhart44.github.io/toolkit/) · [Download v2.2.0](https://github.com/jbenhart44/Research-Toolkit/releases/tag/v2.2.0) · [Report an issue](https://github.com/jbenhart44/Research-Toolkit/issues) · [Discussions](https://github.com/jbenhart44/Research-Toolkit/discussions) · [Contribute](CONTRIBUTING.md)

Design rationale: [DESIGN.md](DESIGN.md). Who this is for and not for: [POSITIONING.md](POSITIONING.md). Error classes the toolkit is built to prevent: [references/preventable_errors.md](references/preventable_errors.md). Consolidated rule index: [references/iron_rules.md](references/iron_rules.md).

## How the toolkit checks itself

The toolkit holds its own release to the standard it asks of your work. The gates below run in CI on every push, and each is proven by a mutation check: a copy of the gate with a defect planted in it must turn its own self-test red.

| Gate | What it refuses | Proof |
|---|---|---|
| `tests/check_toolkit.py` | a command without its contract (frontmatter, "When to use"), an absolute home path, a credential, an email outside the allowlist, and any term in your own private-token file (`~/.claude/toolkit-private-tokens.txt`: project names, course codes, folders that must never ship) | `tests/check_toolkit_mutations.py` |
| `tests/check_claims.py` | a count or version on any page that disagrees with `install.sh` and `VERSION` | `tests/check_claims_mutations.py` |
| `tests/check_install.py` | an install, in any mode, that leaves out a file a command calls, a skill or a council seat; a backup left inside `~/.claude/skills/`; a command that calls a path existing only in a clone; a re-install that changes your config | `tests/check_install_mutations.py` |
| `tests/check_models.py` | a command that starts an agent without naming its model, or names one the role table does not give that role; a pinned model ID; a role table, generated table or failure block out of step with `shared/model-roles.json` | `tests/check_models_mutations.py` |
| `hooks/usage_counter.py` | (a hook, not a gate) a usage counter that drops a call or breaks a session | `hooks/usage_counter_mutations.py` |
| `scripts/emit_run_report.py` | (a helper, not a gate) a run report or `run_log.csv` row that is malformed or never written | `scripts/emit_run_report_mutations.py` |
| `hooks/<hook>_selftest.py` | (hooks, not gates) each optional hook letting through the shape it exists to catch, or blocking a legitimate lookalike | `hooks/<hook>_mutations.py` |
| `scripts/check_*.py`, `scripts/register_hooks.py` | (tools you run) a missed collision, leak or unresolved path, or a registration block that is wrong | `scripts/<script>_mutations.py` |
| `shared/skills/<skill>/assets/*_selftest.py` | (skills) the `/guard-hook` and `/bulletproof` runners reporting a guard or a suite as proven when it is not; the `/list-maker` ledger reusing a number or hiding a deferred item; `/step-by-step` calling an unfinished walkthrough done | `shared/skills/<skill>/assets/*_mutations.py` |

```bash
python3 tests/check_toolkit.py && python3 tests/check_claims.py && python3 tests/check_install.py && python3 tests/check_models.py    # the gates
python3 tests/check_toolkit_mutations.py && python3 tests/check_claims_mutations.py && python3 tests/check_install_mutations.py && python3 tests/check_models_mutations.py
python3 hooks/usage_counter_mutations.py && python3 scripts/emit_run_report_mutations.py
for m in hooks/*_mutations.py scripts/*_mutations.py shared/skills/*/assets/*_mutations.py; do python3 "$m" || echo "FAILED: $m"; done
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

2. **Your project state vanishes when you close the terminal.** `/startup` shows where every workstream left off. `/daily-summary` captures today's work. `/weekly-summary` aggregates by work area. `/commit` makes clean git history. `/run-log` shows longitudinal patterns across commands over weeks.

3. **You need help without burning tokens.** `/readable` extracts PDF text so you can grep-cite. `/quarto` builds slide decks from your notes. `/improve` scans infrastructure gaps. `/simplify` cleans up working code.

**How to use**: Install once (`bash install.sh`), run `/setup` to answer a few questions about your project, then run `/startup` to begin. Each command tells you what it does and when to use it.

> **Skills are patterns to adapt, not install blindly.** If a command doesn't fit your workflow, modify its prompt file or skip it — the toolkit is designed to be forked per-user, not black-boxed.

---

## Quick Start

```bash
git clone https://github.com/jbenhart44/Research-Toolkit.git
cd Research-Toolkit
git checkout v2.2.0
bash install.sh            # add --hooks for the optional hooks, including the usage counter
```

Upgrading from an earlier version? Re-run `install.sh` from the new checkout. Before v2.0.2 the installer did not copy the run-report helper, so commands wrote no run reports; a re-install fixes that. From v2.1.0, also run `/setup` once: the installer never overwrites your config, so the account question is new to you, and until you answer it the `/coa` Chair requests Sonnet. From v2.2.0:
- **Three commands are renamed**: `/dailysummary` is `/daily-summary`, `/weekly-summary` replaces `/weeklysummary`, and `/run-log` replaces `/runlog`. For this release the old names stay installed as one-line pointers that tell you the new name; they go in the next release.
- **Run `/setup` again** so it writes `model_transcriber` (page transcription runs on Haiku, with two readers, on smaller plans).
- The installer copies five `/coa` seat agents to `~/.claude/agents/` (a file of the same name is backed up first, as `<name>.md.bak`), plus three add-on seats with `--addon-seats`, and puts skill backups in `~/.claude/toolkit-backups/`, not in `~/.claude/skills/`.
- The full install adds `/acquire` and seven skills (`/quick-ten`, `/guard-hook`, `/bulletproof`, `/list-maker`, `/step-by-step`, `/automate`, `/meeting-breakdown`), and every install copies `acquire.py` and `check_transcription.py` to `~/.claude/toolkit/scripts/`.
- `--hooks` copies four hooks and registers none. The token-budget and summary-folder hooks you may have registered are Python behind the same `.sh` names, so a registration keeps working.
- Two new tools stay in the clone for you to run: `scripts/agent_stalls.py` (a ledger of subagent stalls) and `scripts/headless_agent.py` (a stalled agent's prompt rerun as a restricted headless session).

Then in Claude Code:

1. **`/setup`** — a two-minute interview that writes `~/.claude/toolkit-config.md`: your project name, workstreams, folders, and which Claude account you use (see [Which model runs each agent](#which-model-runs-each-agent)). Every command reads that file instead of hard-coded paths; a command that needs a value you have not given asks once and offers to save it.
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
| **/acquire** | Downloads a paper or a manifest of papers, refuses HTML and wrong-DOI downloads, extracts the text with a density gate, and grep-checks every claimed figure before anything cites it. **Needs** `pypdf` or `PyMuPDF` (`pip install pypdf PyMuPDF`) to read a PDF |
| **/improve** | Self-reflective meta-agent that audits your Claude Code infrastructure and proposes improvements |
| **/simplify** | Reviews code or documents for redundancy, complexity, and performance issues |
| **/bulletproof** | Puts tests behind new functionality, written first, then proves them by planting the defect each guard exists to prevent and watching named checks go red. A skill; installed by the full install |
| **/guard-hook** | Builds a Claude Code hook guard whose self-test has been watched failing against a neutered copy of itself, and audits installed hooks for six known traps. **Useful only if you use Claude Code hooks.** A skill; installed by the full install |

### Workflow Layer
| Command | What it does |
|---------|-------------|
| **/startup** | Reads recent work summaries and orients you on where you left off |
| **/daily-summary** | Creates a dated summary of the day's work with cross-references |
| **/weekly-summary** | Aggregates daily summaries into weekly workstream reports |
| **/commit** | Analyzes changes and creates logical separate commits, refusing to mix workstreams without your say-so |
| **/run-log** | Renders a longitudinal table of recent toolkit runs — convergence, tokens, outcomes — from local CSVs |
| **/meeting-breakdown** | Breaks a meeting transcript into a per-domain plan (decisions, next steps, deferrals in each domain) with a five-agent PACE-style run. A skill; installed by the full install |
| **/list-maker** | Turns a transcript into a numbered, tiered work list whose numbers never change, so "we're on number 14" still means the same item next month. A skill; installed by the full install |
| **/step-by-step** | One item at a time: walks a git-derived list of what a session changed and refuses to call the walkthrough done while an item is unexplained, or works a `/list-maker` list one item per turn. A skill; installed by the full install |

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
| **/quick-ten** | Before a substantial build: asks only the questions (at most ten) whose answers change what gets built, shows a recap, and writes a short brief the build follows. A skill; installed by the full install |
| **/automate** | Turns a task you just finished into a skill: the deterministic steps become a tested script, the judgment steps stay prose, and the skill is shown to reproduce the original result. A skill; installed by the full install |

### Which model runs each agent

Of the 24 commands, nine start subagents (the six in v2.1.0, `/quick-ten` when it convenes a council, `/acquire` when a PDF is a scanned image, and `/meeting-breakdown`). Each one names the model it requests on the call itself, instead of inheriting your session's model, and `tests/check_models.py` fails the build if one does not. The table is `shared/model-roles.json`; this copy is generated from it.

<!-- BEGIN GENERATED: role-table -->
| Role | Where it runs | `pro`, `team-standard`, `unknown` | `max5x`, `max20x`, `team-premium`, `enterprise`, `api`, `cloud` |
|---|---|---|---|
| `reasoner` | /coa: members, cross-check, rebuttal · /pace: player-a, player-b, coach-c, coach-d, cross-reviewer, revision-reviewer · /review: lenses · /quick-ten: council · /meeting-breakdown: player-a, player-b, coach-c, coach-d, cross-reviewer | sonnet | sonnet |
| `chair` | /coa: chair | sonnet | opus (`model_chair`) |
| `writer` | /daily-summary: writer · /weekly-summary: writer | sonnet | sonnet |
| `transcriber` | /readable: transcriber · /acquire: transcriber | haiku | sonnet (`model_transcriber`) |
<!-- END GENERATED: role-table -->

The columns are the account `/setup` records. They are the toolkit's cost policy, not a claim about which models an account can use: two roles change. The `/coa` Chair requests Opus where the account's allowance makes the cost reasonable and `/model` lists it. The page transcriber requests Haiku on smaller plans, where two readers transcribe and `scripts/check_transcription.py` refuses the result unless they agree on every number. Smaller plans also get a smaller default `/coa` council (three seats) and a lighter `/meeting-breakdown` (one Player and one Coach). Haiku has to pass the admission test in [references/model-roles.md](references/model-roles.md) for any other role. That page gives each reason with Anthropic's sources and the date they were read.

> **What the files cannot guarantee.** They name the model each agent *requests*. `CLAUDE_CODE_SUBAGENT_MODEL_FORCE`, an organization's model allowlist, an `ANTHROPIC_API_KEY` in your environment, or an alias that Anthropic moves can each change what actually runs. Run `/tasks` to see the model each agent ran on, and `/model` to see what your account offers.

### Companion tool: captioner

[**captioner**](https://github.com/jbenhart44/captioner) ([landing page](https://jbenhart44.github.io/captioner/)) is a separate Claude Code skill by the same author: it adds a subject-identifying caption under every picture in a PowerPoint deck and can write screen-reader alt-text for images that lack it. It lives in its own repository, which is its source of truth, and installs on its own. It is not counted among the 24 commands above.

---

## Optional: hooks

`bash install.sh --hooks` copies four optional hooks to `~/.claude/hooks/` and **registers none of them**: which guards run in your sessions is your decision, and the installer never edits a settings file. `python3 scripts/register_hooks.py --list` shows them; `python3 scripts/register_hooks.py protect_files` prints the `settings.json` block for the ones you choose, to paste in yourself.

| Hook | What it does | Posture |
|---|---|---|
| `usage_counter` | records one row per command use in `<evidence_dir>/usage_events.csv`; `python3 scripts/usage_counts.py` reports the counts | silent |
| `token_budget_guard` | estimates a session's agent tokens and asks before an Agent call once the estimate passes your limit | asks |
| `summary_folder_guard` | notes a dated summary written outside your summary folders | notes |
| `protect_files` | blocks a write to one of your `protected_files`; reading stays allowed | blocks, if set |

**`protect_files` holds no list of its own.** It reads its list from `~/.claude/toolkit-config.md`, and with none it allows everything. Every hook has a self-test and a mutation check in `hooks/`, and states what it cannot see; see `hooks/README.md`.

## Optional: Proactive Suggestion Fragment

A declarative CLAUDE.md fragment is bundled at `shared/proactive_fragment.md`, with one rule per command. It tells Claude *when* to proactively suggest each command at the moment a user is about to take an action that the command would improve.

**Default-OFF.** The installer does NOT modify your CLAUDE.md. To activate, manually add ONE `@import` line — `bash install.sh` prints the exact line for your installation.

**Why declarative, not runtime?** A runtime, always-on suggestion agent is a hub-spoke router: it adds a coordination step, and its cost, to every turn. Static rules give the same suggestions with no router, no observer and no per-turn cost. A runtime variant is gated behind a falsifiable pilot test; see the pilot-gate spec at the bottom of `shared/proactive_fragment.md`.

**Drift detection**: `bash scripts/audit_pcv_trigger_sync.sh` performs a 4-check structural sync between the bundled `pcv/skill/SKILL.md` and the fragment's `/pcv` row. Exits 0 (clean), 1 (drift detected, with `--fix-list` for actionable items), or 2 (file missing). Run after upstream toolkit refreshes.

---

## Directory Reference

| Path | What it holds |
|---|---|
| `shared/commands/` | 16 slash command definitions (one per command); the skills and `/pcv` make up the rest of the count |
| `shared/skills/` | Skills, installed to `~/.claude/skills/` by the full install: `/quick-ten`, `/guard-hook`, `/bulletproof`, `/list-maker`, `/step-by-step`, `/automate`, `/meeting-breakdown` (each skill's self-test and mutation check stay in the clone) |
| `coa/agents/` | The `/coa` council seats, installed to `~/.claude/agents/` by every install: `coa-skeptic`, `coa-practitioner`, `coa-economist`, `coa-advocate`, `coa-end-user`. `coa/agents/addon/` holds three add-on seats that `bash install.sh --addon-seats` adds: `coa-historian`, `coa-editor`, `coa-paper-reviewer`. Each holds its seat's lens, so `/coa` sends it only the question; a seat for your own field is a persona file in `coa/personas/` |
| `scripts/` | Helpers called by commands (`emit_run_report.py` for run reports, `check_coa_evidence_paths.py` for `/coa` briefs, `acquire.py` for `/acquire`), tools you run yourself (`usage_counts.py`, `register_hooks.py`, `check_heading_collisions.py`, `check_scratchpad_leak.py`, `agent_stalls.py`, `headless_agent.py`) — see `scripts/README.md` |
| `tests/` | The release gates and their mutation checks; `tests/smoke/` holds fixtures for each command — see `tests/README.md` |
| `references/` | JIT recipe files — workflows that are documents, not commands (e.g., `processing_student_submissions.md`, `model-roles.md`) |
| `instructor/guides/` | Teaching guides for instructors using the toolkit in a classroom |
| `student/` | `bootstrap.md`, an in-session installer: give it to Claude Code and it copies the toolkit with the Read and Write tools, no shell needed |
| `hooks/` | The four optional hooks (a `.sh` launcher and a `.py` each), `_toolkit_config.py` which they share, and every hook's self-test and mutation check — see `hooks/README.md` |
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
  version = {2.2.0},
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
