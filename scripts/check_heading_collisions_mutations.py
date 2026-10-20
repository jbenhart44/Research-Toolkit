#!/usr/bin/env python3
"""Prove check_heading_collisions.py --self-test catches each way the heading check could miss a collision or
report a correct document.

    python3 scripts/check_heading_collisions_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong,
not broken.

Two mutations are deliberately absent. Keeping a closing sequence (`## Summary ##`) changes no verdict, because `#`
is punctuation and the key folds it away; the stripping only tidies the title as printed. And keying a heading's
parent on its text instead of its line needs a second lookup to express, while the "duplicated block reports
once" case already fails if children are compared at all.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_heading_collisions.py").read_text(encoding="utf-8")
MUTANTS = {
    "case is not folded": (
        'NORMALISE_RE.sub(" ", title.casefold())', 'NORMALISE_RE.sub(" ", title)',
        ["one letter's case", "case only, top level, under a title"]),
    "punctuation is not folded": (
        r'NORMALISE_RE = re.compile(r"[\W_]+", re.UNICODE)', r'NORMALISE_RE = re.compile(r"[ ]+", re.UNICODE)',
        ["trailing punctuation only", "bold markers only"]),
    "every same-level heading is compared, not siblings": (
        "        siblings[(h.level, h.parent_line, key)].append((h.line, h.title))",
        "        siblings[(h.level, 0, key)].append((h.line, h.title))",
        ["not gated: per-phase template subsections", "not gated: per-session template subsections"]),
    "fences are not recognised": (
        r'FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")', r'FENCE_OPEN_RE = re.compile(r"^NEVER(`{3,}|~{3,})(.*)$")',
        ["ignored: # comments inside fences", "an unclosed fence is counted and its tail is not parsed"]),
    "tilde fences are not recognised": (
        r'FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")', r'FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,})(.*)$")',
        ["ignored: tilde fences"]),
    "a shorter fence closes a longer one": (
        " and len(m.group(1)) >= fence_len and ", " and ",
        ["ignored: a four-backtick fence holding a three-backtick fence"]),
    "front matter is read as text": (
        "    if n and FRONTMATTER_RE.match(lines[0]):", "    if False:",
        ["ignored: hashes in YAML front matter"]),
    "HTML comments are read as text": (
        '        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:', "        if False:",
        ["ignored: a heading inside an HTML comment"]),
    "a hashtag with no space is a heading": (
        r'ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")',
        r'ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]*(.*?))?[ \t]*$")',
        ["ignored: a hashtag with no space"]),
    "an indented code block is a heading": (
        r'ATX_RE = re.compile(r"^ {0,3}(#{1,6})', r'ATX_RE = re.compile(r"^ *(#{1,6})',
        ["ignored: an indented code block"]),
    "a punctuation-only heading has an identity": (
        "        if not key:  # a heading that is only punctuation has no identity\n            continue\n", "",
        ["ignored: a heading that is only punctuation"]),
    "an unclosed fence is not reported": (
        "    if fence_char is not None:\n        res.unclosed_fence = fence_line", "    if False:\n        res.unclosed_fence = fence_line",
        ["an unclosed fence is counted and its tail is not parsed"]),
    "a setext underline is not counted": (
        "                res.setext_suspect += 1", "                pass",
        ["a setext underline is counted"]),
    "a thematic break is counted as setext": (
        "            if prev and not prev.startswith(", "            if True or not prev.startswith(",
        ["a --- thematic break is not a setext suspect"]),
    "--check never fails": (
        "    if args.check and n_coll:", "    if False:",
        ["--check on a collision exits 1"]),
    "report mode fails on a collision": (
        "    if args.check and n_coll:", "    if n_coll:",
        ["report mode exits 0 even on a collision"]),
    "a missing path beside a real one is skipped": (
        "    if missing or not files:", "    if not files:",
        ["a missing path beside a real one still exits 2"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_heading_collisions.py"), "--self-test"],
                      capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_heading_collisions.py"
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
