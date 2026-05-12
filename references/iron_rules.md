# Iron Rules — consolidated index

The toolkit's hard rules are deliberately distributed across command files (where they are enforced at invocation time) rather than centralized in a single document (where they would be easy to miss). This index exists so a user, contributor, or reviewer can scan every iron rule in one place and find the file that enforces it.

Each entry states the rule, the file it lives in, and a one-line summary of what failure mode it prevents. For the full motivation and incident pattern behind each rule, see `preventable_errors.md`.

---

## Citation and verification

**The PDF-on-disk gate.** No citation enters a deliverable until a matching PDF is found in the project's paper directories. Citations from a `.bib` file alone, from model memory, or from research-agent output are unverified leads, not citations.
- Lives in: `shared/commands/audit.md`
- Prevents: E2 (fabricated citations)

**Grep-verify every cited figure.** Every numerical value attributed to an external source must survive a grep against the extracted `.txt` of the cited paper, with surrounding context confirming the figure means what the document claims.
- Lives in: `shared/commands/audit.md`
- Prevents: E1 (misquoted figures)

**Empirical values in code comments cite their source.** Every R², coefficient, correction factor, or other computed value reported in a comment includes the source file path and line/row that produced it. Placeholders are mandatory while a computation is in flight; values are written only after computation finishes.
- Lives in: project `CLAUDE.md` hard-rule section
- Prevents: E3 (premature filling)

---

## Deliverable integrity

**Never write placeholder content, guessed numbers, or speculative claims in deliverables.** In any reader-facing artifact, unverified content is left blank with an explicit `[GAP: <what is missing, what needs to happen to fill it, what file should supply the value>]` marker.
- Lives in: project `CLAUDE.md` hard-rule section; reinforced in `shared/commands/audit.md` and `shared/commands/quarto.md`
- Prevents: E5 (plausible filler)

**Material gap refusal token — sentinel-comment guard.** When `/audit` reports NOT FOUND or MISMATCH, any inline edit it recommends renders the marker in format-specific comment syntax (`%` for LaTeX, `<!--  -->` for HTML/Markdown/Quarto) — never as visible body text.
- Lives in: `shared/commands/audit.md`
- Prevents: E8 (slide-face leakage)

**Material gap refusal token — speaker-note-only guard.** On a slide deck, any `[MATERIAL GAP: ...]` marker appears only inside the `::: {.notes}` block, never on a slide face. If the slide has no notes block, `/quarto` creates one rather than silently dropping the marker.
- Lives in: `shared/commands/quarto.md`
- Prevents: E8 (slide-face leakage)

**Audit before submission.** `/audit` is run as the last step before any deliverable is printed, submitted, or presented. The audit report lists every open marker so the author submits with full awareness of what remains outstanding.
- Lives in: `shared/commands/audit.md`
- Prevents: E12 (submission-time gap discovery)

---

## Multi-agent discipline

**No simulation of multi-agent review.** Commands invoking multiple agents (`/coa`, `/pace`) must make real Agent tool calls — one per seated member or paired player — in the same message so they run concurrently. Inline role-play ("the Skeptic would say…", "Player A would say…") is forbidden.
- Lives in: `shared/commands/coa.md`, `shared/commands/pace.md`
- Prevents: E7 (single-context simulation)

**Distinct content hashes required.** Every council-member file and every paired-player file must have a unique SHA-256 hash. Identical hashes are a hard failure indicating single-context fallback, and the run is marked unverifiable.
- Lives in: `shared/commands/coa.md`, `shared/commands/pace.md`
- Prevents: E7 (single-context simulation)

**Members must not see each other's work.** Independence is what makes a multi-agent review valuable. Cross-visibility between members within a single run is forbidden.
- Lives in: `shared/commands/coa.md`, `shared/commands/pace.md`
- Prevents: E6 (frame-lock under pushback), E7 (single-context simulation)

**Pre-verification of named external features.** When a `/coa` question references a specific external tool, vendor feature, or release, the Clerk fetches the canonical authoritative source before convening so findings are passed to the council as fact rather than as something to verify.
- Lives in: `shared/commands/coa.md`
- Prevents: factually-grounded review when the underlying claim is unverified

---

## Authorship and attribution

**No AI co-author attribution on commits.** Commit messages do not include `Co-Authored-By` lines for AI assistants. AI assistance belongs in a methods or disclosure section, not in an authorship credit.
- Lives in: project `CLAUDE.md` hard-rule section; `shared/commands/commit.md` enforces by omission
- Prevents: E11 (co-author attribution to AI)

**Honorific discipline.** Doctorate-holders are referred to as "Dr. Surname" in any reader-facing artifact — slides, posters, prose, commit messages, daily summaries, memory bodies, conversational responses. Bare-surname usage is unacceptable in that context. Filenames and identifiers are exempt.
- Lives in: project `CLAUDE.md` hard-rule section
- Prevents: E10 (honorific drift)

---

## Workstream and commit hygiene

**Terminal-scope rule.** When multiple terminals are open on the same repository, each terminal stages and commits only files belonging to its own declared workstream. `git add -A`, `git add .`, and broad glob patterns are forbidden. Files are staged by explicit path.
- Lives in: project `CLAUDE.md` hard-rule section; mechanically re-injected by `shared/commands/commit.md` Step 0a when ≥2 workstreams are touched
- Prevents: E9 (cross-workstream commit bleed)

**Pre-commit scope verification.** Before committing, `git diff --cached --name-only` is run and every staged file is verified to be in scope. Out-of-scope files are unstaged and left for the terminal that owns them.
- Lives in: `shared/commands/commit.md`
- Prevents: E9 (cross-workstream commit bleed)

---

## Methodology and reproducibility

**API-methodology change requires re-validation.** If a deliverable-feeding script has its model ID, sampling parameters, or prompt changed, the outputs are a new methodology. Either re-run and replace, or explicitly date-stamp and label as "[old configuration] run, superseded" in the methods section.
- Lives in: project `CLAUDE.md` hard-rule section; `shared/commands/improve.md` flags such drift
- Prevents: E4 (silent methodology changes)

**Session summaries use the higher-capability model.** Daily summaries, project summaries, and PCV summaries are written by a Sonnet-tier subagent, not a smaller model. Smaller models have produced numerical errors on project-specific figures.
- Lives in: project `CLAUDE.md` hard-rule section; `shared/commands/dailysummary.md` and `shared/commands/weeklysummary.md` configure the subagent accordingly
- Prevents: numerical drift in session-summary artifacts

---

## Read-only constraints

**Audit logs are append-only.** `/runlog`'s `run_log.csv` and `command_performance_log.md` are produced by other commands and never written to by `/runlog` itself.
- Lives in: `shared/commands/runlog.md`
- Prevents: corruption of the longitudinal observation surface

**Memory and summary boundaries.** `/weeklysummary` never writes to `MEMORY.md` automatically; it produces suggestions for manual review. The MEMORY surface is the user's responsibility, with the toolkit observing rather than mutating it.
- Lives in: `shared/commands/weeklysummary.md`
- Prevents: silent corruption of the user's memory layer

---

## How to use this index

Read this document when:

- Auditing whether a proposed change to a command would weaken or strengthen a load-bearing rule.
- Onboarding to the toolkit and wanting to see the constraint surface in one place.
- Debugging a workflow failure and trying to locate the rule that was violated.
- Proposing a new command — checking which existing rules the new command must respect.

Rules are added to this index when a new iron rule is introduced into a command file. The command file is the source of truth; this index is the navigation surface.
