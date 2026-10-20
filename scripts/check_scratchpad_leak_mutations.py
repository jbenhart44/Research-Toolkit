#!/usr/bin/env python3
"""Prove check_scratchpad_leak.py --self-test catches each way the gate could miss a leak or cry wolf.

    python3 scripts/check_scratchpad_leak_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_scratchpad_leak.py").read_text(encoding="utf-8")
MUTANTS = {
    "only .md files are worth keeping": (
        'KEEP_EXT = {".md", ".py", ".jl", ".tex", ".csv", ".json", ".bib", ".pdf", ".qmd", ".toml", ".yaml", ".yml"}',
        'KEEP_EXT = {".md"}',
        ["an unsaved .py is a leak", "an unsaved .pdf is a leak"]),
    "a file counts as saved when its NAME is in the project": (
        "        if sha(p) in repo_hashes:", "        if any(p.name == q.name for q in r_files(repo)):",
        ["content saved under another name is not a leak", "the same name with different content is a leak"]),
    "the size filter skips the files that could match": (
        "                if p.stat().st_size not in sizes:", "                if p.stat().st_size in sizes:",
        ["content saved under another name is not a leak"]),
    "the project is searched only at its top level": (
        "    for dirpath, dirnames, filenames in os.walk(repo):",
        "    for dirpath, dirnames, filenames in [next(os.walk(repo))]:",
        ["content saved deep in the project is found"]),
    "the scratchpad is searched only at its top level": (
        "    for dirpath, dirnames, filenames in os.walk(scratch):",
        "    for dirpath, dirnames, filenames in [next(os.walk(scratch))]:",
        ["a leak nested in subfolders is found"]),
    "throwaway names are kept": (
        "    if name.startswith(EPHEMERAL_PREFIX):", "    if False:",
        ["throwaway names are clean"]),
    "__pycache__ is not derived": (
        '    if "__pycache__" in rel.parts or suf in DERIVED_EXT:', "    if suf in DERIVED_EXT:",
        ["anything under __pycache__ is derived"]),
    ".git is walked": (
        'SKIP_DIRS = {".git", "node_modules", ".venv"}', 'SKIP_DIRS = {"node_modules", ".venv"}',
        ["anything under .git is skipped", "a .md under the project's .git does not count as saved"]),
    "derived files are counted as throwaway": (
        "            if kind == \"DERIVED\":\n                derived += 1\n            elif kind == \"EPHEMERAL\":",
        "            if kind == \"NEVER\":\n                derived += 1\n            elif kind in (\"EPHEMERAL\", \"DERIVED\"):",
        ["the counts are reported (1 saved, 1 derived, 1 throwaway)"]),
    "a missing folder passes": (
        "            print(f\"usage error: not a directory: {d}\", file=sys.stderr)\n            return 2",
        "            print(f\"usage error: not a directory: {d}\", file=sys.stderr)\n            return 0",
        ["a missing scratchpad is exit 2, never a pass", "a missing project is exit 2, never a pass"]),
}
HELPER = "\n\ndef r_files(repo):\n    return [Path(d) / f for d, _, fs in os.walk(repo) for f in fs]\n"

base = subprocess.run([sys.executable, str(HERE / "check_scratchpad_leak.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_scratchpad_leak.py"
    text = SRC.replace(old, new)
    if "r_files(" in new:
        text = text.replace("\n\ndef main(", HELPER + "\n\ndef main(", 1)
    mut.write_text(text, encoding="utf-8")
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
