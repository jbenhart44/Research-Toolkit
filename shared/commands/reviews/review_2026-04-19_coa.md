# /review — coa.md (per-command docs pilot #1)

**Reviewed**: `ai-research-toolkit/shared/commands/coa.md` (~600 lines)
**Lenses**: Skeptic, Practitioner, Editor
**Focus**: Evaluate whether /review output on a command spec produces a reader-facing website description sharper than hand-written docs
**Date**: 2026-04-19

---

## Skeptic's Read

### Takeaways
1. The spec frames CoA as producing "diverse expert perspectives," but admits in the Same-Model Caveat that all members share one LLM — what you actually get is six rewordings of the same model's priors, dressed in persona costumes, not genuinely independent experts.
2. The token-cost disclosure ("~60K-100K" for Quick Panel, "~150K-250K" for Full Council) is presented as a casual "Cost note" but dwarfs most single-agent workflows — a prospective user should read this as "a single question costs roughly one full context window of tokens," not as a minor footnote.
3. The PACE-vs-CoA table ("single correct output" vs. "multiple valid framings") is cleaner in the spec than it will be in practice; many real decisions are mixed (a code architecture question has both a design axis AND a correctness axis) and the user will be forced to pick a lane or run both.
4. The file-manifest/self-audit machinery (separate member files, SHA-256 distinctness, `audit_run_evidence.sh`, `fallback` verdicts) consumes a large fraction of the spec — the prospective user will correctly infer that this command has a known failure mode (silent single-context collapse) that the toolkit has had to bolt fences around.
5. The Cross-Model Routing and Cross-Model Cross-Check steps are written as first-class features but both require an MCP server most users will not have configured; without it, the "genuine cross-model diversity" headline reduces to a same-family Sonnet fallback or nothing at all.
6. Multiple human-approval STOP gates (roster approval, decision gate, rebuttal) and a mandatory self-audit mean CoA is not a fire-and-forget command — it is a multi-turn protocol that will interrupt the user at least twice per run.
7. "400-600 tokens per member, dense not verbose" plus a 7-section Chair synthesis plus a Position Map table is a lot of structure for what is ultimately advisory output — the command produces reading, not deliverables, and the spec concedes this in BEHAVIORAL CONSTRAINTS ("Advisory only").

### Relevance to the user's project
The biggest gap for a prospective user: the spec sells "multi-perspective expert analysis" but delivers *one model role-playing six personas*, with elaborate structural guardrails (separate files, hash checks, audit script) that exist specifically because this command has been caught collapsing into single-context role-play before. If you want genuinely independent voices, you need the optional cross-model MCP, which is not part of the default install. Also: CoA writes no code and edits no files — it produces a synthesis report you must then act on. If you expected a deliverable, you want PACE.

### Implications
- **CAUTION:** Budget 60K-250K tokens per session and two human-input stops — do not run /coa on questions a single agent could answer in one turn.
- **RECONSIDER:** If your question has a verifiable correct answer (code, math, a factual claim), use /pace instead; CoA's value is concentrated in "it depends" questions.
- **CAUTION:** Without the `crossmodel` MCP configured, the "same-model caveat" applies to every output — treat convergence as "my model was consistent across framings," not as independent confirmation.

---

## Practitioner's Read

### Takeaways
1. **Human gate before spawning**: After the Clerk proposes a roster, the user MUST type "convene" (or adjust); nothing fires without approval — budget ~30 seconds of back-and-forth before any council member runs.
2. **Token cost scales with tier**: Quick Panel (3 agents, ~60K-100K tokens) for reversible/low-stakes; Full Council (6 agents, ~150K-250K tokens) for irreversible/high-stakes — use `--quick` or `--full` to skip VOI negotiation.
3. **Poor fit is explicit**: If the question has a single correct answer, needs a verified deliverable, or is code-shaped (file paths, function signatures in $ARGUMENTS), the command auto-redirects to /pace or a single agent — don't fight it.
4. **The File Manifest is the integrity check**: Each member writes a separate `member_{seat}.md` file (>500 bytes, unique SHA-256) plus `chair_synthesis.md` in `CC_Workflow/coa/council_sessions/coa_{date}_{slug}/`; a single `all_members.md` is rejected as single-context fallback.
5. **Output is advisory only** — no file modifications during Steps 0-4, recommendation is 1-3 sentences, and Step 5 consolidation is opt-in ("most sessions end at done").

