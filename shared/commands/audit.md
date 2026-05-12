---
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(wc:*), Bash(date:*), Write, Agent
description: Citation and numerical accuracy audit — verifies every cited metric and source in a document against actual paper PDFs/TXT files on disk. Prevents fabricated citations AND misquoted numbers.
---

# /audit — Citation & Numerical Accuracy Audit

> **When to use**: Before submitting, printing, or presenting any academic document that contains citations or numerical values attributed to external sources.

Verify every citation and numerical value in a document against the actual source papers on disk. This command exists because two failure modes are equally dangerous: (1) fabricating a citation that doesn't exist, and (2) misquoting a number from a real paper.

## Usage

```
/audit <file_path>                        # Audit a specific file (.html, .qmd, .tex, .md)
/audit <directory>                        # Audit all academic files in a directory
/audit <file_path> --sources <dir>        # Specify where source PDFs/TXTs live (overrides auto-search)
/audit <file_path> --deep                 # Claim-chain mode: extends the grep gate to a five-step chain
                                          # with mandatory structured YAML verdict per citation (see § Deep Mode)
```

**Output**: `/audit` reports discrepancies — it does not produce a pass/fail verdict. MISMATCH and NOT FOUND findings require your judgment (some number variations are acceptable; some are not). The audit report lists every finding with line references so you can decide what to fix.

## What It Checks

### 1. Citation Existence (PDF-on-disk gate)
For every citation in the document (Author Year format):
- Search for matching PDF or TXT files in the project's paper directories
- Report: FOUND / NOT ON DISK / PARTIAL (TXT only, no PDF)

### 2. Numerical Accuracy (grep-verify gate)
For every numerical value attributed to an external source:
- Identify the cited paper and the specific number
- Grep the source .txt file for that exact value
- Read surrounding context to confirm the number means what the document claims
- Report: VERIFIED (with line number) / MISMATCH (state what paper actually says) / NOT FOUND / **GAP-IN-SOURCE** (new — see below)

### 2b. GAP-IN-SOURCE recognition (v1.7 — typed extraction-gap awareness)

When the source `.txt` contains a typed `[MATERIAL GAP: extraction failure on page N — ...]` line (produced by `/readable` when a page could not be extracted), and the cited value's page reference falls inside that gap, the audit must NOT report NOT FOUND. Report **GAP-IN-SOURCE** instead, with the page number and the extraction-failure reason copied verbatim from the marker.

Detection rule: for any numerical value where the grep returned zero matches in the source `.txt`, before emitting NOT FOUND, grep the same `.txt` for `^\[MATERIAL GAP: extraction failure on page <P>` where `<P>` is the cited page number (if the document supplies one). If a marker is present for that page, the status is GAP-IN-SOURCE.

Why this distinction matters: NOT FOUND tells the author "the cited number is not in the paper" — actionable advice is "fix the citation or remove the claim." GAP-IN-SOURCE tells the author "we could not read the cited page" — actionable advice is "re-extract the PDF (perhaps with a higher-resolution OCR pass), inspect the page manually, or acquire a clean copy." The two are different problems with different fixes; conflating them produces wrong author behavior.

### 3. Self-Citation Check
Flag any values attributed to internal work (simulations, project data):
- Verify these trace to actual committed files (CSV, logs, scorecards)
- Report the file path where the value can be confirmed

## How It Works

### Step 1: Extract citations and numbers
Strip binary data (base64 images in HTML), then scan for:
- Author-year patterns: `(Author et al. YYYY)`, `(Author YYYY)`, `Author (YYYY)`
- Numerical values with units: dollar amounts, percentages, ratios, counts
- Citation keywords: "Table", "Exhibit", "p.", "page", "Figure"

### Step 2: Verify paper exists on disk
Search project paper directories recursively for matching author name in filename.

### Step 3: Verify numbers against source
For each number + citation pair:
- Grep the source .txt extraction for the exact figure
- If found, read context to confirm meaning matches the claim
- If not found, try variations (with/without $, %, different precision)

### Step 4: Generate audit report
Write to same directory as audited file: `<filename>_audit_YYYY-MM-DD.md`

