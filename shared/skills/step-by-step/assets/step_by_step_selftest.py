#!/usr/bin/env python3
"""Self-test for step_by_step_run.py.

PART A  must-pass and must-block cases, each asserting a specific exit code, driven
        through REAL temporary git repositories with real commits. No mocks: the
        manifest's whole job is to read git, and a fake git tests the fake.
PART B  non-vacuity. Every must-block case is replayed against a build with the
        coverage check removed. Each must turn green there. One that stays red was
        blocking for some unrelated reason and proves nothing.

Run:  python3 step_by_step_selftest.py     (0 = all clear, 1 = a case is wrong)
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

OK, INCOMPLETE, CANTRUN = 0, 1, 2
NAMES = {0: "OK", 1: "INCOMPLETE", 2: "CANTRUN"}


def sh(*args, cwd=None):
    subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def make_repo(root: Path, name: str, commits: int, untracked: int = 0) -> Path:
    r = root / name
    r.mkdir(parents=True)
    sh("git", "init", "-q", "-b", "main", cwd=r)
    sh("git", "config", "user.email", "t@t", cwd=r)
    sh("git", "config", "user.name", "t", cwd=r)
    for i in range(commits):
        (r / f"f{i}.txt").write_text(f"{i}\n")
        sh("git", "add", f"f{i}.txt", cwd=r)
        sh("git", "commit", "-q", "-m", f"commit {i} in {name}", cwd=r)
    for i in range(untracked):
        (r / f"new{i}.txt").write_text("x\n")
    return r


def run(mod, argv):
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
            return mod.main(argv), buf.getvalue()
    except SystemExit as exc:
        return (exc.code if isinstance(exc.code, int) else CANTRUN), buf.getvalue()


def fresh(state: Path):
    import importlib
    import step_by_step_run
    os.environ["STEP_BY_STEP_STATE_FILE"] = str(state)
    state.unlink(missing_ok=True)
    return importlib.reload(step_by_step_run)


def scenarios():
    """(name, fn(mod, root) -> exit code, expected, must_block)"""

    def s_manifest(mod, root):
        r = make_repo(root, "alpha", 3)
        return run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])[0]

    def s_two_repos(mod, root):
        a = make_repo(root, "alpha", 2)
        b = make_repo(root, "beta", 2)
        rc, out = run(mod, ["manifest", "--since", "2000-01-01",
                            "--repo", str(a), "--repo", str(b)])
        return rc if "4 item(s)" in out else 99

    def s_untracked_counted(mod, root):
        r = make_repo(root, "alpha", 1, untracked=2)
        rc, out = run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return rc if "3 item(s)" in out else 99

    def s_cover_all_then_verify(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        run(mod, ["cover", "1", "2"])
        return run(mod, ["verify"])[0]

    def s_show_one(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return run(mod, ["show", "1"])[0]

    def s_verify_uncovered(mod, root):
        r = make_repo(root, "alpha", 3)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        run(mod, ["cover", "1"])
        return run(mod, ["verify"])[0]

    def s_verify_none_covered(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return run(mod, ["verify"])[0]

    def s_status_uncovered(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return run(mod, ["status"])[0]

    def s_not_a_repo(mod, root):
        d = root / "plain"
        d.mkdir()
        return run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(d)])[0]

    def s_empty_window(mod, root):
        r = make_repo(root, "alpha", 2)
        return run(mod, ["manifest", "--since", "2099-01-01", "--repo", str(r)])[0]

    def s_bad_since(mod, root):
        r = make_repo(root, "alpha", 2)
        return run(mod, ["manifest", "--since", "not-a-date", "--repo", str(r)])[0]

    def s_no_manifest_verify(mod, root):
        return run(mod, ["verify"])[0]

    def s_no_manifest_cover(mod, root):
        return run(mod, ["cover", "1"])[0]

    def s_cover_out_of_range(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return run(mod, ["cover", "9"])[0]

    def s_show_out_of_range(mod, root):
        r = make_repo(root, "alpha", 2)
        run(mod, ["manifest", "--since", "2000-01-01", "--repo", str(r)])
        return run(mod, ["show", "9"])[0]

    # The fourth field names WHICH guard the case tests, and Part B removes exactly
    # that one. A blanket "remove the coverage gate" pass reported two cases vacuous
    # when they were in fact testing the range check and blocking correctly. Never
    # assert non-vacuity against a composite: a must-block case that survives may be
    # blocking for someone else's reason, which is the trap /bulletproof names.
    return [
        ("a manifest over one repo",            s_manifest,              OK,         None),
        ("two repos are merged into one list",  s_two_repos,             OK,         None),
        ("untracked files are counted too",     s_untracked_counted,     OK,         None),
        ("cover everything, then verify",       s_cover_all_then_verify, OK,         None),
        ("show one item",                       s_show_one,              OK,         None),

        ("verify REFUSES with one left",        s_verify_uncovered,      INCOMPLETE, "coverage"),
        ("verify REFUSES with none covered",    s_verify_none_covered,   INCOMPLETE, "coverage"),
        ("status reports incomplete",           s_status_uncovered,      INCOMPLETE, "coverage"),
        ("a directory that is not a repo",      s_not_a_repo,            CANTRUN,    "is_repo"),
        ("an empty window is not a pass",       s_empty_window,          CANTRUN,    "empty"),
        ("an unparseable --since",              s_bad_since,             CANTRUN,    "since"),
        ("verify with no manifest",             s_no_manifest_verify,    CANTRUN,    "no_manifest"),
        ("cover with no manifest",              s_no_manifest_cover,     CANTRUN,    "no_manifest"),
        ("cover an item that does not exist",   s_cover_out_of_range,    CANTRUN,    "range"),
        ("show an item that does not exist",    s_show_out_of_range,     CANTRUN,    "range"),
    ]


def stub_items(n=9, covered=True):
    return [{"n": i, "kind": "commit", "repo": "r", "ref": "0", "when": "",
             "what": "w", "covered": covered} for i in range(1, n + 1)]


def remove_guard(mod, guard: str):
    """Neuter exactly ONE guard, named by the case that tests it.

    Removing a blanket 'coverage' gate reported the two range cases vacuous when they
    were blocking correctly on a different check. Per-guard removal asks each case the
    only question that means anything: does IT fire because of the guard IT names?
    """
    if guard == "coverage":
        real = mod.load
        mod.load = lambda: (lambda st: ([it.update(covered=True) for it in st["items"]], st)[1])(
            real() or {"since": "x", "repos": [], "items": stub_items()})
    elif guard == "is_repo":
        # DEFENCE IN DEPTH, so both layers come out. Stubbing is_repo alone leaves the
        # case blocking, because `git log` then fails inside a plain directory and
        # collect() raises. Removing one of two independent guards proves nothing
        # (/bulletproof, "defence in depth needs both gates removed"), so the second
        # is removed too and the case is required to go green.
        mod.is_repo = lambda p: True
        mod.collect = lambda repo, since, paths=None: [
            {"kind": "commit", "repo": repo.name, "ref": "0", "when": "",
             "what": "invented, because neither guard is present"}]
    elif guard == "empty":
        real = mod.collect
        mod.collect = lambda repo, since, paths=None: real(repo, since, paths) or [
            {"kind": "commit", "repo": repo.name, "ref": "0", "when": "",
             "what": "invented so the empty window is not caught"}]
    elif guard == "since":
        mod.valid_since = lambda text: True
    elif guard == "no_manifest":
        mod.load = lambda: {"since": "x", "repos": [], "items": stub_items()}
    elif guard == "range":
        # Accept any index by making every index exist.
        real = mod.load
        mod.load = lambda: (real() or {"since": "x", "repos": [], "items": []}) | {
            "items": stub_items(20, covered=True)}
    else:
        raise AssertionError(f"no removal defined for guard {guard!r}")
    return mod


def main() -> int:
    passed = failed = 0
    print("PART A -- behaviour, against real temporary git repositories")
    for name, fn, expected, _blk in scenarios():
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mod = fresh(root / "state.json")
            got = fn(mod, root)
        ok = got == expected
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
        print(f"  {'PASS' if ok else 'FAIL'}  {name}"
              + ("" if ok else f"   expected {NAMES.get(expected, expected)}, "
                               f"got {NAMES.get(got, got)}"))

    print("\nPART B -- non-vacuity (each must-block case replayed with ITS OWN guard removed)")
    vacuous = 0
    blocks = [c for c in scenarios() if c[3]]
    for name, fn, _expected, guard in blocks:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            mod = remove_guard(fresh(root / "state.json"), guard)
            got = fn(mod, root)
        if got == OK:
            print(f"  ok       [{guard:<11}] {name}")
        else:
            vacuous += 1
            print(f"  VACUOUS  [{guard:<11}] {name}   still blocks "
                  f"({NAMES.get(got, got)}) without its guard")

    total = passed + failed
    print(f"\n{passed}/{total} behaviour cases ({len(blocks)} must-block)")
    print(f"{len(blocks) - vacuous}/{len(blocks)} must-block cases proven non-vacuous")
    if failed or vacuous:
        return 1
    print("all clear")
    return 0


if __name__ == "__main__":
    sys.exit(main())
