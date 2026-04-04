---
allowed-tools: Bash(python3:*), Bash(pip:*), Read, Write, Glob, Agent
description: Extract text from PDF, Word (.docx), or HTML files. Supports single files or entire directories. Saves .txt files alongside originals.
---

# /pdftotxt — Document to Text Extraction

> **When to use**: You need to read PDFs, Word documents, or HTML files that Claude Code's built-in Read tool can't render, OR you need to batch-convert an entire directory of papers for citation verification with `/audit`.

Extract text from PDF, Word (.docx), or HTML files. Supports single files or entire directories. Saves .txt files alongside the originals for easy reading and grep-based citation verification.

## Usage

```
/pdftotxt <path>              — single file or entire directory
/pdftotxt <path> [page_range] — PDF with page range (e.g., 1-20)
```

Examples:
- `/pdftotxt papers/some_paper.pdf` — single PDF
- `/pdftotxt papers/` — ALL supported files in directory
- `/pdftotxt some_paper.pdf 1-20` — first 20 pages only
- `/pdftotxt documents/proposal.docx` — Word document
- `/pdftotxt reports/summary.html` — HTML file

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

## Output Location
- `.txt` files are saved **in the same directory as the source file**
- Image renders (for image-based PDFs) go to `/tmp/` as PNG files
- The command reports what was created so you can Read the outputs

## Why This Exists
- Some environments do not have `poppler-utils` installed (needed by the Read tool for PDFs)
- Installing system packages may require elevated permissions
- `pypdf`, `python-docx`, and `beautifulsoup4` are pure Python libraries — no system dependencies
- Directory mode enables batch conversion for citation verification workflows (`/pdftotxt` → `/audit`)
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

$ARGUMENTS
