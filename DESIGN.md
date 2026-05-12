# Design Rationale — Research Amp Toolkit

**Version:** 1.4
**Date:** 2026-04-19 (v1.4 adds `/review` command + PCV v3.14 bundle bump; see changelog at bottom)
**Authors:** Jake Benhart & Michael G. Kay

This document records every significant design decision in the toolkit: what was chosen, what was rejected, and why. It serves as the authoritative reference when evaluating proposed additions or changes.

---

## Core Principle: Simplest Model That Works

This toolkit applies Occam's razor to AI-assisted research workflows:

> **Include the minimum set of commands that covers the three gaps (verification, planning, documentation). Reject any addition that duplicates existing capability, requires untested infrastructure, or increases the install surface without proportional value.**

The test for inclusion is: *Would a PhD student doing computational research use this command at least weekly?* If not, it's either a v2+ candidate or a teaching guide topic — not a command.

### What "Simplest" Means in Practice

- **One command per function.** If `/pace` already does grading verification, we don't add `/grading-rubric`. If `/improve` already audits infrastructure, we don't add `/research-audit`.
- **Same commands for all users.** Student and instructor toolkits differ in *which* commands are installed, not in command behavior. Context comes from teaching guides, not per-persona command variants.
- **Configuration over code.** Project-specific behavior lives in `toolkit-config.md`, not in command logic. Commands read the config; they don't branch on audience type.
- **Guides over tools for policy.** PII handling, academic integrity, and IRB compliance are policy decisions — they belong in teaching guides with stern notes, not in commands that give false confidence.

---

## Command Inventory (v1.0)

### Why 15 Commands

The toolkit started with 15 commands built during PhD research. Assessment:

| Tier | Commands | Disposition |
|------|----------|-------------|
| **Tier 1 — Showcase** | /pcv, /coa, /pace, /improve, /simplify | Core methodology — included |
| **Tier 2 — Workflow** | /startup, /dailysummary, /weeklysummary, /commit, /runlog | Daily-use productivity — included |
| **Tier 3 — Content** | /quarto, /readable | Document generation — included |
| **Tier 4 — Triage** | /help | Discoverability triage — added v1.3 |
| **Tier 5 — Verification** | /audit, /review | Citation + document review — added v1.0 (audit) / v1.4 (review) |
| **Excluded** | 4 domain-specific commands | Not generalizable beyond the original research context |

15 user-visible commands = 14 command files in `shared/commands/` (one .md per slash-command) + `/pcv` registered via the skills registry. Growth history: /audit added 2026-04-03 after catching 4 numerical mismatches on a dissertation poster (citation verification became non-negotiable); /runlog added v1.1 for longitudinal observability; /help added v1.3 on 2026-04-19 for the paradox-of-choice problem Kay flagged in the 4/15 transcript (line 1304 Brett "traffic cop route"); /review added v1.4 for three-lens document reading. A research instrument (/pcv-research) was previously bundled but was removed on 2026-04-10 after empirical testing revealed its hierarchical subagent spawning architecture is incompatible with Claude Code's tool model; it is held back pending further redesign and is no longer shipped.

### Persona-Command Mapping

| Command | Instructor (`--minimal`) | Student (full) | Layer |
|---------|:---:|:---:|---|
| /pcv | Yes | Yes | Verification |
| /coa | Yes | Yes | Verification |
| /pace | Yes | Yes | Verification |
| /improve | Yes | Yes | Verification |
| /review | Yes | Yes | Verification |
| /help | Yes | Yes | Triage |
| /quarto | Yes | Yes | Content |
| /readable | Yes | Yes | Content |
| /startup | — | Yes | Workflow |
| /dailysummary | — | Yes | Workflow |
| /weeklysummary | — | Yes | Workflow |
| /commit | — | Yes | Workflow |
| /simplify | — | Yes | Workflow |
| /audit | — | Yes | Verification |
| /runlog | — | Yes | Verification |

**Instructor gets 8, student gets 15.** The split logic:
- Instructors need verification tools (teach methodology), the triage entry-point (/help), and content tools (create materials).
- Students also need workflow tools (build research habits: daily documentation, session continuity, clean commits, longitudinal evidence via /runlog).

---

## Tradeoff Log

### Accepted into v1.0

| Decision | Rationale |
|----------|-----------|
| **Bundle PCV v3.14 directly** | Users need it to work immediately. Linking to Kay's repo adds a dependency and version-sync risk. We distribute as-is; improvements go upstream. Refresh cadence managed by `scripts/refresh-pcv-bundle.sh` with `scripts/check-pcv-upstream.sh` drift detection. |
| **Config-file generalization** | Every command that needs project context reads `toolkit-config.md`. Zero hardcoded project paths in any command file. Verified via SC3 grep (Session 1). |
| **Dual installer** | `install.sh` (shell) for terminal users, `bootstrap.md` (Claude Code agent) for in-session install. Two paths to the same result — meets users where they are. |
| **Sonnet recommended, not required** | Academic users have varying model access. Hard Sonnet mandate blocks Haiku-only users. Fallback: "verify numbers manually if Sonnet unavailable." |
| **Teaching guides over command variants** | Three instructor guides (PCV for courses, CoA for discussion, PACE for grading) provide pedagogical context. The commands themselves stay generic. |
| **Inline config examples** | Commented-out examples in `toolkit-config.md` (research project + graduate course) show users what a filled-in config looks like. Lower friction than a separate examples/ directory. |

### Rejected from v1.0 (with reasoning)

