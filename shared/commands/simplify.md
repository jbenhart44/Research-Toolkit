---
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(git:*)
description: Review changed code or documents for reuse, quality, and efficiency, then fix issues found
---

# /simplify — Code & Document Optimization Review

> **When to use**: After completing working code or a document and wanting to make it cleaner, faster, or more maintainable — without changing behavior.

You are executing the `/simplify` command. Your job is to take working code or documents and make them **better** — cleaner, faster, more reusable, more maintainable — without changing their behavior or breaking anything.

**Version**: 1.1 (2026-10-19)

**The gap this fills:** Creation is covered by planning commands such as `/pcv` and by direct implementation. But *optimization of working outputs* — reducing complexity, finding reuse opportunities, improving performance — has no dedicated workflow. This command is that workflow.

---

## WHEN TO USE

- After completing a feature or phase and wanting to clean it up before moving on
- When code works but feels messy, duplicated, or slow
- When a document is complete but could be tighter
- After `/improve` recommends tightening a slash command, reference file, or CLAUDE.md section, to do the line-level pass on that file
- When you want to check: "Is there a simpler way to do this?"

**NOT for:** Debugging broken code (fix the bug first), feature design (use `/pcv`, or `/coa` when several designs are defensible), correctness verification (use `/pace` for a question with one right answer, `/audit` for citations and numbers in a document).

---

## STEP 1: SCOPE THE REVIEW

Parse `$ARGUMENTS` to determine what to review.

**If a file path or glob is given:** Review those specific files.

**If a topic is given** (e.g., "the sweep scripts", "the data pipeline"): Use Glob and Grep to find the relevant files.

**If empty:** Review the files changed in the current session (check `git diff` and conversation context).

**Cap:** Maximum 10 files per invocation. If more are found, present the list and ask the user to prioritize.

**Shared-code folders:** Lens 1 checks for duplication against the project's shared helpers. Read `shared_code_dirs` from `~/.claude/toolkit-config.md` (paths relative to the project root). If the file or the key is missing, ask the user once, in the same message as the scope announcement, where shared helpers live — suggest any folders that look like it (`shared/`, `common/`, `utils/`, `lib/`) — and offer to save the answer to `~/.claude/toolkit-config.md` as `shared_code_dirs`. If the user skips the question, use the suggested folders plus sibling files.

**Announce scope:**
> "Reviewing [N] files: [list]. Focus: [code quality / performance / reuse / all]."

---

## STEP 2: DEEP READ

For each file in scope:

1. **Read the entire file** — not just the changed section
2. **Map dependencies** — what does this file import or include? What includes it?
3. **Check git history** — `git log --oneline -5 [file]` to understand recent evolution
4. **Identify the file's role** — production code, runner script, analysis, documentation

Once per invocation, also read the project's `CLAUDE.md` (and any rule files it points to) if present. Note every rule that governs the files in scope — for example, a requirement that empirical constants cite a source, a required language or style, or files that must not be edited. These rules outrank this command's defaults.

---

## STEP 3: FIVE-LENS ANALYSIS

Review each file through five lenses. For each finding, note the file, line(s), and a concrete fix.

### Lens 1: Redundancy & Reuse
- **Within-file duplication**: Are there copy-pasted blocks that could be a function?
- **Cross-file duplication**: Is this logic duplicated in another file? Check the shared-code folders from Step 1 and sibling files.
- **Dead code**: Are there functions, variables, or branches that are never reached?
- **Stale comments**: Do comments describe behavior that no longer matches the code?

### Lens 2: Complexity Reduction
- **Nested logic**: Can deeply nested if/else or loops be flattened? (Early returns, guard clauses)
- **Unnecessary abstraction**: Is there a wrapper or helper that is used exactly once and adds no clarity?
- **Over-parameterization**: Are there configuration options that are never varied in practice?
- **Occam test**: Could this achieve the same result with fewer lines, fewer concepts, or fewer files?

### Lens 3: Performance
- **Allocation patterns**: Are there unnecessary copies, repeated allocations inside loops, or growing collections with unknown type?
- **Type stability** (dynamically typed or JIT-compiled languages, e.g. Julia): Are there containers of type `Any`, or variables whose type changes, forcing dynamic dispatch in a hot path?
- **I/O patterns**: Is data loaded more than once? Are files opened and closed repeatedly in a loop?
- **Algorithm complexity**: Is there an O(n²) operation that could be O(n log n)?
- **Hot paths**: Are expensive operations gated behind conditions that are almost never true?

