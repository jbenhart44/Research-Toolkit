---
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(wc:*)
description: Socratic triage — ask 0-1 clarifying questions, then recommend 1-3 toolkit commands. Traffic cop, not driver. EXPERIMENTAL (v0.2, shipped 2026-04-19 without premise pilot — success pending end-of-fall evaluation).
---

# /help — Socratic Triage for the Research Amp Toolkit

> **When to use**: You're stuck and not sure which of the toolkit's 13 commands fits your situation. Describe it in one line; /help asks a clarifying question if needed and points you to the right command(s). For the paradox-of-choice problem at 11pm on a Pro plan.

A triage tool. `/help` recommends commands — it does NOT execute them. The student runs the recommended command themselves. This preserves the "you think, tools amplify" contract of the Research Amp Toolkit.

**Status**: EXPERIMENTAL (v0.2). Shipped without the 5-student premise pilot the design council recommended, on a deliberate bet that live usage signals (see "Success metrics" below) will resolve the premise faster than a pilot would. If success metrics don't fire by end of fall 2026, this command is a candidate for removal.

## Usage

```
/help <one-line description of your situation>   # well-formed input
/help I'm stuck                                   # partial input — triggers 1 clarification
/help                                             # bare — triggers scaffold menu
```

## Protocol

### STEP 1 — Classify input shape

| Shape | Trigger | Next step |
|---|---|---|
| **A** — Well-formed (object, verb, state inferrable) | "I have a 20-page PDF and I'm worried about citations" | Skip to STEP 3 |
| **B** — Partial (verb or state present, key info missing) | "I'm stuck on my lit review" | One targeted clarification, then STEP 3 |
| **C** — Bare/fuzzy (empty, "I'm stuck", "this isn't working") | "/help" or "/help I'm stuck" | Scaffold menu |

### STEP 2 — Clarification (0, 1, or scaffold)

**Shape A**: no clarification. Proceed to STEP 3.

**Shape B**: exactly ONE question. The test: *if the answer doesn't change which command I recommend, don't ask it.* Bad: "tell me more." Good: "are you WRITING the paper, or READING it to cite from?"

