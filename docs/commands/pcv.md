# /pcv — Plan-Construct-Verify

You're about to build something complex and you don't want to discover halfway through that you misunderstood the requirements.

## When you need this

- Starting any project that spans multiple files, decisions, or sessions
- Before writing code or a document where getting the structure wrong means rework
- When you have a vague idea and need to turn it into a concrete, reviewed plan before touching anything

## What it does — and what it won't

`/pcv` runs the full Plan-Construct-Verify workflow: it reads your charge file, asks clarifying questions one at a time to resolve ambiguities, runs an adversarial Critic review of the resulting plan, gets your approval at a Gate, then constructs and verifies the deliverable. Every decision is logged. Nothing is built until the plan is approved.

**Note**: `/pcv` is for complex projects — if something is simple and bounded, it will tell you and suggest a lighter path. It does not execute without human approval at key gates. Based on [PCV v3.14](https://mgkay.github.io/pcv/) by Dr. Michael G. Kay (NC State University).

## Worked example

A supply chain PhD student needs to build a Monte Carlo simulation of supplier disruption cascades for her dissertation. She's not sure whether to model it as a stochastic inventory problem or an agent-based simulation — and she has prior work from a failed attempt last semester.

```
/pcv
```

`/pcv` reads her charge file, analyzes the prior work (identifying what's reusable vs. what needs rebuilding), then asks clarifying questions one at a time: *What's the primary deliverable — code, a paper section, or both? Are the cascade dynamics the core contribution or a means to an end?* After 5 questions and a Critic review that catches an underspecified verification criterion, she approves the plan. Construction begins with a clear file structure, component order, and testable success criteria.

## Try it

```
/pcv
/pcv my_charge.md
```
