#!/usr/bin/env python3
"""Self-test for /bulletproof's script. Must-pass and must-fail cases, on fixtures.

Run, from a clone of the toolkit (the installer does not copy self-tests):
    python3 shared/skills/bulletproof/assets/bulletproof_selftest.py
Point it at a different runner with BULLETPROOF_RUN=<path> (the mutation proof does).

The must-fail half is the point. Every case marked MUST-FAIL is handed the exact thing the
guard exists to reject, and the guard has to reject it. A self-test whose cases have only ever
passed proves the happy path and nothing about the guard, and an assertion helper can let
must-fail cases pass vacuously, so each case is also run against the KNOWN-GOOD input first to
prove the check can distinguish the two.
"""

import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
RUN = pathlib.Path(os.environ.get("BULLETPROOF_RUN") or HERE / "bulletproof_run.py")
_spec = importlib.util.spec_from_file_location("bulletproof_run", RUN)
B = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(B)

PASSED, FAILED = [], []


def check(name, cond, detail=""):
    if cond:
        PASSED.append(name)
        print(f"  pass  {name}")
    else:
        FAILED.append((name, detail))
        print(f"  FAIL  {name}" + (f"  -> {detail}" if detail else ""))


GOOD_MUTATIONS = '''
WEEK = SITE / "functions" / "week.js"
MUTATIONS = [
    (
        "the lock never refuses",
        WEEK,
        [("if (locked)", "if (false)")],
        "open",
        ["a pick after the lock is refused"],
    ),
    (
        "two names on separate lines",
        WEEK,
        [("a", "b")],
        "groups",
        [
            "the first thing goes red",
            "the second thing goes red",
        ],
    ),
]


SUITES = {
    "open": [sys.executable, str(HERE / "test_phase1.py"), "open"],
    "locked": [sys.executable, str(HERE / "test_phase1.py"), "locked"],
    "groups": [sys.executable, str(HERE / "test_groups.py")],
}
'''

RUN_ALL = '''
def main():
    results = []
    results.append(run("UNIT", ["node", "--test", "tests/units.test.mjs"]))
    results.append(run("INTEGRATION", [sys.executable, "tests/test_groups.py"]))
'''

SUITE_WITH_CHECKS = '''
def run(base):
    check("a pick after the lock is refused", True)
    check("something else entirely", True)
'''


def scratch():
    d = pathlib.Path(tempfile.mkdtemp(prefix="bulletproof-selftest-"))
    (d / "tests").mkdir()
    (d / "tests" / "harness.py").write_text("# stand-in for the real harness\n")
    (d / "tests" / "mutation_check.py").write_text(GOOD_MUTATIONS)
    (d / "tests" / "run_all.py").write_text(RUN_ALL)
    (d / "tests" / "test_phase1.py").write_text(SUITE_WITH_CHECKS)
    (d / "tests" / "test_groups.py").write_text(
        'def run(base):\n    check("the first thing goes red", True)\n')
    return d


def run_script(args, cwd):
    r = subprocess.run([sys.executable, str(RUN)] + args,
                       capture_output=True, text=True, cwd=str(cwd))
    return r.returncode, r.stdout + r.stderr


