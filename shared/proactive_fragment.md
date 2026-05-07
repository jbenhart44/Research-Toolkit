# AI Research Toolkit — Proactive Suggestion Fragment (v0.1.1)

**Status**: Default-OFF. This fragment is bundled with the toolkit but is NOT auto-imported into your CLAUDE.md. See "How to opt in" at the bottom of this file.

**What this is**: 15 declarative rules — one per toolkit command — that tell Claude when to *suggest* the right command at the moment the user is about to take an action that the command would improve. Each rule fires on observable conversational signals in the current turn; flip conditions are stateless. **No router, no observer, no always-active agent.** This is the declarative path; a runtime market-style variant is gated behind the falsifiable pilot test at the end of this file.

**Why this exists**: Krishnan (2026), "Why Coase Needs Hayek," empirically showed that hub-spoke smart-routing of agentic tasks costs ~4× more than solo agents AND can lose on quality (6.7 vs. 7.2/7.2 across 15 tasks). A runtime always-active suggestion agent IS hub-spoke. This fragment achieves the same suggestion goal via static, declarative rules that Claude reads from CLAUDE.md once per session — no runtime cost, no central agent.

---

## Header policy: stateful flip conditions

Stateful flip conditions: **compile to stateless artifact-checks where possible, document the limitation otherwise**. This fragment is declarative text and cannot remember whether a suggestion was declined earlier in the session. Where a command produces a deterministic on-disk artifact as a normal side-effect of execution (e.g., `pcvplans/charge.md` for `/pcv`, `coa_<date>_*/chair_synthesis.md` for `/coa`, `Daily Summary/<date>.md` for `/dailysummary`, a recent commit visible in `git log` for `/commit`), each row's anti-trigger may reference that artifact directly via current-turn observation or a stateless filesystem check. **No new flag files, decline registries, or session-suggestion logs are permitted** — those are session observers wearing a filesystem costume and re-introduce the hub-spoke topology this fragment exists to avoid.

Reading existing on-disk artifacts that other commands already produce as a normal side-effect of execution is NOT new code infrastructure. *Writing* new flag files, decline registries, or session observers IS infrastructure and is forbidden.

**Known limitation (row 9, /simplify)**: /simplify's "code authored very recently" gate has no on-disk artifact (no command writes such a marker). This row is acknowledged as best-effort rather than papered over with a synthetic flag file.

---

## The 15 rules — Observable + Gate + Anti-trigger

Each rule reads as: *"When [observable] AND [gate], suggest /command — UNLESS [anti-trigger]."* Every Observable is verifiable in the current turn. Every Anti-trigger is stateless.

### 1. /pcv

- **Observable**: User names ≥3 distinct components (files, phases, deliverables, systems) in a single request AND asks how to approach/start.
- **Gate**: Claude's response would require sequencing across ≥3 interdependent decisions without a plan — no phased outline or numbered breakdown exists in this turn or the preceding assistant turn.
- **Anti-trigger**: A scoped plan, numbered breakdown, or phased outline already visible in the current turn; OR `pcvplans/charge.md` exists or `pcvplans/research_runs/` is referenced; OR user is asking for explanation, not construction.
- **Failure mode caught**: Silent scope-creep — a build starts without structure, complexity compounds, rollback becomes costly.
- **Scope-clause footer (residual stateful mechanics)**: Suggest-once and decline-don't-repeat behavior live in `pcv/skill/SKILL.md` §7. The fragment row above only sharpens *when* SKILL.md's trigger should fire; it does not duplicate SKILL.md's behavioral lock.

### 2. /coa (sharpener)

The current CLAUDE.md /coa rule ("decisions where multiple valid perspectives exist") is Observable-only. This row adds a conjunctive Gate and explicit Anti-trigger:

