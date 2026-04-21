# /help — Smoke Fixture

**Purpose**: Verify that `/help` classifies input shape correctly and produces output within the chunk budget before regressions reach users.

**Run manually**: Invoke `/help` with each test input below in a Claude Code terminal. Compare output against the expected shape.

**Not yet automated**: The triage classification requires Claude to interpret natural language, so automated assertion is non-trivial. This fixture is a *specification*, not a runnable test script.

---

## Test Case C1 — Shape A, obvious match

**Input**:
```
/help I need to commit my work
```

**Expected classification**: Shape A (well-formed — object="work", verb="commit", state="ready to save")

**Expected clarifications**: 0

**Expected output** (3 functional chunks, within ≤5 budget):

```
Match: /commit — analyzes staged changes and creates logical separate commits.
Run: /commit   `Verify: tests/smoke/commit_grouping.md`

Skip /dailysummary — that's for capturing today's work narrative, not committing code changes.
```

**Expected CSV row** (after `emit_run_report.sh`):
```csv
...,help,...,input_shape=A,recommendations=commit,clarifying_questions=0,triage_result=match,...
```

**Pass condition**:
- Primary recommendation is `/commit` (and only `/commit`)
- Zero clarifying questions asked
- Output is ≤5 functional chunks
- CSV row has `input_shape=A` and `recommendations=commit` (single command, comma-joined list format)

---

## Test Case C2 — Shape A with prerequisite

**Input**:
```
/help I have a paper and I'm worried about citations, sources are on disk
```

**Expected classification**: Shape A (well-formed — object="paper", verb="verify citations", state="sources available")

**Expected clarifications**: 0

**Expected output** (5 functional chunks, at budget):

```
Primary: /audit — verifies every citation exists on disk AND every quoted number matches the source.
Run: /audit <path/to/your_paper.md> --sources <path/to/sources/>   `Verify: tests/smoke/audit_smoke.md`

Prereq: /readable first IF any source is still a raw PDF (no .txt extraction).
Run: /readable <path/to/sources/>

Skip /pace — it's for decisions with multiple valid answers, not citation checking.
```

**Expected CSV row**:
```csv
...,help,...,input_shape=A,recommendations=audit,readable,clarifying_questions=0,triage_result=match,...
```

**Pass condition**:
- Primary recommendation is `/audit`
- Prerequisite recommendation is `/readable` (conditionally framed)
- Skip entry is `/pace` (one skip, not multiple)
- Output is ≤5 functional chunks
- CSV `recommendations` field is `audit,readable` (comma-joined, no spaces, no brackets)

---

## Test Case C3 — Shape C, bare input triggers scaffold menu

**Input**:
```
/help
```

**Expected classification**: Shape C (bare)

**Expected clarifications**: scaffold menu (4 options + escape hatch), NOT "what are you trying to do?" (too open) and NOT a full 12-command inventory dump (Hick's Law failure).

**Expected first output** (5 chunks, including the menu):

```
What are you trying to do? Pick the closest:
1. Verify something (a citation, a number, a claim)
2. Decide between options (architecture, direction, tradeoff)
3. Capture or find project state (summary, startup, commit)
4. Produce a deliverable (slides, extracted text, simplified code)
5. Something else — describe it in one line.
```

**Follow-up input** (student picks 3):
```
3
```

**Expected follow-up output** (3 chunks):

```
Primary: /startup — shows where every workstream left off, with recommended next action.
Run: /startup

Alt: /dailysummary if you want to close out today's work instead of resume prior work.
Run: /dailysummary
```

**Expected CSV row** (after final recommendation):
```csv
...,help,...,input_shape=C,recommendations=startup,clarifying_questions=1,triage_result=match,...
```

**Pass condition**:
- Scaffold menu offers exactly 4 options + 1 escape ("Something else")
- Does NOT dump the full 12-command inventory
- Does NOT ask an open-ended "what are you trying to do?" with no scaffolding
- After category selection, recommends 1-2 commands with total output ≤5 chunks
- CSV `clarifying_questions=1` (the scaffold menu counts as one clarification round)

---

## Test Case C4 — No match (out-of-scope input)

**Input**:
```
/help my Julia simulation keeps crashing with out-of-memory errors
```

**Expected classification**: out-of-scope (toolkit is research-workflow-focused, not runtime-focused)

**Expected clarifications**: 0

**Expected output** (2 functional chunks, does NOT leak project-specific paths):

```
No match. The toolkit is research-workflow-focused, not simulation-runtime-focused. For runtime/RAM issues, check your project's local reference docs (CLAUDE.md often has a simulation section).

If you want structured debugging with multiple perspectives on WHY it's crashing: /coa — spawn a panel (perf + systems + architecture lenses). Heavier tool than the situation may need.
```

**Expected CSV row**:
```csv
...,help,...,input_shape=A,recommendations=,clarifying_questions=0,triage_result=no_match,...
```

**Pass condition**:
- No recommendation is forced
- Redirects to "check your project's local reference docs" WITHOUT naming specific Jake-only paths like `CC_Workflow/references/...`
- Offers `/coa` as an optional heavier tool, clearly framed as potentially overkill
- CSV `triage_result=no_match` (not `match` or `needs_escalation`)
- `recommendations` field is empty string (no command was primary)

---

## What This Fixture Does NOT Test

1. **Longitudinal pedagogical value** — whether the SKIP section builds student mental models over a semester. This requires a semester of usage data (Cognitive Ergonomist blind spot in council review).
2. **Premise validation** — whether students actually misroute between commands today. Deferred to live signal from `run_log.csv` per the command's success metrics.
3. **Automated pass/fail** — output shape requires Claude's classification, which is non-deterministic. This fixture is a specification for manual comparison, not a CI test.
4. **Input-parsing edge cases** — multi-line inputs, inputs with code blocks, inputs with URLs. These are v0.3 work if they show up in `run_log.csv`.

---

## Regression Signals

If future `/help` invocations in `run_log.csv` show any of these, open a v0.3 revision:

- **R1 — Inventory drift**: `recommendations` includes a command not present in `ls ai-research-toolkit/shared/commands/` (plus `/pcv`)
- **R2 — Clarification overrun**: `clarifying_questions=2` or more (should never happen per the hard cap)
- **R3 — Budget overrun**: rendered output exceeds 5 functional chunks (not directly observable in CSV; requires qualitative review of sample transcripts)
- **R4 — Project-path leak**: output includes `CC_Workflow/references/...` or other Jake-specific paths (not directly observable in CSV; requires qualitative review)
- **R5 — Chain-and-execute**: output includes any `[y/n]` prompt offering to run the recommended command

---

## Related Artifacts

- Command file: `ai-research-toolkit/shared/commands/help.md`
- v0.2 design spec: `plans/help_command_draft.md`
- Council session: `CC_Workflow/coa/council_sessions/coa_2026-04-19_help_command_design/`
