#!/usr/bin/env python3
"""Prove usage_counts.py --self-test catches each way the report could over- or under-count.

    python3 scripts/usage_counts_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "usage_counts.py").read_text(encoding="utf-8")
MUTANTS = {
    "typed and run are never merged (double count)": (
        "        if partner is not None:\n            used.add(id(partner))\n            continue",
        "        if False:\n            continue",
        ["typed then run in the same session within 10 min counts once"]),
    "the merge window is unlimited": (
        "abs((s[\"ts\"] - e[\"ts\"]).total_seconds()) <= MERGE_SECONDS", "True",
        ["the same pair two hours apart counts twice"]),
    "the merge ignores the session": (
        'partner = next((s for s in skills[(e["session_id"], e["name"])]',
        'partner = next((s for s in [x for k, v in skills.items() if k[1] == e["name"] for x in v]',
        ["the same pair in different sessions counts twice"]),
    "one Skill call absorbs several typed rows": (
        "if id(s) not in used and abs(", "if abs(",
        ["one Skill call absorbs only one typed row"]),
    "backfill has no cutover (days counted twice)": (
        "if cutover is None or d < cutover]", "]",
        ["backfill counts only days before the counter's first row"]),
    "unknown typed names are counted": (
        '        if e["name"] not in known:\n            dropped[e["name"]] += 1\n            continue',
        '        if False:\n            continue',
        ["an unknown typed name is dropped and reported"]),
    "the report ignores $CLAUDE_PROJECT_DIR and reads the wrong project's log": (
        '    if env.get("CLAUDE_PROJECT_DIR"):', "    if False:",
        ["the project root is $CLAUDE_PROJECT_DIR, as in the hook"]),
    "--project is ignored": (
        "    if arg:\n        return Path(arg).expanduser()", "    if False:\n        return Path(arg).expanduser()",
        ["--project wins over $CLAUDE_PROJECT_DIR"]),
    "the --tools filter is ignored": (
        "        rows = {k: v for k, v in rows.items() if k in tools}", "        rows = rows",
        ["--tools limits the rows"]),
    "malformed rows are counted": (
        '                if not r["name"] or r["source"] not in ("skill", "typed"):\n                    raise ValueError',
        '                pass',
        ["malformed rows are skipped and counted"]),
}

base = subprocess.run([sys.executable, str(HERE / "usage_counts.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_usage_counts.py"
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
