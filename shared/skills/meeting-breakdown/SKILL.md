---
name: meeting-breakdown
description: Break a meeting transcript into a per-domain action plan with a PACE-style five-agent run (a conventional Player, an adversarial Player, a Coach for each, and a Cross-Reviewer; two agents on smaller plans), so every domain section carries its own decisions, next steps and deferrals. Saves the result beside the transcript as <stem>_breakdown.md. Use after an advisor, client or collaborator meeting whose transcript holds more than one thread of work. Invoke as /meeting-breakdown <transcript path or date stem>.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(wc:*), Bash(date:*), Bash(mkdir:*), Bash(shasum:*), Bash(sha256sum:*), Bash(python3:*), Agent, Skill
---

# /meeting-breakdown — per-domain meeting synthesis

**Version**: 1.0 (toolkit v2.2.0).

> **Cost**: the full run is five subagents (Players A and B, Coaches C and D, a Cross-Reviewer), each on Sonnet, and
> each reads the whole transcript: roughly 100K-250K tokens for a one-hour meeting. On a smaller plan the default is
> the **light run**, two subagents (Player A and Coach C), about two fifths of that.

## Run size

Read `claude_account` from `toolkit-config.md`. **On `pro`, `team-standard`, `unknown`, or with no answer, run the
light run**: Player A and Coach C only, and Coach C also writes the adversarial reading Player B would have given
(Step 3). Every other account runs the full five agents. Either size can be overridden in the request ("full run",
"light run"); say which size ran in the Step 0 line and in the output's metadata.

You are the **Commissioner** of a five-agent workflow that turns a meeting transcript into a per-domain plan. Each
domain section is self-contained: someone who reads only that section has the decisions, the next steps and the
deferrals for it. The protocol underneath is `/pace`: two independent framings, each reviewed by its own Coach, then
compared by a Cross-Reviewer. Without the adversarial framing the result is too agreeable; without the conventional one
it is too contrarian.

## Input

The argument is in `$ARGUMENTS`:

1. **A `.txt` path**: use it.
2. **A date or filename stem** (`4_23`, `2026-04-23`): glob `**/*<stem>*.txt` under the project and use the match. If
   several match, list them and ask which.
3. **Empty**: list the three most recent `.txt` transcripts under the project by modification time and ask which.

The transcript path is `<transcript>`, its filename without the extension is `<stem>`, and the output goes beside it as
`<stem>_breakdown.md`. If that file exists, use `<stem>_breakdown_<YYYY-MM-DD>.md`; never overwrite an earlier
breakdown.

**Project context**: if a `toolkit-config.md` exists in the project root or at `~/.claude/toolkit-config.md`, read
`project_name`, `workstreams` and `evidence_dir` from it. Without `evidence_dir`, use `.toolkit/evidence`. That folder is
`<evidence-dir>` below.

---

## STEP 0: Preflight

Count the transcript's lines (`wc -l "<transcript>"`) and print:

```
meeting-breakdown: <transcript> (<N> lines) · <full run: 5 | light run: 2> agents on sonnet · orchestrator <session model>.
```

It states and proceeds; it does not ask. Over 5,000 lines, say the run will be heavy, and offer a single-agent summary
or a split by section instead before starting.

---

## STEP 1: Load the transcript and build the Task Brief

Read the **whole** transcript, in several reads if it is long. Do not skim: the whole meeting is the input. Read the
project's `CLAUDE.md` if one exists, for its priorities and hard rules.

Then choose the **domains**, the threads the plan is organised around:

- If `workstreams` is set, use those, plus one domain for anything the meeting raised outside them.
- Otherwise, propose four to eight domains from the threads the meeting actually covered, named in the meeting's own
  words.

Show the domain list in one line and proceed. If the user corrects it, use their list.

The **Task Brief** is: the full transcript, the domain list, the project's priorities and hard rules, and the rules in
the next block, which every agent prompt carries.

> **Rules for every agent.** Cite the line number in the transcript for every direction, decision or number you attribute to someone
> (`transcript:412`). Transcription tools often label every speaker with the account that recorded the meeting, so
> decide who said something from what is said, and mark it `[speaker unclear]` when you cannot. Never write a number
> into a next step unless the transcript or a named file states it. All five agents are the same underlying model, so
> agreement between them is not independent confirmation.
>
> **FINISH DISCIPLINE.** Your job is done only when your complete output is written with the Write tool to the exact
> path you were given, and you have returned a one-line receipt ("Wrote <file>, N bytes"). If you are blocked, write
> `[BLOCKED: ...]` in the file and finish anyway. You cannot ask the user anything. Under 500 bytes of real content is
> not finished.

