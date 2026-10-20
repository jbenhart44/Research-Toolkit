#!/usr/bin/env python3
"""Prove register_hooks.py --self-test catches each way the registration printer could print a wrong block.

    python3 scripts/register_hooks_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script (it reads install.sh from the clone it sits in) and deleted after its
run. A mutant must still run: it is wrong, not broken.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "register_hooks.py").read_text(encoding="utf-8")
MUTANTS = {
    "a hook install.sh ships has no registration": (
        '    "summary_folder_guard": ([("PostToolUse", "Write")], "notes a dated summary written outside the summary folders"),\n', "",
        ["every hook install.sh ships has a registration on record"]),
    "an entry is gated by an if: condition": (
        '            entry = {"hooks": [{"type": "command", "command": f"~/.claude/hooks/{name}.sh", "timeout": 5}]}',
        '            entry = {"if": "Bash(git *)", "hooks": [{"type": "command", "command": f"~/.claude/hooks/{name}.sh", "timeout": 5}]}',
        ["no entry carries an if: condition"]),
    "a second event replaces the first": (
        "            hooks.setdefault(event, []).append(entry)", "            hooks[event] = [entry]",
        ["hooks on the same event share its list"]),
    "the matcher is dropped": (
        "            if matcher:\n                entry = {\"matcher\": matcher, **entry}", "            if False:\n                pass",
        ["one hook prints a PreToolUse block for it"]),
    "protect_files watches only Edit and Write": (
        '"protect_files": ([("PreToolUse", "Edit|Write|MultiEdit|NotebookEdit|Bash")]',
        '"protect_files": ([("PreToolUse", "Edit|Write|Bash")]',
        ["protect_files covers all four write tools and Bash"]),
    "an unknown name is printed anyway": (
        "    if unknown:\n        print(", "    if False:\n        print(",
        ["an unknown name is refused (exit 2), never printed"]),
    "--all prints only the first hook": (
        '    names = shipped if "--all" in args else', '    names = shipped[:1] if "--all" in args else',
        ["--all prints every shipped hook"]),
    "the registration is written to settings.json": (
        "    print(json.dumps(block(names), indent=2))\n    return 0",
        "    print(json.dumps(block(names), indent=2))\n    Path('settings.json').write_text(json.dumps(block(names)))\n    return 0",
        ["it writes no file, in the working folder or in HOME"]),
}

base = subprocess.run([sys.executable, str(HERE / "register_hooks.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_register_hooks.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        # A temporary working folder: the "writes settings.json" mutant writes into its working folder, and run from
        # the clone it left a settings.json behind in the repository.
        with tempfile.TemporaryDirectory() as cwd:
            p = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True, cwd=cwd)
    finally:
        mut.unlink()
    if "self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(p.stdout + p.stderr)[-400:]}")
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
