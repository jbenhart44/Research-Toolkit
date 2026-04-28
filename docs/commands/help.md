# /help — Socratic Triage

You've installed 13 commands and you have no idea which one to run first.

## When you need this

- You're new to the toolkit and stuck choosing between commands that sound similar
- You have a situation in mind but aren't sure which command fits
- It's late, you're stuck, and you want a recommendation not a manual

## What it does — and what it won't

`/help` asks zero or one clarifying question, then recommends 1–3 toolkit commands for your situation. It also tells you which commands are NOT what you need right now — reducing the paradox of choice. It does not execute anything — you run the recommended command yourself.

**Status**: `/help` is experimental (v0.2). It may be removed by end of 2026 if adoption signals are low. Safe to use, but treat recommendations as a starting point, not gospel.

## Worked example

Maya is a first-year PhD student who just installed the toolkit. She has 15 PDFs she downloaded today and needs to cite figures from them in her chapter next week.

```
/help I have 15 PDFs I downloaded today and I need to cite figures from them in my chapter — where do I start?
```

`/help` returns: *Start with `/readable "papers/"` to extract text from all 15 PDFs. Then run `/audit "chapter3.qmd"` to verify every figure you cite against the source. Skip `/review` for now — that's for understanding a paper's argument, not verifying citations.* Two commands, one skip, no manual needed.

## Try it

```
/help [describe your situation in one line]
/help I'm not sure which command to use for [situation]
```
