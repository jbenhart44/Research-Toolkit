#!/usr/bin/env python3
"""Prove bulletproof_selftest.py catches each way the /bulletproof runner could report a suite as proven when it
is not.

    python3 shared/skills/bulletproof/assets/bulletproof_mutations.py    # exit 0 = every mutant caught

Each mutant is written to a temporary folder and the self-test is pointed at it with BULLETPROOF_RUN. A mutant must
still run: it is wrong, not broken. The installer does not copy this file.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "bulletproof_run.py").read_text(encoding="utf-8")
SELFTEST = HERE / "bulletproof_selftest.py"
MUTANTS = {
    "scaffold writes over an existing suite": (
        "    if target.exists():\n        die(", "    if False:\n        die(",
        ["MUST FAIL: scaffold refuses to write over an existing suite"]),
    "scaffold guesses where there is no harness": (
        '    if not (tests / "harness.py").exists():', "    if False:",
        ["MUST FAIL: scaffold refuses where there is no harness to follow"]),
    "register adds the runner row twice": (
        '        if f"test_{name}.py" in t:\n            print(f"run_all.py: already runs',
        '        if False:\n            print(f"run_all.py: already runs',
        ["register is idempotent"]),
    "the audit passes a suite no mutation names": (
        "        if not covered:", "        if False:",
        ["MUST FAIL: audit refuses a suite with no mutation behind it"]),
    "the audit passes a suite the runner skips": (
        '        if runner.exists() and f"test_{n}.py" not in runner.read_text():', "        if False:",
        ["MUST FAIL: audit refuses a suite the runner does not run"]),
    "a missing tests folder is a pass": (
        '        die(f"{d} is not a directory", 2)', '        die(f"{d} is not a directory", 0)',
        ["MUST FAIL: a missing tests directory exits 2, not 0"]),
    "a mutation's label is read as an expectation": (
        "                which, must = el.elts[3], el.elts[4]", "                which, must = el.elts[3], el",
        ["MUST NOT read the mutation's own label as an expectation"]),
    "an f-string check name is never matched as a template": (
        '        if "{" not in name:\n            continue', "        continue",
        ["a runtime name matches its f-string template"]),
    "every name counts as covered": (
        "        if re.fullmatch(pattern, expected):\n            return True\n    return False",
        "        if re.fullmatch(pattern, expected):\n            return True\n    return True",
        ["MUST NOT: a name the template cannot produce is covered", "MUST NOT: an unrelated name is covered"]),
    "a moved anchor is read as an uncovered guard": (
        '        elif "no longer exists" in label or "STALE" in label:', "        elif False:",
        ["a moved anchor is counted as STALE, not as a hole"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
tmp = Path(tempfile.mkdtemp(prefix="bulletproof_mut_"))
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = tmp / "bulletproof_run.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                       env=dict(os.environ, BULLETPROOF_RUN=str(mut)))
    if "bulletproof selftest:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(p.stdout + p.stderr)[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:].strip() for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
