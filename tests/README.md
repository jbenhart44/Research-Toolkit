# tests/ — Release Gates and Smoke Fixtures

Two kinds of test live here:

- **Release gates** are Python scripts with an exit code. CI runs them on every push (`.github/workflows/tests.yml`, Linux and macOS). Each one is proven by a mutation check.
- **Smoke fixtures** are Markdown specifications you run by hand inside Claude Code, because they exercise a command's judgment rather than a script.

## Directory structure

```
tests/
├── check_toolkit.py            release gate: command contract, no home paths, credentials, private emails or private tokens
├── check_toolkit_mutations.py  proves check_toolkit.py can fail
├── check_claims.py             release gate: every count and version matches install.sh and VERSION
├── check_claims_mutations.py   proves check_claims.py can fail
├── check_install.py            release gate: a real install in every mode gives a user every file the commands call
├── check_install_mutations.py  proves check_install.py can fail
└── smoke/                      hand-run fixtures (below)
```

## Release gates

```bash
python3 tests/check_toolkit.py              # exit 0 = clean, 1 = findings (each printed as file:line)
python3 tests/check_toolkit.py --tokens my-private-terms.txt   # also refuse your own private terms
python3 tests/check_claims.py               # exit 0 = every page agrees with install.sh and VERSION
python3 tests/check_claims.py path/to/page.html          # also check a page outside the tree
python3 tests/check_install.py              # exit 0 = every install mode gives every file the commands call
python3 tests/check_install.py --previous ../clone-at-previous-tag   # also upgrade from an older checkout (by hand at each release)
```

`check_install.py` runs `install.sh` into temporary HOMEs (default, `--minimal`, `--hooks`, a re-install, `--dry-run`) and takes every expectation from the installer's own arrays and from what the command files call. It exists because from v1.1 to v2.0.1 seven commands called a run-report helper the installer never copied, while the CI step it replaced compared the installed command count to a typed 15.

**Your private terms.** List the names that must never reach a public fork (project names, course codes, private folder names) in `~/.claude/toolkit-private-tokens.txt`, one regular expression per line, `#` for comments. `check_toolkit.py` reads it automatically (or from `--tokens FILE` or `$TOOLKIT_PRIVATE_TOKENS`) and refuses any match outside `pcv/`. Keep the file out of the repository: a list of private terms is itself private. With no file, the gate prints `private-token scan: SKIPPED`, so a missing list is never mistaken for a clean scan.

All three have a `--self-test`. A self-test that passes proves nothing on its own, so each gate also has a mutation check: it writes a copy of the gate with one defect planted, runs the copy's self-test, and requires the named case to go red. A mutant that still passes means a check is vacuous.

```bash
python3 tests/check_toolkit_mutations.py    # every mutant must print CAUGHT; exit 0 = proven
python3 tests/check_claims_mutations.py     # same contract
python3 tests/check_install_mutations.py    # same contract (about two minutes: each run installs many times)
```

The usage counter has the same pair in `hooks/` (`usage_counter_selftest.py`, `usage_counter_mutations.py`), its report in `scripts/` (`usage_counts.py --self-test`, `usage_counts_mutations.py`), and so does the run-report helper (`scripts/emit_run_report_selftest.py`, `scripts/emit_run_report_mutations.py`).

## Smoke fixtures

### smoke/audit_smoke.md + paper.md + sources/
Tests `/audit`'s pass/fail/fabricated detection on a 3-citation test document (2 valid + 1 intentionally fabricated). Expected: 1 VERIFIED, 1 MISMATCH (Jones 42% → 35%), 1 NOT FOUND (Rodriguez).

```bash
cd tests/smoke/
/audit paper.md --sources sources/
```

### smoke/audit_deep_smoke.md
Tests `/audit --deep` (claim-chain mode). Three citations, each engineered to land at a different terminal verdict: `verified`, `retracted`, `misattributed`. The fixture file holds the templates for `paper_deep.md` and its sources; create them first.

### smoke/readable_gap_smoke.md
Tests that `/readable` writes a typed `[MATERIAL GAP: ...]` marker for an image-only page instead of skipping it or inventing text. The fixture file holds the script that builds `gap_fixture.pdf`.

### smoke/pace_source_verification.md + sales_fixture.csv
Tests `/pace`'s source-data verification. The task brief falsely claims the CSV has 24 rows totaling $4.2M; the CSV has 12 rows totaling $2.1M. At least one player must flag the discrepancy.

### smoke/runlog_parser.md
Tests `/runlog`'s CSV parser against a synthetic 8-row fixture (5 valid, 3 legacy or malformed). Portable: it writes its own fixture and needs no project history. Copy the block from the file and run it; expected output `PASS: 5/8 rows valid`.

### smoke/commit_grouping.md
Tests `/commit`'s logical grouping. 6 files in 3 natural groups → expects 3 separate commits, not 1 (concatenation) or 6 (over-fragmentation).

### smoke/help_triage.md
A specification, not a script: four inputs (shapes A, B, C, no match) and the output shape `/help` should produce for each.

## When to run them

- **Gates**: every change. CI runs them anyway; running them locally first saves a red build.
- **Smoke fixtures**: before a release, and after editing the command a fixture covers.

## What is not tested

- `/weeklysummary`, `/quarto` and `/simplify` have no smoke fixtures.
- No test runs a full session end to end (install → `/setup` → `/startup` → … → `/coa`). `check_install.py` proves the files land and that the installed run-report helper writes its row; it does not prove a command behaves.

## Adding a fixture

1. Pick a command with a testable claim.
2. Create `tests/smoke/<command>_<angle>.md` with: purpose, fixture setup, success criteria, failure modes, automated verification where possible.
3. Add a section to this README.
4. Point to the fixture from the command file (for example, the end of `audit.md` points to `tests/smoke/audit_smoke.md`).

If the claim can be checked by a script, write a gate instead, give it a `--self-test`, and add a mutation check that proves the self-test can fail.
