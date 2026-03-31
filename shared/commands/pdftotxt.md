---
allowed-tools: Bash(python3:*), Bash(pip:*), Read
description: Extract text from PDF or Word (.docx) files using Python. Useful when the Read tool cannot render these formats.
---

# /pdftotxt — Document to Text Extraction

Extract text from PDF or Word (`.docx`) files using Python. Useful when the Read tool cannot render these formats (e.g., poppler not installed, or Word files).

## Usage
`/pdftotxt <path_to_file> [page_range]`

Examples:
- `/pdftotxt papers/some_paper.pdf` — full PDF extraction
- `/pdftotxt papers/some_paper.pdf 1-20` — first 20 pages only
- `/pdftotxt documents/proposal.docx` — full Word document extraction

## Supported Formats
- **PDF** (.pdf) — via `pypdf`
- **Word** (.docx) — via `python-docx`

## How it works

### PDF
```python
from pypdf import PdfReader
reader = PdfReader('<path>')
for i in range(len(reader.pages)):
    text = reader.pages[i].extract_text()
    print(f'--- PAGE {i+1} ---')
    print(text)
```

### Word (.docx)
```python
from docx import Document
doc = Document('<path>')
for para in doc.paragraphs:
    print(para.text)
# Also extracts tables:
for table in doc.tables:
    for row in table.rows:
        print('\t'.join(cell.text for cell in row.cells))
```

## Why this exists
- Some environments do not have `poppler-utils` installed (needed by the Read tool for PDFs)
- Installing system packages may require elevated permissions
- `pypdf` and `python-docx` are pure Python libraries — no system dependencies
- Works on any PDF or Word document without administrator/sudo access

## Implementation
When invoked, detect file type by extension and run the appropriate extractor:

```bash
python3 -c "
import sys, os
path = '$FULL_PATH'
ext = os.path.splitext(path)[1].lower()

if ext == '.pdf':
    from pypdf import PdfReader
    reader = PdfReader(path)
    for i in range(len(reader.pages)):
        text = reader.pages[i].extract_text()
        if text:
            print(f'--- PAGE {i+1} ---')
            print(text)
elif ext in ('.docx', '.doc'):
    from docx import Document
    doc = Document(path)
    for para in doc.paragraphs:
        if para.text.strip():
            print(para.text)
    for table in doc.tables:
        print('--- TABLE ---')
        for row in table.rows:
            print('\t'.join(cell.text for cell in row.cells))
else:
    print(f'Unsupported format: {ext}. Supported: .pdf, .docx')
" > "$PWD/.doc_extract_tmp.txt" 2>&1
```

Then read `$PWD/.doc_extract_tmp.txt` as needed. For large documents, use page ranges (PDF only) to avoid flooding context. The temp file is created in the current working directory for cross-platform compatibility (avoids `/tmp/` issues on Windows/WSL). Delete it after reading.

## Dependencies
- `pypdf` — `pip install pypdf`
- `python-docx` — `pip install python-docx`
- Python 3

## Install (if needed)
```bash
pip install pypdf python-docx
```

If your environment requires bypassing system package restrictions:
```bash
pip install --break-system-packages pypdf python-docx
```

$ARGUMENTS
