---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(mkdir:*), Bash(shasum:*), Bash(sha256sum:*), Agent
description: PACE (Parallel Agent Consensus Engine) — spawns four subagents (two players + two coaches), presents independent reports, cross-reviews with a single cross-reviewer, and consolidates into a single final result with convergence/divergence analysis.
---

# PACE Protocol (Parallel Agent Consensus Engine)

<!-- spawn: none reason="the cost warning names the agents a run starts; they are marked at Steps 1, 2, 4 and 7c" -->
> **When to use**: You need a single verified deliverable (code, proof, analysis, document) and want independent agents to cross-check each other's work. Best for tasks with a correct answer where errors are costly.
>
> **Cost warning**: This command spawns 5 subagents (2 players + 2 coaches + 1 cross-reviewer), plus a sixth revision reviewer when findings are applied to an artifact (Step 7c). The subagents run on Sonnet by default (see AGENT MODEL). Estimated cost: 80K-200K tokens per run depending on task complexity.

You are the **Commissioner** of a four-agent workflow. Your job is to run the user's task through two independent **Player** agents (A and B), have each reviewed by their own independent **Coach** agent (C and D), present all four reports to the human, then cross-compare via a single cross-reviewer and consolidate into a single high-quality output. This protocol surfaces blind spots, alternative framings, and trade-offs that a single agent would miss.

**The analogy:** Players A and B do the work independently. Coaches C and D each review their own player's work — catching errors and strengthening arguments *before* the cross-comparison. A single Cross-Reviewer then evaluates both teams side by side. Then everything comes to the Commissioner (the human) who sees all reports and makes the final calls.

**This command is generic.** It works with any task on any research project — writing, analysis, code, planning, research, documentation, or design. The user's task is provided as $ARGUMENTS. If $ARGUMENTS is empty, ask the user what task they want to run through the PACE protocol before proceeding.

**Project context**: If a `toolkit-config.md` exists in the project root or at `~/.claude/toolkit-config.md`, read it for project-specific framing (`project_name`, `workstreams`) and for `evidence_dir`, the folder where run evidence is written. If the file or the key is absent, use `.toolkit/evidence` relative to the project root. The rest of this file calls that folder `<evidence-dir>`. Earlier versions of this command wrote to `evidence/` at the project root; if that folder already holds your PACE runs, set `evidence_dir: evidence` to keep them together.

---

## WHY THIS EXISTS

The core idea is simple: **run two independent copies of the same problem, then cross-check their outputs.** When both agents converge on the same answer, confidence is high. When they diverge, we know exactly where uncertainty lives — and incorrect answers get filtered out rather than silently accepted. This is verification through redundancy: the same principle behind dual-channel safety systems.

A single agent produces a single line of reasoning. It may miss edge cases, favor one framing over another, or make assumptions without flagging them. By running two agents independently, having each coached independently, and then cross-reviewing, we get:

1. **Coverage** — each agent may notice things the other missed
2. **Robustness** — points of agreement are high-confidence; disagreements surface genuine uncertainty
3. **Quality** — the final output incorporates the strongest elements of both attempts
4. **Error filtering** — incorrect answers that a single agent might confidently produce are caught when the other agent reaches a different (correct) conclusion
5. **Internal quality control** — each player's output is reviewed and strengthened by its own coach before it faces cross-comparison, raising the quality floor of both outputs

---

## STEP 0: UNDERSTAND THE TASK

Read the user's task from `$ARGUMENTS`. If the task references specific files, read those files now. Gather all context needed so both subagents can work from the same information.

**Provide complete context or nothing.** Players and Coaches cannot ask follow-up questions. If you give them incomplete context, they will silently fill in gaps with assumptions that may diverge for the wrong reasons. For analytical tasks:
- Include ALL relevant equations, definitions, and assumptions from the source material
- Include the notation table if one exists
- If a derivation builds on a prior result (e.g., "from Appendix A2..."), include the full prior result

### JIT Reference Gate

If the project has a `references/` directory with JIT reference files, check whether any apply to this task:
- Citation standards → look for `references/citation_standards.md` or similar
- Domain-specific procedures → look for files matching the task domain
- Document templates → look for `references/document_header_template.md`

If relevant reference files exist, load them NOW so both subagents have the same standards in context. If the task is domain-agnostic (pure analysis, design, debugging within a known codebase), skip this.

**Assemble a Task Brief** that includes:
- The user's original request (verbatim from $ARGUMENTS)
- Any files read and their relevant content
- Any constraints from the project's CLAUDE.md or configuration that apply
- The expected deliverable type (code, document, analysis, plan, etc.)
- Any applicable reference standards loaded above

**Create a Task Essence** — a structured 200-500 token summary using this template:

> **Task**: [1 sentence — what needs to be produced]
> **Deliverable type**: [code / document / analysis / plan / etc.]
> **Source material**: [list of files read, with sizes — e.g., "main.tex (355 lines), analysis.py (48 lines)"]
> **Key constraints**: [3-5 bullet points — the most important rules or requirements]
> **Success criteria**: [how to judge whether the output is correct/complete]
> **Project rules that apply**: [any hard rules from CLAUDE.md relevant to this task — e.g., "every cited paper must exist as a PDF under `papers/`, searched recursively"]

The Task Essence must contain enough context for a reviewer to evaluate quality WITHOUT re-reading the source files. The Task Essence goes to Coaches and the Cross-Reviewer instead of the full Task Brief. Players still receive the full Task Brief.

**Context budget discipline.** The protocol's token cost scales with source document size multiplied by agent count. To control costs:
- **Players** receive the full Task Brief (they need complete context to work independently)
- **Coaches** receive the Task Essence + their Player's output ONLY. They do NOT receive the original source files — the Player's output contains the relevant analysis. If a Coach needs to verify a specific claim against source material, it should flag this as a review limitation rather than receiving the full source preemptively.
- **Cross-Reviewer** receives the Task Essence + a structured extraction from each team (see Step 4), NOT the raw Player+Coach outputs in full
- **Estimated savings**: for a task with a 1000-line source document, this saves roughly 60% of tokens compared to full duplication (5x the full document reduced to 2x the full document + 3x the essence).

**Name every file by its full path, not by filename.** If the Task Brief mentions a file the Players must inspect, give its full path. A Player that has to *find* a file will search a plausible root, miss, and fall back to reasoning from the brief's prose — producing a lower-evidence answer that still reads as confident. In one run, a Player could not locate a script that sat outside the folders it searched, and returned a recommendation designed without reading it, self-rated MEDIUM. The other Player and a Coach located the same file and each found real defects in it. Same brief, different evidence quality, only because one agent had to guess where to look.

**Path resolution for subagents.** Subagents cannot ask clarifying questions about project structure. When the Task Brief involves file searches (e.g., checking that a cited paper exists on disk, locating code), state explicitly:
- The project root path
- Whether searches should be recursive (e.g., `papers/**/*.pdf` vs `papers/*.pdf`)
- Any project-specific subfolder conventions (e.g., a separate source folder per paper or per chapter)

Leaving these out causes Players to diverge on factual verification for the wrong reasons — path resolution disagreements, not analytical disagreements.

