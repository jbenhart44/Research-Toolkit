#!/usr/bin/env python3
"""Gate: every count and version a reader sees matches the tree it describes.

The v1.x pages said 11, 13, 14 and 15 commands at the same time, because each number was typed by
hand. This check derives the truth and compares every claim against it.

  command count     = len(SHARED_COMMANDS) + len(STUDENT_ONLY) in install.sh, + 1 for /pcv
  instructor count  = len(SHARED_COMMANDS) + 1 (what `install.sh --minimal` installs); the
                      files in SUBSET_FILES are held to this count instead
  version           = the VERSION file

Claims it reads, in every page of the tree (.md, .txt, .cff; found by walking the tree, so a new
page is checked the day it is added) plus any extra file passed on the command line (for example
the landing page in the site repository):

  inventory count   "<N> [up to 3 words] commands" or "<N>-command" with N >= 8, in digits or
                    words. Smaller numbers ("recommends 1-3 commands") are not inventory claims.
  file count        "<N> command files" or "<N> slash command definitions": the command files alone,
                    len(SHARED_COMMANDS) + len(STUDENT_ONLY), or len(SHARED_COMMANDS) on a SUBSET_FILES page
  mutant count      "<N> planted defects" or "<N> mutants" on a line that names a <name>_mutations.py:
                    must equal the entries in that file's *MUTANTS dictionaries (counted, not run)
  version pin       "git checkout vX", "releases/download/vX", "releases/tag/vX", "Download vX",
                    a `version:` line in CITATION.cff, a BibTeX `version = {X.Y.Z}`, and a three-part
                    "Status: vX.Y.Z" (a two-part "Status: v2.0" names a series and is not checked)
  banned claim      phrases with no evidence behind them (BANNED)

Not claim surfaces: HISTORICAL files (DESIGN.md, CHANGELOG.md), which record what was true then;
pcv/, the upstream bundle, which is not ours to edit; tests/smoke/, whose fixtures plant wrong
values on purpose.

Exit codes: 0 consistent, 1 a claim disagrees, 2 cannot derive the truth.
Usage:  python3 tests/check_claims.py [EXTRA_FILE ...]      python3 tests/check_claims.py --self-test
Mutation proof: tests/check_claims_mutations.py
"""
from __future__ import annotations

import ast
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGE_SUFFIXES = {".md", ".txt", ".cff"}
HISTORICAL = {"DESIGN.md", "CHANGELOG.md"}
SKIP_DIRS = {".git", "pcv", "smoke"}
SUBSET_FILES = {"instructor/README.md"}
WORDS = {w: i for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
    "seventeen eighteen nineteen twenty twenty-one twenty-two twenty-three twenty-four twenty-five".split())}
COUNT = re.compile(r"\b(\d+|" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")"
                   r"(?:((?:\s+[A-Za-z-]+){0,3}?)\s+commands\b|-commands?\b)", re.I)
PIN = re.compile(r"(?:git checkout\s+|releases/download/|releases/tag/|Download\s+)v(\d+(?:\.\d+){1,2})", re.I)
CFF_VERSION = re.compile(r"^version:\s*['\"]?(\d+(?:\.\d+){1,2})", re.M)
BIB_VERSION = re.compile(r"\bversion\s*=\s*[{\"](\d+\.\d+\.\d+)[}\"]")
STATUS = re.compile(r"\bStatus:\**\s*v(\d+\.\d+\.\d+)")
NUM = r"(\d+|" + "|".join(sorted(WORDS, key=len, reverse=True)) + r")"
FILES = re.compile(r"\b" + NUM + r"\s+(?:slash\s+)?command\s+(?:files|definitions)\b", re.I)
HARNESS = re.compile(r"\b([A-Za-z0-9_]+)_mutations\.py\b")
MUTANT_COUNT = re.compile(r"\b(\d+)\s+(?:planted defects|mutants)\b", re.I)
BANNED = ["hundreds of production sessions", "guarantees the model", "always runs on"]


