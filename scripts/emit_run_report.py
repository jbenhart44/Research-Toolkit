#!/usr/bin/env python3
"""emit_run_report.py — write a run_report.md and append one row to run_log.csv for a toolkit command.

Commands call it with one line at the end of a run (the installer puts it at ~/.claude/toolkit/scripts/):

    python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py" \\
      --command audit --run-dir "<dir>" --outcome complete \\
      --task-summary "audit of paper.md" --fields "citations_checked=12 mismatches=0 verdict=pass"

Required: --command, --run-dir, --outcome (complete | partial | failed).
Optional: --fields "k1=v1 k2=v2" (space-separated), --task-summary, --evidence-dir, --tool-version.

Writes <run-dir>/run_report.md (YAML frontmatter + body) and appends one row to <evidence-dir>/run_log.csv, creating
the canonical 13-column header when the file is absent or empty. The evidence folder is --evidence-dir, else
<project root>/.toolkit/evidence, where the project root is $CLAUDE_PROJECT_DIR or the working directory. Like every
helper here it is stateless: it never reads ~/.claude/toolkit-config.md, so a command that uses a configured
evidence_dir passes it as --evidence-dir.

The model column is $CLAUDE_MODEL when set, else "unknown": the helper cannot see which model ran.

It never breaks the calling command: every error exits 0, and diagnostics go to a log file in the system temp folder.
If another process holds the log's lock for more than 2 seconds, no row is written and the helper says so on stdout.

This file replaces the logic of emit_run_report.sh (v1.1-v2.0.1), which is now a launcher for it.
Self-test: python3 scripts/emit_run_report_selftest.py   Mutations: python3 scripts/emit_run_report_mutations.py
"""
import argparse
import csv
import datetime
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

COLUMNS = ["run_id", "tool", "tool_version", "date", "task_summary", "outcome", "model", "agent_count",
           "convergence_rate", "agree_count", "diverge_count", "report_path", "notes"]
OUTCOMES = ("complete", "partial", "failed")
COUNT_FIELDS = ("agent_count", "convergence_rate", "agree_count", "diverge_count")
NUMBER = re.compile(r"^-?[0-9]+(\.[0-9]+)?$")
LOCK_SECONDS = 2.0


def diag(msg: str) -> None:
    try:
        with open(Path(tempfile.gettempdir()) / "emit_run_report_errors.log", "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} {msg}\n")
    except Exception:
        pass


def default_evidence_dir() -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()) / ".toolkit" / "evidence"


def parse_fields(text: str) -> list[tuple[str, str]]:
    pairs = []
    for token in text.split():
        key, _, val = token.partition("=")
        if key:
            pairs.append((key, val))
    return pairs


def yaml_str(s: str) -> str:
    return '"' + s.replace('"', '\\"') + '"'


def build_report(run_id, command, tool_version, date, ts, model, summary, outcome, pairs) -> str:
    lines = ["---", 'schema_version: "1.0"', f"run_id: {yaml_str(run_id)}", f"tool: {yaml_str(command)}",
             f"tool_version: {yaml_str(tool_version)}", f"date: {yaml_str(date)}", f"timestamp: {yaml_str(ts)}",
             f"model: {yaml_str(model)}"]
    if summary:
        lines.append(f"task_summary: {yaml_str(summary)}")
    lines.append(f"outcome: {yaml_str(outcome)}")
    for key, val in pairs:
        lines.append(f"{key}: {val}" if NUMBER.match(val) else f"{key}: {yaml_str(val)}")
    lines += ["---", "", "## Task", "", summary or f"Run of /{command} on {date}.", "", "## Fields Captured", ""]
    lines += [f"- `{k}={v}`" for k, v in pairs] or ["- (none)"]
    lines += ["", "## Evidence Footer", "", f"- Command: /{command}", f"- Tool version: {tool_version}",
              f"- Run ID: {run_id}", f"- Timestamp: {ts}", f"- Model: {model}",
              "- Verifiable: re-running this command on the same inputs produces the same fields (modulo timestamp)."]
    return "\n".join(lines) + "\n"


def append_row(log: Path, row: list[str]) -> bool:
    """Append under an exclusive lock; False if the lock is not had within LOCK_SECONDS."""
    try:
        import fcntl
    except ImportError:  # no fcntl (Windows): append without the lock
        fcntl = None
    with open(log, "a", newline="", encoding="utf-8") as f:
        if fcntl is not None:
            deadline = time.time() + LOCK_SECONDS
            while True:
                try:
                    fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.time() >= deadline:
                        return False
                    time.sleep(0.05)
        try:
            if f.tell() == 0 and log.stat().st_size == 0:
                csv.writer(f).writerow(COLUMNS)
            csv.writer(f).writerow(row)
            f.flush()
        finally:
            if fcntl is not None:
                fcntl.flock(f, fcntl.LOCK_UN)
    return True


def main() -> int:
    try:
        ap = argparse.ArgumentParser(add_help=False)
        for flag in ("--command", "--run-dir", "--outcome", "--fields", "--task-summary", "--evidence-dir",
                     "--tool-version"):
            ap.add_argument(flag, default="")
        a, _unknown = ap.parse_known_args()
        if not (a.command and a.run_dir and a.outcome):
            diag(f"missing required arg (command={a.command!r} run-dir={a.run_dir!r} outcome={a.outcome!r})")
            return 0
        if a.outcome not in OUTCOMES:
            diag(f"invalid outcome {a.outcome!r} (must be complete|partial|failed)")
            return 0
        tool_version = a.tool_version or "v1.1"
        run_dir = Path(a.run_dir)
        evidence = Path(a.evidence_dir) if a.evidence_dir else default_evidence_dir()
        run_dir.mkdir(parents=True, exist_ok=True)
        evidence.mkdir(parents=True, exist_ok=True)

        now = datetime.datetime.now(datetime.timezone.utc)
        ts, date = now.strftime("%Y-%m-%dT%H:%M:%SZ"), datetime.date.today().isoformat()
        model = os.environ.get("CLAUDE_MODEL") or "unknown"
        pairs = parse_fields(a.fields)
        report = run_dir / "run_report.md"
        report.write_text(build_report(run_dir.name, a.command, tool_version, date, ts, model, a.task_summary,
                                       a.outcome, pairs), encoding="utf-8")

        values = dict(pairs)
        notes = json.dumps(values, separators=(",", ":")) if pairs else "{}"
        row = [run_dir.name, a.command, tool_version, date, a.task_summary, a.outcome, model,
               *[values.get(k, "") for k in COUNT_FIELDS], str(report), notes]
        log = evidence / "run_log.csv"
        if append_row(log, row):
            print(f"run_report: {report}")
            print(f"run_log:    {log} (1 row appended)")
        else:
            diag(f"lock timeout on {log}")
            print(f"run_report: {report}")
            print(f"run_log:    {log} (NOT appended: the log was locked by another process for {LOCK_SECONDS:g} s)")
    except Exception as e:  # never break the calling command
        diag(f"{type(e).__name__}: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