| Proposal | Source | Why Rejected | Disposition |
|----------|--------|-------------|-------------|
| `/sanitize` or `/privacy-check` | Gemini | PII scanning is a hard problem. Existing tools (Presidio, detect-secrets) do it better than a command file. A command that misses a student ID is worse than no command — it creates false confidence. | **Policy note in instructor guide.** |
| `/study-breakdown` | Gemini | Turns syllabi into study plans. Requires classroom testing to validate. Zero evidence it works. Premature implementation. | **v2+ backlog.** |
| `/integrity-check` | Gemini | Audits student work against CoV protocol. Interesting concept but undefined scope — what exactly does "integrity" mean algorithmically? Needs design research first. | **v2+ backlog.** |
| `/grading-rubric` | Gemini | Generates feedback from rubric. `/pace` already does this — the `using-pace-for-grading.md` guide teaches exactly this workflow. Redundant. | **Already covered by /pace + guide.** |
| `/research-audit` | Gemini | Verifies TA work followed phase gates. `/improve` already audits infrastructure. Adding a TA-specific wrapper is a "skin command" — same engine, different label. | **Already covered by /improve.** |
| `/cite` or `/bib` | Gemini | BibTeX parsing, DOI resolution, PDF matching — each is a deep rabbit hole. Our citation tier system works because it's enforced by CLAUDE.md rules, not a separate tool. A half-built citation manager is worse than no citation manager. | **v3+ backlog (if ever).** |
| **Per-persona command variants** | Gemini | Student `/coa` vs. instructor `/coa` with different defaults. Doubles the maintenance surface. Commands are generic; context comes from guides and config. | **Rejected permanently.** |
| **NC State theme bundling** | Internal | University brand assets (SCSS, logos) don't belong in a public MIT-licensed repo. Users bring their own themes. | **BYOT (Bring Your Own Theme).** |
| **Project-specific safety hooks** | Internal | Hooks enforcing project-specific rules (protected files, commit policies) are safety nets tied to a particular workflow. Generic users don't have the same protected files. | **Not bundled.** Generic utility hooks (token budget, folder guard) are shipped as optional opt-in via `--hooks` flag. |
| **ECL-lite scorecard system** | Internal | Council session scoring requires infrastructure (scorecard templates, precedent index) that most users don't need. Adds complexity for a niche use case. | **v2+ backlog.** |
| **PRECEDENT_INDEX session tracking** | Internal | Cumulative CoA session history is valuable for longitudinal research but adds file management overhead. Most users run CoA for one-off questions, not multi-session analysis. | **v2+ backlog.** |
| **Per-task-type cost benchmarks** | Internal | Token cost tables from our 14 PCV-Research runs are specific to our charge types and model versions. Publishing them as general guidance would be misleading. | **Removed from generalized /pace.** |

### Design Principles That Drove Rejections

1. **No false confidence.** A tool that claims to do something but does it poorly is worse than no tool. (Applies to: /sanitize, /cite)
2. **No premature implementation.** If we have zero evidence it works, don't ship it. Test first, ship second. (Applies to: /study-breakdown, /integrity-check)
3. **No redundant commands.** If an existing command + a teaching guide covers the use case, don't add a wrapper. (Applies to: /grading-rubric, /research-audit)
4. **No maintenance multiplication.** Per-persona variants double the files to maintain. One command + config + guides is the right architecture. (Applies to: persona variants)
5. **No proprietary assets in public repos.** University branding, project-specific safety nets, and internal infrastructure don't ship. (Applies to: NC State theme, safety hooks, ECL-lite)

---

## What Was Lost in Generalization

Each command was generalized from a project-specific version. Here's what was intentionally removed and why that's acceptable:

| Command | Removed Feature | Why Acceptable |
|---------|----------------|----------------|
| `/coa` | ECL-lite scorecard, PRECEDENT_INDEX, `coa/personas/` paths | Built-in roster fallback works out of the box. Session tracking is v2+. |
| `/pace` | JIT reference gate, per-task cost benchmarks, citation tier verification | Core 4-agent pattern is fully generic. Cost benchmarks were project-specific. |
| `/improve` | Read-only file list (project-specific protected files), `plans/` folder assumptions | Works on any project with a CLAUDE.md. First-time mode added for projects without one. |
| `/startup` | Multi-directory summary scanning, priority rules, MCP monitoring | Config-driven: reads `workstreams` and `summary_folder` from toolkit-config.md. |
| `/dailysummary` | Parameter-specific numerical verification, incident documentation | Generic numerical accuracy check preserved. Sonnet fallback added. |
| `/commit` | Project folder categorization (project-specific folder names) | Uses git diff to infer structure. No hardcoded folder names needed. |
| `/quarto` | NC State theme references | BYOT architecture. Theme is a user-provided SCSS file, not bundled. |
| `/readable` | Hardcoded `/tmp/` path | Cross-platform temp path via Python `tempfile`. |

---

## v2+ Roadmap

Items deferred from v1.0, ordered by estimated value:

### v2 (after classroom testing)

1. **Overlay commands** (`/pcv-class`, `/coa-class`, `/pace-grade`) — PCV structured for course assignments, CoA reframed as discussion prompts, PACE for rubric grading. Requires testing with actual students first.
2. **Session history tracking** — Optional PRECEDENT_INDEX for CoA sessions. Configurable via toolkit-config.md.
3. **Auto-detect workstreams** in `/startup` — Replace manual config with git/folder inference.
4. **ECL-lite scoring** — Council session quality metrics. Useful for longitudinal research.

### v3+ (speculative)

5. **Citation management** (`/cite`) — Only if we can do it well. BibTeX parsing + DOI resolution + PDF matching is a significant engineering effort.
6. **PII scanning** (`/sanitize`) — Only if we can integrate Presidio or equivalent, not a regex hack.
7. **Cross-model council** — CoA with Gemini/GPT members alongside Claude. Currently works via MCP but requires manual setup.
8. **DataFrame integration** — Instrumentation data in Julia/Python DataFrames for richer analysis.
9. **Chair-vs-panelist token-cost telemetry** — Instrument Chair-synthesis vs panelist token consumption per `/coa`, `/pace`, `/review`, `/pcv` run. Motivation: surface hub-spoke coordination overhead empirically. (Inspired by 2026 commentary on agent-coordination cost; deferred until reproducible measurement is in scope.) v0.1 ships without; CSV schema migration deferred to avoid breaking `runlog.csv` contracts. Open question: per-panelist breakdown granularity vs single Chair-vs-rest aggregate.
10. **Generalize `/meetingbreakdown` for toolkit** — Currently user-level only; toolkit counterpart deferred until generalization pattern stabilizes.

### Topology Selection

The toolkit's commands fall into two topological shapes; this table maps task shape to recommended command. This is documented as toolkit-internal best practice based on session experience.

| Task shape | Topology | Recommended command |
|---|---|---|
| Global-state code (refactors, lockfiles, sync edits) | Solo | direct edit, no agents |
| Brittle reasoning (parallelizable, unstable) | Market-shaped | `/coa --quick` |
| Decomposable, coherent synthesis needed | Hub-spoke | `/coa`, `/pace`, `/review`, `/pcv` |

External inspiration: hub-spoke vs market topology distinction echoes a recent advisor-shared analysis (n=15, no seeds — weakly supported); rows above are toolkit-internal best practice, not a citation of that result.

---

## Versioning Policy

