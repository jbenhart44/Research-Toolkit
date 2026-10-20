---
name: bulletproof
description: Put real tests behind a piece of functionality you are about to build or just built - written before the code where possible, at the right level (unit for pure functions, integration for served pages, tooling for fetchers and guards), registered in the project's runner, and then PROVEN non-vacuous by injecting the defect each new guard exists to prevent and watching named checks go red. Use whenever new functionality lands, or when an existing suite has never been watched fail.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(python3:*), Bash(node:*), Bash(npm:*), Bash(ls:*), Bash(chmod:*), Bash(git:*), AskUserQuestion, Skill
---

# /bulletproof — tests that would actually notice

**Version**: 1.1 (toolkit v2.2.0).

**The promise is not "tests exist." It is "these tests have been watched go red for the right reason."** A green
suite is a claim that the tests would notice a defect. Only a mutation makes that claim true. When this procedure was
applied to eight features of one web application in a row, mutations caught **six tests that passed for the wrong
reason**, every one written by someone who believed they were testing the thing.

## When to use

- New functionality has landed, or is about to: put tests behind it, written first where possible.
- An existing suite has never been watched fail.

The runner below is `python3 ~/.claude/skills/bulletproof/assets/bulletproof_run.py` (written `bulletproof_run.py`
from here on). Its `scaffold`, `register`, `check` and `audit` commands fit a pytest-shaped tree; Question 0 says
whether yours is one.

---

## Step 1 — The gate (skip it when the request already answered it)

Four questions fork the work. If the request already answers them, say so in one line and go to Step 2: a gate with
nothing to ask is friction, and friction gets routed around.

**Question 0 comes first, because it decides which Step 2 you are in.** Answer it mechanically, not by looking at
the language:

```bash
python3 -c "import pathlib,glob; r=pathlib.Path('.'); print('pytest' if (r/'tests/run_all.py').exists() else 'per-tool' if glob.glob('**/*_mutations.py',recursive=True) else 'hand-rolled')"
```

| It prints | The tree is | Step 2 is |
|---|---|---|
| `pytest` | **pytest-shaped** | `bulletproof_run.py scaffold`, the default path below |
| `per-tool` | **per-tool Python** | add cases to the tool's own `self_test()`, mutations in a sibling `<tool>_mutations.py`. **Do not scaffold.** See "When the tree IS Python but the idiom is not pytest" |
| `hand-rolled` | **not Python**, or nothing established yet | hand-roll the runner in the analysis's language. See "When the tree is not Python" |

This toolkit's own tree answers `per-tool`: every gate carries a `--self-test` and a `<gate>_mutations.py`.

Then:

1. **What level does this behaviour live at?** Pure function: unit test (fast, exhaustive, fabricated inputs).
   Served page or route: integration test against a real local server. A fetcher, build step or guard: tooling test
   on crafted inputs. **Recommended: the lowest level that can see the behaviour**, plus one integration check that
   the wiring is real.
2. **What is the defect this guard exists to prevent?** Name it as a sentence before writing anything. It becomes
   the mutation. If you cannot name it, there is no guard here: you are describing code, and a test that describes
   code cannot fail usefully.
3. **Is anything here honestly untestable right now?** Say so and record it as a stated gap rather than letting a
   green run imply cover. (Worked case: a leaderboard's scoring-mode flag could not be caught until real scores
   existed, because with no games played both modes render identical pages. That was written down, not hidden.)

Ask with `AskUserQuestion` only if an answer genuinely changes the work.

---

## Step 2 — Write the test first, and watch it fail

**Only if Question 0 said pytest-shaped.** In a per-tool tree this command writes files nothing reads; go to "When
the tree IS Python but the idiom is not pytest", and come back here for everything from "Every assertion names the
element it reads" onward, which holds in any idiom.

```bash
python3 ~/.claude/skills/bulletproof/assets/bulletproof_run.py scaffold <name> --tests tests
```

The scaffold lands full of `[GAP: ]` markers on purpose. Fill them in **before** the code exists, then run it and
watch it go red. A suite written after the code tests the code you happened to write rather than the behaviour you
meant, and the red run is the only proof the test can fail at all.

