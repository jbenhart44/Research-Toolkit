# /coa — Council of Agents

You're deciding between two valid approaches and you've been going back and forth for a week.

## When you need this

- Research design decisions where multiple approaches are genuinely defensible
- Any "should we X or Y?" question where the answer depends on values, tradeoffs, or domain assumptions
- Before committing to an architecture, methodology, or framing that will be hard to reverse

## What it does — and what it won't

`/coa` seats 4–6 specialist agents with distinct expert perspectives, has each independently analyze your question, then synthesizes convergence and divergence through a Chair. You get a structured report showing where experts agree (high confidence) and where they diverge (where the real ambiguity lives).

**Note**: `/coa` produces advisory analysis, not a deliverable. For tasks with a single correct answer that needs verification, `/pace` is a better fit. For focused technical questions, use `/coa --quick` for a faster 3-seat panel.

## Worked example

Priya needs to decide whether to add a Bayesian correction to her differential expression pipeline before her ISMB submission deadline. She's been going back and forth for a week — both choices seem defensible.

```
/coa Should I add a Bayesian prior correction to my DE pipeline before ISMB submission, or submit with the current frequentist method and note the limitation?
```

The Statistician argues the Bayesian correction reduces false discovery rate on sparse cell types — worth it if there's time. The Software Engineer warns that adding it now risks introducing bugs without time for re-validation. The Skeptic notes reviewers will accept the limitation note if Priya can quantify the expected FDR difference. The Chair synthesizes: convergence on "submit now, revise after" — with a specific limitation-note template.

## Try it

```
/coa Should I [option A] or [option B]?
/coa --quick [focused question]
```

> *Run `/dailysummary` after a council session — the Chair synthesis and any DIVERGE findings are decision rationale that's easy to lose if not recorded.*
