---
name: automate
description: Turn a task you just finished into a reusable skill. Reconstructs what was actually done from the conversation and from disk, splits it into the deterministic part (extracted into a real runnable script) and the judgment part (prose in SKILL.md), runs /quick-ten so version 1 is aimed right, then proves the generated skill reproduces the original result before calling it done. Use after completing a complex multi-step task you expect to repeat.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(mkdir:*), Bash(git:*), Bash(python3:*), Bash(date:*), Bash(wc:*), Bash(chmod:*), AskUserQuestion, Skill
---

# /automate — turn a finished task into a skill

**Version**: 1.0 (toolkit v2.2.0). Needs `/quick-ten`, which ships with it; `/bulletproof` is used at Step 6
when it is installed.

The job: **take a complex task that is already complete, and turn it into an installed skill that does as much of it
automatically as the task honestly permits.**

The promise is not "a skill file". It is **a skill whose deterministic core actually runs, and which has been shown to
reproduce the result the original task produced.** A generated skill that only re-describes the work in prose has
automated nothing.

---

## The six rules

1. **Automate what was done, not what you imagine was done.** Every step in the generated skill traces to evidence: a
   command that ran, a file that changed, a decision the user made. No evidence, no step. Where the record is thin,
   write `[GAP: <what is unknown>]`.
2. **Split before you write.** Classify every step as DETERMINISTIC, PARAMETRIC, JUDGMENT or HUMAN (Step 2) and state
   the automatable fraction out loud. The split decides what becomes code and what stays prose.
3. **`/quick-ten` runs twice**: once now, on the skill being built, and once inside every run of the skill you
   generate. See Steps 3 and 5.
4. **The generated script is verified by being made to fail.** A self-test that has only ever passed has not been
   tested. Ship at least one must-fail case and watch it fire (Step 6).
5. **Logic lives in a real program.** Python by default, or the language the project's own rules name for that kind
   of work. A shell command only launches the program or runs git; it never computes the result.
6. **New files only.** `/automate` writes a skill that does not yet exist. It never overwrites an existing `SKILL.md`,
   never removes anything, and stops to ask if the name is taken. `--revise` (Step 8) improves an existing one.

---

## STEP 0 — Is this task actually automatable?

Answer three questions in one line each. If any answer is no, say so and **stop**: a skill for a one-time task is pure
overhead.

- **Finished?** The task is complete, with a result on disk. `/automate` reads outcomes, not intentions.
- **Repeatable?** Will this shape of task recur? Once more is enough. Never is not.
- **Stable?** Would a repeat run touch roughly the same tools, files and decisions? A task whose every step depends on
  context that will not recur is a judgment call, not a procedure.

If the task is repeatable but almost entirely judgment, say so and offer a **checklist skill** instead (prose only, no
script). Do not manufacture a script for work that has no deterministic core.

---

## STEP 1 — Reconstruct the trace from evidence

Build an ordered list of what actually happened. Sources, in priority order:

| # | Source | How to read it |
|---|---|---|
| 1 | **This conversation** | Every tool call, command, file write and user decision for this task. |
| 2 | **Git** | `git log --stat` and `git diff --name-status` across the task's commits: what really changed, including what the conversation summarised away. |
| 3 | **Session notes** | The daily summary for the task's date, if the project keeps them (`summary_folder` in `toolkit-config.md`). Catches decisions made in an earlier session. |
| 4 | **The artifacts** | The files the task produced. Their structure is the specification for what a repeat run must produce. |

Write the trace as a numbered list. Each entry gets **what was done**, **the concrete command or file**, and **why**
(the decision behind it, if there was one). Show the trace to the user before continuing: they were there, and they
will spot a missing step faster than you will.

---

## STEP 2 — Classify each step, and state the automatable fraction

| Tag | Meaning | Goes to |
|---|---|---|
| **DETERMINISTIC** | Same inputs, same outputs, every time. | The script. |
| **PARAMETRIC** | Same shape, different input each run (a date, a path, a name). | The script, as an argument. |
| **JUDGMENT** | Needs a model to read, weigh or write something. | SKILL.md prose. |
| **HUMAN** | Needs the user's decision, approval or knowledge. | A question in the prose. |