**Every assertion names the element it reads.** Five of the six false passes came from this, so it is not a style
note:

| The check that passed for the wrong reason | What it was actually reading | The fix |
|---|---|---|
| "a 16-game week shows 32 logos" | the whole page: a side panel added 14 of its own | count inside the games list |
| "the group says week by week" | a navigation button in the page chrome | read the group's own lede paragraph |
| "dark logos get a light plate" | the CSS *selector*, still present with every declaration deleted | read the `background` property out of the rule body |
| "a pick after the season is refused" | a redirect that fires for an unfinished season whatever the lock says | seed a player with every pick made first |
| "the member reads as Finished" | the first status anywhere on the page | read the viewer's own table row |

**A positive control comes first.** "It refused" is evidence only if something that should work demonstrably does
in the same run; an expired session, a wrong path and a working guard all produce identical refusals. Pair every
refusal with an acceptance.

**Make every guard refuse on purpose.** A fetcher that shipped with five validity checks had never once said no.
Hand each check the thing it exists to reject (a value off the allowed step, one out of range, an id the source
does not have), require the refusal, and pin the edge case that must still be allowed.

---

## Step 3 — Register it, or a full run skips it

```bash
python3 ~/.claude/skills/bulletproof/assets/bulletproof_run.py register <name> --tests tests
```

Idempotent. Adds the suite to the project's runner and to the mutation check's `SUITES` dict: both, because a suite
missing from the second can never be pointed at by a mutation, the state the audit calls "never watched go red".
Edit the printed label to say what the suite covers.

---

## Step 4 — Add the mutation. This is the step that makes it real

Add an entry to `tests/mutation_check.py` that injects the defect from Step 1 and names the checks that must go red:

```python
(
    # Why this defect matters, in a sentence a stranger could act on.
    "a short statement of the WRONG behaviour",
    FILE_CONSTANT,
    [("the exact source line", "the broken version")],
    "<suite key>",
    ["the check that must fail", "and any other"],
),
```

Four rules:

- **The mutation must produce a WORKING program that behaves wrongly.** A mutation that breaks the syntax stops the
  suite before it reaches the named checks, and the run reports a stale expectation instead of a defect. Broken code
  tests nothing.
- **Defence in depth needs both gates removed.** A behaviour held by two independent checks stays correct when one is
  removed, which proves nothing.
- **A structural invariant may be un-mutatable, and that is a finding.** When a property is guaranteed by the shape of
  the data (one record per key, because the key is the record), removing the code that also enforces it changes
  nothing observable. Record that the invariant is structural, and mutate the structure if you can.
- **Name checks that CAN fail.** An expectation naming a sentence the page never prints reports as an uncovered guard
  forever.

---

## Step 5 — Prove it, and read STALE as "moved", not "missing"

```bash
python3 ~/.claude/skills/bulletproof/assets/bulletproof_run.py check "<filter>" --tests tests
python3 ~/.claude/skills/bulletproof/assets/bulletproof_run.py audit --tests tests
python3 tests/run_all.py
```

`check` runs the mutation set and **exits non-zero on any `NOT DETECTED` or STALE**. `audit` refuses if any suite is
unregistered or has no mutation behind it.

**`audit` matches an f-string check name by template, not by string equality.** A check built as
`check(f"{kind}: offers exactly {expected}", ...)` emits a name no mutation can name statically; the audit treats
each `{placeholder}` as a wildcard, and is strict about partial matches so it does not become vacuous. A tool that
reports a working guard as missing trains people to ignore it.

**`STALE EXPECTATION` / "a mutation target no longer exists" means an anchor MOVED, not that a guard is missing.**
When code moves into a shared module, every mutation anchored on it goes stale at once. The honest fix is to re-point
each anchor at the file the code lives in now. Reading STALE as a hole sends you hunting defects that do not exist;
reading it as nothing lets a mutation quietly stop testing.

**When the harness refuses because some other suite's baseline is red, narrow the run; do not bypass the harness.**
Add a `--only <targets>` flag that runs, and baselines, only the named targets, and have its summary say how many
mutations were NOT run and that this is not a verdict on them. Then re-run in full once the other suite is green. If
you add such a flag, prove it with two harness mutants: one that ignores `--only`, one that narrows the mutations but
not the baselines.