def main():
    print("\n-- the parsers read structure, not patterns --")

    files = B.suite_files(GOOD_MUTATIONS)
    check("a suite key maps to the file it runs",
          files.get("groups") == "test_groups.py", str(files))
    check("two keys can point at ONE file, as phase 1's two clocks do",
          files.get("open") == "test_phase1.py" and files.get("locked") == "test_phase1.py",
          str(files))

    exp = dict(B.mutation_expectations(GOOD_MUTATIONS))
    check("a single inline expectation is read",
          exp.get("open") == {"a pick after the lock is refused"}, str(exp.get("open")))
    check("expectations spread over several lines are read",
          exp.get("groups") == {"the first thing goes red", "the second thing goes red"},
          str(exp.get("groups")))
    # MUST-FAIL SHAPE: the label must never be mistaken for an expectation. The first version of
    # this parser did exactly that and reported four false problems out of nine real suites.
    check("MUST NOT read the mutation's own label as an expectation",
          "the lock never refuses" not in exp.get("open", set())
          and "two names on separate lines" not in exp.get("groups", set()),
          "the label leaked into the expectations")

    print("\n-- an f-string check name is matched as a template --")
    emitted = {"plain check", "{kind}: offers exactly {expected}"}
    check("an exact name is covered", B.covers(emitted, "plain check"))
    check("a runtime name matches its f-string template", B.covers(emitted, "picks: offers exactly 3"))
    check("MUST NOT: a name the template cannot produce is covered",
          not B.covers(emitted, "picks: offers at most 3"), "a partial match counted")
    check("MUST NOT: an unrelated name is covered", not B.covers(emitted, "something else"))

    print("\n-- verdict parsing --")

    d, m, s = B.parse_mutation_output(
        "  DETECTED      a real one\n"
        "  NOT DETECTED  an uncovered guard  -> suite still passed (exit 0)\n"
        "  NOT DETECTED  a moved anchor  -> a mutation target no longer exists in the source\n")
    check("a detected mutation is counted as detected", d == ["a real one"], str(d))
    check("an uncovered guard is counted as uncovered", len(m) == 1, str(m))
    check("a moved anchor is counted as STALE, not as a hole", len(s) == 1, str(s))

    print("\n-- the commands, on a scratch project --")

    d1 = scratch()
    rc, out = run_script(["scaffold", "newthing", "--tests", "tests"], d1)
    check("scaffold writes a suite", rc == 0 and (d1 / "tests" / "test_newthing.py").exists(),
          out.strip()[-200:])
    check("and it lands full of GAP markers, not a finished test",
          "[GAP:" in (d1 / "tests" / "test_newthing.py").read_text(),
          "the scaffold has no gaps to fill")

    # MUST-FAIL: scaffolding over an existing suite.
    rc, out = run_script(["scaffold", "newthing", "--tests", "tests"], d1)
    check("MUST FAIL: scaffold refuses to write over an existing suite",
          rc == 1 and "already exists" in out, f"rc={rc}: {out.strip()[-200:]}")

    rc, out = run_script(["register", "newthing", "--tests", "tests"], d1)
    check("register wires the suite into both files", rc == 0, out.strip()[-200:])
    txt = (d1 / "tests" / "run_all.py").read_text()
    mut = (d1 / "tests" / "mutation_check.py").read_text()
    check("run_all.py now runs it", "tests/test_newthing.py" in txt, "not in run_all.py")
    check("SUITES now has it", '"newthing":' in mut, "not in SUITES")

    rc, out = run_script(["register", "newthing", "--tests", "tests"], d1)
    check("register is idempotent", rc == 0 and txt.count("test_newthing.py") == 1
          and (d1 / "tests" / "run_all.py").read_text().count("test_newthing.py") == 1,
          "a second run duplicated the row")

    # MUST-FAIL: the audit has to refuse a suite that no mutation is pointed at. `newthing` was
    # just registered and has no mutation, which is exactly the state that means "never watched
    # go red".
    rc, out = run_script(["audit", "newthing", "--tests", "tests"], d1)
    check("MUST FAIL: audit refuses a suite with no mutation behind it",
          rc == 1 and "never been watched go red" in out, f"rc={rc}: {out.strip()[-300:]}")

    rc, out = run_script(["audit", "groups", "--tests", "tests"], d1)
    check("POSITIVE CONTROL: a suite that IS covered passes the audit",
          rc == 0, f"rc={rc}: {out.strip()[-300:]}")

    # MUST-FAIL: a suite registered in the mutation check but missing from the runner is a suite
    # a full run silently skips.
    d2 = scratch()
    (d2 / "tests" / "run_all.py").write_text(
        RUN_ALL.replace('results.append(run("INTEGRATION", [sys.executable, '
                        '"tests/test_groups.py"]))\n', ""))
    rc, out = run_script(["audit", "groups", "--tests", "tests"], d2)
    check("MUST FAIL: audit refuses a suite the runner does not run",
          rc == 1 and "run_all.py" in out, f"rc={rc}: {out.strip()[-300:]}")

    # MUST-FAIL: no harness to follow means the scaffold would be a guess.
    d3 = pathlib.Path(tempfile.mkdtemp(prefix="bulletproof-selftest-nohar-"))
    (d3 / "tests").mkdir()
    rc, out = run_script(["scaffold", "x", "--tests", "tests"], d3)
    check("MUST FAIL: scaffold refuses where there is no harness to follow",
          rc == 1 and "harness.py" in out, f"rc={rc}: {out.strip()[-200:]}")

    # MUST-FAIL: a tests directory that is not there at all.
    rc, out = run_script(["audit", "--tests", "nope"], d3)
    check("MUST FAIL: a missing tests directory exits 2, not 0",
          rc == 2, f"rc={rc}: {out.strip()[-200:]}")

    total = len(PASSED) + len(FAILED)
    print(f"\n{'=' * 62}\nbulletproof selftest: {len(PASSED)}/{total} passed")
    if FAILED:
        for name, detail in FAILED:
            print(f"  - {name}{('  -> ' + detail) if detail else ''}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
