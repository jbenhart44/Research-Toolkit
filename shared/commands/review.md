---
allowed-tools: Read, Glob, Grep, Bash(ls:*), Bash(date:*), Bash(wc:*), Bash(mkdir:*), Agent
description: Read a document through 3 expert lenses in parallel (Skeptic + Practitioner + Editor), then synthesize into takeaways, project-relevance, and implications. Use for external writing you want to absorb quickly — papers, memos, advisor docs, long emails, spec proposals.
---

# /review — Three-Lens Document Review

> **When to use**: Someone handed you a document (a paper, a memo from your advisor, a long article, a spec proposal) and you want more than "summarize this." /review reads it through three distinct expert perspectives in parallel and returns (a) 5–10 key takeaways, (b) relevance to your project, (c) 3 concrete implications for you.

A triage-and-absorb tool. `/review` does NOT execute recommended actions — it surfaces them. You decide what to do with the implications.

**Cost note**: Spawns 3 subagents in parallel (~80K–120K tokens). Lighter than /coa Quick Panel because the synthesis is integrative rather than adversarial.

## Usage

```
/review <path-to-document>                      # single document review
/review <path-to-document> <focus-question>     # review with a specific lens bias
/review                                         # prompts for the document path
```

Examples:
```
/review meeting_notes/text_formats.md
/review papers/smith2025.pdf "how does this relate to my current project?"
/review notes/feedback.md
```

## What you get back

Three independent reports (one per lens) plus a Chair synthesis:

1. **Skeptic's read** — what's fragile in the doc's claims, what's oversold, what would need to be true for this to be wrong
2. **Practitioner's read** — what's actionable, what it would cost to apply, what's blocked by your current setup
3. **Editor's read** — what the doc is actually arguing (vs. what it appears to argue), its narrative structure, what's underemphasized

Each lens returns the same three deliverables:
- **5–10 takeaways** (with a preference for 5 strong ones over 10 weak ones)
- **Relevance to your project** (specific workstreams, files, or decisions)
- **3 implications** (concrete actions or reframings, not generalities)

Chair synthesis: convergence across lenses, material divergences, and a single consolidated "top 3 implications for you" list.

---

## STEP 0 — Pre-flight

Parse `$ARGUMENTS`:
- If empty → ask: "Which document should I review? (path relative to project root, or absolute)"
- If a path is given → verify the file exists with `ls`. If not found, ask for the correct path.
- If a focus-question follows the path → pass it to each lens as additional framing
- If the path ends in `.pdf`, `.docx`, or `.html` → tell the user: "That's a non-text format. Run `/readable <path>` first, then `/review` on the resulting `.txt`." STOP.

Read the target document end-to-end. If it is >500 lines, read it in sections and summarize each before passing to subagents (keeps subagent context clean).

**Project context for subagents**: If the project has a `CLAUDE.md` or `toolkit-config.md` at its root, read the first 50 lines. Extract project name + 2-3 active workstreams. Pass this as "PROJECT CONTEXT" in each lens briefing. If neither file exists, pass "PROJECT CONTEXT: (none — treat this as a general review)".

Output a one-line scope statement before launching subagents:
> **Reviewing**: `<path>` (<N> lines, <rough topic>) through Skeptic + Practitioner + Editor lenses. Focus: <focus-question or "general">.

---

## STEP 1 — Spawn three lens agents in parallel

All three subagents run in parallel (single message, three `Agent` tool calls). Use `subagent_type: "general-purpose"` for all three.

### Skeptic briefing

```
You are the SKEPTIC on a 3-person document review panel. You have one job:
find what is fragile, oversold, or unsupported in the document below.

DOCUMENT TO REVIEW:
<full document text>

USER CONTEXT (optional focus): <focus-question or "general review">

PROJECT CONTEXT: <project name + active workstreams, from Clerk's pre-flight>

Your method:
1. Read the document end-to-end.
2. For each major claim, ask: what would need to be true for this to be wrong?
   Are there cases where it fails? Is the evidence cited, or implied?
3. Identify what's oversold (strong language, weak support) and what's
   underacknowledged (caveats that get hand-waved).
4. Call out any claims that conflict with established knowledge in the user's
   domain — if you don't know the domain, flag the claim as "check against
   domain literature" rather than asserting it's wrong.

Your deliverable (in this exact structure):

## Skeptic's Read

### 5–10 takeaways
(Each takeaway is ONE sentence stating what the doc claims AND your skeptical
frame on it. Prefer 5 strong observations over 10 weak ones.)

### Relevance to the user's project
(2–4 sentences. If the document touches the user's workstreams (see user
context, CLAUDE.md if available, or the document's own references),
name which ones and how. If it doesn't, say so plainly.)

### 3 implications
(Three concrete things the user should DO or RECONSIDER based on your
skeptical read. Not generalities — specific actions, files, or decisions.
Prefix each with "CAUTION:" or "RECONSIDER:" as appropriate.)

Return ONLY the report. No preamble, no meta-commentary.
```

### Practitioner briefing

