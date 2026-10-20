---
name: quick-ten
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(mkdir:*), Bash(git:*), Agent, AskUserQuestion
description: Quick clarifying-questions gate before a build. Surfaces the highest-leverage questions (at most 10) whose answers actually change what gets built, asks them in batches, shows a recap, and writes a short brief the build is then accountable to. Lightweight by default (single sharp pass); escalates to a real multi-perspective council only when the task genuinely has 3+ conflicting stakeholder lenses. Use before a substantial build/redesign/document/plan to aim it right the first time.
---

# /quick-ten — Highest-Leverage Clarifying Questions Before a Build

You are executing `/quick-ten`. The job: **before building something substantial, ask the user the questions whose answers actually change the build — at most ten, ordered by leverage — then build against a short recorded brief.**

**Version**: 1.0. Its five rules below came out of a council on how this gate should work; do not silently drop them.

The name is a mnemonic ("quick ten"), **not a quota**. The real promise is *the highest-leverage questions, at most 10* — never ten-for-the-sake-of-ten.

---

## THE FIVE RULES (do not violate)

1. **Up to 10, no floor.** Generate candidates, keep only questions that *fork the build* (different answers → materially different output), sort by leverage, cap at 10, and **stop wherever leverage drops off — even at 3.** Forcing a count manufactures filler, which trains the user to rubber-stamp and destroys the signal on the next run.
2. **Every finalist carries a build-divergence tag.** For each question you keep, you must be able to write one line: *"if answered differently, the build changes: ___."* A question that can't produce that sentence is cut **before the user ever sees it**. This tag is the entire difference between `/quick-ten` and generic requirements-gathering.
3. **Dedupe against the user's own message first.** Before asking anything, re-read the user's invoking request. **Never ask what they already told you** — re-asking reads as "the tool didn't listen" and is more damaging than a mediocre question. Also dedupe near-identical questions across sources (>~70% overlap → merge).
4. **Council is escalation, not the default.** Clarifying questions are a *breadth* problem, not a reasoning-depth problem — a single sharp pass with the category checklist (Step 2) finds most of them. Spawn a real multi-seat council **only** when the task itself has **3+ genuinely distinct, conflicting stakeholder lenses** (e.g. a public redesign: design / copy / engineering / business). Default is the single pass.
5. **Persist a brief, then recap before building.** Write the answers to `quickten_brief_{slug}.md` as a "Decisions Locked" table, show the user a one-screen recap of their choices **before** the build starts (so a fast-click misread is a 5-second fix, not a build-and-redo), and have the build cite the brief.

---

## STEP 0 — Should `/quick-ten` even run? (the skip valve)

Read the user's invoking request in full. `/quick-ten` **SKIPS itself and goes straight to the build** when any of these hold — say so in one line, then build:

- The task is **small, reversible, or exploratory** (a config tweak, a one-file script, a quick edit, a throwaway).
- The user **already specified the constraints** in their request (audience, scope, look, done-criteria are all stated) — asking anyway is ignoring context, not gathering it.
- The user explicitly said "just build it / use your judgment."

If you skip: `"This is well-specified / small enough that /quick-ten would just add friction — building directly. (Say so if you'd rather I ask first.)"` Then proceed.

Otherwise continue to Step 1.

---

## STEP 1 — Frame the build + decide single-pass vs. council

State in 1–2 sentences: **what is being built**, its **audience**, and its **one job**. Then decide the generation path:

- **Single sharp pass (DEFAULT).** You (the main context) generate the candidate questions using the Step 2 checklist. Fast, cheap, right for most builds.
- **Council escalation.** ONLY if the task has **3+ distinct, conflicting stakeholder lenses**.

<!-- spawn: role=reasoner model=sonnet site=quick-ten#council -->
For the council escalation, start 3–4 seats in ONE message with the Agent tool, each with `subagent_type: "coa-<seat>"` (the toolkit's seat agents: `coa-end-user`, `coa-practitioner`, `coa-skeptic`, `coa-advocate`; pick the lenses the task actually has) and `model: "sonnet"` (the `reasoner` row of the toolkit's role table). Brief each to return **5–8 candidate clarifying questions, each with a one-line build-divergence tag**, in this exact format so they parse cleanly:

```
Q: <question> | OPTIONS: <2-4 short options> | DIVERGES: <how the build changes if answered differently>
```

