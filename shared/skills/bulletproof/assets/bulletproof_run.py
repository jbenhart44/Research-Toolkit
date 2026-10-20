#!/usr/bin/env python3
"""The deterministic half of /bulletproof: scaffold a suite, register it, and audit the wiring.

Built from applying this procedure to eight features of one web application in a row.

Four commands, each doing one thing that has an exactly right answer:

    scaffold <name> [--tests DIR]   write tests/test_<name>.py from the project's own harness
    register <name> [--tests DIR]   add it to run_all.py and mutation_check.py's SUITES
    audit    [<name>] [--tests DIR] refuse if a suite is unregistered or has no mutation
    check    [filter]  [--tests DIR] run the mutation set; refuse on NOT DETECTED or STALE

Everything a person has to DECIDE stays in SKILL.md: which level to test at, what defect to
inject, and how to scope an assertion. This file only does the parts where deciding would be a
waste of a person.

Exit codes: 0 fine, 1 something is wrong and named, 2 the script could not run at all.
"""

import argparse
import ast
import pathlib
import re
import subprocess
import sys

TEMPLATE = '''#!/usr/bin/env python3
"""{title}

Run: python3 tests/test_{name}.py

WHAT THIS SUITE IS FOR
    [GAP: one paragraph - what behaviour is pinned here, and what would break if it were wrong.
     Write it before the code exists, so it is a specification and not a description.]

WHY THESE ASSERTIONS AND NOT LOOSER ONES
    [GAP: name the element each check reads. A whole-page substring is not a measurement: on
     this project a page-wide logo count was silently satisfied by a side panel, and a
     "Week by week" match was satisfied by a nav button. Say what you scoped to and why.]
"""

import pathlib
import re
import shutil
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from harness import (  # noqa: E402
    Client, SITE, check, free_port, refuse_if_mutating, start_server, stop, summary,
)


def run(base):
    print("\\n-- [GAP: name the first behaviour] --")

    c = Client(base)
    c.join("{cap}Tester", "{name}pass123")

    # POSITIVE CONTROL FIRST. "It refused" is only evidence if something that should work
    # demonstrably does; otherwise a completely broken path reads as a working guard.
    status, body, _ = c.get("/")
    check("the server is answering at all", status in (200, 303), f"got {{status}}")

    # [GAP: the real checks. Each one names the element it reads.]


def main():
    if refuse_if_mutating():
        return 2
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="{name}-"))
    proc = None
    try:
        persist = tmp / "state"
        persist.mkdir(parents=True)
        proc, base = start_server(free_port(), persist)
        run(base)
    finally:
        if proc:
            stop(proc)
        shutil.rmtree(tmp, ignore_errors=True)
    return summary("{title}")


if __name__ == "__main__":
    sys.exit(main())
'''


def die(msg, code=1):
    print(f"REFUSED: {msg}", file=sys.stderr)
    sys.exit(code)


def tests_dir(arg):
    d = pathlib.Path(arg).resolve()
    if not d.is_dir():
        die(f"{d} is not a directory", 2)
    return d


def scaffold(name, tests):
    target = tests / f"test_{name}.py"
    if target.exists():
        die(f"{target.name} already exists - /bulletproof never writes over a suite")
    if not (tests / "harness.py").exists():
        die(f"no harness.py in {tests} - this project's suites do not follow that shape, so "
            f"write the first one by hand and register it with `register`")
    target.write_text(TEMPLATE.format(
        name=name, cap=name[:1].upper() + name[1:], title=name.replace("_", " ").capitalize()))
    print(f"wrote {target}")
    print("  it is full of [GAP: ] markers on purpose. Fill them in BEFORE the code exists,")
    print("  then watch the suite go red. A suite written after the code tests the code you")
    print("  happened to write, not the behaviour you meant.")
    return 0


