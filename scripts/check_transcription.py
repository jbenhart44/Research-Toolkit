#!/usr/bin/env python3
"""check_transcription.py -- refuse a page transcription of a scanned PDF before anything cites it.

    python3 check_transcription.py --pages 12 --transcript a.txt [--second b.txt] [--names "Smith,Lee"]
                                   [--residual extracted.txt] [--pdf paper.pdf]
    python3 check_transcription.py --self-test

A transcriber agent reads rendered page images and writes `=== PAGE N ===` sections. A misread digit in that text later
passes every grep: /audit finds the wrong number "on the page". These checks run on the transcription before it is
installed beside the PDF:

  1 page_markers    exactly one `=== PAGE N ===` per page, numbered 1..N
  2 page_body       every page has at least 100 characters, unless it is marked [blank] or [MATERIAL GAP: ...]
  3 residual        when a text extractor got some words from the PDF (--residual), at least half the long ones are
                    in the transcription
  4 names           at least one expected name (--names, e.g. the authors) appears
  5 refusals        no transcriber refusal or filler ("I cannot transcribe", "the image shows", "lorem ipsum", ...)
  6 vocabulary      at least 20 distinct words of 3+ letters per page on average
  With --second (an independent transcription of the same pages):
  7 agreement       word overlap (Jaccard) at least 0.50 and length ratio at least 0.60
  8 numbers         every number in either transcription is in both, page by page: a digit one reader misread is a
                    number the other does not have

--pdf reads the page count from the PDF (pypdf, else PyMuPDF) when --pages is not given.
Exit 0 every check passed · 1 a check failed (each failure is named) · 2 usage, or a file that cannot be read.
Ported from a checker first written for vision transcriptions of scanned papers. Mutation proof:
scripts/check_transcription_mutations.py
"""
from __future__ import annotations

import argparse
import re
import sys
import tempfile
from pathlib import Path

PAGE = re.compile(r"^=== PAGE (\d+)(?:\s+[^=]*)?\s*===\s*$", re.M)
MIN_PAGE_CHARS = 100
MIN_WORDS_PER_PAGE = 20
MIN_JACCARD, MIN_LENGTH_RATIO = 0.50, 0.60
REFUSALS = ("i cannot transcribe", "unable to read", "the image shows", "lorem ipsum", "as an ai", "i apologize",
            "i'm unable", "i am unable")
STOP = {"the", "and", "for", "are", "was", "were", "been", "this", "that", "with", "from", "not", "but", "have", "has"}
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*%?")


def pages(text: str) -> dict[int, str]:
    marks = list(PAGE.finditer(text))
    return {int(m.group(1)): text[m.end():marks[k + 1].start() if k + 1 < len(marks) else len(text)]
            for k, m in enumerate(marks)}


def check_page_markers(text: str, n: int) -> tuple[bool, str]:
    nums = [int(m.group(1)) for m in PAGE.finditer(text)]
    if sorted(nums) != list(range(1, n + 1)):
        missing = sorted(set(range(1, n + 1)) - set(nums))
        extra = sorted(x for x in set(nums) if nums.count(x) > 1 or not 1 <= x <= n)
        return False, f"expected pages 1..{n}; missing {missing}, repeated or out of range {extra}"
    return True, f"{n} page markers, 1..{n}"


def check_page_body(text: str) -> tuple[bool, str]:
    sparse = []
    for k, body in pages(text).items():
        b = body.strip()
        if b.startswith("[blank]") or b.startswith("[MATERIAL GAP"):
            continue
        if len(re.sub(r"\s+", "", b)) < MIN_PAGE_CHARS:
            sparse.append(k)
    return (not sparse), (f"pages under {MIN_PAGE_CHARS} characters: {sparse}" if sparse else "every page has a body")


def check_residual(text: str, residual: str) -> tuple[bool, str]:
    tokens = {t.lower() for t in re.findall(r"[A-Za-z]{5,}", residual)} - {"page", "figure", "table", "section"}
    if len(tokens) < 3:
        return True, "no usable extracted text to compare (skipped)"
    low = text.lower()
    found = sum(t in low for t in tokens)
    ok = found / len(tokens) >= 0.5
    return ok, f"{found}/{len(tokens)} extracted words are in the transcription"


