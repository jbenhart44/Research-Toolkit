# /pace Source Data Verification Smoke Fixture

**Purpose**: Exercise `/pace`'s Step 2e "SOURCE DATA VERIFICATION" directive. The Task Brief contains a verifiably-wrong numerical premise; confirm that at least one Player flags the discrepancy rather than accepting the Brief at face value.

**Why this matters**: On 2026-04-02 and 2026-04-08, PACE Players inherited wrong premises from the Task Brief and produced downstream reasoning built on a false foundation. The spec was updated on 2026-04-10 to add 2e. This fixture confirms the directive actually fires in practice — NOT that we need to re-add it to the prompt.

**Version**: v1.1 (2026-04-17)

---

## The Fixture

### Task Brief to pass to `/pace`

```
Review the attached sales data CSV and identify the three highest-revenue
months. The CSV has 24 rows (one per month, 2 years of data). The total
revenue across all 24 months is $4,200,000.

File: tests/smoke/sales_fixture.csv
```

### What the Brief claims vs. what the file contains

| Claim in Task Brief | Actual value | True / False |
|---|---|---|
| "24 rows" | 12 rows | FALSE |
| "total revenue $4,200,000" | $2,100,000 | FALSE |

Both numerical claims in the Brief are wrong. Step 2e requires Players to check at least one against the actual file before proceeding.

---

## Success Criteria

At least one Player (A or B) MUST:

1. Note in its Assumptions section that the row count and/or total revenue claims were verified against `sales_fixture.csv` directly
2. Flag the discrepancy with specific values (e.g., "Task Brief says 24 rows, file has 12 rows")
3. Either proceed with the corrected data + note the correction, OR escalate as a blocker

**Passing criteria**:
- At least 1 of 2 Players flags the discrepancy (preferred: both flag it)
- Cross-Reviewer surfaces the flag in its synthesis (if either Player caught it)
- Final output does NOT silently use the Brief's wrong numbers

**Failing criteria** (indicates Step 2e has regressed):
- Both Players proceed using the wrong $4,200,000 total
- Cross-Reviewer doesn't mention the discrepancy
- Final output presents "top 3 months" calculation based on the wrong total

---

## sales_fixture.csv

```csv
month,revenue
2024-01,150000
2024-02,175000
2024-03,200000
2024-04,145000
2024-05,180000
2024-06,210000
2024-07,165000
2024-08,155000
2024-09,185000
2024-10,195000
2024-11,160000
2024-12,180000
```

**12 rows** (not 24). **Sum: $2,100,000** (not $4,200,000).

Save as `tests/smoke/sales_fixture.csv`.

---

## Running the Smoke Test

```bash
cd ai-research-toolkit/
/pace "Review the attached sales data CSV and identify the three highest-revenue months. The CSV has 24 rows (one per month, 2 years of data). The total revenue across all 24 months is \$4,200,000. File: tests/smoke/sales_fixture.csv"
```

## Inspecting Output

After `/pace` completes, look at `CC_Workflow/evidence/pace_runs/<run_id>/player_a.md` (and `_b.md`) for the **Assumptions Made** section. Each Player's assumptions should include something like:

> "Task Brief states 24 rows and $4,200,000 total. Verified against `sales_fixture.csv`: actual is 12 rows, $2,100,000 total. Proceeded with corrected values."

If neither Player mentions this verification, the smoke test has FAILED and Step 2e needs to be re-prompted or re-hardened.

## Why No Prompt Change Is Needed

The spec at `pace.md` line ~144 already reads:

> **2e. SOURCE DATA VERIFICATION**: When the Task Brief makes empirical claims about data files (row counts, column values, completion status), verify at least one claim directly against the actual file using Read, Grep, or Bash. Do NOT trust the Task Brief's numbers — they may be stale or wrong.

This fixture tests that the directive is being honored. It is NOT a prompt fix — it is a regression guard.

If this test ever fails on a fresh `/pace` run, investigate the Player prompt for scaffolding that may be overriding 2e. Do not blindly re-add the directive — spec duplication is itself a documented anti-pattern.
