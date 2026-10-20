#!/usr/bin/env python3
"""Prove guard_hook_selftest.py catches each way the /guard-hook runner could build, prove or register a guard wrongly.

    python3 shared/skills/guard-hook/assets/guard_hook_mutations.py    # exit 0 = every mutant caught (a few minutes)

Each mutant is written to a temporary folder and the self-test is pointed at it with GUARD_HOOK_RUN. A mutant must
still run: it is wrong, not broken. The installer does not copy this file.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "guard_hook_run.py").read_text(encoding="utf-8")
SELFTEST = HERE / "guard_hook_selftest.py"
MUTANTS = {
    "the sentinel does not stop a registration": (
        "        if os.path.exists(path) and UNAUTHORED in open(path).read():", "        if False:",
        ["MUST FAIL: register refuses an unauthored guard (exit 3)"]),
    "a failing self-test does not stop a registration": (
        "    if r.returncode != 0:\n        sys.stderr.write(r.stdout)\n        return die(4, \"refused: self-test exits",
        "    if False:\n        sys.stderr.write(r.stdout)\n        return die(4, \"refused: self-test exits",
        ["MUST FAIL: register refuses when the self-test does not pass (exit 4)"]),
    "registering twice adds a second entry": (
        '            if h.get("command") == command and e.get("matcher") == args.matcher:', "            if False:",
        ["register twice is a no-op, not a duplicate"]),
    "a narrow write matcher is accepted in silence": (
        "        if missing:\n            print(\"WARNING: matcher", "        if False:\n            print(\"WARNING: matcher",
        ["a narrow write matcher is warned about, not silently accepted"]),
    "failfirst accepts an inert self-test": (
        "    if broken.returncode == 0:", "    if False:",
        ["MUST FAIL: an INERT self-test is caught (exit 6) -- the headline case"]),
    "failfirst never neuters the guard": (
        "    lines[span[0] - 1:span[1]] = ['TRIGGER = re.compile(r\"(?!x)x\")  # NEUTERED\\n']",
        "    lines = lines",
        ["failfirst proves a real guard bites, and restores it byte for byte"]),
    "audit misses an if-gated registration": (
        '                if "if" in e:', "                if False:",
        ["MUST FAIL: audit catches an if-gated registration (exit 7)"]),
    "audit misses a hook with no self-test": (
        '        if not fam["test"]:', "        if False:",
        ["MUST FAIL: audit catches a hook with no self-test (exit 7)"]),
    "a generated blocking guard does not read NotebookEdit's fields": (
        '("command", "file_path", "notebook_path", "content", "new_string", "new_source", "prompt")',
        '("command", "file_path", "content", "new_string", "prompt")',
        ["a generated blocking guard reads NotebookEdit's notebook_path and new_source"]),
    "a generated advisory guard does not read NotebookEdit's fields": (
        '    path = ti.get("file_path") or ti.get("notebook_path") or ""\n'
        '    for key in ("command", "content", "new_string", "new_source", "prompt"):',
        '    path = ti.get("file_path") or ""\n'
        '    for key in ("command", "content", "new_string", "prompt"):',
        ["a generated advisory guard reads NotebookEdit's new_source and names its notebook"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
tmp = Path(tempfile.mkdtemp(prefix="guard_hook_mut_"))
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = tmp / "guard_hook_run.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                       env=dict(os.environ, GUARD_HOOK_RUN=str(mut)))
    if "PASS --" not in p.stdout and "FAIL --" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{p.stderr[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in p.stdout.splitlines()
           if ln.strip().startswith("FAIL ") and not ln.strip().startswith("FAIL --")]  # not the summary line
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
