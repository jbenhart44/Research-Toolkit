#!/usr/bin/env python3
"""Catch a markdown document that carries two sections claiming to be the same section.

WHY IT EXISTS
  A document edited many times in one long session can end up with two sections headed, say,
  `## Next steps` and `## Next Steps`, holding two different lists. Every edit was right on its own; the
  document disagrees with itself, and a reader has no way to know which section is current. Per-edit review
  cannot see this. Only a whole-document check can.

WHAT COUNTS AS A COLLISION
  Two headings that are SIBLINGS (same level, inside the same enclosing section) whose titles are equal after
  case-folding and after every non-word character is folded to a single space. All of these collide:

      ## Next steps     ==   ## Next Steps
      ## Commits        ==   ## Commits:
      ## **Commits**    ==   ## Commits
      ## Summary ##     ==   ## Summary

  Siblings only, and this is the load-bearing decision. Not across levels: `## Files Modified` followed by
  `### Files Modified` is a section that summarises and then details itself. Not across sections: a per-item
  template (`### Results` under each of `## Phase 1`, `## Phase 2`, …) is a correct document. On the corpus this
  gate was built against, comparing every same-level heading reported 42 collisions, 37 of them template repeats;
  scoping to siblings kept every true defect and dropped every template repeat.

  ACCEPTED BLIND SPOT: a duplication split across two different parent sections is not reported. The count of
  such repeats is always printed, and `--cross-section` lists them, but they never affect the exit code.

  A duplicated block that drags its children with it is reported once, at the block: its children sit under two
  different instances of the parent, so only the parent is flagged.

WHAT IT WILL NOT SEE (counted and printed, never silently dropped)
  * Headings after an unclosed code fence: per CommonMark an unterminated fence runs to the end of the file. Such
    files are named under UNCHECKED.
  * Setext headings (a title underlined with === or ---). A `---` line is also a thematic break and a front-matter
    delimiter, and parsing it would cost false positives. Files with a probable setext underline are counted
    under UNCHECKED.
  * Headings inside HTML blocks other than comments, and headings produced by templating.
  * Files that cannot be decoded as UTF-8: counted and named.

WHAT IS DELIBERATELY IGNORED (each was a false-positive class in the triage)
  Fenced code (``` and ~~~, any length, any info string), YAML front matter, HTML comments, `#hashtag` with no
  space after the hashes, and lines indented four or more spaces.

USAGE
    python3 scripts/check_heading_collisions.py notes.md docs/          # report only, exits 0
    python3 scripts/check_heading_collisions.py --check notes.md        # gate: exits 1 on a sibling collision
    --cross-section  also list same-title headings in different sections (never gated)
    --ext .md,.qmd   extensions to pick up when walking a directory (default .md)
    --quiet          print only collisions and the totals
    --self-test      run the pinned cases and exit

EXIT CODES  0 clean, or reporting mode · 1 --check and a sibling collision · 2 a path is missing or nothing matched
Mutation proof: scripts/check_heading_collisions_mutations.py
"""
import argparse
import os
import re
import sys
import tempfile
from collections import defaultdict

# ATX heading: up to 3 leading spaces, 1-6 '#', then a space or tab, or the end of the line. The space is
# CommonMark, and it is what keeps `#hashtag` and `#!/usr/bin/env python3` from reading as headings.
ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?[ \t]*$")
ATX_CLOSE_RE = re.compile(r"[ \t]+#+[ \t]*$")  # `## Title ##` -> `Title`, for the printed title; the key folds `#` anyway
FENCE_OPEN_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
FRONTMATTER_RE = re.compile(r"^-{3,}[ \t]*$")
FRONTMATTER_END_RE = re.compile(r"^(-{3,}|\.{3,})[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(={2,}|-{2,})[ \t]*$")
# Fold case, then every non-word character and the underscore to one space, so `## /improve Candidates` and
# `## /improve candidates` land on the same key.
NORMALISE_RE = re.compile(r"[\W_]+", re.UNICODE)


def normalise(title):
    """Case- and punctuation-insensitive key for a heading title."""
    return " ".join(NORMALISE_RE.sub(" ", title.casefold()).split())


class Heading:
    """One ATX heading, plus the line of its enclosing section (0 at top level).

    Two headings are siblings when they share a level and a parent LINE. Keying on the parent's line, not its
    text, is what keeps a pasted-twice section's children from being reported apart from the section.
    """

    __slots__ = ("level", "title", "line", "parent_line")

    def __init__(self, level, title, line, parent_line):
        self.level, self.title, self.line, self.parent_line = level, title, line, parent_line


