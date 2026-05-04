---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(mkdir:*), Agent
description: PACE (Parallel Agent Consensus Engine) — spawns four subagents (two players + two coaches), presents independent reports, cross-reviews with a single cross-reviewer, and consolidates into a single final result with convergence/divergence analysis.
---

# PACE Protocol (Parallel Agent Consensus Engine)

> **When to use**: You need a single verified deliverable (code, proof, analysis, document) and want independent agents to cross-check each other's work. Best for tasks with a correct answer where errors are costly.
>
> **Cost warning**: This command spawns 5 subagents (2 players + 2 coaches + 1 cross-reviewer). Estimated cost: 80K-200K tokens per run depending on task complexity.

You are the **Commissioner** of a four-agent workflow. Your job is to run the user's task through two independent **Player** agents (A and B), have each reviewed by their own independent **Coach** agent (C and D), present all four reports to the human, then cross-compare via a single cross-reviewer and consolidate into a single high-quality output. This protocol surfaces blind spots, alternative framings, and trade-offs that a single agent would miss.

**The analogy:** Players A and B do the work independently. Coaches C and D each review their own player's work — catching errors and strengthening arguments *before* the cross-comparison. A single Cross-Reviewer then evaluates both teams side by side. Then everything comes to the Commissioner (the human) who sees all reports and makes the final calls.

**This command is generic.** It works with any task on any research project — writing, analysis, code, planning, research, documentation, or design. The user's task is provided as $ARGUMENTS. If $ARGUMENTS is empty, ask the user what task they want to run through the PACE protocol before proceeding.

**Project context**: If a `toolkit-config.md` exists in the project root or at `~/.claude/toolkit-config.md`, read it for project-specific framing. This is optional — the command works without it.

---

## WHY THIS EXISTS

The core idea is simple: **run two independent copies of the same problem, then cross-check their outputs.** When both agents converge on the same answer, confidence is high. When they diverge, we know exactly where uncertainty lives — and incorrect answers get filtered out rather than silently accepted.

A single agent produces a single line of reasoning. It may miss edge cases, favor one framing over another, or make assumptions without flagging them. By running two agents independently, having each coached independently, and then cross-reviewing, we get:

1. **Coverage** — each agent may notice things the other missed
2. **Robustness** — points of agreement are high-confidence; disagreements surface genuine uncertainty
3. **Quality** — the final output incorporates the strongest elements of both attempts
4. **Error filtering** — incorrect answers that a single agent might confidently produce are caught when the other agent reaches a different (correct) conclusion
5. **Internal quality control** — each player's output is reviewed and strengthened by its own coach before it faces cross-comparison, raising the quality floor of both outputs

---

## STEP 0: UNDERSTAND THE TASK

Read the user's task from `$ARGUMENTS`. If the task references specific files, read those files now. Gather all context needed so both subagents can work from the same information.

**Provide complete context or nothing.** Players and Coaches cannot ask follow-up questions. If you give them incomplete context, they will silently fill in gaps with assumptions that may diverge for the wrong reasons.

### JIT Reference Gate

If the project has a `references/` directory with JIT reference files, check whether any apply to this task:
- Citation standards → look for `references/citation_standards.md` or similar
- Domain-specific procedures → look for files matching the task domain
- Document templates → look for `references/document_header_template.md`

If relevant reference files exist, load them NOW so both subagents have the same standards in context.

**Assemble a Task Brief** that includes:
- The user's original request (verbatim from $ARGUMENTS)
- Any files read and their relevant content
- Any constraints from the project's CLAUDE.md or configuration that apply
- The expected deliverable type (code, document, analysis, plan, etc.)
- Any applicable reference standards loaded above

**Create a Task Essence** — a structured 200-500 token summary using this template:

> **Task**: [1 sentence — what needs to be produced]
> **Deliverable type**: [code / document / analysis / plan / etc.]
> **Source material**: [list of files read, with sizes]
> **Key constraints**: [3-5 bullet points — the most important rules or requirements]
> **Success criteria**: [how to judge whether the output is correct/complete]
> **Project rules that apply**: [any hard rules from CLAUDE.md relevant to this task]