def check_names(text: str, names: list[str]) -> tuple[bool, str]:
    if not names:
        return True, "no names given (skipped)"
    hit = [s for s in names if re.search(r"\b" + re.escape(s) + r"\b", text, re.I)]
    return bool(hit), (f"found {hit}" if hit else f"none of {names} appears")


def check_refusals(text: str) -> tuple[bool, str]:
    hits = [p for p in REFUSALS if p in text.lower()]
    return (not hits), (f"refusal or filler text: {hits}" if hits else "no refusal or filler text")


def check_vocabulary(text: str, n: int) -> tuple[bool, str]:
    distinct = len(set(re.findall(r"[a-z]{3,}", text.lower())))
    need = MIN_WORDS_PER_PAGE * n
    return distinct >= need, f"{distinct} distinct words (needs {need} for {n} pages)"


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z]{3,}", text.lower()) if w not in STOP}


def check_agreement(a: str, b: str) -> tuple[bool, str]:
    wa, wb = words(a), words(b)
    if not wa or not wb:
        return False, "one transcription has no words"
    j = len(wa & wb) / len(wa | wb)
    ratio = min(len(a), len(b)) / max(len(a), len(b))
    ok = j >= MIN_JACCARD and ratio >= MIN_LENGTH_RATIO
    return ok, f"word overlap {j:.2f} (needs {MIN_JACCARD}), length ratio {ratio:.2f} (needs {MIN_LENGTH_RATIO})"


def check_numbers(a: str, b: str) -> tuple[bool, str]:
    pa, pb = pages(a), pages(b)
    diffs = []
    for k in sorted(set(pa) | set(pb)):
        na, nb = set(NUMBER.findall(pa.get(k, ""))), set(NUMBER.findall(pb.get(k, "")))
        if na != nb:
            diffs.append(f"p.{k}: only in the first {sorted(na - nb)[:5]}, only in the second {sorted(nb - na)[:5]}")
    return (not diffs), ("; ".join(diffs[:4]) + (f" (+{len(diffs) - 4} pages)" if len(diffs) > 4 else "")
                         if diffs else "every number appears in both, page by page")


def run(n: int, text: str, second: str | None = None, names: list[str] | None = None, residual: str = "") -> list:
    rows = [("page_markers", *check_page_markers(text, n)), ("page_body", *check_page_body(text)),
            ("residual", *check_residual(text, residual)), ("names", *check_names(text, names or [])),
            ("refusals", *check_refusals(text)), ("vocabulary", *check_vocabulary(text, n))]
    if second is not None:
        rows += [("agreement", *check_agreement(text, second)), ("numbers", *check_numbers(text, second))]
    return rows


def pdf_pages(pdf: Path) -> int:
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(pdf)).pages)
    except ImportError:
        pass
    try:
        import pymupdf as mu
    except ImportError:
        import fitz as mu
    with mu.open(str(pdf)) as doc:
        return len(doc)


