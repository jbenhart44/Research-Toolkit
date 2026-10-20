# Evidence — Research Amp Toolkit

What each claim about this toolkit rests on, in three tiers: **reproducible** (you can rerun it), **measured**
(a count from the author's own logs, with how it was taken), and **observed** (one author's notes from real
use, not a benchmark). A claim that fits none of these is not made.

---

## 1. Reproducible: the release gates and their mutation checks

Run these yourself; CI runs them on Linux and macOS on every push (`.github/workflows/tests.yml`).

| What is checked | Command | Proof it can fail |
|---|---|---|
| Every command carries its contract; no absolute home path, credential, private email, or term from your private-token file anywhere in the tree | `python3 tests/check_toolkit.py` | `python3 tests/check_toolkit_mutations.py` — 14 planted defects, each must turn a named self-test case red |
| Every count and version on every page matches `install.sh` and `VERSION`, and every "N planted defects" matches its mutation file | `python3 tests/check_claims.py` | `python3 tests/check_claims_mutations.py` — 24 planted defects |
| Every place a command starts an agent names the model the role table gives it; the role table, its generated copies and the failure block agree | `python3 tests/check_models.py` (triage of its first run: `tests/model_gate_triage.md`) | `python3 tests/check_models_mutations.py` — 23 planted defects |
| The usage counter records every use and never breaks a session | `python3 hooks/usage_counter_selftest.py` | `python3 hooks/usage_counter_mutations.py` — 9 planted defects |
| The usage report merges and counts correctly | `python3 scripts/usage_counts.py --self-test` | `python3 scripts/usage_counts_mutations.py` — 10 planted defects |
| The installer gives a user every file the commands call, in every install mode, and a re-install keeps the user's config | `python3 tests/check_install.py` (real installs into temporary `HOME`s; every expectation derived from `install.sh` and the command files) | `python3 tests/check_install_mutations.py` — 16 planted defects |
| The run-report helper writes a well-formed report and one `run_log.csv` row, and never breaks the calling command | `python3 scripts/emit_run_report_selftest.py` | `python3 scripts/emit_run_report_mutations.py` — 15 planted defects |

A mutation check is the evidence that a green test means something: each planted defect leaves a working
program that behaves wrongly, and the matching self-test must name the case that caught it. A gate that has
never been watched failing has never been tested.

## 2. Measured: how often the author used each command

**Method:** `scripts/usage_counts.py` over the author's usage counter (from 2026-10-19) and, before that date,
the author's command log (headings `## /name — YYYY-MM-DD`, from 2026-04-02). Counts only; no task text.
**Caveat:** the older log deliberately skipped lightweight commands (`/commit`, `/readable`, `/startup`,
`/simplify`), so those rows are floors, not usage rates. Taken 2026-10-19.

| Command | Logged uses | First | Last |
|---|---:|---|---|
| /dailysummary | 357 | 2026-04-06 | 2026-10-19 |
| /coa | 164 | 2026-04-09 | 2026-10-18 |
| /pace | 59 | 2026-04-02 | 2026-10-18 |
| /improve | 24 | 2026-04-27 | 2026-10-12 |
| /quarto | 11 | 2026-04-19 | 2026-08-04 |
| /audit | 9 | 2026-04-23 | 2026-07-25 |
| /review | 3 | 2026-04-19 | 2026-05-03 |
| /pcv | 2 | 2026-10-06 | 2026-10-18 |
| /weeklysummary | 1 | 2026-05-12 | 2026-05-12 |
| /startup, /commit | 1 each (floors; see caveat) | | |

These describe one author's workflow. They show the commands are used for real work, not how well they work
for anyone else.

## 3. Observed: notes from real use (single author, not benchmarks)

- **CoA.** Council members given distinct professional personas (Skeptic, Economist, Practitioner and others)
  produced different analyses of the same question in three contamination tests the author ran in March 2026;
  the Chair synthesis separated convergence from genuine disagreement.
- **/review.** Its first real run (April 2026, on a 70-line design memo) took about 30 seconds per lens with
  three lenses in parallel, about 106K tokens in total, and each lens produced observations the other two did
  not. It shipped as v1.0 with no revisions after that run.
- **PACE.** Two independent players with coaching review surfaced errors a single pass missed, including an
  arithmetic error in a 48-item scoring and circular logic in model code. Most useful for checking existing
  work rather than generating new work.

---

## PCV Bundle Version

**Current bundled version:** PCV v3.14 (upstream by Dr. Michael G. Kay, 2026-04-18 release, bumped from v3.9 on 2026-04-19)

Dr. Kay's v3.14 release notes claim "approximately 3 times faster and using about half the number of tokens as previous versions." **This claim is upstream pending local remeasurement in the Research Amp Toolkit context** — we have not independently benchmarked PCV v3.14 against v3.9 in this toolkit. Benchmarking is not part of the install smoke test; it would require a controlled comparison with matched charges and matched model configurations, which has not been scheduled.

Bundle provenance is tracked in `pcv/.upstream-version`, `pcv/.upstream-sha`, and `pcv/.upstream-fetched-at`. Drift detection via `scripts/check-pcv-upstream.sh`.

---

## Evidence Architecture

Instrumented commands produce a structured run report with YAML frontmatter at the end of each run. Reports accumulate in tool-specific directories and are indexed in a central CSV for cross-tool aggregation.

1. You run a command on a real task.
2. The command does its work.
3. As its final step, it writes a run report with structured metadata and appends one row to `run_log.csv`:
   - `/pace` and `/coa` write both themselves, into your `evidence_dir` (set by `/setup`; default `.toolkit/evidence`).
   - `/audit`, `/commit`, `/dailysummary`, `/help`, `/improve`, `/runlog` and `/startup` call the run-report helper that `install.sh` puts in `~/.claude/toolkit/scripts/`. `/dailysummary` and `/startup` pass your `evidence_dir`; the other five write to `<project>/.toolkit/evidence`, so a changed `evidence_dir` does not reach their rows yet.
4. Run `/improve --tools` or `/runlog` to see aggregate statistics across runs.

**Before v2.0.2** the installer did not copy the helper, and those seven commands called it at a path that exists only in a clone of this repository. On a user's machine they wrote no report and no row. Re-run `install.sh` to receive the fix; `tests/check_install.py` now fails if a command calls a script the installer does not copy.

You don't need to understand the schema to use the tools; collection is automatic. After 5+ runs, aggregate statistics start to mean something. See [QUICKSTART.md](QUICKSTART.md) for calibration tasks.

---

## Methodology Notes

- **Same-model caveat:** All agents in CoA and PACE use the same underlying Claude model. Convergence between agents does not constitute independent validation — it indicates consistency within the model's reasoning space. Cross-model validation (via Gemini in CoA) partially addresses this.
- **Token estimates:** Character count / 4 approximation. Valid for relative comparison across runs, not absolute cost measurement.
- **Selection bias:** The measured and observed tiers come from a single researcher's workflow. Generalizability to other research contexts has not been formally tested.