Then one line the user can hold you to:

```
Automatable fraction: <N> of <M> steps are DETERMINISTIC or PARAMETRIC (<pct>%).
Script covers: <steps>.  Prose covers: <steps>.  Human gate at: <steps>.
```

**A HUMAN step is never promoted to DETERMINISTIC to raise the fraction.** If the original task had the user approve
something hard to undo (a push, a delete, a send, a change to a shared folder), that approval survives into the
generated skill as a mandatory stop. Automating away a human gate is the one failure of this skill that does real
damage.

---

## STEP 3 — Run `/quick-ten` on the skill being built (mandatory)

Invoke the `quick-ten` skill. **The subject is the skill under construction, not the finished task**: nothing about
the task is still open, and the questions that matter are about the future runs. Seed it with the questions that fork
a generated skill, and let it cut the ones already answered:

- **What varies between runs?** (The script's arguments.)
- **What must never be automated?** (Where the human gates go.)
- **Done criteria**: how does a run prove it worked?
- **Failure posture**: stop and ask, or continue and report? (Whether the script exits non-zero or warns.)
- **Invocation**: bare `/name`, or does it take an argument?
- **Scope**: this project only (`.claude/skills/`) or every project (`~/.claude/skills/`)?
- **Precedent**: an existing skill whose shape this should match?

`/quick-ten`'s own rules apply in full: at most ten questions, no floor, every question carries a build-divergence tag,
and a recap before the build. Its brief becomes `BRIEF.md` in the generated skill's folder, and the generated
`SKILL.md` cites it. If `/quick-ten` skips itself because the answers are already in the conversation, record that in
the brief and move on.

---

## STEP 4 — Name it, and check for a collision

Pick a short, lowercase, verb-like name. It becomes `/<name>`, so it shares a namespace with every command and skill
already installed, including Claude Code's built-in ones. Before writing anything, check that none of these exists:

```
.claude/skills/<name>/SKILL.md        ~/.claude/skills/<name>/SKILL.md
.claude/commands/<name>.md            ~/.claude/commands/<name>.md
```

and that `/<name>` is not a built-in command. Report one line: `COLLISION CHECK: /<name> -> clear`. **On any
collision, stop and ask** for another name, or for permission to revise the existing skill (Step 8). Never overwrite.

---

## STEP 5 — Write the skill

Into the scope Step 3 chose:

```
<skills>/<name>/
  SKILL.md                     the procedure: judgment, orchestration, human gates
  BRIEF.md                     the /quick-ten decisions this skill is accountable to
  assets/<name>_run.py         the DETERMINISTIC and PARAMETRIC steps, runnable
  assets/<name>_selftest.py    must-pass and must-fail cases
```

**`SKILL.md`** has YAML frontmatter with `name:` (matching the folder), `description:` (what it does and when to reach
for it, written so a future session recognises the moment), and `allowed-tools:` limited to what the procedure needs.
The body states its version and origin (`generated by /automate from <task>, <date>`), puts the human gates in bold,
says how to run the script, and cites `BRIEF.md`.

**The generated `SKILL.md` opens with its own `/quick-ten` gate.** Every step Step 2 tagged JUDGMENT or HUMAN is a seed
question for it: those are exactly the decisions the script cannot make, and leaving them to a default is how a
generated skill produces a plausible artifact aimed at nobody's actual problem. Write them as the skill's Step 1,
phrased for the future run:

- Name each question so that a different answer visibly changes the output.
- Give the recommended answer and why, so the gate is quick to clear.
- Keep `/quick-ten`'s skip valve: if the request already answered them, say so in one line and continue. A gate that
  cannot be skipped when it has nothing to ask becomes friction, and friction gets routed around.
- Put `Skill` in the generated `allowed-tools` so it can invoke `quick-ten`, and `AskUserQuestion` if it asks directly.

`BRIEF.md` records the decisions made once, at generation; the embedded gate makes the per-run ones. Do not collapse
the two: a decision locked at generation is a property of the skill, and a decision made per run is a property of the
job.

**The script** takes the PARAMETRIC values as real command-line arguments, with defaults where the original task had
one. It prints what it did. **It exits non-zero when it could not do its job**: a script whose exit code is always 0
is invisible to every caller.

**Carry the project's standing rules into the generated `SKILL.md`**, because a subagent running the skill may not
have read the project's `CLAUDE.md`. If the skill commits, it stages by explicit path. If it writes a document others
will read, it leaves a `[GAP: …]` rather than a guessed number. If it sends, pushes or publishes, it stops for
approval each time.

---

## STEP 6 — Verify: run it, and make it fail

Nothing is reported as working until this step passes. Three checks, in order:

1. **The self-test runs.** `python3 <skills>/<name>/assets/<name>_selftest.py`. Report the count as `N/N`.
2. **A must-fail case fires.** The self-test holds at least one case the script must reject. Confirm it is rejected.
   If the script has a guard, break the guard's input on purpose and watch it catch. If `/bulletproof` is installed,
   use it here: it injects the defect each guard exists to prevent and requires the named checks to go red.
3. **Reproduction.** Run the generated script on the *original task's* inputs and compare its output with what the
   original task produced. Report it honestly:
   - **Reproduced**: the output matches. Say what you compared.
   - **Partial**: it matches except for named differences. Name them.
   - **Not reproduced**: say so plainly, and leave the skill installed with the gap recorded at the top of its
     `SKILL.md`. Do not quietly downgrade the claim to "the script runs".

Reproduction is the whole proof. A skill generated from a task it cannot re-perform is a summary of that task.

---

## STEP 7 — Report

```
INSTALLED  /<name>  ->  <skills>/<name>/
Automated  <pct>% of the traced steps (<N>/<M>).
Script     assets/<name>_run.py  (<what it does, one line>)
Human gate <where the user must still decide, or "none">
Verified   self-test N/N; must-fail case fired; reproduction: <reproduced | partial: … | not reproduced: …>
Orphans    <any folder this run created under a name that was then abandoned, or "none">
```

**Name the orphan if the name changed mid-build.** Step 4's collision check runs before Step 5 writes anything, so it
cannot help when the user renames the skill after files exist. The abandoned folder then holds an older copy of the
script, which is hazardous if anyone runs it. `/automate` never removes it; the report names its path and says it
holds an older copy, so the user can decide.

**Confirm the skill is loadable rather than assuming.** A newly written `SKILL.md` has been observed to become
invokable in the same session. If `/<name>` does not appear after writing, say so and suggest a restart; do not state
a restart is needed when it is not.

---

## STEP 8 — `--revise`: the second pass that makes it good

Version 1 is a hypothesis. After the skill has been used for real:

```
/automate --revise <name>
```

This mode reads the existing `SKILL.md`, `BRIEF.md` and script, gathers what went wrong in the run that just happened
(from the conversation and the skill's own output), and proposes edits. **It shows the diff and waits**: a revision
changes a working artifact, so it needs the user's OK. It may add steps; it removes one only when the user names it.

Put anything the revision teaches into the brief. A lesson that lives only in a conversation is not a guard.

---

## Guardrails at a glance

- [ ] Is the task finished, repeatable and stable?
- [ ] Does every generated step trace to evidence, with `[GAP:]` where it does not?
- [ ] Did I state the automatable fraction as a number?
- [ ] Did every HUMAN approval in the original survive as a mandatory gate?
- [ ] Did `/quick-ten` run, aimed at the skill and not the finished task?
- [ ] Does the generated skill open with its own `/quick-ten` gate, with a working skip valve?
- [ ] Did the collision check pass before I wrote a file?
- [ ] Is the logic in a real program, with a real non-zero exit?
- [ ] Did I run the self-test AND watch a must-fail case fire?
- [ ] Did I report reproduction honestly, including "not reproduced"?

## Invocation

- `/automate`: infer the just-finished task from the conversation and build a skill from it.
- `/automate <describe the task>`: build from the named task, reconstructed from git, session notes and its artifacts.
- `/automate --revise <name>`: improve a generated skill after real use (Step 8).
- `/automate --dry-run`: run Steps 0 to 4 and show the trace, the classification and the proposed name; write nothing.

`/automate` creates files and never destroys them. It states what it could not automate as readily as what it could:
the honest fraction is the useful number, and a skill claiming more coverage than it has costs more than the manual
task it replaced.