Create the run directory: `mkdir -p "<evidence-dir>/meetingbreakdown_runs/<YYYY-MM-DD_HHMMSS>_<stem>"`. It is
`<run-dir>` below.

---

## STEP 2: Players A and B, in parallel (the light run starts Player A only)

<!-- spawn: role=reasoner model=sonnet site=meeting-breakdown#player-a,meeting-breakdown#player-b -->
Start two Player subagents in ONE message with the Agent tool, `subagent_type: "general-purpose"`, **each with
`model: "sonnet"`** (the `reasoner` row of `references/model-roles.md`); on the light run, start Player A alone. Give
each the Task Brief. **Never write a Player's output yourself**: if the Agent tool is unavailable, stop and say so.

- **Player A (conventional).** For each domain: the direction given or proposal made, why it matters, the concrete
  next step, its timing (this week / this month / later), and the decisions the user owns. End with the five actions
  for this week, ranked. Write `<run-dir>/player_a_output.md`.
- **Player B (adversarial).** Same domains, with an explicit charge to challenge advice where it conflicts with the
  user's stated priorities and deadlines: hunt for an attention drain dressed as an opportunity, a hidden dependency,
  an item that is cheap to say yes to and expensive to do. Each item adds an "Adversarial reading" and a "Hidden cost".
  End with the three deferrals that matter most and three actions for this week. Write `<run-dir>/player_b_output.md`.

---

## STEP 3: Coaches C and D, in parallel

<!-- spawn: role=reasoner model=sonnet site=meeting-breakdown#coach-c,meeting-breakdown#coach-d -->
When both Players have written their files, start two Coach subagents in ONE message with the Agent tool, **each with
`model: "sonnet"`**. Each Coach sees only its own Player's output, the transcript, and the domain list.

- **Coach C reviews Player A**: completeness, correctness (spot-check the cited line numbers in the transcript with Read or Grep),
  attribution (whose idea, whose number), assumptions, framing bias, and the improvements that matter most, ranked.
  Write `<run-dir>/coach_c_review.md`.
- **Coach D reviews Player B**: the same, plus an over-rotation check. Did the adversarial framing go too far? Would
  following it literally damage the working relationship? Write `<run-dir>/coach_d_review.md`.

Then show the user a short Quick-Look: where the two teams' structures agree, the main divergence, each Coach's
headline finding, and any factual correction.

**On the light run**, start Coach C alone. It reviews Player A as above **and** writes the adversarial reading Player B
would have given: for each domain, the "Adversarial reading" and "Hidden cost", then the three deferrals that matter
most. Step 4 is skipped, and the consolidation uses Coach C's adversarial section where it would have used Team B.

---

## STEP 4: The Cross-Reviewer (full run only)

<!-- spawn: role=reasoner model=sonnet site=meeting-breakdown#cross-reviewer -->
Start one Cross-Reviewer subagent with the Agent tool, **with `model: "sonnet"`**. Give it structured extracts, not the
raw files: for each team, the core findings, the key assumptions, the Player's confidence, the Coach's top three
findings and the Coach's confidence. It writes `<run-dir>/cross_reviewer.md` with: where each team is stronger, what
each Coach caught, what each team alone contributed, what the consolidation must keep, which team's structure should be
the foundation, and the divergences the Commissioner must decide.

<!-- BEGIN MODEL FAILURE -->
**MODEL FAILURE — when an agent cannot run on the model it requested.**
1. **A session or weekly limit** ("You've hit your session limit"). These limits are shared across all models, so another model does not help. Stop starting agents, quote the error and its reset time, and offer two choices: wait, or stop. Do not retry.
2. **An Opus limit, or a model the account cannot use, on the Chair's `opus` request** ("You've hit your Opus limit"; "There's an issue with the selected model"). Retry the Chair once on `sonnet`. Write `fallback_from: opus` and the error text into the run report, and name the model that ran in the printed model line.
3. **Any other error, or any other role.** Stop that role, quote the error, and offer the choices: retry as written, run that role on the session's model, or stop. Never change a role's model on your own; rule 2 is the only exception.
4. Do not rely on a fallback-model setting for this: Claude Code never switches models on an authentication, billing or rate-limit error.
<!-- END MODEL FAILURE -->

`/meeting-breakdown` starts no Chair, so rule 2 never applies here.

---

## STEP 5: Consolidate (this is what the user reads)

**Decisions, next steps and deferrals go INSIDE each domain section.** No separate master plan, decision list or
deferral list at the end: a reader scans one domain at a time.