Done means: the new suite is green, every new mutation reports `DETECTED`, `audit` exits 0, and any untestable
guard is written down as a gap.

---

## When the tree is not Python: keep the steps, hand-roll the runner

The runner's commands are pytest-shaped, and a gate is written in the language of the analysis it checks: a Julia
model gets a Julia gate, so it gets a Julia self-test too. **The steps transfer completely. Only the tooling does
not.**

| Step | Python tree | Non-Python tree |
|---|---|---|
| 2: write the test first | `bulletproof_run.py scaffold` | write `selftest/<gate>_selftest.jl` by hand, in the gate's language |
| 3: register it | `bulletproof_run.py register` | add it to whatever the project already runs; if nothing runs it, say so as a stated gap |
| 4: the mutation | an entry in `tests/mutation_check.py` | build mutated COPIES of the gate in a scratch folder and run the suite against each |
| 5: prove it | `bulletproof_run.py check` | one line per mutation: exit code, count of red cases, and WHICH ones |

**Give the self-test a way to point at a different gate**, or step 4 is impossible. One environment variable or one
`--gate <path>` argument is the whole mechanism:

```julia
const GATE = let i = findfirst(==("--gate"), ARGS)
    i === nothing ? joinpath(@__DIR__, "..", "scripts", "<gate>.jl") : ARGS[i+1]
end
```

**The bar does not move.** Every mutation leaves a WORKING gate that behaves wrongly, each turns exactly the case
aimed at it red, and the run that proves it goes in the report. A mutation that breaks the script instead of
disabling a check turns nearly every case red; **compile the mutation before running it.**

**The strongest fixture is often already on disk.** A real earlier version of a document that had the defect, copied
in and hash-pinned, beats an imagined one: nobody has to guess what going wrong looks like.

## When the tree IS Python but the idiom is not pytest

Recognise it by two marks: each tool carries its own `--self-test`, and mutations live in a sibling named for the
tool (`check_claims_mutations.py`). One suite per tool, not one per feature.

| Step | pytest tree | per-tool tree |
|---|---|---|
| 2: write the test first | `scaffold` | add cases to the tool's own `self_test()`, with its existing `check(label, cond)` helper |
| 3: register it | `register` | add the tool's `--self-test` and its mutations file to the tree's runner or CI |
| 4: the mutation | a `tests/mutation_check.py` entry | a sibling `<tool>_mutations.py` that writes a mutant, runs its `--self-test`, and names the cases that must go red |
| 5: prove it | `check` / `audit` | run the mutations file; it exits non-zero on any mutant not caught |

Three things this idiom teaches:

- **Write the mutant NEXT TO the real tool, not in a scratch folder,** when the tool finds its siblings or its repo
  root from its own `__file__`. A copy run from elsewhere fails for reasons unrelated to the mutation and reports a
  false red. (A tool that imports nothing from its folder can be mutated anywhere.)
- **A guard written inline inside a function that only runs on the happy path is untestable, and the mutation is
  what proves it.** If disabling a check leaves every case green, suspect the guard's location before the mutation:
  extract it into a function that takes its inputs, and the same mutation turns its case red.
- **Register the gate wherever the tree registers gates.** A gate nothing runs is indistinguishable from a gate that
  passes.

---

## A check is a script on disk, reusable, or it is not a check

**When you verify something, write the verification as a script and leave it on disk.** Not a grep in a transcript,
not a one-off `python3 -c`, not a paragraph in a report saying it was checked: a script with a name, a
`--self-test`, and an exit code. A verification that lives only in a session transcript is evidence, not a guard: it
cannot be re-run, so it cannot catch the same defect twice. Worse, a document that CLAIMS a self-test that does not
exist stops anyone looking again.

**The test of reusable**: could someone re-run it in six weeks, on a changed tree, without you? If the answer needs a
person to remember something, it is not a check yet.

| Write a script | Not a script |
|---|---|
| a property that must hold on every build | a one-time question about today's tree |
| anything that will be claimed in a report | reading a file to understand it |
| anything a person would otherwise remember | an exploratory search |

