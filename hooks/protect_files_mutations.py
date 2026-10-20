#!/usr/bin/env python3
"""Prove protect_files_selftest.py catches each way the write lock could miss a write, or block a read.

    python3 hooks/protect_files_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real hook (it imports _toolkit_config.py from its own folder) and deleted after
its run; the self-test is pointed at it with PF_HOOK (or PF_LAUNCHER). A mutant must still run. How an entry
matches is proven by _toolkit_config_mutations.py; here, only that this hook uses that matcher.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "protect_files.py").read_text(encoding="utf-8")
SELFTEST = HERE / "protect_files_selftest.py"
MUTANTS = {
    "NotebookEdit's notebook_path is not read": (
        'tool_input.get("file_path") or tool_input.get("notebook_path") or None', 'tool_input.get("file_path") or None',
        ["blocks: NotebookEdit a protected notebook (its field is notebook_path)"]),
    "every Bash command is judged, reads included": (
        "        return tool, command if BASH_WRITE.search(command) else None", "        return tool, command or None",
        ["allows: Bash: cat it", "allows: Bash: grep it", "allows: Bash: git log on it"]),
    "a descriptor redirect counts as a write": (
        r'    r"|>>?\s*(?![&|\s])[^|\s]"', r'    r"|>>?\s*[^|\s]"',
        ["allows: Bash: a read ending in 2>&1", "allows: Bash: a read sent to >&2"]),
    "a redirect is not a write": (
        r'    r"|>>?\s*(?![&|\s])[^|\s]"', r'    r"|NEVER>"',
        ["blocks: Bash: truncate with >", "blocks: Bash: append with >>"]),
    "sed's -i may sit inside a longer word": (
        r'''    r"|\bsed\b[^|;]*(?:^|\s)-i(?:\s|$|'|\")"''', r'''    r"|\bsed\b[^|;]*-i"''',
        ["allows: Bash: sed -n on a path holding -i is a read"]),
    "perl -i is not a write": (
        r'''    r"|\bperl\b[^|;]*(?:^|\s)-i(?:\s|$|'|\")"''', r'''    r"|\bNEVER\b"''',
        ["blocks: Bash: perl -i"]),
    "git add and git commit count as writes": (
        r"(?:rm|mv|checkout|restore|apply|am)\b", r"(?:add|commit|rm|mv|checkout|restore|apply|am)\b",
        ["allows: Bash: git add changes no bytes", "allows: Bash: git commit changes no bytes"]),
    "git checkout is not a write": (
        r"(?:rm|mv|checkout|restore|apply|am)\b", r"(?:rm|mv|restore|apply|am)\b",
        ["blocks: Bash: git checkout over it"]),
    "tee is not a write": (
        "(?:cp|mv|rm|rmdir|touch|mkdir|tee|dd|", "(?:cp|mv|rm|rmdir|touch|mkdir|dd|",
        ["blocks: Bash: tee into it"]),
    "write_text is not a write": (
        r'    r"|\.write_text\(|\.write_bytes\(|\bopen\([^)]*[' "'" r'\"][wax]",',
        r'    r"|\.write_bytes\(|\bopen\([^)]*[' "'" r'\"][wax]",',
        ["blocks: Bash: python write_text"]),
    "open for writing is not a write": (
        r'    r"|\.write_text\(|\.write_bytes\(|\bopen\([^)]*[' "'" r'\"][wax]",',
        r'    r"|\.write_text\(|\.write_bytes\(",',
        ["blocks: Bash: python open for writing"]),
    "Read is treated as a write tool": (
        'WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")',
        'WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit", "Read")',
        ["allows: Read is not a write tool"]),
    "with no list, a default list is protected": (
        'config.path_hit(config.values("protected_files"), text, single_path=tool != "Bash")',
        'config.path_hit(config.values("protected_files") or ["paper/main.tex"], text, single_path=tool != "Bash")',
        ["no config file: protects nothing", "an empty list protects nothing"]),
    "a substring test replaces the shared path matcher": (
        '    entry = config.path_hit(config.values("protected_files"), text, single_path=tool != "Bash")',
        '    entry = next((e for e in config.values("protected_files") if e.lower() in text.lower()), None)',
        ["allows: Edit a folder whose name ends like the entry's"]),
    "the Bash route note is shown for every tool": (
        '    if tool == "Bash":\n        reason +=', "    if True:\n        reason +=",
        ["a Bash refusal names the Write-tool route"]),
    "nothing is logged": (
        "    log_block(entry, text)\n    return 0", "    return 0",
        ["a denial adds one line to <evidence_dir>/protect_files_audit.log"]),
    "a log failure undoes the block": (
        "    except OSError:\n        pass  # a log that cannot be written never undoes the block",
        "    except ZeroDivisionError:\n        pass",
        ["a log that cannot be written never undoes the block"]),
    "malformed input breaks the session": (
        "    except ValueError:\n        return 0", "    except KeyError:\n        return 0",
        ["malformed input exits 0 and prints nothing"]),
}

LAUNCHER_SRC = (HERE / "protect_files.sh").read_text(encoding="utf-8")
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
    mut = HERE / ("_mutant_protect_files.py" if kind == "py" else "_mutant_protect_files.sh")
    mut.write_text(src.replace(old, new), encoding="utf-8")
    var = "PF_HOOK" if kind == "py" else "PF_LAUNCHER"
    try:
        p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                           env=dict(os.environ, **{var: str(mut)}))
    finally:
        mut.unlink()
    if "protect_files self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{p.stderr[-400:]}")
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