```markdown
# <Meeting title> — Per-Domain Synthesis

**Date of meeting**: YYYY-MM-DD · **Length**: ~N minutes (if inferable) · **Source**: <transcript> (N lines)
**Run**: <run-dir> (<full | light>) · **Agents**: Player A (conventional), Player B (adversarial), Coach C, Coach D, Cross-Reviewer; on the light run, Player A and Coach C

## Meeting overview
One paragraph: what was covered, and the threads the other party emphasised.

## 1. <Domain> (<status: priority / maintain / defer>)

**Decisions you own**
- **D1a. <question>** → Recommendation: **<one sentence>**. Why, with the line number in the transcript.

**This week**
1. <concrete action: the file, the command, the person> (transcript:NNN)

**This month**
2. ...

**Later**
3. ...

**Deferrals**
- <sounds good, should not be pursued now> — why not

**Raised by one Player only** (at most three; neither convergence nor divergence)
- [Player A | Player B]: <finding> (HIGH | LOW confidence)
```

Repeat for every domain, then:

```markdown
## Caveats
<attribution uncertainties, optimistic claims in the transcript, anything the Coaches flagged and the run could not settle>

## People named in the meeting
- Name (role): context, line number in the transcript

## Protocol metadata
<agents, models, convergence rate, divergences and how each was resolved, the same-model caveat>
```

**Consolidation rules**

- Use the team with the stronger structural coverage as the foundation (usually A), and lay the other team's discipline
  over it (deferrals, urgency order, hidden costs).
- **Carry every Coach correction through**, attribution errors above all: whose idea, whose number, whose decision.
  These are the highest-value catches the protocol makes.
- Never put a number in a next step that the transcript or a named file does not state. A rough number someone
  endorsed in the meeting is still unverified.
- **Weight deferrals heavily.** The easy answer in a meeting is "yes, let's do that"; the plan's default is "not this
  week" unless the item advances the user's top priority.

Write `<run-dir>/consolidated.md`, copy it to the output file beside the transcript, and show it in the conversation.

---

## STEP 6: Self-audit (mandatory)

Check the run directory mechanically before delivering anything:

1. **Files present**: `player_a_output.md`, `player_b_output.md`, `coach_c_review.md`, `coach_d_review.md`,
   `cross_reviewer.md`, `consolidated.md`; on the light run, `player_a_output.md`, `coach_c_review.md` and
   `consolidated.md`.
2. **Sizes**: each is over 500 bytes (`ls -l "<run-dir>"`).
3. **Distinct authors**: the SHA-256 of `player_a_output.md` and `player_b_output.md` differ (`shasum -a 256` on
   macOS, `sha256sum` on Linux); on the light run, compare `player_a_output.md` with `coach_c_review.md`. Identical
   hashes mean one context wrote both.
4. **No collapsed file** such as `all_outputs.md` or `agents_combined.md`.

Verdict: `verified_real` (all four pass) · `suspicious` (all pass, but an agent stalled or its file had to be saved from
its returned message: name it, and put a warning at the top of the output) · `fallback` (identical hashes, a collapsed
file, or Player files written by the orchestrator: **stop, deliver nothing**, and say the run was not independent) ·
`unverifiable` (a file missing or under 500 bytes: stop and name it).

---

## STEP 7: Run report

```bash
python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py" --command meeting-breakdown --tool-version v1.0 \
  --run-dir "<run-dir>" --outcome complete --evidence-dir "<evidence-dir>" \
  --task-summary "breakdown of <stem>" \
  --fields "agent_count=<5 or 2> run=<full|light> subagent_model=sonnet convergence_rate=<0.0-1.0> self_audit_verdict=<verdict> output=<output file>"
```

`--outcome partial` or `failed` when the run did not finish; write the report anyway.

---

## STEP 8: Deliver

Tell the user where the breakdown is, where the run evidence is, and the self-audit verdict. Then offer:

1. Show any Player or Coach output in full.
2. Expand one domain's next steps.
3. Put the actions on a numbered work list with `/list-maker` (this week → tier 1 or 2, this month → 3, later → 4), so
   `/step-by-step` can work through them one at a time.
4. Done.

## Why it is built this way

1. **Per-domain self-containment, not a master plan.** People act on one domain at a time.
2. **Two framings underneath.** Their disagreement is where the real judgment calls are.
3. **Coach review before comparison** catches attribution errors before they reach the plan.
4. **The output lives beside the transcript**, so a later meeting's breakdown can be compared with this one.
5. **Same-model caveat.** All five agents are one model; their agreement is not independent validation.
