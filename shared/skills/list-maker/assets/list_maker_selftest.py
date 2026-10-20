#!/usr/bin/env python3
"""
list_maker_selftest.py -- runs the script's own suite, and asserts the things a caller
depends on that the suite cannot see from inside itself.

Two layers, because they fail differently. The inner suite checks the LOGIC. This checks
the SURFACE: that the script is invokable, that its exit codes mean what SKILL.md says
they mean, and that the documented actions exist. A tool whose exit code is always 0 is
invisible to every caller.

Point it at a different copy with LIST_MAKER=<path>, which is what the mutation run does.
"""
from __future__ import annotations

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
SCRIPT = pathlib.Path(os.environ.get("LIST_MAKER", HERE / "list_maker_run.py"))

passed = failed = 0


def ck(name: str, cond: bool) -> None:
    global passed, failed
    passed, failed = (passed + 1, failed) if cond else (passed, failed + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {name}")


def run(*args):
    env = {k: v for k, v in os.environ.items() if k != "LIST_MAKER_LEDGER"}
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, env=env)


inner = run("--self-test")
ck("the script's own suite passes", inner.returncode == 0)
ck("and it reports a count", "passed," in inner.stdout)

help_out = run("--help").stdout
for action in ("scan", "add", "bump", "status", "list", "next", "active"):
    ck(f"action {action!r} is a real choice", action in help_out)

tmp = pathlib.Path(tempfile.mkdtemp())
led = tmp / "w.json"

# --- EXIT CODES MEAN WHAT SKILL.md SAYS. 2 is a refusal, 1 is nothing-to-report, 0 is done.
r = run("bump", "--id", "999", "--tier", "1", "--ledger", str(led))
ck("bumping an id that does not exist exits 2", r.returncode == 2)
ck("and says REFUSED", "REFUSED" in r.stderr)
r = run("bump", "--id", "1", "--tier", "77", "--ledger", str(led))
ck("a tier outside the scale exits 2", r.returncode == 2)
r = run("scan", "--transcript", str(tmp / "nope.txt"))
ck("a missing transcript exits 2", r.returncode == 2)
r = run("list", "--ledger", str(led))
ck("an empty ledger exits 1, not 0", r.returncode == 1)
ck("and says so in words", "nothing open" in r.stdout.lower())
r = run("next", "--ledger", str(led))
ck("next on an empty ledger exits 1", r.returncode == 1)

# --- a real round trip through the CLI, which the inner suite never exercises
items = tmp / "i.json"
items.write_text('{"items": [{"text": "Send the infrastructure email", "owner": "me", '
                 '"tier": 1, "source": "t.txt:623", "outward": true}, '
                 '{"text": "Short answers for the study guide", "owner": "them", "tier": 3}]}')
r = run("add", "--items", str(items), "--ledger", str(led))
ck("add through the CLI exits 0", r.returncode == 0)
ck("it reports the new numbers", "1." in r.stdout and "2." in r.stdout)
r = run("add", "--items", str(items), "--ledger", str(led))
ck("adding the same file twice exits 1, nothing new", r.returncode == 1)
ck("and says they were already present", "already on the list" in r.stdout)
r = run("next", "--ledger", str(led))
ck("next returns the tier-1 item", r.returncode == 0 and r.stdout.startswith("1."))
ck("and marks it outward-facing", "outward" in r.stdout)
r = run("active", "--ledger", str(led))
ck("positive control: an active list with work on it exits 0", r.returncode == 0 and "ACTIVE LIST:" in r.stdout)
r = run("bump", "--id", "2", "--tier", "1", "--why", "asked to do it first", "--ledger", str(led))
ck("a bump exits 0", r.returncode == 0)
ck("and states the id is unchanged", "id is unchanged" in r.stdout)
r = run("status", "--id", "1", "--set", "done", "--ledger", str(led))
ck("marking done exits 0", r.returncode == 0)
ck("and says the number is kept for life", "for life" in r.stdout)
r = run("list", "--ledger", str(led))
ck("a done item is hidden by default", " 1." not in r.stdout)
r = run("list", "--all", "--ledger", str(led))
ck("a done item is visible with --all", " 1." in r.stdout)
run("status", "--id", "2", "--set", "deferred", "--ledger", str(led))
r = run("list", "--ledger", str(led))
ck("a DEFERRED item is still shown", " 2." in r.stdout)
ck("and is marked rather than hidden", "[~]" in r.stdout)
run("status", "--id", "2", "--set", "done", "--ledger", str(led))
r = run("active", "--ledger", str(led))
ck("a cleared active list exits 3, never 0 or 1", r.returncode == 3)
ck("and tells the caller to ask before promoting", "Ask the user whether to restart" in r.stdout)

items2 = tmp / "i2.json"
items2.write_text('{"items": [{"text": "A third thing entirely", "tier": 2}]}')
r = run("add", "--items", str(items2), "--ledger", str(led))
ck("the next item gets 3, not a reused 1", " 3." in r.stdout)

# --- one stream, one owner vocabulary
r = run("add", "--items", str(items2), "--owners", "me,client,both", "--ledger", str(led))
ck("--owners that differ from an existing ledger's are refused, exit 2", r.returncode == 2 and "fixed at creation" in r.stderr)
led2 = tmp / "client.json"
items3 = tmp / "i3.json"
items3.write_text('{"items": [{"text": "Recolour the overlay", "owner": "client", "tier": 1}]}')
r = run("add", "--items", str(items3), "--owners", "me,client,both", "--ledger", str(led2))
ck("positive control: --owners on a new ledger sets its vocabulary", r.returncode == 0)

# --- DURABILITY. The numbers are the product; an untracked ledger lives on one disk only.
# The warning sits on the SAVE path, so it fires on the action that creates the thing worth losing.
subprocess.run(["git", "init", "-q", str(tmp)], capture_output=True)
untracked = tmp / "u.json"
items4 = tmp / "i4.json"
items4.write_text('{"items": [{"text": "durability probe", "tier": 4}]}')
r = run("add", "--items", str(items4), "--ledger", str(untracked))
ck("saving an UNTRACKED ledger warns", "NOT TRACKED" in r.stderr)
ck("the warning names the fix", "git add" in r.stderr)
ck("it still saves rather than refusing", untracked.exists())
subprocess.run(["git", "-C", str(tmp), "add", "u.json"], capture_output=True)
r = run("add", "--items", str(items4), "--ledger", str(untracked))
ck("a TRACKED ledger does not warn", "NOT TRACKED" not in r.stderr)

shutil.rmtree(tmp, ignore_errors=True)
print(f"list-maker surface self-test: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
