# tests/ — Smoke Fixtures

Lightweight fixtures that exercise the toolkit's commands and helpers to confirm they work as documented. NOT a full test suite — just enough to catch regressions before they reach users.

## Directory structure

```
tests/
└── smoke/          Smoke-test fixtures (run by hand or in a post-release check)
```

## Available fixtures (v1.1)

### smoke/audit_smoke.md + paper.md + sources/
Tests `/audit`'s pass/fail/fabricated detection on a 3-citation test document (2 valid + 1 intentionally fabricated). Expected: 1 VERIFIED, 1 MISMATCH (Jones 42% → 35%), 1 NOT FOUND (Rodriguez).

**Run**:
```bash
cd tests/smoke/
/audit paper.md --sources sources/
```

### smoke/pace_source_verification.md + sales_fixture.csv
Tests `/pace`'s Step 2e Source Data Verification directive. Task Brief falsely claims CSV has 24 rows totaling $4.2M; actual CSV has 12 rows totaling $2.1M. At least one Player must flag the discrepancy.

**Run**: feed the Task Brief from `pace_source_verification.md` to `/pace` and inspect Player outputs' Assumptions sections.

### smoke/runlog_parser.md
Tests `/runlog`'s CSV parser against the live `${EVIDENCE_DIR:-evidence}/run_log.csv`. Guards against regression to raw `awk -F','` (the v1.0 bug).

**Run** (one-liner):
```bash
cd "$(git rev-parse --show-toplevel)"
python3 <<'PY'
import csv
from collections import Counter
with open("${EVIDENCE_DIR:-evidence}/run_log.csv") as f:
    rows = list(csv.DictReader(f))
valid = [r for r in rows if r.get("tool", "") and not r["tool"].startswith(("2026-","2025-","pace_","coa_","pcv_"))]
counts = Counter(r["tool"] for r in valid)
print(f"{len(valid)}/{len(rows)} rows valid: {dict(counts)}")
assert counts.get("pcv-research", 0) >= 10
print("PASS")
PY
```

### smoke/commit_grouping.md
Tests `/commit`'s logical grouping claim. 6 files in 3 natural groups → expects 3 separate commits, not 1 (concatenation) or 6 (over-fragmentation).

**Run**: follow setup block in `commit_grouping.md`, invoke `/commit`, verify with the automated verification block.

---

## When to run all fixtures

- Before cutting a v1.x release
- After edits to `shared/commands/` (especially the command the fixture covers)
- Kay's classroom fall rollout — run the full suite as the install validation gate

## What's NOT tested (v1.1 deferred)

- `/weeklysummary`, `/quarto`, `/readable`, `/simplify` have no smoke fixtures (no usage evidence yet — these are v1.2 work)
- End-to-end classroom simulation (install.sh → /startup → ... → /coa) — tracked separately in `plans/charge_toolkit_v1_1_release.md`

## Adding a fixture

1. Pick a command with a testable claim
2. Create `tests/smoke/<command>_<angle>.md` with: purpose, fixture setup, success criteria, failure modes, automated verification
3. Add a section to this README (short description + run command)
4. Reference the fixture from the command's SKILL.md (e.g., at the end of `audit.md`, point to `tests/smoke/audit_smoke.md`)