- **v1.x** — Bug fixes, documentation improvements, config template updates. No new commands. *D-2 ruling (2026-05-02): "command" means a `.md` file under `shared/commands/` that gets installed to `~/.claude/commands/`. Audit/helper scripts under `scripts/` (e.g., `emit_run_report.sh`, `refresh-pcv-bundle.sh`) are not "commands" and may be added or revised within v1.x without violating the no-new-commands rule.*
- **v2.0** — New commands only after classroom testing validates the concept. Each new command must pass the weekly-use test.
- **PCV upstream** — PCV files are Kay's upstream. We distribute v3.14 as-is. Version bumps come from Kay's repo; maintainer-only via `scripts/refresh-pcv-bundle.sh --version <tag>`. Student/user-facing install never touches the network for PCV.

---

## Conventions for this document (added 2026-05-02 per /coa Q5 Z1 ruling)

Three identifiers, three jobs — used consistently throughout DESIGN.md and the rest of the toolkit:

- **Brand name** (prose): **Research Amp Toolkit**. Used in README hero copy, CITATION text, slide decks, anywhere a human reads.
- **Path / repo slug**: `Research-Toolkit/`. Used in install instructions, `git clone` URLs, and any doc telling a user where the toolkit lives on disk after a clone.
- **Legacy on-disk name**: `ai-research-toolkit/`. The pre-rename directory name. Appears only in v1.0–v1.3 changelog narrative for audit-trail purposes — NOT in user-facing instructions for v1.4+.

**Command count source-of-truth**: 14 standalone commands (`.md` files in `~/.claude/commands/`, listed by the `SHARED_COMMANDS` and `STUDENT_ONLY` arrays in `install.sh`) + `/pcv` (registered via `~/.claude/skills/`) = **15 user-visible commands**. Any prose count in any doc must match this rule; the install banner derives counts from the arrays at runtime, not from prose.

**Recipe CWD invariant**: All shell recipes in user-facing docs assume CWD = the toolkit clone root (`Research-Toolkit/`). No `cd ai-research-toolkit/...` chains. If a recipe requires a deeper directory, the recipe begins with one bare `cd <subdir>/` line; never with the toolkit name as a prefix.

---

## File Inventory

```
Research-Toolkit/                        Total: ~40 files (excluding pcv/ upstream bundle)
├── README.md                            Root documentation
├── LICENSE                              MIT
├── CITATION.md                          BibTeX + attribution prose
├── CITATION.cff                         Machine-readable citation
├── CONTRIBUTING.md                      Contribution guidelines
├── EVIDENCE.md                          Empirical metrics
├── DESIGN.md                            This file
├── QUICKSTART.md                        First-session walk-through
├── USAGE_GUIDE.md                       Full command reference
├── toolkit-config.md                    User configuration template
├── install.sh                           Dual-mode installer (array-driven counts; v0.1)
├── instructor/
│   ├── README.md                        Instructor quick start (8 commands)
│   └── guides/
│       ├── using-pcv-in-courses.md      Teaching guide
│       ├── using-coa-for-discussion.md  Teaching guide
│       └── using-pace-for-grading.md    Teaching guide
├── student/
│   ├── README.md                        Student quick start (15 commands)
│   └── bootstrap.md                     In-session installer for Claude Code
├── shared/commands/                     14 generalized commands
│   ├── coa.md                           Council of Agents
│   ├── pace.md                          Parallel Agent Consensus
│   ├── audit.md                         Citation & numerical audit (v1.0+)
│   ├── review.md                        Three-lens document review (v1.4)
│   ├── improve.md                       Infrastructure scanner
│   ├── simplify.md                      Code/document review
│   ├── help.md                          Triage entry-point (v1.3)
│   ├── runlog.md                        Longitudinal run observability (v1.1)
│   ├── startup.md                       Session briefing
│   ├── dailysummary.md                  Daily work summary
│   ├── weeklysummary.md                 Weekly aggregation
│   ├── commit.md                        Intelligent git commits
│   ├── quarto.md                        Slide generation
│   └── readable.md                      Document extraction
├── scripts/                             Shared helper scripts (v1.1+)
│   ├── emit_run_report.sh               Run instrumentation helper (atomic flock append)
│   └── refresh-pcv-bundle.sh            Maintainer-only PCV upstream sync
├── tests/
│   ├── README.md                        Test fixture index
│   └── smoke/                           Smoke test fixtures
│       ├── fresh_clone_test.sh          Project-token leak scan + frontmatter contract
│       ├── audit_smoke.md, paper.md, sources/   /audit fixture
│       ├── pace_source_verification.md, sales_fixture.csv   /pace Step 2e fixture
│       ├── help_triage.md               /help triage fixture (v1.3)
│       ├── commit_grouping.md           /commit logical-grouping fixture
│       └── runlog_parser.md             /runlog parser fixture (v1.2 — synthetic, portable)
├── references/                          JIT recipe files
│   └── processing_student_submissions.md (v1.1)
├── docs/                                Landing page content (jbenhart44.github.io)
└── pcv/                                 PCV v3.14 (Kay's upstream; refresh via scripts/refresh-pcv-bundle.sh)
    ├── skill/                           Recursive (handlers, hooks, planning, construction, verification, transition, bundled)
    └── agents/ (4 files)                pcv-builder, pcv-critic, pcv-research, pcv-verifier
```

---

## v1.1 Canonical `run_log.csv` Schema (2026-04-17)

All tools that emit instrumentation MUST append rows using this **13-column schema** (unified with historical /pace, /coa, /pcv-research rows):

```csv
run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
```

**Rules**:
- **Multi-agent commands** (/pace, /coa, /pcv-research): fill `agent_count`, `convergence_rate`, `agree_count`, `diverge_count` with numeric values.
- **Single-agent commands** (/audit, /improve, /dailysummary, /commit, /startup, /runlog): leave those 4 columns **EMPTY** (not 0, not N/A — empty). They have no convergence semantics.
- **All commands**: write a JSON object in the `notes` cell holding structured fields (CSV-quoted, with `""` escaping internal quotes). Keys are command-specific; downstream consumers parse as JSON.
- **Parsing**: downstream consumers (e.g., /runlog) MUST use Python's `csv` module (or equivalent CSV-aware parser), **not** raw `awk -F','`. The `task_summary` and `notes` cells contain embedded commas which break naive splitting.

**Historical compatibility**:
- Legacy rows (pre-2026-04-10) may have older 9-column schema or column-shifted tool-name-in-position-1 errors. The `scripts/emit_run_report.sh` helper auto-creates the canonical 13-column header if the file doesn't exist; it appends to existing files regardless of header shape.
- `/runlog`'s parser heuristically detects legacy/malformed rows (tool column starting with `2026-`, `2025-`, `pace_`, `coa_`, `pcv_` is treated as a column-shifted legacy row) and skips them with a count in the evidence footer.

