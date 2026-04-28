# /simplify — Code & Document Optimization Review

Your preprocessing script works, but it's grown to 280 lines across four months and you know it has redundant logic.

## When you need this

- After a working implementation is complete and you want to clean it up before sharing or publishing
- When a function has been patched multiple times and you suspect there's duplication
- After a document has gone through several revision rounds and feels bloated

## What it does — and what it won't

`/simplify` reviews your code or document through five lenses: redundancy, complexity, performance, robustness, and readability. It identifies specific issues with line references and proposes concrete fixes. It applies changes only after you confirm.

**Note**: `/simplify` does not run tests. It reads the code and identifies issues — you should run your tests separately after applying any changes. Use it on working code, not broken code.

## Worked example

Priya's RNA-seq preprocessing script works correctly but has grown to 280 lines. She suspects there's duplicated logic across the filtering and normalization steps.

```
/simplify scripts/preprocess_rnaseq.R
```

`/simplify` returns five findings: the cell-filtering threshold check is written identically in three places (lines 44, 112, 201) — proposes a `filter_cells()` helper; a nested if/else block on lines 155–189 can be flattened to four guard clauses; the normalization loop re-reads the full count matrix on each iteration (O(n²)) — proposes a vectorized equivalent; a helper function defined but only called once; no check that the input matrix is non-empty before normalization. Priya reviews the report and decides which fixes to apply.

## Try it

```
/simplify script.py
/simplify document.md
```
