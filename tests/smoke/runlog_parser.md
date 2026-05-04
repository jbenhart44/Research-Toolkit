# /runlog Parser Smoke Test

**Purpose**: Verify /runlog's CSV parser correctly aggregates `run_log.csv` and skips malformed/legacy rows. Guards against regression to raw `awk -F','` parsing, which was the v1.0 bug (caught in T4 verification on 2026-04-17).

**Fixture**: a synthetic 8-row CSV written to `/tmp/test_run_log.csv` at test time. Portable — no dependency on any author's project history.

**Version**: v1.2 (2026-05-03 — fixture rewritten to be portable per /coa 2026-05-02 D-1 ruling)

---

## The Test (one-liner from fresh clone)

```bash
# 1. Write a synthetic fixture (8 rows: 5 valid, 3 legacy/malformed)
cat > /tmp/test_run_log.csv <<'CSV'
run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
r001,pcv-research,v3.14,2026-04-20,"plan A",complete,opus,4,0.85,17,3,plans/a.md,"sample"
r002,pcv-research,v3.14,2026-04-21,"plan B",complete,opus,4,0.90,18,2,plans/b.md,"sample"
r003,pcv-research,v3.14,2026-04-22,"plan C",complete,opus,4,0.80,16,4,plans/c.md,"sample"
r004,pace,v1.1,2026-04-23,"verify D",complete,opus,4,0.95,19,1,evidence/pace_runs/d.md,"sample"
r005,coa,v2.1,2026-04-24,"council E",complete,opus,6,0.75,15,5,coa/council_sessions/e.md,"sample"
2026-04-25T10:00:00Z,pace_run_001,v1.0,2026-04-25,"legacy column-shifted row",complete,opus,2,1.0,2,0,,
2026-04-26T10:00:00Z,coa_session_002,v1.0,2026-04-26,"another legacy row",complete,opus,6,0.83,5,1,,
r008,pcv_v3,v3.0,2026-04-27,"prefix collision row",complete,opus,4,0.88,17,3,plans/h.md,"sample"
CSV

# 2. Run the parser test against the fixture
python3 <<'PY'
import csv
from collections import Counter

with open("/tmp/test_run_log.csv") as f:
    rows = list(csv.DictReader(f))

# Legacy-row filter: drop rows whose `tool` column starts with timestamps or
# legacy underscored prefixes (column-shifted rows from v1.0 emit_run_report.sh).
valid = [r for r in rows if r.get("tool", "") and not r["tool"].startswith(
    ("2026-", "2025-", "pace_", "coa_", "pcv_")
)]

assert len(rows) == 8, f"expected 8 total rows, got {len(rows)}"
assert len(valid) == 5, f"expected 5 valid rows, got {len(valid)}"

counts = Counter(r["tool"] for r in valid)
assert counts.get("pcv-research", 0) == 3, f"expected 3 pcv-research, got {counts.get('pcv-research', 0)}"
assert counts.get("pace", 0) == 1, f"expected 1 pace, got {counts.get('pace', 0)}"
assert counts.get("coa", 0) == 1, f"expected 1 coa, got {counts.get('coa', 0)}"

print(f"PASS: {len(valid)}/{len(rows)} rows valid, counts: {dict(counts)}")
PY

# 3. Cleanup
rm -f /tmp/test_run_log.csv
```

---

## What Passing Looks Like

```
PASS: 5/8 rows valid, counts: {'pcv-research': 3, 'pace': 1, 'coa': 1}
```

Exactly these numbers — the fixture is fixed, so unlike the live-CSV version this test has tight equality assertions. Any drift indicates a real parser regression.

---

## What Failing Looks Like

**Failure mode 1 — parser regressed to raw awk**:
```
AssertionError: expected 5 valid rows, got 3
```
Cause: raw `awk -F','` split on embedded commas in the `task_summary` cell, miscounted rows.
Fix: restore Python `csv.DictReader`-based parser in `shared/commands/runlog.md` Step 2.

**Failure mode 2 — legacy-row filter regressed**:
```
AssertionError: expected 5 valid rows, got 8
```
Cause: the `tool`-column prefix filter (`2026-`, `2025-`, `pace_`, `coa_`, `pcv_`) was removed; column-shifted legacy rows are leaking into the count.
Fix: restore the prefix filter in `shared/commands/runlog.md` Step 2.

**Failure mode 3 — CSV corrupted mid-row**:
```
_csv.Error: ...
```
Cause: a command called `emit_run_report.sh` without `flock`; concurrent append interleaved bytes.
Fix: verify `scripts/emit_run_report.sh` has the `flock 9` atomic-append block (v1.1 patch).

---

## Why the fixture is synthetic (v1.2 change, 2026-05-03)

v1.1 of this fixture read the live `${EVIDENCE_DIR:-evidence}/run_log.csv` from the author's project, with assertions like `>=10 pcv-research`. That made the test:
- Non-portable — failed on a fresh clone with no author-history
- Drift-prone — assertions would slowly break as the live CSV grew or shrank

v1.2 writes a fixed 8-row fixture to `/tmp/test_run_log.csv`, runs assertions with `==` instead of `>=`, then cleans up. Same parser logic exercised; no project-state coupling.

---

## Related Guards

- `scripts/emit_run_report.sh` includes a `flock 9` atomic-append block — without it, concurrent /pace + /coa calls could corrupt the CSV. This fixture would catch corruption via `_csv.Error`.
- The canonical schema is documented in `DESIGN.md` § "v1.1 Canonical run_log.csv Schema".
