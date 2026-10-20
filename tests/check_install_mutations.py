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
    "the bootstrap installer is never checked": (
        "            if needed and anchor not in boot:", "            if False:",
        ["a bootstrap installer with no runtime-scripts step is caught", "a bootstrap with no skills step is caught"]),
    "skills are never looked for after a full install": (
        '            elif "--minimal" not in flags and not present:', "            elif False:",
        ["a skill the full install leaves out is caught"]),
    "a skill in --minimal passes": (
        '            if "--minimal" in flags and present:', "            if False:",
        ["a skill installed by --minimal is caught"]),
    "seat agents are never looked for": (
        '            if not (claude / "agents" / f"{a}.md").is_file():', "            if False:",
        ["a seat agent no install copies is caught"]),
    "an add-on seat copied without its flag passes": (
        '            elif "--addon-seats" not in flags and present:', "            elif False:",
        ["an add-on seat copied without --addon-seats is caught"]),
    "--addon-seats is never checked for the seats it copies": (
        '            if "--addon-seats" in flags and not present:', "            if False:",
        ["--addon-seats that copies nothing is caught"]),
    "a stray add-on seat file passes": (
        "        if p.stem not in addon:", "        if False:",
        ["an add-on seat file in no array is caught"]),
    "a pointer to a missing command passes": (
        "        for t in sorted(set(targets) - installed):", "        for t in []:",
        ["a pointer to a command no array installs is caught"]),
    "a stray pointer file passes": (
        "        if p.stem not in pointers:", "        if False:",
        ["a pointer file in no array is caught"]),
    "a backup inside skills/ passes": (
        '        if ".bak" in d.name:', "        if False:",
        ["a backup written inside ~/.claude/skills/ is caught"]),
    "any file may sit in a skill folder": (
        '            if not (rel.as_posix() == "SKILL.md" or (rel.parts[0] == "assets" and len(rel.parts) == 2)):',
        "            if False:",
        ["a skill folder holding more than SKILL.md and assets/ is caught"]),
    "a skill's name: is not compared with its folder": (
        "        if not m or m.group(1) != s:", "        if False:",
        ["a skill whose name: is not its folder is caught"]),
    "a skill folder outside SKILLS passes": (
        "        if d.name not in skills:", "        if False:",
        ["a skill folder in no array is caught"]),
    "a seat file outside SEAT_AGENTS passes": (
        "        if p.stem not in seats:", "        if False:",
        ["a seat file in no array is caught"]),
    "a skill may be missing from the catalog": (
        '            if f"/{s}" not in text(rel):', "            if False:",
        ["a skill /help does not name is caught"]),
    "a seat may be missing from the catalog": (
        "            if a not in text(rel):", "            if False:",
        ["a seat the README does not name is caught"]),
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
        'MODES = [(), ("--minimal",), ("--hooks",), ("--addon-seats",)]', 'MODES = [(), ("--hooks",), ("--addon-seats",)]',
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
    "a self-test's __pycache__ is read as part of the skill": (
        '        for p in sorted(x for x in d.rglob("*") if x.is_file() and "__pycache__" not in x.parts):',
        '        for p in sorted(x for x in d.rglob("*") if x.is_file()):',
        ["a __pycache__ folder left by a self-test run is not a contract breach"]),
    "a hook file in no array passes": (
        '        if p.suffix in (".sh", ".py") and not TEST_FILE.search(p.name) and p.name not in expected:',
        "        if False:",
        ["a hook file in no array is caught"]),
    "an array entry with no hook file passes": (
        '        if not (root / "hooks" / name).is_file():', "        if False:",
        ["an array entry with no hook file is caught"]),
    "a hook installed without --hooks passes": (
        '        elif any((claude / "hooks" / h).is_file() for h in hooks):', "        elif False:",
        ["a hook installed without --hooks is caught"]),
    "an installer that writes settings.json passes": (
        '        if (claude / "settings.json").exists():', "        if False:",
        ["an installer that writes settings.json is caught"]),
    "a hook may be missing from the hooks README": (
        "        if h not in text:", "        if False:",
        ["a hook the hooks README does not name is caught"]),
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
