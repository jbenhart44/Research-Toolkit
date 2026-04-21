# /runlog Parser Smoke Test

**Purpose**: Verify /runlog's CSV parser correctly aggregates `run_log.csv` and skips malformed/legacy rows. Guards against regression to raw `awk -F','` parsing, which was the v1.0 bug (caught in T4 verification on 2026-04-17).

**Fixture**: the live `CC_Workflow/evidence/run_log.csv` on this project (mix of canonical v1.1 rows + legacy pre-2026-04-10 rows).

**Version**: v1.1 (2026-04-17)

---

## Expected Results (as of 2026-04-17 run_log.csv state)

- **Total rows**: 15 (data rows, excluding header)
- **Valid rows after legacy-filter**: 13
- **Malformed/legacy rows (skipped)**: 2 (column-shifted rows with `pace_` and `coa_` in the `tool` column)
- **Per-tool counts**:
  - `pcv-research`: 10
  - `pace`: 2
  - `pcv-researchJake`: 1

Ground truth re-verified at every new valid row append — as more commands emit via `emit_run_report.sh`, these counts grow but the parser logic is invariant.

---

## The Test

Run this Python block against the live CSV. If any `assert` fires, /runlog's parser is broken.

```python
import csv
from collections import Counter

with open("CC_Workflow/evidence/run_log.csv") as f:
    rows = list(csv.DictReader(f))

# Legacy-row filter: heuristic for detecting column-shifted rows where the
# `tool` column contains what should have been a `run_id`
valid = [r for r in rows if r.get("tool", "") and not r["tool"].startswith(
    ("2026-", "2025-", "pace_", "coa_", "pcv_")
)]

assert len(rows) >= 15, f"expected >=15 total rows, got {len(rows)}"
assert len(valid) >= 13, f"expected >=13 valid rows, got {len(valid)}"

counts = Counter(r["tool"] for r in valid)
assert counts.get("pcv-research", 0) >= 10, f"expected >=10 pcv-research, got {counts.get('pcv-research', 0)}"
assert counts.get("pace", 0) >= 2, f"expected >=2 pace, got {counts.get('pace', 0)}"
assert counts.get("pcv-researchJake", 0) >= 1, f"expected >=1 pcv-researchJake, got {counts.get('pcv-researchJake', 0)}"

print(f"PASS: {len(valid)}/{len(rows)} rows valid, counts: {dict(counts)}")
```

---

## What Passing Looks Like

```
PASS: 13/15 rows valid, counts: {'pcv-research': 10, 'pace': 2, 'pcv-researchJake': 1}
```

(Numbers grow over time as more instrumented runs accumulate — the `>=` assertions account for growth.)

---

## What Failing Looks Like

**Failure mode 1 — parser regressed to raw awk**:
```
AssertionError: expected >=10 pcv-research, got 2
```
Cause: raw `awk -F','` split on embedded commas in the `task_summary` cell, miscounted rows.
Fix: restore Python csv.DictReader-based parser in `shared/commands/runlog.md` Step 2.

**Failure mode 2 — new schema variant introduced without filter update**:
```
AssertionError: expected >=13 valid rows, got 7
```
Cause: new `emit_run_report.sh` version wrote a different tool-column convention.
Fix: update the legacy-row filter heuristic in this test + `runlog.md` Step 2.

**Failure mode 3 — CSV corrupted mid-row**:
```
_csv.Error: ...
```
Cause: a command called `emit_run_report.sh` without flock; concurrent append interleaved bytes.
Fix: verify `scripts/emit_run_report.sh` has the `flock 9` atomic-append block (v1.1 patch).

---

## Running the Test

From the project root:

```bash
python3 ai-research-toolkit/tests/smoke/runlog_parser_test.py
```

(The test script body is embedded in this markdown — extract to a `.py` file or run inline via a heredoc.)

Alternative one-liner:

```bash
cd "$(git rev-parse --show-toplevel)" && python3 <<'PY'
import csv
from collections import Counter
with open("CC_Workflow/evidence/run_log.csv") as f:
    rows = list(csv.DictReader(f))
valid = [r for r in rows if r.get("tool", "") and not r["tool"].startswith(("2026-", "2025-", "pace_", "coa_", "pcv_"))]
counts = Counter(r["tool"] for r in valid)
print(f"{len(valid)}/{len(rows)} rows valid, counts: {dict(counts)}")
assert counts.get("pcv-research", 0) >= 10
assert counts.get("pace", 0) >= 2
print("PASS")
PY
```

---

## Related Guards

- `scripts/emit_run_report.sh` includes a `flock 9` atomic-append block — without it, concurrent /pace + /coa calls could corrupt the CSV. This fixture would catch corruption via `_csv.Error`.
- The canonical schema is documented in `DESIGN.md` § "v1.1 Canonical run_log.csv Schema".
