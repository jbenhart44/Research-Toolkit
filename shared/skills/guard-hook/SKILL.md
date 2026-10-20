---
name: guard-hook
description: Build a Claude Code hook guard that actually bites — a thin .sh launcher, a .py decision file that parses the payload as real JSON, an adversarial self-test proven to fail when the guard is neutered, and a validated settings.json registration. Also audits hooks already installed for six traps (payload truncation, logic in bash, no self-test, no fail-open path, a write matcher that omits MultiEdit or NotebookEdit, an if-gated registration a chained command slips past). Use when adding any PreToolUse or PostToolUse guard, or when asking whether the guards already installed are real.
allowed-tools: Bash, Read, Write, Edit, Glob, Grep, Skill, AskUserQuestion
---

# /guard-hook — a guard that has been made to fail

**Version**: 1.1 (toolkit v2.2.0). **Useful only if you use Claude Code hooks**: it builds and tests them, and
nothing else in the toolkit needs it.

The promise is not a hook file. It is **a guard whose self-test has been watched failing against a neutered version
of itself**, and which is registered where the harness will actually invoke it.

## When to use

- You are adding a PreToolUse or PostToolUse hook that is meant to stop or flag something.
- You want to know whether the hooks already in `.claude/hooks/` are real guards (`audit`).

Not for a hook that only records (a counter, a logger): there is nothing for it to refuse, so nothing to make fail.

Each rule below was paid for by a real failure. Hooks have shipped with a payload parser that truncated at the first
quote inside the JSON value, so the shapes most worth blocking were the shapes that got through. A write guard has
been registered for `Edit|Write` only, so `MultiEdit` and `NotebookEdit` bypassed it. A rule file has claimed a
self-test that did not exist on disk, with live holes behind the claim. `/guard-hook` makes those mistakes hard to
repeat.

---

## THE FIVE RULES

1. **A guard that has never failed has never been tested.** `failfirst` is not optional. If the self-test passes
   against a guard whose pattern has been removed, the test does not exercise the guard, and its clean run
   manufactures confidence rather than earning it.
2. **Bash launches; it does not decide.** The launcher is a shebang and one `exec` line. Every decision lives in
   Python, which parses the payload as real JSON.
3. **An unauthored guard is never registered.** The scaffold ships a pattern that matches nothing and stub case
   lists, so the first self-test run is red on purpose. `register` refuses while the `GUARD_HOOK-UNAUTHORED`
   sentinel stands, and refuses again if the self-test does not pass.
4. **Blocking is a choice, not a default.** A guard that cannot reliably tell a violation from a legitimate
   exception should warn, not block. An obstruction gets routed around; a warning gets read. Decide this out loud
   (Step 1).
5. **State the false positive before shipping.** Every guard has one. Name it in the docstring with its workaround,
   or the first person it stops will assume the guard is broken and disable it.

The runner below is `python3 ~/.claude/skills/guard-hook/assets/guard_hook_run.py` (written `guard_hook_run.py` from
here on). It works on `$CLAUDE_PROJECT_DIR/.claude/hooks/` and `.claude/settings.json`, or on `--hooks-dir` and
`--settings` if you pass them.

---

## STEP 1 — `/quick-ten` on THIS guard

Run `/quick-ten` before writing anything, on the specific guard being built. Seed it with these five, which are the
judgment the script cannot make:

- **Which rule does this enforce, and where is it written?** A guard with no citable rule cannot be adjudicated
  later. If there is no rule yet, write the rule first.
- **Blocking or advisory?** Blocking when the violation is unambiguous and the damage is not reversible (attribution
  in permanent git history, a delete inside a shared folder). Advisory when correct exceptions exist and cannot be
  told apart mechanically.
- **Which tools carry the thing you are guarding?** If the answer is "file writes", it is all four of `Edit`,
  `Write`, `MultiEdit`, `NotebookEdit`, in `TOOLS` *and* in the matcher. `NotebookEdit` names its file
  `notebook_path` and its text `new_source`; the generated guard reads both.
- **`deny` or `ask`?** `deny` where a single call cannot be undone; `ask` where a person looking at the specific
  call is the right check.
- **What is the acceptable false positive?** Name the legitimate lookalike this guard will catch, and the
  workaround. If you cannot name one, the pattern is probably too narrow to work.

Write the answers into the generated docstrings. `/quick-ten`'s own skip valve applies: if the request already
answered all five, say so and continue.

## STEP 2 — Scaffold

```bash
python3 ~/.claude/skills/guard-hook/assets/guard_hook_run.py new \
  --name <lower_snake> --posture blocking|advisory \
  --tools "Bash"   # or "Edit,Write,MultiEdit,NotebookEdit" \
  --decision deny|ask \
  --rule "<the rule and where it is written>" \
  --reason "<what the user sees, including how to proceed legitimately>" \
  --false-positives "<the legitimate lookalike, and the workaround>"
```

Writes three files into `.claude/hooks/` and stops on any name collision (exit 2). Nothing is registered. Confirm
the fresh self-test **fails**: that red is correct.

## STEP 3 — Author the guard

Two edits, both judgment:

