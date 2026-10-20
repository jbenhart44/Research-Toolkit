#!/usr/bin/env python3
"""Prove acquire.py --self-test catches each way an acquisition could let a wrong or unread source through.

    python3 scripts/acquire_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong, not
broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "acquire.py").read_text(encoding="utf-8")
MUTANTS = {
    "HTML is saved as the PDF": (
        '    if kind == "html":\n        return 1,', '    if False:\n        return 1,',
        ["HTML in place of a PDF is refused, exit 1, and nothing is left on disk"]),
    "an existing file is overwritten": (
        "    if target.exists():\n        return 2,", "    if False:\n        return 2,",
        ["an existing target is refused, exit 2, and left untouched"]),
    "a failed download passes": (
        '        return 4, f"UNCHECKED: could not download', '        return 0, f"UNCHECKED: could not download',
        ["a download that fails is exit 4, never a pass"]),
    "the density gate is off": (
        '    return ("OK" if per >= MIN_CHARS_PER_PAGE else "SPARSE"), per', '    return ("OK" if per >= 0 else "SPARSE"), per',
        ["71 characters a page (scanned-page header noise) is SPARSE", "199 characters a page does not",
         "a SPARSE PDF writes no .txt and hands its pages to the transcriber, exit 3"]),
    "the density floor is off by one": (
        '    return ("OK" if per >= MIN_CHARS_PER_PAGE else "SPARSE"), per',
        '    return ("OK" if per > MIN_CHARS_PER_PAGE else "SPARSE"), per',
        ["exactly 200 characters a page passes the density gate"]),
    "a sparse extraction is written as the .txt": (
        '    if status == "OK":\n        text = assemble(', '    if status in ("OK", "SPARSE"):\n        text = assemble(',
        ["a SPARSE PDF writes no .txt and hands its pages to the transcriber, exit 3"]),
    "an empty page is left silent": (
        '        body = t.strip() or f"{GAP} no text extracted', '        body = t.strip() if True else f"{GAP} no text extracted',
        ["a page with no text carries a MATERIAL GAP marker, never silence"]),
    "a sparse source is grep-checked anyway": (
        '    if status != "OK":\n        return 3, [f"NOT RUN', '    if False:\n        return 3, [f"NOT RUN',
        ["a sparse source is refused, exit 3, even when the string is in its header"]),
    "line breaks are not normalised": (
        '    return re.sub(r"\\s+", " ", s).strip().lower()', '    return s.strip().lower()',
        ["a claim wrapped across a line break is still found"]),
    "matching is case-sensitive": (
        '    return re.sub(r"\\s+", " ", s).strip().lower()', '    return re.sub(r"\\s+", " ", s).strip()',
        ["matching ignores case"]),
    "a hyphenated line break is not joined": (
        '    s = re.sub(r"(\\w)-\\s*\\n\\s*(\\w)", r"\\1\\2", s)', '    s = s',
        ["a word hyphenated across a line break is found, on page 14"]),
    "a DOI for another paper is accepted": (
        "    if not name or name not in names:", "    if False:",
        ["a DOI that points at a different paper is a MISMATCH, exit 1"]),
    "a particle family name is not matched": (
        ' | {fold(a).split()[-1] for a in rec["authors"] if a.strip()}', "",
        ["a family name with a particle matches its last word"]),
    "a year far off is accepted": (
        "abs(int(rec[\"year\"]) - year) > 1:", "abs(int(rec[\"year\"]) - year) > 99:",
        ["a year off by more than one is a MISMATCH"]),
    "CrossRef silence reads as a match": (
        '        return 4, [f"UNCHECKED: {e}"]\n    lines = [f"Title:', '        return 0, [f"UNCHECKED: {e}"]\n    lines = [f"Title:',
        ["CrossRef not answering is exit 4, never a match"]),
    "an HTTP 400 is not retried": (
        '    for attempt in ([title, title.split(":")[0].strip()] if ":" in title else [title]):',
        "    for attempt in [title]:",
        ["an HTTP 400 is retried with the title cut at its colon, and found"]),
    "no results reads as no open copy": (
        '        return 4, notes + ["UNCHECKED: OpenAlex has no record', '        return 1, notes + ["UNCHECKED: OpenAlex has no record',
        ["no results is exit 4 (could not ask), never 'no open copy'"]),
    "an UNVERIFIED row skips the DOI check": (
        '        if r["unverified"]:\n            m = DOI_RE', '        if False:\n            m = DOI_RE',
        ["an UNVERIFIED row whose DOI names another paper is BLOCKED and never downloaded"]),
    "a NOT FOUND claim does not fail the manifest": (
        "    clean = acquired == n and not notfound", "    clean = acquired == n",
        ["every row acquired with one claim NOT FOUND is still exit 1"]),
    "a second report overwrites the first": (
        "    while report.exists():", "    while False:",
        ["a second run never overwrites the first report"]),
}

base = subprocess.run([sys.executable, str(HERE / "acquire.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_acquire.py"
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