```markdown
# Citation & Numerical Audit Report
**File**: <path>
**Date**: YYYY-MM-DD

## Results Summary
- VERIFIED: N
- MISMATCH: N (CRITICAL — must fix before publication)
- NOT FOUND: N (investigate)
- NOT ON DISK: N (need to acquire PDF)

## Detailed Results
| # | Claim | Cited Source | Value | Status | Notes |
|---|-------|-------------|-------|--------|-------|
```

### Step 5: Report to user
If ANY mismatches:
> "**CRITICAL: [N] numerical mismatches found.** Must fix before publication."

If all verified:
> "All [N] citations verified, all [M] numerical values confirmed."

## Important Rules

- **NEVER skip a number.** Every numerical value with a citation gets checked.
- **NEVER assume a number is correct** because it looks plausible.
- **Context matters.** Same paper may have different values in abstract vs. table vs. robustness check. Verify the specific value matches the specific claim.
- **Currency conversions are NOT automatic.** Flag any unit conversions for manual review.
- **A wrong number from a real paper is as bad as a fabricated citation.** Both are academic misrepresentation.
- **MATERIAL GAP refusal token** (v1.2 — sentinel-comment guard). When a NOT FOUND or MISMATCH finding is identified, emit it in the audit report as `[MATERIAL GAP: <claim> — no grep hit for "<pattern>" in <searched dirs>]`. If you are *also* recommending an inline edit to the document, render the marker ONLY as a comment sentinel for that document's format — NEVER as visible body text:
  - LaTeX (`.tex`):    `% [MATERIAL GAP: <claim>]`
  - Quarto / HTML:     `<!-- [MATERIAL GAP: <claim>] -->`
  - Markdown:          `<!-- [MATERIAL GAP: <claim>] -->`

  Rationale: the token is a *quiet placeholder for the author* (replaces the pre-v1.2 informal `% TODO: citation needed` convention with a structured form), not a public artifact. Visible refusal text in submitted prose is louder than a fabricated citation — a reviewer encountering `[MATERIAL GAP: ...]` in body prose instantly knows the author used an LLM and didn't clean up before submission. The token belongs in the audit report and in author-only comment sentinels; never on a slide face, never in body prose, never in a rendered HTML/PDF reader-facing output.

## Deep Mode — claim-chain audit (v1.7)

Invoked via `/audit <file> --deep`. Extends the single-step grep gate to a five-step chain. Every VERIFIED citation from the standard audit gets re-checked against four additional gates; the deep audit emits a structured YAML verdict per citation with a **mandatory terminal state** — the deep audit cannot terminate in ambiguity.

### The five-step chain

For each citation that passed the standard grep gate (status: VERIFIED):

1. **PDF on disk** — already established by step 1 of the standard audit.
2. **Grep hit** — already established by step 2 of the standard audit.
3. **Methodology section located.** Grep the source `.txt` for one of: `Methods`, `Methodology`, `Approach`, `Sample`, `Data and Methods`, `Empirical Strategy`, `Identification` (case-insensitive, at line start). Record the line number range where the methodology section begins and ends (next H2 or end of file).
4. **Retraction / correction notice absence.** Grep the source `.txt` AND any co-located retraction-notes files (`<paper-stem>.retraction.md`, `<paper-stem>.corrections.md`, or `RETRACTION_NOTES.md` in the source directory) for any of: `retracted`, `retraction`, `corrigendum`, `correction`, `expression of concern`, `superseded`, `withdrawn`, `EOC`. A hit on any of these in the source paper itself OR in a co-located retraction file flips the verdict.
5. **Robustness-check context.** If the cited value's `.txt` line falls inside a section header containing `Robustness`, `Supplementary`, `Appendix`, `Sensitivity`, or `Falsification`, record this as context. A robustness-check value cited as a headline result is a misattribution; the deep audit flags it without auto-reclassifying (the author decides whether the citation was intended as headline or qualifier).

### Terminal verdict — one of five (mandatory)

The deep audit emits a YAML file `<filename>_claim_chain_YYYY-MM-DD.yaml` with one entry per audited citation:

```yaml
- citation: "Author 2023"
  value: "$25.50"
  cited_page: 7
  verdict: verified | partial | unverifiable | misattributed | retracted
  chain:
    pdf_on_disk: true
    grep_hit: true
    methodology_section_located: true
    retraction_notice_found: false
    robustness_check_context: false
  notes: "one-line free-text rationale if the verdict is not 'verified' — e.g., 'value appears in §A.4 Robustness, but the document cites it as a headline result'"
```

