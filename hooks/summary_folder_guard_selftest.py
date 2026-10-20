#!/usr/bin/env python3
"""Self-test for summary_folder_guard.py — the note when a dated summary lands outside the summary folders.

Run:
    python3 hooks/summary_folder_guard_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch. The folders come from a temporary config
file named by TOOLKIT_CONFIG. Point it at a different hook with SUMMARY_GUARD_HOOK=<path> and a different launcher
with SUMMARY_GUARD_LAUNCHER=<path> (the mutation proof does).

Why the cases look like this: the shell hook this replaces matched the folder name as a regular expression and
anywhere in the path, so a folder name with a regex character, and a longer folder that starts with the same words,
each have a case.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = Path(os.environ.get("SUMMARY_GUARD_HOOK", HERE / "summary_folder_guard.py"))
LAUNCHER = Path(os.environ.get("SUMMARY_GUARD_LAUNCHER", HERE / "summary_folder_guard.sh"))
FAILS = []


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def config_file(text):
    p = Path(tempfile.mkdtemp(prefix="sumguard_")) / "toolkit-config.md"
    if text is not None:
        p.write_text(text, encoding="utf-8")
    return p


DEFAULTS = config_file(None)


def note(path, tool="Write", cfg=DEFAULTS, argv=None, raw=None, **kw):
    """NOTE, SILENT or ERROR."""
    data = raw if raw is not None else json.dumps({"tool_name": tool, "tool_input": {"file_path": path}})
    env = dict(os.environ, TOOLKIT_CONFIG=str(cfg), **kw.pop("env", {}))
    r = subprocess.run(argv or [sys.executable, str(HOOK)], input=data, capture_output=True, text=True,
                       timeout=30, env=env, **kw)
    if r.returncode != 0 or r.stderr.strip():
        return "ERROR"
    if not r.stdout.strip():
        return "SILENT"
    try:
        json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
        return "NOTE"
    except (ValueError, KeyError, TypeError):
        return "ERROR"


check("a dated summary in Daily Summary is silent", note("/p/Daily Summary/2026-10-20_work.md") == "SILENT")
check("a dated summary in Weekly Summary is silent", note("/p/Weekly Summary/2026-10-20.md") == "SILENT")
check("the folder is matched ignoring case", note("/p/daily summary/2026-10-20.md") == "SILENT")
check("a dated summary elsewhere gets a note", note("/p/notes/2026-10-20_work.md") == "NOTE")
check("a longer folder that starts with the same words gets a note",
      note("/p/Daily Summary Archive/2026-10-20.md") == "NOTE")
check("an undated file elsewhere is silent", note("/p/notes/plan.md") == "SILENT")
check("a dated file that is not .md is silent", note("/p/data/2026-10-20_results.csv") == "SILENT")
check("an Edit is not checked, only a Write", note("/p/notes/2026-10-20.md", tool="Edit") == "SILENT")

custom = config_file("summary_folder: logs/daily\nweekly_folder: logs (weekly)\n")
check("summary_folder from the config is used", note("/p/logs/daily/2026-10-20.md", cfg=custom) == "SILENT")
check("the default folder no longer counts once the config names another",
      note("/p/Daily Summary/2026-10-20.md", cfg=custom) == "NOTE")
check("a folder name with regex characters is matched literally",
      note("/p/logs (weekly)/2026-10-20.md", cfg=custom) == "SILENT"
      and note("/p/logs weekly/2026-10-20.md", cfg=custom) == "NOTE")

check("malformed input exits 0 and prints nothing", note("", raw="{not json") == "SILENT")
check("the launcher notes too", note("/p/notes/2026-10-20.md", argv=["bash", str(LAUNCHER)]) == "NOTE")
check("the launcher works when started from its own folder by bare name",
      note("/p/notes/2026-10-20.md", argv=["bash", LAUNCHER.name], cwd=LAUNCHER.parent) == "NOTE")
r = subprocess.run(["/bin/bash", str(LAUNCHER)], input="{}", capture_output=True, text=True, timeout=30,
                   env=dict(os.environ, PATH="/nonexistent"))
check("with no python3 on PATH the launcher exits 0 and prints nothing", r.returncode == 0 and not r.stdout and not r.stderr)

print(f"\nsummary_folder_guard self-test: {'all passed' if not FAILS else f'{len(FAILS)} failed'}")
sys.exit(1 if FAILS else 0)
