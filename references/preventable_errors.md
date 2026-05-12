# Preventable Errors — what the toolkit is built to catch

This document lists the categories of error this toolkit's rules and commands are designed to prevent in academic-research deliverables, with the specific command or rule that addresses each. It is meant to be read by users deciding whether the toolkit's friction is buying them something they care about — and by future maintainers deciding whether a proposed simplification would weaken a load-bearing guardrail.

Each entry is an error *class*, grounded in patterns observed during the toolkit's development. The toolkit does not claim to eliminate any of these — only to make them mechanically harder to commit unnoticed.

---

## E1 — Misquoted figures attributed to real sources

**Pattern:** A number is written into a paper, slide, or poster with a citation to a real source. The cited source exists; the number is wrong. The error is harder to catch than a fabricated citation because the reader who checks "does this paper exist?" gets a yes.

**What prevents it:** `/audit` greps every cited figure against the extracted `.txt` of the source PDF and reports MISMATCH when the value the document claims does not appear in the source. The hard rule "every cited number requires grep-verified PDF backing" makes the check mandatory before a deliverable is finalized.

**Why it matters more than fabrication:** a wrong number attributed to a real paper passes the cheapest plausibility checks. Catching it requires opening the source, finding the value, and confirming the context matches the document's claim. The toolkit automates that loop.

**Extension (v1.7) — methodology-level misquotation.** A number can survive the grep gate (the value appears in the source PDF at the cited page) yet still be misquoted at the methodology level: it may be from a robustness or supplementary section presented as a headline finding, or from a paper whose methodology has since been retracted, corrected, or superseded. `/audit --deep` (claim-chain mode) extends the single-step grep gate to a five-step chain — PDF presence, grep hit, methodology section locatable, retraction/correction notice absent, not from a robustness-only context — with a mandatory terminal verdict (`verified` / `partial` / `unverifiable` / `misattributed` / `retracted`). The deep mode cannot terminate in ambiguity; an entry without a verdict is a defect.

---

## E2 — Fabricated citations

**Pattern:** A reference is written into a draft that does not correspond to a real publication. The author exists; the paper does not. Often produced when a model is asked to support a claim and confabulates a plausible-looking citation.

**What prevents it:** the PDF-on-disk gate. No citation lands in a deliverable until the corresponding PDF is found in the project's paper directories. `/audit` reports NOT ON DISK when a citation has no matching PDF and refuses to mark the entry as verified.

---

## E3 — Premature filling of unknown values

**Pattern:** A placeholder value is written into a draft before the computation that produces it has finished. The placeholder looks like a real result, gets carried forward, and is never updated when the actual value arrives. By the time the discrepancy surfaces, the wrong value has propagated to multiple downstream artifacts.

**What prevents it:** the `[GAP: ...]` and `% TODO:` placeholder rules. The toolkit treats "I don't have this value yet" as a first-class state with its own marker, not as something to be filled with a guess. Every gap is greppable, located exactly where the missing content belongs, and explicit about what file should supply the value.

---

## E4 — Silent methodology changes

**Pattern:** A pipeline that produces deliverable content has its model ID, prompt, or sampling parameters changed in a single commit. The pre-change outputs are carried forward as if "the same experiment with an upgrade," but they are a different methodology and the methods section no longer matches the artifacts.

**What prevents it:** the API-methodology hard rule. Any change to a deliverable-feeding pipeline's model ID, sampling config, or prompt requires either re-running the pipeline and replacing the outputs, or explicitly date-stamping and labeling the outputs as "[old configuration] run, superseded" in the methods section. `/improve` flags such changes when it detects mismatched configuration history.

---

## E5 — Plausible-sounding filler in deliverables

**Pattern:** When a value, citation, or result is unknown, the writer (or the model) fills the space with text that *sounds* like a verified claim but is actually paraphrased half-memory or fabricated structure. Months later the filler is indistinguishable from verified content.

**What prevents it:** the deliverable-content hard rule. In any reader-facing artifact — paper, outline, slide, poster, grant document, methodology writeup — unverified content is left blank with an explicit `[GAP: <what is missing, what needs to happen to fill it, what file should supply the value>]` marker. Plausible filler is treated as a worse failure than a visible gap because it cannot be undone once the project moves on.

---

## E6 — Frame-lock under user pushback