The Task Essence must contain enough context for a reviewer to evaluate quality WITHOUT re-reading the source files. The Task Essence goes to Coaches and the Cross-Reviewer instead of the full Task Brief. Players still receive the full Task Brief.

**Context budget discipline.**
- **Players** receive the full Task Brief (they need complete context to work independently)
- **Coaches** receive the Task Essence + their Player's output ONLY
- **Cross-Reviewer** receives the Task Essence + a structured extraction from each team (see Step 4), NOT the raw Player+Coach outputs in full

**Token budget estimate.** Before launching, estimate the total token cost:
- Player prompts: ~(source doc chars / 4 + 500 instruction tokens) x 2
- Player outputs: ~2000-4000 each
- Coach prompts: ~(500 essence + Player output size) x 2
- Coach outputs: ~1500-3000 each
- Cross-Reviewer prompt: ~500 essence + 2 x ~1000 extraction
- Cross-Reviewer output: ~2000-3000
- **If estimated total exceeds 200K tokens**, inform the Commissioner with the estimate and the single-agent alternative cost for comparison.

**Difficulty assessment.** The protocol adds ~6-7x latency and ~3-5x token cost. Use it for:
- **Good fit**: Mathematical proofs, architectural decisions, critical document sections, complex debugging, high-stakes deliverables
- **Poor fit**: Simple edits, mechanical refactoring, straightforward lookups, tasks with only one correct answer

If the task is a poor fit, inform the Commissioner and offer a single-agent alternative.

**SAME-MODEL CAVEAT (CRITICAL)**: All agents use the same underlying language model. Convergence is NOT independent validation — both agents share training data, failure modes, and biases. The protocol catches errors within the model's capability range; it cannot exceed it.

Do NOT begin subagent work until you have a complete Task Brief and Task Essence. If the task is ambiguous, ask the user one round of clarifying questions (max 3 questions) before proceeding.

---

## REQUIRED FILE MANIFEST — THE EVIDENCE BAR

A real PACE run MUST write each agent's output as a separate file so the run is mechanically auditable. Create a run directory at `evidence/pace_runs/pace_{run_id}_{slug}/` (a directory, not just a single markdown file) and write these artifacts:

- `player_a_output.md` — Player A's complete SOLUTION + METADATA (non-empty, >500 bytes)
- `player_b_output.md` — Player B's complete output (non-empty, >500 bytes, content hash MUST differ from Player A)
- `coach_c_review.md` — Coach C's review of Player A
- `coach_d_review.md` — Coach D's review of Player B
- `cross_reviewer.md` — Cross-Reviewer's comparative critique
- `consolidated.md` — The final consolidated output delivered to the Commissioner
- `run_report.md` — The summary report with YAML frontmatter (the existing Step 9 output; now lives inside the run directory)

**PROHIBITED**: Any single combined file containing multiple agents' content interleaved. If you find yourself writing something like `all_outputs.md` or `agents_combined.md`, STOP — that is the single-context fallback pattern. The self-audit step (added below) will flag this and mark the run as invalid.

### Rationale

Historical PACE runs (pre-2026-04-10) wrote only a summary `run_report.md` with narrative descriptions of what Players A and B said. This made it impossible to mechanically verify that two distinct subagents actually spawned vs the orchestrator role-playing both. On 2026-04-09 an audit of sibling multi-agent commands found that recent runs had silently collapsed multi-agent outputs into single context role-play. This file manifest is the structural check that forces each agent's output to exist as independent evidence.

---

## STEP 1: SPAWN TWO PLAYERS

Spawn two Player subagents **in parallel** using the Agent tool. Give each the following instructions.

**CRITICAL — NO SIMULATION ALLOWED.** You (the orchestrator) MUST make two actual Agent tool calls — one for Player A, one for Player B — in the same message so they run concurrently. Do NOT "role-play" Player A and Player B by writing two outputs yourself. Do NOT write inline prose labeled "Player A would say..." and "Player B would say...". If the Agent tool is not available in this session, STOP and tell the user: "Agent tool unavailable — PACE cannot run. Fall back to single-agent work or restart the session." Single-context role-play defeats the entire point of the protocol (independent reasoning from two separate contexts) and produces convergence data that is indistinguishable from a single agent's confidence.