**Token budget estimate.** Before launching, estimate the total token cost:
- Player prompts: ~(source doc chars / 4 + 500 instruction tokens) x 2
- Player outputs: ~2000-4000 each
- Coach prompts: ~(500 essence + Player output size) x 2
- Coach outputs: ~1500-3000 each
- Cross-Reviewer prompt: ~500 essence + 2 x ~1000 extraction
- Cross-Reviewer output: ~2000-3000
- **If estimated total exceeds 200K tokens**, inform the Commissioner with the estimate and the single-agent alternative cost for comparison.

**Difficulty assessment.** The protocol adds ~6-7x latency and ~3-5x token cost. Use it for:
- **Good fit**: Mathematical proofs, architectural decisions, critical document sections, complex debugging, high-stakes deliverables where multiple valid framings exist
- **Poor fit**: Simple edits, mechanical refactoring, straightforward lookups, tasks with only one correct answer

If the task is a poor fit, inform the Commissioner and offer a single-agent alternative.

**SAME-MODEL CAVEAT (CRITICAL)**: The fan-out agents all run the same model (Sonnet by default, per AGENT MODEL below). So Player convergence is NOT independent validation — both Players share training data, failure modes, and biases. The protocol catches errors within that model's capability range; it cannot exceed it.

**One genuine second reader exists, and it is worth using deliberately.** When the fan-out agents run on Sonnet and the orchestrator stays on the session's model (often a stronger one), the Commissioner reading the findings is a reader on a *different* model — a real second check, not the same reasoning repeated. Two consequences: the Commissioner should re-derive any finding a verdict turns on rather than passing it through, and a claim **all five agents missed** is the one this protocol is weakest against, so the Commissioner owns looking for it. If the user raises the agents to the session's model, this second reader is gone; say so in the report.

**CITATION ENFORCEMENT (CRITICAL)**: Every numerical value in a Player's SOLUTION must carry an explicit citation: (Author Year, page/exhibit), a public data source URL, or a project run ID. If a Player cannot find a source for a number, it MUST either (a) state the claim qualitatively without a number, or (b) label the figure explicitly as "Calibration heuristic — [methodology and inputs]". Uncited numbers presented as facts are treated as hallucinations. This applies to every deliverable — posters, papers, dissertation chapters, analysis reports. In one run, agents built a cost comparison table with specific dollar figures and no citations, and it nearly went onto a research poster.

Do NOT begin subagent work until you have a complete Task Brief and Task Essence. If the task is ambiguous to the point where two agents would interpret the goal itself differently, ask the user one round of clarifying questions (max 3 questions) before proceeding.

---

## REQUIRED FILE MANIFEST — THE EVIDENCE BAR

A real PACE run MUST write each agent's output as a separate file so the run is mechanically auditable.

**Before Step 1**, generate a `run_id` from the current timestamp (`YYYY-MM-DD_HHMMSS`) and a slug (2-4 words, lowercase, hyphens, max 30 characters), then create the run directory `<evidence-dir>/pace_runs/pace_{run_id}_{slug}/` (a **directory**, not a single file). The rest of this file calls it `<run-dir>`. Pass its full path to every agent. It holds:

- `player_a_output.md` — Player A's complete SOLUTION + METADATA (non-empty, >500 bytes)
- `player_b_output.md` — Player B's complete output (non-empty, >500 bytes, content hash MUST differ from Player A)
- `coach_c_review.md` — Coach C's review of Player A
- `coach_d_review.md` — Coach D's review of Player B
- `cross_reviewer.md` — Cross-Reviewer's comparative critique (may be substituted only as described at the end of Step 4)
- `consolidated.md` — The final consolidated output delivered to the Commissioner
- `run_report.md` — The summary report with YAML frontmatter (FINAL STEP)
- `revision_review.md` — **required whenever findings were APPLIED to an artifact** (Step 7c). Absent when the run only reported and changed nothing. Absent for any other reason is a missing artifact, because the repairs then had exactly one reader, and that reader wrote them.

Each agent writes its own file (see AGENT FINISH DISCIPLINE). The orchestrator writes `consolidated.md`, `run_report.md`, and nothing else in the agents' names.

**PROHIBITED**: Any single combined file containing multiple agents' content interleaved. If you find yourself writing something like `all_outputs.md` or `agents_combined.md`, STOP — that is the single-context fallback pattern. The self-audit step will flag this and mark the run as invalid.

### Rationale

<!-- spawn: none reason="rationale for the file manifest" -->
Earlier PACE runs wrote only a summary report with narrative descriptions of what Players A and B said. That made it impossible to verify mechanically that two distinct subagents actually spawned, rather than the orchestrator role-playing both. An audit of sibling multi-agent commands found that runs had silently collapsed multi-agent outputs into single-context role-play. This file manifest is the structural check that forces each agent's output to exist as independent, hashable evidence.

---

## AGENT FINISH DISCIPLINE — NO SILENT STALLS

**The failure this prevents.** A Player or Coach finishes its reasoning but **comes to rest without saving its output**, leaving its file missing or frozen at a stub, with no completion notification. The orchestrator then waits blind. This has happened to both Coaches in the same run. The cause: the agent treated "return my answer" as optional or deferred and went idle before persisting it.

**The contract — every Player, Coach, Cross-Reviewer and revision-reviewer prompt MUST embed this block verbatim (referenced as `[FINISH-DISCIPLINE BLOCK]` in the prompt templates below):**

> **FINISH DISCIPLINE — do not stop until your work is persisted.**
> 1. Your job is NOT done when you have *thought through* the answer — it is done only when your complete output is **written to disk** at the exact path the orchestrator gave you (`<run-dir>/<your-file>.md`) using the Write tool, AND you have returned a final message.
> 2. **Write the file BEFORE you return.** Do not return your answer only as a chat message — persist it with Write first, then return a one-line confirmation ("Wrote <file>, N bytes"). The file is the deliverable; the chat message is just the receipt.
> 3. **Do not come to rest with an empty or stub file.** If you are tempted to stop, pause, or "wait for more context," that is the stall failure — instead, write your best current output to the file now (mark any open question inline) and only then stop. A complete-but-imperfect persisted file always beats a silent stall.
> 4. **You cannot ask the human anything** (you are non-interactive). If blocked, state the blocker inside your output file as an explicit `[BLOCKED: ...]` line and finish anyway.
> 5. Minimum viable output: >500 bytes of real content. If your file is smaller than that, you have not finished — keep going.

**Orchestrator-side liveness check (mechanical — run it; do not eyeball).** After spawning Players, and again after spawning Coaches, list the run directory with sizes:

```bash
ls -l "<run-dir>"
```

Any expected agent file that is missing or ≤200 bytes after ~2× the time the fastest sibling took is STALLED. Treat a stalled Player or Coach per the fallback rules (Coach-liveness timeout in Step 2; the one-Player-fails and Coach-stall edge cases). The finish-discipline block is the *prevention*; this check is the *detection*. Both are mandatory.

If an agent returned its full output in its final message but did not write its file, save the returned text verbatim to that file and name the agent in `self_audit_reason` (Step 7b). Never write an agent's file from your own reasoning.

---

## TOOL RULES — NAME ONLY TOOLS THE AGENT HAS

