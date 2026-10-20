#!/usr/bin/env python3
"""Prove the list-maker suites catch each way the ledger could lose an item or reuse a number.

    python3 list_maker_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script, run through BOTH suites (the script's own --self-test and
list_maker_selftest.py with LIST_MAKER pointing at the mutant), and deleted. A mutant must still run: it is wrong, not
broken.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "list_maker_run.py").read_text(encoding="utf-8")
MUTANTS = {
    "a done item's number is reused": (
        '        it = {"id": led["next_id"],',
        '        it = {"id": 1 + sum(1 for i in led["items"] if i["status"] != "done"),',
        ["an id is never reused after the item is done"]),
    "the corruption guard is off": (
        '    if ids and d["next_id"] <= max(ids):', "    if False:",
        ["a ledger whose next_id would reuse a number is refused"]),
    "a re-added item gets a second number": (
        "        if k in seen:", "        if False:",
        ["the same item re-added creates no second number", "adding the same file twice exits 1, nothing new"]),
    "a deferred item is hidden from the list": (
        '        rows = [r for r in rows if r["status"] in ("open", "deferred")]',
        '        rows = [r for r in rows if r["status"] in ("open",)]',
        ["a deferred item still renders", "a DEFERRED item is still shown"]),
    "a deferred tier-1 item clears the active list": (
        '            if r["tier"] == 1 and r["status"] in ("open", "deferred")]',
        '            if r["tier"] == 1 and r["status"] in ("open",)]',
        ["a deferred tier-1 item keeps the list active, since deferred is not done"]),
    "an unranked item jumps the queue": (
        '    return (r.get("rank") if r.get("rank") is not None else 10**6, r["id"])',
        '    return (r.get("rank") if r.get("rank") is not None else -1, r["id"])',
        ["an UNRANKED item falls to the end, never to the front"]),
    "next ignores rank": (
        '    rows.sort(key=lambda r: (r["tier"],) + rank_key(r))\n    return rows[0]',
        '    rows.sort(key=lambda r: (r["tier"], r["id"]))\n    return rows[0]',
        ["next honours rank before id, like active does"]),
    "any owner is accepted": (
        "        if owner not in owners:", "        if False:",
        ["an unknown owner is refused", "that ledger refuses an owner from another stream"]),
    "a tier outside the scale is accepted": (
        "        if tier not in TIERS:", "        if False:",
        ["a tier outside 1-4 is refused"]),
    "a stream's owners can be changed": (
        "            if ledger.exists() and ledger_owners(led) != wanted:", "            if False:",
        ["--owners that differ from an existing ledger's are refused, exit 2"]),
    "a cleared active list exits 0": (
        "                return 3\n", "                return 0\n",
        ["a cleared active list exits 3, never 0 or 1"]),
    "an untracked ledger is saved silently": (
        "    if is_tracked(path) is False:", "    if False:",
        ["saving an UNTRACKED ledger warns"]),
    "an empty list exits 0": (
        "            return 0 if rows else 1", "            return 0",
        ["an empty ledger exits 1, not 0"]),
    "scan keeps the hedges": (
        "        if NOISE.search(s):\n            continue", "        if False:\n            continue",
        ["scan skips the hedge"]),
    "quoted email text is scanned again": (
        "        if not s or TS.match(s) or EMAIL_SKIP.match(s):", "        if not s or TS.match(s):",
        ["quoted lines of an earlier message are skipped", "an email's own request is a candidate"]),
    "the outward mark is dropped": (
        '        if raw.get("outward"):', "        if False:",
        ["an outward-facing item is marked so the walk stops for approval", "and marks it outward-facing"]),
}

base_inner = subprocess.run([sys.executable, str(HERE / "list_maker_run.py"), "--self-test"], capture_output=True, text=True)
base_outer = subprocess.run([sys.executable, str(HERE / "list_maker_selftest.py")], capture_output=True, text=True)
if base_inner.returncode or base_outer.returncode:
    print("SETUP ERROR: an unmutated suite is red:\n" + base_inner.stdout[-800:] + base_outer.stdout[-800:])
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_list_maker_run.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        inner = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True)
        outer = subprocess.run([sys.executable, str(HERE / "list_maker_selftest.py")], capture_output=True, text=True,
                               env={**os.environ, "LIST_MAKER": str(mut)})
    finally:
        mut.unlink()
    if "self-test:" not in inner.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(inner.stdout + inner.stderr)[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in (inner.stdout + outer.stdout).splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
