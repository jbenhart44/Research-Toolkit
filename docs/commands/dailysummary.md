# /dailysummary — Daily Work Summary

You're about to close your terminal and you know you'll forget what you did today by tomorrow morning.

## When you need this

- End of any work session where you made decisions, ran analyses, or changed files
- Before switching to a different project or taking a break longer than a few hours
- Any time you want a permanent record of what happened and why

## What it does — and what it won't

`/dailysummary` reads your git history and session context, then spawns a Sonnet subagent to write a structured dated summary: what was accomplished, decisions made, files changed, open items, and next steps. It saves to your daily summary folder — the same folder `/startup` reads tomorrow morning.

Three modes: `--full` (heavy session with decisions and code changes), `--quick` (light session, documentation only), `--append-pointer` (mid-session continuation, appends to today's existing summary instead of creating a new file).

## Worked example

Priya just finished a four-hour session rewriting her gene clustering algorithm and running it on two new datasets. She wants a record before closing her terminal.

```
/dailysummary
```

`/dailysummary` reads the git diff and session context, then produces `Daily Summary/2026-04-21_clustering_rewrite.md`: what changed (switched k-means to Leiden clustering), why (benchmark comparison showed 12% improvement on sparse data), next steps (run on TCGA dataset, validate against Chen 2024), and a flag that the distance metric function is duplicated across two scripts — an `/improve` candidate for next session.

## Try it

```
/dailysummary
/dailysummary --quick
```

> *If the summary flagged `/improve` candidates, run `/improve` at the start of your next session to action them while the context is warm.*