**The failure this prevents.** A prompt that tells an agent to use a tool it does not have forces it to break one instruction to follow another. In one run every Player and Coach prompt said "use the Read and Grep tools"; the session had no Grep tool. A Player discovered this mid-run, said so in its output, and fell back to shell search, which the same prompt had forbidden. The work was sound; the prompt was wrong.

**So, before writing any agent prompt, check the tool list in your own context** and name only the tools that are in it. A `general-purpose` subagent normally gets the same tools as the main session. Do not copy tool names from an older prompt or from `allowed-tools` above — that list names `Glob` and `Grep`, which is not evidence that this build of Claude Code provides them.

Every Player, Coach, Cross-Reviewer and revision-reviewer prompt embeds this block (referenced as `[TOOL-RULES BLOCK]` in the templates below). Fill the first line from the live tool list:

> **TOOL RULES.**
> 1. To read a file, use the Read tool. To search for text: <use the Grep tool | the Grep tool is not available here, so locate lines with read-only `grep -n` or `rg -n` through Bash>.
> 2. Use shell search to LOCATE lines only. Do not derive a reported number from a shell pipeline (counts, sums, sorts). If you need a number, read the lines and count them, or compute it in a short script and include the script in your output.
> 3. If a tool this prompt names is missing, say so in one line at the top of your output, use the fallback above, and finish. Do not stop.
> 4. Write only your own output file.

---

## AGENT MODEL — SONNET BY DEFAULT, DECLARED BEFORE EVERY RUN

### The declaration, before any agent is spawned

<!-- spawn: none reason="the topology declaration printed before the first agent starts" -->
**Print this line, every run, before the first Agent call. Not after, not in the final report.**

```
PACE topology: requested 5 agents on sonnet (default) · second reader: orchestrator <session model> at <effort> effort.
Say "opus players" or name a seat to raise it; otherwise this proceeds as stated.
```

Fill both blanks from the live session rather than copying the example: the orchestrator's model is whatever this session is running, and the effort level is the session's current setting (`low` / `medium` / `high` / `xhigh` / `max`). If you cannot determine the effort level, write `unknown` rather than guessing.

**It states and proceeds. It does NOT ask.** A confirmation prompt on every run is friction, and the default is the cheap option, so proceeding is the safe direction. The point of the line is that the cost is visible **before** it is spent, not that permission is sought.

**Why it has to be said out loud.** A model choice is invisible in the output. Five Sonnet agents and five Opus agents produce reports that read alike and differ several-fold in cost and noticeably in depth — and nothing in a tool result names the model a subagent used, so afterwards neither the user nor the orchestrator can tell which ran. Declaring it is the only moment the choice is observable.

### Raising it is the user's call, and only the user's

**Sonnet is the default and stays the default.** It is raised only when the user says so **in that turn**, naming what to raise: all five, the Players only, or one seat. Never raised because the task "feels" important, never carried over from a previous run, and never inferred from the artifact being high-stakes.

When the user raises it, say which seats changed in the declaration line, so the run's cost is still visible before it is spent:

```
PACE topology: Players A/B on Opus (raised by you), Coaches C/D + Cross-Reviewer on Sonnet.
```

<!-- spawn: none reason="the model policy for every PACE agent; each start is marked at its step" -->
**Every subagent this protocol spawns — Player A, Player B, Coach C, Coach D, the Cross-Reviewer and the Step 7c revision reviewer — is spawned with `model: "sonnet"`, explicitly, on every call, unless the user raised that seat in the current turn.** Pass it as an argument to the Agent tool; do not rely on a default. `sonnet` is the `reasoner` row of the toolkit's role table (`references/model-roles.md`). If an agent cannot run on the model it requested, follow MODEL FAILURE below, and record what ran in `subagent_model`.

<!-- BEGIN MODEL FAILURE -->
**MODEL FAILURE — when an agent cannot run on the model it requested.**
1. **A session or weekly limit** ("You've hit your session limit"). These limits are shared across all models, so another model does not help. Stop starting agents, quote the error and its reset time, and offer two choices: wait, or stop. Do not retry.
2. **An Opus limit, or a model the account cannot use, on the Chair's `opus` request** ("You've hit your Opus limit"; "There's an issue with the selected model"). Retry the Chair once on `sonnet`. Write `fallback_from: opus` and the error text into the run report, and name the model that ran in the printed model line.
3. **Any other error, or any other role.** Stop that role, quote the error, and offer the choices: retry as written, run that role on the session's model, or stop. Never change a role's model on your own; rule 2 is the only exception.
4. Do not rely on a fallback-model setting for this: Claude Code never switches models on an authentication, billing or rate-limit error.
<!-- END MODEL FAILURE -->

PACE has no Chair, so rule 2 never applies here.

<!-- spawn: none reason="why the model is passed on every call" -->
**Why it has to be explicit.** A subagent with no `model` set inherits the orchestrator's model. PACE spawns five of them and its cost is dominated by that fan-out, so one omitted argument is the difference between one expensive-model run and six. Nothing in the tool result says which model a subagent used, so an omission is invisible afterwards — which is why this is a written rule with a field in the run report rather than a habit.

**The orchestrator (the Commissioner) stays on whatever model the session is running.** It does the convergence analysis, the judgment calls and the consolidation, which is where the reasoning that cannot be delegated lives. This rule is about the fan-out agents only.

**What this costs.** PACE's value is catching the defect a single agent would confidently miss, and a Player that reasons less well finds fewer of them, so expect each run to catch somewhat less than it would with stronger Players. Two things make that an acceptable trade rather than a silent downgrade: the fan-out is still two independent Players plus two Coaches, so the *structural* error filtering is unchanged, and the Commissioner still reads every finding on the session model. **If a run's findings come back thin on a high-stakes artifact, the answer is to re-run the specific question with stronger agents, not to assume the pass was thorough.** Say so in the report when it happens.

**Record it.** The run report's frontmatter carries `subagent_model` alongside `model` (the orchestrator's), plus `effort` and `topology_declared`. A run whose frontmatter does not name the subagent model cannot be compared with one that does, and a run that did not print the declaration line says so in `topology_declared` rather than leaving it unknowable.

---

## STEP 1: SPAWN TWO PLAYERS

<!-- spawn: role=reasoner model=sonnet site=pace#player-a,pace#player-b -->
Spawn two Player subagents **in parallel** using the Agent tool, **each with `model: "sonnet"`** (see AGENT MODEL). Give each the following instructions.

<!-- spawn: none reason="the no-simulation warning; the Player starts are marked above" -->
**CRITICAL — NO SIMULATION ALLOWED.** You (the orchestrator) MUST make two actual Agent tool calls — one for Player A, one for Player B — in the same message so they run concurrently. Do NOT "role-play" Player A and Player B by writing two outputs yourself. Do NOT write inline prose labeled "Player A would say..." and "Player B would say...". If the Agent tool is not available in this session, STOP and tell the user: "Agent tool unavailable — PACE cannot run. Fall back to single-agent work or restart the session." Single-context role-play defeats the entire point of the protocol (independent reasoning from two separate contexts) and produces convergence data that is indistinguishable from a single agent's confidence.

### Instructions for Player A:

**Spawn with `model: "sonnet"`.**

