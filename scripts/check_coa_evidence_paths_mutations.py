#!/usr/bin/env python3
"""Prove check_coa_evidence_paths.py --self-test catches each way the evidence-path check could pass a bad brief.

    python3 scripts/check_coa_evidence_paths_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script (it finds tests/golden/ from its own folder) and deleted after its
run. A mutant must still run: it is wrong, not broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_coa_evidence_paths.py").read_text(encoding="utf-8")
MUTANTS = {
    "surrounding spaces are kept": (
        "    raw = given.strip()", "    raw = given",
        ["same verdict as the Julia original: '  brief.md  ' -> file"]),
    "a trailing slash is kept": (
        '    resolved = resolved.rstrip("/") or "/"', "    resolved = resolved",
        ["same verdict as the Julia original: 'session/notes.md/' -> file"]),
    "a relative path is read from the working directory, not the base": (
        "    resolved = expanded if os.path.isabs(expanded) else os.path.join(base, expanded)",
        "    resolved = expanded if os.path.isabs(expanded) else os.path.abspath(expanded)",
        ["same verdict as the Julia original: 'brief.md' -> file", "every path resolves: exit 0"]),
    "a leading ~ is not expanded": (
        '    expanded = os.path.expanduser("~") + raw[1:] if raw.startswith("~") else raw', "    expanded = raw",
        ["a leading ~ is the home folder"]),
    "a folder reads as missing": (
        '    kind = "dir" if os.path.isdir(resolved) else "file" if os.path.isfile(resolved) else "MISSING"',
        '    kind = "file" if os.path.isfile(resolved) else "MISSING"',
        ["same verdict as the Julia original: 'session' -> dir"]),
    "a missing path still passes": (
        "    if not missing:\n        print(", "    if True:\n        print(",
        ["one missing among two: exit 1"]),
    "no paths is a pass": (
        "        return 2\n    return report(", "        return 0\n    return report(",
        ["no paths: exit 2, never a pass"]),
    "--stdin is ignored": (
        '    if "--stdin" in args:', "    if False:",
        ["--stdin reads one path per line"]),
    "blank stdin lines are read as paths": (
        "        paths = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]",
        "        paths = [ln.strip() for ln in sys.stdin.read().splitlines()]",
        ["--stdin skips blank lines"]),
    "the report does not say where it looked": (
        '            print(f"        looked at: {resolved}")', "            pass",
        ["a missing path says where it looked"]),
    "COA_EVIDENCE_BASE is ignored": (
        '    base = os.environ.get("COA_EVIDENCE_BASE") or os.getcwd()', "    base = os.getcwd()",
        ["every path resolves: exit 0"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_coa_evidence_paths.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_coa_evidence_paths.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True)
    finally:
        mut.unlink()
    if "self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{p.stderr[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
