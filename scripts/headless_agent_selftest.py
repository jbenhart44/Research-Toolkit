#!/usr/bin/env python3
"""Self-test for headless_agent.py. No real Claude call: a stand-in `claude` on PATH writes output.md and echoes.

    python3 scripts/headless_agent_selftest.py    # exit 0 = every case passes

Point it at a different copy with HEADLESS_AGENT=<path>, which is what scripts/headless_agent_mutations.py does. This
file, not the script, holds the refused values (fable, a full model ID), because a self-test plants them on purpose.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile
import types

SCRIPT = pathlib.Path(os.environ.get("HEADLESS_AGENT") or pathlib.Path(__file__).resolve().parent / "headless_agent.py")
# Compiled from source every run, never through the import system: the mutation check writes successive mutants to
# one path, and a cached .pyc of an earlier mutant was once loaded in place of the current one.
ha = types.ModuleType("headless_agent_under_test")
exec(compile(SCRIPT.read_text(encoding="utf-8"), str(SCRIPT), "exec"), ha.__dict__)

ok = bad = 0


def ck(name, cond):
    global ok, bad
    ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
    print(f"  {'PASS' if cond else 'FAIL'} {name}")


c = ha.command("p", "sonnet", ["/x"], False)
ck("the output rule is Edit(path), not Write(path) (Write alone is denied)",
   "Edit(/output.md)" in c and not any(t.startswith("Write(") for t in c))
ck("never skips permissions", not any("skip-permissions" in t for t in c))
ck("no Bash unless asked", not any(t.startswith("Bash") for t in c))
ck("--bash allows only python3, grep and rg",
   {t for t in ha.command("p", "sonnet", [], True) if t.startswith("Bash")} == {"Bash(python3:*)", "Bash(grep:*)", "Bash(rg:*)"})
ck("the model is passed", "--model" in c and c[c.index("--model") + 1] == "sonnet")
ck("extra read folders are passed", "--add-dir" in c and c[c.index("--add-dir") + 1] == "/x")

fake = pathlib.Path(tempfile.mkdtemp(prefix="headless_fake_"))
(fake / "claude").write_text('#!/bin/sh\npython3 -c "import os,sys; open(\'output.md\',\'w\').write(\'x\'*int('
                             'os.environ.get(\'FAKE_BYTES\',\'0\'))) if int(os.environ.get(\'FAKE_BYTES\',\'0\')) else None"'
                             '\necho "args: $*"\n')
(fake / "claude").chmod(0o755)
prompt = pathlib.Path(tempfile.mkdtemp(prefix="headless_prompt_")) / "prompt.md"
prompt.write_text("Summarise the notes.\n", encoding="utf-8")


def quiet_run(*a, **kw):
    real_out, real_err = sys.stdout, sys.stderr
    with open(os.devnull, "w") as null:
        sys.stdout = sys.stderr = null
        try:
            return ha.run(*a, **kw)
        except Exception as e:  # noqa: BLE001 - a crash fails its case; the run goes on
            return f"raised {type(e).__name__}"
        finally:
            sys.stdout, sys.stderr = real_out, real_err


os.environ["PATH"] = f"{fake}{os.pathsep}{os.environ.get('PATH', '')}"
os.environ["FAKE_BYTES"] = "800"
ck("an output over 500 bytes is exit 0", quiet_run(str(prompt), tempfile.mkdtemp()) == 0)
os.environ["FAKE_BYTES"] = "100"
ck("an output of 500 bytes or less is exit 1", quiet_run(str(prompt), tempfile.mkdtemp()) == 1)
os.environ["FAKE_BYTES"] = "0"
ck("no output at all is exit 1", quiet_run(str(prompt), tempfile.mkdtemp()) == 1)
os.environ["FAKE_BYTES"] = "800"
ck("opus is allowed", quiet_run(str(prompt), tempfile.mkdtemp(), model="opus") == 0)
ck("haiku is allowed", quiet_run(str(prompt), tempfile.mkdtemp(), model="haiku") == 0)
ck("fable is refused (it can bill usage credits without asking)",
   quiet_run(str(prompt), tempfile.mkdtemp(), model="fable") == 2)
ck("a full model ID is refused", quiet_run(str(prompt), tempfile.mkdtemp(), model="claude-opus-5-5") == 2)
ck("a missing prompt file is exit 2, never a run", quiet_run("/nonexistent/prompt.md", tempfile.mkdtemp()) == 2)
work = pathlib.Path(tempfile.mkdtemp()) / "new" / "folder"
quiet_run(str(prompt), str(work))
ck("the working folder is created", work.is_dir())

print(f"headless_agent self-test: {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