> **Role:** You are Player A in a four-agent protocol. You are working independently — you will NOT see Player B's work until the cross-review phase.
>
> **Your output file:** `<run-dir>/player_a_output.md` (the orchestrator gives you the exact `<run-dir>`). Write your SOLUTION + METADATA there with the Write tool before you return.
>
> [FINISH-DISCIPLINE BLOCK]  ← insert the verbatim block from "AGENT FINISH DISCIPLINE" above
> [TOOL-RULES BLOCK]  ← insert the block from "TOOL RULES" above, first line filled from the live tool list
>
> **Task Brief:**
> [Insert the assembled Task Brief here]
>
> **Instructions:**
> 1. Complete the task described in the Task Brief.
> 2. Do NOT prompt the human for clarification — if anything is ambiguous, state your interpretation in an "Assumptions" section and proceed.
> 2b. **Same-model awareness**: You and the other Player use the same underlying model. Your convergence provides limited independent validation. Actively seek alternative interpretations, edge cases, and framings that the "obvious" approach might miss.
> 2c. **CITATION ENFORCEMENT**: Every numerical value in your SOLUTION must have an explicit citation — (Author Year, page/exhibit), a public data source, or a project run ID. If you cannot cite a source for a number, you MUST either (a) state the claim qualitatively without a number, or (b) label the figure explicitly as "Calibration heuristic — [methodology]". NEVER present an uncited number as a fact. Uncited numbers are treated as hallucinations.
> 2d. **NUMERICAL AUDIT**: For every number in your SOLUTION that cites an external paper, search the source's text file (.txt) for that exact value before submitting, using the search route named in your TOOL RULES. If the text file is not available, flag the number as "UNVERIFIED — source text not available for search confirmation." A wrong number from a real paper is as bad as a fabricated citation.
> 2e. **SOURCE DATA VERIFICATION**: When the Task Brief makes empirical claims about data files (row counts, column values, completion status), verify at least one claim directly against the actual file using Read or the search route named in your TOOL RULES. Do NOT trust the Task Brief's numbers — they may be stale or wrong. If you cannot verify (file not accessible), flag the unverified claim in your Assumptions section.
> 2f. **CLAIMS ABOUT A SLIDE DECK OR OTHER BINARY DOCUMENT** (a slide count, which topic or case a deck covers, what a PDF or spreadsheet contains): NEVER assert these from memory. Extract the text from the file itself, or read an existing text extraction, and check the claim against it. If you cannot read the file, mark the claim "UNVERIFIED — file not read".
> 3. For mathematical or analytical tasks: Include at least one numerical verification — pick concrete parameter values, compute the result by hand or direct calculation, and confirm it matches your derived formula.
> 4. **Self-verify before returning**: After completing your solution, re-read it and check:
>    - Does every claim have supporting evidence or a stated assumption?
>    - For code: re-read for off-by-one errors, type mismatches, and untested edge cases. If the code is runnable, run it.
>    - For analysis: trace at least one number end-to-end from source data to final claim.
>    - For documents: check internal consistency — do later sections contradict earlier ones?
>    - State what you verified in a **VERIFICATION** line (e.g., "Verified: ran numerical example with n=3, matches formula").
> 5. Structure your output with a **SOLUTION** section (the core deliverable, as concise as possible while complete) followed by a **METADATA** section containing:
>    - **Assumptions Made**: List every assumption you made and why.
>    - **Confidence Assessment**: Rate your confidence (High / Medium / Low) and explain what would change your assessment.
>    - **Alternative Approaches Considered**: Approaches you considered but rejected, and why.
>    - **Verification**: What self-checks you performed and their results.
> 6. Keep the solution tight — verbose explanation belongs in metadata.
> 7. Write the complete output to your output file, then return.

### Instructions for Player B:

**Spawn with `model: "sonnet"`.**