**Shape C**: offer a 4-option scaffold menu (Hick's Law: 4 options = log2(4)=2 bits vs 12-command log2(12)=3.6 bits, 45% faster to selection, fits within Miller-under-stress ceiling of 5 chunks).

```
What are you trying to do? Pick the closest:
1. Verify something (a citation, a number, a claim)
2. Decide between options (architecture, direction, tradeoff)
3. Capture or find project state (summary, startup, commit)
4. Produce a deliverable (slides, extracted text, simplified code)
5. Something else — describe it in one line.
```

Whichever they pick becomes the input to STEP 3. **Hard cap: at most one clarification question total.** Two = conversation, not diagnostic.

### STEP 3 — Recommend 1-3 commands (≤5 functional chunks output)

**Output budget: maximum 5 functional chunks** rendered. A functional chunk = a thing the stressed reader must hold in working memory.

| Element | Chunks |
|---|---|
| 1 primary recommendation (command + why + invocation) | 1 |
| Optional prerequisite command | 1 |
| Optional alternative command (when ambiguous between two) | 1 |
| At most 1 SKIP entry (STEP 4) | 1 |
| Per-recommendation smoke-fixture pointer | 0 (trailing monospace, not a chunk) |

**Format per recommendation**:
- **Command** (`/xxx`)
- **One-sentence why** it matches the specific situation
- **Invocation hint**: `Run: /xxx <args>` with placeholders
- **Smoke pointer** (only if fixture exists): trailing line `Verify first: ai-research-toolkit/tests/smoke/xxx_smoke.md`

If more than 3 commands match, your STEP 2 question didn't narrow enough — go back to STEP 2.

### STEP 4 — Name ONE command to SKIP (pedagogical, capped)

For the single most-likely-mis-selected neighbor, name it in one sentence:

> *"Skip /pace — it's for decisions with multiple valid answers, not citation checking."*

**Cap at ONE skip entry.** Multiple skips become a study aid rather than a routing aid (transforms `/help` from triage to comparison-shopping).

**Omit STEP 4 entirely** if the primary recommendation is unambiguous. Strawman rejections add cognitive load without pedagogical value.

### STEP 5 — Emit run report

Append one row to `.toolkit/evidence/run_log.csv` via `emit_run_report.sh`:

```bash
bash ai-research-toolkit/scripts/emit_run_report.sh \
  --command help \
  --run-dir ".toolkit/evidence/help_runs/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "triage: <first 80 chars of user's one-liner>" \
  --fields "input_shape=A|B|C recommendations=cmd1,cmd2 clarifying_questions=0|1 triage_result=match|no_match|needs_escalation"
```

**Field encoding rules**:
- `recommendations` is a **comma-joined list, no spaces, no JSON brackets** (`audit,readable` ✓ not `[audit, readable]` ✗). The `--fields` parser tokenizes on whitespace; JSON lists break it silently.
- Use `triage_result` (NOT `outcome`) for the user-facing field, because `outcome` collides with the script's native YAML key.

### STEP 6 — Exit without executing

Do NOT offer to run the recommended command.

**One documented exception**: if exactly ONE command is recommended AND no SKIP entry was issued, `/help` MAY append: *"Ready to run? Invoke `/xxx` when you're ready."* This is an invitation, never a `[y/n]` prompt-and-chain. Any `[y/n]` offer is pressed 100% of the time under stress, bypassing verification.

---

## Command Inventory

**Inventory sync contract**: Canonical inventory is the contents of `ai-research-toolkit/shared/commands/*.md` (12 files) plus `/pcv` which lives at `ai-research-toolkit/pcv/agents/*.md` and is invoked via the skills registry. Any PR adding/renaming a command must update this block AND the command file's frontmatter.

Grouped by problem-shape:

**Verification** (check if something is right):
- `/audit` — citations and numerical values against source papers (4 smoke fixture: `audit_smoke.md`)
- `/pace` — two-player consensus on a decision with a single right answer (smoke: `pace_source_verification.md`)
- `/coa` — panel of experts with different lenses on a decision with multiple valid framings
- `/pcv` — structured plan-construct-verify for a multi-step task *(invoked via skills registry, NOT `shared/commands/pcv.md`)*
- `/improve` — audit of my Claude Code infrastructure itself
- `/simplify` — reduce redundancy in code or documents

**Workflow** (project state / continuity):
- `/startup` — where did I leave off across workstreams?
- `/dailysummary` — capture today's work
- `/weeklysummary` — roll up the week by workstream
- `/commit` — make git history from uncommitted changes (smoke: `commit_grouping.md`)
- `/runlog` — longitudinal view of how my toolkit has been performing (smoke: `runlog_parser.md`)

**Content** (produce something):
- `/quarto` — slide deck from notes
- `/readable` — extract text from PDFs/DOCX for grep/cite

---

## Example Transcripts

### Example 1 — Shape A, obvious match (3 chunks)

```
student: /help I need to make slides from my research notes

/help:
Match: /quarto — generates Quarto RevealJS decks from background documents.
Run: /quarto <path/to/your/notes.md>

Skip /readable — only needed if your notes are still PDFs.
```

### Example 2 — Shape A, one prerequisite (5 chunks, at budget)

```
student: /help I have a paper and I'm worried about citations, sources are on disk

/help:
Primary: /audit — verifies every citation exists on disk AND every quoted number matches the source.
Run: /audit <path/to/your_paper.md> --sources <path/to/sources/>   `Verify: tests/smoke/audit_smoke.md`

Prereq: /readable first IF any source is still a raw PDF (no .txt extraction).
Run: /readable <path/to/sources/>

Skip /pace — it's for decisions with multiple valid answers, not citation checking.
```

### Example 3 — Shape B, one clarification (4 chunks)

```
student: /help I'm stuck on a writing decision

/help:
One question: do you already know there are multiple reasonable choices, or are you looking for a single right answer?

student: multiple reasonable choices

/help:
Match: /coa — spawns a panel of experts with distinct lenses, surfaces convergence/divergence across reasonable framings.
Run: /coa "<your decision framed as a question>"
If the panel feels heavy: /coa --quick (3 seats, ~100K tokens vs ~200K).

Skip /pace — for verification of a single right answer, not comparison of reasonable options.
```

### Example 4 — Shape C, scaffold menu (3 chunks)

```
student: /help

/help:
What are you trying to do? Pick the closest:
1. Verify something (a citation, a number, a claim)
2. Decide between options (architecture, direction, tradeoff)
3. Capture or find project state (summary, startup, commit)
4. Produce a deliverable (slides, extracted text, simplified code)
5. Something else — describe it in one line.

student: 3

/help:
Primary: /startup — shows where every workstream left off, with recommended next action.
Run: /startup

Alt: /dailysummary if you want to close out today's work instead of resume prior work.
Run: /dailysummary
```

### Example 5 — No match (2 chunks, does NOT leak project-specific paths)

```
student: /help my simulation keeps crashing with out-of-memory errors

/help:
No match. The toolkit is research-workflow-focused, not simulation-runtime-focused. For runtime/RAM issues, check your project's local reference docs (CLAUDE.md often has a simulation section).

If you want structured debugging with multiple perspectives on WHY it's crashing: /coa — spawn a panel (perf + systems + architecture lenses). Heavier tool than the situation may need.
```

---

## Non-goals

1. Does not execute commands. Recommendation is the terminus.
2. Does not answer research questions. Route to `/coa` or `/pace`.
3. Does not explain commands in depth. Point to `shared/commands/<cmd>.md`.
4. Does not teach the toolkit curriculum. That's the README.
5. Does not remember prior invocations. Stateless — re-invoke with the new one-liner.
6. Does not chain-and-execute. Single carve-out (STEP 6) is an *invitation*, never `[y/n]`.

---

## Success Metrics (pre-registered)

`/help` is useful if AT LEAST ONE of these fires in `run_log.csv` by end of fall 2026:

1. **Triage signal**: ≥20% of recommended commands are subsequently run by the same session within 30 minutes (recommendation acted on).
2. **Routing improvement**: Sessions invoking `/help` have higher command-diversity (≥2 commands used) than sessions not using `/help`.
3. **Premise validation**: Low rate of same-student invoking `/help` multiple times for the same underlying problem (R2 detection negative).

## Re-open Triggers

Open a v0.3 revision if ANY fire in `run_log.csv`:
- **R1**: >10% of recommendations point to a deprecated/renamed command (inventory drift)
- **R2**: High correlation between `clarifying_questions=1` AND `triage_result=no_match`
- **R3**: Same-student-same-command `/help`-for-study pattern (triage → study-aid inversion)

## Removal Trigger

If by end of fall 2026 NONE of the three success criteria hold, `/help` is a candidate for removal (not just revision). This preserves the ability to delete a command that didn't earn its keep.

---

## Verify Your Install

```bash
cat ai-research-toolkit/tests/smoke/help_triage.md
# The smoke fixture documents 4 expected cases (shape A, B, C, no-match).
# Invoke /help with each test input and confirm output shape matches expectations.
```

---

## Design Artifacts

- v0.2 spec: `plans/help_command_draft.md`
- Shipped without premise pilot — deferred to live-signal resolution per "Success Metrics" above.
