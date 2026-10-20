#!/usr/bin/env python3
"""Self-test for protect_files.py — the write lock over the files you name.

Run:
    python3 hooks/protect_files_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch. Nothing is executed: each case is a
PreToolUse payload, and only the hook's decision is read. The protected list comes from a temporary config file
named by TOOLKIT_CONFIG, with HOME set to a temporary folder. Point it at a different hook with PF_HOOK=<path> and
a different launcher with PF_LAUNCHER=<path> (the mutation proof does).

Why the cases look like this. A write lock fails in two directions. It can miss a write: every way of writing a
file from a shell has a must-block case, and NotebookEdit is sent with its real field, notebook_path. Or it can
block a read, which gets the lock removed: every read of a protected file has a must-pass case, including the two
that fooled its ancestor (`sed -n` on a path holding "-i", and `2>&1`, which writes nothing).
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOOK = Path(os.environ.get("PF_HOOK", HERE / "protect_files.py"))
LAUNCHER = Path(os.environ.get("PF_LAUNCHER", HERE / "protect_files.sh"))
FAILS = []
HOME = Path(tempfile.mkdtemp(prefix="pf_home_"))
PROJECT = Path(tempfile.mkdtemp(prefix="pf_project_"))


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def config_file(text):
    p = Path(tempfile.mkdtemp(prefix="pf_cfg_")) / "toolkit-config.md"
    if text is not None:
        p.write_text(text, encoding="utf-8")
    return p


LIST = config_file("protected_files: [paper/main.tex, docs/from-advisor/, docs/from-instructor/, "
                   '"Shared Notes/plan.md", analysis/results.ipynb, ~/Archive/thesis.pdf]\nevidence_dir: evidence\n')
P = "paper/main.tex"


def run(tool, tool_input, cfg=LIST, argv=None, **kw):
    env = dict(os.environ, TOOLKIT_CONFIG=str(cfg), HOME=str(HOME), CLAUDE_PROJECT_DIR=str(PROJECT),
               **kw.pop("env", {}))
    payload = json.dumps({"tool_name": tool, "tool_input": tool_input})
    return subprocess.run(argv or [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True,
                          timeout=30, env=env, **kw)


def decide(tool, tool_input, **kw):
    """BLOCK, PASS or ERROR."""
    r = run(tool, tool_input, **kw)
    if r.returncode != 0 or r.stderr.strip():
        return "ERROR"
    if not r.stdout.strip():
        return "PASS"
    try:
        return "BLOCK" if json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] == "deny" else "PASS"
    except (ValueError, KeyError, TypeError):
        return "ERROR"


def bash(cmd):
    return ("Bash", {"command": cmd})


MUST_BLOCK = [
    ("Edit the file", ("Edit", {"file_path": P})),
    ("Edit it by absolute path", ("Edit", {"file_path": "/work/project/paper/main.tex"})),
    ("Write over it", ("Write", {"file_path": P})),
    ("MultiEdit it", ("MultiEdit", {"file_path": P, "edits": []})),
    ("NotebookEdit a protected notebook (its field is notebook_path)",
     ("NotebookEdit", {"notebook_path": "/work/project/analysis/results.ipynb", "new_source": "x"})),
    ("NotebookEdit sent with file_path", ("NotebookEdit", {"file_path": "analysis/results.ipynb", "new_source": "x"})),
    ("Write a file inside a protected folder", ("Write", {"file_path": "docs/from-advisor/notes.md"})),
    ("Bash: cp over it", bash(f"cp draft.tex {P}")),
    ("Bash: mv over it", bash(f"mv draft.tex {P}")),
    ("Bash: rm it", bash(f"rm {P}")),
    ("Bash: truncate with >", bash(f"> {P}")),
    ("Bash: append with >>", bash(f"echo x >> {P}")),
    ("Bash: sed -i", bash(f"sed -i '' 's/a/b/' {P}")),
    ("Bash: perl -i", bash(f"perl -i -pe 's/a/b/' {P}")),
    ("Bash: tee into it", bash(f"cat a | tee {P}")),
    ("Bash: python write_text", bash(f"python3 -c \"import pathlib; pathlib.Path('{P}').write_text('y')\"")),
    ("Bash: python open for writing", bash(f"python3 -c \"open('{P}','w').write('')\"")),
    ("Bash: chained after cd", bash(f"cd /tmp && cp x.tex {P}")),
    ("Bash: a path in another case", bash("cp x.tex PAPER/MAIN.TEX")),
    ("Bash: git checkout over it", bash(f"git checkout -- {P}")),
    ("Bash: git restore it", bash(f"git restore {P}")),
    ("Bash: a redirect into a protected folder", bash("echo x > docs/from-advisor/a.md")),
    ("Bash: a name with a space, escaped", bash("cp x Shared\\ Notes/plan.md")),
    ("Bash: a ~/ entry written as $HOME", bash("cp x $HOME/Archive/thesis.pdf")),
]
MUST_PASS = [
    ("Bash: cat it", bash(f"cat {P}")),
    ("Bash: grep it", bash(f"grep -n theorem {P}")),
    ("Bash: head it", bash(f"head -40 {P}")),
    ("Bash: ls a protected folder", bash("ls docs/from-advisor/")),
    ("Bash: sed -n on a path holding -i is a read", bash("sed -n '1,20p' docs/from-instructor/x.md")),
    ("Bash: a read ending in 2>&1", bash("ls docs/from-advisor/ 2>&1 | head -3")),
    ("Bash: a read sent to >&2", bash("cat docs/from-advisor/x.md >&2")),
    ("Bash: git log on it", bash(f"git log -- {P}")),
    ("Bash: git diff on it", bash(f"git diff -- {P}")),
    ("Bash: git add changes no bytes", bash(f"git add {P}")),
    ("Bash: git commit changes no bytes", bash('git commit -m "update the proof in paper/main.tex"')),
    ("Bash: a write to some other file", bash("echo x > notes.md")),
    ("Edit an unrelated file", ("Edit", {"file_path": "notes.md"})),
    ("Edit a similarly named file", ("Edit", {"file_path": "paper/domain.tex"})),
    ("Edit the same name in another folder", ("Edit", {"file_path": "slides/main.tex"})),
    ("Edit a folder whose name ends like the entry's", ("Edit", {"file_path": "mypaper/main.tex"})),
    ("Read is not a write tool", ("Read", {"file_path": P})),
    ("a ~/ entry is not a relative path", ("Edit", {"file_path": "Archive/thesis.pdf"})),
]

print("PROTECTED LIST set")
for name, (tool, ti) in MUST_BLOCK:
    check(f"blocks: {name}", decide(tool, ti) == "BLOCK")
for name, (tool, ti) in MUST_PASS:
    check(f"allows: {name}", decide(tool, ti) == "PASS")

print("NO LIST")
check("no config file: protects nothing", decide("Edit", {"file_path": P}, cfg=config_file(None)) == "PASS")
check("an empty list protects nothing", decide("Edit", {"file_path": P}, cfg=config_file("protected_files: []\n")) == "PASS")

print("REFUSAL")
edit_text = json.loads(run("Edit", {"file_path": P}).stdout)["hookSpecificOutput"]["permissionDecisionReason"]
bash_text = json.loads(run(*bash(f"cp x {P}")).stdout)["hookSpecificOutput"]["permissionDecisionReason"]
check("the refusal names the entry", "'paper/main.tex'" in edit_text)
check("the refusal names the config key", "protected_files" in edit_text)
check("the refusal says reading is still allowed", "Reading it is still allowed" in edit_text)
check("a Bash refusal names the Write-tool route", "Write tool" in bash_text and "Write tool" not in edit_text)

print("LOG")
log = PROJECT / "evidence" / "protect_files_audit.log"
before = log.read_text().count("\n") if log.exists() else 0
decide("Write", {"file_path": P})
after = log.read_text().count("\n") if log.exists() else 0
check("a denial adds one line to <evidence_dir>/protect_files_audit.log", after == before + 1)
afile = Path(tempfile.mkdtemp(prefix="pf_badlog_")) / "afile"
afile.write_text("a file where the log folder should be\n")
check("a log that cannot be written never undoes the block",
      decide("Edit", {"file_path": P}, cfg=config_file(f"protected_files: [{P}]\nevidence_dir: {afile}\n")) == "BLOCK")
r = subprocess.run([sys.executable, str(HOOK)], input="not json", capture_output=True, text=True, timeout=30)
check("malformed input exits 0 and prints nothing", r.returncode == 0 and not r.stdout.strip())

print("LAUNCHER")
pybin = Path(tempfile.mkdtemp(prefix="pf_py_"))
(pybin / "python3").symlink_to(sys.executable)  # a python3 shim reading $HOME would break with HOME replaced
with_py = {"PATH": f"{pybin}{os.pathsep}{os.environ['PATH']}"}
check("the launcher blocks too", decide("Edit", {"file_path": P}, argv=["bash", str(LAUNCHER)], env=with_py) == "BLOCK")
check("the launcher works when started from its own folder by bare name",
      decide("Edit", {"file_path": P}, argv=["bash", LAUNCHER.name], cwd=LAUNCHER.parent, env=with_py) == "BLOCK")
r = run("Edit", {"file_path": P}, argv=["/bin/bash", str(LAUNCHER)], env={"PATH": "/nonexistent"})
check("with no python3 on PATH the launcher exits 0 and prints nothing", r.returncode == 0 and not r.stdout and not r.stderr)

print(f"\nprotect_files self-test: {'all passed' if not FAILS else f'{len(FAILS)} failed'}")
sys.exit(1 if FAILS else 0)