```
You are the PRACTITIONER on a 3-person document review panel. You have one job:
extract what is actionable and assess the cost of applying it.

DOCUMENT TO REVIEW:
<full document text>

USER CONTEXT (optional focus): <focus-question or "general review">

PROJECT CONTEXT: <project name + active workstreams, from Clerk's pre-flight>

Your method:
1. Read the document end-to-end.
2. For each recommendation, principle, or pattern: what would applying it
   look like concretely? What's the first step, what's the blocker,
   what's the estimated effort?
3. Identify what the user already does well vs. what's a real gap.
4. Name the tools, files, or workflows that would change if these ideas
   were adopted.

Your deliverable (in this exact structure):

## Practitioner's Read

### 5–10 takeaways
(Each takeaway is ONE sentence stating an actionable idea from the doc AND
how hard it would be to apply. Prefer 5 concrete observations over 10 vague ones.)

### Relevance to the user's project
(2–4 sentences. Name specific workstreams, files, or commands that would
change. If the user's current state already matches the doc's recommendations,
say so — don't invent work.)

### 3 implications
(Three concrete next-actions the user could take. Each should include: (a)
what to do, (b) where to do it (file/dir/command), (c) rough effort estimate.
Prefix each with "DO:" or "INVESTIGATE:" as appropriate.)

Return ONLY the report. No preamble, no meta-commentary.
```

### Editor briefing

```
You are the EDITOR on a 3-person document review panel. You have one job:
assess what the document is actually arguing and how it's structured.

DOCUMENT TO REVIEW:
<full document text>

USER CONTEXT (optional focus): <focus-question or "general review">

PROJECT CONTEXT: <project name + active workstreams, from Clerk's pre-flight>

Your method:
1. Read the document end-to-end.
2. Identify the actual thesis (vs. the apparent thesis, if they differ).
3. Assess narrative structure: where does argument build? Where does it
   meander? What's the most important paragraph? What's load-bearing
   rhetoric vs. filler?
4. Identify what's underemphasized — claims the author almost hides that
   deserve more weight — and what's overemphasized — claims that get air
   time disproportionate to their importance.
5. Note audience: who is this written for, and does that match who's
   actually reading it?

Your deliverable (in this exact structure):

## Editor's Read

### 5–10 takeaways
(Each takeaway is ONE sentence about what the doc is ACTUALLY saying,
structurally or rhetorically. Prefer 5 sharp observations over 10 surface ones.)

### Relevance to the user's project
(2–4 sentences. If the document's framing or rhetorical style is relevant
to the user's own writing — dissertation, NSF, toolkit docs — name that.
If it's just content-relevant, stay with the content.)

### 3 implications
(Three concrete things the user should take from this doc's form or argument.
Each should be specific: a framing to borrow, a structural lesson for their
own writing, or a reading-path reordering of their own work. Prefix each
with "BORROW:", "RESTRUCTURE:", or "REREAD:" as appropriate.)

Return ONLY the report. No preamble, no meta-commentary.
```

---

## STEP 2 — Synthesize (Chair role)

You (the Clerk) now act as Chair. You have three reports. Do NOT spawn a 4th agent — the Chair work is synthesis, and the user needs to see all three raw reports plus your consolidation.

Output in this exact order:

```
# /review — <document-name>

**Reviewed**: <path> (<N> lines)
**Lenses**: Skeptic, Practitioner, Editor
**Focus**: <focus-question or "general">

---

<paste Skeptic's Read verbatim>

---

<paste Practitioner's Read verbatim>

---

<paste Editor's Read verbatim>

---

## Chair Synthesis

### Convergence (2–4 points where all three lenses agree)
- Point 1
- Point 2
- ...

### Material divergence (where the lenses disagree and it matters)
- The Skeptic says X; the Practitioner says Y. The gap is <what it means for the user>.
- (If no material divergence, say: "The three lenses converged cleanly — no material disagreements.")

### Top 3 implications for the user (consolidated)
1. **<Verb-led headline>** — <1–2 sentences of specifics>
2. **<Verb-led headline>** — <1–2 sentences of specifics>
3. **<Verb-led headline>** — <1–2 sentences of specifics>

### Suggested next command
(If the implications suggest a specific /toolkit command, recommend it.
Common pairings: implications require a decision → /coa; implications are
a deliverable → /pace; implications are cited-figure verification → /audit;
implications are "capture this somewhere" → memory write or Daily Summary.)
```

---

## STEP 3 — Save the review artifact

```bash
mkdir -p "$(dirname "<document-path>")/reviews" 2>/dev/null || mkdir -p "./reviews"
DATE=$(date +%Y-%m-%d)
REVIEW_PATH="./reviews/review_${DATE}_$(basename <document-path> | sed 's/\.[^.]*$//').md"
```

Write the full synthesis (STEP 2 output) to `$REVIEW_PATH`. Tell the user where it landed.

---

## Notes

**Why three lenses, not four or five?**
Document review is not a decision — it's an absorption task. More lenses add redundancy without proportional coverage gain. The three chosen (Skeptic, Practitioner, Editor) map to the three questions a reader actually asks: "Is this true?", "Can I use this?", "What is this really saying?"

**Why these three specifically?**
- **Skeptic + Practitioner are mandatory** in the /coa ROSTER. /review inherits that rule.
- **Editor** replaces Historian as the third seat for documents specifically — the Editor persona is defined in the ROSTER as the Historian replacement when the question involves "proposal, paper, presentation, narrative, writing, slides, poster."
- For documents where the Editor lens is a mismatch (e.g., a raw dataset, a code file), consider /coa instead — /review is built for prose.

**Not for**:
- Code review → use /pace (single-deliverable verification)
- Long multi-document synthesis → use /coa Full Council
- Citation accuracy checks on papers → use /audit
- Extracting text from a PDF → use /readable first, then /review on the .txt

**Related commands**: /coa (multi-perspective decisions), /pace (single-deliverable verification), /audit (citation accuracy), /improve (self-reflective meta-review of the user's own workflow).