Members must be genuine Agent calls (never role-played inline). After they return, check that their outputs are distinct (different files and voices); if they collapsed to one voice, treat the result as a single pass and say so. If a seat cannot run on the model it requested, stop that seat, quote the error and offer the choices (retry, run it on the session's model, or continue with the single pass); never change its model on your own.

State which path you chose and why in one line (e.g. *"Single pass — one clear audience, no conflicting stakeholders."*).

---

## STEP 2 — Generate candidate questions (the leverage checklist)

Whether single-pass or council, every candidate must come from a category that can change the build. Sweep these:

| Category | The question it forces |
|---|---|
| **Audience** | Who is the one primary reader/user? (drives everything downstream) |
| **The one job** | What is the single outcome the artifact must achieve? |
| **Done-criteria** | What does "good / finished" look like — how will we know? |
| **Out-of-bounds** | What should it explicitly NOT do / NOT include? |
| **Precedent** | Something to match, or deliberately avoid (a reference, a house style, a prior version)? |
| **Constraints** | Hard limits — tech, length, tone, budget, deadline, honesty/claims? |
| **Proof / assets** | Is there a real example, visual, number, or source available (vs. must be produced)? |
| **Success metric** | What action/result counts as this working? |
| **Trade-off** | Any known tension the user must adjudicate (speed vs. polish, breadth vs. depth)? |
| **Distribution / fit** | Where/how will it actually be used or seen — does that change the build? |

For **each** candidate, attach the **build-divergence tag** (Rule 2). Then apply the filters in order:
1. **Cut** anything the user already answered in their request (Rule 3).
2. **Cut** anything whose tag is weak/generic ("what tone?" with no real fork) — if you can't name how the build changes, cut it.
3. **Merge** near-duplicates.
4. **Rank** the survivors by leverage (most build-changing first).
5. **Cap at 10** — but keep only what survived; **fewer is correct and expected.** Log anything notable you cut (`"cut: <q> — didn't change the build"`).

---

## STEP 3 — Ask the user (in ROUNDS, with recommended defaults)

**Ask in rounds of 1 to 3 questions, most important first** — never one giant prompt, and never a single wall of text. Small rounds keep each answer considered; a long list gets skimmed. Wait for each round's answers before sending the next, and weave prior answers into later rounds where they change the framing.

`AskUserQuestion` allows up to 4 per call, but this skill deliberately caps each round at **3** (each question with a `header` label + 2–4 `options`; an "Other" free-text is added automatically; set `multiSelect: true` only for non-exclusive choices). Round split (overall max **10** questions):

- 1–3 questions → **one** round.
- 4–6 → **two** rounds (3 + rest).
- 7–9 → **three** rounds (3 + 3 + rest).
- 10 → **four** rounds (3 + 3 + 3 + 1).

Rules for the options:
- **Put the recommended option first and append "(Recommended)"** so the user can bulk-accept fast and only override what they care about (fights fatigue).
- Put the **most important questions in the first batch** — later batches get skimmed.
- Write each option's `description` to say what choosing it *means for the build*.

---

## STEP 4 — Recap, then write the brief

**Before building anything**, show the user a compact recap of every decision:

```
Here's what I have — say the word and I build, or correct any line:
1. <question> → <their answer>
2. <question> → <their answer>
...
```

This is the fast-click safety net — one line to catch a misread. If they correct a line, update it.

Then write `quickten_brief_{slug}.md` (in the build's own directory, or a scratch directory if there isn't one yet) with a **Decisions Locked** table:

```markdown
# Quickten Brief — <what's being built> — <date>
| # | Decision | Chosen | Build implication |
|---|----------|--------|-------------------|
| 1 | <question> | <answer> | <how it shapes the build> |
...
Generation path: single-pass | council (<seats>). Questions asked: N. Cut for low leverage: <list or none>.
```

---

## STEP 5 — Build, accountable to the brief

Proceed to the actual build (directly, or hand it to the command that fits — `/pcv` for a planned multi-part build, `/quarto` for a deck, `/pace` for a verified deliverable). The build **opens by citing the brief** ("per the quick-ten brief: …") and stays faithful to the Decisions Locked table. If a build choice must diverge from a locked decision, **flag it to the user** rather than silently overriding — the brief is a contract, not a suggestion.

---

## GUARDRAILS AT A GLANCE (the pre-mortem, as a checklist)

- [ ] Did I re-read the user's request and cut already-answered questions? (else: "tool didn't listen")
- [ ] Does every asked question have a real build-divergence tag? (else: filler)
- [ ] Is the count what leverage justified, not a forced 10? (else: rubber-stamp training)
- [ ] If a council ran, were the members real Agent calls with distinct outputs? (else: fake multiplicity)
- [ ] Are near-duplicate questions merged? (else: "who is this for?" twice)
- [ ] Did I show a recap before building? (else: build-and-redo on a misclick)
- [ ] Is there a persisted brief the build cites? (else: questions asked but ignored)
- [ ] Did I offer the skip valve for a small/already-specified task? (else: friction where none was needed)

---

## INVOCATION

- `/quick-ten` — infer the pending build from the conversation; run the gate on it.
- `/quick-ten <describe the build>` — run the gate on the described build.
- `/quick-ten build X` — same; the described thing is what will be built after the questions.

Behavioral notes: `/quick-ten` is **advisory-then-active** — it asks, records, then builds. It never fabricates an answer the user didn't give (leave a decision `[open]` in the brief if declined). Keep it fast: the whole point is a light gate that makes the build land right the first time, not a protocol.
