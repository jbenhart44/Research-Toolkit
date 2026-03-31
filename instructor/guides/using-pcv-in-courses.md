# Using PCV in Courses

## What PCV Does

Plan-Construct-Verify (PCV) adds structured planning discipline to Claude Code projects. Instead of students jumping straight to code, PCV guides them through:

1. **Planning** — Write a charge (project spec), answer clarification questions one at a time, get adversarial review from a Critic agent, produce an approved MakePlan
2. **Construction** — Build per the approved plan, with deviation logging when things change
3. **Verification** — Systematic check that deliverables meet the charge specification

## Why Use It in a Course

- **Students learn to plan before coding.** The charge template forces them to specify success criteria, constraints, and technology choices upfront.
- **The decision log is an audit trail.** You can see every planning decision the student made, what questions the AI asked, and how the student answered. This is grading gold.
- **Adversarial review teaches critical thinking.** The Critic agent challenges the plan before construction begins — students see their assumptions questioned.

## Example: Homework Assignment

### Step 1: Create the Charge

Tell students to create a `charge.md` in their project directory:

```markdown
# Project Charge

## Configuration
Name: [Student Name]
Project Name: HW3 — Supply Chain Optimization
Project Directory:
Export Target:
Prior Work:

## Project Description
Implement a two-stage stochastic programming model for a 3-warehouse,
10-customer supply chain network. Compare expected value solution vs.
stochastic solution.

## Technology & Constraints
- Python with Pyomo or Julia with JuMP
- Must solve to optimality (no heuristics)
- Report EVPI and VSS metrics

## Success Criteria
- Model runs without errors on provided test data
- EVPI and VSS computed correctly
- 2-page writeup explaining results
```

### Step 2: Students Run PCV

Students type `/pcv` in their project directory. PCV will:
- Validate the charge
- Ask 4-6 clarification questions (one at a time)
- Draft a MakePlan
- Run a Critic to challenge assumptions
- Present the plan for student approval

### Step 3: You Review the Decision Log

After submission, check `plans/logs/decision-log.md`. You'll see:
- What clarification questions the AI asked
- How the student answered (verbatim)
- What the Critic flagged
- What was approved at each gate

This tells you far more about the student's understanding than the final code alone.

## Tips for Instructors

- **Start small.** Have students use PCV for one assignment before expecting them to use it routinely.
- **The charge IS the assignment spec.** You can provide the charge directly, or have students write their own (higher learning value).
- **Review decision logs, not just deliverables.** The planning process reveals understanding.
- **PCV's clarification questions are teaching moments.** If a student can't answer "What edge cases should the model handle?", that's a learning gap you can address.