### Instructions for Player A:

> **Role:** You are Player A in a four-agent protocol. You are working independently — you will NOT see Player B's work until the cross-review phase.
>
> **Task Brief:**
> [Insert the assembled Task Brief here]
>
> **Instructions:**
> 1. Complete the task described in the Task Brief.
> 2. Do NOT prompt the human for clarification — if anything is ambiguous, state your interpretation in an "Assumptions" section and proceed.
> 2b. **Same-model awareness**: You and the other Player use the same underlying model. Actively seek alternative interpretations, edge cases, and framings that the "obvious" approach might miss.
> 2c. **CITATION ENFORCEMENT**: Every numerical value in your SOLUTION must have an explicit citation — (Author Year, page/exhibit), a public data source, or a simulation run ID. If you cannot cite a source for a number, you MUST either (a) state the claim qualitatively without a number, or (b) label the figure explicitly as "Calibration heuristic — [methodology]". NEVER present an uncited number as a fact. Uncited numbers are treated as hallucinations.
> 2d. **NUMERICAL AUDIT**: For every number in your SOLUTION that cites an external paper, grep the source .txt file for that exact value before submitting. If the .txt file is not available, flag the number as "UNVERIFIED — source text not available for grep confirmation." A wrong number from a real paper is as bad as a fabricated citation.
> 2e. **SOURCE DATA VERIFICATION**: When the Task Brief makes empirical claims about data files (row counts, column values, completion status), verify at least one claim directly against the actual file using Read, Grep, or Bash. Do NOT trust the Task Brief's numbers — they may be stale or wrong. If you cannot verify (file not accessible), flag the unverified claim in your Assumptions section.
> 3. For mathematical or analytical tasks: Include at least one numerical verification — pick concrete parameter values, compute the result, and confirm it matches your derived formula.
> 4. **Self-verify before returning**: After completing your solution, re-read it and check:
>    - Does every claim have supporting evidence or a stated assumption?
>    - For code: re-read for off-by-one errors, type mismatches, and untested edge cases. If the code is runnable, run it.
>    - For analysis: trace at least one number end-to-end from source data to final claim.
>    - For documents: check internal consistency — do later sections contradict earlier ones?
>    - State what you verified in a **VERIFICATION** line.
> 5. Structure your output with a **SOLUTION** section followed by a **METADATA** section containing:
>    - **Assumptions Made**: List every assumption you made and why.
>    - **Confidence Assessment**: Rate your confidence (High / Medium / Low) and explain what would change your assessment.
>    - **Alternative Approaches Considered**: Approaches you considered but rejected, and why.
>    - **Verification**: What self-checks you performed and their results.
> 6. Keep the solution tight — verbose explanation belongs in metadata.
> 7. Return the complete output when finished.

### Instructions for Player B:

> **Role:** You are Player B in a four-agent protocol. You are working independently — you will NOT see Player A's work until the cross-review phase.
>
> **Task Brief:**
> [Insert the same Task Brief here]
>
> **Instructions:**
> 1. Complete the task described in the Task Brief.
> 2. Do NOT prompt the human for clarification — if anything is ambiguous, state your interpretation in an "Assumptions" section and proceed.
> 2b. **Same-model awareness**: Actively seek alternative interpretations, edge cases, and framings that the "obvious" approach might miss.
> 3. **APPROACH DIFFERENTLY:** Before solving, commit to at least one alternative methodology or framing. Pick ONE of these techniques:
>    - **First Principles**: Rebuild the solution from basic axioms rather than copying the obvious approach.
>    - **Alternative Representation**: Reframe the problem in a different domain (equations → pseudocode, algorithms → data structures).
>    - **Adversarial**: Deliberately assume the opposite of the most obvious constraint.
>    - **Scaling Axis**: If the standard solution optimizes for one axis (e.g., speed), optimize for a different axis (e.g., correctness or simplicity).
>    - If you find the alternative approach is clearly inferior during development, you may abandon it — but document why you rejected it.
> 4. For mathematical or analytical tasks: Include at least one numerical verification.
> 5. **Self-verify before returning**: (same as Player A above)
> 6. Structure your output with a **SOLUTION** section followed by a **METADATA** section (same as Player A).
> 7. Keep the solution tight — verbose explanation belongs in metadata.
> 8. Return the complete output when finished.