```
Suggest /coa when:
  OBSERVABLE: User's current turn names ≥2 distinct options OR uses a comparator phrase
              ("should I", "which of", "tradeoffs", "better approach", "is X or Y").
  GATE: Both of the following hold —
    (i) ACTION-DIVERGENCE: A 2-persona dry-run (Practitioner optimizing for shipped-deliverable
        speed/reversibility vs. Dissertation Advisor optimizing for reviewer-defensibility/
        publishable rigor) would yield DIFFERENT recommended next actions on this exact
        question — not just the same action with different rationales.
    (ii) STAKES-WARRANT-PREMIUM: At least ONE of —
            - IRREVERSIBILITY: chosen option binds ≥2 future deliverables, costs >2h to undo,
              OR commits a public artifact (commit, ship, send to advisor);
            - STAKEHOLDER ASYMMETRY: ≥2 named/implied parties (advisor, reviewer, future self,
              end-user) would weigh dimensions differently;
            - EXPERT-DISAGREEMENT-PRECEDENT: contested dimension appears in prior CoA divergence
              record OR in CLAUDE.md hard-rule provenance.
  ANTI-TRIGGER: Any one of —
    (a) Verifiable single answer: 2-minute Bash/Read/grep/code-test could settle the question;
    (b) Stylistic / reversible / low-stakes preference: switching cost in minutes, not hours;
    (c) Execution request, not deliberation: conjunction is "and-then" not "or";
    (d) /coa output for this exact decision already cited in this turn.
```

