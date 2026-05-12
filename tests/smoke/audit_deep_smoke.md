# /audit --deep Smoke Test Fixture

**Purpose**: Exercise `/audit --deep` (claim-chain mode, v1.7+) against a 3-citation document where each citation is engineered to land at a distinct terminal verdict — `verified`, `retracted`, and `misattributed`. Confirms the deep mode emits the YAML verdict file with the correct terminal state for each citation.

**Usage**: From this directory, run `/audit paper_deep.md --sources sources/ --deep`. Expected: a `paper_deep_claim_chain_<date>.yaml` file with three entries, terminal verdicts `verified` / `retracted` / `misattributed` in the order the citations appear.

**Version**: v1.7 (2026-05-12)

---

## Expected Results

| Citation | Behavior | Expected terminal verdict |
|---|---|---|
| Patel (2022) | Clean: PDF present, grep hit at p.4, methodology section locatable, no retraction notice, value in main results | `verified` |
| Kowalski (2021) | Retraction signal: co-located `kowalski_2021.retraction.md` is present and contains the word "Retraction" | `retracted` |
| Chen (2024) | Misattribution signal: value appears in source `.txt` inside `## Robustness Checks` section header, but the document cites it as a headline finding | `misattributed` |

## Success Criteria

- The deep mode produces `paper_deep_claim_chain_<date>.yaml` with exactly 3 entries (one per citation).
- Every entry has a non-empty `verdict` field. **No entry may omit the verdict** — that is a defect, not a tolerated state.
- The three verdicts match the expected column above.
- Each entry's `chain` block has all five booleans present (`pdf_on_disk`, `grep_hit`, `methodology_section_located`, `retraction_notice_found`, `robustness_check_context`).
- Total runtime: < 90 seconds.

## Contents of this fixture

The author of the smoke run must create these files before invoking the command:

- `paper_deep.md` — the test document (template below)
- `sources/patel_2022.txt` — clean source with the cited value in a regular results section
- `sources/kowalski_2021.txt` — source where the cited value is present, plus a co-located `sources/kowalski_2021.retraction.md` containing a retraction notice
- `sources/chen_2024.txt` — source with the cited value present, but inside a `## Robustness Checks` section, NOT in the main results

---

## paper_deep.md (the test document)

```markdown
# Deep Audit Smoke Test

This paper cites three sources, each engineered to land at a different deep-mode verdict.

Patel (2022) reports a 0.34 elasticity of substitution between capital and labor (p.4).

Kowalski (2021) finds a 0.78 R-squared for the baseline specification (p.12).

Chen (2024) shows the effect persists at a magnitude of 0.41 (p.8).
```

## sources/patel_2022.txt (clean)

```
Patel (2022) Journal of Applied Econometrics, Vol 28.

Methodology

We estimate a translog production function with capital, labor, and intermediate inputs.

Results

The elasticity of substitution between capital and labor is 0.34 (s.e. 0.04), significant at the 1% level. This is robust across all specifications considered.
```

## sources/kowalski_2021.txt + retraction note

```
Kowalski (2021) Quarterly Journal of Test Data, Vol 15.

Methodology

We use a structural VAR with three lags.

Results

The baseline specification has R-squared 0.78 across the full sample period.
```

And the load-bearing co-located retraction file:

`sources/kowalski_2021.retraction.md`:
```
Retraction notice

The journal has issued a retraction of Kowalski (2021) following the discovery of an identification error in the structural VAR specification. The R-squared figure cited in the paper does not reproduce on the corrected specification.
```

## sources/chen_2024.txt (misattribution)

```
Chen (2024) Review of Test Methodology, Vol 9.

Methodology

We estimate a two-way fixed effects DiD with state and year fixed effects.

Results

The main specification shows an effect magnitude of 0.18 (s.e. 0.06).

Robustness Checks

Under the alternative specification with quadratic time trends, the effect magnitude rises to 0.41. We caution that the alternative specification is sensitive to the choice of bandwidth and recommend reading the result as a robustness check, not as a primary finding.
```

---

## Running the Test

```bash
# Run from tests/smoke/ — ensure paper_deep.md + sources/ exist (see "Contents" above)
/audit paper_deep.md --sources sources/ --deep
```

## Interpreting Output

A passing test produces a YAML file approximately like:

```yaml
- citation: "Patel 2022"
  value: "0.34"
  cited_page: 4
  verdict: verified
  chain:
    pdf_on_disk: true
    grep_hit: true
    methodology_section_located: true
    retraction_notice_found: false
    robustness_check_context: false
  notes: ""

- citation: "Kowalski 2021"
  value: "0.78"
  cited_page: 12
  verdict: retracted
  chain:
    pdf_on_disk: true
    grep_hit: true
    methodology_section_located: true
    retraction_notice_found: true
    robustness_check_context: false
  notes: "retraction notice present in co-located kowalski_2021.retraction.md"

- citation: "Chen 2024"
  value: "0.41"
  cited_page: 8
  verdict: misattributed
  chain:
    pdf_on_disk: true
    grep_hit: true
    methodology_section_located: true
    retraction_notice_found: false
    robustness_check_context: true
  notes: "value appears under Robustness Checks section; document cites it as headline finding"
```

If any verdict is missing, or any verdict is wrong relative to the expected column, the deep mode has regressed.

## Why This Fixture Matters

The deep mode's value depends entirely on the **mandatory terminal verdict** rule — that the chain cannot terminate in ambiguity. This fixture is the structural test that confirms the rule is enforced by the prompt, not just stated in it. Without this smoke test, a regression in which the deep mode silently omits the verdict on a borderline case would not be caught until a real submission used the mode.