**Why this was decided**: Pre-v1.1 /pace, /coa, and /pcv-research each wrote their own ad-hoc instrumentation. During v1.1 planning (2026-04-17), `emit_run_report.sh` was built with a 9-column schema that collided with the 13-column historical schema. Reconciled in-session to the 13-column canonical. Recorded here so v1.2+ contributors don't reproduce the mismatch.

---

## v1.1 Changelog (2026-04-17)

Added:
- `/runlog` command — longitudinal run observability (198 lines)
- `scripts/emit_run_report.sh` — shared instrumentation helper (~130 lines)
- `tests/smoke/` — fixtures for /audit, /pace, /runlog
- `references/processing_student_submissions.md` — JIT recipe
- `instructor/guides/using-audit-for-student-submissions.md` — new (170 lines)

Changed:
- `/coa` STEP 1b — added local-Sonnet fallback when Gemini cross-check fails (was silent skip)
- `/dailysummary` — added `--append-pointer` mode, Step 0c filename collision resolution, Step 1 WSL-aware 5s git timeouts, evidence footer, instrumentation call
- `/startup` — evidence footer + instrumentation call
- `/audit` — instrumentation call + smoke-test pointer
- `/improve` — Priority-3 gating (skip historical reads when <3 friction signals) + gate self-test log + instrumentation call
- `/commit` — instrumentation call
- `/pace` — cross-linked /audit integration for grading workflow
- `instructor/guides/using-pace-for-grading.md` — expanded with /audit integration
- README.md — 3-problem student-facing rewrite + fork-friendly disclaimer + /runlog + 13-command count
- `jbenhart44.github.io/index.html` — parallel updates

Deferred to v1.2:
- Instrumentation for /weeklysummary, /quarto, /readable, /simplify (no usage evidence)
- `/audit` + `/audit-library` merger
- `/dailysummary` + `/weeklysummary` merger

---

## v1.2 Changelog (2026-04-18)

**Renamed: `AI-Assisted Research Toolkit` → `Research Amp Toolkit`**

Rationale: The prior name read as "toolkit doing AI research" rather than "toolkit for doing research with AI" (Kay 4/15 transcript line 1805-1811). Two-round naming process documented in `plans/toolkit_rename_preview.md`. Round 1 winner (`socratic-research-toolkit`, 18/20 score) was rejected by Jake on tone — too academic-jargon-heavy. Round 2 surfaced human-dependence-framed candidates; `research-amp` won the deployment-criteria comparison (113/125, narrowly behind `thinking-tools-research` at 114/125 on K2 methodological-anchor only). After the Round 2 lock, Jake appended "Toolkit" (4/19) to restore the collection-of-commands signal and improve student-fit readability — final name: **Research Amp Toolkit**.

