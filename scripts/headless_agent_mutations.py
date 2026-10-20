#!/usr/bin/env python3
"""Prove scripts/headless_agent_selftest.py catches each way the headless fallback could run wider, or report wrongly.

    python3 scripts/headless_agent_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong, not
broken. No real Claude call is made: the self-test puts a stand-in `claude` on PATH.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "headless_agent.py").read_text(encoding="utf-8")
MUTANTS = {
    "fable is allowed": (
        'MODELS = ("haiku", "sonnet", "opus")', 'MODELS = ("haiku", "sonnet", "opus", "fable")',
        ["fable is refused (it can bill usage credits without asking)"]),
    "any model is allowed": (
        "    if model not in MODELS:", "    if False:",
        ["fable is refused (it can bill usage credits without asking)", "a full model ID is refused"]),
    "the output rule is Write(path), which the permission check denies": (
        'tools = ["Read", "Edit(/output.md)"]', 'tools = ["Read", "Write(/output.md)"]',
        ["the output rule is Edit(path), not Write(path)"]),
    "permissions are skipped": (
        'cmd = ["claude", "-p", prompt, "--model", model, "--allowedTools", *tools]',
        'cmd = ["claude", "-p", prompt, "--model", model, "--dangerously-skip-permissions", "--allowedTools", *tools]',
        ["never skips permissions"]),
    "Bash is always allowed": (
        '+ (["Bash(python3:*)", "Bash(grep:*)", "Bash(rg:*)"] if bash else [])',
        '+ ["Bash(python3:*)", "Bash(grep:*)", "Bash(rg:*)"]',
        ["no Bash unless asked"]),
    "the model is not passed": (
        'cmd = ["claude", "-p", prompt, "--model", model, "--allowedTools", *tools]',
        'cmd = ["claude", "-p", prompt, "--allowedTools", *tools]',
        ["the model is passed"]),
    "extra read folders are dropped": (
        '    if add_dirs:\n        cmd += ["--add-dir", *add_dirs]', "    if False:\n        pass",
        ["extra read folders are passed"]),
    "any output counts as done": (
        "    return 0 if size > MIN_BYTES else 1", "    return 0 if size >= 0 else 1",
        ["an output of 500 bytes or less is exit 1", "no output at all is exit 1"]),
    "a missing prompt file is run anyway": (
        "    if not pf.is_file():", "    if False:",
        ["a missing prompt file is exit 2, never a run"]),
    "the working folder is not created": (
        "    work.mkdir(parents=True, exist_ok=True)", "    pass",
        ["the working folder is created"]),
}

TEST = HERE / "headless_agent_selftest.py"
base = subprocess.run([sys.executable, str(TEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_headless_agent.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(TEST)], capture_output=True, text=True,
                           env={**os.environ, "HEADLESS_AGENT": str(mut)})
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
