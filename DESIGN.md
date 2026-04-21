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

### Why 12 Commands

The toolkit started with 15 commands built during PhD research. Assessment:

| Tier | Commands | Disposition |
|------|----------|-------------|
| **Tier 1 — Showcase** | /pcv, /coa, /pace, /improve, /simplify | Core methodology — included |
| **Tier 2 — Workflow** | /startup, /dailysummary, /weeklysummary, /commit | Daily-use productivity — included |
| **Tier 3 — Content** | /quarto, /readable | Document generation — included |
| **Tier 4 — Triage** | /help | Discoverability triage — added v1.3 |
| **Excluded** | 4 domain-specific commands | Not generalizable beyond the original research context |

14 commands (13 command files + /pcv via skills registry). The 12th (audit) was added on 2026-04-03 after catching 4 numerical mismatches on a dissertation poster — citation verification became a non-negotiable capability. The 13th (/runlog) was added in v1.1 for longitudinal observability. The 14th (/help) was added in v1.3 on 2026-04-19 to address the paradox-of-choice problem Kay identified in the 4/15 transcript (line 1304 Brett "traffic cop route"); see v1.3 changelog below. A research instrument (/pcv-research) was previously bundled but was removed on 2026-04-10 after empirical testing revealed its hierarchical subagent spawning architecture is incompatible with Claude Code's tool model; it is held back pending further redesign and is no longer shipped.

### Persona-Command Mapping

| Command | Instructor (`--minimal`) | Student (full) | Layer |
|---------|:---:|:---:|---|
| /pcv | Yes | Yes | Verification |
| /coa | Yes | Yes | Verification |
| /pace | Yes | Yes | Verification |
| /improve | Yes | Yes | Verification |
| /quarto | Yes | Yes | Content |
| /readable | Yes | Yes | Content |
| /startup | — | Yes | Workflow |
| /dailysummary | — | Yes | Workflow |
| /weeklysummary | — | Yes | Workflow |
| /commit | — | Yes | Workflow |
| /simplify | — | Yes | Workflow |
| /audit | — | Yes | Verification |

**Instructor gets 6, student gets 12.** The split logic:
- Instructors need verification tools (teach methodology) and content tools (create materials).
- Students also need workflow tools (build research habits: daily documentation, session continuity, clean commits).

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

---

## Versioning Policy

- **v1.x** — Bug fixes, documentation improvements, config template updates. No new commands.
- **v2.0** — New commands only after classroom testing validates the concept. Each new command must pass the weekly-use test.
- **PCV upstream** — PCV files are Kay's upstream. We distribute v3.14 as-is. Version bumps come from Kay's repo; maintainer-only via `scripts/refresh-pcv-bundle.sh --version <tag>`. Student/user-facing install never touches the network for PCV.

---

## File Inventory

```
research-amp/                            Total: 33 files
├── README.md                            Root documentation
├── LICENSE                              MIT
├── CITATION.md                          BibTeX + attribution
├── EVIDENCE.md                          Empirical metrics
├── DESIGN.md                            This file
├── toolkit-config.md                    User configuration template
├── install.sh                           Dual-mode installer
├── instructor/
│   ├── README.md                        6-command quick start
│   └── guides/
│       ├── using-pcv-in-courses.md      Teaching guide
│       ├── using-coa-for-discussion.md  Teaching guide
│       └── using-pace-for-grading.md    Teaching guide
├── student/
│   ├── README.md                        Full suite quick start
│   └── bootstrap.md                     In-session installer
├── shared/commands/                     11 generalized commands
│   ├── coa.md                           Council of Agents
│   ├── pace.md                          Parallel Agent Consensus
│   ├── audit.md                         Citation & numerical audit
│   ├── improve.md                       Infrastructure scanner
│   ├── simplify.md                      Code review
│   ├── startup.md                       Session briefing
│   ├── dailysummary.md                  Daily work summary
│   ├── weeklysummary.md                 Weekly aggregation
│   ├── commit.md                        Intelligent git commits
│   ├── quarto.md                        Slide generation
│   └── readable.md                      Document extraction
│   └── runlog.md                        Longitudinal run observability (v1.1)
├── scripts/                             Shared helper scripts (v1.1)
│   └── emit_run_report.sh               Run instrumentation helper
├── tests/smoke/                         Smoke test fixtures (v1.1)
│   ├── audit_smoke.md, paper.md, sources/
│   ├── pace_source_verification.md, sales_fixture.csv
│   └── runlog_parser.md (v1.1)
├── references/                          JIT recipe files
│   └── processing_student_submissions.md (v1.1)
└── pcv/                                 PCV v3.14 (Kay's upstream; refresh via scripts/refresh-pcv-bundle.sh)
    ├── skill/ (6 files)
    └── agents/ (4 files)
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
- README.md — 3-problem student-facing rewrite + Panjwani disclaimer + /runlog + 13-command count
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
- Council session: `CC_Workflow/coa/council_sessions/coa_2026-04-19_help_command_design/`

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
- `CC_Workflow/evidence/command_performance_log.md` — debut invocation logged
- `plans/review_command_documentation_idea.md` — tracks the per-command-docs future use case

Bonus bug caught during I3 shell test: the spec's user field `outcome=match` collided with the script's native `outcome:` YAML key, producing duplicate keys. Renamed to `triage_result=match`. This is a lesson for future command specs — do not use field names that shadow the script's built-ins.