Why "Research Amp" as the metaphor core: the amplifier framing is literal — the tool produces zero output without the user's signal. This honors Kay's "user thinks / tool guides" criterion (transcript line 1825-1832) and avoids both SaaS-marketing fluff (Kay's companion/copilot rejection at line 1820-1828) and the agent-overloaded vocabulary (line 4565). Single-syllable hook ("amp") for outreach memorability.

Why append "Toolkit": (a) restores the collection-of-things signal that a 13-command repo needs, (b) improves student-fit — "the Research Amp Toolkit" reads more natural than bare "Research Amp" in a Kay-to-student email, (c) keeps URL reasonable at 49 chars for `research-amp-toolkit`, still shorter than the pre-rename `ai-research-toolkit`.

Changed:
- README.md — hero sentence rewritten around amplifier framing; `/audit` smoke fixture path updated
- DESIGN.md — title + this changelog
- CITATION.md — attribution paragraph + BibTeX `title` field updated
- toolkit-config.md — template default updated (if applicable)
- jbenhart44.github.io — tag cloud, workflow table, hero sentence
- Directory references inside docs: `ai-research-toolkit/` → `research-amp/` (mechanical replace across 13 files)

Not changed (deferred):
- Directory rename on disk — pending coordinated commit (see `plans/charge_toolkit_v1_1_release.md`)
- GitHub repo URL — separate operation, may keep `Research-Toolkit` as the public repo slug for inbound link continuity

Earlier shortlist (Round 1, superseded): socratic-research-toolkit / claude-research-assistant / research-scaffold / guided-research-toolkit. See `plans/toolkit_rename_preview.md` for full Round 2 scoring against the K1-K6 Kay-validated criteria.

---

## v1.3 Changelog (2026-04-19)

**Added: `/help` — Socratic triage command (EXPERIMENTAL)**

Motivation: Kay 4/15 transcript line 1304 (Brett's "traffic cop route" comment) flagged the paradox-of-choice problem as the 13-command toolkit grows. A stressed student on a Pro plan at 11pm shouldn't have to read the README to find the right command. `/help` takes a one-line situation and recommends 1-3 commands after 0-1 clarifying questions.

Design process: The v0.1 draft was reviewed by a 3-seat CoA Quick Panel (Skeptic + Practitioner + Cognitive Ergonomist) on 2026-04-19. All three converged on "NOT ship-ready, but minor revision not redesign" via three independent causal chains:
- Skeptic: structural defects (inventory drift, leaked Jake-specific paths)
- Practitioner: factual errors vs filesystem (spec claimed 13 commands / 10 fixtures; disk has 12 / 4) + silent `emit_run_report.sh` parser bug
- Cognitive Ergonomist: Examples 2 & 3 exceeded Miller-under-stress working-memory ceiling by 2-3x; 23% alarm-fatigue rate on fixture pointers

v0.2 applied all 6 tactical fixes (T1-T6), 2 strategic contracts (S1 inventory sync, S2 success metric), and the I3 shell test for field encoding. Gemini cross-check truncated at ~400 chars; local Sonnet fallback invoked per /coa v2.1 protocol. Sonnet surfaced one independent insight: the modal stressed-student input is not "I have a paper and I'm worried about citations" but `/help I'm stuck` or bare `/help` — treated as modal case, not edge case, via the shape-C scaffold menu.

**Shipped WITHOUT the 5-student premise pilot the council recommended (I1 deferred).** Rationale: pilots are logistically hard pre-rollout, and the success metrics + re-open triggers give us a 3-4 week feedback loop in live classroom use. Premise resolution happens via `run_log.csv` signals, not pre-registration.

Success metrics (pre-registered): `/help` is useful if AT LEAST ONE of — (1) ≥20% of recommended commands are subsequently run within 30 min, (2) sessions using `/help` have higher command-diversity than sessions without, (3) low rate of same-student multi-invocation for the same problem. If NONE fire by end of fall 2026, `/help` is a removal candidate.

Re-open triggers: R1 (inventory drift >10%), R2 (clarify-then-no-match correlation), R3 (study-aid inversion pattern).

Added:
- `shared/commands/help.md` — the command file (~180 lines, follows audit.md pattern)
- `tests/smoke/help_triage.md` — 4 test cases (shape A, shape A-with-prereq, shape C scaffold, no-match)
- README.md — new "Triage Layer" section
- DESIGN.md — this changelog + Tier 4 row in command inventory
- jbenhart44.github.io — /help added to command list + tag cloud (pending)

Design artifacts (preserved for longitudinal comparison if /help is removed and re-attempted):
- v0.2 spec: `plans/help_command_draft.md`
- Council session: `coa/council_sessions/coa_2026-04-19_help_command_design/` (author-local; not bundled with the toolkit)

---

## v1.4 Changelog (2026-04-19)

**Two coordinated changes: PCV v3.14 bundle bump + `/review` command ship.**

### PCV v3.14 bundle bump (was v3.9)

Dr. Kay released PCV v3.14 on 2026-04-19. Per his email: "significantly more efficient, running approximately 3 times faster and using about half the number of tokens as previous versions." This is a 5-version jump; intermediate v3.10-v3.13 included the breaking `plans/` → `pcvplans/` rename in v3.13 and the new `handlers/` + `hooks/` shell-script architecture in v3.14.

v3.14 upstream claim of 3× speed / 50% token reduction is **upstream pending local remeasurement** — we have not independently benchmarked it in this toolkit. See `EVIDENCE.md`.

Migration plan: `plans/charge_pcv_v314_migration.md` (8 open questions, 10-phase plan produced by `/pcv-research` on 2026-04-19 at `plans/research_runs/2026-04-19_104834/`).

Bundle changes:
- `pcv/` updated from Kay's upstream (shallow clone from `github.com/mgkay/mgkay.github.io/main/pcv/`, SHA pinned via `.upstream-sha`)
- New `scripts/refresh-pcv-bundle.sh` — maintainer-only refresh from upstream, requires explicit `--version` arg
- New `scripts/check-pcv-upstream.sh` — drift detector (single HEAD request, exits 1 on drift); CLAUDE.md audit-flag entry added
- New `scripts/rollback-pcv-v314.sh` — scripted rollback from tarball; dry-run gate before execute

Install.sh changes:
- Flat-file PCV install loop replaced with recursive `cp -r` (v3.14's subdirectory structure — handlers/, hooks/, planning/, construction/, verification/, transition/ — was incompatible with the v3.9 flat-file assumption)
- Added `chmod +x` for handler + hook shell scripts (OneDrive WSL strips exec bits; install.sh now restores them automatically)
- Added `/review` + `/runlog` (previously unregistered) to SHARED_COMMANDS and STUDENT_ONLY respectively
- Command count bumped: 12 → 15 full, 6 → 8 minimal

**HOME-isolated smoke test (Phase 3 of migration plan)** caught the flat-file install bug before touching Jake's real `~/.claude/`. This validated Instance 2's bundle-first + dogfooded install order over Instance 1's local-first order in the PCV-Research synthesis.

### /review — three-lens document review (SHIPPED v1.0)

Takes an external document (paper, advisor memo, spec draft) and runs it through three parallel expert lenses — Skeptic + Practitioner + Editor — producing 5-10 takeaways + project relevance + 3 implications per lens, plus a Chair synthesis. Complements /coa (decisions) and /pace (deliverables) as the third-flavor multi-agent primitive: /review is for **absorbing** external writing.

Design: The three lenses are the mandatory Skeptic + Practitioner from the /coa ROSTER plus Editor (the ROSTER's designated Historian-replacement for prose documents). Chair role is inline synthesis by the Clerk — no 4th agent, reducing token cost vs /coa Quick Panel while preserving multi-perspective coverage.

Design process: Lean adversarial self-review on the spec caught two issues before smoke (project-context extraction not specified; PDF/docx guard missing from Step 0); both patched. Smoke test was the command's first substantive invocation — running /review against Kay's text-formats doc (`Kay Meetings/text_based_formats_for_claude_code.md`). Results: three agents ~30s each in parallel, ~106K tokens total (within 80-120K projected envelope), non-overlapping outputs, Chair synthesis produced cleanly, shipped as v1.0 with no post-smoke revisions.

**Smoke-test artifact**: `Kay Meetings/reviews/review_2026-04-19_text_based_formats_for_claude_code.md` — validates the command's value proposition with a real document. This file is referenced from `EVIDENCE.md` as the v1.0 baseline.

**Future work tracked**: /review as a template for per-command documentation on the public toolkit website. See `plans/review_command_documentation_idea.md`.

Added:
- `shared/commands/review.md` — the command file (~240 lines)
- Install.sh registration + command count bump (see above)
- `EVIDENCE.md` — new /review section with smoke-test metrics
- `evidence/command_performance_log.md` — debut invocation logged (author-local instrumentation; not bundled with the toolkit)
- `plans/review_command_documentation_idea.md` — tracks the per-command-docs future use case

Bonus bug caught during I3 shell test: the spec's user field `outcome=match` collided with the script's native `outcome:` YAML key, producing duplicate keys. Renamed to `triage_result=match`. This is a lesson for future command specs — do not use field names that shadow the script's built-ins.

---

## v1.5 Changelog (2026-05-11)

**Three coordinated prompt edits to `/audit`, `/quarto`, `/commit` after a multi-stage /pcv-research + /coa validation pass.**

This is the first toolkit-wide enhancement wave driven by structured comparative review rather than direct user-encountered incident. Prior changelogs (v1.1–v1.4) were motivated by failures encountered during live use (commit-attribution bug, citation pipeline misses, PCV bundle drift). The v1.5 wave was produced by:

1. `/pcv-research` BF-1 + BF-2 run on 2026-05-11 → 10-item enhancement queue
2. `/coa` Working Council session on 2026-05-11 → 4-seat (Skeptic + Practitioner + End User + Editor) + Gemini cross-check → conditional partial proceed
3. v1.5 ships items 1, 2, 5 of the queue (Tier 1, three prompt-only edits). Items 3, 4 (Attack Intensity Preservation + /coa Concession Threshold) deferred 48h pending advisor surface decision per End User finding. Item 7 (/simplify prose-branch watchlist) deferred indefinitely pending domain-vocabulary allowlist per Editor finding (operations-research methodology vocabulary would produce false-positive AI-tell flags under the proposed checklist).

Source artifacts for this wave are tracked in the maintainer's internal planning surface; this changelog records the user-facing changes only.

### Change 1: `/audit` MATERIAL GAP refusal token (Item 1 of the queue)

`shared/commands/audit.md` "Important Rules" section gains a sixth rule documenting the `[MATERIAL GAP: <claim> — no grep hit for "<pattern>" in <searched dirs>]` token. The token replaces the pre-v1.5 informal `% TODO: citation needed` convention with a structured form that is machine-greppable.

**Sentinel-comment guard (binding constraint from /coa Editor seat)**: the marker emits to the audit report directly, but when /audit is also recommending an inline edit to the document being audited, the marker MUST render as a comment sentinel for that document's format (`% [...]` for LaTeX, `<!-- [...] -->` for Quarto/HTML/Markdown), NEVER as visible body text. Rationale (Editor's pre-mortem): a visible `[MATERIAL GAP: ...]` line in submitted prose is louder than the underlying gap — a reviewer reading it instantly knows the author used an LLM and didn't clean up before submission. The quiet placeholder convention defends author credibility; the loud version damages it.

### Change 2: `/quarto` MATERIAL GAP speaker-note-only guard (Item 2 of the queue)

`shared/commands/quarto.md` Step 3c "Data Accuracy" section gains a fifth rule extending Change 1 to slide bullets. When `/audit` returns NOT FOUND or MISMATCH for a value that would otherwise appear on a slide, the `[MATERIAL GAP: ...]` marker goes ONLY in the speaker-note block (`::: {.notes}` ... `:::`), NEVER as a slide-face bullet.

**Why stricter than Change 1**: slide bullets are seen by audiences (conference attendees, committee members, site-visit panels), not just authors. A projected `[MATERIAL GAP: ...]` line at a committee meeting is a credibility hit that the comment-sentinel guard for prose drafts does not need to address. Speaker notes are author-only by default in the Quarto render pipeline.

### Change 3: `/commit` workstream-scope pre-check (Item 5 of the queue — IRON RULE re-injection)

`shared/commands/commit.md` gains a new Step 0a (after Step 0 "Survey All Changes", before Step 0b "Slow-Filesystem Detection") that mechanically enforces the project-level CLAUDE.md terminal-scope rule at the commit boundary.

Mechanism: after `git status --short`, count distinct top-level workstream directories across modified + untracked files. If ≥2 workstreams are touched, re-inject the terminal-scope hard rule into the user-facing output and require explicit confirmation (`scope-confirmed: <ws>` to stage only one workstream, or `multi-scope-acknowledged` for deliberate cross-scope commits). If only 1 workstream is touched, skip silently. This converts a previously discipline-only rule into a mechanically enforced check at the highest-leverage boundary, where cross-scope leak silently propagates to git history.

### Items deferred from this wave (and why)

- **Items 3 + 4 (Attack Intensity Preservation + /coa Concession Threshold + Frame-Lock Detection)**: deferred 48h. Three Council seats converged on item 3 as the highest-risk item: Skeptic flagged that the same model self-assesses its own 1–5 evidence rubric (self-certification circularity); End User flagged that the "≥4" threshold is a free parameter with no documented calibration rationale, violating the "transparency is structural rather than procedural" tenet; Practitioner flagged that items 3 and 4 both modify `coa.md` and must ship as a single coordinated PR. Resolution requires an advisor surface decision on whether /pace and /coa behavioral changes ship with prior notification or post-hoc changelog.
- **Item 7 (/simplify prose-branch style-tells)**: deferred indefinitely. Editor seat showed the proposed style-tell watchlist is calibrated for general writing — flagging terms like "robust" as AI-tells when they are standard operations-research methodology vocabulary ("robust optimization", "robust regression"). Pursuing this requires a domain-vocabulary allowlist + report-only mode (no auto-edits) before adoption is safe.
- **Items 6, 8, 9, 10 (Tier 2)**: deferred to the week of 2026-05-19, post-submission. Item 9 (passport.yaml triple for cross-command state) was further gated on a prior-work `grep` of `startup.md` — which returned zero hits, confirming the item needs full implementation from scratch.
- **Tier 3 / v2.0 deferrals**: live-network paper existence checks (default-path H2 violation); two-call generator-evaluator gate structure (not verified against current `/coa` and `/pace` orchestrators); plugin-marketplace install architecture (changes install surface, deferred past v1.x stability promise); cross-model benchmark utility (deferred until post-grant-submission).

### Hard rules honored

- **No /pcv or /pcv-research changes** in this wave. Per memory `feedback_pcv_is_kays_project.md` (2026-04-15), /pcv changes go through Dr. Kay. Items 3 + 4 touch `coa.md`, not `/pcv` — but the End User finding raised an analogous "co-author surface" concern about /pace behavioral changes that the user (Jake) will address with Dr. Kay before items 3 + 4 ship.
- **Same-model caveat preserved**: the queue was generated by Sonnet 4.6 BF instances, synthesized by Sonnet 4.6 Chair, and implemented by Sonnet 4.6 in this commit. The /coa Gemini cross-check returned a strong divergent signal ("WAIT and revise — postpone all enhancements until after Paper 1 submission"), which the Chair downgraded as paternalistic on the urgency framing but preserved as the top Surprise Finding (S1: mono-model audit chain) — addressed in this commit by limiting the wave to items 1, 2, 5 (the three highest-confidence, lowest-coordination-risk items) and deferring everything else pending additional verification gates.
- **Honorifics**: "Dr. Kay" and "Dr. McConnell" used consistently throughout the changelog and v1.5 sources.
- **No Claude-Code coauthor**: this commit follows the toolkit's standing no-attribution rule.

### What did NOT change

- No new commands. No new files in `shared/commands/`. No new dependencies. No new install.sh registration. No version bump in `pcv/skill/VERSION` (Dr. Kay's project, untouched). The three edits are additive prompt rules within existing command files; the toolkit's command count and install surface are unchanged.

### Cross-model verification gate — gate fired, found a real fix

Before commit, the actual edited prompts for Changes 1 and 2 were handed to a cross-model query (via `mcp__crossmodel__query_model`) with a synthetic scenario: a value attributed to a fabricated paper. The cross-model verifier was asked to predict the behavior of the edited prompt and flag any failure mode.

- **Change 1 (/audit)**: cross-model verifier predicted correct behavior. Shipped as drafted.
- **Change 2 (/quarto)**: cross-model verifier flagged a real failure mode the original drafting missed — the rule said "the marker goes ONLY in the speaker-note block," but did not handle slides that have no `::: {.notes}` block yet. The implementing model could silently omit the marker when the speaker-note section was absent, losing the gap-tracking artifact entirely. Fix applied pre-commit: an explicit "if the slide does not already have a `::: {.notes}` block, create one" clause.

This is the first instance of cross-model verification catching an underspecification on a Tier-1 toolkit edit before merge. Worth codifying as a v2.0 standing policy: any prompt edit to a citation-pipeline command is handed to an independent model for behavior prediction on a synthetic-failure scenario before the edit is committed.

---

## v1.6 Changelog (2026-05-11) — Documentation pass

**Five additive documentation artifacts: `POSITIONING.md`, `references/preventable_errors.md`, `references/iron_rules.md`, README headline philosophy, `llms.txt`. No command-prompt changes; no behavioral changes; no install-surface changes.**

The v1.5 wave added rules to commands; v1.6 makes the toolkit's positioning, error surface, and rule index discoverable in their own right. The motivation is that a user evaluating whether to install the toolkit, a contributor proposing a change, or a future maintainer auditing a load-bearing rule should not have to read the entire command corpus to find the answer to "who is this for?", "what does it prevent?", or "where is rule X enforced?". Each of these questions now has a single navigable file.

### Change 1: `POSITIONING.md` — what this toolkit is for, and what it is not

A dedicated positioning artifact, separate from `README.md` (install + catalog) and `DESIGN.md` (architecture + changelog). States the toolkit's target users (PhD students, early-career researchers, faculty advisors, instructors) and the categories of work it is deliberately not optimized for (general-purpose software engineering, persistent-memory agents, hidden AI use, production CI/CD, black-box installation). Articulates six design commitments — citation pipeline as primary gate; planning/construction/verification as three auditable steps; multi-perspective adversarial review as first-class; text-first architecture; per-user forkability; honorific and authorship discipline — and four intentional non-goals so the omissions are not mistaken for oversights. This file is the answer to "should I install this?" and "who is this for?"

### Change 2: `references/preventable_errors.md` — twelve error classes and what prevents each

A catalog of the categories of academic-research error this toolkit's rules and commands are designed to prevent in deliverables. Twelve classes (E1 through E12): misquoted figures attributed to real sources, fabricated citations, premature filling of unknown values, silent methodology changes, plausible-sounding filler, frame-lock under user pushback, single-context simulation of multi-agent review, slide-face leakage of author-only markers, cross-workstream commit bleed, honorific drift in reader-facing artifacts, co-author attribution to AI assistance, and submission-time discovery of an open gate. Each entry pairs the error pattern with the command or rule that prevents it. This file is the answer to "what is the toolkit's friction buying me?" and to "would this simplification weaken a load-bearing guardrail?"

### Change 3: `references/iron_rules.md` — consolidated rule index

The toolkit's iron rules live in the command files that enforce them. That distribution is correct for invocation-time enforcement, but it makes it hard to scan the constraint surface in one place. This file is the navigation surface: every iron rule, the file it lives in, and a one-line summary of which preventable-errors entry motivates it. Rules are grouped by domain — citation and verification, deliverable integrity, multi-agent discipline, authorship and attribution, workstream and commit hygiene, methodology and reproducibility, read-only constraints. This file is the answer to "where does rule X live?" and "what rules does my proposed change need to respect?"

### Change 4: README headline philosophy

The README opener gains a single-line philosophical framing — "Every empirical value cites a file on disk. Every claim survives `grep`. Dissertation-grade, not vibe-grade." — placed above the v0.1 status warning. The line is meant to be the first thing a reader encounters and to set expectations about what kind of tool this is before they reach feature lists. The README also gains pointers to `POSITIONING.md`, `references/preventable_errors.md`, and `references/iron_rules.md` in the existing "Design rationale" links line.

### Change 5: `llms.txt` — LLM-consumable summary at repo root

A short, single-file summary at the repository root in the conventional `llms.txt` discoverability format. States the toolkit's purpose, target users, command catalog organized by workflow phase, key documents, design commitments, and install instructions. Intended for consumption by language-model agents orienting to the repository — downstream installers, contribution helpers, indexing agents — that benefit from a concise self-contained summary rather than having to read multiple documents to understand what the toolkit is and is not.

### What did NOT change

- No new commands. No new files in `shared/commands/`. No new dependencies. No new install.sh registration. No version bump in `pcv/skill/VERSION` (out of toolkit scope). The five additions are pure documentation; the toolkit's command count, install surface, and runtime behavior are unchanged.
- No command-prompt edits and no rule changes. v1.6 documents the existing rule surface; the rules themselves are as v1.5 left them.

### Disclosure of source pattern

The v1.6 wave is informed by reviewing the documentation layouts of several other Claude Code toolkits in adjacent problem categories (general-purpose software engineering, persistent-agent memory). The patterns adopted — a separate positioning file, a named error-class reference, a consolidated rule index, a one-line README framing, an `llms.txt` summary — are overarching documentation patterns observed widely across well-maintained toolkit repositories. The content of every file shipped in v1.6 is written from this toolkit's own provenance, its own rule structure, and its own design commitments. No external taxonomies, no external citations, and no external toolkit structures are reproduced.

### Hard rules honored

- **Honorifics**: "Dr. Surname" used throughout where doctorate-holders are named.
- **No AI co-author**: the v1.6 commit follows the standing no-attribution rule.
- **Citation pipeline**: no empirical values attributed to external sources are introduced in v1.6 artifacts — the new files describe the toolkit's own commitments and rule surface, with no numerical claims.
- **Workstream scope**: the v1.6 commit stages files exclusively from the `ai-research-toolkit/` workstream; the parent-repo submodule pointer bump is a separate commit in the parent repo.

---

## v1.7 Changelog (2026-05-12) — End-to-end citation pipeline

**Two coordinated edits that close the upstream-to-downstream loop on the citation gate: `/readable` now emits typed extraction-gap markers when a page cannot be read; `/audit` now recognizes those markers and additionally exposes a `--deep` sub-mode that extends the single-step grep gate to a five-step claim chain with a mandatory terminal verdict per citation.**

The motivation. v1.6 documented the citation pipeline as the toolkit's primary gate. Two failure modes in that pipeline survived the prior wave: (a) `/readable` could silently skip a page when extraction failed (image-only PDFs with OCR-resistant content, encoding errors, table renders the visual subagent could not disambiguate), leaving the downstream `/audit` unable to distinguish "the cited value is genuinely not in the paper" from "we never managed to read the cited page;" and (b) `/audit` ran a single-step grep gate that caught misquoted *numbers* but did not catch misquoted *methodology* — a value that appears in a paper's robustness section presented as a headline finding, or a value cited from a paper whose methodology has since been retracted or corrected. v1.7 addresses both.

### Change 1: `/readable` — typed extraction-gap markers

When pypdf returns empty for a page AND the fitz fallback returns empty AND the image-render visual-subagent path also fails to produce readable text, the `.txt` MUST contain an explicit typed gap marker at the corresponding `=== PAGE N ===` boundary, of the form `[MATERIAL GAP: extraction failure on page N — <reason>]`. The reason is mandatory and human-readable. The marker is the page content for that page — no best-guess approximation is written alongside it.

The marker is greppable: a downstream consumer can distinguish a clean empty page from an extraction failure with a single grep. Most importantly, it composes with `/audit`'s grep gate — see Change 2.

This is the upstream half of E5 (plausible filler) prevention. The toolkit's prior `/readable` design assumed an extraction failure was a transient problem the user would notice; the rest of the pipeline did not have a structural way to know an extraction had failed silently. The marker closes that hole.

### Change 2: `/audit` — GAP-IN-SOURCE recognition + `--deep` claim-chain sub-mode

Two additions to `/audit`, both additive.

**Addition 2a: GAP-IN-SOURCE status.** When the standard grep gate returns zero matches for a cited value, `/audit` now grep-checks the source `.txt` for a typed `[MATERIAL GAP: extraction failure on page <P>]` marker at the cited page before emitting NOT FOUND. If the marker is present, the status is GAP-IN-SOURCE — a different actionable finding than NOT FOUND. NOT FOUND tells the author "the cited value is not in the paper, fix the citation"; GAP-IN-SOURCE tells the author "we could not read the cited page, re-extract or inspect manually." Conflating the two produced wrong author behavior in the prior gate.

**Addition 2b: `--deep` sub-mode (claim-chain audit).** Invoked via `/audit <file> --deep`. Extends the single-step grep gate to a five-step chain. For every citation that passed the standard grep gate, the deep mode additionally checks: methodology section locatable in the source `.txt`; absence of any retraction or correction notice in the source paper or in a co-located retraction-notes file; and whether the cited value's location falls inside a robustness, supplementary, sensitivity, or appendix section while the document cites it as a headline result. The deep mode emits a structured YAML verdict per citation, one of five mandatory terminal states: `verified`, `partial`, `unverifiable`, `misattributed`, `retracted`. The verdict field is mandatory — the deep audit cannot terminate in ambiguity. An entry without a verdict is a defect.

The deep mode does not call external services. Retraction signals come from local `.txt` extractions and from user-curated co-located retraction-notes files (`<paper-stem>.retraction.md` or directory-level `RETRACTION_NOTES.md`). Live-network retraction lookup (CrossRef, Retraction Watch, Semantic Scholar) is explicitly out of scope for v1.7 — it would violate the no-live-network default-path constraint and is not addable as an opt-in flag within v1.7's scope.

The deep mode is a pre-submission gate, not an every-session step. The standard `/audit` remains the daily-use command. The deep mode adds the chain on top of the standard audit; a document submitted without the standard audit having passed is not made safer by skipping straight to deep mode.

### What did NOT change

- No new commands. The two changes are additive prompt edits within existing command files (`readable.md`, `audit.md`) and additive content within existing reference files (`preventable_errors.md`, `iron_rules.md`). The toolkit's command count, install surface, and runtime behavior outside the augmented modes are unchanged.
- No new dependencies. The deep mode uses Read + Grep tools the standard audit already has access to. No additional Python packages required.
- No changes to `/audit`'s default-mode behavior. Documents that the standard audit previously marked VERIFIED, MISMATCH, NOT FOUND continue to receive those statuses in the default mode. GAP-IN-SOURCE replaces NOT FOUND only when a typed extraction-gap marker is present at the cited page — a state that did not previously exist in `.txt` outputs.
- No changes to `/pcv` or `/pcv-research`. Out of scope per the standing rule that those commands are Dr. Kay's project.

### Verification gate that gated this change

A V1 mechanism-test gate was applied to the deep-mode design before any prompt edit was drafted. The three checks:

1. **No live-network on the default path.** The deep mode uses only local PDFs, local `.txt` extractions, and local co-located retraction-notes files. No HTTP requests, no SDK calls, no opt-in network flag introduced. ✓
2. **No DB or daemon dependency.** All chain steps are file reads; the YAML verdict is written to disk; no background process, no shared store. ✓
3. **Maps to a named error class in `preventable_errors.md`.** Refines E1 (misquoted figures) by extending the gate from value-level to methodology-level. The E1 entry now carries an explicit extension paragraph documenting the v1.7 refinement. ✓

The gate passed. Documented here so the precedent is visible: any future toolkit edit that proposes augmenting an existing command with a behavior whose mechanism resembles an external pattern must pass this three-check gate before the prompt is drafted, and the gate result is recorded in the changelog.

### Smoke fixtures

Two smoke fixtures ship with v1.7 — both stubs that document the test, since neither can be executed inside the prompt-edit harness:

- `tests/smoke/audit_deep_smoke.md` — fixture exercising the five-step chain on three citations: one clean (expected `verified`), one whose source `.txt` contains a retraction marker (expected `retracted`), one whose cited value falls inside a Robustness section but is cited as a headline result (expected `misattributed`).
- `tests/smoke/readable_gap_smoke.md` — fixture exercising the typed gap marker emission when a page cannot be extracted (image-only PDF page with OCR-resistant content). Documents the expected marker shape and the downstream `/audit` GAP-IN-SOURCE recognition.

Both fixtures should be run as part of the next test pass when a Python environment with the `/readable` dependencies is available.

### Hard rules honored

- **Honorifics**: "Dr. Surname" used throughout where doctorate-holders are named.
- **No AI co-author**: the v1.7 commit follows the standing no-attribution rule.
- **Citation pipeline**: no empirical values attributed to external sources are introduced in v1.7 artifacts — the changes describe the toolkit's own pipeline extensions, with no numerical claims requiring grep verification.
- **Workstream scope**: the v1.7 commit stages files exclusively from the `ai-research-toolkit/` workstream; the parent-repo submodule pointer bump is a separate commit in the parent repo.
- **Describe in own terms**: the v1.7 changes are framed as extensions of the toolkit's existing citation-pipeline commitment from v1.6; no external toolkits, papers, or feature names appear in the prompt edits, reference files, or this changelog.