**Pattern:** In a multi-step adversarial review, an attacking agent (skeptic, adversary, devil's-advocate role) concedes too quickly when the user expresses disagreement, treating user persistence as evidence the attack was wrong. The review loses its diagnostic value because the dissenting position is structurally unable to hold.

**What prevents it:** `/coa`'s structural protections for adversarial seats — independent contexts per member, file-manifest verification that each seat produced distinct content, and concession-threshold discipline in the seat definitions. The orchestrator cannot role-play a council; each member is a real Agent tool call with no visibility into the others' reasoning.

---

## E7 — Single-context simulation of multi-agent review

**Pattern:** A command nominally invoking multiple agents (council members, paired players, paired coaches) is executed by a single context writing all the outputs sequentially. The output looks like multi-agent review but provides no independent reasoning — the convergence data is meaningless because there was never any independence.

**What prevents it:** SHA-256 content-hash verification in `/coa` and `/pace`. Every member file or player file must have a unique hash. Identical hashes are treated as a hard failure indicating single-context fallback, and the run is marked unverifiable. The orchestrator is explicitly forbidden from writing inline role-played outputs.

---

## E8 — Slide-face leakage of author-only markers

**Pattern:** A refusal marker or gap token meant for the author (`[GAP: ...]`, `[MATERIAL GAP: ...]`) appears on a slide projected to an audience, on a printed poster, or in submitted body prose. The marker is louder than the underlying issue — it advertises that the author used AI and did not clean up before submission.

**What prevents it:** the sentinel-comment guard in `/audit` (markers go in format-specific comment syntax: `%` for LaTeX, `<!--  -->` for HTML/Markdown/Quarto) and the speaker-note-only guard in `/quarto` (markers go in the `::: {.notes}` block, never on a slide face). Both make the marker mechanically invisible to the rendered audience while still discoverable by the author and by `grep`.

---

## E9 — Cross-workstream commit bleed

**Pattern:** A project hosting multiple workstreams (papers, proposals, side projects, toolkit edits) accumulates uncommitted changes across several of them at once. A blanket `git add -A` from one workstream's terminal commits the others' work-in-progress, mixing unrelated changes into one commit and breaking the per-workstream history that lets future readers trace which decision belongs to which project.

**What prevents it:** the workstream-scope pre-check in `/commit` (re-injects the terminal-scope rule when the working tree spans two or more top-level workstream directories) and the hard rule against `git add -A` or `git add .`. Files are staged by explicit path. Cross-workstream commits require explicit acknowledgment.

---

## E10 — Honorific drift in reader-facing artifacts

**Pattern:** Doctorate-holders are referred to by bare surname in slides, posters, prose, commit messages, or other reader-facing artifacts. The bare-surname form reads as casual peer-to-peer reference and is the wrong register for any document a third party may read.

**What prevents it:** the honorific hard rule (always "Dr. Surname" for doctorate-holders in any prose-level reference) and the `/improve` and `/audit` checks that flag bare-surname usage in scanned drafts. Filenames and code identifiers are exempt; reader-facing artifact content is not.

---

## E11 — Co-author attribution to AI assistance

**Pattern:** A commit message, paper acknowledgment, or authorship line records AI assistance as a co-author. Even when AI was used in production, the attribution is not appropriate at the authorship level — AI assistance belongs in a methods or disclosure section, not in an authorship credit.

**What prevents it:** the no-co-author hard rule, enforced in `/commit` (refuses `Co-Authored-By` lines for AI assistants) and called out explicitly in every command's commit-related guidance. Disclosure of AI use is a methods-section concern, handled separately from authorship.

---

## E12 — Submission-time discovery of an open gate

**Pattern:** A deliverable approaches submission with one or more open `[GAP: ...]` or `% TODO:` markers that were never closed. The author either submits with the gaps visible (E8) or discovers them under time pressure and fills them with whatever comes to mind (E5).

**What prevents it:** the audit-before-submission convention. `/audit` is run as the last step before any deliverable is printed, submitted, or presented. The audit report explicitly counts and lists every open marker so the author cannot submit unaware of what is still outstanding.

---

## How to use this list

Read this document when:

- Deciding whether to install the toolkit (does it prevent error classes you care about?).
- Proposing a simplification to a command (which of these does the proposed simpler version still prevent?).
- Auditing the toolkit's design (do the rules still address the error classes they were written for?).
- Onboarding a new contributor (here is the failure surface this codebase was designed against).

Each entry is grounded in patterns the toolkit's authors have encountered during their own research and development. The list is not exhaustive — it is the subset of error classes the toolkit's current guardrails specifically address. New entries are added when a new class of error has produced a load-bearing guardrail.