**Verdict rules** (mechanical, not discretionary):

| Verdict | When |
|---|---|
| `verified` | Steps 1–5 all clean: PDF present, grep hit, methodology section locatable, no retraction signal, not from a robustness-only context |
| `partial` | Steps 1–2 pass but step 3 fails (cannot locate a methodology section — paper may be a comment, editorial, or working paper where methodology is implicit) |
| `unverifiable` | Steps 1–2 pass but the `.txt` shows a GAP-IN-SOURCE on the cited page (extraction failure prevents step 3+) |
| `misattributed` | Step 5 fires: cited value is verbatim present but only inside a robustness/supplementary/sensitivity section, while the document cites it as a headline finding |
| `retracted` | Step 4 fires: a retraction or correction notice is present in the source paper or its co-located retraction file |

**The verdict field is mandatory.** A claim_chain entry without a verdict is a defect — the deep audit must terminate at one of the five states. If the audit cannot determine a verdict, the correct state is `unverifiable` with a `notes:` line stating what blocked the determination.

### When to run `--deep`

- **Before any final submission** where the author is committing to causal or empirical claims that rest on cited methodologies (not just on cited numbers in isolation).
- **After any methodology section is rewritten** to confirm that every cited result still survives the chain.
- **When acquiring a new paper into the project** — the first audit of a paper through `--deep` establishes its baseline claim-chain status, which the standard audit's grep gate alone cannot.

Deep mode is more expensive than the standard audit (typically 3-5× the wall-clock time per citation, because step 3 reads the methodology section and steps 4-5 grep additional structure). It is a pre-submission gate, not an every-session step. The standard `/audit` remains the daily-use command.

### What the deep mode does NOT do

- It does NOT call external services. No CrossRef API, no Retraction Watch API, no Semantic Scholar — all retraction signals must come from local `.txt` extractions or co-located retraction notes the user has manually added. Live-network retraction lookup is out of scope for v1.7 (would violate the no-live-network default-path constraint).
- It does NOT auto-fix the document. Like the standard audit, deep mode reports findings — the author decides what to fix.
- It does NOT replace the standard audit. The standard `/audit` runs the grep gate on every citation; deep mode adds the chain on top. A document submitted without the standard audit having passed is not made safer by skipping straight to deep mode.

## Dependencies
- Source papers should have .txt extractions alongside the PDFs (use `/readable` first)
- If .txt files don't exist, flag as UNVERIFIABLE and suggest running `/readable`
- For deep mode: retraction notes (if any) live alongside the PDF as `<paper-stem>.retraction.md` or in a directory-level `RETRACTION_NOTES.md`. These are user-curated; the toolkit does not fetch them.

## When to Run
- Before printing any poster or submitting any paper
- After any session where cited numbers were written or modified
- After any PACE run that produces numerical content

---

## Instrumentation (v1.1 — one-line emit at end of run)

After writing the audit report, emit a structured run_report for observability via `/runlog`:

```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command audit \
  --run-dir "$audit_reports_dir/.run_reports/$(date +%Y-%m-%d_%H%M%S)" \
  --outcome complete \
  --task-summary "Audit of $DOCUMENT_PATH" \
  --fields "input_file=$DOCUMENT_PATH citations_checked=$N_CITED numerical_values_checked=$N_NUMERIC verified_count=$N_VERIFIED mismatch_count=$N_MISMATCH not_found_count=$N_NOT_FOUND not_on_disk_count=$N_NOT_ON_DISK verdict=$VERDICT"
```

Where `$VERDICT` is `pass` (zero mismatches/not-found) or `fail` (any mismatch or not-found). One-line call via the helper. Skip silently if helper is unavailable — the audit report is the user-facing deliverable.

---

## Smoke Test

A smoke test fixture lives at `tests/smoke/audit_smoke.md` with 3 citations (2 valid + 1 fabricated). Run this to confirm `/audit` is working after installation:

```bash
cd tests/smoke/
/audit paper.md --sources sources/
# Expected: VERIFIED: 1, MISMATCH: 1 (Jones 42% vs 35%), NOT FOUND: 1 (Rodriguez)
```

> **What next?** If any citation shows NOT ON DISK, run `/readable` on that paper's PDF first to generate a searchable `.txt`, then re-run `/audit` to verify the specific number.
