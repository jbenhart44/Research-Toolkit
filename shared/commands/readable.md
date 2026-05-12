---
allowed-tools: Bash(python3:*), Bash(pip:*), Read, Write, Glob, Agent
description: Extract text from PDF, Word (.docx), or HTML files. Supports single files or entire directories. Saves .txt files alongside originals.
---

# /readable — Document to Text Extraction

> **When to use**: You need persistent, grep-searchable `.txt` extractions from PDFs, Word docs, or HTML files — for batch citation verification with `/audit`, or for files where you need to search across many documents at once. Note: Claude Code's built-in Read tool *can* render individual PDFs natively; `/readable` adds value for batch processing, image-based OCR, and producing `.txt` files that persist on disk for later grep-based citation work.

Extract text from PDF, Word (.docx), or HTML files. Supports single files or entire directories. Saves .txt files alongside the originals for easy reading and grep-based citation verification.

## Usage

```
/readable <path>              — single file or entire directory
/readable <path> [page_range] — PDF with page range (e.g., 1-20)
```

Examples:
- `/readable papers/some_paper.pdf` — single PDF
- `/readable papers/` — ALL supported files in directory
- `/readable some_paper.pdf 1-20` — first 20 pages only
- `/readable documents/proposal.docx` — Word document
- `/readable reports/summary.html` — HTML file

## Supported Formats
- **PDF** (.pdf) — via `pypdf` (text-based) or `fitz`/PyMuPDF (image-based fallback with page rendering)
- **Word** (.docx) — via `python-docx`
- **HTML** (.html, .htm) — via `BeautifulSoup` (strips scripts, styles, nav, headers, footers)

## Behavior

### Single File Mode
When given a file path, extract text and save as `<filename>.txt` in the same directory as the source file. Report the output path and character count.

### Directory Mode
When given a directory path, find ALL `.pdf`, `.docx`, `.doc`, `.html`, and `.htm` files in that directory. For each:
1. Check if a `.txt` version already exists — skip if so (report "SKIP")
2. Extract text using the appropriate method
3. Save as `<original_name>.txt` in the same directory
4. Report: filename, method used, character count, or reason for failure

### Image-Based PDFs
Some PDFs contain scanned images with no extractable text (e.g., screenshots of web pages, scanned papers). When `pypdf` and `fitz` both return empty text:
1. Render each page as a high-DPI PNG image (200 DPI) and save to `/tmp/<filename_slug>_p<N>.png`
2. Report: "IMAGE-BASED — rendered N pages as PNG to /tmp/<slug>_p*.png"
3. **Then spawn a background subagent** that reads each PNG image using the Read tool (which supports visual image reading) and transcribes the FULL text of every page into a .txt file alongside the PDF
4. The subagent writes `<filename>.txt` in the same directory as the PDF with `=== PAGE N ===` headers
5. Tables should be transcribed in markdown table format
6. Figure/chart images noted as `[FIGURE: brief description]`
7. Report when transcription is complete: "Transcription complete: <filename>.txt (<N> chars)"

**This is the critical difference from standard extraction**: image-based PDFs require VISUAL READING of rendered pages, not text extraction. The subagent uses Claude's multimodal capability to read the images and produce text. This takes longer but produces a complete, readable .txt file that can be searched and cited.

### HTML Extraction
Strip all `<script>`, `<style>`, `<nav>`, `<header>`, `<footer>` tags before extracting text. Use `get_text(separator='\n', strip=True)` for clean output.

### Typed extraction-gap markers (v1.7 — upstream side of the citation pipeline)

When a page cannot be extracted to readable text — pypdf returns empty for that page AND the fitz fallback returns empty AND the image-render visual-subagent path also fails (encoding error, corrupt page, image too low-resolution to OCR, table that did not transcribe cleanly) — the `.txt` MUST NOT omit the page silently and MUST NOT approximate. Instead, emit an explicit typed gap marker at the corresponding `=== PAGE N ===` boundary in the output file:

```
=== PAGE 7 ===
[MATERIAL GAP: extraction failure on page 7 — <one-line reason, e.g., "image-only page; OCR returned 12 non-printable characters"; "table render contains overlapping cells the subagent could not disambiguate"; "page contains scanned handwriting"; "encoding errors prevented decode">. Source PDF: <relative path>.]
```

The marker rules:

- **One marker per failing page.** Never collapse multiple failed pages into one marker — each page that could not be read gets its own line with its own reason. Downstream consumers (`/audit`) need to know which page boundary the gap occupies.
- **Reason is mandatory.** A bare `[MATERIAL GAP]` with no reason is a defect; future maintainers and downstream `/audit` consumers cannot distinguish "image-only page" from "encoding error" from "subagent ran out of context" without it. The reason should be one line, plain English, no jargon.
- **The marker is the page content for that page** — do not also write best-guess approximated text. Plausible-looking filler from a failed OCR is exactly the failure mode the marker prevents.
- **Page-render fallback PNGs (when produced) remain on disk** at the standard `/tmp/<slug>_p<N>.png` path. The marker may reference the PNG path so the author can inspect manually.

Why this rule exists: when `/audit` later greps the extracted `.txt` for a cited number, a silent page-skip is indistinguishable from "the number is genuinely not in the source." That false-negative is the upstream-side analog of the silent-fabrication problem the citation pipeline exists to prevent. Typed gap markers make the failure mode greppable: `/audit` can distinguish "page extracted, number not there" (genuine NOT FOUND) from "page failed to extract, number may or may not be there" (new GAP-IN-SOURCE status — see `/audit` command for downstream handling).

## Output Location
- `.txt` files are saved **in the same directory as the source file**
- Image renders (for image-based PDFs) go to `/tmp/` as PNG files
- The command reports what was created so you can Read the outputs

## Why This Exists
- Some environments do not have `poppler-utils` installed (needed by the Read tool for PDFs)
- Installing system packages may require elevated permissions
- `pypdf`, `python-docx`, and `beautifulsoup4` are pure Python libraries — no system dependencies
- Directory mode enables batch conversion for citation verification workflows (`/readable` → `/audit`)
- Image-based PDF handling ensures no paper is unreadable

## Dependencies
- `pypdf` — `pip install pypdf`
- `python-docx` — `pip install python-docx`
- `beautifulsoup4` — `pip install beautifulsoup4`
- `PyMuPDF` (fitz) — `pip install PyMuPDF`
- Python 3

## Install (if needed)
```bash
pip install pypdf python-docx beautifulsoup4 PyMuPDF
```

If your environment requires bypassing system package restrictions:
```bash
pip install --break-system-packages pypdf python-docx beautifulsoup4 PyMuPDF
```

> **What next?** If `.txt` files were just extracted, run `/audit` on any document that cites figures from these papers — now that the source text is on disk, every number can be grep-verified before you write it.

$ARGUMENTS
