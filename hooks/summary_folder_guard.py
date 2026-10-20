#!/usr/bin/env python3
"""summary_folder_guard.py — PostToolUse (Write) hook: a note when a dated summary lands outside the summary folders.

After a Write, if the file is a `.md` whose name starts with a date (YYYY-MM-DD) and its path names neither
`summary_folder` nor `weekly_folder` from ~/.claude/toolkit-config.md (defaults "Daily Summary" and
"Weekly Summary"), it adds one line of context for Claude. It never blocks: you may mean to write it there.

A folder matches as whole path components, ignoring case (_toolkit_config.path_pattern with single_path), so
`Daily Summary` matches `notes/Daily Summary/2026-10-20.md` and not `Daily Summary Archive/2026-10-20.md`.
Why Python. The shell version read the path with `grep -o` and matched the folder name as a regular expression, so a
folder name holding a regex character matched the wrong paths.
Never breaks a session: any error exits 0 and prints nothing.
Self-test: python3 hooks/summary_folder_guard_selftest.py   Mutations: python3 hooks/summary_folder_guard_mutations.py
"""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import _toolkit_config as config  # noqa: E402
except ImportError:  # copied without its config reader: no folder can be checked, so it says nothing
    config = None

DATED = re.compile(r"^\d{4}-\d{2}-\d{2}")


def main():
    try:
        if config is None:
            return 0
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict) or payload.get("tool_name") != "Write":
            return 0
        path = (payload.get("tool_input") or {}).get("file_path") or ""
        name = os.path.basename(path)
        if not (DATED.match(name) and name.lower().endswith(".md")):
            return 0
        folders = [config.value("summary_folder") or "Daily Summary", config.value("weekly_folder") or "Weekly Summary"]
        if config.path_hit(folders, path, single_path=True):
            return 0
        text = (f"[Summary folder guard] A dated file was written to '{path}', outside the summary folders "
                f"('{folders[0]}' / '{folders[1]}' in ~/.claude/toolkit-config.md). If that is intended, nothing to "
                "do. If it is a daily or weekly summary, it may be in the wrong place.")
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": text}}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
