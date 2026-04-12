# Quick Start: Your First Evidence-Producing Session

**Time**: 5 minutes to first useful output

---

## Step 1: Pick a Real Task

Don't test with a toy problem. Pick something you're actually working on today:
- A document that needs fact-checking
- A design decision with tradeoffs
- A code review that needs a second pair of eyes
- A research question with multiple valid perspectives

The tools work best on real tasks because they're designed to catch real errors.

## Step 2: Run /pace

In your Claude Code terminal:

```
/pace Review this analysis for errors: [paste your task here]
```

PACE spawns two independent agents, has each coached, then cross-compares. You'll see:
- Where both agents agree (high confidence)
- Where they disagree (this is where errors hide)
- What the coaches caught that the players missed

**What to expect**: PACE typically runs 3-5 minutes. The output includes a convergence/divergence table. Your first run will also produce a **run report** automatically — a structured evidence file that captures what happened.

## Step 3: Check Your Evidence

After PACE completes, look at:
- The run report file it created (path shown at the end of output)
- The CSV index row appended to `evidence/run_log.csv`

That's it. Your first evidence record exists. Every future PACE and CoA run adds to it automatically.

---

## What Comes Next

| After N runs... | You can do... |
|-----------------|---------------|
| 1 | See your first run report |
| 5 | Run `/improve --tools` for your first aggregate statistics |
| 10 | Meaningful convergence trends become visible |
| 20+ | Publishable evidence base (cite specific metrics with provenance) |

## Recommended Adoption Order

1. **Start with /pace** — lowest barrier, highest immediate value (error catching)
2. **Add /dailysummary + /startup** — session continuity (prevents "where was I?" syndrome)
3. **Add /coa** for strategic decisions — when you face a choice with multiple valid perspectives
4. **Add /pcv** for structured planning on complex multi-component projects

---

## Calibration Tasks (Optional)

Want to see how the tools perform on problems with known answers? Try these:

### PACE Calibration
```
/pace Review this calculation: "A project has 3 tasks taking 2, 4, and 3 days respectively. Tasks 1 and 2 are parallel, Task 3 depends on both. The critical path is 2+3 = 5 days. The project can be completed in 5 days with 2 workers."
```
*Known issues*: The critical path is actually max(2,4)+3 = 7 days, not 5. PACE should catch the max() error.

### CoA Calibration
```
/coa --quick Should a new PhD student focus their first year on coursework or on starting research immediately?
```
*Known answer*: There is no single correct answer — this is a genuine tradeoff. A good CoA session surfaces the considerations that matter (funding timeline, advisor expectations, course prerequisites for research, etc.) without falsely converging on one side.

---

## Baseline Benchmarks (from author's usage, 40+ sessions)

| Tool | Metric | Author's Baseline |
|------|--------|------------------|
| PACE | Convergence rate | 70-90% on well-specified tasks |
| PACE | Error catches per run | 0.5-2.0 (higher on numerical/code tasks) |
| CoA | Council independence | Contamination tests passed (3/3) |
| CoA | Perspective diversity | High differentiation when personas are well-defined |

These are reference points, not targets. Your results will vary based on task type and domain.
