#!/usr/bin/env python3
"""Self-test for guard_hook_run.py -- the /guard-hook generator.

Run, from a clone of the toolkit (the installer does not copy self-tests):
    python3 shared/skills/guard-hook/assets/guard_hook_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch. Point it at a different runner with
GUARD_HOOK_RUN=<path> (the mutation proof does).
Every case runs inside a throwaway sandbox directory. Nothing under the real
.claude/ tree is read or written; no hook is registered; no settings file is
touched. The only files removed are tempfiles this test itself created.

THE CASE THAT MATTERS is INERT-TEST-DETECTED: a guard whose self-test passes even
when its TRIGGER has been removed. That test proves nothing, and `failfirst` must
exit 6 rather than report a clean run. This whole skill exists because a guard
that has never failed has never been tested.

Re-run this whenever a template, a subcommand, or an exit code changes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
RUN = os.environ.get("GUARD_HOOK_RUN") or os.path.join(HERE, "guard_hook_run.py")
SENTINEL = "GUARD_HOOK-UNAUTHORED"

STUB_BLOCK = '    ("[GAP: author the case this guard exists to catch]", "REPLACE ME"),'
STUB_PASS = '    ("[GAP: author a legitimate lookalike that must not be caught]", "harmless"),'


class Sandbox(object):
    def __init__(self):
        self.dir = tempfile.mkdtemp(prefix="guard_hook_selftest_")
        self.hooks = os.path.join(self.dir, ".claude", "hooks")
        os.makedirs(self.hooks)
        self.settings = os.path.join(self.dir, ".claude", "settings.json")
        with open(self.settings, "w") as f:
            json.dump({"hooks": {"PreToolUse": []}}, f, indent=2)

    def run(self, *argv):
        cmd = [sys.executable, RUN, "--hooks-dir", self.hooks,
               "--settings", self.settings] + list(argv)
        return subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    def new(self, name="demo", posture="blocking", tools="Bash"):
        return self.run("new", "--name", name, "--posture", posture, "--tools", tools)

    def author(self, name="demo", inert=False, pattern="FORBIDDEN"):
        """Turn the scaffold into a real guard, the way a human would."""
        logic = os.path.join(self.hooks, name + ".py")
        src = open(logic).read()
        src = src.replace('r"""(?!x)x"""', 'r"""%s"""' % pattern)
        src = "\n".join(l for l in src.splitlines() if SENTINEL not in l) + "\n"
        with open(logic, "w") as f:
            f.write(src)

        st = os.path.join(self.hooks, name + "_selftest.py")
        t = open(st).read()
        # An INERT test has no case that depends on TRIGGER at all.
        t = t.replace(STUB_BLOCK, "" if inert
                      else '    ("the forbidden shape", "echo %s now"),' % pattern)
        t = t.replace(STUB_PASS, '    ("an innocent command", "echo hello"),')
        t = "\n".join(l for l in t.splitlines() if SENTINEL not in l) + "\n"
        with open(st, "w") as f:
            f.write(t)

    def read_settings(self):
        return json.loads(open(self.settings).read())

    def baks(self):
        d = os.path.dirname(self.settings)
        return [f for f in os.listdir(d) if f.startswith("settings.json.bak-")]

    def close(self):
        shutil.rmtree(self.dir, ignore_errors=True)


CASES = []


def case(label):
    def deco(fn):
        CASES.append((label, fn))
        return fn
    return deco


def rc(r):
    return r.returncode


# ---- scaffolding -----------------------------------------------------------

@case("new scaffolds exactly three files")
def _(sb):
    r = sb.new()
    files = sorted(os.listdir(sb.hooks))
    want = ["demo.py", "demo.sh", "demo_selftest.py"]
    return rc(r) == 0 and files == want, "rc=%d files=%s" % (rc(r), files)


@case("the launcher is executable and only launches")
def _(sb):
    sb.new()
    p = os.path.join(sb.hooks, "demo.sh")
    lines = open(p).read().splitlines()
    body = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    ok = (os.access(p, os.X_OK)
          and lines[0].startswith("#!")
          and len(body) == 1
          and body[0].startswith("exec python3 "))
    return ok, "exec=%s shebang=%r body=%r" % (os.access(p, os.X_OK), lines[0], body)


@case("MUST FAIL: a second new on the same name is a collision (exit 2)")
def _(sb):
    sb.new()
    r = sb.new()
    return rc(r) == 2 and "COLLISION" in r.stderr, "rc=%d" % rc(r)


@case("MUST FAIL: an illegal hook name is refused (exit 2)")
def _(sb):
    r = sb.new(name="Demo-Hook")
    return rc(r) == 2, "rc=%d" % rc(r)


@case("the fresh scaffold's own self-test FAILS (red before green)")
def _(sb):
    sb.new()
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo_selftest.py")],
                       capture_output=True, text=True, timeout=120)
    return rc(r) == 1, "rc=%d" % rc(r)


# ---- registration ----------------------------------------------------------

@case("MUST FAIL: register refuses an unauthored guard (exit 3)")
def _(sb):
    sb.new()
    r = sb.run("register", "--name", "demo", "--matcher", "Bash")
    return rc(r) == 3 and SENTINEL in r.stderr, "rc=%d" % rc(r)


@case("MUST FAIL: register refuses when the self-test does not pass (exit 4)")
def _(sb):
    sb.new()
    sb.author()
    st = os.path.join(sb.hooks, "demo_selftest.py")
    t = open(st).read().replace('"echo hello"', '"echo FORBIDDEN"')
    with open(st, "w") as f:
        f.write(t)
    r = sb.run("register", "--name", "demo", "--matcher", "Bash")
    return rc(r) == 4, "rc=%d" % rc(r)


@case("register installs the entry, and writes a backup first")
def _(sb):
    sb.new()
    sb.author()
    r = sb.run("register", "--name", "demo", "--matcher", "Bash")
    cfg = sb.read_settings()
    cmds = [h["command"] for e in cfg["hooks"]["PreToolUse"] for h in e["hooks"]]
    return (rc(r) == 0 and len(sb.baks()) == 1
            and any("demo.sh" in c for c in cmds)), \
        "rc=%d baks=%d cmds=%s" % (rc(r), len(sb.baks()), cmds)


@case("the backup is a faithful copy of the pre-write file")
def _(sb):
    sb.new()
    sb.author()
    before = open(sb.settings).read()
    sb.run("register", "--name", "demo", "--matcher", "Bash")
    bak = os.path.join(os.path.dirname(sb.settings), sb.baks()[0])
    return open(bak).read() == before, "backup differs from pre-write content"


@case("register twice is a no-op, not a duplicate")
def _(sb):
    sb.new()
    sb.author()
    sb.run("register", "--name", "demo", "--matcher", "Bash")
    r = sb.run("register", "--name", "demo", "--matcher", "Bash")
    cfg = sb.read_settings()
    n = sum(1 for e in cfg["hooks"]["PreToolUse"]
            for h in e["hooks"] if "demo.sh" in h["command"])
    return rc(r) == 0 and n == 1 and "ALREADY" in r.stdout, "rc=%d n=%d" % (rc(r), n)


@case("a narrow write matcher is warned about, not silently accepted")
def _(sb):
    sb.new(name="w", tools="Edit,Write,MultiEdit,NotebookEdit")
    sb.author(name="w")
    r = sb.run("register", "--name", "w", "--matcher", "Edit|Write")
    return rc(r) == 0 and "MultiEdit" in r.stderr, "rc=%d stderr=%r" % (rc(r), r.stderr[:80])


# ---- fail-first ------------------------------------------------------------

@case("failfirst proves a real guard bites, and restores it byte for byte")
def _(sb):
    sb.new()
    sb.author()
    logic = os.path.join(sb.hooks, "demo.py")
    before = open(logic).read()
    r = sb.run("failfirst", "--name", "demo")
    return (rc(r) == 0 and open(logic).read() == before
            and "FAIL-FIRST PROVEN" in r.stdout), "rc=%d" % rc(r)


@case("MUST FAIL: an INERT self-test is caught (exit 6) -- the headline case")
def _(sb):
    sb.new()
    sb.author(inert=True)
    st = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo_selftest.py")],
                        capture_output=True, text=True, timeout=120)
    r = sb.run("failfirst", "--name", "demo")
    # The inert test passes on its own -- that is exactly why it is dangerous.
    return (rc(st) == 0 and rc(r) == 6 and "proves nothing" in r.stderr), \
        "selftest rc=%d failfirst rc=%d" % (rc(st), rc(r))


@case("failfirst restores the guard even when the mutated run misbehaves")
def _(sb):
    sb.new()
    sb.author(inert=True)
    logic = os.path.join(sb.hooks, "demo.py")
    before = open(logic).read()
    sb.run("failfirst", "--name", "demo")
    return open(logic).read() == before, "guard left neutered after a failed failfirst"


@case("MUST FAIL: failfirst refuses a guard with no TRIGGER to neuter (exit 2)")
def _(sb):
    sb.new()
    sb.author()
    logic = os.path.join(sb.hooks, "demo.py")
    src = open(logic).read().replace("TRIGGER = re.compile(", "OTHER = re.compile(")
    with open(logic, "w") as f:
        f.write(src)
    r = sb.run("failfirst", "--name", "demo")
    return rc(r) == 2, "rc=%d" % rc(r)


# ---- audit -----------------------------------------------------------------

@case("audit is clean on a guard built by this skill")
def _(sb):
    sb.new()
    sb.author()
    r = sb.run("audit")
    return rc(r) == 0 and "no traps" in r.stdout, "rc=%d" % rc(r)


@case("MUST FAIL: audit catches the grep -o truncation idiom (exit 7)")
def _(sb):
    sb.new()
    sb.author()
    with open(os.path.join(sb.hooks, "legacy.sh"), "w") as f:
        f.write('#!/bin/bash\nC=$(grep -o \'"command"[^"]*"\')\n'
                'echo "$C"\nexit 0\n[ -n "$C" ] && echo x\n')
    r = sb.run("audit")
    return rc(r) == 7 and "GREP_O_TRUNCATION" in r.stdout, "rc=%d" % rc(r)


@case("audit does NOT flag a launcher that merely documents the old idiom")
def _(sb):
    sb.new()
    sb.author()
    with open(os.path.join(sb.hooks, "fixed.sh"), "w") as f:
        f.write('#!/bin/bash\n'
                '# Rewritten. This file used to parse the payload with\n'
                '#   grep -o \'"command"[[:space:]]*:[[:space:]]*"[^"]*"\'\n'
                '# whose class truncates at the first embedded quote.\n'
                'exec python3 "$(dirname "$0")/fixed.py"\n')
    with open(os.path.join(sb.hooks, "fixed.py"), "w") as f:
        f.write("import json,sys\ntry:\n    json.load(sys.stdin)\nexcept Exception:\n    pass\n")
    with open(os.path.join(sb.hooks, "fixed_selftest.py"), "w") as f:
        f.write("import sys\nsys.exit(0)\n")
    r = sb.run("audit")
    return "GREP_O_TRUNCATION" not in r.stdout, "stdout=%r" % r.stdout[:200]


@case("MUST FAIL: audit catches a hook with no self-test (exit 7)")
def _(sb):
    with open(os.path.join(sb.hooks, "bare.sh"), "w") as f:
        f.write("#!/bin/bash\nexit 0\n")
    r = sb.run("audit")
    return rc(r) == 7 and "NO_SELFTEST" in r.stdout, "rc=%d" % rc(r)


@case("MUST FAIL: audit catches an if-gated registration (exit 7)")
def _(sb):
    sb.new()
    sb.author()
    cfg = sb.read_settings()
    cfg["hooks"]["PreToolUse"].append(
        {"matcher": "Bash", "if": "Bash(git push *)",
         "hooks": [{"type": "command", "command": '"x/legacy.sh"'}]})
    with open(sb.settings, "w") as f:
        f.write(json.dumps(cfg, indent=2))
    r = sb.run("audit")
    return rc(r) == 7 and "IF_GATED" in r.stdout, "rc=%d" % rc(r)


# ---- advisory posture ------------------------------------------------------

@case("advisory posture scaffolds a PostToolUse guard that never blocks")
def _(sb):
    r = sb.new(name="adv", posture="advisory", tools="Edit,Write,MultiEdit,NotebookEdit")
    src = open(os.path.join(sb.hooks, "adv.py")).read()
    return (rc(r) == 0 and "PostToolUse" in r.stdout
            and "ALWAYS 0" in src and "permissionDecision" not in src), "rc=%d" % rc(r)


@case("an advisory guard flags on stderr and still exits 0")
def _(sb):
    sb.new(name="adv", posture="advisory", tools="Edit,Write,MultiEdit,NotebookEdit")
    sb.author(name="adv")
    payload = json.dumps({"tool_name": "Edit",
                          "tool_input": {"file_path": "a.md", "new_string": "FORBIDDEN"}})
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "adv.py")],
                       input=payload, capture_output=True, text=True, timeout=60)
    return rc(r) == 0 and "FORBIDDEN" in r.stderr and not r.stdout.strip(), \
        "rc=%d stdout=%r" % (rc(r), r.stdout[:60])


# ---- the generated guard's own contract ------------------------------------

@case("a generated guard fails open on an unreadable payload, and says so")
def _(sb):
    sb.new()
    sb.author()
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo.py")],
                       input="{not json", capture_output=True, text=True, timeout=60)
    return rc(r) == 0 and not r.stdout.strip() and "NOT scanned" in r.stderr, \
        "rc=%d stderr=%r" % (rc(r), r.stderr[:80])


@case("a generated blocking guard reads NotebookEdit's notebook_path and new_source")
def _(sb):
    sb.new(tools="Edit,Write,MultiEdit,NotebookEdit")
    sb.author()
    payload = json.dumps({"tool_name": "NotebookEdit",
                          "tool_input": {"notebook_path": "/work/a.ipynb", "new_source": "FORBIDDEN"}})
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo.py")],
                       input=payload, capture_output=True, text=True, timeout=60)
    return rc(r) == 0 and '"permissionDecision"' in r.stdout, "stdout=%r stderr=%r" % (r.stdout[:60], r.stderr[:80])


@case("a generated advisory guard reads NotebookEdit's new_source and names its notebook")
def _(sb):
    sb.new(posture="advisory", tools="Edit,Write,MultiEdit,NotebookEdit")
    sb.author()
    payload = json.dumps({"tool_name": "NotebookEdit",
                          "tool_input": {"notebook_path": "/work/a.ipynb", "new_source": "FORBIDDEN"}})
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo.py")],
                       input=payload, capture_output=True, text=True, timeout=60)
    return rc(r) == 0 and "FORBIDDEN" in r.stderr and "/work/a.ipynb" in r.stderr, "stderr=%r" % r.stderr[:120]


@case("a generated guard ignores tools it was not registered for")
def _(sb):
    sb.new()
    sb.author()
    payload = json.dumps({"tool_name": "Read", "tool_input": {"command": "FORBIDDEN"}})
    r = subprocess.run([sys.executable, os.path.join(sb.hooks, "demo.py")],
                       input=payload, capture_output=True, text=True, timeout=60)
    return rc(r) == 0 and not r.stdout.strip(), "stdout=%r" % r.stdout[:60]


def main():
    print("guard_hook_run.py -- generator self-test")
    print("=" * 72)
    failures = []
    for label, fn in CASES:
        sb = Sandbox()
        try:
            ok, detail = fn(sb)
        except Exception as exc:            # a crash is a failure, never a skip
            ok, detail = False, "raised %s: %s" % (type(exc).__name__, exc)
        finally:
            sb.close()
        print("  %s %s" % ("ok  " if ok else "FAIL", label))
        if not ok:
            failures.append((label, detail))

    total = len(CASES)
    must_fail = sum(1 for l, _ in CASES if l.startswith("MUST FAIL"))
    print("=" * 72)
    if not failures:
        print("PASS -- %d/%d (%d must-fail-correctly, %d must-pass)"
              % (total, total, must_fail, total - must_fail))
        return 0
    print("FAIL -- %d of %d:" % (len(failures), total))
    for label, detail in failures:
        print("  %s\n      %s" % (label, detail))
    return 1


if __name__ == "__main__":
    sys.exit(main())
