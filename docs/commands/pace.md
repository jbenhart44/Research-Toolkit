# /pace — Parallel Agent Consensus Engine

You need a verified deliverable — not just an answer, but one that's been independently checked.

## When you need this

- Writing a methods section you'll defend in front of a committee
- Verifying that a numerical claim in your paper is arithmetically correct
- Any task where an error would be hard to catch without a second opinion

## What it does — and what it won't

`/pace` routes your task through two independent agents (Players A and B) who work without seeing each other's output. Each is reviewed by a Coach. A Cross-Reviewer then compares both teams. You get a consolidated result that explicitly surfaces where the two teams agreed (high confidence) and where they diverged (genuine uncertainty).

**Note**: `/pace` runs 5 agents and produces substantial output — best suited for tasks where correctness matters enough to justify the cost. For advisory questions with no single correct answer, `/coa` is a better fit.

## Worked example

Maya has written a methods section claiming her difference-in-differences analysis achieves a "12% reduction in demographic parity gap." She wants the arithmetic and experimental design verified before submitting to a workshop.

```
/pace Verify the DiD methods section in dissertation/methods.qmd — check every numerical claim against the evaluation logs in results/
```

Players A and B independently verify each claim. Player B catches that the "12%" is computed on the test split but the paper's Figure 3 shows the validation split — an inconsistency. The Cross-Reviewer flags it as the highest-priority finding. Maya gets a consolidated report: 2 verified claims, 1 discrepancy requiring correction, 1 claim needing a confidence interval.

## Try it

```
/pace Verify [claim] against [source]
/pace Write and cross-check [deliverable]
```

> *Run `/dailysummary` after a PACE run to capture the findings — convergence results and any discrepancies resolved are decision context worth preserving.*
