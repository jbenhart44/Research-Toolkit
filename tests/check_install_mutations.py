#!/usr/bin/env python3
"""Prove check_install.py --self-test catches each way the install gate could pass a broken install.

    python3 tests/check_install_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real checker and deleted after its run. A mutant must still run:
it is wrong, not broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_install.py").read_text(encoding="utf-8")
MUTANTS = {
    # The never-copied case stays green here: the re-install check reports it too. Each check gets its own mutant.
    "installed scripts are never looked for after a single install": (
        "            if not script.is_file():", "            if False:",
        ["a runtime script installed only in the full install is caught in --minimal"]),
    "a re-install is not checked for the scripts it should leave": (
        '        if not (home / ".claude" / "toolkit" / "scripts" / f"{n}.py").is_file():', "        if False:",
        ["a re-install that backs up the script and never copies the new one is caught"]),
    "a re-install may overwrite the user's config": (
        '    if cfg.read_text(encoding="utf-8") != USER_CONFIG:', "    if False:",
        ["a re-install that overwrites the user's config is caught"]),
    "an upgrade that keeps old command files passes": (
        "        if dst.is_file() and dst.read_bytes() != src.read_bytes():", "        if False:",
        ["an upgrade that keeps the old command files is caught"]),
    "--previous is accepted but never installed": (
        "    if previous is not None:", "    if False:",
        ["an upgrade that keeps the old command files is caught"]),
    "a call to an uninstalled script is allowed": (
        "            if name not in runtime:", "            if False:",
        ["a command calling a script missing from RUNTIME_SCRIPTS is caught"]),
    "only $TOOLKIT_ROOT counts as a clone path": (
        "CLONE_CALL = re.compile(r'\\$TOOLKIT_ROOT|\\b(?:bash|python3)\\s+\"?(?:\\./)?(?:scripts|hooks)/')",
        "CLONE_CALL = re.compile(r'\\$TOOLKIT_ROOT')",
        ["a command calling a repo-relative scripts/ path is caught"]),
    "the python3 permission is not checked": (
        '"Bash(python3:*)" not in tools.group(1)', "False",
        ["a command calling python3 without the permission is caught"]),
    "a command in neither array is allowed": (
        "        if cmd.stem not in shipped:", "        if False:",
        ["a command file in neither array is caught"]),
    "installed test files are not looked for": (
        "            if TEST_FILE.search(p.name):", "            if False:",
        ["an installer that copies hook test files is caught"]),
    "--minimal is never installed": (
        'MODES = [(), ("--minimal",), ("--hooks",)]', 'MODES = [(), ("--hooks",)]',
        ["a runtime script installed only in the full install is caught in --minimal"]),
    "the installed helper is never run": (
        '            elif name == "emit_run_report" and not helper_writes_row(script):', "            elif False:",
        ["a broken installed helper is caught"]),
    "a dry run that writes files passes": (
        "    if wrote:", "    if False:",
        ["a dry run that writes files is caught"]),
    "the installer's exit code is ignored": (
        "    return p.returncode", "    return 0",
        ["an installer that exits non-zero is caught"]),
    "only extra commands are caught, not missing ones": (
        "        if got != want:", "        if set(got) - set(want):",
        ["an installed command set that differs from the arrays is caught"]),
    "--hooks is not checked for every runtime hook": (
        '                if not (claude / "hooks" / h).is_file():', "                if False:",
        ["--hooks leaving out a runtime hook is caught"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_install.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_install.py"
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