def register(name, tests):
    """Add the suite to the project's runner and to the mutation check. Idempotent."""
    changed = []

    runner = tests / "run_all.py"
    if runner.exists():
        t = runner.read_text()
        if f"test_{name}.py" in t:
            print(f"run_all.py: already runs test_{name}.py")
        else:
            anchor = re.search(r"^(\s*)results\.append\(run\(", t, re.M)
            if not anchor:
                die("run_all.py has no results.append(run( line to anchor on")
            indent = anchor.group(1)
            block = (f'{indent}results.append(run("SUITE  ({name})",\n'
                     f'{indent}                   [sys.executable, "tests/test_{name}.py"]))\n')
            t = t[:anchor.start()] + block + t[anchor.start():]
            runner.write_text(t)
            changed.append("run_all.py")
    else:
        print(f"no run_all.py in {tests} - skipped")

    mut = tests / "mutation_check.py"
    if mut.exists():
        t = mut.read_text()
        if f'"{name}":' in t:
            print(f"mutation_check.py: SUITES already has {name!r}")
        else:
            m = re.search(r"^SUITES = \{\n", t, re.M)
            if not m:
                die("mutation_check.py has no SUITES dict to add to")
            row = f'    "{name}": [sys.executable, str(HERE / "test_{name}.py")],\n'
            t = t[:m.end()] + row + t[m.end():]
            mut.write_text(t)
            changed.append("mutation_check.py")
    else:
        print(f"no mutation_check.py in {tests} - skipped")

    print("registered in: " + (", ".join(changed) if changed else "nothing (already there)"))
    return 0


def _strings(node):
    """Every string constant under an AST node."""
    return [n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]


def suite_files(mut_text):
    """Suite key -> the test file it runs.

    Read with `ast`, not a regex. The first version of this used pattern matching and reported
    four false problems out of nine suites on its first real run: it mistook a mutation's LABEL
    for its must-fail list, and it could not see that test_phase1.py is registered under two
    keys ("open" and "locked") rather than under its own name. A regex guesses at structure that
    the parser already knows.
    """
    out = {}
    for node in ast.walk(ast.parse(mut_text)):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "SUITES" for t in node.targets):
            for key, val in zip(node.value.keys, node.value.values):
                if not isinstance(key, ast.Constant):
                    continue
                files = [s for s in _strings(val) if s.startswith("test_") and s.endswith(".py")]
                out[key.value] = files[0] if files else None
    return out


def check_names(suite_text):
    """Every check name a suite emits, read out of its check("...") calls.

    An f-string name comes back as its TEMPLATE, placeholders and all - so
    `check(f"{kind}: offers exactly {expected}", ...)` yields the literal
    `{kind}: offers exactly {expected}`, which never equals the runtime name a mutation has to
    put in its expectation list. Use `covers()` to compare, not `==`.
    """
    return set(re.findall(r'check\(\s*f?"([^"]+)"', suite_text))


def covers(emitted, expected):
    """Does a suite that emits `emitted` produce the check name `expected`?

    Exact match first. Failing that, treat any emitted name containing a {placeholder} as an
    f-string template and match the expectation against it with the placeholders wild.

    WHY THIS EXISTS (2026-09-08). The audit compared expectations to statically-extracted names
    with `&`. A suite whose checks are f-strings therefore read as UNCOVERED even when a
    mutation named its runtime output exactly and reported DETECTED - the guard was real and
    the audit said it was not. It cost two rounds of adding static-named checks purely to
    satisfy the audit before the cause was found. A tool that reports a working guard as
    missing trains people to ignore it, which is the same failure as a gate pointed at the
    wrong artifact.
    """
    if expected in emitted:
        return True
    for name in emitted:
        if "{" not in name:
            continue
        pattern = "".join(
            ".*" if part.startswith("{") else re.escape(part)
            for part in re.split(r"(\{[^{}]*\})", name) if part)
        if re.fullmatch(pattern, expected):
            return True
    return False


def mutation_expectations(mut_text):
    """(suite, {check names that must go red}) for every mutation, read positionally.

    A mutation entry is (label, file, edits, suite, must_fail[, cross...]), so the suite is
    element 3 and the expectations element 4. Positional and exact.
    """
    out = []
    for node in ast.walk(ast.parse(mut_text)):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", None) == "MUTATIONS" for t in node.targets):
            for el in getattr(node.value, "elts", []):
                if not isinstance(el, ast.Tuple) or len(el.elts) < 5:
                    continue
                which, must = el.elts[3], el.elts[4]
                if not isinstance(which, ast.Constant):
                    continue
                out.append((which.value, set(_strings(must))))
    return out