class ParseResult:
    def __init__(self):
        self.headings = []
        self.unclosed_fence = None   # line where a never-closed fence opened
        self.setext_suspect = 0      # probable setext underlines seen


def parse_headings(lines):
    """ATX headings, skipping fenced code, front matter and HTML comments; what was not examined is recorded."""
    res = ParseResult()
    i, n = 0, len(lines)
    if n and FRONTMATTER_RE.match(lines[0]):  # front matter only when '---' is the very first line
        j = 1
        while j < n and not FRONTMATTER_END_RE.match(lines[j]):
            j += 1
        if j < n:
            i = j + 1
    fence_char, fence_len, fence_line = None, 0, 0
    in_html_comment = False
    stack = []  # open headings, outermost first: [(level, line), ...]
    while i < n:
        line = lines[i]
        if fence_char is not None:
            m = FENCE_OPEN_RE.match(line)  # a closing fence: same character, at least as long, nothing after
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len and m.group(2).strip() == "":
                fence_char = None
            i += 1
            continue
        if in_html_comment:
            if "-->" in line:
                in_html_comment = False
            i += 1
            continue
        m = FENCE_OPEN_RE.match(line)
        if m:
            marker, info = m.group(1), m.group(2)
            if not (marker[0] == "`" and "`" in info):  # a backtick fence's info string may not hold a backtick
                fence_char, fence_len, fence_line = marker[0], len(marker), i + 1
                i += 1
                continue
        if "<!--" in line and "-->" not in line.split("<!--", 1)[1]:
            in_html_comment = True
            i += 1
            continue
        m = ATX_RE.match(line)
        if m:
            level = len(m.group(1))
            title = ATX_CLOSE_RE.sub("", m.group(2) or "").strip()
            while stack and stack[-1][0] >= level:
                stack.pop()
            res.headings.append(Heading(level, title, i + 1, stack[-1][1] if stack else 0))
            stack.append((level, i + 1))
            i += 1
            continue
        if SETEXT_RE.match(line) and i > 0:  # counted only, so the file is reported as partly unchecked
            prev = lines[i - 1].strip()
            if prev and not prev.startswith(("#", "-", "*", "+", ">", "|")) and not FENCE_OPEN_RE.match(lines[i - 1]):
                res.setext_suspect += 1
        i += 1
    if fence_char is not None:
        res.unclosed_fence = fence_line
    return res


class FileReport:
    def __init__(self, path):
        self.path = path
        self.collisions = []      # (level, key, [(line, title), ...]) among siblings
        self.cross_section = []   # the same across different parents; never gated
        self.unclosed_fence = None
        self.setext_suspect = 0
        self.error = None


def check_file(path):
    rep = FileReport(path)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except UnicodeDecodeError as exc:
        rep.error = f"not valid UTF-8 ({exc.reason})"
        return rep
    except OSError as exc:
        rep.error = f"unreadable ({exc.strerror})"
        return rep
    res = parse_headings(lines)
    rep.unclosed_fence, rep.setext_suspect = res.unclosed_fence, res.setext_suspect
    siblings = defaultdict(list)   # (level, parent_line, key) -> hits
    by_title = defaultdict(list)   # (level, key) -> hits
    for h in res.headings:
        key = normalise(h.title)
        if not key:  # a heading that is only punctuation has no identity
            continue
        siblings[(h.level, h.parent_line, key)].append((h.line, h.title))
        by_title[(h.level, key)].append((h.line, h.title))
    gated = set()
    for (level, _parent, key), hits in siblings.items():
        if len(hits) > 1:
            rep.collisions.append((level, key, sorted(hits)))
            gated.update(ln for ln, _ in hits)
    for (level, key), hits in by_title.items():
        if len(hits) > 1 and not all(ln in gated for ln, _ in hits):
            rep.cross_section.append((level, key, sorted(hits)))
    rep.collisions.sort(key=lambda c: c[2][0][0])
    rep.cross_section.sort(key=lambda c: c[2][0][0])
    return rep


def collect_paths(paths, exts):
    files, missing = [], []
    for p in paths:
        if os.path.isdir(p):
            for root, dirnames, filenames in os.walk(p):
                dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".venv", "__pycache__")]
                files.extend(os.path.join(root, fn) for fn in sorted(filenames) if fn.lower().endswith(exts))
        elif os.path.isfile(p):
            files.append(p)
        else:
            missing.append(p)
    return sorted(set(files)), missing


