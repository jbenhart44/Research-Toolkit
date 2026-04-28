# /audit — Citation & Numerical Accuracy Audit

You're about to submit a paper citing a figure you haven't verified against the original source in weeks.

## When you need this

- You've been editing a document and want to confirm every number still matches its cited source
- A collaborator added citations you haven't personally verified
- You're about to print, submit, or present anything with cited numerical values

## What it does — and what it won't

`/audit` scans every citation and numerical value in your document, then grep-searches the source `.txt` files on disk to confirm each number appears on the page you cited. It reports VERIFIED, MISMATCH (with what the paper actually says), or NOT ON DISK. It does **not** produce a pass/fail verdict — you decide what to fix based on the findings.

**Prerequisite**: Run `/readable` on your source PDFs first to generate the `.txt` files `/audit` searches. If a paper shows NOT ON DISK, that's your signal to run `/readable` on it before re-auditing.

## Worked example

Maya is submitting her dissertation chapter on childhood vaccine coverage disparities. She's cited seven WHO and CDC reports with specific cost-per-DALY figures.

```
/audit "dissertation/chapters/chapter2_costs.qmd"
```

`/audit` finds 12 citations and 9 numerical values. It returns: 8 VERIFIED with line numbers, 1 MISMATCH (her draft says "$340" but the paper says "$310 at 2020 prices"), and 1 NOT ON DISK (she needs to run `/readable` on that PDF first). She fixes the mismatch before her advisor sees it.

## Try it

```
/audit your_document.qmd
/audit your_document.qmd --sources papers/
```

> *After auditing: if any citation was NOT ON DISK, run `/readable` on that PDF to extract the text, then re-run `/audit`.*
