#!/usr/bin/env python3
"""Prove summary_folder_guard_selftest.py catches each way the summary-folder note could misfire or stay silent.

    python3 hooks/summary_folder_guard_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real hook (it imports _toolkit_config.py from its own folder) and deleted after its
run; the self-test is pointed at it with SUMMARY_GUARD_HOOK (or SUMMARY_GUARD_LAUNCHER). A mutant must still run.
How a folder matches is proven by _toolkit_config_mutations.py; here, only that this hook uses that matcher.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "summary_folder_guard.py").read_text(encoding="utf-8")
SELFTEST = HERE / "summary_folder_guard_selftest.py"
MUTANTS = {
    "it never notes": (
        "        if config.path_hit(folders, path, single_path=True):\n            return 0", "        if True:\n            return 0",
        ["a dated summary elsewhere gets a note"]),
    "a substring test replaces the shared path matcher": (
        "        if config.path_hit(folders, path, single_path=True):",
        "        if any(f.lower() in path.lower() for f in folders):",
        ["a longer folder that starts with the same words gets a note"]),
    "the path is matched as command text, not as one path": (
        "config.path_hit(folders, path, single_path=True)", "config.path_hit(folders, path)",
        ["a longer folder that starts with the same words gets a note"]),
    "an undated file is checked too": (
        '        if not (DATED.match(name) and name.lower().endswith(".md")):',
        '        if not name.lower().endswith(".md"):',
        ["an undated file elsewhere is silent"]),
    "a file that is not .md is checked too": (
        '        if not (DATED.match(name) and name.lower().endswith(".md")):', "        if not DATED.match(name):",
        ["a dated file that is not .md is silent"]),
    "every tool is checked, not only Write": (
        'payload.get("tool_name") != "Write"', "False",
        ["an Edit is not checked, only a Write"]),
    "the configured folder is ignored": (
        '        folders = [config.value("summary_folder") or "Daily Summary", config.value("weekly_folder") or "Weekly Summary"]',
        '        folders = ["Daily Summary", "Weekly Summary"]',
        ["summary_folder from the config is used"]),
    "an error escapes and breaks the session": (
        "    except Exception:\n        pass", "    except ZeroDivisionError:\n        pass",
        ["malformed input exits 0 and prints nothing"]),
}

LAUNCHER_SRC = (HERE / "summary_folder_guard.sh").read_text(encoding="utf-8")
LAUNCHER_MUTANTS = {
    "the launcher has no python3 guard": (
        "command -v python3 >/dev/null 2>&1 || exit 0\n", "",
        ["with no python3 on PATH the launcher exits 0 and prints nothing"]),
    "the launcher breaks when started by bare name": (
        "    *) here=. ;;", '    *) here="${0%/*}" ;;',
        ["the launcher works when started from its own folder by bare name"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
ALL = [(n, m, "py") for n, m in MUTANTS.items()] + [(n, m, "sh") for n, m in LAUNCHER_MUTANTS.items()]
for name, (old, new, must), kind in ALL:
    src = SRC if kind == "py" else LAUNCHER_SRC
    if src.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {src.count(old)} times")
        sys.exit(2)
    mut = HERE / ("_mutant_summary_folder_guard.py" if kind == "py" else "_mutant_summary_folder_guard.sh")
    mut.write_text(src.replace(old, new), encoding="utf-8")
    var = "SUMMARY_GUARD_HOOK" if kind == "py" else "SUMMARY_GUARD_LAUNCHER"
    try:
        p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                           env=dict(os.environ, **{var: str(mut)}))
    finally:
        mut.unlink()
    if "summary_folder_guard self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(p.stdout + p.stderr)[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(ALL) - len(holes)}/{len(ALL)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
