#!/usr/bin/env python3
"""usage_counter.py — count every tool use: one CSV row per skill call or typed slash command.

A counter that drops calls reads as low usage, which is indistinguishable from the truth, so this
hook has no skip list and parses the hook payload as JSON (a `grep -o` extractor truncates at the
first quote inside a value and silently loses calls).

Events (register both in .claude/settings.json; see hooks/README.md):
  PostToolUse, matcher Skill  -> source "skill", name = tool_input.skill
  UserPromptSubmit            -> source "typed", when the prompt starts with /<name>

A typed /x that Claude then runs through the Skill tool produces both rows; the report
(scripts/usage_counts.py) merges them. This hook only records.

It must never break a session: any error exits 0 and prints nothing.

Log, first match wins:
  1. $USAGE_EVENTS_CSV
  2. <evidence_dir>/usage_events.csv, with evidence_dir read from ~/.claude/toolkit-config.md
     (relative paths resolve against the project root, $CLAUDE_PROJECT_DIR or the working directory)
  3. <project root>/.toolkit/evidence/usage_events.csv
Columns: ts_utc, session_id, source, name
Self-test: python3 hooks/usage_counter_selftest.py
"""
import csv
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

TYPED = re.compile(r"^\s*/([A-Za-z][A-Za-z0-9_.:-]*)(?=\s|$)")
FIELDS = ["ts_utc", "session_id", "source", "name"]
EVIDENCE_KEY = re.compile(r"^\s*evidence_dir:\s*(.+?)\s*$", re.M)


def event_name(payload: dict):
    """(source, name) for a payload that is a tool use, else None."""
    ev = payload.get("hook_event_name", "")
    if ev == "PostToolUse" and payload.get("tool_name") == "Skill":
        name = (payload.get("tool_input") or {}).get("skill", "")
        return ("skill", name.strip()) if name.strip() else None
    if ev == "UserPromptSubmit":
        m = TYPED.match(payload.get("prompt") or "")
        return ("typed", m.group(1)) if m else None
    return None


def log_path() -> Path:
    if os.environ.get("USAGE_EVENTS_CSV"):
        return Path(os.environ["USAGE_EVENTS_CSV"])
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
    cfg = Path(os.environ.get("HOME", "~")).expanduser() / ".claude" / "toolkit-config.md"
    evidence = ".toolkit/evidence"
    if cfg.exists():
        m = EVIDENCE_KEY.search(cfg.read_text(encoding="utf-8", errors="replace"))
        if m:
            evidence = m.group(1).split("#")[0].strip().strip("\"'") or evidence
    ev = Path(evidence).expanduser()
    return (ev if ev.is_absolute() else root / ev) / "usage_events.csv"


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        hit = event_name(payload) if isinstance(payload, dict) else None
        if not hit:
            return 0
        path = log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        new = not path.exists() or path.stat().st_size == 0
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            if new:
                w.writerow(FIELDS)
            ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            w.writerow([ts, payload.get("session_id", ""), hit[0], hit[1]])
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
