#!/usr/bin/env python3
"""Prove agent_stalls.py --self-test catches each way the stall ledger could lose a stall or hide one.

    python3 scripts/agent_stalls_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong, not
broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "agent_stalls.py").read_text(encoding="utf-8")
MUTANTS = {
    "the window is never checked": (
        "            if when >= cut:\n                out.append(r)", "            if True:\n                out.append(r)",
        ["and not after the window"]),
    "a recorded stall is never found": (
        "                out.append(r)\n    return out", "                out.append(r)\n    return []",
        ["a recorded stall is found in the window", "recent exits 1 when a stall is in the window"]),
    "an unreadable row crashes recent": (
        "            except ValueError:\n                if unreadable is not None:",
        "            except KeyError:\n                if unreadable is not None:",
        ["a row with no readable timestamp is skipped and counted, never a crash"]),
    "the header is written on every event": (
        "    new = not ledger.exists() or ledger.stat().st_size == 0", "    new = True",
        ["a second event appends, with the header written once"]),
    "the run's receipt is never written": (
        "    if instr and instr.exists():", "    if False:",
        ["the run's instrumentation.csv gets one STALLED row per agent"]),
    "--no-receipt is ignored": (
        '    instr = Path(run_dir) / "instrumentation.csv" if run_dir and receipt else None',
        '    instr = Path(run_dir) / "instrumentation.csv" if run_dir else None',
        ["--no-receipt leaves the run's instrumentation.csv alone"]),
    "an empty record is written": (
        "    if not agents or not reason.strip():", "    if False:",
        ["refuses an empty record (no agents)", "refuses an empty record (no reason)"]),
    "the model is not recorded": (
        '"n_agents": str(len(agents)), "model": model,', '"n_agents": str(len(agents)), "model": "",',
        ["the row names the agents, their count, the model, the reason and files written"]),
    "AGENT_STALLS_CSV is ignored": (
        '    return Path(arg or os.environ.get("AGENT_STALLS_CSV") or Path(".toolkit") / "evidence" / "agent_stalls.csv")',
        '    return Path(arg or Path(".toolkit") / "evidence" / "agent_stalls.csv")',
        ["AGENT_STALLS_CSV names the ledger when --ledger does not"]),
    "recent always exits 0": (
        "        return 1 if rows else 0", "        return 0",
        ["recent exits 1 when a stall is in the window"]),
    "a refused record from the command line exits 0": (
        '            print(f"refused: {e}", file=sys.stderr)\n            return 2',
        '            print(f"refused: {e}", file=sys.stderr)\n            return 0',
        ["a record with no agent from the command line is exit 2"]),
}

base = subprocess.run([sys.executable, str(HERE / "agent_stalls.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_agent_stalls.py"
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
