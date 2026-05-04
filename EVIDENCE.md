# Evidence — Research Amp Toolkit

This document provides empirical evidence for the toolkit's effectiveness, drawn from real usage during PhD research (2025-2026). All metrics are from actual sessions, not synthetic benchmarks.

---

## PCV Bundle Version

**Current bundled version:** PCV v3.14 (upstream by Dr. Michael G. Kay, 2026-04-18 release, bumped from v3.9 on 2026-04-19)

Kay's v3.14 release notes claim "approximately 3 times faster and using about half the number of tokens as previous versions." **This claim is upstream pending local remeasurement in the Research Amp Toolkit context** — we have not independently benchmarked PCV v3.14 against v3.9 in this toolkit. Benchmarking is not part of the install smoke test; it would require a controlled comparison with matched charges and matched model configurations, which has not been scheduled.

Bundle provenance is tracked in `pcv/.upstream-version`, `pcv/.upstream-sha`, and `pcv/.upstream-fetched-at`. Drift detection via `scripts/check-pcv-upstream.sh`.

---

## CoA (Council of Agents)

**Source:** 3 contamination tests + ECL-lite scoring (March 2026)

The Council of Agents spawns specialists with distinct professional perspectives. Contamination tests verify that council members produce genuinely independent analyses rather than echo-chamber agreement.

| Metric | Value | Source |
|--------|-------|--------|
| Contamination tests conducted | 3 | Contamination test files saved to your project's `coa/council_sessions/` directory (auto-created on first /coa run) |
| Independent perspective rate | Council members produce distinct analyses | ECL-lite scorecard methodology |
| Cross-model validation | Gemini used as external check (optional) | Cross-model MCP integration |

**Key finding:** Council members with well-defined professional personas (Skeptic, Economist, Practitioner, etc.) produce meaningfully different analyses of the same question. The Chair synthesis correctly identifies convergence vs. genuine disagreement.

---

## /review (Three-Lens Document Review)

**Source:** 1 smoke-test invocation (April 2026, command shipped v1.0)

`/review` reads a document through three parallel expert lenses (Skeptic + Practitioner + Editor) and synthesizes into takeaways, project-relevance, and 3 concrete implications. The three lenses are the mandatory-Skeptic-and-Practitioner pair from the CoA ROSTER plus Editor (the ROSTER's designated Historian-replacement for prose).

| Metric | Value | Source |
|--------|-------|--------|
| Shipped version | v1.0 (no post-smoke revisions needed) | `shared/commands/review.md` |
| Smoke-test document | Kay's "Text-Based Formats for Claude Code" (70 lines, advisor-authored) | `reviews/review_2026-04-19_text_based_formats_for_claude_code.md` |
| Parallel agent runtime | ~30 seconds per lens (3 in parallel) | Smoke-test run log |
| Total tokens | ~106K (within projected 80-120K envelope) | Same |
| Lens distinctness | Each lens produced non-overlapping observations (no convergence-to-sameness) | Same |
| Unique insights per lens | Skeptic: 2 failure modes the others missed; Practitioner: only-one-with-action-items (3 DO entries with effort estimates); Editor: surfaced the doc's sharpest single sentence ("structural vs procedural transparency") that the other two skipped | Same |

**Key finding:** The three-lens formulation produces genuinely different readings of the same document — the Editor's rhetorical insight about thesis-vs-apparent-thesis is the kind of observation a single-agent summary never surfaces. The Chair synthesis is easy to write inline without a 4th agent because the convergence/divergence points emerge cleanly from three reports.

**Design reference for future command documentation:** The /review output format — 5–10 takeaways + project relevance + 3 implications per lens + Chair synthesis — is under consideration as a template for per-command documentation on the public toolkit website. Running /review against each command's own SKILL/command file produces a reader-facing description that is both skeptical and actionable in a way that hand-written docs typically aren't.

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

**Source:** Hundreds of production sessions (2025–2026)

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

**Storage** (paths are relative to your project's workflow directory; commands create them automatically on first use — no stub directories ship with the toolkit):
- PACE reports: `evidence/pace_runs/`
- CoA reports: `coa/council_sessions/` (YAML frontmatter added to session files)
- CSV index: `evidence/run_log.csv`

**For new users:** You don't need to understand the schema to use the tools. Evidence collection is automatic. After 5+ runs, run `/improve --tools` to see your first aggregate statistics. After 10+ runs, trends become visible. See [QUICKSTART.md](QUICKSTART.md) for calibration tasks and baseline benchmarks.

---

## Methodology Notes

- **Same-model caveat:** All agents in CoA and PACE use the same underlying Claude model. Convergence between agents does not constitute independent validation — it indicates consistency within the model's reasoning space. Cross-model validation (via Gemini in CoA) partially addresses this.
- **Token estimates:** Character count / 4 approximation. Valid for relative comparison across runs, not absolute cost measurement.
- **Selection bias:** These metrics come from a single researcher's workflow. Generalizability to other research contexts has not been formally tested.
