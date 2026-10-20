#!/usr/bin/env python3
"""Gate: nothing of value is left living only in a session's scratchpad.

WHY IT EXISTS
  Claude Code gives each session a scratchpad folder, and it disappears with the session. A finding, a rebuilt
  PDF or a working script written there looks exactly like a saved file while the session is alive. The loss
  happens later, when nobody is looking.

WHAT IT CHECKS
  Every file in the scratchpad is put in one class:
    KEEP       durable value and NOT in the project: these are the leaks. By extension: .md .py .jl .tex .csv
               .json .bib .pdf .qmd .toml .yaml .yml
    DERIVED    a build artifact the project can rebuild (.aux .log .bbl .pyc … and anything under __pycache__)
    EPHEMERAL  everything else, and any name starting with tmp, scratch, test_ or _tmp
  A KEEP file is "in the project" when a file with the same SHA-256 exists anywhere under the project root:
  same content, any path, any name, because the question is whether the content survives.

LIMITS, STATED
  * It cannot judge whether a file deserves keeping: it flags by extension and a person decides. Over-flagging is
    the intended bias, since a false alarm costs one glance and a miss costs the work.
  * A file saved and then edited in the project is flagged, because the contents differ. A diverged copy is worth
    a look.
  * It does not look inside archives, and it skips .git, node_modules and .venv in both trees.
  * Large files are hashed in full; there is no size cap, because a size cap is a silent skip. Only project files
    whose SIZE equals a candidate's are hashed: two files of different sizes cannot match, so this changes the
    speed, never the answer.
  It reports; it never moves or removes anything.

USAGE   python3 scripts/check_scratchpad_leak.py <scratchpad> [--repo <project root>] [--quiet]
        python3 scripts/check_scratchpad_leak.py --self-test
EXIT    0 clean · 1 a file of value lives only in the scratchpad · 2 a folder is missing
Mutation proof: scripts/check_scratchpad_leak_mutations.py
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

KEEP_EXT = {".md", ".py", ".jl", ".tex", ".csv", ".json", ".bib", ".pdf", ".qmd", ".toml", ".yaml", ".yml"}
DERIVED_EXT = {".aux", ".log", ".out", ".toc", ".bbl", ".blg", ".fls", ".fdb_latexmk", ".synctex", ".gz", ".pyc",
               ".nav", ".snm", ".vrb", ".lof", ".lot", ".idx", ".ilg", ".ind"}
EPHEMERAL_PREFIX = ("tmp", "scratch", "test_", "_tmp")
SKIP_DIRS = {".git", "node_modules", ".venv"}


def sha(path: Path) -> str | None:
    h = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def index_repo(repo: Path, sizes: set[int]) -> set[str]:
    """SHA-256 of every project file whose size equals a candidate's."""
    seen: set[str] = set()
    for dirpath, dirnames, filenames in os.walk(repo):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            try:
                if p.stat().st_size not in sizes:
                    continue
            except OSError:
                continue
            d = sha(p)
            if d:
                seen.add(d)
    return seen


def classify(rel: Path) -> str:
    name, suf = rel.name.lower(), rel.suffix.lower()
    if "__pycache__" in rel.parts or suf in DERIVED_EXT:
        return "DERIVED"
    if name.startswith(EPHEMERAL_PREFIX):
        return "EPHEMERAL"
    return "KEEP" if suf in KEEP_EXT else "EPHEMERAL"