**Critical:** The two Players MUST NOT see each other's work. Their independence is what makes this protocol valuable.

Wait for both Players to complete. Label their outputs as **Output A** and **Output B**.

---

## STEP 2: SPAWN TWO COACHES

Spawn two Coach subagents **in parallel** using the Agent tool. Each Coach reviews ONLY their own Player's work. **Coaches MUST be spawned as independent subagents** via two Agent tool calls in the same message. **Do NOT have the orchestrator act as a Coach** — no inline role-play, no "Coach C would say..." prose. If the Agent tool is not available, STOP and inform the user — do not attempt to simulate the coaches from the orchestrator's context.

### Instructions for Coach C (reviews Player A):

> **Role:** You are Coach C in a four-agent protocol. Your job is to review and strengthen Player A's output BEFORE it goes to cross-comparison with another team. You do NOT know what Player B produced.
>
> **Task Essence:**
> [Insert Task Essence here]
>
> **Player A's Output:**
> [Insert Agent A's complete output]
>
> **Review and Strengthen — evaluate each:**
>
> 1. **Completeness**: Does it fully address every aspect of the task? What is missing?
> 2. **Correctness**: Are there factual errors, logical flaws, or incorrect assumptions? For mathematical tasks: verify the Player's numerical example independently.
> 3. **Assumptions**: Are all assumptions explicitly stated? Any hidden assumptions?
> 4. **Framing Bias**: Does the output favor one perspective without adequate justification?
> 5. **Strengths**: What does this output do particularly well?
> 6. **Weaknesses**: What are the most significant problems? Rank them by impact.
> 7. **Recommended Improvements**: Specific, actionable changes.
> 8. **Upgraded Confidence**: Given your review, what is your confidence in Player A's output? (High / Medium / Low)
>
> Be specific. Reference the Task Essence for grounding. Your goal is to make Player A's work as strong as possible before it faces comparison.

### Instructions for Coach D (reviews Player B):

> [Same instructions as Coach C above, but reviewing Player B's output instead of Player A's.]

Wait for both Coaches to complete. Label their outputs as **Coach C's Review of A** and **Coach D's Review of B**.

### 2b. Diagnostic Check (before presentation)

Quick diagnostics before presenting to the Commissioner:
1. **Coach Agreement**: Do both Coaches flag the same issues?
2. **Confidence Floor**: Did any Coach report confidence below HIGH?
3. **Recommendation Overlap**: Are Coaches suggesting similar improvements?

Report these inline in Quick-Look Observations (section 3c).

---

## STEP 3: PRESENT ALL FOUR REPORTS TO THE COMMISSIONER

**Before any cross-comparison**, present all four agents' outputs to the human. This is the only moment where each team's independent reasoning is visible without contamination.

### 3a. Present Team A (Player A + Coach C)

Present under `## TEAM A — INDEPENDENT REPORT`. Include Player A's full output (SOLUTION + METADATA) followed by Coach C's full review.

### 3b. Present Team B (Player B + Coach D)

Present under `## TEAM B — INDEPENDENT REPORT`. Include Player B's full output followed by Coach D's full review.

### 3c. Quick-Look Comparison

After presenting both teams, provide a brief (3-5 bullet) initial observation:

> **Quick-look observations:**
> - Both Players structured the solution as [X] — likely a strong approach
> - Player A focused on [Y] while Player B emphasized [Z]
> - Coach C flagged [issue] in A's work; Coach D flagged [different issue] in B's work
> - Coach C upgraded A's confidence to [level]; Coach D upgraded B's confidence to [level]
> - Player A flagged [assumption] that Player B did not mention

### 3d. Proceed Directly to Cross-Comparison

After presenting the quick-look observations, proceed directly to Step 4 without pausing for Commissioner input.

---

## STEP 4: CROSS-COMPARISON

Before spawning the Cross-Reviewer, perform a **structured extraction** from each team's output:

**For each team, extract:**
1. **Core findings/deliverables** — the SOLUTION section, stripped of source document reproduction
2. **Key assumptions** — from METADATA (deduplicated)
3. **Confidence level** — from both Player and Coach
4. **Coach's top 3 findings** — most significant issues, in order of impact
5. **Coach's upgraded confidence** — with brief reasoning

Spawn a **single Cross-Reviewer** subagent:

### Instructions for Cross-Reviewer:

> **Role:** You are a cross-comparison reviewer. Two independent teams produced outputs for the same task. Evaluate both against each other and produce a unified comparative critique.
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
> 3. **Coach alignment**: Did each Coach catch the issues that comparison reveals? Were there blind spots?
> 4. **Unique contributions from each team**: What does A provide that B does not, and vice versa?
> 5. **Recommended elements to preserve from each team**: What from each team should appear in the final output?
> 6. **Overall recommendation**: Which team's output should serve as the structural foundation, and why?
> 7. **Coach quality assessment**: Rank each Coach's review quality (High / Medium / Low)

Wait for the Cross-Reviewer to complete. Label the output as **Cross-Comparison Report**.

---

## STEP 5: ANALYZE CONVERGENCE AND DIVERGENCE

Categorize every substantive element:

### Convergence (Both Teams Agree)
Items where both Players reached the same conclusion. If both Coaches also endorsed these items, this is the highest-confidence signal.

**Same-model caveat:** Full convergence between same-model agents provides limited independent confirmation. Note "same-model convergence" rather than treating it as strong independent validation.

When both Players converge on an answer that **contradicts the source material**, flag it prominently as "CONVERGENT FINDING vs. SOURCE MATERIAL." Present the contradiction clearly and let the Commissioner decide.

### Divergence (Teams Disagree)
For each divergence, note:
- What Player A chose and why
- What Player B chose and why
- What Coach C said about A's choice
- What Coach D said about B's choice
- What the Cross-Comparison Report flagged
- Your preliminary assessment of which is stronger (with reasoning)

### Unique Contributions
Items in one team's output but not the other. Note whether the other team's Coach or Cross-Reviewer flagged the absence.

### Single-Panelist Unique Findings

<!-- regime-shift v0.1: surfaces buried-best-findings hidden under aggregate Cross-Reviewer synthesis -->

Findings raised by exactly ONE agent (one Player or one Coach) that no other panelist mentioned. These are NOT convergence (multiple agreement) and NOT divergence (active disagreement) — they are agent-exclusive observations distinct from per-team Unique Contributions above.

For each unique finding (max 4):
- `[Player A | Player B | Coach A | Coach B]: <finding>` (1–2 lines)
- Why this agent caught it (1 line)
- Confidence flag: `[HIGH if downstream-actionable | LOW if speculative]`

Rationale: regime-shift answers are often visible only through one perspective; aggregate synthesis can bury them. Surface them explicitly.

---

## STEP 6: PRESENT ANALYSIS TO COMMISSIONER

**Do NOT write the consolidated output yet.** Present:

### 6a. Summary

- **Task**: Brief description
- **Deliverable**: Type
- **Agents Used**: Player A, Coach C, Player B, Coach D, Cross-Reviewer
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

Deduplicated list of all assumptions from both Players and both Coaches.

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

When the protocol reveals a potential error in the user's existing work, the consolidated output must:
- Present the finding WITHOUT editing the source files
- Recommend verification steps
- Let the Commissioner decide whether to modify the source
- NEVER silently "fix" something based on team consensus alone

**Minority Confidence Preservation** — If any agent (Player or Coach) reports confidence lower than HIGH, the consolidated output's confidence CANNOT be rated HIGH without explicit justification. Surface minority signals prominently — do not suppress them for a clean deliverable.

### Consolidation Footer

```markdown
---

## PACE Protocol Metadata

**Process**: Dual-team independent generation (Players A+B) + Coach review (C+D) + Commissioner review + Cross-comparison + Commissioner-directed consolidation
**Agents Used**: Player A, Coach C, Player B, Coach D, Cross-Reviewer
**Convergence Rate**: [X of Y substantive items agreed upon] ([percentage]%)
**Divergence Items Resolved**: [N items, with brief resolution notes]
**Unique Contributions Incorporated**: [From Team A: N items, From Team B: M items]
**Commissioner Overrides**: [None / List of specific overrides]
```

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

## STEP 8b: SELF-AUDIT (MANDATORY — DO NOT SKIP)

**Before writing the run report, the orchestrator MUST verify its own output against the FILE MANIFEST.** This is a mechanical check — no LLM judgment involved.

### 8b.1: Run the auditor

If `scripts/audit_run_evidence.sh` exists under the project root, invoke it on the run directory:

```bash
bash scripts/audit_run_evidence.sh "evidence/pace_runs/pace_{run_id}_{slug}"
```

If the script does not exist, perform the equivalent checks inline:
1. Verify all required files exist: `player_a_output.md`, `player_b_output.md`, `coach_c_review.md`, `coach_d_review.md`, `cross_reviewer.md`, `consolidated.md`
2. Verify each file is non-empty (>500 bytes)
3. Compute SHA-256 of `player_a_output.md` and `player_b_output.md`. They MUST differ. (Identical hashes = single-context fallback.)
4. Reject any directory containing `all_outputs.md`, `agents_combined.md`, or similar collapsed files.

### 8b.2: Interpret the verdict

| Verdict | Action |
|---------|--------|
| `verified_real` | Proceed to Step 9 (run report). |
| `suspicious` | Proceed BUT add a WARNING block to the run report frontmatter naming the specific concern. |
| `fallback` | **STOP.** Write a failure run report with `outcome: failed` and `fallback_detected: true`. Tell the user: "The PACE run did not produce independent Player A and Player B outputs — this is a single-context fallback. The results are not trustworthy. Recommend re-running in a session where the Agent tool is available." |
| `unverifiable` | **STOP.** Write a failure report naming which artifacts are missing. |

### 8b.3: Record the verdict

Add to the run report YAML frontmatter:
```yaml
self_audit_verdict: "verified_real"
self_audit_reason: "..."
fallback_detected: false
```

### 8b.4: Why this step exists

On 2026-04-09 a retrospective audit found that ~30 historical multi-agent runs had structural signs of single-context fallback despite claiming multi-agent output. PACE is vulnerable to the same failure mode because its Step 1 prompts the orchestrator to "spawn two Players" — a sloppy orchestrator can interpret this as "write two outputs inline" without making real Agent tool calls. The SELF-AUDIT step blocks that failure from reaching the run report.

---

## STEP 9: RUN REPORT (AUTOMATIC)

**This step runs automatically after every PACE delivery — do not skip or ask permission.**

1. **Generate `run_id`**: Use the current timestamp formatted as `YYYY-MM-DD_HHMMSS`.

2. **Create evidence directory**: Ensure `evidence/pace_runs/` exists (create it and any parent directories if needed).

3. **Write run report** to `evidence/pace_runs/pace_{date}_{slug}.md` where `{slug}` is a 2-4 word kebab-case summary of the task. The file must contain:

```yaml
---
schema_version: "1.0"
run_id: "{run_id}"
tool: "pace"
tool_version: "v1.0"
date: "{YYYY-MM-DD}"
model: "{model used, e.g. claude-opus-4-6}"
task_summary: "{1-line from user's task}"
outcome: "{complete|partial|failed}"
agent_count: 5
convergence_rate: "{X/Y substantive items agreed}"
agree_count: {N}
diverge_count: "{N items with disagreement}"
error_catches: {N}
coach_corrections: {N}
commissioner_overrides: {N}
---

## Task
{2-3 sentence description of the charge.}

## Key Findings
{2-5 bullets: decisions made, errors caught, insights generated.}

## Issues & Limitations
{Any problems: API failures, partial completions, same-model caveats. "None." if clean.}

## PACE Protocol Metadata

[Consolidation footer content from Step 7]
```

4. **Append to CSV index**: Add one row to `evidence/run_log.csv` (create file with header row if it does not exist). CSV columns:
```
run_id,tool,tool_version,date,task_summary,outcome,model,agent_count,convergence_rate,agree_count,diverge_count,report_path,notes
```

5. **Report to user**:
> "Run evidence saved to `evidence/pace_runs/pace_{date}_{slug}.md`"

---

## EDGE CASES

### If subagent spawning is unavailable

> "Subagent spawning is not available in this environment. To run the PACE protocol manually:
> 1. Open two separate Claude sessions (Players A and B).
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
- Well-specified implementation where both Players would produce essentially identical code
- Single-file edits with no architectural judgment required
- Layout or formatting adjustments with a single correct answer per the user's visual preference

> "This task is [too small / a well-specified implementation] — both Players would converge trivially, and the ~6x latency overhead is not justified. I recommend completing it directly. Proceed with single-agent, or run the protocol anyway?"

**Good fit for PACE:**
- Mathematical proofs or derivations (exact reasoning chain matters)
- Architectural decisions with multiple valid approaches
- Critical document sections where framing affects research conclusions
- Debugging where the root cause is genuinely unknown
- Any task where an incorrect answer would be hard to detect without cross-checking

### If one Player fails

1. Inform the Commissioner: "Player [A/B] completed but Player [A/B] failed due to [reason]."
2. Offer options:
   - (a) Run the completed Player's output through its Coach only (single-team review)
   - (b) Retry the failed Player
   - (c) Use the completed Player's output as-is with a "single-team caveat"
3. If option (a): skip Cross-Comparison and note "Single-team analysis" in the consolidation footer.

### If both Players produce identical output

> "Both Players produced essentially the same output — full convergence. Note: same-model convergence confirms the answer is within the model's confident range but does not constitute strong independent validation. Still running Coaches and cross-comparison — they may catch issues both Players missed."

### If the task involves writing to files

- Do NOT write files during Steps 1-4
- Only write files in Step 8 (after consolidation and Commissioner approval)
- If both teams propose different file paths, flag this as a divergence item

---

## INTERACTION STYLE

- **Before spawning**: Be brief. Confirm understanding of the task, then launch Players.
- **After Step 1**: Launch Coaches immediately — do not wait for Commissioner input.
- **After Step 2**: Present all four reports (Step 3) completely. This is the Commissioner's first look at uncontaminated team outputs — do not rush or summarize excessively.
- **After Step 3**: Proceed directly to cross-comparison without pausing.
- **At the summary**: Be thorough. The convergence/divergence analysis is the core value.
- **At consolidation**: Follow Commissioner direction precisely.
- **Throughout**: Never fabricate agreement or disagreement.

## OUTPUT LENGTH MANAGEMENT

The full PACE protocol can produce 15,000-25,000 tokens across Steps 3-6. To keep the Commissioner's review manageable:

### Step 3 Progressive Disclosure
1. **Lead with Quick-Look Comparison** (3c) — orients the Commissioner before the details
2. **Present each team's SOLUTION section in full** — the core deliverable
3. **Summarize each Coach's review** as 3-5 bullet points — full text available on request
4. **Skip full METADATA sections** — extract only Assumptions and Confidence into the Quick-Look

### When to Use Full Presentation
- Mathematical proofs or derivations (exact text matters)
- Divergence is high and the Commissioner needs exact reasoning
- The Commissioner explicitly requests full reports

> **What next?** Run `/dailysummary` to capture the PACE findings before they leave context — the convergence result, any discrepancy that was resolved, and the verified deliverable are all worth preserving in your session record.

$ARGUMENTS
