# Evidence — AI-Assisted Research Toolkit

This document provides empirical evidence for the toolkit's effectiveness, drawn from real usage during PhD research (2025-2026). All metrics are from actual sessions, not synthetic benchmarks.

---

## CoA (Council of Agents)

**Source:** 3 contamination tests + ECL-lite scoring (March 2026)

The Council of Agents spawns specialists with distinct professional perspectives. Contamination tests verify that council members produce genuinely independent analyses rather than echo-chamber agreement.

| Metric | Value | Source |
|--------|-------|--------|
| Contamination tests conducted | 3 | Contamination test files in `coa/council_sessions/` |
| Independent perspective rate | Council members produce distinct analyses | ECL-lite scorecard methodology |
| Cross-model validation | Gemini used as external check (optional) | Cross-model MCP integration |

**Key finding:** Council members with well-defined professional personas (Skeptic, Economist, Practitioner, etc.) produce meaningfully different analyses of the same question. The Chair synthesis correctly identifies convergence vs. genuine disagreement.

---

## PACE (Parallel Agent Consensus Engine)

**Source:** 20+ verification tasks (February-March 2026)

PACE runs tasks through two independent players with coaching review, then cross-compares for verification through redundancy.

| Metric | Value | Source |
|--------|-------|--------|
| Verification tasks completed | 20+ | Session logs |
| Error catches (single-agent would miss) | Arithmetic errors on 48+ item scoring, circular logic in model code | verification session, model review task |
| Convergence rate across players | Typically 70-90% on well-specified tasks | PACE run reports |

**Key finding:** PACE catches errors that single-agent workflows miss. The two-player + two-coach architecture provides redundancy without the overhead of full PCV planning. Most effective for verification tasks (checking existing work) rather than generation tasks (creating new work).

---

## Workflow Commands

**Source:** 40+ sessions (January-March 2026)

| Command | Usage Count | Key Benefit |
|---------|------------|-------------|
| /dailysummary | 30+ summaries | Prevents knowledge loss across sessions |
| /weeklysummary | 5+ weekly rollups | Surfaces dormant workstreams and stale TODOs |
| /startup | Every session | Reduces "where was I?" time from minutes to seconds |
| /commit | Every commit session | Logical grouping catches mixed-concern commits |
| /simplify | 10+ reviews | 5-lens analysis finds issues human review misses |
| /improve | 5+ audits | Self-reflective infrastructure keeps toolkit evolving |

---

## Evidence Architecture (v1.0, 2026-03-31)

Every PACE and CoA run automatically produces a structured run report with YAML frontmatter. Reports accumulate in tool-specific directories and are indexed in a central CSV for cross-tool aggregation.

**How it works:**
1. You run `/pace` or `/coa` on a real task
2. The tool does its work (verification or council analysis)
3. As its final step, it auto-generates a run report with structured metadata
4. The report is saved to a tool-specific directory and a row is appended to `run_log.csv`
5. Run `/improve --tools` anytime to see aggregate statistics across all runs

**Storage:**
- PACE reports: `evidence/pace_runs/`
- CoA reports: `coa/council_sessions/` (YAML frontmatter added to session files)
- CSV index: `evidence/run_log.csv`

> These paths are relative to your project's workflow directory. Create them as needed — commands will create directories automatically on first use.

**For new users:** You don't need to understand the schema to use the tools. Evidence collection is automatic. After 5+ runs, run `/improve --tools` to see your first aggregate statistics. After 10+ runs, trends become visible. See [QUICKSTART.md](QUICKSTART.md) for calibration tasks and baseline benchmarks.

---

## Methodology Notes

- **Same-model caveat:** All agents in CoA and PACE use the same underlying Claude model. Convergence between agents does not constitute independent validation — it indicates consistency within the model's reasoning space. Cross-model validation (via Gemini in CoA) partially addresses this.
- **Token estimates:** Character count / 4 approximation. Valid for relative comparison across runs, not absolute cost measurement.
- **Selection bias:** These metrics come from a single researcher's workflow. Generalizability to other research contexts has not been formally tested.