Both Gate tests are required. Action-divergence is the necessary condition (no point convening a council that will agree); structural-stakes is the sufficient-stakes condition (no point paying Krishnan's 4× premium when reversal is cheap). The 2-persona dry-run is **stateless in-Claude introspection** — structurally identical to the existing "Verified:" self-check habit. No spawned agent, no router, no session memory.

**Failure mode caught**: Decision made with one value framework in a context where another framework's verdict would be different — later conflict is predictable.

### 3. /pace

- **Observable**: ≥1 specific numerical claim, statistical result, citation, or logical proof step in current turn OR attached artifact the user is about to use.
- **Gate**: Next action is commit/submit/present/share (finalizing intent stated or implied), OR user explicitly asks "is this right" / "does this check out".
- **Anti-trigger**: Claim is a trivially public constant (e.g., π); OR user says "I'll verify later" / "this is a draft"; OR a prior /pace run for this specific artifact has been explicitly cited in the current conversation.
- **Failure mode caught**: Numerical error or citation mismatch survives into a submitted or shared deliverable.

### 4. /audit

- **Observable**: User message references a `.qmd` / `.tex` / `.md` document representing an academic or scholarly deliverable AND includes intent signal ("submit" / "final" / "send to" / "present" / "print").
- **Gate**: Document contains inline citations or numerical values that require source-file backing under the project's citation pipeline.
- **Anti-trigger**: Document is a scratch note or exploratory analysis clearly marked as such; OR /audit already explicitly named and its output referenced in this turn.
- **Failure mode caught**: Citation fabrication or placeholder value survives into a submitted academic deliverable.

### 5. /readable

- **Observable**: User mentions need to grep/cite/systematically compare evidence across ≥1 PDF or doc file on disk.
- **Gate**: User needs machine-searchable text — not a one-off read of a single document for summary.
- **Anti-trigger**: User asking Claude to read a single file now using the Read tool; OR `.txt` extractions for these docs already confirmed present on disk in this turn.
- **Failure mode caught**: Interactive PDF reading misses evidence; downstream /audit or citation verification fails.

### 6. /quarto

- **Observable**: User states need for slides/presentation/deck referencing existing source documents.
- **Gate**: Source material is multi-document or multi-section; request implies a formal structured deck.
- **Anti-trigger**: One-slide summary or verbal outline request; OR `.qmd` for this talk already exists and user is iterating it; OR user wants a simpler output artifact.
- **Failure mode caught**: Manual slide construction reinvents /quarto's structural logic; beats missed; formatting inconsistent.

### 7. /commit

- **Observable**: `git status` or `git diff` output visible in turn showing changes, OR user names ≥2 changed files.
- **Gate**: Current turn signals completion of a unit ("that's working" / "fix is in" / "done for now") AND changes appear to span ≥2 logical concerns (code + docs, OR two distinct features, OR model + tests).
- **Anti-trigger**: Mid-task: "next I'll" / "still need to" / incomplete state stated; OR changes clearly belong to a single atomic concern; OR /commit just completed and its output visible in this turn.
- **Failure mode caught**: Multi-concern changes accumulate in a single commit; rollback and blame become ambiguous.

### 8. /improve

- **Observable**: Working code or document section just completed — test passing, file written, or user says "done" / "it's working" / "finished the".
- **Gate**: Completed artifact is reusable infrastructure, shared utility, or deliverable-adjacent (not a throwaway one-run script).
- **Anti-trigger**: User immediately signals replacing or deleting the artifact; OR artifact explicitly labeled throwaway ("just for today's run"); OR an /improve pass on this artifact already referenced in this turn.
- **Failure mode caught**: Working code or document ships with latent inefficiencies; technical or prose debt compounds across sessions.

### 9. /simplify

- **Observable**: Working code exists in current turn or prior turn AND user confirmed correct output ("it runs" / "passes" / "output looks right").
- **Gate**: User's stated concern is maintainability, length, or readability — NOT adding a feature or fixing a bug; OR imminent code review.
- **Anti-trigger**: Code currently broken or untested; OR user's goal is adding a feature or fixing correctness (complexity reduction is premature); OR code authored very recently (still in active edit loop).
- **Failure mode caught**: Code that works ships in a form that is hard to audit, review, or extend; reviewer feedback forces rewrite.
- **⚠ Known limitation**: The "active edit loop" anti-trigger has no on-disk artifact. Best-effort only. See header policy.

### 10. /startup

- **Observable**: First user message in conversation is a task, question, or "what was I working on" — session-start pattern with no prior context loaded.
- **Gate**: Message implies resumption from a prior session (≥1-day gap implied by phrasing, OR user asks about "yesterday" / "last time" / "where we left off").
- **Anti-trigger**: User already quoted a daily summary or listed open tasks in the opening message; OR user explicitly framed the session as a fresh, unrelated task.
- **Failure mode caught**: User starts in wrong context — stale branch assumptions, missed blockers, duplicates work completed previously.

### 11. /dailysummary

- **Observable**: Session contains ≥2 commits, completed tasks, or significant decisions visible in conversation history.
- **Gate**: User signals session end: "wrapping up" / "that's it for today" / "need to go" / "good stopping point" / "pick this up tomorrow".
- **Anti-trigger**: A daily summary file for today already exists on disk (e.g., `Daily Summary/<today>.md`) AND its file path or content is referenced in this turn; OR user signals immediate continuation ("I'll keep going").
- **Failure mode caught**: Completed work, decisions, and blockers fall out of memory; next session starts without accurate state.

### 12. /weeklysummary

- **Observable**: User references end-of-week, Monday startup, or multi-day progress ("this week" / "last week" / "how has the week gone") AND `/dailysummary` entries from ≥3 distinct dates are reachable in the project.
- **Gate**: Conversation context implies cross-session synthesis need, not single-day summary.
- **Anti-trigger**: Weekly summary for the current ISO week already mentioned or linked in this turn; OR user only needs today's summary.
- **Failure mode caught**: Cross-session patterns invisible; advisor/committee handoffs lack longitudinal view.

### 13. /runlog

- **Observable**: User asks about patterns, trends, or comparisons across multiple runs ("getting better" / "compare last week" / "how has performance changed" / "what did /pace find across sessions").
- **Gate**: Project has entries in `run_log.csv` or `command_performance_log.md` (files exist on disk).
- **Anti-trigger**: User asking about result of a single specific run; OR no prior logged runs exist to compare; OR user already reading `run_log.csv` content in this turn.
- **Failure mode caught**: Informal mental comparison draws incorrect trend conclusions; performance regressions go unnoticed.

### 14. /review

- **Observable**: An external document has arrived in the conversation (paste, file attachment, or user quotes content attributed elsewhere — "my advisor sent" / "committee feedback" / "here's the draft" / "reviewer 2 says").
- **Gate**: User wants evaluation, critique, or decision — not just a brief summary or restatement.
- **Anti-trigger**: User asks for a brief summary only ("give me the gist"); OR document is the user's own work (not external); OR critique already delivered in this turn.
- **Failure mode caught**: External document evaluated by single-agent perspective; systematic blind spots missed.

### 15. /help

- **Observable**: User message expresses explicit uncertainty about which toolkit command to use ("which command" / "what should I run" / "is there a command for" / "I'm not sure how to" / "where do I start with").
- **Gate**: ≥2 plausible candidate commands could apply AND user has not named a specific command.
- **Anti-trigger**: User already named the specific command they want (knows what they want, asking how to use it); OR question is about a specific task that maps unambiguously to a single command.
- **Failure mode caught**: User picks command by guesswork; under-uses the right tool or over-uses a costly one.

---

## How to opt in

By default this fragment is NOT loaded. To activate it:

1. **Review** the rules above. They will affect which commands Claude proactively suggests during your sessions.
2. **Add ONE line** to your CLAUDE.md (project root, or `~/.claude/CLAUDE.md` for global):

   ```
   @path/to/ai-research-toolkit/shared/proactive_fragment.md
   ```

   The exact path depends on where you have the toolkit checked out. Run `bash ai-research-toolkit/install.sh` and look for the post-install message — it will print the literal `@import` line for your installation.

3. **(Recommended) Delete the legacy /coa rule** in your existing CLAUDE.md if you have one — the `## Council of Agents — Proactive Suggestion Rule` section. The fragment's row 2 above is its successor with a sharper Gate. Leaving both means /coa fires twice per qualifying turn.

## How to opt out

Remove the `@import` line from your CLAUDE.md. The fragment is byte-isolated; no other toolkit machinery depends on it being loaded.

---

## Falsifiable pilot gate (for any future runtime upgrade)

This fragment ships as the **declarative path**. Whether to ever upgrade to a runtime market-style variant is gated by the following pre-registered empirical bar:

| Tier | Metric | Threshold | Sample size |
|---|---|---|---|
| **Primary (decisive)** | `AONR = (TP_acted − 4·FP_acted) / observable_hits_triaged` | **≥ 0.40** weighted-mean | **N ≥ 50** sessions (target 75) |
| **Ratification R1** (measurement-credentialing) | Stage-2 inter-labeler Cohen's κ on SHOULD-FIRE | **κ ≥ 0.65** | ≥ 60 dual-labeled segments |
| **Ratification R2** (durability-credentialing) | `fatigue_delta = AONR(first half) − AONR(second half)` | **≤ 10 pp** | Same N as primary |

**Rules of combination**: AONR is decisive. R1-fail → metric un-credentialed (verdict: "rejected as un-credentialed", not "failed"). R2-fail → AONR clearance treated as novelty-driven, upgrade held in re-pilot. R1 and R2 cannot independently *cause* a pass; they can only invalidate a primary pass.

**Why AONR ≥ 0.40**: Krishnan (2026) measured hub-spoke at 4× solo cost. For a runtime upgrade's expected value to clear, `Useful_yield(runtime) ≥ 4 × Useful_yield(declarative)`. If declarative-only AONR ≈ 0.10, runtime must clear 0.40. Below that threshold, market-style runtime is strictly dominated by ship-declarative-only. The FP weight `w = 4` is *not* a free parameter — it is the same Krishnan ratio that sets the primary threshold. **One citation, one knob, one statistic.**

**Re-pilot trigger**: AONR rises through 0.40 on a fresh 30-session window after fragment revision; OR `stage2_kappa` drops mid-pilot; OR a previously-structural miss class becomes routable.

**Removal trigger**: AONR < 0.20 AND ≥80% of Stage-2 misses are `structural` (cases the proposed runtime variant also could not catch) → freeze declarative-only as permanent and abandon the upgrade plan.

**Secondary check (optional)** — Krishnan-Miss Concentration Index (KMCI) on flagged misses: if upgrade is contemplated despite AONR ≥ 0.40, also verify ≥60% of misses are concentrated in command rows where multi-perspective evaluation is the bottleneck (vs. distributed across all 15 rows uniformly, which would suggest a fragment text problem rather than a missing-runtime problem).

---

## References

- Krishnan (2026), "Why Coase Needs Hayek." Empirical baseline for the 4× hub-spoke cost premium and the AONR threshold derivation.
