#!/usr/bin/env python3
"""check_coa_evidence_paths.py — before a /coa council convenes, check that every path its brief hands a seat exists.

WHY IT EXISTS
  A seat cannot check the brief it is given. Handed a path that does not resolve (relative to the wrong folder,
  one letter off, a file renamed since), it searches, finds nothing, and reports the absence as a finding: "the
  source does not exist", in a session where the source was there all along. Worse, one seat's false finding can
  make its whole assessment look out of line with the others, and its real findings get discounted with it. The
  brief was the defect, so the check runs on the brief.

  /coa runs it on the evidence paths in a brief before it starts the seats (Step 0b in shared/commands/coa.md).

WHAT IT DOES
  For each path: strip surrounding spaces, expand a leading ~, join a relative path to the base folder
  ($COA_EVIDENCE_BASE if set, else the working directory), drop trailing slashes, and report it as a file, a dir
  or MISSING. A trailing slash is not required for a folder.

USAGE
  python3 scripts/check_coa_evidence_paths.py <path> [<path> ...]
  python3 scripts/check_coa_evidence_paths.py --stdin          # one path per line; blank lines are skipped
  python3 scripts/check_coa_evidence_paths.py --self-test      # in a clone: also compares with tests/golden/
EXIT  0 every path resolves · 1 at least one does not; the brief is not ready to send · 2 no paths given

A port of a Julia original; its verdicts on a fixed tree are recorded in tests/golden/check_coa_evidence_paths.json,
and the self-test requires the same verdict for every one.
Mutation proof: scripts/check_coa_evidence_paths_mutations.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

GOLDEN = Path(__file__).resolve().parents[1] / "tests" / "golden" / "check_coa_evidence_paths.json"


def checkpath(given: str, base: str) -> tuple[str, str, str]:
    """(given, resolved, kind) with kind 'file', 'dir' or 'MISSING'."""
    raw = given.strip()
    expanded = os.path.expanduser("~") + raw[1:] if raw.startswith("~") else raw
    resolved = expanded if os.path.isabs(expanded) else os.path.join(base, expanded)
    resolved = resolved.rstrip("/") or "/"
    kind = "dir" if os.path.isdir(resolved) else "file" if os.path.isfile(resolved) else "MISSING"
    return raw, resolved, kind


def report(checks) -> int:
    missing = [c for c in checks if c[2] == "MISSING"]
    print(" /coa evidence-path check: do the paths in the brief resolve?")
    for given, resolved, kind in checks:
        print(f"  {'ok ' if kind != 'MISSING' else 'NO '} [{kind:<7}] {given}")
        if kind == "MISSING":
            print(f"        looked at: {resolved}")
    print()
    if not missing:
        print(f"  All {len(checks)} evidence path(s) resolve. The brief can go to the seats.")
        return 0
    print(f"  {len(missing)} of {len(checks)} evidence path(s) DO NOT RESOLVE.\n")
    print("  Do not start the seats with these in the brief. A seat handed a path that does not resolve cannot tell")
    print("  'absent' from 'pointed at the wrong place', and reports the absence as a finding. Fix the path, or say")
    print("  in the brief that the artifact is out of that seat's reach on purpose, and why.")
    return 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        return self_test()
    base = os.environ.get("COA_EVIDENCE_BASE") or os.getcwd()
    if "--stdin" in args:
        paths = [ln.strip() for ln in sys.stdin.read().splitlines() if ln.strip()]
    else:
        paths = [a for a in args if not a.startswith("--")]
    if not paths:
        print("usage: python3 check_coa_evidence_paths.py <path>... | --stdin | --self-test", file=sys.stderr)
        return 2
    return report([checkpath(p, base) for p in paths])


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def quiet(fn, *a, stdin_text=None):
        real_out, real_err, real_in = sys.stdout, sys.stderr, sys.stdin
        with open(os.devnull, "w") as null:
            sys.stdout = sys.stderr = null
            if stdin_text is not None:
                sys.stdin = __import__("io").StringIO(stdin_text)
            try:
                return fn(*a)
            finally:
                sys.stdout, sys.stderr, sys.stdin = real_out, real_err, real_in

    if GOLDEN.is_file():
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        base = tempfile.mkdtemp(prefix="coa_golden_")
        for f in golden["tree"]["files"]:
            p = Path(base, f)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("x")
        for d in golden["tree"]["dirs"]:
            Path(base, d).mkdir(parents=True, exist_ok=True)
        for case in golden["cases"]:
            given = case["given"].replace("<BASE>", base)
            check(f"same verdict as the Julia original: {case['given']!r} -> {case['kind']}",
                  checkpath(given, base)[2] == case["kind"])
    else:
        check(f"the golden file is present ({GOLDEN})", False)

    base = tempfile.mkdtemp(prefix="coa_paths_")
    Path(base, "brief.md").write_text("x")
    old = os.environ.get("COA_EVIDENCE_BASE")
    os.environ["COA_EVIDENCE_BASE"] = base
    try:
        check("every path resolves: exit 0", quiet(main, ["brief.md"]) == 0)
        check("one missing among two: exit 1", quiet(main, ["brief.md", "gone.pdf"]) == 1)
        check("no paths: exit 2, never a pass", quiet(main, []) == 2)
        check("--stdin reads one path per line", quiet(main, ["--stdin"], stdin_text="brief.md\ngone.pdf\n") == 1)
        real = sys.stdout
        buf = __import__("io").StringIO()
        sys.stdout, sys.stdin = buf, __import__("io").StringIO("brief.md\n\n   \n")
        try:
            code = main(["--stdin"])
        finally:
            sys.stdout, sys.stdin = real, sys.__stdin__
        check("--stdin skips blank lines", code == 0 and "All 1 evidence path(s)" in buf.getvalue())
        buf = __import__("io").StringIO()
        sys.stdout = buf
        try:
            main(["gone.pdf"])
        finally:
            sys.stdout = real
        check("a missing path says where it looked", f"looked at: {os.path.join(base, 'gone.pdf')}" in buf.getvalue())
    finally:
        if old is None:
            os.environ.pop("COA_EVIDENCE_BASE", None)
        else:
            os.environ["COA_EVIDENCE_BASE"] = old
    home = tempfile.mkdtemp(prefix="coa_home_")
    Path(home, "notes.md").write_text("x")
    old_home = os.environ.get("HOME")
    os.environ["HOME"] = home
    try:
        check("a leading ~ is the home folder", checkpath("~/notes.md", "/nonexistent")[2] == "file")
    finally:
        os.environ["HOME"] = old_home or ""
    print(f"check_coa_evidence_paths self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
