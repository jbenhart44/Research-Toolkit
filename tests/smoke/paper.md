# Test Paper for /audit Smoke Fixture

This paper cites three sources — two valid, one fabricated. See `audit_smoke.md` for details.

---

## Test Claims

Smith (2022) found that 85% of respondents preferred option A.

Jones (2023) reports a 42% decrease in churn after intervention.

Rodriguez (2024) proposed the framework we build on.

---

## Expected audit output

- Smith (2022) → VERIFIED
- Jones (2023) → MISMATCH (doc says 42%, source says 35%)
- Rodriguez (2024) → NOT FOUND (no source PDF in sources/)
