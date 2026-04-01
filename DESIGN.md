# Design Rationale — AI-Assisted Research Toolkit

**Version:** 1.0
**Date:** 2026-03-31
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

### Why 11 Commands

The toolkit started with 15 commands built during PhD research. Assessment:

| Tier | Commands | Disposition |
|------|----------|-------------|
| **Tier 1 — Showcase** | /pcv, /coa, /pace, /pcv-research, /improve, /simplify | Core methodology — included |
| **Tier 2 — Workflow** | /startup, /dailysummary, /weeklysummary, /commit | Daily-use productivity — included |
| **Tier 3 — Content** | /quarto, /pdftotxt | Document generation — included |
| **Excluded** | /cbb, /chunker, /dualsimrunner | Domain-specific (basketball betting, TLC data extraction, city simulation) — not generalizable |

11 commands. The 12th (pcv-research) was initially omitted from Session 1 and added in Session 2 after confirming it generalizes cleanly.

### Persona-Command Mapping

| Command | Instructor (`--minimal`) | Student (full) | Layer |
|---------|:---:|:---:|---|
| /pcv | Yes | Yes | Verification |
| /coa | Yes | Yes | Verification |
| /pace | Yes | Yes | Verification |
| /improve | Yes | Yes | Verification |
| /quarto | Yes | Yes | Content |
| /pdftotxt | Yes | Yes | Content |
| /startup | — | Yes | Workflow |
| /dailysummary | — | Yes | Workflow |
| /weeklysummary | — | Yes | Workflow |
| /commit | — | Yes | Workflow |
| /simplify | — | Yes | Workflow |
| /pcv-research | — | Yes | Verification |

**Instructor gets 6, student gets 12.** The split logic:
- Instructors need verification tools (teach methodology) and content tools (create materials).
- Students also need workflow tools (build research habits: daily documentation, session continuity, clean commits).
- `/pcv-research` is student-only because it's a research instrument for studying PCV itself — instructors who want it can upgrade with `bash install.sh`.

---

## Tradeoff Log

### Accepted into v1.0

| Decision | Rationale |
|----------|-----------|
| **Bundle PCV v3.9 directly** | Users need it to work immediately. Linking to Kay's repo adds a dependency and version-sync risk. We distribute as-is; improvements go upstream. |
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
| **Safety hooks in generic toolkit** | Internal | The `protect_files` / `git_safety` / `no_coauthor` hooks are project-specific safety nets. Generic users don't have the same protected files. Including hooks that reference nonexistent files confuses new users. | **Power users configure their own.** |
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
| `/coa` | ECL-lite scorecard, PRECEDENT_INDEX, `CC_Workflow/coa/personas/` paths | Built-in roster fallback works out of the box. Session tracking is v2+. |
| `/pace` | JIT reference gate, per-task cost benchmarks, citation tier verification | Core 4-agent pattern is fully generic. Cost benchmarks were project-specific. |
| `/improve` | Read-only file list (Worker Voice .tex), `plans/` folder assumptions | Works on any project with a CLAUDE.md. First-time mode added for projects without one. |
| `/startup` | Multi-directory summary scanning (4 project folders), priority rules, MCP monitoring | Config-driven: reads `workstreams` and `summary_folder` from toolkit-config.md. |
| `/dailysummary` | Parameter-specific numerical verification, incident documentation | Generic numerical accuracy check preserved. Sonnet fallback added. |
| `/commit` | Project folder categorization (Strategic Driver, MVP Class Paper, etc.) | Uses git diff to infer structure. No hardcoded folder names needed. |
| `/pcv-research` | RAM check, Julia process monitoring, NSF/dissertation purpose framing | Generic "research instrument" framing. Process check simplified to `free -h`. |
| `/quarto` | NC State theme references | BYOT architecture. Theme is a user-provided SCSS file, not bundled. |
| `/pdftotxt` | Hardcoded `/tmp/` path | Cross-platform temp path via Python `tempfile`. |

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
- **PCV upstream** — PCV files are Kay's upstream. We distribute v3.9 as-is. Version bumps come from Kay's repo.

---

## File Inventory

```
ai-research-toolkit/                     Total: 33 files
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
├── shared/commands/                     12 generalized commands
│   ├── coa.md                           Council of Agents
│   ├── pace.md                          Parallel Agent Consensus
│   ├── pcv-research.md                  PCV Research Protocol
│   ├── improve.md                       Infrastructure scanner
│   ├── simplify.md                      Code review
│   ├── startup.md                       Session briefing
│   ├── dailysummary.md                  Daily work summary
│   ├── weeklysummary.md                 Weekly aggregation
│   ├── commit.md                        Intelligent git commits
│   ├── quarto.md                        Slide generation
│   └── pdftotxt.md                      Document extraction
└── pcv/                                 PCV v3.9 (Kay's upstream)
    ├── skill/ (6 files)
    └── agents/ (4 files)
```