**Put it where the thing it guards is built**, so the build runs it rather than a person choosing to.

**Two failure modes to write against:**

- **A check pinned to a transient state.** A self-test that asserted a file was missing from an allowlist was true
  when written and false ten minutes later, when the allowlist was fixed, and the suite went red. A test that has to
  be deleted to make the suite pass is how suites get deleted. Test the FUNCTION against synthetic inputs, both ways,
  and let the live run report live state. The same holds for a one-shot migration: its self-test must not assert the
  pre-migration state, or it goes red the moment the migration succeeds.
- **A check pointed at the wrong artifact.** A gate on the source that was correct all along, while the artifact that
  was wrong was the PUBLISHED copy, passes; and a pass is indistinguishable from correctness.

## Three hazards of any tree-wide rename

1. **An untracked file makes `git mv` refuse, and the sweep continues.** The tree is left half-moved. Check
   `git status` after any sweep.
2. **A blanket string replacement rewrites test fixtures that must contain the old string.** A case asserting "this
   name has an underscore and must be rejected" can have its fixture rewritten into a valid name, after which it
   asserts that a valid name is invalid. Write fixtures against values no real file uses.
3. **A migration tool can rewrite its own mapping table**, every key becoming its own value, destroying the record of
   what it did. A migration tool excludes itself from its own sweep, by resolved path.

## Anything others will run is run as they run it, before they use it

A validation of something other people will execute (a skill, an installer, a handout with commands) is performed on
the **deployed copy, executed the way they execute it**, and close to when they will use it. Four questions, in
order:

1. **Is the deployed copy the one you validated?** Compare bytes (a hash, not a version number) on the copy they
   actually pull.
2. **Is that copy current with its remote?** A clone behind its remote is not what they have.
3. **Read it as the reader receives it**, top to bottom, in its own voice, not as a diff: a diff shows what changed
   and hides what it now says. Text pasted verbatim from an internal record into a user-facing file can be true in
   every line and still not be theirs to read.
4. **Run the path it describes**, with the commands it gives, in a scratch copy.

A file you are editing is not the file that runs: when an installed copy and a working copy drift, the procedure
being followed is the old one.

## A committed build product is a claim about code that has since moved

A green suite proves the generator works today. It says nothing about the PDF, rendered page or generated CSV sitting
beside it, which was produced at a commit nobody recorded.

- **Stale.** Same path, same name, built from older code. The guard: rebuild into a scratch path and compare with the
  committed artifact, refusing on drift. For a PDF, compare the extracted text or a page-image hash rather than the
  bytes, since timestamps and font subsetting move on every render.
- **Silently thinner.** A parser change upstream can make a composed artifact lose a section while every file it is
  composed from stays correct. No test fails, because nothing is wrong with either file. The guard: a composed
  artifact asserts its **content** (the sections it must contain), not its exit code. The mutation that proves it:
  delete one section from the composed output and watch the named assertion go red.

**When a test reads a description of an artifact rather than the artifact, it is measuring the description.** Point
it at the thing.

## Standing rules that bind any run of this skill

- **Never write over an existing suite** and never remove one without the user naming it.
- **Language follows the analysis.** A gate is written in the language of what it checks; Bash launches a program or
  does git and never holds logic.
- **No invented values in a fixture that stands in for real data.** A fabricated line, score or date inside a unit
  test is fine and named as fabricated; a number presented as real needs a source.
- **State the gap.** A guard that cannot be tested yet is reported as such, with what would make it testable.
- **A guard over a composed or rendered artifact asserts its CONTENT.** "The build exited 0" and "the page has the
  three sections on it" are different claims, and only the second survives a parser change upstream.
- **Fail closed when the reference is unreachable.** An absent comparison source is reported as unverified, with a
  non-zero exit, never as a pass: an unreadable source and an unchanged one look identical from here.

## Verification of this skill

From a clone of the toolkit (the installer copies the runner, not its tests):

```bash
python3 shared/skills/bulletproof/assets/bulletproof_selftest.py
python3 shared/skills/bulletproof/assets/bulletproof_mutations.py
```

## Related

`/guard-hook` (the same discipline for hooks).