- **`TRIGGER`** in `<name>.py`. Prefer an explicit list over a clever morphology: an `-ise -> -ize` regex looks
  obvious and wrongly flags *advise, comprise, surprise, otherwise*. Add `re.IGNORECASE` only if case truly does
  not matter: a git guard must tell safe `branch -d` from force `branch -D`.
- **`MUST_BLOCK` / `MUST_PASS`** in `<name>_selftest.py`. Author the shape that motivated the guard, then every
  evasion you can construct: a quoted argument, a `&&` chain, a flag that takes an argument (`git -C <dir>`), case
  variation, and the same operation wrapped inside a quoted Python string. `MUST_PASS` matters as much: the
  read-only lookalike, the other tool, the substring that is not a real match. Those cases keep the guard usable.

Delete both sentinel lines when done.

## STEP 4 — Prove it bites

```bash
python3 ~/.claude/skills/guard-hook/assets/guard_hook_run.py failfirst --name <name>
```

Neuters `TRIGGER`, runs the self-test, requires it to fail, restores the file and verifies the checksum, then
requires a clean run. **Exit 6 means the self-test passed against a neutered guard**: the cases do not touch
`TRIGGER`, and the honest fix is better cases, never a louder claim.

## STEP 5 — Register

```bash
python3 ~/.claude/skills/guard-hook/assets/guard_hook_run.py register --name <name> --matcher "Bash"
```

Backs up `settings.json`, inserts one unconditional entry, re-parses, and rolls back on any failure (exit 5).
Refuses an unauthored guard (3) or a failing self-test (4). Registering the same entry twice is a no-op.

Register **once, unconditionally**. Do not add an `if:` condition: it matches only commands that *begin* with the
verb, so `git add -A && git push --force` matches no `if: Bash(git push *)` and the hook is never invoked for the
shape most likely to destroy work. Filter inside the Python instead.

**Test it with one live call before reporting it active.** A hook added mid-session has been seen both to fire at
once and not to fire until the next session. Until a live call has been refused (or flagged), say the guard is
registered, not that it is working.

## STEP 6 — Draft the rule file, and hand it over

Write a draft recording the rule, the posture and why, the self-test command and its count, the fail-first result,
and the named false positive. **Do not install it into `.claude/rules/` yourself**: a rule file with no `paths:`
frontmatter loads into every session, so where it goes is the user's call.

Record the real count. A rule file claiming a self-test that does not exist is worse than one claiming nothing,
because it stops anyone from looking again.

## STEP 7 — Commit (HUMAN GATE)

**Stop and ask.** Stage by explicit path, never `git add -A` or a directory pathspec.

If the commit message describes the guard, a guard that tests command text (such as one that blocks deletes of named
paths) may block the commit on its own prose: it tests the raw command string and cannot tell a description from an
instruction. Use `git commit -F <message-file>` so the prose never reaches the command line. Do **not** reword the
message to get past the matcher.

---

## AUDIT MODE

```bash
python3 ~/.claude/skills/guard-hook/assets/guard_hook_run.py audit
```

Exit 0 clean, 7 on any finding. Six traps, each one a real incident:

| Trap | What it means |
|---|---|
| `grep_o_truncation` | Shell payload parsing that stops at the first quote inside the JSON value. |
| `logic_in_bash` | Decisions made in `.sh` with no `.py` alongside. |
| `no_selftest` | No `_selftest.py`. The guard has never been made to fail. |
| `no_failopen` | No parse-error path: a malformed payload is indistinguishable from a clean pass. |
| `narrow_write_matcher` | The matcher names `Edit`/`Write` but omits `MultiEdit` or `NotebookEdit`, which then bypass it. |
| `if_gated` | A registration behind an `if:` prefix pattern that a chained command slips past. |

Audit reports; it never edits and never removes. Fixing a flagged hook is a separate decision for the user.

---

## VERIFICATION OF THIS SKILL

From a clone of the toolkit (the installer copies the runner, not its tests):

```bash
python3 shared/skills/guard-hook/assets/guard_hook_selftest.py     # 26 cases, each in a throwaway sandbox
python3 shared/skills/guard-hook/assets/guard_hook_mutations.py    # each planted defect must turn its case red
```

The headline case is `INERT-TEST-DETECTED`: a guard whose self-test passes with its `TRIGGER` removed, which
`failfirst` must catch as exit 6. No real hook, settings file or project path is touched.

---

## GUARDRAILS AT A GLANCE

- [ ] Did `/quick-ten` run on this specific guard before anything was written?
- [ ] Is the posture a decision someone made, rather than a default?
- [ ] If it guards writes, does it name all four write tools, in `TOOLS` and in the matcher?
- [ ] Did the fresh scaffold's self-test fail before the guard was authored?
- [ ] Did `failfirst` exit 0, having actually watched the neutered guard fail?
- [ ] Is the named false positive in the docstring, with its workaround?
- [ ] Is the registration unconditional, with no `if:` prefix?
- [ ] Has one live call been refused or flagged before the guard is called active?
- [ ] Is the rule-file draft handed over rather than installed?
- [ ] Did the user approve the commit, by explicit path?
