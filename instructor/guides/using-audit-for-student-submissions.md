# Using `/audit` for Student Submissions

**Audience**: Instructors teaching research-writing or methodology courses who want to verify citations and numerical claims in student submissions.

**Prerequisite**: This guide assumes you have already installed the toolkit (`bash install.sh --instructor`). You do NOT need `/pace`, `/coa`, or any other verification command for this workflow — `/audit` alone is enough.

---

## What This Guide Does

`/audit` grep-verifies every cited metric and source in a document against the actual PDFs or text files on disk. It was built to prevent two academic failure modes:

1. **Fabricated citations** — a paper that doesn't exist, or has the wrong author/year/venue
2. **Misquoted numbers** — a real paper whose quoted figure doesn't match the text

Both of these are common failure modes in AI-assisted student work, especially when the student has used an LLM to summarize papers they haven't actually read.

This guide shows you how to use `/audit` to catch both kinds of error in student submissions, without needing to build a new grading command.

---

## The Minimal Setup

Ask students to submit **two** items:

1. The document (PDF, `.md`, or `.docx`)
2. A folder of source PDFs for every paper they cite

Place both in a submission folder structure like:

```
submissions/
  student_name/
    paper.md              # the submission
    sources/
      author1_year.pdf
      author2_year.pdf
      ...
```

That's the whole setup. No per-student config. No grading rubric file.

---

## The `/audit` Invocation

From the student's submission folder:

```
/audit paper.md --sources sources/
```

`/audit` will:

1. Find every `(Author Year)` or `[@author_year]` citation in the document
2. Match each to a file in `sources/`
3. For each numerical value attributed to a source, `grep` the value in the source's `.txt` extraction (auto-invoked via `/pdftotxt` if missing)
4. Flag three classes of error:
   - **MISMATCH** — number in document ≠ number in source
   - **NOT FOUND** — citation has no matching PDF in `sources/`
   - **UNVERIFIED** — citation exists but no numerical claim to check (informational, not an error)

---

## What You Get Back

A structured report with:

- Every citation the student made, in the order they made them
- Pass/fail verdict per citation
- For MISMATCH: the document's value and the source's actual value, side by side
- For NOT FOUND: an explicit flag that the source PDF is missing — no silent pass
- For UNVERIFIED: the citation with a note that it's textual-support-only

**How to use this for grading:**

- MISMATCH count → rubric deduction (or conversation, if early in the semester)
- NOT FOUND count → treat as "citation needed" — the same severity as fabricating
- UNVERIFIED is not an error — some citations legitimately support prose without quoting a number

---

## Running at Scale — 20+ Students

Two options:

### Option A: Batch via your own loop

```bash
for student in submissions/*/; do
  echo "=== $student ==="
  cd "$student" && /audit paper.md --sources sources/ && cd -
done
```

This gives you a per-student audit in your terminal scrollback. Good for 5-15 submissions.

### Option B: `/pace` with an audit persona

For larger classes where you want structured output:

- Ask `/pace` to audit all student papers in parallel
- Each Player reviews a different subset
- The Cross-Reviewer flags inconsistencies (e.g., "Student A cited value X, Student B cited value Y for the same paper — one of them is wrong")

See `using-pace-for-grading.md` for the full PACE-for-grading workflow.

---

## What `/audit` Does NOT Do

- **Grade the argument.** `/audit` checks whether cited facts are real. Whether the student's argument is *good* is a human judgment.
- **Check argument-fact connection.** A student might cite a real number correctly but use it to support a conclusion it doesn't actually imply. That's a rhetorical-analysis task, not an audit.
- **Handle non-numerical claims.** If a student cites "most economists believe X" and the source just says "many economists believe X" — that's interpretive drift, which `/audit` flags as UNVERIFIED rather than MISMATCH.
- **Replace manual inspection.** `/audit` is a first-pass filter. A 10-minute read by the instructor after `/audit` reviews is still necessary.

---

## Academic Integrity Note

`/audit` catches fabrication but does NOT distinguish:

- A student fabricating a citation intentionally
- A student using an AI that fabricated a citation
- A student misreading a legitimate source
- The source PDF being the wrong version of a paper

**Treat `/audit` results as evidence for a conversation, not as a verdict.** The first time a MISMATCH shows up in a semester, the right move is a private conversation ("Help me understand where this number came from"), not an integrity referral.

As AI-assisted writing becomes normal, fabricated citations will become more common — and they will usually originate upstream of the student, in the LLM they consulted. Treat detection as part of teaching the verification habit, not as a gotcha.

---

## Pedagogical Extension — Teach the Verification Habit

Consider giving students a copy of `/audit` to run on their own drafts before submission. The toolkit is free and installable in 2 minutes. Make "run `/audit` on your draft and include the output as an appendix" a submission requirement.

This has two effects:

1. Students catch their own fabrications before you do (better learning outcome)
2. The burden shifts: turning in a paper with MISMATCH errors in the appendix looks worse than turning it in without the appendix at all

This is the Panjwani (VoxDev 2025) "skills as patterns to adapt" principle applied pedagogically — treating `/audit` as a habit to build, not a black box for the instructor.

---

## Known Limitations

- **PDF extraction quality varies.** Image-based PDFs require `/pdftotxt` OCR, which has a ~95% success rate but can miss text on complex layouts. If `/audit` flags a NOT FOUND on a citation you *know* the student has, spot-check the `.txt` extraction.
- **Citation format heterogeneity.** `/audit` currently matches `(Author Year)`, `[@author_year]`, and numbered `[1]` styles well. Footnote-only citation systems (e.g., some Chicago styles) may require a second pass.
- **Numerical formatting.** `/audit` normalizes percentages ("35%" ↔ "0.35") and comma-number pairs ("1,000" ↔ "1000") but may miss unusual formats. Flag false positives back to the toolkit maintainer — these get added to the normalization rules.

---

## Troubleshooting

**"/audit says NOT FOUND on a PDF I can see in sources/"**
Check the filename. `/audit` matches on author+year; a file named `paper_final_v2.pdf` without an author or year in the name won't match. Ask students to rename to `author_year.pdf`.

**"/audit is slow on a 20-citation document"**
First invocation does `/pdftotxt` on every PDF. Subsequent runs use the cached `.txt`. Expect ~3 seconds per citation first pass, ~0.5 seconds per citation on re-run.

**"Numbers I know match are being flagged MISMATCH"**
Check for units. "35%" in the document vs. "0.35" in the source is normalized; "35 percent" vs. "35%" is also normalized; but "$35M" vs. "35 million" may not be. Flag these upstream.

---

## Commitment

If you adopt `/audit` for student submissions, please let the toolkit maintainer know. Your edge cases will drive the next round of improvements — this is exactly the kind of field evidence v1.2 needs.