def audit(name, tests):
    """Refuse if a suite is not wired in, or if no mutation requires any of its checks.

    This is the rule with teeth: a new suite with no mutation pointed at it has never been
    watched go red, so nothing yet says it would notice a defect.
    """
    mut = tests / "mutation_check.py"
    runner = tests / "run_all.py"
    if not mut.exists():
        die(f"no mutation_check.py in {tests}, so there is nothing to audit against", 2)
    mut_text = mut.read_text()
    keys_for = {}
    for key, f in suite_files(mut_text).items():
        if f:
            keys_for.setdefault(f, []).append(key)
    targets = [name] if name else sorted(
        p.stem[len("test_"):] for p in tests.glob("test_*.py"))

    problems = []
    for n in targets:
        suite = tests / f"test_{n}.py"
        if not suite.exists():
            problems.append(f"{n}: no tests/test_{n}.py")
            continue
        if runner.exists() and f"test_{n}.py" not in runner.read_text():
            problems.append(f"{n}: not registered in run_all.py, so a full run skips it")
        # A suite file can be registered under a name of its own, or under several keys - the
        # phase 1 suite runs as "open" and "locked", one per clock. Match on the FILE.
        keys = keys_for.get(f"test_{n}.py", [])
        if not keys:
            problems.append(f"{n}: not in mutation_check.py SUITES, so no mutation can use it")
            continue
        mine = check_names(suite.read_text())
        covered = any(
            w in keys and (not names or any(covers(mine, n) for n in names))
            for w, names in mutation_expectations(mut_text))
        if not covered:
            problems.append(
                f"{n}: no mutation names any of its {len(mine)} checks - it has never been "
                f"watched go red")

    for p in problems:
        print(f"  PROBLEM  {p}")
    print(f"audited {len(targets)} suite(s): {len(problems)} problem(s)")
    return 1 if problems else 0


def parse_mutation_output(text):
    """Pull the verdicts out of a mutation run. Kept pure so it can be tested on a fixture."""
    detected, missed, stale = [], [], []
    for line in text.splitlines():
        m = re.match(r"\s+(DETECTED|NOT DETECTED)\s+(.*)", line)
        if not m:
            continue
        label = m.group(2).strip()
        if m.group(1) == "DETECTED":
            detected.append(label)
        elif "no longer exists" in label or "STALE" in label:
            stale.append(label)
        else:
            missed.append(label)
    return detected, missed, stale


def check_cmd(flt, tests):
    mut = tests / "mutation_check.py"
    if not mut.exists():
        die(f"no mutation_check.py in {tests}", 2)
    cmd = [sys.executable, str(mut)] + ([flt] if flt else [])
    print("running: " + " ".join(cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=str(tests.parent))
    sys.stdout.write(r.stdout[-4000:])
    detected, missed, stale = parse_mutation_output(r.stdout)
    print(f"\nDETECTED {len(detected)} | NOT DETECTED {len(missed)} | STALE {len(stale)}")
    for s in stale:
        print(f"  STALE   {s}")
        print("          A MOVED ANCHOR IS NOT A HOLE. Re-point it at the file the code lives")
        print("          in now, then run again.")
    for m in missed:
        print(f"  UNCOVERED  {m}")
        print("             Either the test is decorative, or the assertion cannot fail.")
    return 1 if (missed or stale) else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="scaffold, register and audit a test suite")
    ap.add_argument("command", choices=["scaffold", "register", "audit", "check"])
    ap.add_argument("name", nargs="?", default=None)
    ap.add_argument("--tests", default="tests", help="the project's tests directory")
    a = ap.parse_args(argv)
    t = tests_dir(a.tests)

    if a.command in ("scaffold", "register") and not a.name:
        die(f"{a.command} needs a suite name", 2)
    if a.command == "scaffold":
        return scaffold(a.name, t)
    if a.command == "register":
        return register(a.name, t)
    if a.command == "audit":
        return audit(a.name, t)
    return check_cmd(a.name, t)


if __name__ == "__main__":
    sys.exit(main())