def derive(root: Path) -> tuple[int | None, int | None, str | None]:
    """(command count, instructor count, version) from the tree, or None where it cannot be derived."""
    count = instructor = version = None
    inst = root / "install.sh"
    if inst.exists():
        text = inst.read_text(encoding="utf-8", errors="replace")
        arrays = {m.group(1): m.group(2).split() for m in re.finditer(r"^(SHARED_COMMANDS|STUDENT_ONLY)=\(([^)]*)\)", text, re.M)}
        if len(arrays) == 2:
            count = len(arrays["SHARED_COMMANDS"]) + len(arrays["STUDENT_ONLY"]) + 1
            instructor = len(arrays["SHARED_COMMANDS"]) + 1
    vf = root / "VERSION"
    if vf.exists() and vf.read_text(encoding="utf-8").strip():
        version = vf.read_text(encoding="utf-8").strip()
    return count, instructor, version


def claim_files(root: Path) -> list[Path]:
    """Every page in the tree that a reader could take as describing the current release."""
    out = []
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if (p.is_file() and p.suffix in PAGE_SUFFIXES and rel.as_posix() not in HISTORICAL
                and not set(rel.parts[:-1]) & SKIP_DIRS):
            out.append(p)
    return out


def mutant_entries(root: Path, harness: str) -> int | None:
    """Entries in the *MUTANTS dictionaries of <harness>_mutations.py anywhere in the tree, or None if absent."""
    found = [p for p in root.rglob(f"{harness}_mutations.py") if ".git" not in p.parts]
    if not found:
        return None
    tree = ast.parse(found[0].read_text(encoding="utf-8"))
    return sum(len(node.value.keys) for node in tree.body
               if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict)
               and any(isinstance(t, ast.Name) and t.id.endswith("MUTANTS") for t in node.targets))


