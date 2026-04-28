# /readable — Document to Text Extraction

You have 30 PDFs you need to grep-search for specific figures before you can write your literature review.

## When you need this

- You want to batch-extract an entire folder of papers into searchable `.txt` files for citation verification with `/audit`
- Some of your PDFs are scanned images with no text layer and you need OCR
- You want persistent `.txt` files on disk that you can grep across many papers at once

## What it does — and what it won't

`/readable` extracts text from PDFs, Word docs, and HTML files and saves `.txt` files alongside the originals. For image-based scanned PDFs, it applies visual OCR — slower, but produces a readable result. It skips files that already have a `.txt` (run it safely on a folder without re-processing).

**Note**: Claude Code's built-in Read tool can render individual PDFs natively — you don't need `/readable` just to read one paper. Use `/readable` when you need batch processing, image-based OCR, or persistent `.txt` files for downstream grep-based citation work.

**Performance**: Directory mode processes files sequentially. A folder of 30 text-based PDFs takes a few minutes; image-based scanned PDFs take significantly longer per file. Run it before you need the results, not right before a deadline.

## Worked example

Dario is writing his labor economics dissertation chapter. He's downloaded 31 papers on minimum wage elasticity — many of them older scanned journals. He needs to search across all of them for specific coefficient values.

```
/readable "papers/minimum_wage_elasticity/"
```

`/readable` processes all 31 PDFs. For the 8 image-based scanned journals, it runs OCR and flags them separately for quality review. The 23 natively digital papers extract cleanly with page headers intact. All `.txt` files are now on disk, ready for `/audit` to grep-verify every number he cites.

## Try it

```
/readable papers/one_paper.pdf
/readable papers/
/readable papers/long_paper.pdf 1-40
```

> *After extraction: run `/audit` on any document that cites figures from these papers — now that the source text is on disk, every number can be grep-verified before you write it.*