### Lens 4: Robustness
- **Error handling at boundaries**: Are external inputs validated? (File existence, parameter ranges, data quality)
- **Silent failures**: Could a bug here produce wrong results without any error or warning?
- **State leaks**: Are mutable globals used where a function parameter would be clearer and safer?

### Lens 5: Readability & Maintainability
- **Naming**: Do variable and function names communicate intent? Would a new reader understand this code?
- **Structure**: Does the file flow logically? (Setup → core logic → output → cleanup)
- **Magic numbers**: Are there unexplained constants? Empirical values should cite their source in a comment. If the project's CLAUDE.md sets a stricter citation rule, apply that rule.

---

## STEP 4: PRIORITIZE FINDINGS

Sort all findings into three tiers:

| Tier | Criteria | Action |
|------|----------|--------|
| **Fix now** | Bug risk, performance issue in a hot path, or duplication that will cause maintenance pain | Apply the fix (with user approval) |
| **Fix soon** | Code smell, mild duplication, readability issue | Draft the fix, present to user |
| **Note for later** | Stylistic preference, premature optimization, or minor cleanup | One-line mention, no draft |

**Cap:** Maximum 15 findings total. If more exist, keep the top 15 by tier and mention the overflow count.

---

## STEP 5: PRESENT FINDINGS

```
================================================================
/simplify — Optimization Review
================================================================
Scope: [N] files reviewed
Focus: [code quality / performance / reuse / all]
================================================================

## Fix Now (apply with approval)

### 1. [Title] — [file:line]
**Lens**: [which lens caught this]
**Issue**: [1-2 sentences describing the problem]
**Fix**:
```[language]
[concrete code change — before/after or the replacement code]
```
**Impact**: [why this matters — bug risk, performance, maintainability]

[repeat for each Fix Now item]

---

## Fix Soon (drafts ready)

[same format as Fix Now]

---

## Note for Later

- [one-line description] — [file:line]
- [one-line description] — [file:line]

---

## Summary
- Fix Now: [N] items
- Fix Soon: [N] items
- Note for Later: [N] items
- Estimated lines removed/simplified: [N]
- Reuse opportunities found: [N]

To apply: say "fix [N]" or "fix all now" or "fix 1, 3, 5"
```

**STOP and wait for user direction.**

---

## STEP 6: APPLY FIXES

When the user approves fixes:

1. Apply each fix using the Edit tool
2. After applying, re-read the modified file to verify the edit is correct
3. If tests exist and are runnable, run them to confirm nothing broke
4. Report what was changed

**Before a heavy test or profiling run** (long simulations, large datasets): check that the machine has memory to spare and that no other long job, such as a parameter sweep, is running that the test run could slow down or starve. Use the operating system's own tool (Activity Monitor or `vm_stat` on macOS, `/proc/meminfo` on Linux, Task Manager on Windows). If memory is tight, tell the user and ask before starting.

**If a fix turns out to be wrong or breaks something:** Revert immediately and explain why. Do not compound errors.

---

## BEHAVIORAL CONSTRAINTS

- **Never change behavior.** The output and results of the code must be identical before and after simplification. If a fix would change behavior (even for the better), flag it separately — that is a feature change, not simplification.
- **Project rules come first.** Check every proposed fix against the CLAUDE.md rules noted in Step 2 before presenting it, and again before applying it. A fix that breaks a project rule is not a fix.
- **Respect Occam's razor.** The goal is fewer moving parts, not different moving parts. Do not replace one complexity with another.
- **Do not refactor for its own sake.** Every change must pass: "Would this save time or prevent an error?" If the answer is no, skip it.
- **Do not add abstractions.** Three similar lines of code is fine. A premature abstraction is worse than duplication.
- **Respect scaffolding.** In research code, do not suggest removing features that appear unused — model components or options may be scaffolding for planned work. When in doubt, ask.

---

## EDGE CASES

### If the code is already clean
> "Reviewed [N] files. No significant optimization opportunities found. The code is clean."

Do not manufacture findings to justify the invocation.

### If the files are too large (>500 lines each, or >5 files)
Split into multiple invocations by subsystem. Suggest grouping to the user.

### If the user wants performance optimization specifically
Focus Lens 3 exclusively. Suggest profiling before changing anything, with the profiler for the language in use. For example:

- Python: `python3 -m cProfile -s cumtime script.py`
- R: `Rprof("prof.out"); run_analysis(); Rprof(NULL); summaryRprof("prof.out")`
- Julia: `using Profile; @profile run_simulation(model); Profile.print(format=:flat, sortedby=:count)`

$ARGUMENTS
