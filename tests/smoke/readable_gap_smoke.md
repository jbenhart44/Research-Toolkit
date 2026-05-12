# /readable typed-gap-marker Smoke Test Fixture

**Purpose**: Exercise `/readable`'s typed extraction-gap marker emission (v1.7+) on a multi-page PDF where one page is image-only and OCR-resistant. Confirms the command emits the typed marker rather than silently skipping the page or writing approximated text.

**Usage**: From this directory, run `/readable gap_fixture.pdf`. Expected output: `gap_fixture.txt` containing the readable pages AND an explicit `[MATERIAL GAP: extraction failure on page <N> — <reason>]` line at the failing page boundary.

**Version**: v1.7 (2026-05-12)

---

## Expected Results

| Page | Content type | Expected behavior |
|---|---|---|
| 1 | Standard text | Extracted normally, headed by `=== PAGE 1 ===` |
| 2 | Image-only, OCR-resistant (low-contrast handwritten figure with overlapping lines) | Marker emitted: `[MATERIAL GAP: extraction failure on page 2 — image-only page; OCR returned <N> non-printable characters]` (or similar reason in plain English) |
| 3 | Standard text | Extracted normally, headed by `=== PAGE 3 ===` |

## Success Criteria

- `gap_fixture.txt` exists alongside `gap_fixture.pdf`.
- Pages 1 and 3 are extracted as text content.
- Page 2 is represented by a `[MATERIAL GAP: extraction failure on page 2 — <reason>]` line — NOT silently skipped, NOT approximated.
- The reason is non-empty and human-readable.
- The marker is on its own line at the `=== PAGE 2 ===` boundary, so it can be grepped by page.
- Total runtime: < 60 seconds (excluding image-render fallback latency).

## Downstream check — `/audit` GAP-IN-SOURCE recognition

This fixture also exercises `/audit`'s downstream GAP-IN-SOURCE status. After the typed marker is in place:

```bash
# Create a stub doc that cites the unreadable page
echo "Source X (2024) reports a value of 0.42 on page 2." > stub_doc.md
/audit stub_doc.md --sources ./
```

Expected: the audit reports status **GAP-IN-SOURCE** for the citation (not NOT FOUND), with the extraction-failure reason copied from the marker. If `/audit` reports NOT FOUND, the GAP-IN-SOURCE recognition has regressed and the two failure modes are being conflated.

## Fixture construction

The PDF must be constructed such that:

- Page 1 contains normal extractable text (e.g., a short paragraph).
- Page 2 is image-only with content that resists both `pypdf` (returns empty) and `fitz` (also returns empty) — e.g., a scanned image of low-contrast handwritten content, or a rendered image with intentionally non-OCR-friendly fonts. The image-render visual-subagent fallback should also fail to produce confident text (e.g., the content is genuinely illegible or contains overlapping diagrams).
- Page 3 contains normal extractable text.

A scripted way to construct such a PDF for testing:

```python
# Build gap_fixture.pdf with three pages — text, image-only-illegible, text
# Run once to create the fixture; not part of the smoke test itself.
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("gap_fixture.pdf", pagesize=letter)
c.drawString(72, 720, "Page 1: This is a normal extractable text page.")
c.showPage()
# Page 2: render an image that is intentionally OCR-resistant — e.g., overlapping diagonal lines
c.setStrokeColorRGB(0.5, 0.5, 0.5)
for x in range(72, 540, 8):
    c.line(x, 100, x + 50, 700)
c.showPage()
c.drawString(72, 720, "Page 3: This is a normal extractable text page.")
c.save()
```

(The deliberately ambiguous page-2 content forces the marker path. If your environment's OCR succeeds anyway, increase visual chaos — overlapping handwritten-style strokes, no characters at all — until the OCR cannot produce a confident transcription.)

## Why This Fixture Matters

The typed-gap marker rule is the structural test that distinguishes "page read but value not present" from "page could not be read." Without this smoke test, a regression in which `/readable` silently omits an unreadable page would not be caught until a downstream `/audit` reported NOT FOUND on a value that was actually present in a page the toolkit failed to extract — which is exactly the failure mode the marker rule prevents.

## Running the Test

```bash
# From tests/smoke/ — fixture PDF must be present
/readable gap_fixture.pdf
grep "^\[MATERIAL GAP: extraction failure" gap_fixture.txt
# Expected: at least one line, mentioning page 2 with a non-empty reason
```

A passing run prints the marker line; a failing run prints nothing (silent skip) or prints approximated text from page 2 (plausible filler — the failure mode the rule prevents).