> **Role:** You are Player B in a four-agent protocol. You are working independently — you will NOT see Player A's work until the cross-review phase.
>
> **Your output file:** `<run-dir>/player_b_output.md` (the orchestrator gives you the exact `<run-dir>`). Write your SOLUTION + METADATA there with the Write tool before you return.
>
> [FINISH-DISCIPLINE BLOCK]  ← insert the verbatim block from "AGENT FINISH DISCIPLINE" above
> [TOOL-RULES BLOCK]  ← insert the block from "TOOL RULES" above, first line filled from the live tool list
>
> **Task Brief:**
> [Insert the same Task Brief here]
>
> **Instructions:**
> 1. Complete the task described in the Task Brief.
> 2. Do NOT prompt the human for clarification — if anything is ambiguous, state your interpretation in an "Assumptions" section and proceed.
> 2b–2f. [Insert Player A's items 2b, 2c, 2d, 2e and 2f verbatim.]
> 3. **APPROACH DIFFERENTLY:** Before solving, commit to at least one alternative methodology or framing. Pick ONE of these techniques:
>    - **First Principles**: Rebuild the solution from basic axioms rather than copying the obvious approach.
>    - **Alternative Representation**: Reframe the problem in a different domain (equations → pseudocode, algorithms → data structures).
>    - **Adversarial**: Deliberately assume the opposite of the most obvious constraint.
>    - **Scaling Axis**: If the standard solution optimizes for one axis (e.g., speed), optimize for a different axis (e.g., correctness or simplicity).
>    - If you find the alternative approach is clearly inferior during development, you may abandon it — but document why you rejected it.
> 3b. **MANDATORY ADVERSARIAL — HOT-PATH RULE**: If the Task Brief involves edits to a hot path — code that runs per step, per event or per request inside a simulation or service loop, such as a dispatch or matching loop, an accept/reject branch, timeout or retry handling, or any function that mutates shared state and is called from the main step function — you MUST pick **Adversarial** above and cannot abandon it. These paths produce results that look correct on aggregate metrics while carrying subtle contamination. Assume the edit IS introducing silent breakage that a parse or compile check missed; trace EVERY downstream effect of the new code (which counter increments, which state mutates, which branch or cascade fires) and verify each is intentional rather than a side effect. Document your search even if it comes up empty.
>
>    *Why this rule exists:* in one ride-hailing simulation run, an edit set an acceptance flag to false, which silently fell into the rejection branch and incremented the decline counters — contaminating the very metrics a planned parameter sweep was meant to measure. The Player using the standard framing missed it; the Player using the adversarial framing caught it, and both Coaches confirmed it at the source. Without the adversarial framing, the whole sweep would have run on contaminated results.
> 4. For mathematical or analytical tasks: Include at least one numerical verification.
> 5. **Self-verify before returning**: (same as Player A above)
> 6. Structure your output with a **SOLUTION** section followed by a **METADATA** section (same as Player A).
> 7. Keep the solution tight — verbose explanation belongs in metadata.
> 8. Write the complete output to your output file, then return.

**Critical:** The two Players MUST NOT see each other's work. Their independence is what makes this protocol valuable.

Wait for both Players to complete, then run the liveness check. Label their outputs as **Output A** and **Output B**.

---

## STEP 2: SPAWN TWO COACHES

<!-- spawn: role=reasoner model=sonnet site=pace#coach-c,pace#coach-d -->
Spawn two Coach subagents **in parallel** using the Agent tool — two actual Agent tool calls in the same message, **each with `model: "sonnet"`** (see AGENT MODEL). Each Coach reviews ONLY their own Player's work + the Task Essence — not the other Player's output or the other Coach's review. **Coaches MUST be spawned as independent subagents.** **Do NOT have the orchestrator act as a Coach** — no inline role-play, no "Coach C would say..." prose. If the Agent tool is not available, STOP and inform the user — do not attempt to simulate the coaches from the orchestrator's context.

### Instructions for Coach C (reviews Player A):

> **Role:** You are Coach C in a four-agent protocol. Your job is to review and strengthen Player A's output BEFORE it goes to cross-comparison with another team. You do NOT know what Player B produced — focus entirely on making Player A's output as strong as possible.
>
> **Your output file:** `<run-dir>/coach_c_review.md` (the orchestrator gives you the exact `<run-dir>`). Write your full review there with the Write tool before you return. Coaches are the agents most likely to stall — the FINISH-DISCIPLINE block below is not optional.
>
> [FINISH-DISCIPLINE BLOCK]  ← insert the verbatim block from "AGENT FINISH DISCIPLINE" above
> [TOOL-RULES BLOCK]  ← insert the block from "TOOL RULES" above, first line filled from the live tool list
>
> **Task Essence:**
> [Insert Task Essence here]
>
> **Player A's Output:**
> [Insert Player A's complete output]
>
> **Review and Strengthen — evaluate each:**
>
> 1. **Completeness**: Does it fully address every aspect of the task? What is missing?
> 2. **Correctness**: Are there factual errors, logical flaws, or incorrect assumptions? For mathematical tasks: verify the Player's numerical example independently — if you get a different result, flag it as a critical finding.
> 3. **Assumptions**: Are all assumptions explicitly stated? Any hidden assumptions?
> 4. **Framing Bias**: Does the output favor one perspective without adequate justification?
> 5. **Strengths**: What does this output do particularly well? These should be highlighted in cross-comparison.
> 6. **Weaknesses**: What are the most significant problems? Rank them by impact.
> 7. **Recommended Improvements**: Specific, actionable changes. If the Player made an error, state what the correction should be.
> 8. **Upgraded Confidence**: Given your review, what is your confidence in Player A's output? (High / Medium / Low)
>
> Be specific. Reference the Task Essence for grounding. Your goal is to make Player A's work as strong as possible before it faces comparison.

### Instructions for Coach D (reviews Player B):

> [Same instructions as Coach C above, but reviewing Player B's output instead of Player A's. Coach D's output file is `<run-dir>/coach_d_review.md`. Include the same `[FINISH-DISCIPLINE BLOCK]` and `[TOOL-RULES BLOCK]` and the same "write the file before you return" requirement.]

Wait for both Coaches to complete, then run the liveness check. Label their outputs as **Coach C's Review of A** and **Coach D's Review of B**.

**Coach-liveness timeout.** A Coach can stall silently — its output file never appears or never grows past a stub, and no completion notification fires. Prevention is the `[FINISH-DISCIPLINE BLOCK]` in every Coach prompt; detection is the liveness check; recovery is this rule. Do NOT wait indefinitely. If a Coach has not produced its file within ~2× the time the Players took, declare it STALLED and fall back:
- (a) proceed with the Coach that DID return;
- (b) if BOTH Coaches stalled, replace their cross-check with the Commissioner independently re-verifying each Player's key findings against the source (search the cited files), and note "Coaches stalled — cross-check via Commissioner source re-verification" in the run report;
- (c) set `self_audit_verdict: suspicious` with the stall named in `self_audit_reason`.

A stalled Coach degrades the run to PARTIAL. It does NOT block delivery, because the two independent Players and their source-cited findings are the irreplaceable evidence. (See the matching edge case below.)

### 2b. Diagnostic Check (before presentation)

Quick diagnostics before presenting to the Commissioner:
1. **Coach Agreement**: Do both Coaches flag the same issues?
2. **Confidence Floor**: Did any Coach report confidence below HIGH?
3. **Recommendation Overlap**: Are Coaches suggesting similar improvements?

Report these inline in Quick-Look Observations (section 3c).

---

## STEP 3: PRESENT ALL FOUR REPORTS TO THE COMMISSIONER

**Before any cross-comparison**, present all four agents' outputs to the human. This is the only moment where each team's independent reasoning is visible without contamination from the other team. Once cross-comparison begins, the outputs are filtered through comparison and the raw signal is lost.

### 3a. Present Team A (Player A + Coach C)

Present under `## TEAM A — INDEPENDENT REPORT`. Include Player A's full output (SOLUTION + METADATA) followed by Coach C's full review.

### 3b. Present Team B (Player B + Coach D)

Present under `## TEAM B — INDEPENDENT REPORT`. Include Player B's full output followed by Coach D's full review.

### 3c. Quick-Look Comparison

After presenting both teams, provide a brief (3-5 bullet) initial observation of obvious similarities and differences — just enough to orient the Commissioner. Do NOT attempt a full convergence/divergence analysis here; that comes in Step 5.

> **Quick-look observations:**
> - Both Players structured the solution as [X] — likely a strong approach
> - Player A focused on [Y] while Player B emphasized [Z]
> - Coach C flagged [issue] in A's work; Coach D flagged [different issue] in B's work
> - Coach C upgraded A's confidence to [level]; Coach D upgraded B's confidence to [level]
> - Player A flagged [assumption] that Player B did not mention

### 3d. Proceed Directly to Cross-Comparison

After presenting the quick-look observations, proceed directly to Step 4 without pausing for Commissioner input. The Commissioner has a single review gate at Step 6d, after all analysis is complete.

---

## STEP 4: CROSS-COMPARISON

Before spawning the Cross-Reviewer, perform a **structured extraction** from each team's output:

**For each team, extract:**
1. **Core findings/deliverables** — the SOLUTION section, stripped of source document reproduction
2. **Key assumptions** — from METADATA (deduplicated list, not full text)
3. **Confidence level** — from both Player and Coach, with reasoning
4. **Coach's top 3 findings** — most significant issues, in order of impact
5. **Coach's upgraded confidence** — with brief reasoning

**Do NOT include** in the Cross-Reviewer's prompt:
- Full source documents or file contents (already analyzed by Players)
- Full Player METADATA sections (extract only assumptions and confidence)
- Full Coach review text (extract only top findings and confidence)
- Duplicated Task Brief content (use the Task Essence instead)

<!-- spawn: role=reasoner model=sonnet site=pace#cross-reviewer -->
Spawn a **single Cross-Reviewer** subagent with the Agent tool, **with `model: "sonnet"`** (see AGENT MODEL):

### Instructions for Cross-Reviewer:

> **Role:** You are a cross-comparison reviewer. Two independent teams produced outputs for the same task. Evaluate both against each other and produce a unified comparative critique.
>
> **Your output file:** `<run-dir>/cross_reviewer.md`. Write your critique there with the Write tool before you return.
>
> [FINISH-DISCIPLINE BLOCK]  ← insert the verbatim block from "AGENT FINISH DISCIPLINE" above
> [TOOL-RULES BLOCK]  ← insert the block from "TOOL RULES" above, first line filled from the live tool list
>
> **Task Essence:**
> [Insert Task Essence here]
>
> **Team A — Extracted Summary:**
> - Core findings: [extracted]
> - Key assumptions: [extracted]
> - Player confidence: [level + reasoning]
> - Coach top findings: [1. ..., 2. ..., 3. ...]
> - Coach confidence: [level + reasoning]
>
> **Team B — Extracted Summary:**
> [Same structure as Team A]
>
> **Produce a unified comparative critique covering:**
>
> 1. **Where Team A is stronger**: What does Team A do better than Team B?
> 2. **Where Team B is stronger**: What does Team B do better than Team A?
> 3. **Coach alignment**: Did each Coach catch the issues that comparison with the other team reveals? Were there blind spots the Coaches missed?
> 4. **Unique contributions from each team**: What does A provide that B does not, and vice versa?
> 5. **Recommended elements to preserve from each team**: What from each team should appear in the final output?
> 6. **Overall recommendation**: Which team's output should serve as the structural foundation, and why?
> 7. **Coach quality assessment**: Rank each Coach's review quality (High / Medium / Low) — did they catch the right issues?

Wait for the Cross-Reviewer to complete. Label the output as **Cross-Comparison Report**.

**Cross-Reviewer substitution — allowed, but must be RECORDED.** If BOTH Coaches independently verified their Player's claims against the SOURCE (not merely reviewed the prose), they have already produced the comparative evidence this stage exists for, and a fifth agent adds cost without adding independence. In one run, one Coach verified 12 of 14 claim groups and the other verified 20 claims, both against the live files — exactly the cross-check this stage is meant to supply. You may skip the Cross-Reviewer in that case, but you MUST record the substitution where the self-audit reads it: one line in the YAML frontmatter of `<run-dir>/run_report.md` (create the file now with just this frontmatter if it does not exist yet; the FINAL STEP completes it):

```yaml
cross_reviewer_substituted: "<what each Coach verified against source, at least 40 characters>"
```

The same words in the report body do not count, and a reason under 40 characters does not count. The substitution exempts only `cross_reviewer.md`: the Player, Coach and `consolidated.md` files stay required, and the hash checks still run. An unexplained missing `cross_reviewer.md` is `unverifiable`, not `verified_real` — the difference between a justified substitution and a silent omission is whether it is written down.

---

## STEP 5: ANALYZE CONVERGENCE AND DIVERGENCE

Compare the two teams' outputs, informed by the Coach reviews and the Cross-Comparison Report. Categorize every substantive element:

### Convergence (Both Teams Agree)
Items where both Players reached the same conclusion, used the same approach, or produced equivalent content. **If both Coaches also endorsed these items**, this is the highest-confidence signal. Preserve them.

**Same-model caveat:** Full convergence between same-model agents provides limited independent confirmation. Note "same-model convergence" rather than treating it as strong independent validation.

When both Players converge on an answer that **contradicts the source material**, and both Coaches endorse it, do NOT dismiss it because it disagrees with the user's existing work. Flag it prominently as "CONVERGENT FINDING vs. SOURCE MATERIAL", present the contradiction clearly, and let the Commissioner decide.

Check whether both Players surfaced the **same structural insight** that unifies several results. Flag a shared structural insight as a "CONVERGENT STRUCTURAL FINDING" — such insights often reveal connections the original work did not make explicit. They are especially significant if BOTH Coaches independently highlighted the same insight.

### Divergence (Teams Disagree)
For each divergence, note:
- What Player A chose and why
- What Player B chose and why
- What Coach C said about A's choice
- What Coach D said about B's choice
- What the Cross-Comparison Report flagged
- Your preliminary assessment of which is stronger (with reasoning)

### Unique Contributions
Items in one team's output but not the other — coverage gaps rather than agreement or disagreement. Note which team contributed each, whether the other team's Coach or the Cross-Reviewer flagged its absence, and whether it should be incorporated.

### Single-Panelist Unique Findings

<!-- regime-shift v0.1: surfaces buried-best-findings hidden under aggregate Cross-Reviewer synthesis -->

Findings raised by exactly ONE agent (one Player or one Coach) that no other panelist mentioned. These are NOT convergence (multiple agreement) and NOT divergence (active disagreement) — they are agent-exclusive observations distinct from per-team Unique Contributions above.

For each unique finding (max 4):
- `[Player A | Player B | Coach C | Coach D]: <finding>` (1–2 lines)
- Why this agent caught it (1 line)
- Confidence flag: `[HIGH if downstream-actionable | LOW if speculative]`

Rationale: regime-shift answers are often visible only through one perspective; aggregate synthesis can bury them. Surface them explicitly for the Commissioner.

---

## STEP 6: PRESENT ANALYSIS TO COMMISSIONER

**Do NOT write the consolidated output yet.** Present:

### 6a. Summary

- **Task**: Brief description
- **Deliverable**: Type
- **Agents Used**: Player A, Coach C, Player B, Coach D, Cross-Reviewer (or "Cross-Reviewer substituted — see run report")
- **Convergence**: Bulleted list of agreed items
- **Divergence**: For each item — what A chose, what B chose, what each Coach said, your recommendation
- **Unique Contributions**: Items from Team A only; items from Team B only
- **Confidence**: Overall assessment

### 6b. Judgment Calls

For each divergence where you had to pick one team's approach, explain:
- What both Players did
- What their respective Coaches said
- Why you favor one over the other
- What would change your mind

### 6c. Merged Assumptions

Deduplicated list of all assumptions from both Players and both Coaches. Flag any assumption that only one team made (the other may have handled that aspect without assuming).

### 6d. Ask for Confirmation

> "The above summarizes where the two teams agreed and diverged. I have NOT made pre-determined choices on divergence items — those are for you to decide.
>
> For each divergence:
> 1. Which team's approach do you prefer, or do you want a hybrid?
> 2. Are there unique contributions you want to exclude?
> 3. Should I prioritize Team A's or Team B's overall structure?
> 4. Any Coach-recommended improvements to apply?
>
> Say 'proceed' to accept my analysis as-is, or provide specific direction."

**STOP and wait for the Commissioner to respond.**

---

## STEP 7: CONSOLIDATE

After receiving Commissioner direction, produce a single consolidated output that:

1. **Preserves all convergence items**
2. **Resolves all divergence items** per Commissioner direction (or your recommendation if they said 'proceed')
3. **Incorporates unique contributions** from both teams (unless Commissioner excluded any)
4. **Addresses weaknesses** identified by Coaches and the Cross-Reviewer
5. **Follows the stronger structural framing** (as directed by the Commissioner)

Save it as `<run-dir>/consolidated.md`.

When the protocol reveals a potential error in the user's existing work (code, paper, documentation), the consolidated output must:
- Present the finding WITHOUT editing the source files
- Recommend verification steps (e.g., "run the analysis script with these parameters to check")
- Let the Commissioner decide whether to modify the source
- NEVER silently "fix" something based on team consensus alone

**Minority Confidence Preservation** — If any agent (Player or Coach) reports confidence lower than HIGH, the consolidated output's confidence CANNOT be rated HIGH without explicit justification for overriding that minority signal. When a single Coach reports MEDIUM or LOW while all other agents report HIGH, surface that Coach's concern prominently — minority signals are often the best calibrated in the system. If convergence is high but any Coach reported lower than HIGH, include a "Caveats and Limitations" section in the consolidated output that states the Coach's concern. Do not suppress minority signals for a clean deliverable.

### Consolidation Footer

```markdown
---

## PACE Protocol Metadata

**Process**: Dual-team independent generation (Players A+B) + Coach review (C+D) + Commissioner review + Cross-comparison + Commissioner-directed consolidation
**Agents Used**: Player A, Coach C, Player B, Coach D, Cross-Reviewer
**Agent Model**: [subagent model, e.g. Sonnet] · Commissioner on [session model]
**Convergence Rate**: [X of Y substantive items agreed upon] ([percentage]%) — substantive = major architectural or methodological decisions, core algorithmic choices, critical assumptions, key design trade-offs. Excludes stylistic variations, minor wording and presentation order.
**Divergence Items Resolved**: [N items, with brief resolution notes]
**Unique Contributions Incorporated**: [From Team A: N items, From Team B: M items]
**Commissioner Overrides**: [None / List of specific overrides]
```

---

## STEP 7b: SELF-AUDIT (MANDATORY — DO NOT SKIP)

**Before delivering the consolidated output, the orchestrator MUST verify the run directory against the FILE MANIFEST.** This is a mechanical check — no LLM judgment involved. It catches single-context fallback before it reaches the deliverable.

### 7b.1: Run the checks

If your project has its own run-evidence auditor script, you may run it on `<run-dir>` as well; the checks below are required either way, and the verdict comes from them.

1. **Files present**: `player_a_output.md`, `player_b_output.md`, `coach_c_review.md`, `coach_d_review.md`, `cross_reviewer.md`, `consolidated.md` exist in `<run-dir>`. `cross_reviewer.md` may be absent only if `run_report.md` frontmatter carries a `cross_reviewer_substituted:` line of at least 40 characters. `revision_review.md` must exist if findings were applied to an artifact (Step 7c).
2. **Sizes**: each present file is >500 bytes (`ls -l "<run-dir>"`).
3. **Distinct Players**: compute SHA-256 of `player_a_output.md` and `player_b_output.md` (`shasum -a 256` on macOS, `sha256sum` on Linux). They MUST differ. Identical hashes = single-context fallback.
4. **No collapsed files**: the directory contains no combined file such as `all_outputs.md`, `agents_combined.md` or `both_players.md`.

<!-- spawn: none reason="the verdict list mentions spawned agents; it starts nothing" -->
Map the results to a verdict:
- `verified_real` — all four checks pass, with nothing that calls for `suspicious`.
- `suspicious` — all four checks pass, but a Coach stalled, an agent's file had to be saved by the orchestrator from the agent's returned message, or another irregularity occurred. Name it.
- `fallback` — Player hashes are identical, a collapsed file is present, or the Player outputs were written by the orchestrator rather than by two spawned agents.
- `unverifiable` — a required file is missing (with no recorded substitution) or below 500 bytes.

### 7b.2: Interpret the verdict

<!-- spawn: none reason="the verdict table names the Agent tool in its fallback advice; it starts nothing" -->
| Verdict | Action |
|---------|--------|
| `verified_real` | Proceed to Step 7c / Step 8. |
| `suspicious` | Proceed, BUT prepend a WARNING block to the consolidated output naming the specific concern. |
| `fallback` | **STOP. Do NOT deliver a consolidated output.** Write a failure run report with `outcome: failed` and `fallback_detected: true`, and tell the user: "The PACE run did not produce independent Player A and Player B outputs — this is a single-context fallback. The results are not trustworthy. Recommend re-running in a session where the Agent tool is available." |
| `unverifiable` | **STOP.** Write a failure run report naming the missing artifacts. |

### 7b.3: Record the verdict

Add to the run report YAML frontmatter:
```yaml
self_audit_verdict: "verified_real"   # or suspicious | fallback | unverifiable
self_audit_reason: "..."              # which checks passed or failed, and any irregularity
fallback_detected: false              # true if verdict is fallback
```

### 7b.4: Why this step exists

<!-- spawn: none reason="rationale for the self-audit" -->
A retrospective audit of earlier multi-agent runs found that many had structural signs of single-context fallback despite claiming multi-agent output. PACE is vulnerable to the same failure because Step 1's "spawn two Players" can be misread as "write two outputs inline" by a sloppy orchestrator. This step blocks that failure from reaching the deliverable.

---

## STEP 7c: THE REPAIRS GET THEIR OWN REVIEW (MANDATORY when findings were applied)

**Applying a review's findings creates a new, unreviewed draft.** If the Commissioner directed you to apply the findings to an artifact (edit the document, code or brief that was reviewed), the result is not the artifact anyone reviewed — it is that artifact plus every change made in response. Those changes have had exactly one reader, the agent that made them, and re-reading your own rewrite is not an independent check.

<!-- spawn: role=reasoner model=sonnet site=pace#revision-reviewer -->
**So when findings were applied to an artifact, spawn ONE reviewer subagent with `model: "sonnet"`, aimed at the repairs rather than at the artifact.** Give it three things: the repaired artifact, the source of truth, and a numbered list of what each repair was supposed to fix. Ask it three questions:

1. Did each repair land correctly and completely?
2. **Did any repair introduce a new defect?** This is the highest-value output; say so in the prompt.
3. Did any repair leave stale text elsewhere that still reflects the pre-repair version?

It writes to `<run-dir>/revision_review.md`. Embed the `[FINISH-DISCIPLINE BLOCK]` and the `[TOOL-RULES BLOCK]` as with every other agent. Present its findings to the Commissioner before Step 8, and fix what it finds before delivery.

**Why this is a step.** In one run, nine defects in a document were repaired, and the revision review found that the fix for the first defect had introduced a new high-severity one: the replacement text swapped one unsupported claim for another — a conflation of two different metrics the source never equates — inside a passage readers would take as settled fact. Nothing else in this protocol catches that class of error. The Players and Coaches read the artifact as it was **before** the repairs; the self-audit only checks that files exist and differ; and the Commissioner wrote the repairs, so its own re-reading is not a second opinion.

**A pre-repair review does not cover the repaired file.** If your project records that an artifact was reviewed (a checklist, a sign-off, a hash-keyed validation log), that record now describes content that no longer exists. Either record this revision review against the new version, or record explicitly what changed since the last reviewed version. Do not mark the new version as reviewed on the strength of a review that never read it.

---

## STEP 8: DELIVER

Present the consolidated output. If the deliverable is a file (code, document, etc.), write it to the appropriate location. If conversational (analysis, recommendation), present it inline.

After delivery, ask:

> "The consolidated output is complete. Would you like me to:
> 1. Show the full Team A package (Player A + Coach C) for reference?
> 2. Show the full Team B package (Player B + Coach D) for reference?
> 3. Show the Cross-Comparison Report?
> 4. Make specific revisions to the consolidated output?
> 5. We're done — move on."

---

## EDGE CASES

### If subagent spawning is unavailable

<!-- spawn: none reason="edge case: no agent can be started" -->
> "Subagent spawning is not available in this environment. To run the PACE protocol manually:
> 1. Open two separate Claude Code sessions (Players A and B).
> 2. Give each the same Task Brief (I will provide it).
> 3. Open two more sessions (Coaches C and D).
> 4. Give Coach C Player A's output; give Coach D Player B's output.
> 5. Open one more session (Cross-Reviewer).
> 6. Give the Cross-Reviewer both teams' complete packages.
> 7. Collect all five outputs and paste them back here.
> 8. I will then run the convergence analysis and consolidation steps."

Provide the Task Brief for copy-pasting.

### If the task is too small OR is a well-specified implementation

**Poor fit triggers** — offer single-agent alternative:
- Trivial tasks: one-line answer, simple lookup, mechanical operation
- Well-specified implementation ("write this function", "add this field", "fix this bug") where the spec is unambiguous and both Players would produce essentially identical code
- Single-file edits with no architectural judgment required
- Layout or formatting adjustments (font sizes, spacing, colors) with a single correct answer per the user's visual preference

> "This task is [too small / a well-specified implementation] — both Players would converge trivially, and the ~6x latency overhead is not justified. I recommend completing it directly. Proceed with single-agent, or run the protocol anyway?"

**Good fit for PACE:**
- Mathematical proofs or derivations (exact reasoning chain matters)
- Architectural decisions with multiple valid approaches
- Critical document sections where framing affects research conclusions
- Debugging where the root cause is genuinely unknown
- Any task where an incorrect answer would be hard to detect without cross-checking

### If one Player fails (usage limit, API error, timeout, stall)

1. Inform the Commissioner: "Player [A/B] completed but Player [A/B] failed due to [reason]."
2. Offer options:
   - (a) Run the completed Player's output through its Coach only (single-team review)
   - (b) Retry the failed Player
   - (c) Use the completed Player's output as-is with a "single-team caveat"
3. If option (a): skip Cross-Comparison and Convergence Analysis (Steps 4-5) and note "Single-team analysis — cross-comparison not possible" in the consolidation footer.

### If a Coach stalls (no output file, no completion notification)

Treat this as a degraded run, not a blocker:
1. Do not wait past ~2× the time the Players took. Declare the Coach STALLED.
2. If one Coach returned, present that team's review; note that the other team had "no Coach review (stalled)".
3. If BOTH stalled, skip Steps 2b–4 and have the Commissioner re-verify each Player's findings against the source directly (the cross-check the Coaches would have provided). Note this substitution in the run report.
4. Mark the run PARTIAL, `self_audit_verdict: suspicious`, and name the stall in `self_audit_reason`.

In one run both Coaches stalled on a document audit; the substitute Commissioner re-verification against the source caught a real page-number error that one Player had wrong.

### If both Players produce identical output

> "Both Players produced essentially the same output — full convergence. Note: same-model convergence confirms the answer is within the model's confident range but does not constitute strong independent validation. Still running Coaches and cross-comparison — they may catch issues both Players missed."

### If the task involves writing to files

- Agents write only their own files inside `<run-dir>` (the evidence). They do NOT write the deliverable or touch the user's files during Steps 1-4.
- Write the deliverable only in Step 8 (after consolidation, the self-audit and Commissioner approval).
- If both teams propose different file paths or structures, flag this as a divergence item in Step 6.

---

## INTERACTION STYLE

- **Before spawning**: Be brief. Confirm understanding of the task, print the topology declaration, then launch Players.
- **After Step 1**: Launch Coaches immediately — do not wait for Commissioner input.
- **After Step 2**: Present all four reports (Step 3) completely. This is the Commissioner's first look at uncontaminated team outputs — do not rush or summarize excessively.
- **After Step 3**: Proceed directly to cross-comparison without pausing.
- **During cross-comparison**: Report when the Cross-Reviewer completes. Do not narrate what you are about to do — just do it.
- **At the summary**: Be thorough. The convergence/divergence analysis is the core value.
- **At consolidation**: Follow Commissioner direction precisely. If they said "proceed," use your judgment. If they gave overrides, implement them exactly.
- **Throughout**: Never fabricate agreement or disagreement.

## OUTPUT LENGTH MANAGEMENT

The full PACE protocol can produce 15,000-25,000 tokens across Steps 3-6. To keep the Commissioner's review manageable:

### Step 3 Progressive Disclosure
1. **Lead with Quick-Look Comparison** (3c) — orients the Commissioner before the details
2. **Present each team's SOLUTION section in full** — the core deliverable
3. **Summarize each Coach's review** as 3-5 bullet points — full text available on request
4. **Skip full METADATA sections** — extract only Assumptions and Confidence into the Quick-Look

This roughly halves Step 3 (from ~8,000 tokens to ~4,000) while keeping all decision-relevant information. The Commissioner can always ask for the full Team A or Team B package at Step 8.

### When to Use Full Presentation
- Mathematical proofs or derivations (exact text matters)
- Divergence is high and the Commissioner needs exact reasoning
- The Commissioner explicitly requests full reports

---

## FINAL STEP: RUN REPORT (AUTOMATIC)

**This step runs automatically after every PACE delivery — do not skip or ask permission.** If the run fails or is interrupted, still write the report with `outcome: partial` or `outcome: failed` and document the failure under Issues & Limitations.

1. **Write the run report** to `<run-dir>/run_report.md` (the `run_id` and `<run-dir>` were created before Step 1). If the file already exists because a Cross-Reviewer substitution was recorded, keep that line and complete the file. It must contain:

```yaml
---
schema_version: "1.0"
run_id: "{run_id}"
tool: "pace"
tool_version: "v2.0"
date: "{YYYY-MM-DD}"
model: "{orchestrator model — the session's model}"
subagent_model: "{model the fan-out agents ran on, e.g. sonnet}"
effort: "{low|medium|high|xhigh|max|unknown — the level declared before spawning}"
topology_declared: true          # false only if the declaration line was NOT printed before the first spawn
task_summary: "{1-line from user's task}"
outcome: "{complete|partial|failed}"
agent_count: {total agents started}
convergence_rate: {fraction of substantive items both teams agreed on, 0.0-1.0}
agree_count: {N}
diverge_count: {N}
error_catches: {errors caught that a single agent would have missed}
coach_corrections: {items the Coaches changed}
commissioner_overrides: {items the human overrode}
self_audit_verdict: "{verified_real|suspicious|fallback|unverifiable}"
self_audit_reason: "{...}"
fallback_detected: false
# cross_reviewer_substituted: "{only if Step 4 substitution was used, at least 40 characters}"
---

## Task
{2-3 sentence description of the charge.}

## Key Findings
{2-5 bullets: decisions made, errors caught, insights generated.}

## Issues & Limitations
{Any problems: API failures, stalls, partial completions, same-model caveats, thin findings on a high-stakes artifact. "None." if clean.}

## PACE Protocol Metadata

[Consolidation footer content from Step 7]
```

2. **Append to CSV index**: Add one row to `<evidence-dir>/run_log.csv` (create the file with the header row if it does not exist). Use the toolkit's 13-column schema:
```
run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
```
Quote `task_summary` and `notes` (they may contain commas). `report_path` is `<run-dir>/run_report.md`. `notes` is a JSON object, e.g. `"{""subagent_model"":""sonnet"",""self_audit_verdict"":""verified_real""}"`.

3. **Report to user**:
> "Run evidence saved to `<run-dir>/`"

> **What next?** Run `/daily-summary` to capture the PACE findings before they leave context — the convergence result, any discrepancy that was resolved, and the verified deliverable are all worth preserving in your session record.

$ARGUMENTS
