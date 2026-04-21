# Processing Student Submissions — JIT Reference

**Type**: Reference recipe, not a command.
**Audience**: Instructors who want to cluster / extract / summarize a batch of student submissions using existing toolkit commands.
**Version**: v1.1 (2026-04-17)

---

## Why This Is a Reference, Not a Command

Kay flagged in an advisor conversation: "the key is to have that thing, you know, between when a student submits something" — i.e., a feedback loop from student work to grading/response.

We considered building a `/feedback` or `/grading-rubric` command for v1.1 and rejected both. Reasons documented in `ai-research-toolkit/DESIGN.md`:

1. **No premature implementation.** No instructor has run this loop end-to-end in a classroom yet. Building it speculatively would produce a command whose prompts don't match actual classroom needs.
2. **Existing commands already do this.** `/pace` + `/audit` + `/dailysummary` already cover citation-checking, multi-agent review, and submission-tracking. A new command would duplicate capability.
3. **Course workflow ≠ student command.** What Kay needs is HIS grading workflow. That's an instructor-side recipe, not something every student runs.

Instead: this JIT reference file documents the recipe. Adapt it to your course.

---

## The Recipe

### Step 1 — Ingest

Place all student submissions in a single folder:

```
submissions/fall-2026-week-3/
  alice_paper.md
  bob_paper.md
  charlie_paper.md
  ...
```

Use whatever filename convention works for you. The toolkit doesn't care.

### Step 2 — Citation-check each submission

Run `/audit` on each student's paper. See `instructor/guides/using-audit-for-student-submissions.md` for the full setup.

Output: per-student MISMATCH/NOT FOUND/UNVERIFIED counts.

### Step 3 — Cluster for discussion

If your goal is to surface common themes or errors across the class, use `/pace`:

```
/pace "Review these N student papers and produce: (1) the 3 most common analytical errors, (2) the 3 most common conceptual misunderstandings, (3) the 3 strongest arguments worth highlighting in class. Papers are in submissions/fall-2026-week-3/"
```

`/pace` will spawn 2 Players (each reviewing the papers independently) + 2 Coaches + 1 Cross-Reviewer. Convergence on a theme = high confidence that theme is real. Divergence = the theme may be an artifact of one Player's reading.

### Step 4 — Extract question sets

If you run a class where students submit questions (Kay's ISE 754 format):

```
/pace "Extract all student questions from submissions/fall-2026-week-3/. Produce: (1) the N distinct questions, (2) a ranking by how many students independently asked versions of the same question, (3) a prep note for each top-3 question covering what to say in class."
```

Output: a class-ready question set you can walk into lecture with.

### Step 5 — Individual feedback

For each student who needs a private note, `/pace` on their single paper:

```
cd submissions/fall-2026-week-3/alice
/pace "Review alice_paper.md for: (1) fact-checking via /audit, (2) argumentative clarity, (3) one specific improvement suggestion. Produce a 100-word feedback note I can send Alice."
```

### Step 6 — Track the loop

Use `/dailysummary` to capture your grading session:

```
/dailysummary "Graded fall-2026-week-3 batch. N submissions. Common theme: [...]. N fabricated citations flagged."
```

This creates a dated file you can reference in the next week's planning.

---

## Scaling Knobs

- **Class size < 15**: Run Steps 2-5 serially. Takes ~1-2 hours for a 10-paper batch with careful per-student feedback.
- **Class size 15-40**: Use `/pace` batching in Step 3 + Step 4. Only do Step 5 for students needing a private note. Takes ~3-4 hours.
- **Class size > 40**: Parallelize Step 2 (citation-check) across multiple terminals. Step 3 (clustering) still scales — `/pace` reads all N papers in the Task Brief once.

---

## What This Does NOT Solve

- **Grading the argument.** Every step above returns evidence or clusters. Turning evidence into a grade is still human judgment.
- **Originality detection.** `/audit` catches fabricated citations. It does not detect LLM-written prose, paraphrased-from-LLM structure, or uncited borrowing.
- **Plagiarism between students.** You need a dedicated similarity tool (e.g., Turnitin) for this. The toolkit doesn't try to compete.

---

## When To Graduate This Recipe Into a Command

If you run this recipe for a full semester and notice:

- The same `/pace` prompt, verbatim, three weeks in a row → it's a pattern worth canonicalizing
- A specific batching strategy works for you that the recipe doesn't capture → it's an instructor-specific hook, not a command
- A new verification gap that none of `/pace`, `/audit`, or `/dailysummary` covers → that's a v2.0 `/feedback` command candidate

Until one of those three happens, this stays a reference, not a command.

Report usage back to the toolkit maintainer. Classroom evidence is what moves this from recipe to canonical workflow.

---

## Related Docs

- `instructor/guides/using-audit-for-student-submissions.md` — full `/audit` setup for submission folders
- `instructor/guides/using-pace-for-grading.md` — the canonical PACE-for-grading guide
- `instructor/guides/using-coa-for-discussion.md` — using `/coa` to prep in-class discussions
- `ai-research-toolkit/DESIGN.md` § "Rejected from v1.0" — why `/grading-rubric` and `/feedback` were not built

---

## Verification

This reference is itself PLN-verifiable: re-run the recipe in Steps 1-6 on the same submission batch, and you get the same clusters and the same flag counts. The recipe is not an opaque black box; it is transparent chain of `/audit` + `/pace` + `/dailysummary` invocations against deterministic inputs.