### Relevance to the user's project
/coa fits the "should we..." slot: phase architecture choices, dissertation framing, Paper 1 vs Paper 3 sequencing, NSF narrative decisions — anywhere multiple valid framings exist and the user wants breadth-of-perspective before committing. It is the only toolkit command optimized for divergence-mapping rather than convergence-to-a-deliverable; /pace verifies a single output, /review absorbs one document through 3 lenses, /pcv plans implementation. Prospective user's memory-worthy rule: **"/coa when there's no right answer, /pace when there is."**

### Implications
- **DO: Start with `--quick` on your first invocation.** Invoke as `/coa --quick <your question>` to force the 3-agent Quick Panel and cap token burn at ~60-100K; upgrade to Full Council only after you've seen the output shape once. Effort: 5 minutes including reading the Position Map.
- **INVESTIGATE: Whether `scripts/audit_run_evidence.sh` and a `coa/council_sessions/` directory exist in your project** before first use. The self-audit in Step 5b will fail loudly if they don't; either run the command once to let it create the directory, or `mkdir -p CC_Workflow/coa/council_sessions/` manually. Effort: 1 minute.
- **DO: Decide up front whether you want cross-model validation.** If you have a `crossmodel` MCP server configured (Gemini/OpenAI), the same-model caveat drops; if not, the command falls back to a local Sonnet cross-check and labels the caveat PARTIAL. For a first-time user with no MCP setup, expect MAXIMUM same-model caveat and plan to weight "all members agreed" signals accordingly. Effort: 0 if you accept the caveat, ~30 min to wire up MCP if you don't.

---

## Editor's Read

### Takeaways
1. The spec reads like an **operations manual for paranoid orchestrators**, not a user guide — roughly 40% of its bulk is anti-fallback enforcement (self-audits, SHA-256 hash checks, prohibited filenames) rather than explaining what a user gets.
2. The actual thesis is narrower than the header suggests: CoA is **a forcing function for structurally distinct reasoning**, not just "multi-perspective analysis" — the Differentiation Check and anonymization steps are the real mechanism.
3. The PACE-vs-CoA comparison table at line 27 is the single clearest user-facing artifact in the entire document and answers "when should I use this?" better than the rest of the spec combined.
4. Dynamic Seating (Quick Panel / Working / Full Council) is a **cost-and-stakes dial**, and the spec buries its most useful feature — `--quick` as the default technical-question mode — inside a table on line 82.
5. The tone oscillates between pitch ("The analogy: A review committee...") and compliance ("PROHIBITED", "STOP", "MANDATORY — DO NOT SKIP"), which is unusual — it reads like a command that was burned once and wrote the incident into its own spec.
6. The Chair synthesis structure (7 sections: convergence, divergence map, surprises, verification flags, recommendation, execution differences, limits) is genuinely distinctive output and barely advertised.
7. "Same-model caveat" is repeated 6+ times — the spec is honest about its own epistemic limits in a way that would actually sell the tool to a skeptical researcher.

### Relevance to the user's project
A `/review` pass on this spec would produce a usable landing-page draft but would need **heavy condensation** — probably 80% cut. The spec's signal (when-to-use table, council-size tiers, Chair's 7-section output, same-model caveat) would survive; the enforcement machinery (file manifest, SHA-256 audit, fallback recovery paths, YAML frontmatter schemas) is internal plumbing that a prospective user should never see on page 1. A lightly-edited `/review` output is plausible only if the Editor lens explicitly excludes operational sections.

### Implications
- **BORROW:** The PACE-vs-CoA comparison table structure — this is the single best "do I need this?" artifact and should be the landing page's fold. Every command spec should have an equivalent "vs. the obvious alternative" table.
- **RESTRUCTURE:** Move the Council Member Prompt Template's Conviction bet ("wager $___") and Flip Condition forward — these are the distinctive outputs a user should see in an example, not buried at line 195. The landing page should show a sample output, not describe the protocol.
- **CONDENSE:** All of STEP 5b (self-audit), STEP 6 (evidence saving), and the file manifest section belong in a separate `coa-internals.md`, not the public-facing spec. A prospective user evaluating the toolkit does not need to know about SHA-256 collision checks before they know what a Chair synthesis looks like.

