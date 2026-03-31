# Evidence — AI-Assisted Research Toolkit

This document provides empirical evidence for the toolkit's effectiveness, drawn from real usage during PhD research (2025-2026). All metrics are from actual sessions, not synthetic benchmarks.

---

## PCV (Plan-Construct-Verify)

**Source:** PCV-Research Protocol, 14 runs (March 2026)

The PCV-Research protocol runs planning through parallel depth-first and breadth-first strategies (2x2 design: 2 DF instances, 2 BF instances), each using 3 agents (proposer A, proposer B, decider C), to study how AI agents navigate planning decisions.

| Metric | Value | Source |
|--------|-------|--------|
| Total PCV-Research runs | 14 | Run logs in `plans/research_runs/` |
| Cross-instance convergence (DF) | 42-87% full agreement | Instrumentation CSVs |
| Cross-instance convergence (BF) | 33-94% full agreement | Instrumentation CSVs |
| DIVERGE outcomes (DF avg) | 0-1 per run | Agent C decisions |
| DIVERGE outcomes (BF avg) | 1-3 per run | Agent C decisions |

**Key finding:** Depth-first mode produces more consistent, actionable plans for implementation-heavy charges. Breadth-first mode reveals enabling connections between questions but introduces path dependency risk. Task-type matching matters more than mode preference.

**Task-type guidance (from 14-run corpus):**

| Task Type | Preferred Mode | Evidence |
|-----------|---------------|----------|
| Well-scoped engineering | DF | Run 5: DF 87.5% vs BF 43.8% |
| Cascading architecture | BF | Run 4: BF 93.8% vs DF 68.8% |
| Analysis/report | Full 2+2 | Default — both modes add value |
| Under-specified charge | Rewrite charge first | Run 8: both <50% |

---

## CoA (Council of Agents)

**Source:** 3 contamination tests + ECL-lite scoring (March 2026)

The Council of Agents spawns specialists with distinct professional perspectives. Contamination tests verify that council members produce genuinely independent analyses rather than echo-chamber agreement.

| Metric | Value | Source |
|--------|-------|--------|
| Contamination tests conducted | 3 | `CC_Workflow/coa/council_sessions/contamination_test_2026-03-25.md` |
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
| Error catches (single-agent would miss) | Arithmetic errors on 48+ item scoring, circular logic in model code | CBB session 2026-03-22, Phase 9b review |
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

## Methodology Notes

- **Same-model caveat:** All agents in PCV-Research, CoA, and PACE use the same underlying Claude model. Convergence between agents does not constitute independent validation — it indicates consistency within the model's reasoning space. Cross-model validation (via Gemini in CoA) partially addresses this.
- **Token estimates:** Character count / 4 approximation. Valid for relative comparison across runs, not absolute cost measurement.
- **Selection bias:** These metrics come from a single researcher's workflow. Generalizability to other research contexts has not been formally tested.
