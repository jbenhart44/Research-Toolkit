#!/usr/bin/env python3
"""Prove check_toolkit.py --self-test catches each way the release gate could pass a bad tree.

    python3 tests/check_toolkit_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real checker and deleted after its run. A mutant must still run:
it is wrong, not broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_toolkit.py").read_text(encoding="utf-8")
MUTANTS = {
    "the description field is not required": (
        '        if not re.search(r"^description:", text, re.M):', "        if False:",
        ["a command without description is caught"]),
    "'When to use' is not required": (
        '        if "> **When to use**:" not in text:', "        if False:",
        ["a command without 'When to use' is caught"]),
    "the closing --- may sit anywhere": (
        '        elif "---" not in lines[1:10]:', '        elif "---" not in lines[1:]:',
        ["frontmatter closing after line 10 is caught"]),
    "WSL and Windows home paths are not recognised": (
        'HOME_PATH = re.compile(r"(?:/Users/|/home/|/mnt/[a-z]/Users/)[A-Za-z0-9._-]+|[A-Za-z]:\\\\Users\\\\[A-Za-z0-9._-]+")',
        'HOME_PATH = re.compile(r"(?:/Users/|/home/)[A-Za-z0-9._-]+")',
        ["a WSL home path is caught as the full", "a Windows home path is caught"]),
    "credentials are not scanned": (
        "            for m in CREDENTIAL.finditer(line):", "            for m in []:",
        ["a credential shape is caught"]),
    "every email is allowed": (
        "                if addr not in ALLOWED_EMAILS and not any(", "                if False and not any(",
        ["a private email is caught"]),
    "pcv/ and other bundled folders are skipped": (
        '        if ".git" in rel.parts or not p.is_file() or p.resolve() == SELF:',
        '        if ".git" in rel.parts or rel.parts[0] in ("pcv", "coa", "docs") or not p.is_file() or p.resolve() == SELF:',
        ["a file in docs/, coa/ or pcv/ is scanned too"]),
    "findings do not change the exit code": (
        "    return (1 if findings else 0), findings", "    return 0, findings",
        ["a content finding makes the exit code 1", "a frontmatter finding makes the exit code 1"]),
    "private tokens are loaded but never scanned": (
        "            for pat, rx in tokens:", "            for pat, rx in []:",
        ["a private token from the token file is caught", "a token line is a regular expression"]),
    "token lines are matched as plain text, not patterns": (
        '            out.append((line, re.compile(line)))', '            out.append((line, re.compile(re.escape(line))))',
        ["a token line is a regular expression"]),
    "comments in the token file are loaded as tokens": (
        '        if line and not line.startswith("#"):', "        if line:",
        ["comments and blank lines in the token file are ignored"]),
    "the upstream bundle is scanned for private tokens": (
        'TOKEN_SKIP_DIRS = {"pcv"}', "TOKEN_SKIP_DIRS = set()",
        ["a token inside pcv/ is not a finding"]),
    "a named token file that is missing is silently skipped": (
        '        return (0, p, "--tokens") if p.is_file() else (2, None, f"--tokens file not found: {p}")',
        '        return (0, p, "--tokens") if p.is_file() else (0, None, "no token file")',
        ["a missing --tokens file is exit 2"]),
    "no token file is reported as a clean scan": (
        '        return f"private-token scan: SKIPPED ({source}; see --tokens)"',
        '        return "private-token scan: clean"',
        ["no token file anywhere is reported as SKIPPED"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_toolkit.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_toolkit.py"
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