def claims_in(text: str) -> list[tuple[int, str, str]]:
    """(line, kind, value) for every claim in text. kind is count, files, mutants, pin, cff_version or banned."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for m in COUNT.finditer(line):
            tok = m.group(1).lower()
            value = int(tok) if tok.isdigit() else WORDS[tok]
            if value >= 8:
                out.append((n, "count", str(value)))
        for m in FILES.finditer(line):
            tok = m.group(1).lower()
            out.append((n, "files", str(int(tok) if tok.isdigit() else WORDS[tok])))
        harnesses = list(HARNESS.finditer(line))
        for m in MUTANT_COUNT.finditer(line):
            before = [h for h in harnesses if h.start() < m.start()]
            h = before[-1] if before else (harnesses[0] if harnesses else None)
            if h:
                out.append((n, "mutants", f"{h.group(1)}:{m.group(1)}"))
        for rx in (PIN, BIB_VERSION, STATUS):
            for m in rx.finditer(line):
                out.append((n, "pin", m.group(1)))
        low = line.lower()
        for phrase in BANNED:
            if phrase in low:
                out.append((n, "banned", phrase))
    for m in CFF_VERSION.finditer(text):
        out.append((text[:m.start()].count("\n") + 1, "cff_version", m.group(1)))
    return out


def run(root: Path, extra: list[Path]) -> tuple[int, list[str], tuple]:
    root = root.resolve()
    count, instructor, version = derive(root)
    if count is None or version is None:
        return 2, [f"cannot derive the truth: count={count} version={version}"], (count, version)
    problems = []
    files = claim_files(root) + [p for p in extra if p.resolve() not in claim_files(root)]
    for p in files:
        p = p.resolve()
        name = p.relative_to(root).as_posix() if root in p.parents else f"{p.parent.name}/{p.name}"
        want, source = (instructor, "install.sh --minimal") if name in SUBSET_FILES else (count, "install.sh")
        for n, kind, value in claims_in(p.read_text(encoding="utf-8", errors="replace")):
            if kind == "count" and int(value) != want:
                problems.append(f"{name}:{n}  says {value} commands; {source} gives {want}")
            elif kind == "files" and int(value) != want - 1:
                problems.append(f"{name}:{n}  says {value} command files; {source} gives {want - 1}")
            elif kind == "mutants":
                harness, said = value.split(":")
                real = mutant_entries(root, harness)
                if real is None:
                    problems.append(f"{name}:{n}  names {harness}_mutations.py, which is not in the tree")
                elif int(said) != real:
                    problems.append(f"{name}:{n}  says {said} for {harness}_mutations.py; it holds {real} mutants")
            elif kind in ("pin", "cff_version") and value != version:
                problems.append(f"{name}:{n}  pins {value}; VERSION is {version}")
            elif kind == "banned":
                problems.append(f"{name}:{n}  banned claim: {value!r}")
    return (1 if problems else 0), problems, (count, version)


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def tree(readme, version="2.0.0", shared="(setup coa pace)", student="(startup audit)"):
        d = Path(tempfile.mkdtemp(prefix="checkclaims_"))
        (d / "install.sh").write_text(f"SHARED_COMMANDS={shared}\nSTUDENT_ONLY={student}\n", encoding="utf-8")
        if version is not None:
            (d / "VERSION").write_text(version + "\n", encoding="utf-8")
        (d / "README.md").write_text(readme, encoding="utf-8")
        return d

    # 3 + 2 + /pcv = 6 commands; numbers below 8 are not inventory claims, so the fixtures use a bigger set
    big_shared = "(setup coa pace improve quarto readable help review)"
    big_student = "(startup dailysummary weeklysummary commit simplify audit runlog)"
    good = "16 Claude Code commands. Install: git checkout v2.0.0\nIt recommends 1-3 commands.\n"
    code, probs, truth = run(tree(good, shared=big_shared, student=big_student), [])
    check("derived count is shared + student + /pcv", truth == (16, "2.0.0"))
    check("a consistent tree passes (positive control)", code == 0 and not probs)

    code, probs, _ = run(tree("15 Claude Code commands\n", shared=big_shared, student=big_student), [])
    check("a wrong digit count is caught", code == 1 and any("says 15" in p for p in probs))
    code, probs, _ = run(tree("Fifteen Claude Code slash commands\n", shared=big_shared, student=big_student), [])
    check("a wrong count in words is caught", code == 1 and any("says 15" in p for p in probs))
    code, probs, _ = run(tree("the 11 core research workflow commands work\n", shared=big_shared, student=big_student), [])
    check("a count with qualifying words between is caught", code == 1 and any("says 11" in p for p in probs))
    code, probs, _ = run(tree("It recommends 1-3 commands, or 2 commands at most.\n", shared=big_shared, student=big_student), [])
    check("small recommendation counts are not inventory claims", code == 0)
    code, probs, _ = run(tree("The full 15-command toolkit\n", shared=big_shared, student=big_student), [])
    check("a hyphenated count ('15-command') is caught", code == 1 and any("says 15" in p for p in probs))
    code, probs, _ = run(tree("The full 16-command toolkit: 15 command files plus /pcv\n", shared=big_shared, student=big_student), [])
    check("a correct hyphenated count and a correct command-file count pass", code == 0)
    code, probs, _ = run(tree("It ships 14 command files plus /pcv.\n", shared=big_shared, student=big_student), [])
    check("a wrong command-file count is caught", code == 1 and any("says 14 command files" in p for p in probs))
    code, probs, _ = run(tree("`shared/commands/` holds fifteen slash command definitions.\n", shared=big_shared, student=big_student), [])
    check("'N slash command definitions' is a file count, in words too", code == 0)

    def add(d, rel, text):
        (d / rel).parent.mkdir(parents=True, exist_ok=True)
        (d / rel).write_text(text, encoding="utf-8")
        return d

    d = add(tree(good, shared=big_shared, student=big_student), "student/README.md", "The full 15-command toolkit\n")
    code, probs, _ = run(d, [])
    check("a page in any folder is checked (discovery, not a hand list)", code == 1 and any(p.startswith("student/README.md:1") for p in probs))
    d = add(tree(good, shared=big_shared, student=big_student), "instructor/README.md", "A 9-command subset: 9 commands.\n")
    code, probs, _ = run(d, [])
    check("the instructor page passes at the instructor count (shared + /pcv)", code == 0)
    d = add(tree(good, shared=big_shared, student=big_student), "instructor/README.md", "9 commands: 8 command files plus /pcv.\n")
    code, probs, _ = run(d, [])
    check("the instructor page's command-file count is held to SHARED_COMMANDS", code == 0)
    d = add(tree(good, shared=big_shared, student=big_student), "instructor/README.md", "All 16 commands.\n")
    code, probs, _ = run(d, [])
    check("the instructor page is caught at any other count", code == 1 and any("--minimal gives 9" in p for p in probs))
    d = add(tree(good, shared=big_shared, student=big_student), "DESIGN.md", "v1.0 shipped 15 commands.\n")
    code, probs, _ = run(d, [])
    check("historical files are not claim surfaces", code == 0)
    d = add(add(tree(good, shared=big_shared, student=big_student), "pcv/skill/SKILL.md", "15 commands\n"), "tests/smoke/fixture.md", "15 commands\n")
    code, probs, _ = run(d, [])
    check("pcv/ and tests/smoke/ are not claim surfaces", code == 0)

    code, probs, _ = run(tree("git checkout v0.1.0\n", shared=big_shared, student=big_student), [])
    check("a stale install pin is caught", code == 1 and any("pins 0.1.0" in p for p in probs))
    code, probs, _ = run(tree("curl -L https://x/releases/download/v1.6/x.zip\n", shared=big_shared, student=big_student), [])
    check("a stale download URL is caught", code == 1 and any("pins 1.6" in p for p in probs))
    code, probs, _ = run(tree("@software{x,\n  version = {1.9.0},\n}\n", shared=big_shared, student=big_student), [])
    check("a stale BibTeX version is caught", code == 1 and any("pins 1.9.0" in p for p in probs))
    code, probs, _ = run(tree("Status: v1.9.0 (2026-01-01).\n", shared=big_shared, student=big_student), [])
    check("a stale three-part Status line is caught", code == 1 and any("pins 1.9.0" in p for p in probs))
    code, probs, _ = run(tree("> **Status: v2.0.** One author.\n", shared=big_shared, student=big_student), [])
    check("a two-part 'Status: v2.0' is a series, not a pin", code == 0)
    code, probs, _ = run(tree("Validated across hundreds of production sessions.\n", shared=big_shared, student=big_student), [])
    check("the banned unbacked claim is caught", code == 1 and any("banned" in p for p in probs))

    d = tree(good, shared=big_shared, student=big_student)
    (d / "CITATION.cff").write_text("cff-version: 1.2.0\nversion: 0.1.0\n", encoding="utf-8")
    code, probs, _ = run(d, [])
    check("CITATION.cff version must match VERSION (cff-version is not the version)", code == 1 and any("CITATION.cff" in p and "0.1.0" in p for p in probs) and not any("1.2.0" in p for p in probs))

    page = Path(tempfile.mkdtemp()) / "index.html"
    page.write_text("<p>14 commands</p>", encoding="utf-8")
    code, probs, _ = run(tree(good, shared=big_shared, student=big_student), [page])
    check("an extra file (the landing page) is checked too", code == 1 and any("says 14" in p for p in probs))

    for phrase in ("This guarantees the model each agent uses.", "Every seat always runs on Sonnet."):
        code, probs, _ = run(tree(phrase + "\n", shared=big_shared, student=big_student), [])
        check(f"the banned claim in {phrase!r} is caught", code == 1 and any("banned" in p for p in probs))

    harness = 'MUTANTS = {"a": 1, "b": 2}\nLAUNCHER_MUTANTS = {"c": 3}\nOTHER = {"d": 4}\n'
    d = add(tree(good, shared=big_shared, student=big_student), "tests/x_mutations.py", harness)
    add(d, "EVIDENCE.md", "| `python3 tests/x_mutations.py` — 3 planted defects |\n")
    code, probs, _ = run(d, [])
    check("a mutant count that matches its harness passes (every *MUTANTS dictionary counted)", code == 0)
    add(d, "EVIDENCE.md", "| `python3 tests/x_mutations.py` — 4 planted defects |\n")
    code, probs, _ = run(d, [])
    check("a mutant count that disagrees with its harness is caught",
          code == 1 and any("says 4 for x_mutations.py; it holds 3" in p for p in probs))
    add(d, "EVIDENCE.md", "`x_mutations.py` (3 mutants) and `a_mutations.py` (5 mutants)\n")
    code, probs, _ = run(d, [])
    check("each mutant count pairs with the harness named just before it",
          code == 1 and any("a_mutations.py, which is not in the tree" in p for p in probs)
          and not any("x_mutations.py" in p for p in probs))

    code, probs, _ = run(tree(good, version=None, shared=big_shared, student=big_student), [])
    check("no VERSION file is exit 2, never a pass", code == 2)
    d = tree(good, shared=big_shared, student=big_student)
    (d / "install.sh").write_text(f"SHARED_COMMANDS={big_shared}\n", encoding="utf-8")
    code, probs, _ = run(d, [])
    check("an installer with an array missing is exit 2, never a pass", code == 2)

    print(f"check_claims self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    code, problems, (count, version) = run(ROOT, [Path(a).resolve() for a in sys.argv[1:]])
    for p in problems:
        print(p)
    print(f"\ntruth: {count} commands, version {version}; {len(problems)} disagreement(s)")
    return code


if __name__ == "__main__":
    sys.exit(main())
