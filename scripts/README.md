# scripts/ — Shared Helper Scripts

Shared helper scripts called by slash commands, plus the usage report. The helpers follow a silent-fail, callable-from-any-command contract.

## usage_counts.py — how often each command was used

Reads the CSV the usage-counter hook writes (`hooks/usage_counter.py`, into your `evidence_dir`) and prints a count per command with first and last use. Counts only; it never reads task text.

```bash
python3 scripts/usage_counts.py                          # every known tool in your log
python3 scripts/usage_counts.py --tools coa,pace,audit   # only these
python3 scripts/usage_counts.py --events path.csv        # a different counter file
python3 scripts/usage_counts.py --backfill log.md        # also count '## /name — YYYY-MM-DD' headings from an older log
python3 scripts/usage_counts.py --json counts.json       # also write the counts as JSON
python3 scripts/usage_counts.py --project ~/my-project   # read the log of a project other than the current folder
python3 scripts/usage_counts.py --self-test              # and: python3 scripts/usage_counts_mutations.py
```

When `--backfill` is given, the older log counts only days before the counter's first event, so a day is never counted twice. Every run prints a balance line: live plus backfilled equals the total.

## Contract for helpers here

1. **Silent-fail**: the script ALWAYS exits 0, even on invalid input. Errors go to stderr or a log file — never block the calling command's primary output.
2. **Stateless**: helpers don't read `~/.claude/toolkit-config.md` directly. The calling command passes required paths as arguments.
3. **One responsibility**: each helper does one thing well. If you need two helpers' worth of logic, write two helpers.
4. **bash -n clean, bash 3.2 safe**: `bash -n script.sh` must pass, and the script must run on macOS's system bash 3.2 (no `declare -A`, no `mapfile`). CI parses every script.

## Current helpers

### emit_run_report.py — Run instrumentation (v1.1; Python since v2.0.2)

Writes a `run_report.md` with YAML frontmatter + appends a row to `<project>/.toolkit/evidence/run_log.csv`, or to the folder given as `--evidence-dir`. It does not read `~/.claude/toolkit-config.md` (rule 2 above), so a command that uses a configured `evidence_dir` passes it.

Called by: `/audit`, `/improve`, `/daily-summary`, `/commit`, `/startup`, `/run-log`, `/help` — at the end of each command's execution flow. `install.sh` copies it to `~/.claude/toolkit/scripts/` in every install mode; before v2.0.2 it was never installed, so these calls found nothing and no run report reached a user. `emit_run_report.sh` is now a launcher for the Python file, kept for anyone calling it from a clone.

**Usage** (one-line call from any command file):
```bash
python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py" \
  --command <name> \
  --run-dir <dir> \
  --outcome complete|partial|failed \
  --task-summary "<text>" \
  --fields "k1=v1 k2=v2 ..."
```

Schema: the canonical 13-column `run_log.csv` schema (documented in `DESIGN.md` § "v1.1 Canonical run_log.csv Schema"). The model column is `$CLAUDE_MODEL` when set, else `unknown` (the shell helper wrote one fixed, older model ID).

Concurrency: an exclusive `fcntl` lock with a 2-second wait. `/pace`'s 4-agent parallelism and `/coa`'s 3-6 seat parallelism can call this simultaneously without corrupting the CSV. If the lock is not had in time, no row is written and the helper says so. The shell helper used the `flock` command and appended with no lock where it was missing, which includes macOS (none on a macOS 26.7 test machine).

## Checks and tools (from v2.2.0)

These are not helpers: **their exit code is their verdict**, so the silent-fail rule above does not apply. Each exits 0 on a clean result, 1 when it found something, and 2 when it could not look (a missing path, no input), which is never a pass. Each has a `--self-test` and a `<name>_mutations.py` beside it.

### check_coa_evidence_paths.py — do the paths in a `/coa` brief resolve?

`/coa` runs it on each seat's evidence paths before starting the seats (Step 0b), so a seat is never sent to a path that does not exist and then reports the absence as a finding. Installed to `~/.claude/toolkit/scripts/` in every mode.

```bash
python3 "$HOME/.claude/toolkit/scripts/check_coa_evidence_paths.py" brief.md data/ "Shared Folder/report.pdf"
python3 scripts/check_coa_evidence_paths.py --self-test     # compares with tests/golden/check_coa_evidence_paths.json
```

A port of a Julia original. The golden file records the original's own verdicts on a fixed tree, and the self-test requires the same verdict for every input: an independent implementation, not a re-reading.

### check_heading_collisions.py — two sections claiming to be the same section

Reports sibling markdown headings that are equal ignoring case and punctuation (`## Next steps` and `## Next Steps`). Ignores fenced code, front matter, HTML comments and indented code; counts and names what it could not check. Report mode exits 0; `--check` exits 1 on a collision.

```bash
python3 scripts/check_heading_collisions.py --check notes.md docs/
```

### check_scratchpad_leak.py — work living only in a session scratchpad

Lists the files of value (by extension) in a scratchpad whose content is nowhere in the project, compared by SHA-256, so a renamed copy counts as saved and an edited one does not. It reports; it never moves or removes anything.

```bash
python3 scripts/check_scratchpad_leak.py <scratchpad folder> --repo .
```

### register_hooks.py — the settings entries for the hooks you choose

Prints the `settings.json` block for the hooks you name (or `--all`, or `--list`), each registered unconditionally. It never edits a file; `install.sh --hooks` copies the hooks and registers none.

```bash
python3 scripts/register_hooks.py --list
python3 scripts/register_hooks.py protect_files usage_counter
```

---

## Adding a new helper

1. Write the script in Python, standard library only (silent-fail; always exit 0)
2. Give it a self-test and a mutation file, like `emit_run_report_selftest.py` and `emit_run_report_mutations.py`
3. If a command calls it, add its name to `RUNTIME_SCRIPTS` in `install.sh` and call it as `python3 "$HOME/.claude/toolkit/scripts/<name>.py"`. A script that is not installed is not there for a user: that is how run reports went missing from v1.1 to v2.0.1. `tests/check_install.py` fails when a command calls a script the installer does not copy
4. Add a section to this README (one paragraph + usage example)
5. If the helper produces artifacts downstream consumers depend on, document the schema in `DESIGN.md`

Do NOT add:
- Logic in bash beyond argument handling and file appends — anything that parses, counts or decides belongs in a Python script with a `--self-test` (like `usage_counts.py`)
- Scripts that block the caller (network calls, long-running operations) — helpers must be fast

---

## Testing

Smoke tests for helpers live in `tests/smoke/`. Each helper should have a paired smoke fixture.

- `emit_run_report.py` → `python3 scripts/emit_run_report_selftest.py` (19 cases) and `python3 scripts/emit_run_report_mutations.py` (15 mutants, two of them in the `.sh` launcher; each must turn its case red); `tests/smoke/runlog_parser.md` checks the CSV a reader sees
