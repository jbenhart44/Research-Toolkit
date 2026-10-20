#!/usr/bin/env python3
"""Prove token_budget_guard_selftest.py catches each way the token-budget warning could miscount or misfire.

    python3 hooks/token_budget_guard_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real hook and deleted after its run; the self-test is pointed at it with
TOKEN_BUDGET_HOOK (or TOKEN_BUDGET_LAUNCHER). A mutant must still run: it is wrong, not broken.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "token_budget_guard.py").read_text(encoding="utf-8")
SELFTEST = HERE / "token_budget_guard_selftest.py"
MUTANTS = {
    "a small call counts its own length only": (
        "    return max(len(prompt) // 3, MIN_CALL)", "    return len(prompt) // 3",
        ["a small call counts at least 5,000"]),
    "a long prompt counts the minimum only": (
        "    return max(len(prompt) // 3, MIN_CALL)", "    return MIN_CALL",
        ["a long prompt counts its length / 3"]),
    "the total never resets for a new session": (
        '        total = (state.get("total", 0) if state.get("session_id") == session else 0) + estimate(prompt)',
        '        total = state.get("total", 0) + estimate(prompt)',
        ["a new session starts its total again"]),
    "the total is not kept between calls": (
        '        total = (state.get("total", 0) if state.get("session_id") == session else 0) + estimate(prompt)',
        "        total = estimate(prompt)",
        ["over 80% of the limit adds a note, and the call proceeds", "over the limit asks"]),
    "the limit never asks": (
        "        if total > limit:", "        if False:",
        ["over the limit asks"]),
    "the 80% note is never given": (
        "        elif total > limit * 80 // 100:", "        elif False:",
        ["over 80% of the limit adds a note, and the call proceeds"]),
    "every tool is counted, not only Agent": (
        'payload.get("tool_name") != "Agent"', "False",
        ["other tools are not counted"]),
    "the default limit is 50K": (
        "DEFAULT_LIMIT = 500000", "DEFAULT_LIMIT = 50000",
        ["with no config the limit is 500K (50K estimated is silent)"]),
    "an unreadable state file breaks the session": (
        "        except (OSError, ValueError):\n            state = {}", "        except OSError:\n            state = {}",
        ["an unreadable state file starts again, never breaks"]),
    "an error escapes and breaks the session": (
        "    except Exception:\n        pass", "    except ZeroDivisionError:\n        pass",
        ["malformed input exits 0 and prints nothing"]),
}

LAUNCHER_SRC = (HERE / "token_budget_guard.sh").read_text(encoding="utf-8")
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
    mut = HERE / ("_mutant_token_budget_guard.py" if kind == "py" else "_mutant_token_budget_guard.sh")
    mut.write_text(src.replace(old, new), encoding="utf-8")
    var = "TOKEN_BUDGET_HOOK" if kind == "py" else "TOKEN_BUDGET_LAUNCHER"
    try:
        p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                           env=dict(os.environ, **{var: str(mut)}))
    finally:
        mut.unlink()
    if "token_budget_guard self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(p.stdout + p.stderr)[-400:]}")
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