def _print_group(label, level, key, hits):
    hashes = "#" * level
    print(f"  {label}  level {level} ({hashes})  → \"{key}\"")
    for lineno, title in hits:
        print(f"      line {lineno}: {hashes} {title}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Report markdown headings that collide within a file (same level, "
                                             "same enclosing section, case- and punctuation-insensitive).")
    ap.add_argument("paths", nargs="*", help="markdown files and/or directories to walk")
    ap.add_argument("--check", action="store_true", help="exit 1 if any sibling collision is found")
    ap.add_argument("--cross-section", action="store_true",
                    help="also list same-title headings in different sections (never affects the exit code)")
    ap.add_argument("--ext", default=".md", help="comma-separated extensions to pick up when walking a directory")
    ap.add_argument("--quiet", action="store_true", help="print only collisions and totals")
    ap.add_argument("--self-test", action="store_true", help="run the pinned cases and exit")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if not args.paths:
        ap.print_usage(sys.stderr)
        print("error: no paths given", file=sys.stderr)
        return 2
    exts = tuple(e if e.startswith(".") else "." + e for e in (s.strip().lower() for s in args.ext.split(",")) if e)
    files, missing = collect_paths(args.paths, exts)
    for p in missing:
        print(f"error: no such file or directory: {p}", file=sys.stderr)
    if missing or not files:
        if not files:
            print("error: no markdown files matched", file=sys.stderr)
        return 2
    reports = [check_file(p) for p in files]
    n_coll_files = n_coll = n_cross = 0
    for rep in reports:
        if rep.error:
            continue
        n_cross += len(rep.cross_section)
        show_cross = args.cross_section and rep.cross_section
        if not rep.collisions and not show_cross:
            continue
        n_coll_files += bool(rep.collisions)
        print(f"\n{rep.path}")
        for level, key, hits in rep.collisions:
            n_coll += 1
            _print_group("COLLISION    ", level, key, hits)
        if show_cross:
            for level, key, hits in rep.cross_section:
                _print_group("repeated (ok)", level, key, hits)
    unreadable = [r for r in reports if r.error]
    unclosed = [r for r in reports if not r.error and r.unclosed_fence]
    setext = [r for r in reports if not r.error and r.setext_suspect]
    print(f"\nscanned {len(files)} file(s): {n_coll} sibling collision(s) in {n_coll_files} file(s)")
    print(f"NOT GATED: {n_cross} same-title heading pair(s) in different sections (--cross-section to list)")
    # What could not be checked is printed on every run, a clean one included.
    print(f"UNCHECKED: {len(unclosed)} file(s) with an unclosed code fence (the text after it is code)")
    print(f"UNCHECKED: {len(setext)} file(s) with a probable setext underline (setext headings are not parsed)")
    print(f"UNCHECKED: {len(unreadable)} file(s) unreadable")
    if not args.quiet:
        for rep in unclosed:
            print(f"    unclosed fence  {rep.path}:{rep.unclosed_fence}")
        for rep in setext:
            print(f"    setext suspect  {rep.path} ({rep.setext_suspect})")
        for rep in unreadable:
            print(f"    unreadable      {rep.path}: {rep.error}")
    if args.check and n_coll:
        print("\nFAIL: two sections in this document claim to be the same section. Merge or rename them.")
        return 1
    return 0


