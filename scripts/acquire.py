#!/usr/bin/env python3
"""acquire.py -- download a source, prove it is the document, extract its text, and check claimed figures against it.

    python3 scripts/acquire.py fetch <url> <target.pdf> [--user-agent "Your Name you@example.org"]
    python3 scripts/acquire.py extract <target.pdf> [--renders DIR]
    python3 scripts/acquire.py verify <target.txt> "<claim>" ["<claim>" ...]
    python3 scripts/acquire.py doi <doi> [--expect "Author et al. (2023)"]
    python3 scripts/acquire.py oa "<title>"
    python3 scripts/acquire.py manifest <manifest.md>
    python3 scripts/acquire.py --self-test

The steps of /acquire, as one tool, so that every check in them can be re-run and has been made to fail.

fetch     saves only a real PDF. HTML (a bot block, a paywall page) is deleted and refused; a file that is neither is kept
          for inspection and refused. It never overwrites a file that exists.
extract   pypdf, then PyMuPDF. Every page gets a `=== PAGE N ===` header; a page with no text gets a typed
          `[MATERIAL GAP: ...]` marker, never silence. The density gate: under 200 characters per page is SPARSE (a
          scanned page yields only header noise, about 70 a page; a text page yields thousands). SPARSE and EMPTY write
          no .txt and render the pages as PNGs for a transcriber agent instead.
verify    finds each claimed string, case- and line-break-insensitive, and names its page. It refuses a SPARSE source:
          a sparse file finds or misses strings in page headers, so its answers mean nothing.
doi       asks CrossRef what a DOI points to. With --expect, the first author's family name must be on the record:
          a DOI supplied by a language model can be real and point at a different paper.
oa        asks OpenAlex whether an open copy exists. An HTTP 400 is a malformed query, not a negative result: a long
          title is retried cut at its colon. No results is "could not ask", never "no open copy".
manifest  runs the steps above for every row of a manifest table, trusted rows first, then UNVERIFIED rows with the
          DOI check enforced, prints the verification matrix and the VERDICT line, and saves both beside the manifest.

Exit codes: 0 good · 1 the check said no (HTML received, claim not found, wrong paper, no open copy) · 2 usage, or a
target that exists · 3 not usable yet (SPARSE, EMPTY, not a PDF, sparse source) · 4 could not ask (network, a missing
library, no results).
Mutation proof: scripts/acquire_mutations.py
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

MIN_CHARS_PER_PAGE = 200      # a text page yields thousands; a scanned page's header noise about 70
SMALL_PDF_BYTES = 50_000      # a PDF smaller than this is suspicious even with a %PDF header
USER_AGENT = "Research-Toolkit-acquire/1.0"
PAGE_RE = re.compile(r"^=== PAGE (\d+) ===[ \t]*$", re.M)
GAP = "[MATERIAL GAP:"
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s?#\"'<>]+")


class CannotAsk(Exception):
    """The question could not be put: a network error, a missing library, or no answer to read."""


def http_get(url: str, user_agent: str = USER_AGENT, timeout: float = 30) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


# --- fetch -------------------------------------------------------------------------------------------------------

def header_kind(head: bytes) -> str:
    if head.startswith(b"%PDF"):
        return "pdf"
    if head.lstrip(b"\xef\xbb\xbf \t\r\n").startswith(b"<"):
        return "html"
    return "other"


def fetch(url: str, target: Path, user_agent: str = USER_AGENT) -> tuple[int, str]:
    if target.exists():
        return 2, f"REFUSED: {target} exists; an acquisition never overwrites a file"
    try:
        data = http_get(url, user_agent)
    except (urllib.error.URLError, OSError, ValueError) as e:
        return 4, f"UNCHECKED: could not download {url}: {e}"
    if target.suffix.lower() != ".pdf":
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return 0, f"saved {len(data)} bytes to {target}; not a PDF target, so extract it with /readable"
    kind = header_kind(data[:64])
    if kind == "html":
        return 1, ("REFUSED: downloaded HTML, not a PDF. The source is likely bot-blocked or paywalled; nothing was "
                   "saved. Check the known bot-blocked sources in /acquire before retrying.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    if kind == "other":
        return 3, (f"NOT A PDF: the first bytes are {data[:4]!r}, not %PDF. Kept at {target} for inspection; do not "
                   "extract it until it is identified.")
    note = f"saved {len(data)} bytes to {target}, %PDF header confirmed"
    if len(data) < SMALL_PDF_BYTES:
        note += f"; WARN: under {SMALL_PDF_BYTES // 1000} KB, so open it and confirm it is the paper"
    return 0, note


# --- extract -----------------------------------------------------------------------------------------------------

def txt_path(pdf: Path) -> Path:
    return pdf.with_suffix(".txt")   # paper.pdf -> paper.txt, never paper.pdf.txt


def classify(page_texts: list[str]) -> tuple[str, float]:
    n = max(len(page_texts), 1)
    chars = sum(len(t.strip()) for t in page_texts)
    if chars == 0:
        return "EMPTY", 0.0
    per = chars / n
    return ("OK" if per >= MIN_CHARS_PER_PAGE else "SPARSE"), per


def assemble(page_texts: list[str], source_name: str) -> str:
    out = []
    for i, t in enumerate(page_texts, 1):
        body = t.strip() or f"{GAP} no text extracted from page {i}; it may be blank or an image. Source PDF: {source_name}.]"
        out.append(f"=== PAGE {i} ===\n{body}\n")
    return "".join(out)


def _pymupdf():
    try:
        import pymupdf
        return pymupdf
    except ImportError:
        try:
            import fitz
            return fitz
        except ImportError:
            return None


def read_pages(pdf: Path) -> tuple[list[str], str]:
    texts: list[str] = []
    try:
        from pypdf import PdfReader
        texts = [p.extract_text() or "" for p in PdfReader(str(pdf)).pages]
        if any(t.strip() for t in texts):
            return texts, "pypdf"
    except ImportError:
        pass
    except Exception:  # noqa: BLE001 -- a PDF pypdf cannot parse goes to the next reader
        texts = []
    mu = _pymupdf()
    if mu is None:
        if texts:
            return texts, "pypdf"
        raise CannotAsk("neither pypdf nor PyMuPDF is installed: pip install pypdf PyMuPDF")
    with mu.open(str(pdf)) as doc:
        return [doc[i].get_text() for i in range(len(doc))], "pymupdf"


def render_pages(pdf: Path, out_dir: Path | None) -> list[Path]:
    mu = _pymupdf()
    if mu is None:
        raise CannotAsk("rendering pages needs PyMuPDF: pip install PyMuPDF")
    out_dir = out_dir or Path(tempfile.mkdtemp(prefix=f"acquire_{re.sub(r'[^A-Za-z0-9]+', '_', pdf.stem)}_"))
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    with mu.open(str(pdf)) as doc:
        for i in range(len(doc)):
            p = out_dir / f"p{i + 1}.png"
            doc[i].get_pixmap(dpi=150).save(str(p))
            paths.append(p)
    return paths


def extract(pdf: Path, renders: Path | None = None) -> tuple[int, str]:
    out = txt_path(pdf)
    if out.exists():
        status, per = source_density(out.read_text(encoding="utf-8", errors="replace"))
        return (0 if status == "OK" else 3), f"SKIP: {out} exists ({status}, {per:.0f} chars/page); it was not re-extracted"
    try:
        pages, method = read_pages(pdf)
    except CannotAsk as e:
        return 4, f"UNCHECKED: {e}"
    status, per = classify(pages)
    if status == "OK":
        text = assemble(pages, pdf.name)
        out.write_text(text, encoding="utf-8")
        gaps = sum(1 for t in pages if not t.strip())
        return 0, (f"OK {method}: {len(pages)} pages, {per:.0f} chars/page -> {out}"
                   + (f"; {gaps} page(s) had no text and carry a MATERIAL GAP marker" if gaps else ""))
    try:
        pngs = render_pages(pdf, renders)
        where = f"rendered {len(pngs)} page(s) to {pngs[0].parent}/p*.png" if pngs else "the PDF has no pages"
    except CannotAsk as e:
        where = f"could not render pages: {e}"
    return 3, (f"{status} ({per:.0f} chars/page, under {MIN_CHARS_PER_PAGE}): not acquired, and no .txt was written. "
               f"{where}. Start the transcriber agent on those pages; do not grep or cite this source until it has run.")


# --- verify ------------------------------------------------------------------------------------------------------

def split_pages(text: str) -> list[tuple[str, str]]:
    marks = list(PAGE_RE.finditer(text))
    if not marks:
        return [("?", text)]
    return [(m.group(1), text[m.end():marks[k + 1].start() if k + 1 < len(marks) else len(text)])
            for k, m in enumerate(marks)]


def source_density(text: str) -> tuple[str, float]:
    pages = split_pages(text)
    return classify(["" if GAP in body else body for _, body in pages])


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).replace("−", "-").replace("­", "")
    s = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", s)          # a word hyphenated across a line break
    return re.sub(r"\s+", " ", s).strip().lower()


def find_claim(text: str, claim: str) -> list[tuple[str, str]]:
    want, hits = norm(claim), []
    for page, body in split_pages(text):
        flat = norm(body)
        i = flat.find(want)
        if i >= 0:
            hits.append((page, flat[max(0, i - 60):i + len(want) + 60]))
    return hits


def verify(txt: Path, claims: list[str]) -> tuple[int, list[str]]:
    text = txt.read_text(encoding="utf-8", errors="replace")
    status, per = source_density(text)
    if status != "OK":
        return 3, [f"NOT RUN: {txt} is {status} ({per:.0f} chars/page); a sparse source finds and misses strings in "
                   "page headers, so transcribe it first"]
    gaps = [p for p, body in split_pages(text) if GAP in body]
    lines, missing = [], 0
    for c in claims:
        hits = find_claim(text, c)
        if hits:
            page, ctx = hits[0]
            more = f" (and {len(hits) - 1} more page(s))" if len(hits) > 1 else ""
            lines.append(f'FOUND "{c}" p.{page}{more}: "...{ctx}..."')
        else:
            missing += 1
            why = (f"; page(s) {', '.join(gaps)} could not be read, so it may be there" if gaps
                   else "; a possible hallucination, so log it before anything cites it")
            lines.append(f'NOT FOUND "{c}"{why}')
    return (1 if missing else 0), lines


# --- doi and oa --------------------------------------------------------------------------------------------------

def fold(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch)).lower().strip()


def parse_expect(expect: str) -> tuple[str, int | None]:
    year = re.search(r"\b(1[89]\d\d|20\d\d)\b", expect)
    name = re.split(r"\s+et al\.?|\s*&|\s+and\s+|,|\(", expect.strip(), maxsplit=1)[0].strip()
    return fold(name.split()[-1] if name else ""), int(year.group(1)) if year else None


def doi_record(doi: str, user_agent: str = USER_AGENT) -> dict:
    try:
        msg = json.loads(http_get(f"https://api.crossref.org/works/{urllib.parse.quote(doi)}", user_agent))["message"]
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        raise CannotAsk(f"CrossRef did not answer for {doi}: {e}") from e
    year = (msg.get("issued", {}).get("date-parts") or [[None]])[0][0]
    return {"title": (msg.get("title") or ["<missing>"])[0], "authors": [a.get("family", "?") for a in msg.get("author", [])],
            "year": year}


def doi_check(doi: str, expect: str = "", user_agent: str = USER_AGENT) -> tuple[int, list[str]]:
    try:
        rec = doi_record(doi, user_agent)
    except CannotAsk as e:
        return 4, [f"UNCHECKED: {e}"]
    lines = [f"Title: {rec['title']}", f"Authors: {', '.join(rec['authors'])}", f"Year: {rec['year']}"]
    if not expect:
        return 0, lines + ["(no --expect given: compare the record with the claimed paper yourself)"]
    name, year = parse_expect(expect)
    names = {fold(a) for a in rec["authors"]} | {fold(a).split()[-1] for a in rec["authors"] if a.strip()}
    if not name or name not in names:
        return 1, lines + [f"MISMATCH: '{expect}' claims an author {name or '<none>'} who is not on this record. The DOI "
                           "points at a different paper: correct the manifest row and do not download"]
    if year and rec["year"] and abs(int(rec["year"]) - year) > 1:
        return 1, lines + [f"MISMATCH: '{expect}' claims {year}; the record says {rec['year']}"]
    if year and rec["year"] and int(rec["year"]) != year:
        return 0, lines + [f"MATCH on author; YEAR DIFFERS by one ({year} claimed, {rec['year']} on record): online and "
                           "print years often differ, so check which one the citation uses"]
    return 0, lines + ["MATCH: the claimed first author is on the record" + (" and the year agrees" if year else "")]


def openalex(title: str, user_agent: str = USER_AGENT) -> tuple[int, list[str]]:
    notes = []
    for attempt in ([title, title.split(":")[0].strip()] if ":" in title else [title]):
        url = ("https://api.openalex.org/works?filter=title.search:" + urllib.parse.quote(attempt) + "&per-page=3")
        try:
            results = json.loads(http_get(url, user_agent)).get("results", [])
            break
        except urllib.error.HTTPError as e:
            if e.code != 400:
                return 4, notes + [f"UNCHECKED: OpenAlex returned HTTP {e.code}"]
            notes.append(f"HTTP 400 for '{attempt}': a malformed query, not a negative result"
                         + ("; retrying with the title cut at its colon" if attempt == title and ":" in title else ""))
        except (urllib.error.URLError, OSError, ValueError) as e:
            return 4, notes + [f"UNCHECKED: OpenAlex did not answer: {e}"]
    else:
        return 4, notes + ["UNCHECKED: every form of the query was refused"]
    if not results:
        return 4, notes + ["UNCHECKED: OpenAlex has no record matching that title, which says nothing about an open copy"]
    lines, open_copy = notes, False
    for w in results:
        oa = w.get("open_access") or {}
        open_copy = open_copy or bool(oa.get("is_oa") and oa.get("oa_url"))
        lines += [f"{w.get('publication_year')} | {w.get('title')}", f"   is_oa: {oa.get('is_oa')} | oa_url: {oa.get('oa_url')}",
                  f"   doi  : {w.get('doi')}"]
    if open_copy:
        return 0, lines + ["An open copy exists. is_oa true is not the same as retrievable: some hosts refuse every "
                           "automated request, so one browser click may still be needed"]
    return 1, lines + ["No open copy is recorded: stop hunting and go to the fallback ladder in /acquire"]


# --- manifest ----------------------------------------------------------------------------------------------------

def parse_manifest(text: str) -> list[dict]:
    rows, header = [], None
    for line in text.splitlines():
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            if any("url" in c.lower() for c in cells) and any("target" in c.lower() for c in cells):
                header = [c.lower() for c in cells]
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        row = dict(zip(header, cells))
        get = lambda key: next((v for k, v in row.items() if key in k), "")  # noqa: E731
        claims = [] if get("claim").strip() in ("", "--", "—") else re.findall(r'"([^"]+)"', get("claim"))
        rows.append({"paper": get("paper"), "url": get("url"), "target": get("target"), "claims": claims,
                     "doi_source": get("doi"), "unverified": "unverified" in get("doi").lower()})
    return rows


def run_manifest(manifest: Path, user_agent: str = USER_AGENT, today: dt.date | None = None) -> tuple[int, str]:
    rows = parse_manifest(manifest.read_text(encoding="utf-8"))
    if not rows:
        return 2, f"no manifest table in {manifest}: it needs a header row naming URL and Target path"
    base = manifest.parent
    order = [r for r in rows if not r["unverified"]] + [r for r in rows if r["unverified"]]
    matrix = ["| Paper | Downloaded | Extract status | Claimed figure | Grep result |", "|---|---|---|---|---|"]
    acquired = sparse = notfound = blocked = unv_pass = unv_fail = 0
    for r in order:
        target = Path(r["target"]) if Path(r["target"]).is_absolute() else base / r["target"]
        if r["unverified"]:
            m = DOI_RE.search(r["url"])
            code, lines = doi_check(m.group(0), r["paper"], user_agent) if m else (4, ["no DOI in the URL"])
            if code != 0:
                unv_fail += 1
                blocked += 1
                matrix.append(f"| {r['paper']} | BLOCKED: DOI check: {lines[-1]} | (not run) | | |")
                continue
            unv_pass += 1
        if target.exists():
            dl = "on disk already"
        else:
            code, note = fetch(r["url"], target, user_agent)
            if code != 0:
                blocked += 1
                matrix.append(f"| {r['paper']} | {note} | (not run) | | |")
                continue
            dl = f"OK {target.stat().st_size / 1e6:.1f}MB"
        if target.suffix.lower() != ".pdf":
            blocked += 1
            matrix.append(f"| {r['paper']} | {dl} | not a PDF: run /readable | | |")
            continue
        code, note = extract(target)
        if code != 0:
            sparse += 1
            matrix.append(f"| {r['paper']} | {dl} | {note.split(':')[0]} needs transcription | (blocked) | (not run) |")
            continue
        acquired += 1
        _, per = source_density(txt_path(target).read_text(encoding="utf-8", errors="replace"))
        ext = f"OK ({per:.0f}/pg)"
        if not r["claims"]:
            matrix.append(f"| {r['paper']} | {dl} | {ext} | -- | -- |")
        for c in r["claims"]:
            code, lines = verify(txt_path(target), [c])
            notfound += code == 1
            matrix.append(f"| {r['paper']} | {dl} | {ext} | \"{c}\" | {lines[0]} |")
    n = len(rows)
    verdict = (f"VERDICT: {acquired}/{n} acquired | {sparse} SPARSE/EMPTY (need transcription) | {notfound} grep NOT-FOUND"
               f" | {blocked} blocked")
    unv = sum(r["unverified"] for r in rows)
    lines = matrix + ["", verdict] + ([f"UNVERIFIED rows: {unv_pass} passed the DOI check, {unv_fail} failed or could "
                                        "not be checked"] if unv else [])
    report = base / f"{manifest.stem}_verified_{(today or dt.date.today()).isoformat()}.md"
    k = 2
    while report.exists():
        report = base / f"{manifest.stem}_verified_{(today or dt.date.today()).isoformat()}_{k}.md"
        k += 1
    report.write_text(f"# Verification matrix for {manifest.name}\n\n" + "\n".join(lines) + "\n", encoding="utf-8")
    clean = acquired == n and not notfound
    return (0 if clean else 1), "\n".join(lines) + f"\n\nsaved: {report}"


# --- self-test ---------------------------------------------------------------------------------------------------

def _tiny_pdf(text: str) -> bytes:
    """A one-page PDF whose text pypdf can read, built by hand so the test needs no PDF writer."""
    stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET".encode()
    objs = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    out, offs = bytearray(b"%PDF-1.4\n"), []
    for i, o in enumerate(objs, 1):
        offs.append(len(out))
        out += f"{i} 0 obj\n".encode() + o + b"\nendobj\n"
    xref = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    out += b"".join(f"{o:010d} 00000 n \n".encode() for o in offs)
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    return bytes(out)


def self_test() -> int:
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    g = globals()
    real_get, real_read, real_render = g["http_get"], g["read_pages"], g["render_pages"]
    served: dict = {}

    def fake_get(url, user_agent=USER_AGENT, timeout=30):
        v = served.get(url)
        if v is None:
            for k, val in served.items():
                if url.startswith(k):
                    v = val
                    break
        if isinstance(v, Exception):
            raise v
        if v is None:
            raise urllib.error.URLError("no such host in the test")
        return v

    def http400(url):
        return urllib.error.HTTPError(url, 400, "Bad Request", None, None)

    pdf_bytes = b"%PDF-1.4\n" + b"x" * 60_000
    page_text = "The response rate of 22% was observed across all\nregions in 2023. " * 40
    g["http_get"] = fake_get
    g["render_pages"] = lambda pdf, out_dir=None: [Path(tempfile.gettempdir()) / "p1.png"]
    try:
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            check("a %PDF header is a PDF", header_kind(b"%PDF-1.7 ...") == "pdf")
            check("an HTML page is HTML, with leading space or a byte-order mark",
                  header_kind(b"<!DOCTYPE html>") == header_kind(b"  \n<html>") == header_kind(b"\xef\xbb\xbf<html>") == "html")
            check("a zip is neither", header_kind(b"PK\x03\x04") == "other")
            check("paper.pdf extracts to paper.txt, never paper.pdf.txt",
                  txt_path(Path("a/Paper.PDF")) == Path("a/Paper.txt") and txt_path(Path("a/b.c.pdf")) == Path("a/b.c.txt"))

            served["https://x.test/good.pdf"] = pdf_bytes
            code, _ = fetch("https://x.test/good.pdf", d / "good.pdf")
            check("positive control: a PDF is saved, exit 0", code == 0 and (d / "good.pdf").read_bytes() == pdf_bytes)
            served["https://x.test/block.pdf"] = b"<html><body>Are you a robot?</body></html>"
            code, note = fetch("https://x.test/block.pdf", d / "block.pdf")
            check("HTML in place of a PDF is refused, exit 1, and nothing is left on disk",
                  code == 1 and not (d / "block.pdf").exists() and "HTML" in note)
            served["https://x.test/odd.pdf"] = b"PK\x03\x04zipdata"
            code, _ = fetch("https://x.test/odd.pdf", d / "odd.pdf")
            check("a file that is neither PDF nor HTML is kept for inspection, exit 3", code == 3 and (d / "odd.pdf").exists())
            (d / "keep.pdf").write_bytes(b"%PDF original")
            code, _ = fetch("https://x.test/good.pdf", d / "keep.pdf")
            check("an existing target is refused, exit 2, and left untouched",
                  code == 2 and (d / "keep.pdf").read_bytes() == b"%PDF original")
            served["https://x.test/small.pdf"] = b"%PDF-1.4 tiny"
            code, note = fetch("https://x.test/small.pdf", d / "small.pdf")
            check("a PDF under 50 KB is saved with a warning", code == 0 and "WARN" in note)
            code, _ = fetch("https://x.test/absent.pdf", d / "absent.pdf")
            check("a download that fails is exit 4, never a pass", code == 4 and not (d / "absent.pdf").exists())

            check("positive control: thousands of characters a page is OK", classify([page_text] * 3)[0] == "OK")
            check("71 characters a page (scanned-page header noise) is SPARSE", classify(["x" * 71] * 5)[0] == "SPARSE")
            check("exactly 200 characters a page passes the density gate", classify(["x" * 200] * 2)[0] == "OK")
            check("199 characters a page does not", classify(["x" * 199] * 2)[0] == "SPARSE")
            check("no text at all is EMPTY", classify(["", " \n"])[0] == "EMPTY")

            g["read_pages"] = lambda pdf: ([page_text, ""], "pypdf")
            (d / "text.pdf").write_bytes(pdf_bytes)
            code, note = extract(d / "text.pdf")
            body = (d / "text.txt").read_text() if (d / "text.txt").exists() else ""
            check("a text PDF writes paper.txt with a header for every page, exit 0",
                  code == 0 and "=== PAGE 1 ===" in body and "=== PAGE 2 ===" in body)
            check("a page with no text carries a MATERIAL GAP marker, never silence", f"{GAP} no text extracted from page 2" in body)
            g["read_pages"] = lambda pdf: (["Journal of X  12"] * 4, "pypdf")
            (d / "scan.pdf").write_bytes(pdf_bytes)
            code, note = extract(d / "scan.pdf")
            check("a SPARSE PDF writes no .txt and hands its pages to the transcriber, exit 3",
                  code == 3 and not (d / "scan.txt").exists() and "transcriber" in note)
            g["read_pages"] = lambda pdf: (["", ""], "pymupdf")
            (d / "image.pdf").write_bytes(pdf_bytes)
            code, note = extract(d / "image.pdf")
            check("an image-only PDF is EMPTY, writes no .txt, exit 3",
                  code == 3 and not (d / "image.txt").exists() and note.startswith("EMPTY"))
            g["read_pages"] = real_read

            code, lines = verify(d / "text.txt", ["response rate of 22%"])
            check("positive control: a claim on the page is FOUND with its page", code == 0 and lines[0].startswith('FOUND "response rate of 22%" p.1'))
            code, lines = verify(d / "text.txt", ["observed across all regions"])
            check("a claim wrapped across a line break is still found", code == 0)
            code, lines = verify(d / "text.txt", ["RESPONSE RATE OF 22%"])
            check("matching ignores case", code == 0)
            code, lines = verify(d / "text.txt", ["response rate of 23.4%"])
            check("a claim that is not there is NOT FOUND, exit 1, and names the unread page",
                  code == 1 and lines[0].startswith("NOT FOUND") and "page(s) 2 could not be read" in lines[0])
            (d / "hy.txt").write_text("=== PAGE 14 ===\n" + "filler words " * 30 + "a hallu-\ncination rate of 9%\n")
            code, lines = verify(d / "hy.txt", ["hallucination rate of 9%"])
            check("a word hyphenated across a line break is found, on page 14", code == 0 and " p.14" in lines[0])
            (d / "sparse.txt").write_text("=== PAGE 1 ===\nJournal 22%\n=== PAGE 2 ===\nJournal 22%\n")
            code, lines = verify(d / "sparse.txt", ["22%"])
            check("a sparse source is refused, exit 3, even when the string is in its header", code == 3 and "NOT RUN" in lines[0])

            check("'Konishi et al. (2023)' parses to a family name and a year", parse_expect("Konishi et al. (2023)") == ("konishi", 2023))
            check("'Borkotokey, Kumar & Sarangi (2015)' parses to the first author", parse_expect("Borkotokey, Kumar & Sarangi (2015)") == ("borkotokey", 2015))
            cr = "https://api.crossref.org/works/"
            served[cr + "10.1016/j.test.2014.12.023"] = json.dumps({"message": {"title": ["Fair allocation"], "author": [{"family": "Menegatti"}],
                                                            "issued": {"date-parts": [[2015]]}}}).encode()
            code, lines = doi_check("10.1016/j.test.2014.12.023", "Borkotokey, Kumar & Sarangi (2015)")
            check("a DOI that points at a different paper is a MISMATCH, exit 1", code == 1 and "MISMATCH" in lines[-1])
            code, lines = doi_check("10.1016/j.test.2014.12.023", "Menegatti (2015)")
            check("positive control: the right first author and year is a MATCH, exit 0", code == 0 and lines[-1].startswith("MATCH"))
            code, lines = doi_check("10.1016/j.test.2014.12.023", "Menegatti (2014)")
            check("a year off by one still matches, and says so", code == 0 and "YEAR DIFFERS" in lines[-1])
            code, lines = doi_check("10.1016/j.test.2014.12.023", "Menegatti (2011)")
            check("a year off by more than one is a MISMATCH", code == 1)
            check("an accented family name matches its plain form", fold("Ménégatti") == "menegatti")
            served[cr + "10.1016/j.test.2020.1"] = json.dumps({"message": {"title": ["T"], "author": [{"family": "van der Berg"}],
                                                                          "issued": {"date-parts": [[2020]]}}}).encode()
            check("a family name with a particle matches its last word",
                  doi_check("10.1016/j.test.2020.1", "Berg et al. (2020)")[0] == 0)
            code, lines = doi_check("10.9999/none", "Anyone (2020)")
            check("CrossRef not answering is exit 4, never a match", code == 4 and lines[0].startswith("UNCHECKED"))

            oa = "https://api.openalex.org/works?filter=title.search:"
            long_t = "Sourcing Under Supplier Responsibility Risk: The Effects of Certification"
            served[oa + urllib.parse.quote(long_t)] = http400(oa)
            served[oa + urllib.parse.quote("Sourcing Under Supplier Responsibility Risk")] = json.dumps({"results": [
                {"publication_year": 2019, "title": "Sourcing Under Supplier Responsibility Risk",
                 "open_access": {"is_oa": True, "oa_url": "https://preprints.test/1"}, "doi": None}]}).encode()
            code, lines = openalex(long_t)
            check("an HTTP 400 is retried with the title cut at its colon, and found", code == 0 and "malformed query" in lines[0])
            served[oa + urllib.parse.quote("Closed Paper")] = json.dumps({"results": [
                {"publication_year": 2001, "title": "Closed Paper", "open_access": {"is_oa": False, "oa_url": None}}]}).encode()
            code, lines = openalex("Closed Paper")
            check("no open copy is exit 1 and points at the fallback ladder", code == 1 and "fallback ladder" in lines[-1])
            served[oa + urllib.parse.quote("Unknown Paper")] = json.dumps({"results": []}).encode()
            code, lines = openalex("Unknown Paper")
            check("no results is exit 4 (could not ask), never 'no open copy'", code == 4)
            served[oa + urllib.parse.quote("No Colon Here")] = http400(oa)
            code, lines = openalex("No Colon Here")
            check("an HTTP 400 with nothing to cut is exit 4", code == 4)

            mdir = d / "m"
            mdir.mkdir()
            served["https://pub.test/a.pdf"] = pdf_bytes
            served["https://doi.org/10.1016/j.test.2014.12.023"] = pdf_bytes
            g["read_pages"] = lambda pdf: ([page_text], "pypdf")
            manifest = mdir / "manifest.md"
            manifest.write_text(
                "| Paper | URL | Target path | Claimed figures | DOI source |\n|---|---|---|---|---|\n"
                '| Konishi et al. (2023) | https://pub.test/a.pdf | papers/a.pdf | "22%", "99.9%" | Direct from publisher |\n'
                "| Borkotokey, Kumar & Sarangi (2015) | https://doi.org/10.1016/j.test.2014.12.023 | papers/b.pdf | -- | Gemini-claimed (UNVERIFIED) |\n")
            rows = parse_manifest(manifest.read_text())
            check("the manifest table parses into rows with their claims", len(rows) == 2 and rows[0]["claims"] == ["22%", "99.9%"]
                  and rows[1]["unverified"] and rows[1]["claims"] == [])
            code, out = run_manifest(manifest, today=dt.date(2026, 10, 20))
            check("an UNVERIFIED row whose DOI names another paper is BLOCKED and never downloaded",
                  "BLOCKED" in out and not (mdir / "papers" / "b.pdf").exists())
            check("positive control: the trusted row is downloaded, extracted and grep-checked",
                  (mdir / "papers" / "a.txt").exists() and 'FOUND "22%"' in out)
            check("the matrix carries the NOT FOUND claim and the VERDICT line counts it",
                  'NOT FOUND "99.9%"' in out and "VERDICT: 1/2 acquired | 0 SPARSE/EMPTY (need transcription) | 1 grep NOT-FOUND | 1 blocked" in out)
            check("a manifest that is not clean is exit 1", code == 1)
            check("the matrix is saved beside the manifest", (mdir / "manifest_verified_2026-10-20.md").exists())
            code, _ = run_manifest(manifest, today=dt.date(2026, 10, 20))
            check("a second run never overwrites the first report", (mdir / "manifest_verified_2026-10-20_2.md").exists())
            manifest.write_text(
                "| Paper | URL | Target path | Claimed figures | DOI source |\n|---|---|---|---|---|\n"
                '| Konishi et al. (2023) | https://pub.test/a.pdf | papers/a.pdf | "22%" | Direct from publisher |\n')
            code, out = run_manifest(manifest)
            check("positive control: a clean manifest is exit 0", code == 0 and "VERDICT: 1/1 acquired" in out)
            manifest.write_text(
                "| Paper | URL | Target path | Claimed figures | DOI source |\n|---|---|---|---|---|\n"
                '| Konishi et al. (2023) | https://pub.test/a.pdf | papers/a.pdf | "99.9%" | Direct from publisher |\n')
            code, out = run_manifest(manifest)
            check("every row acquired with one claim NOT FOUND is still exit 1", code == 1 and "VERDICT: 1/1 acquired" in out)
            g["read_pages"] = real_read
            (mdir / "empty.md").write_text("no table here\n")
            check("a file with no manifest table is exit 2", run_manifest(mdir / "empty.md")[0] == 2)

            try:
                import pypdf  # noqa: F401
                have_pypdf = True
            except ImportError:
                have_pypdf = False
            if have_pypdf:
                (d / "real.pdf").write_bytes(_tiny_pdf("Observed rate 14.41 percent " * 12))
                code, note = extract(d / "real.pdf")
                check("end to end: a real PDF read by pypdf is OK and its figure is FOUND",
                      code == 0 and verify(d / "real.txt", ["rate 14.41 percent"])[0] == 0)
            else:
                print("  SKIP end to end with a real PDF: pypdf is not installed")
    finally:
        g["http_get"], g["read_pages"], g["render_pages"] = real_get, real_read, real_render
    print(f"acquire self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--user-agent", default=USER_AGENT, help='some hosts require "Your Name you@example.org"')
    sub = ap.add_subparsers(dest="cmd")
    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("target")
    e = sub.add_parser("extract")
    e.add_argument("pdf")
    e.add_argument("--renders", default="", help="folder for page images (default: a new temporary folder)")
    v = sub.add_parser("verify")
    v.add_argument("txt")
    v.add_argument("claims", nargs="+")
    o = sub.add_parser("doi")
    o.add_argument("doi")
    o.add_argument("--expect", default="", help='the claimed paper, e.g. "Author et al. (2023)"')
    a = sub.add_parser("oa")
    a.add_argument("title")
    m = sub.add_parser("manifest")
    m.add_argument("manifest")
    args = ap.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.cmd == "fetch":
        code, note = fetch(args.url, Path(args.target), args.user_agent)
        print(note)
        return code
    if args.cmd == "extract":
        code, note = extract(Path(args.pdf), Path(args.renders) if args.renders else None)
        print(note)
        return code
    if args.cmd in ("verify", "doi", "oa"):
        code, lines = (verify(Path(args.txt), args.claims) if args.cmd == "verify"
                       else doi_check(args.doi, args.expect, args.user_agent) if args.cmd == "doi"
                       else openalex(args.title, args.user_agent))
        print("\n".join(lines))
        return code
    if args.cmd == "manifest":
        code, out = run_manifest(Path(args.manifest), args.user_agent)
        print(out)
        return code
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
