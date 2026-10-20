#!/usr/bin/env python3
"""Prove check_claims.py --self-test catches each way the claims gate could pass a wrong page.

    python3 tests/check_claims_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real checker and deleted after its run. A mutant must still run.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_claims.py").read_text(encoding="utf-8")
MUTANTS = {
    "/pcv is not counted": (
        'count = len(arrays["SHARED_COMMANDS"]) + len(arrays["STUDENT_ONLY"]) + len(arrays["SKILLS"]) + 1',
        'count = len(arrays["SHARED_COMMANDS"]) + len(arrays["STUDENT_ONLY"]) + len(arrays["SKILLS"])',
        ["derived count is shared + student + /pcv"]),
    "counts written in words are ignored": (
        "        value = int(tok) if tok.isdigit() else WORDS[tok]",
        "        value = int(tok) if tok.isdigit() else 0",
        ["a wrong count in words is caught"]),
    "qualifying words between number and 'commands' hide a claim": (
        r'((?:\s+[A-Za-z-]+){0,3}?)\s+commands\b', r'((?:\s+[A-Za-z-]+){0,1}?)\s+commands\b',
        ["a count with qualifying words between is caught"]),
    "small recommendation counts are treated as inventory": (
        "        if value >= 8:", "        if value >= 0:",
        ["small recommendation counts are not inventory claims"]),
    "counts are read line by line, so a wrapped count is missed": (
        "    for m in COUNT.finditer(text):",
        "    for m in (m for line in text.splitlines() for m in COUNT.finditer(line)):",
        ["a count wrapped across a line break is caught"]),
    "command-file counts are read line by line": (
        "    for m in FILES.finditer(text):",
        "    for m in (m for line in text.splitlines() for m in FILES.finditer(line)):",
        ["a command-file count wrapped across a line break is caught"]),
    "download URLs are not checked": (
        r'PIN = re.compile(r"(?:git checkout\s+|releases/download/|releases/tag/|Download\s+)v(\d+(?:\.\d+){1,2})", re.I)',
        r'PIN = re.compile(r"(?:git checkout\s+)v(\d+(?:\.\d+){1,2})", re.I)',
        ["a stale download URL is caught"]),
    "cff-version is read as the version": (
        r'''CFF_VERSION = re.compile(r"^version:\s*['\"]?(\d+(?:\.\d+){1,2})", re.M)''',
        r'''CFF_VERSION = re.compile(r"version:\s*['\"]?(\d+(?:\.\d+){1,2})", re.M)''',
        ["CITATION.cff version must match VERSION"]),
    "BibTeX versions are not checked": (
        "        for rx in (PIN, BIB_VERSION, STATUS):", "        for rx in (PIN, STATUS):",
        ["a stale BibTeX version is caught"]),
    "Status lines are not checked": (
        "        for rx in (PIN, BIB_VERSION, STATUS):", "        for rx in (PIN, BIB_VERSION):",
        ["a stale three-part Status line is caught"]),
    "a two-part Status series is read as a pin": (
        r'STATUS = re.compile(r"\bStatus:\**\s*v(\d+\.\d+\.\d+)")', r'STATUS = re.compile(r"\bStatus:\**\s*v(\d+\.\d+(?:\.\d+)?)")',
        ["a two-part 'Status: v2.0' is a series, not a pin"]),
    "banned claims are not checked": (
        '        for phrase in BANNED:', '        for phrase in []:',
        ["the banned unbacked claim is caught"]),
    "extra files are ignored": (
        "    pages = claim_files(root) + [p for p in extra if p.resolve() not in claim_files(root)]",
        "    pages = claim_files(root)",
        ["an extra file (the landing page) is checked too"]),
    "a hand list replaces discovery, so a new page is never read": (
        "    pages = claim_files(root) + [p for p in extra if p.resolve() not in claim_files(root)]",
        '    pages = [root / "README.md"] + [p for p in extra if p.resolve() not in claim_files(root)]',
        ["a page in any folder is checked"]),
    "hyphenated counts are ignored": (
        r'r"(?:((?:\s+[A-Za-z-]+){0,3}?)\s+commands\b|-commands?\b)", re.I)',
        r'r"(?:((?:\s+[A-Za-z-]+){0,3}?)\s+commands\b)", re.I)',
        ["a hyphenated count ('15-command') is caught"]),
    "the instructor page is held to the full count": (
        '        want, source = (instructor, "install.sh --minimal") if subset else (count, "install.sh")',
        '        want, source = (count, "install.sh")',
        ["the instructor page passes at the instructor count"]),
    "historical files are read as current": (
        'HISTORICAL = {"DESIGN.md", "CHANGELOG.md"}', "HISTORICAL = set()",
        ["historical files are not claim surfaces"]),
    "the upstream bundle and fixtures are read as current": (
        'SKIP_DIRS = {".git", "pcv", "smoke"}', 'SKIP_DIRS = {".git"}',
        ["pcv/ and tests/smoke/ are not claim surfaces"]),
    "a missing VERSION passes": (
        '        return 2, [f"cannot derive the truth: count={count} version={version}"], (count, version)',
        '        return 0, [], (count, version)',
        ["no VERSION file is exit 2"]),
    "a missing installer array still gives a count": (
        '        if len(arrays) == 3:\n'
        '            count = len(arrays["SHARED_COMMANDS"]) + len(arrays["STUDENT_ONLY"]) + len(arrays["SKILLS"]) + 1\n'
        '            instructor = len(arrays["SHARED_COMMANDS"]) + 1\n'
        '            files = len(arrays["SHARED_COMMANDS"]) + len(arrays["STUDENT_ONLY"])',
        '        if arrays:\n'
        '            a = {k: arrays.get(k, []) for k in ("SHARED_COMMANDS", "STUDENT_ONLY", "SKILLS")}\n'
        '            count = len(a["SHARED_COMMANDS"]) + len(a["STUDENT_ONLY"]) + len(a["SKILLS"]) + 1\n'
        '            instructor = len(a["SHARED_COMMANDS"]) + 1\n'
        '            files = len(a["SHARED_COMMANDS"]) + len(a["STUDENT_ONLY"])',
        ["an installer with an array missing is exit 2"]),
    "skills are not counted toward the command total": (
        '+ len(arrays["STUDENT_ONLY"]) + len(arrays["SKILLS"]) + 1', '+ len(arrays["STUDENT_ONLY"]) + 1',
        ["skills count toward the command total"]),
    "command-file counts are not checked": (
        "    for m in FILES.finditer(text):", "    for m in []:",
        ["a wrong command-file count is caught"]),
    "command-file counts are held to the count that includes /pcv": (
        "        want_files = instructor - 1 if subset else command_files",
        "        want_files = instructor - 1 if subset else count",
        ["a correct hyphenated count and a correct command-file count pass"]),
    "mutant counts are not checked": (
        "        for m in MUTANT_COUNT.finditer(line):", "        for m in []:",
        ["a mutant count that disagrees with its harness is caught"]),
    "only the dictionary named MUTANTS is counted": (
        'any(isinstance(t, ast.Name) and t.id.endswith("MUTANTS") for t in node.targets)',
        'any(isinstance(t, ast.Name) and t.id == "MUTANTS" for t in node.targets)',
        ["a mutant count that matches its harness passes"]),
    "a mutant count pairs with the first harness on its line": (
        "            h = before[-1] if before else (harnesses[0] if harnesses else None)",
        "            h = harnesses[0] if harnesses else None",
        ["each mutant count pairs with the harness named just before it"]),
    "the model-claim phrases are not banned": (
        'BANNED = ["hundreds of production sessions", "guarantees the model", "always runs on"]',
        'BANNED = ["hundreds of production sessions"]',
        ["the banned claim in 'This guarantees the model", "the banned claim in 'Every seat always runs on"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_claims.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_claims.py"
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