# Each class found in the full-corpus triage, with the shape of the text that produced it.
# (name, markdown, expected sibling collisions, expected cross-section pairs)
SELF_TEST_CASES = [
    ("one letter's case", "## /improve Candidates\ncontent\n\n## /improve candidates\nmore\n", 1, 0),
    ("case only, top level, under a title", "# Session notes\n\n## Next steps\n- a\n\n## Next Steps\n- b\n", 1, 0),
    ("identical, top level", "# Build log\n\n## Next Steps\n1. a\n\n## Next Steps\n1. b\n", 1, 0),
    ("a duplicated block reports once, at the block",
     "## Planning State — RESUME HERE\n\n### Current Status\na\n\n### How to Resume\nb\n\n## Commits\n\nnone\n\n"
     "## Planning State — RESUME HERE\n\n### Current Status\nc\n\n### How to Resume\nd\n", 1, 2),
    ("trailing punctuation only", "## Commits\na\n\n## Commits:\nb\n", 1, 0),
    ("bold markers only", "## **Commits**\na\n\n## Commits\nb\n", 1, 0),
    ("a closing sequence is stripped", "## Summary ##\na\n\n## Summary\nb\n", 1, 0),
    ("three occurrences are one collision", "## Notes\na\n\n## notes\nb\n\n## NOTES:\nc\n", 1, 0),
    ("not gated: per-phase template subsections",
     "## Phase 1: Baseline (21 runs)\n### Objective\na\n### Design\nb\n### Results\nc\n\n"
     "## Phase 2: Tuning (27 runs)\n### Objective\nd\n### Design\ne\n### Results\nf\n", 0, 3),
    ("not gated: the same subsection under two sections",
     "## Files Modified / Added\n### Toolkit repository\na\n\n## Commits\n### Toolkit repository\nb\n", 0, 1),
    ("not gated: per-session template subsections",
     "## Session 1: Morning\n### Work Completed\na\n### Evidence\nb\n\n"
     "## Session 2: Afternoon\n### Work Completed\nc\n### Evidence\nd\n", 0, 2),
    ("ignored: # comments inside fences",
     "## Profiling\n\n```julia\n# BEFORE:\nf(x)\n```\n\n```julia\n# AFTER:\ng(x)\n```\n\n"
     "## Next\n\n```julia\n# BEFORE:\nh(x)\n```\n", 0, 0),
    ("ignored: a comment repeated in two shell examples",
     "## Examples\n\n```bash\n# Run simulation\njulia a.jl\n```\n\n```bash\n# Run simulation\njulia b.jl\n```\n", 0, 0),
    ("ignored: a shebang and comments in a python fence",
     "## A\n\n```python\n#!/usr/bin/env python3\n# helper\n```\n\n## B\n\n```python\n#!/usr/bin/env python3\n# helper\n```\n",
     0, 0),
    ("ignored: tilde fences", "## A\n\n~~~\n# note\n~~~\n\n## B\n\n~~~\n# note\n~~~\n", 0, 0),
    ("ignored: a four-backtick fence holding a three-backtick fence",
     "## A\n\n````md\n```bash\n# note\n```\n# note\n````\n\n## B\n\n````md\n```bash\n# note\n```\n# note\n````\n", 0, 0),
    ("ignored: hashes in YAML front matter", "---\nname: notes\n# Comment\n# Comment\n---\n\n## Body\n", 0, 0),
    ("ignored: a hashtag with no space", "#improve\ntext\n\n#improve\ntext\n", 0, 0),
    ("ignored: a heading inside an HTML comment", "## Draft\n\n<!--\n## Draft\n-->\n", 0, 0),
    ("ignored: an indented code block", "## A\n\n    # Draft\n\n## B\n\n    # Draft\n", 0, 0),
    ("ignored: different levels are nesting", "## Files Modified\ntext\n\n### Files Modified\ntext\n", 0, 0),
    ("ignored: a heading that is only punctuation", "## ***\na\n\n## ***\nb\n", 0, 0),
]


def _report(body):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as fh:
        fh.write(body)
    try:
        return check_file(fh.name)
    finally:
        os.unlink(fh.name)


def self_test():
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    for name, body, want_coll, want_cross in SELF_TEST_CASES:
        rep = _report(body)
        check(name, (len(rep.collisions), len(rep.cross_section)) == (want_coll, want_cross))
    rep = _report("## A\n\n```bash\n# never closed\n## A\n")
    check("an unclosed fence is counted and its tail is not parsed", rep.unclosed_fence == 3 and not rep.collisions)
    check("a setext underline is counted", _report("Heading One\n===========\n\ntext\n").setext_suspect == 1)
    check("a --- thematic break is not a setext suspect", _report("## A\n\n---\n\n## B\n").setext_suspect == 0)

    d = tempfile.mkdtemp(prefix="headings_")
    bad_doc, good_doc = os.path.join(d, "bad.md"), os.path.join(d, "good.md")
    with open(bad_doc, "w", encoding="utf-8") as fh:
        fh.write("## Next steps\na\n\n## Next Steps\nb\n")
    with open(good_doc, "w", encoding="utf-8") as fh:
        fh.write("## One\n\n## Two\n")
    quiet = ["--quiet"]
    with open(os.devnull, "w") as null:
        real, sys.stdout = sys.stdout, null
        try:
            codes = (main(["--check", bad_doc] + quiet), main([bad_doc] + quiet), main(["--check", good_doc] + quiet),
                     main([os.path.join(d, "missing.md")] + quiet), main(["--check", bad_doc, os.path.join(d, "x.md")]))
        finally:
            sys.stdout = real
    check("--check on a collision exits 1", codes[0] == 1)
    check("report mode exits 0 even on a collision", codes[1] == 0)
    check("--check on a clean file exits 0 (positive control)", codes[2] == 0)
    check("a missing path exits 2, never a pass", codes[3] == 2)
    check("a missing path beside a real one still exits 2", codes[4] == 2)
    print(f"check_heading_collisions self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
