#!/usr/bin/env python3
"""Self-test for token_budget_guard.py — the per-session token-budget warning.

Run:
    python3 hooks/token_budget_guard_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch. Each case uses a temporary HOME, so your
~/.claude is never touched. Point it at a different hook with TOKEN_BUDGET_HOOK=<path> and a different launcher
with TOKEN_BUDGET_LAUNCHER=<path> (the mutation proof does).

Why the cases look like this: the shell hook this replaces measured a prompt only up to its first quote, so a
quoted prompt has a case; and a warning that never resets, or resets on every call, is useless either way.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = Path(os.environ.get("TOKEN_BUDGET_HOOK", HERE / "token_budget_guard.py"))
LAUNCHER = Path(os.environ.get("TOKEN_BUDGET_LAUNCHER", HERE / "token_budget_guard.sh"))
FAILS = []


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def new_home(limit=None):
    h = Path(tempfile.mkdtemp(prefix="tokbudget_"))
    (h / ".claude").mkdir()
    if limit is not None:
        (h / ".claude" / "token-budget.json").write_text(json.dumps({"session_limit": limit}))
    return h


def call(home, prompt="x", session="s1", tool="Agent", argv=None, raw=None, **kw):
    data = raw if raw is not None else json.dumps(
        {"tool_name": tool, "session_id": session, "tool_input": {"prompt": prompt}})
    env = dict(os.environ, HOME=str(home), **kw.pop("env", {}))
    r = subprocess.run(argv or [sys.executable, str(HOOK)], input=data, capture_output=True, text=True,
                       timeout=30, env=env, **kw)
    if r.returncode != 0 or r.stderr.strip():
        return "ERROR", ""
    if not r.stdout.strip():
        return "SILENT", ""
    out = json.loads(r.stdout)["hookSpecificOutput"]
    return ("ASK" if out.get("permissionDecision") == "ask" else "NOTE"), json.dumps(out)


def total(home):
    """The recorded total, or None when the state is missing or unreadable (a case fails; the run goes on)."""
    try:
        return json.loads((home / ".claude" / "toolkit" / "state" / "token_budget.json").read_text())["total"]
    except (OSError, ValueError, KeyError, TypeError):
        return None


h = new_home(limit=20000)
check("a small call is silent", call(h)[0] == "SILENT")
check("a small call counts at least 5,000", total(h) == 5000)
call(h)
call(h)
got, text = call(h, prompt="y" * 6000)  # a fourth call of at least 5,000: 20,000, over 80% and not over 20,000
check("over 80% of the limit adds a note, and the call proceeds", got == "NOTE" and "of 20K" in text)
got, text = call(h, prompt="y" * 6000)
check("over the limit asks", got == "ASK" and "Proceed anyway" in text)

h = new_home(limit=20000)
call(h, prompt="z" * 30000)
check("a long prompt counts its length / 3", total(h) == 10000)
h = new_home(limit=20000)
quoted = 'Review "the gate" and report.' + " q" * 15000
call(h, prompt=quoted)
check("a prompt holding quotes is counted in full", total(h) == len(quoted) // 3)

h = new_home(limit=20000)
for _ in range(3):
    call(h, session="s1")
call(h, session="s2")
check("a new session starts its total again", total(h) == 5000)

h = new_home(limit=20000)
got, _ = call(h, tool="Bash")
check("other tools are not counted", got == "SILENT"
      and not (h / ".claude" / "toolkit" / "state" / "token_budget.json").exists())
h = new_home()
for _ in range(10):
    call(h)
check("with no config the limit is 500K (50K estimated is silent)", call(h)[0] == "SILENT")
h = new_home()
(h / ".claude" / "token-budget.json").write_text("not json")
check("an unreadable config falls back to 500K", call(h)[0] == "SILENT")
h = new_home(limit=20000)
(h / ".claude" / "toolkit" / "state").mkdir(parents=True)
(h / ".claude" / "toolkit" / "state" / "token_budget.json").write_text("garbage")
check("an unreadable state file starts again, never breaks", call(h)[0] == "SILENT" and total(h) == 5000)
check("malformed input exits 0 and prints nothing", call(new_home(), raw="{not json")[0] == "SILENT")

pybin = Path(tempfile.mkdtemp(prefix="tokbudget_py_"))
(pybin / "python3").symlink_to(sys.executable)  # a python3 shim reading $HOME would break with HOME replaced
with_py = {"PATH": f"{pybin}{os.pathsep}{os.environ['PATH']}"}
h = new_home(limit=6000)
call(h, argv=["bash", str(LAUNCHER)], env=with_py)
check("the launcher counts too", total(h) == 5000)
h = new_home(limit=6000)
call(h, argv=["bash", LAUNCHER.name], cwd=LAUNCHER.parent, env=with_py)
check("the launcher works when started from its own folder by bare name",
      (h / ".claude" / "toolkit" / "state" / "token_budget.json").exists())
r = subprocess.run(["/bin/bash", str(LAUNCHER)], input="{}", capture_output=True, text=True, timeout=30,
                   env=dict(os.environ, HOME=str(new_home()), PATH="/nonexistent"))
check("with no python3 on PATH the launcher exits 0 and prints nothing", r.returncode == 0 and not r.stdout and not r.stderr)

print(f"\ntoken_budget_guard self-test: {'all passed' if not FAILS else f'{len(FAILS)} failed'}")
sys.exit(1 if FAILS else 0)