**Ideal 3-paragraph landing page structure:** (1) What it is + the committee analogy + 1 concrete example question. (2) When to use it — PACE comparison table + the three council-size tiers. (3) What you actually get — a sample Position Map row and the 7-section Chair synthesis headers, closing with the same-model caveat as an honesty signal.

---

## Chair Synthesis

### Convergence (all three lenses agree)
- **The same-model caveat is the real story.** Skeptic flags it as oversold, Practitioner names MCP as the only mitigation, Editor says its honesty would *sell* the tool to a skeptical user. All three say: lead with it, don't bury it.
- **The PACE-vs-CoA distinction is the highest-value user-facing artifact in the spec.** Skeptic complains the dichotomy blurs in practice, Practitioner compresses it to one memorable sentence ("/coa when there's no right answer, /pace when there is"), Editor says the comparison table should be the website fold. All three say: this is the answer to "when should I use this?"
- **The spec is user-hostile in its current form.** Operational machinery (self-audits, SHA-256 checks, file manifests, MCP plumbing) dominates the document at the expense of what a prospective user needs to know: what they'll type, what they'll get back, and what it costs.

### Material divergence
- **Skeptic vs Practitioner on the value proposition.** Skeptic: "CoA is one model in six costumes with structural guardrails bolted on after it was caught collapsing." Practitioner: "CoA is the only toolkit command optimized for divergence-mapping; that's a real and unique niche." They're both right — Skeptic is honest about the mechanism, Practitioner is honest about the utility. The Chair synthesis should keep both: "This is one model forced to reason through distinct frames. That's less than 'six independent experts' — but it's more than any single-agent invocation can produce."
- **Editor vs Skeptic on whether the spec's extensive caveating is a bug or a feature.** Editor says the honest same-model-caveat treatment would *sell* the tool to researchers; Skeptic says the volume of structural-integrity machinery signals past failure. Both are correct — the spec is unusually honest about limits (good) AND unusually burdened by anti-fallback enforcement (bad). The landing page can keep the honesty and hide the enforcement.

### Top 3 implications for the per-command-docs pilot
1. **The /review output is usable as a website description IF we run it with an explicit "exclude operational sections" instruction.** The default Editor lens already does 80% of the condensation work; one more editorial pass keeps signal, cuts plumbing. Effort to ship /coa's website description from this output: ~30 minutes of editing.
2. **The Editor's "Ideal 3-paragraph landing page structure" is the template for all 14 remaining commands.** Three paragraphs: what it is + analogy + example / when to use (with comparison table) / what you get (with sample output + honest caveats). This is now the de-facto command-docs template.
3. **The PACE-vs-CoA comparison table pattern is the missing piece in most toolkit commands.** All three lenses independently landed on this. Practical next step: audit each of the 15 command specs for a "vs. the obvious alternative" table. Commands that lack one (likely most of them) need it added before they're ready for the per-command-docs pass.

### Suggested next command
- For shipping /coa's website description right now: just edit the Editor's 3-paragraph structure into a new file and link it from `jbenhart44.github.io/index.html`. No further command needed.
- For the broader 14-command pilot: **run /review on /pace next** as the validation pair — if /pace produces a similarly useful output and the PACE-vs-CoA comparison table shows up from both angles, the pattern is confirmed and the batch pass is worth doing.
- For the "vs. alternative" table audit: one-line grep (`grep -L "vs\\." shared/commands/*.md` or similar) tells us which commands lack one.

---

## Pilot validation notes

**Verdict**: /review against a command spec produces genuinely useful reader-facing draft material — SHARPER than hand-written docs in specific ways (the PACE-vs-CoA memorable rule didn't appear in coa.md's own prose) but needs ~30 min of editorial condensation to ship as a website page.

**What worked**:
- Three lenses produced non-overlapping, complementary reads (Skeptic caught oversold claims, Practitioner extracted decision rule, Editor identified reader-hostile sections)
- "Same-model caveat" as the central story emerged from triangulation, not from any one lens
- Convergence on "PACE-vs-CoA table is the killer artifact" — three independent paths to the same conclusion

**What needs adjustment for the batch pass**:
- Editor briefing already selects for reader-facing value; could add explicit instruction to propose the 3-paragraph landing page copy directly (not just describe it)
- Add a fourth phase: "condensation" — instruct the Clerk to produce a shippable 200-word website description as the final output, not just the synthesis

**Pilot result**: Proceed. Run /review on /pace next as the validation-pair. If it works, batch the remaining 13 commands in a dedicated session.
