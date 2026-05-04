# /audit Smoke Test Fixture

**Purpose**: Exercise `/audit` against a 3-citation test document with 2 valid and 1 fabricated citation. Confirms the command correctly identifies the fabricated citation.

**Usage**: From this directory, run `/audit paper.md --sources sources/`. Expected output: `VERIFIED: 2, FABRICATED: 1, verdict: fail`.

**Version**: v1.1 (2026-04-17)

---

## Expected Results

| Citation | In `sources/`? | Number correct? | Expected verdict |
|---|---|---|---|
| Smith (2022) | YES | YES (85%) | VERIFIED |
| Jones (2023) | YES | NO (doc says 42% but source says 35%) | MISMATCH |
| Rodriguez (2024) | NO (filename `rodriguez_2024.pdf` does not exist) | N/A | NOT FOUND (fabricated) |

## Success Criteria

- `/audit` identifies exactly 1 VERIFIED, 1 MISMATCH, 1 NOT FOUND
- NOT FOUND must surface Rodriguez (2024) by name
- MISMATCH must show both numbers (42% in doc, 35% in source)
- Total runtime: < 30 seconds

## Contents of this fixture

- `paper.md` — the test document (see below)
- `sources/smith_2022.txt` — a stub file with the string "85%" (representing the valid source)
- `sources/jones_2023.txt` — a stub with "35%" (the source for the MISMATCH test)
- `sources/` does NOT contain `rodriguez_2024.pdf` or `.txt` (intentional absence for NOT FOUND test)

---

## paper.md (the test document)

```markdown
# Test Paper for /audit Smoke

This paper cites three sources.

Smith (2022) found that 85% of respondents preferred option A.

Jones (2023) reports a 42% decrease in churn after intervention.

Rodriguez (2024) proposed the framework we build on.
```

Save the above markdown block as `paper.md` in this directory before running the test.

---

## Running the Test

```bash
# Run from tests/smoke/ — ensure paper.md + sources/ exist (see "Contents" above)
/audit paper.md --sources sources/
```

## Interpreting Output

A passing test output should look approximately like:

```
/audit summary:
  VERIFIED:    1 (Smith 2022 — 85% matches source)
  MISMATCH:    1 (Jones 2023 — document says 42%, source says 35%)
  NOT FOUND:   1 (Rodriguez 2024 — no PDF in sources/)

Verdict: FAIL (1 MISMATCH, 1 NOT FOUND)
```

If `/audit` reports VERIFIED on Rodriguez or misses the MISMATCH on Jones, the command has regressed.

## Why This Fixture Matters

Before v1.1, `/audit` had zero field-tested invocations in `command_performance_log.md`. Shipping a tool for classroom use without a smoke test meant Kay and other instructors would encounter bugs during actual grading. This fixture is the minimum that allows `/audit` to graduate from UNTESTED to TESTED in the audit matrix.

---

## Companion sources/

Create these files before running the test:

`sources/smith_2022.txt`:
```
Smith (2022) Journal of Test Data, Vol 42.

Abstract: We surveyed 1,200 respondents and found that 85% preferred option A, with statistical significance p<0.001.
```

`sources/jones_2023.txt`:
```
Jones (2023) Journal of Intervention Studies, Vol 15.

Findings: the intervention reduced churn by 35%, with a confidence interval of 32-38%.
```

Note: intentionally no `rodriguez_2024.*` file. The test of NOT FOUND requires absence.
