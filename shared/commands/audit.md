---
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(wc:*), Bash(date:*), Write, Agent
description: Citation and numerical accuracy audit — verifies every cited metric and source in a document against actual paper PDFs/TXT files on disk. Prevents fabricated citations AND misquoted numbers.
---

# /audit — Citation & Numerical Accuracy Audit

> **When to use**: Before submitting, printing, or presenting any academic document that contains citations or numerical values attributed to external sources.

Verify every citation and numerical value in a document against the actual source papers on disk. This command exists because two failure modes are equally dangerous: (1) fabricating a citation that doesn't exist, and (2) misquoting a number from a real paper.

## Usage

```
/audit <file_path>         # Audit a specific file (.html, .qmd, .tex, .md)
/audit <directory>         # Audit all academic files in a directory
```

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
- Report: VERIFIED (with line number) / MISMATCH (state what paper actually says) / NOT FOUND

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

## Dependencies
- Source papers should have .txt extractions alongside the PDFs (use `/pdftotxt` first)
- If .txt files don't exist, flag as UNVERIFIABLE and suggest running `/pdftotxt`

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
cd ai-research-toolkit/tests/smoke/
/audit paper.md --sources sources/
# Expected: VERIFIED: 1, MISMATCH: 1 (Jones 42% vs 35%), NOT FOUND: 1 (Rodriguez)
```
