# Using PACE for Grading Consistency

## What PACE Does

PACE (Parallel Agent Consensus Engine) runs a task through two independent "players" (agents A and B), each reviewed by their own "coach" (agents C and D), then cross-compares all four outputs for convergence. It's verification through redundancy.

## Why Use It for Grading

- **Catches arithmetic errors.** When grading 30+ assignments with rubrics involving multiple criteria and point calculations, single-pass grading misses errors. PACE catches them.
- **Surfaces rubric ambiguity.** If Player A scores a submission 85 and Player B scores it 72, the rubric is ambiguous for that submission — and you know exactly where to look.
- **Consistent across the stack.** PACE applies the same rubric with the same attention to the first and last paper in the stack.

## Example: Grading a Homework Set

### Step 1: Define the Rubric

Create a clear rubric document:

```markdown
## HW3 Grading Rubric (100 points)

### Model Formulation (40 pts)
- Objective function correct: 15 pts
- All constraints present: 15 pts
- Variable domains specified: 10 pts

### Implementation (30 pts)
- Code runs without errors: 15 pts
- Correct solver configuration: 10 pts
- Clean code structure: 5 pts

### Analysis (30 pts)
- EVPI computed correctly: 10 pts
- VSS computed correctly: 10 pts
- Written interpretation: 10 pts
```

### Step 2: Run PACE per Submission

```
/pace "Grade this submission against the HW3 rubric.
Rubric: [paste or reference rubric]
Submission: [paste or reference student work]
Provide point breakdown per criterion with brief justification."
```

PACE produces:
- Player A's grade with breakdown
- Player B's grade with breakdown (independent)
- Coach C and D reviews
- Cross-comparison: where scores agree and disagree

### Step 3: Review Divergences

When scores diverge on a criterion, the cross-comparison tells you exactly which criterion and why. Common patterns:
- **Partial credit ambiguity**: "Is a constraint that's present but wrong worth 5/15 or 0/15?"
- **Interpretation differences**: "Does 'clean code structure' require comments?"
- **Boundary cases**: "The code runs but with warnings — is that 15/15 or 10/15?"

These are exactly the rubric clarifications you need to make grading fair.

## Tips for Instructors

- **PACE is overkill for simple assignments.** Use it for complex rubrics (10+ criteria) or high-stakes grading.
- **Use PACE to calibrate, then grade manually.** Run PACE on 3-4 representative submissions to identify rubric ambiguities, resolve them, then grade the rest yourself with the clarified rubric.
- **The convergence report is your documentation.** If a student challenges a grade, the PACE output shows exactly how the rubric was applied.

## Combining With `/audit` — Full Submission Workflow

For research-writing courses where students cite published work, `/pace` on its own does not catch fabricated citations. Use this two-step flow:

1. **`/audit paper.md --sources sources/`** — catches MISMATCH / NOT FOUND on every citation. See `using-audit-for-student-submissions.md` for setup.
2. **`/pace` with the rubric above** — grades the argument, clarity, and analytical correctness.

Run `/audit` first. If it flags any fabricated citations, that's a rubric issue (zero for the citation criterion) PLUS a conversation with the student before the PACE pass.

If you run a large class, see `references/processing_student_submissions.md` for the batching recipe that scales this workflow to 40+ students.

## What `/pace` Does Not Do for Grading

- **Doesn't replace your judgment.** PACE provides two independent reads; you integrate them into the final grade.
- **Doesn't detect LLM-written prose.** PACE grades a paper at face value; it doesn't try to detect whether the paper was ghostwritten by an LLM.
- **Doesn't compare across students.** If you need to find patterns across the class (common errors, common strengths), run `/pace` on the *batch*, not per-paper. See `processing_student_submissions.md`.

## Evidence Trail

Every `/pace` run writes `run_report.md` with YAML frontmatter. When a student challenges a grade, you can:

1. Hand them the PACE run_report (Player A output, Player B output, Coach reviews, Cross-Reviewer synthesis)
2. Show them the exact rubric criterion where the divergence was
3. Let them argue their case against the specific point of disagreement

This is faster and fairer than "here's my grade, trust me." The student sees the actual reasoning.