def scan(scratch: Path, repo: Path):
    """(leaks as [(path, size)], already-saved count, derived count, ephemeral count)."""
    candidates, derived, ephemeral = [], 0, 0
    for dirpath, dirnames, filenames in os.walk(scratch):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            kind = classify(p.relative_to(scratch))
            if kind == "DERIVED":
                derived += 1
            elif kind == "EPHEMERAL":
                ephemeral += 1
            else:
                try:
                    candidates.append((p, p.stat().st_size))
                except OSError:
                    continue
    repo_hashes = index_repo(repo, {sz for _, sz in candidates})
    leaks, saved = [], 0
    for p, size in candidates:
        if sha(p) in repo_hashes:
            saved += 1
        else:
            leaks.append((p, size))
    return leaks, saved, derived, ephemeral


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("scratchpad", nargs="?", help="the session scratchpad folder")
    ap.add_argument("--repo", default=".", help="project root to check against (default: the working directory)")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.scratchpad:
        ap.print_usage(sys.stderr)
        return 2
    scratch, repo = Path(args.scratchpad).expanduser().resolve(), Path(args.repo).expanduser().resolve()
    for d in (scratch, repo):
        if not d.is_dir():
            print(f"usage error: not a directory: {d}", file=sys.stderr)
            return 2
    leaks, saved, derived, ephemeral = scan(scratch, repo)
    if not args.quiet or leaks:
        print(f"check_scratchpad_leak: {scratch}")
        print(f"  already in the project: {saved} | build artifacts: {derived} | throwaway: {ephemeral}")
        if leaks:
            print(f"\nONLY IN THE SCRATCHPAD, gone when the session ends ({len(leaks)}, {sum(s for _, s in leaks):,} bytes):")
            for p, size in sorted(leaks, key=lambda x: -x[1]):
                print(f"  {size:>12,}  {p.relative_to(scratch)}")
            print("\n  Decide for each: copy it into the project, or drop it on purpose. Nothing was moved or removed.")
        else:
            print("  clean: nothing of durable value exists only in the scratchpad")
    return 1 if leaks else 0


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def pair(files_s=(), files_r=()):
        root = Path(tempfile.mkdtemp(prefix="leak_"))
        s, r = root / "s", root / "r"
        for base, files in ((s, files_s), (r, files_r)):
            base.mkdir()
            for rel, data in files:
                (base / rel).parent.mkdir(parents=True, exist_ok=True)
                (base / rel).write_bytes(data if isinstance(data, bytes) else data.encode())
        return s, r

    def code(s, r):
        with open(os.devnull, "w") as null:
            real, sys.stdout = sys.stdout, null
            try:
                return main([str(s), "--repo", str(r), "--quiet"])
            finally:
                sys.stdout = real

    check("an unsaved .md is a leak", code(*pair([("FINDING.md", "a real finding\n")])) == 1)
    check("content saved under another name is not a leak",
          code(*pair([("FINDING.md", "a real finding\n")], [("renamed.md", "a real finding\n")])) == 0)
    check("the same name with different content is a leak",
          code(*pair([("notes.md", "version two\n")], [("notes.md", "version one\n")])) == 1)
    check("content saved deep in the project is found",
          code(*pair([("r.csv", "a,b\n")], [("data/2026/q3/r_final.csv", "a,b\n")])) == 0)
    check("an unsaved .py is a leak", code(*pair([("compare.py", "import sys\n")])) == 1)
    check("an unsaved .pdf is a leak", code(*pair([("paper.pdf", b"%PDF-1.4\n")])) == 1)
    check("a leak nested in subfolders is found", code(*pair([("build/deep/RESULT.md", "buried\n")])) == 1)
    check("build artifacts alone are clean", code(*pair([("main.aux", "x\n"), ("main.log", "x\n")])) == 0)
    check("throwaway names are clean", code(*pair([("tmp_probe.py", "x\n"), ("test_thing.py", "x\n")])) == 0)
    check("anything under __pycache__ is derived", code(*pair([("__pycache__/notes.md", "x\n")])) == 0)
    check("anything under .git is skipped", code(*pair([(".git/info/notes.md", "x\n")])) == 0)
    check("a .md under the project's .git does not count as saved",
          code(*pair([("FINDING.md", "a real finding\n")], [(".git/FINDING.md", "a real finding\n")])) == 1)
    s, r = pair([("main.aux", "x\n"), ("tmp_a.py", "x\n"), ("keep.md", "k\n")], [("keep.md", "k\n")])
    leaks, saved, derived, ephemeral = scan(s, r)
    check("the counts are reported (1 saved, 1 derived, 1 throwaway)", (len(leaks), saved, derived, ephemeral) == (0, 1, 1, 1))
    root = Path(tempfile.mkdtemp(prefix="leak_missing_"))
    check("a missing scratchpad is exit 2, never a pass", code(root / "nope", root) == 2)
    check("a missing project is exit 2, never a pass", code(root, root / "nope") == 2)
    print(f"check_scratchpad_leak self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
