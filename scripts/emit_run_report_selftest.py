#!/usr/bin/env python3
"""Self-test for emit_run_report.py — the run-report helper that toolkit commands call at the end of a run.

Run:
    python3 scripts/emit_run_report_selftest.py      (exit 0 = every case passed)
Point it at a different helper with EMIT_RUN_REPORT=<path> (the mutation proof does).

Each case runs the helper as a subprocess in a fresh temporary project, with HOME pointed at a temporary folder so
the user's real ~/.claude/toolkit-config.md is never read.
"""
import csv
import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HELPER = Path(os.environ.get("EMIT_RUN_REPORT", Path(__file__).resolve().parent / "emit_run_report.py"))
LAUNCHER = Path(os.environ.get("EMIT_RUN_REPORT_SH", Path(__file__).resolve().parent / "emit_run_report.sh"))
FAILS = []
COLS = ["run_id", "tool", "tool_version", "date", "task_summary", "outcome", "model", "agent_count",
        "convergence_rate", "agree_count", "diverge_count", "report_path", "notes"]


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def fresh():
    root = Path(tempfile.mkdtemp(prefix="emitrr_"))
    (root / "home").mkdir()
    (root / "proj").mkdir()
    return root


def run(root, *args, env_extra=None, timeout=30):
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_MODEL", "CLAUDE_PROJECT_DIR")}
    env.update(HOME=str(root / "home"), CLAUDE_PROJECT_DIR=str(root / "proj"))
    env.update(env_extra or {})
    return subprocess.run([sys.executable, str(HELPER), *args], capture_output=True, text=True,
                          cwd=root / "proj", env=env, timeout=timeout)