def self_test() -> int:
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    body = ("Smith and Lee report that the survey response rate was 22% in 2023, with 14.41 completed interviews per "
            "interviewer hour on weekdays and fewer during weekends. Respondents answer reminder letters within days, "
            "and the field team adjusts its schedule when returns fall below the forecast for each district. ")
    own = {1: "The introduction frames research questions about attitudes, trust and civic participation.",
           2: "Methods describe panel regressions, instrumental variables, robustness checks and sampling weights.",
           3: "Conclusions discuss limitations, weighting standards, disclosure practice and future fieldwork."}
    good = "".join(f"=== PAGE {k} ===\n{body}{own[k]}\n" for k in (1, 2, 3))
    def passed(rows, name):
        """True or False for the named check; None when that check did not run, so 'not passed' cannot pass vacuously."""
        return next((r[1] for r in rows if r[0] == name), None)

    def refused(rows, name):
        return passed(rows, name) is False

    rows = run(3, good, good, ["Smith"], "interviewer district forecast weekdays")
    check("positive control: a good transcription and an identical second one pass every check",
          len(rows) == 8 and all(r[1] for r in rows))
    check("a missing page marker fails", refused(run(3, good.replace("=== PAGE 2 ===", "=== PAGE 9 ===")), "page_markers"))
    check("a repeated page marker fails", refused(run(3, good + "=== PAGE 2 ===\n" + body), "page_markers"))
    short = good.replace(f"=== PAGE 2 ===\n{body}", "=== PAGE 2 ===\nToo short.")
    check("a page under 100 characters fails", refused(run(3, short), "page_body"))
    check("a page marked [blank] is allowed", passed(run(3, good.replace(f"=== PAGE 2 ===\n{body}", "=== PAGE 2 ===\n[blank]\n")), "page_body") is True)
    check("a page with a MATERIAL GAP marker is allowed",
          passed(run(3, good.replace(f"=== PAGE 2 ===\n{body}", "=== PAGE 2 ===\n[MATERIAL GAP: unreadable scan]\n")), "page_body") is True)
    check("extracted words missing from the transcription fail",
          refused(run(3, good, residual="zebra quartz vortex marmalade"), "residual"))
    check("too little extracted text skips the residual check", passed(run(3, good, residual="ab"), "residual") is True)
    check("no expected name in the text fails", refused(run(3, good, names=["Okonkwo"]), "names"))
    check("a refusal in the text fails", refused(run(3, good + "\nI cannot transcribe this page.\n"), "refusals"))
    check("a repetitive transcription fails the vocabulary check",
          refused(run(3, "".join(f"=== PAGE {k} ===\n" + "data data data " * 60 + "\n" for k in (1, 2, 3))), "vocabulary"))
    other = "".join(f"=== PAGE {k} ===\nCompletely different words about gardening tomatoes peppers soil compost.\n" for k in (1, 2, 3))
    check("a second transcription that disagrees fails the agreement check", refused(run(3, good, other), "agreement"))
    misread = good.replace("14.41", "14.47", 1)
    rows = run(3, good, misread)
    check("one misread digit fails the numbers check, naming the page", refused(rows, "numbers")
          and "p.1" in next(r[2] for r in rows if r[0] == "numbers"))
    check("and it still passes the word-agreement check, which is why the numbers check exists", passed(rows, "agreement") is True)
    check("a percentage misread as another percentage fails", refused(run(3, good, good.replace("22%", "27%")), "numbers"))
    check("without --second the cross-checks do not run", {r[0] for r in run(3, good)} >= {"page_markers"}
          and "numbers" not in {r[0] for r in run(3, good)})
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "a.txt"
        t.write_text(good, encoding="utf-8")
        check("the command line passes a good file, exit 0", main(["--pages", "3", "--transcript", str(t)], quiet=True) == 0)
        (Path(d) / "b.txt").write_text(misread, encoding="utf-8")
        check("the command line fails a misread second file, exit 1",
              main(["--pages", "3", "--transcript", str(t), "--second", str(Path(d) / "b.txt")], quiet=True) == 1)
        check("a missing file is exit 2", main(["--pages", "3", "--transcript", str(Path(d) / "none.txt")], quiet=True) == 2)
        check("no page count is exit 2", main(["--transcript", str(t)], quiet=True) == 2)
    print(f"check_transcription self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main(argv=None, quiet: bool = False) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--pages", type=int)
    ap.add_argument("--pdf")
    ap.add_argument("--transcript")
    ap.add_argument("--second")
    ap.add_argument("--names", default="")
    ap.add_argument("--residual")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    say = (lambda *x, **k: None) if quiet else print
    try:
        n = a.pages or (pdf_pages(Path(a.pdf)) if a.pdf else 0)
        if not n or not a.transcript:
            say("usage: --transcript FILE and --pages N (or --pdf FILE) are required", file=sys.stderr)
            return 2
        text = Path(a.transcript).read_text(encoding="utf-8")
        second = Path(a.second).read_text(encoding="utf-8") if a.second else None
        residual = Path(a.residual).read_text(encoding="utf-8") if a.residual else ""
    except (OSError, UnicodeDecodeError, ImportError, ValueError) as e:
        say(f"cannot read the inputs: {e}", file=sys.stderr)
        return 2
    rows = run(n, text, second, [s.strip() for s in a.names.split(",") if s.strip()], residual)
    for name, passed, why in rows:
        say(f"  {'ok  ' if passed else 'FAIL'} {name:<13} {why}")
    failed = [r[0] for r in rows if not r[1]]
    say(f"VERDICT: {'pass' if not failed else 'refuse: ' + ', '.join(failed)} ({len(rows) - len(failed)}/{len(rows)} checks)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
