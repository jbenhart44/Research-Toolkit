# /quarto — Slide Deck Generator

You have a 48-hour deadline for a lab meeting presentation and you're starting from a pile of notes and paper drafts.

## When you need this

- You need a presentation and have background documents (papers, notes, reports, methods drafts) to build from
- You want a structured RevealJS slide deck without manually scaffolding 20 slides
- You have source material in PDF or Markdown and need a presentable output fast

## What it does — and what it won't

`/quarto` reads your source documents, designs a narrative arc, proposes a slide outline for your approval, then generates a complete Quarto RevealJS `.qmd` file with a companion CSS file. It renders the deck and opens it for review.

**Note**: Two stop-points before any slides are rendered — you approve the outline first, then the full deck. Source documents should be readable text files; run `/readable` on PDFs first if needed. Rendering can fail if text overflows slides — `/quarto` handles CSS adjustments automatically.

## Worked example

Priya is presenting her RNA-seq pipeline at a lab group meeting in 48 hours. She has her methods paper draft and a benchmark comparison table, but no slides.

```
/quarto "20-min lab talk on pseudobulk DE pipeline, read methods/pipeline_draft.md and results/benchmark_comparison.md"
```

`/quarto` reads both files, proposes a 19-slide outline: Title, Motivation (2), Background (2), Pipeline Architecture (3), Benchmark Results (5), Limitations (2), Conclusion (2). Priya approves. It writes `slides.qmd` and `custom.css`, renders, and opens in her browser. The benchmark table is wide — `/quarto` adds an overflow CSS class automatically.

## Try it

```
/quarto "talk description, read source_doc.md"
/quarto "5-slide update, read weekly_summary.md"
```