def json_or_none(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def rows(log):
    if not log.exists():
        return []
    with open(log, newline="", encoding="utf-8") as f:
        return list(csv.reader(f))


def main():
    # 1. positive control: a report and one row
    root = fresh()
    rd = root / "proj" / "runs" / "2026-10-20_120000_x"
    r = run(root, "--command", "audit", "--run-dir", str(rd), "--outcome", "complete",
            "--task-summary", "audit the paper", "--fields", "citations_checked=12 verdict=pass")
    log = root / "proj" / ".toolkit" / "evidence" / "run_log.csv"
    got = rows(log)
    report = (rd / "run_report.md").read_text(encoding="utf-8") if (rd / "run_report.md").exists() else ""
    check("writes run_report.md and one log row (positive control)",
          r.returncode == 0 and report.startswith("---\n") and len(got) == 2)
    check("the header is the canonical 13 columns", got and got[0] == COLS)
    check("every row has exactly 13 cells", got and all(len(x) == 13 for x in got))
    row = dict(zip(COLS, got[1])) if len(got) > 1 else {}
    check("the row carries run_id, tool, outcome and report path",
          row.get("run_id") == rd.name and row.get("tool") == "audit" and row.get("outcome") == "complete"
          and row.get("report_path", "").endswith("run_report.md"))
    check("numbers stay unquoted in YAML, strings are quoted",
          "citations_checked: 12\n" in report and 'verdict: "pass"' in report)
    check("notes holds the fields as compact JSON",
          json_or_none(row.get("notes")) == {"citations_checked": "12", "verdict": "pass"})

    # 2. a second call appends under the same header
    run(root, "--command", "audit", "--run-dir", str(rd.parent / "second"), "--outcome", "partial")
    got = rows(log)
    check("a second call appends one row and does not repeat the header",
          len(got) == 3 and sum(1 for x in got if x == COLS) == 1)

    # 3. CSV escaping: a task summary with a comma and a quote round-trips
    root = fresh()
    tricky = 'check "this", then that'
    run(root, "--command", "commit", "--run-dir", str(root / "proj" / "r1"), "--outcome", "complete",
        "--task-summary", tricky)
    got = rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")
    check("a task summary with a comma and a quote round-trips through csv",
          len(got) == 2 and len(got[1]) == 13 and got[1][4] == tricky)

    # 4. the four count columns are filled from fields
    root = fresh()
    run(root, "--command", "pace", "--run-dir", str(root / "proj" / "r"), "--outcome", "complete",
        "--fields", "agent_count=4 convergence_rate=0.75 agree_count=3 diverge_count=1")
    got = rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")
    row = dict(zip(COLS, got[1])) if len(got) > 1 else {}
    check("agent_count, convergence_rate, agree_count and diverge_count fill their columns",
          (row.get("agent_count"), row.get("convergence_rate"), row.get("agree_count"), row.get("diverge_count"))
          == ("4", "0.75", "3", "1"))

    # 5. model: unknown by default, CLAUDE_MODEL when set
    root = fresh()
    run(root, "--command", "audit", "--run-dir", str(root / "proj" / "a"), "--outcome", "complete")
    run(root, "--command", "audit", "--run-dir", str(root / "proj" / "b"), "--outcome", "complete",
        env_extra={"CLAUDE_MODEL": "sonnet"})
    got = rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")
    check("the model defaults to unknown and follows CLAUDE_MODEL when set",
          len(got) == 3 and got[1][6] == "unknown" and got[2][6] == "sonnet")

    # 6. bad input never breaks the caller and writes nothing
    root = fresh()
    r1 = run(root, "--command", "audit", "--run-dir", str(root / "proj" / "x"), "--outcome", "maybe")
    r2 = run(root, "--command", "audit", "--outcome", "complete")
    check("an invalid outcome or a missing argument exits 0 and writes nothing",
          r1.returncode == 0 and r2.returncode == 0
          and not (root / "proj" / ".toolkit" / "evidence" / "run_log.csv").exists())

    # 7. where the log goes: --evidence-dir, else <project root>/.toolkit/evidence; the config is never read
    root = fresh()
    (root / "home" / ".claude").mkdir()
    (root / "home" / ".claude" / "toolkit-config.md").write_text(
        "## Folder Paths\nevidence_dir: notes/evidence  # mine\n", encoding="utf-8")
    run(root, "--command", "audit", "--run-dir", str(root / "proj" / "c"), "--outcome", "complete")
    check("the helper is stateless: a config evidence_dir is not read",
          len(rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")) == 2
          and not (root / "proj" / "notes").exists())
    run(root, "--command", "audit", "--run-dir", str(root / "proj" / "d"), "--outcome", "complete",
        "--evidence-dir", str(root / "proj" / "explicit"))
    check("--evidence-dir sets the log folder", len(rows(root / "proj" / "explicit" / "run_log.csv")) == 2)

    # 7b. the project root is $CLAUDE_PROJECT_DIR, not the working directory
    root = fresh()
    (root / "proj" / "sub").mkdir()
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_MODEL",)}
    env.update(HOME=str(root / "home"), CLAUDE_PROJECT_DIR=str(root / "proj"))
    subprocess.run([sys.executable, str(HELPER), "--command", "audit", "--run-dir", str(root / "proj" / "g"),
                    "--outcome", "complete"], cwd=root / "proj" / "sub", env=env, capture_output=True, timeout=30)
    check("from a subfolder the log still goes to $CLAUDE_PROJECT_DIR/.toolkit/evidence",
          len(rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")) == 2
          and not (root / "proj" / "sub" / ".toolkit").exists())

    # 8. an unwritable evidence location never breaks the caller
    root = fresh()
    blocker = root / "proj" / "blocked"
    blocker.write_text("a file where the folder should be", encoding="utf-8")
    r = run(root, "--command", "audit", "--run-dir", str(root / "proj" / "e"), "--outcome", "complete",
            "--evidence-dir", str(blocker / "sub"))
    check("an unwritable log location exits 0", r.returncode == 0)

    # 9. the lock is honoured: while another process holds it, the helper does not append
    root = fresh()
    ev = root / "proj" / ".toolkit" / "evidence"
    ev.mkdir(parents=True)
    log = ev / "run_log.csv"
    log.write_text(",".join(COLS) + "\n", encoding="utf-8")
    with open(log, "a") as held:
        fcntl.flock(held, fcntl.LOCK_EX)
        t0 = time.time()
        r = run(root, "--command", "audit", "--run-dir", str(root / "proj" / "f"), "--outcome", "complete")
        waited = time.time() - t0
        fcntl.flock(held, fcntl.LOCK_UN)
    check("while the log is locked elsewhere the helper waits, then writes no row and says so",
          r.returncode == 0 and len(rows(log)) == 1 and waited >= 1.5 and "NOT appended" in r.stdout)

    # 10. concurrent calls each land one intact row
    root = fresh()
    procs = []
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_MODEL",)}
    env.update(HOME=str(root / "home"), CLAUDE_PROJECT_DIR=str(root / "proj"))
    for i in range(12):
        procs.append(subprocess.Popen([sys.executable, str(HELPER), "--command", "coa", "--run-dir",
                                       str(root / "proj" / f"p{i}"), "--outcome", "complete",
                                       "--task-summary", f"parallel run {i}, with a comma"],
                                      cwd=root / "proj", env=env, stdout=subprocess.DEVNULL))
    for p in procs:
        p.wait(timeout=60)
    got = rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")
    check("12 concurrent calls give 12 intact 13-cell rows under one header",
          len(got) == 13 and got[0] == COLS and all(len(x) == 13 for x in got[1:]))

    # 11. the shell launcher: finds the .py beside itself from any folder, and is silent without python3
    root = fresh()
    env = {k: v for k, v in os.environ.items() if k not in ("CLAUDE_MODEL",)}
    # the interpreter running this test first on PATH: a python3 wrapper that reads $HOME breaks under a fake HOME
    env.update(HOME=str(root / "home"), CLAUDE_PROJECT_DIR=str(root / "proj"),
               PATH=os.pathsep.join([str(Path(sys.executable).parent), os.environ.get("PATH", "")]))
    r = subprocess.run(["bash", str(LAUNCHER), "--command", "commit", "--run-dir", str(root / "proj" / "h"),
                        "--outcome", "complete"], cwd=root / "home", env=env, capture_output=True, text=True,
                       timeout=30)
    got = rows(root / "proj" / ".toolkit" / "evidence" / "run_log.csv")
    check("the launcher run from another folder writes the row", r.returncode == 0 and len(got) == 2
          and got[1][1] == "commit")
    bare = dict(env, PATH=str(root / "empty"))
    r = subprocess.run(["/bin/bash", str(LAUNCHER), "--command", "commit", "--run-dir", str(root / "proj" / "i"),
                        "--outcome", "complete"], cwd=root / "proj", env=bare, capture_output=True, text=True,
                       timeout=30)
    check("the launcher with no python3 on PATH exits 0 and prints nothing",
          r.returncode == 0 and r.stdout == "" and r.stderr == "")

    print(f"emit_run_report self-test: {len(FAILS)} failed" if FAILS else "emit_run_report self-test: all passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
