#!/usr/bin/env python3
"""Prove check_transcription.py --self-test catches each way the checker could pass a bad transcription.

    python3 scripts/check_transcription_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong, not
broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_transcription.py").read_text(encoding="utf-8")
MUTANTS = {
    "page numbers are not checked": (
        "    if sorted(nums) != list(range(1, n + 1)):", "    if False:",
        ["a missing page marker fails", "a repeated page marker fails"]),
    "a repeated marker counts once": (
        "    if sorted(nums) != list(range(1, n + 1)):", "    if sorted(set(nums)) != list(range(1, n + 1)):",
        ["a repeated page marker fails"]),
    "a short page passes": (
        "        if len(re.sub(r\"\\s+\", \"\", b)) < MIN_PAGE_CHARS:", "        if False:",
        ["a page under 100 characters fails"]),
    "a blank marker is not honoured": (
        '        if b.startswith("[blank]") or b.startswith("[MATERIAL GAP"):',
        '        if b.startswith("[MATERIAL GAP"):',
        ["a page marked [blank] is allowed"]),
    "the extracted text is never compared": (
        "    ok = found / len(tokens) >= 0.5", "    ok = True",
        ["extracted words missing from the transcription fail"]),
    "names are never looked for": (
        "    return bool(hit), (f\"found {hit}\"", "    return True, (f\"found {hit}\"",
        ["no expected name in the text fails"]),
    "refusals pass": (
        "    return (not hits), (f\"refusal or filler text: {hits}\"", "    return True, (f\"refusal or filler text: {hits}\"",
        ["a refusal in the text fails"]),
    "the vocabulary floor is off": (
        "    return distinct >= need,", "    return True,",
        ["a repetitive transcription fails the vocabulary check"]),
    "two disagreeing transcriptions pass": (
        "    ok = j >= MIN_JACCARD and ratio >= MIN_LENGTH_RATIO", "    ok = True",
        ["a second transcription that disagrees fails the agreement check"]),
    "numbers are compared as a whole file, not by page": (
        "        if na != nb:", "        if len(na) != len(nb):",
        ["one misread digit fails the numbers check, naming the page", "a percentage misread as another percentage fails"]),
    "a percentage sign is dropped from numbers": (
        'NUMBER = re.compile(r"(?<![\\w.])\\d+(?:[.,]\\d+)*%?")', 'NUMBER = re.compile(r"(?<![\\w.])\\d+%?")',
        ["one misread digit fails the numbers check, naming the page"]),
    "the numbers check never runs": (
        '("agreement", *check_agreement(text, second)), ("numbers", *check_numbers(text, second))]',
        '("agreement", *check_agreement(text, second))]',
        ["one misread digit fails the numbers check, naming the page", "a percentage misread as another percentage fails"]),
    "a failed check exits 0": (
        "    return 1 if failed else 0\n\n\nif", "    return 0\n\n\nif",
        ["the command line fails a misread second file, exit 1"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_transcription.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_transcription.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True)
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
