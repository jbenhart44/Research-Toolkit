# /startup — Session Startup Briefing

You just opened your terminal and can't remember where you left off yesterday.

## When you need this

- Starting a work session after any gap — overnight, a weekend, or longer
- You're juggling multiple projects and need to know which one needs attention
- You want to know what's blocked and what the next concrete action is

## What it does — and what it won't

`/startup` reads your recent daily summaries and produces a prioritized briefing: what each workstream is doing, where it left off, what the next step is, and whether anything is blocked. It also shows git status and any running processes.

**Prerequisite**: `startup` reads summaries written by `/dailysummary`. If you haven't been writing daily summaries, `/startup` falls back to `git log` and open file context — useful, but not the full picture. Build the `/dailysummary` habit at the end of each session first.

## Worked example

Dario opens his laptop Tuesday morning after a three-day weekend. He was working on two things — a wage regression and a lit review — and isn't sure which was blocked.

```
/startup
```

`/startup` reads the last three daily summaries and returns: *Wage Regression — left off after adding state fixed effects, next step is placebo tests. Lit review — blocked, waiting on Autor (2014) to be extracted. Run `/readable papers/autor2014.pdf` to unblock.* It also surfaces 3 uncommitted files from Thursday's session.

## Try it

```
/startup
```

> *Plan to run `/dailysummary` at the end of this session — that's what makes the next `/startup` useful.*
