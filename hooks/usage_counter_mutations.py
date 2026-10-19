#!/usr/bin/env python3
"""Prove usage_counter_selftest.py catches each way the counter could miscount or break a session.

    python3 hooks/usage_counter_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real hook and deleted after its run; the self-test is pointed at it with
USAGE_COUNTER_HOOK. A mutant must still run: it is wrong, not broken.

One mutation is deliberately absent: dropping the `tool_name == "Skill"` test changes nothing observable,
because a non-Skill payload carries no tool_input.skill and is rejected one line later. That check is
structural (defence in depth), so there is no behaviour for a test to catch.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "usage_counter.py").read_text(encoding="utf-8")
SELFTEST = HERE / "usage_counter_selftest.py"
MUTANTS = {
    "the skill name is read from the wrong field": (
        'name = (payload.get("tool_input") or {}).get("skill", "")',
        'name = (payload.get("tool_input") or {}).get("args", "")',
        ["a Skill call writes one row"]),
    "typed slash commands are not counted": (
        'if ev == "UserPromptSubmit":', "if False:",
        ["a typed slash command writes one row"]),
    "a path is counted as a command": (
        r'TYPED = re.compile(r"^\s*/([A-Za-z][A-Za-z0-9_.:-]*)(?=\s|$)")',
        r'TYPED = re.compile(r"^\s*/([A-Za-z][A-Za-z0-9_.:-]*)")',
        ["an absolute path is not a command"]),
    "the header is written on every call": (
        "new = not path.exists() or path.stat().st_size == 0", "new = True",
        ["two calls give two rows under one header"]),
    "an error escapes and breaks the session": (
        "    except Exception:\n        pass", "    except ZeroDivisionError:\n        pass",
        ["malformed input exits 0", "an unwritable log never breaks the session"]),
    "the config's evidence_dir is ignored": (
        "        if m:\n", "        if False:\n",
        ["without USAGE_EVENTS_CSV the log goes to the config's evidence_dir"]),
    "the default log goes to the wrong folder": (
        '    evidence = ".toolkit/evidence"', '    evidence = "evidence"',
        ["with no config the log goes to .toolkit/evidence in the project"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_usage_counter.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                           env=dict(os.environ, USAGE_COUNTER_HOOK=str(mut)))
    finally:
        mut.unlink()
    red = [ln.strip()[5:] for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
