# scripts/ — Shared Helper Scripts

Shared helper scripts called by slash commands. Written in bash with a silent-fail, callable-from-any-command contract.

## Contract for helpers here

1. **Silent-fail**: the script ALWAYS exits 0, even on invalid input. Errors go to stderr or a log file — never block the calling command's primary output.
2. **Stateless**: helpers don't read `~/.claude/toolkit-config.md` directly. The calling command passes required paths as arguments.
3. **One responsibility**: each helper does one thing well. If you need two helpers' worth of logic, write two helpers.
4. **bash -n clean**: `bash -n script.sh` must pass on all supported shells (bash 4+).

## Current helpers

### emit_run_report.sh — Run instrumentation (v1.1)

Writes a `run_report.md` with YAML frontmatter + appends a row to `.toolkit/evidence/run_log.csv` (default; override via `evidence_dir` in `~/.claude/toolkit-config.md`).

Called by: `/audit`, `/improve`, `/dailysummary`, `/commit`, `/startup`, `/runlog` (v1.1) — at the end of each command's execution flow.

**Usage** (one-line call from any SKILL.md):
```bash
bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh" \
  --command <name> \
  --run-dir <dir> \
  --outcome complete|partial|failed \
  --task-summary "<text>" \
  --fields "k1=v1 k2=v2 ..."
```

Schema: the canonical 13-column `run_log.csv` schema (documented in `DESIGN.md` § "v1.1 Canonical run_log.csv Schema").

Concurrency: uses `flock -w 2 -x 9` for atomic CSV append. `/pace`'s 4-agent parallelism and `/coa`'s 3-6 seat parallelism can call this simultaneously without corrupting the CSV.

---

## Adding a new helper

1. Write the bash script (silent-fail; arg parsing via `while case ...`)
2. `chmod +x` it
3. `bash -n` must pass
4. Add a section to this README (one paragraph + usage example)
5. If the helper produces artifacts downstream consumers depend on, document the schema in `DESIGN.md`

Do NOT add:
- Scripts in other languages (Python, Julia, etc.) — those go in the calling command's own directory structure
- Scripts that block the caller (network calls, long-running operations) — helpers must be fast

---

## Testing

Smoke tests for helpers live in `ai-research-toolkit/tests/smoke/`. Each helper should have a paired smoke fixture.

- `emit_run_report.sh` → smoke test embedded in `tests/smoke/runlog_parser.md` (verifies the CSV output)
