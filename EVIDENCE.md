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
| Every count and version on every page matches `install.sh` and `VERSION` (a count wrapped across a line break included), and every "N planted defects" matches its mutation file | `python3 tests/check_claims.py` | `python3 tests/check_claims_mutations.py` — 27 planted defects |
| Every place a command starts an agent names the model the role table gives it; the role table, its generated copies and the failure block agree | `python3 tests/check_models.py` (triage of its first run: `tests/model_gate_triage.md`) | `python3 tests/check_models_mutations.py` — 25 planted defects |
| The usage counter records every use and never breaks a session | `python3 hooks/usage_counter_selftest.py` | `python3 hooks/usage_counter_mutations.py` — 9 planted defects |
| The usage report merges and counts correctly | `python3 scripts/usage_counts.py --self-test` | `python3 scripts/usage_counts_mutations.py` — 10 planted defects |
| The installer gives a user every file the commands call, every skill and council seat in the modes that ship them, every optional hook with `--hooks` and none without, registers no hook, leaves no backup inside `~/.claude/skills/`, and a re-install keeps the user's config | `python3 tests/check_install.py` (real installs into temporary `HOME`s; every expectation derived from `install.sh` and the command files) | `python3 tests/check_install_mutations.py` — 38 planted defects |
| The run-report helper writes a well-formed report and one `run_log.csv` row, and never breaks the calling command | `python3 scripts/emit_run_report_selftest.py` | `python3 scripts/emit_run_report_mutations.py` — 15 planted defects |
| The hooks' config reader reads keys, lists and comments as `/setup` writes them, and matches a path entry as whole names | `python3 hooks/_toolkit_config_selftest.py` | `python3 hooks/_toolkit_config_mutations.py` — 18 planted defects |
| `protect_files` blocks every way of writing a protected file, `NotebookEdit` included, and allows every read | `python3 hooks/protect_files_selftest.py` | `python3 hooks/protect_files_mutations.py` — 20 planted defects |
| `token_budget_guard` counts whole prompts per session and asks past the limit | `python3 hooks/token_budget_guard_selftest.py` | `python3 hooks/token_budget_guard_mutations.py` — 12 planted defects |
| `summary_folder_guard` notes a dated summary outside the configured folders and nothing else | `python3 hooks/summary_folder_guard_selftest.py` | `python3 hooks/summary_folder_guard_mutations.py` — 10 planted defects |
| The `/coa` evidence-path check gives the Julia original's verdict on every input in the golden file | `python3 scripts/check_coa_evidence_paths.py --self-test` (against `tests/golden/check_coa_evidence_paths.json`) | `python3 scripts/check_coa_evidence_paths_mutations.py` — 11 planted defects |
| The heading check finds sibling sections with one title and ignores every false-positive class found in its first full-corpus run | `python3 scripts/check_heading_collisions.py --self-test` | `python3 scripts/check_heading_collisions_mutations.py` — 17 planted defects |
| The scratchpad check finds content that exists only in the scratchpad, whatever it is named | `python3 scripts/check_scratchpad_leak.py --self-test` | `python3 scripts/check_scratchpad_leak_mutations.py` — 10 planted defects |
| The registration printer gives every shipped hook an unconditional entry and writes no file | `python3 scripts/register_hooks.py --self-test` | `python3 scripts/register_hooks_mutations.py` — 8 planted defects |
| The `/guard-hook` runner refuses an unauthored or failing guard, catches an inert self-test, and audits six traps | `python3 shared/skills/guard-hook/assets/guard_hook_selftest.py` | `python3 shared/skills/guard-hook/assets/guard_hook_mutations.py` — 10 planted defects |
| The `/bulletproof` runner refuses a suite no mutation names or the runner skips, and matches f-string check names | `python3 shared/skills/bulletproof/assets/bulletproof_selftest.py` | `python3 shared/skills/bulletproof/assets/bulletproof_mutations.py` — 10 planted defects |
| `/acquire` refuses HTML for a PDF, a DOI that names another paper, and a sparse extraction; never overwrites; reads an HTTP 400 as a malformed query; finds a claim across a line break | `python3 scripts/acquire.py --self-test` | `python3 scripts/acquire_mutations.py` — 20 planted defects |
| A page transcription is refused unless its pages, text and (with two readers) every number agree, page by page | `python3 scripts/check_transcription.py --self-test` | `python3 scripts/check_transcription_mutations.py` — 13 planted defects |
| Every command and skill carries a chatbot label, and the landing page's chatbot prompts match what the commands say | `python3 scripts/render_chatbot_prompts.py --self-test` | `python3 scripts/render_chatbot_prompts_mutations.py` — 15 planted defects |
| The stall ledger records every stall with its model, and `recent` exits 1 when one is in the window | `python3 scripts/agent_stalls.py --self-test` | `python3 scripts/agent_stalls_mutations.py` — 11 planted defects |
| The headless fallback refuses fable and a full model ID, never skips permissions, and grants Bash only when asked | `python3 scripts/headless_agent_selftest.py` (a stand-in `claude`; no real call) | `python3 scripts/headless_agent_mutations.py` — 10 planted defects |
| The `/list-maker` ledger never reuses a number, keeps deferred work visible, and exits 3 when the active list is cleared | `python3 shared/skills/list-maker/assets/list_maker_selftest.py` | `python3 shared/skills/list-maker/assets/list_maker_mutations.py` — 16 planted defects |
| `/step-by-step` refuses to call a walkthrough done while an item is unexplained, and refuses a date git would ignore | `python3 shared/skills/step-by-step/assets/step_by_step_selftest.py` (real temporary git repositories) | the same file, Part B: each of its 10 guards removed in turn must turn its case green |

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
| /daily-summary | 357 | 2026-04-06 | 2026-10-19 |
| /coa | 164 | 2026-04-09 | 2026-10-18 |
| /pace | 59 | 2026-04-02 | 2026-10-18 |
| /improve | 24 | 2026-04-27 | 2026-10-12 |
| /quarto | 11 | 2026-04-19 | 2026-08-04 |
| /audit | 9 | 2026-04-23 | 2026-07-25 |
| /review | 3 | 2026-04-19 | 2026-05-03 |
| /pcv | 2 | 2026-10-06 | 2026-10-18 |
| /weekly-summary | 1 | 2026-05-12 | 2026-05-12 |
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
   - `/audit`, `/commit`, `/daily-summary`, `/help`, `/improve`, `/run-log` and `/startup` call the run-report helper that `install.sh` puts in `~/.claude/toolkit/scripts/`. `/daily-summary` and `/startup` pass your `evidence_dir`; the other five write to `<project>/.toolkit/evidence`, so a changed `evidence_dir` does not reach their rows yet.
4. Run `/improve --tools` or `/run-log` to see aggregate statistics across runs.

**Before v2.0.2** the installer did not copy the helper, and those seven commands called it at a path that exists only in a clone of this repository. On a user's machine they wrote no report and no row. Re-run `install.sh` to receive the fix; `tests/check_install.py` now fails if a command calls a script the installer does not copy.

You don't need to understand the schema to use the tools; collection is automatic. After 5+ runs, aggregate statistics start to mean something. See [QUICKSTART.md](QUICKSTART.md) for calibration tasks.

---

## Methodology Notes

- **Same-model caveat:** All agents in CoA and PACE use the same underlying Claude model. Convergence between agents does not constitute independent validation — it indicates consistency within the model's reasoning space. Cross-model validation (via Gemini in CoA) partially addresses this.
- **Token estimates:** Character count / 4 approximation. Valid for relative comparison across runs, not absolute cost measurement.
- **Selection bias:** The measured and observed tiers come from a single researcher's workflow. Generalizability to other research contexts has not been formally tested.
