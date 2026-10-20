#!/usr/bin/env python3
"""Prove emit_run_report_selftest.py catches each way the run-report helper could write a wrong or broken log.

    python3 scripts/emit_run_report_mutations.py    # exit 0 = every mutant caught

Each mutant is written to a temporary folder (the helper imports nothing from its own folder) and the self-test is
pointed at it with EMIT_RUN_REPORT. A mutant must still run: it is wrong, not broken.
"""
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "emit_run_report.py").read_text(encoding="utf-8")
SELFTEST = HERE / "emit_run_report_selftest.py"
MUTANTS = {
    "the header is never written": (
        "                csv.writer(f).writerow(COLUMNS)", "                pass",
        ["the header is the canonical 13 columns"]),
    "the header is written on every call": (
        "            if f.tell() == 0 and log.stat().st_size == 0:", "            if True:",
        ["a second call appends one row and does not repeat the header"]),
    "a column is dropped": (
        "*[values.get(k, \"\") for k in COUNT_FIELDS], str(report), notes]",
        "*[values.get(k, \"\") for k in COUNT_FIELDS], str(report)]",
        ["every row has exactly 13 cells"]),
    "the row is joined by hand, so commas and quotes break it": (
        "            csv.writer(f).writerow(row)", "            f.write(\",\".join(row) + \"\\n\")",
        ["a task summary with a comma and a quote round-trips through csv"]),
    "the lock is never taken": (
        "                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)\n                    break",
        "                    break",
        ["while the log is locked elsewhere the helper waits, then writes no row and says so"]),
    "the model default is a frozen old model ID": (
        'os.environ.get("CLAUDE_MODEL") or "unknown"', 'os.environ.get("CLAUDE_MODEL") or "claude-opus-4-7"',
        ["the model defaults to unknown and follows CLAUDE_MODEL when set"]),
    "the helper reads the user's config (helpers stay stateless)": (
        '    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".toolkit" / "evidence"',
        '    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())\n'
        '    cfg = Path(os.environ["HOME"]) / ".claude" / "toolkit-config.md"\n'
        '    m = re.search(r"evidence_dir:\\s*(\\S+)", cfg.read_text()) if cfg.exists() else None\n'
        '    return root / (m.group(1) if m else ".toolkit/evidence")',
        ["the helper is stateless: a config evidence_dir is not read"]),
    "the default folder follows the working directory, not the project root": (
        'Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".toolkit"', 'Path(os.getcwd()) / ".toolkit"',
        ["from a subfolder the log still goes to $CLAUDE_PROJECT_DIR/.toolkit/evidence"]),
    "--evidence-dir is ignored": (
        "evidence = Path(a.evidence_dir) if a.evidence_dir else default_evidence_dir()",
        "evidence = default_evidence_dir()",
        ["--evidence-dir sets the log folder"]),
    "the count columns are left empty": (
        "*[values.get(k, \"\") for k in COUNT_FIELDS]", "*[\"\" for k in COUNT_FIELDS]",
        ["agent_count, convergence_rate, agree_count and diverge_count fill their columns"]),
    "numbers are quoted in the YAML": (
        "if NUMBER.match(val) else", "if False else",
        ["numbers stay unquoted in YAML, strings are quoted"]),
    "an invalid outcome is accepted": (
        "        if a.outcome not in OUTCOMES:", "        if False:",
        ["an invalid outcome or a missing argument exits 0 and writes nothing"]),
    "an error escapes and breaks the calling command": (
        "    except Exception as e:  # never break the calling command",
        "    except ZeroDivisionError as e:  # never break the calling command",
        ["an unwritable log location exits 0"]),
}
SH = (HERE / "emit_run_report.sh").read_text(encoding="utf-8")
LAUNCHER_MUTANTS = {
    "the launcher has no python3 guard": (
        "command -v python3 >/dev/null 2>&1 || exit 0\n", "",
        ["the launcher with no python3 on PATH exits 0 and prints nothing"]),
    "the launcher looks for the .py in the working folder": (
        '    */*) here="${0%/*}" ;;', "    */*) here=. ;;",
        ["the launcher run from another folder writes the row"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
tmp = Path(tempfile.mkdtemp(prefix="emitrr_mut_"))
(tmp / "emit_run_report.py").write_text(SRC, encoding="utf-8")  # a mutant launcher runs the real helper beside it
jobs = [(n, SRC, o, nw, m, "emit_run_report.py", "EMIT_RUN_REPORT") for n, (o, nw, m) in MUTANTS.items()]
jobs += [(n, SH, o, nw, m, "emit_run_report.sh", "EMIT_RUN_REPORT_SH") for n, (o, nw, m) in LAUNCHER_MUTANTS.items()]
for name, src, old, new, must, fname, var in jobs:
    if src.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {src.count(old)} times")
        sys.exit(2)
    mut = tmp / ("_mutant_" + fname)
    mut.write_text(src.replace(old, new), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                       env=dict(os.environ, **{var: str(mut)}))
    if "self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the self-test did not finish\n{p.stderr[-300:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(jobs) - len(holes)}/{len(jobs)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
