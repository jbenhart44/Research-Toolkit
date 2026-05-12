# Positioning

> Every empirical value cites a file on disk. Every claim survives `grep`. Dissertation-grade, not vibe-grade.

This document states what this toolkit is for, who it serves, and what it is deliberately not. It is meant to be read before deciding to install.

---

## What this toolkit is for

Producing **structured, verifiable research artifacts** — papers, proposals, posters, slide decks, code, analyses, and the verification trail behind them — with a Claude Code workflow that treats every cited number, every quoted source, and every methodological claim as something that has to survive an audit.

The toolkit was built for complex, multi-component projects where AI assistance is real but the artifact has to be defensible afterwards — to a committee, a reviewer, a co-author, a collaborator, a teammate, or a future version of yourself. A wrong number in a deliverable is not a runtime bug to be patched in a later release; it is a permanent record that the writer mis-stated a fact. The toolkit's commands exist to make that class of error mechanically hard to commit, regardless of which discipline you work in.

---

## Who this is for

Anyone whose AI-augmented work needs to leave an audit trail. The toolkit was developed inside a PhD research environment where the cost of a fabricated citation or a misquoted number is unusually visible, but the discipline it enforces (verification, structured planning, multi-perspective review, persistent context across sessions) applies wherever AI assistance is real and the artifact has to be defensible.

Concrete user shapes the toolkit serves well:

- **PhD students and early-career researchers** producing dissertation work, journal submissions, conference papers, and grant proposals where citation accuracy and methodological reproducibility are load-bearing.
- **Faculty advisors and committee members** who want students' AI-augmented drafting to leave behind an inspectable trail (plan → construction artifact → verification report → audit log) rather than an opaque "the model wrote it" handoff.
- **Instructors and TAs** teaching AI-augmented research, writing, or programming methods who want students to learn the *separation* of planning, construction, and verification as distinct steps with their own deliverables, rather than as a single conflated prompt-and-pray loop.
- **Collaborative research labs and teams** where multiple people share a codebase, dataset, or document and need a common discipline for what counts as "verified" before something is committed or sent.
- **Solo researchers, engineers, and analysts** working on complex multi-component projects across simulation, analysis, documentation, code review, and presentation — the recurring failure modes (unverified numbers, fabricated citations, premature filling, frame-lock, cross-workstream commit bleed) are not discipline-specific.
- **Anyone working on a project where reviewer-defensibility outweighs narrative sharpness** and where "we couldn't find the source" is a stronger reason to remove a claim than "the model was confident."

If you are writing, building, or analyzing something where a reviewer (human or future-you) could ask "where does this number come from?" and expect a verifiable answer, you are in scope.

---

## Who this is not for

- **General-purpose software engineering** — production-system development, browser automation, release engineering, design-system construction, real-time agent coordination across multiple vendors. Other tool families address those needs; this toolkit's design choices (text-first, citation-gated, audit-trailed) are wrong defaults for that work.
- **Personal-agent memory layers** — persistent knowledge graphs, autonomous overnight enrichment cycles, durable cross-session job queues. The toolkit is fundamentally synchronous, session-scoped, and stateless beyond what the user explicitly commits to git. If you want an agent that ingests your meetings, emails, and tweets and surfaces them tomorrow, this is the wrong shape of tool.
- **Hidden AI use** — workflows where the goal is to obscure that AI helped produce the artifact. Every command in this toolkit leaves a trail in git. The disclosure trail is a feature.
- **Production CI/CD or live deployment** — there is no daemon, no database, no scheduled job runner, no service component. The toolkit runs when invoked and stops when finished.
- **Black-box installation** — the commands are not meant to be installed and forgotten. They are Markdown prompt files you are expected to read, modify, and fork per-user. If you want a closed product with a vendor support line, this is not it.

---

## What makes this toolkit distinct

These are design commitments, not feature claims. Each commitment trades against something a general-purpose tool would optimize differently.

**Citation pipeline as the primary gate.** Every number, every quoted figure, every reference attributed to an external source must trace to a PDF on disk and survive a `grep` against the extracted `.txt`. `/audit` enforces this mechanically; the workflow refuses to write into deliverables when the gate is open, leaving `[GAP: ...]` markers where verification is missing rather than filling from model memory.

**Planning, construction, and verification are three steps with their own artifacts.** The toolkit treats these as separately auditable. The planning step produces a plan document, construction produces the artifact-and-evidence pair, verification produces a review report. This is slower than a single prompt and produces more files. The files are the point.

**Multi-perspective adversarial review is a first-class step.** When a decision admits more than one defensible framing, a structured panel of independent perspectives is the right shape of review — not a single agent asked to "consider counterarguments." `/coa` and `/pace` exist because consensus from one context is not evidence of correctness.

**Text-first architecture, with no binary formats in the authoring path.** Commands are Markdown. Configuration is YAML frontmatter. Helpers are bash. Outputs that need binary form (PDF, DOCX) are produced at the end of the pipeline from text sources, not edited as binaries. This is what makes a third reviewer — human or machine — able to read and reproduce the workflow.

**The toolkit is forkable per user.** Every command's prompt lives in a file the user owns. Modifying a command's behavior is opening the file and editing the Markdown. There is no central server, no plugin marketplace, no per-user license, no telemetry. The trade is: you are responsible for your own version.

**No live network on the default execution path.** The toolkit reads files on disk. Optional cross-model verification (an opt-in path) is the only commanding surface that contacts an external API, and it requires explicit invocation. Default workflows complete without sending project content off the local machine.

**Honorific and authorship discipline.** Doctorates are written as "Dr. Surname" in any reader-facing artifact. AI assistance is never recorded as a commit co-author. These are positioning commitments, not stylistic preferences — they show up in commit hooks and command prompts so the discipline is mechanical rather than dependent on the user remembering.

---

## What this toolkit is not optimizing for

These are intentional non-goals, listed so the omission is not mistaken for an oversight.

- **Throughput.** This toolkit is slower than a single-prompt workflow. The slowness is structural — verification, audit, and adversarial review take time. If you need to produce many artifacts quickly without per-artifact review, this is the wrong shape of tool.
- **Style or voice imitation.** The toolkit has no style-calibration component. Voice is the writer's responsibility. The toolkit's job is to make sure the facts are right, not to make the prose sound like the writer.
- **Browser automation, real-time UI testing, or visual-design feedback.** Outside scope; addressed by other tool families.
- **Persistent cross-session memory beyond git.** State that is not committed does not persist. Session memory is the user's responsibility via memory files; the toolkit does not auto-populate.

---

## Version posture

The toolkit is in early release (v0.1+). Breaking changes between minor versions are expected. The design tenets above are stable; specific command implementations are not. Issues and pull requests are welcome; responses are best-effort, not contractually guaranteed.

The maintained surface is the Claude Code environment. Other coding-agent surfaces are out of scope.
