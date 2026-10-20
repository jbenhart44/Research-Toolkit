# Research Amp Toolkit — Usage Guide

The 24 commands in this toolkit work best as a system, not as isolated tools. This guide gets you from "just installed" to productive in under 10 minutes.

---

## Part 1: Start Here

**First, once:** run `/setup`. It asks where your summaries, plans and evidence live, which workstreams you track, and how you commit, then writes `~/.claude/toolkit-config.md`. Every other command reads that file, so nothing below assumes anyone else's folders.

Three situations cover 80% of first-year use cases.

**"I have papers to cite and I need to verify my numbers before submitting."**
→ Run `/readable papers/` first to extract `.txt` from your PDFs. Then run `/audit your_document.qmd` to verify every cited figure against the source. These two commands always go together.

**"I have a research decision I've been going back and forth on for days."**
→ Run `/coa "your question"`. Six specialist perspectives will argue it out, and a Chair will synthesize where they agree and where the genuine ambiguity lives. For a faster 3-seat panel on a focused question, use `/coa --quick`.

**"I closed my terminal last week and I don't know where I left off."**
→ Run `/startup`. It reads your recent daily summaries and tells you exactly what's blocked, what's next, and what files changed. Requires that you've been writing `/daily-summary` at the end of sessions — start doing that today.

---

## Part 2: Three Workflow Chains

### Chain 1: The Citation Pipeline

*For any session where you write cited figures into a document.*

```
/readable papers/          ← extract .txt from source PDFs
[write your document]
/audit your_document.qmd  ← verify every cited number
/commit                    ← checkpoint
/daily-summary              ← record what was written and verified
```

Maya (public health) runs this chain every time she adds citations to her dissertation chapter. The `/readable` step takes a few minutes; it saves hours of "wait, where did that number come from?" before her defense.

### Chain 2: The Hard Decision Chain

*For architecture, methodology, or research design decisions.*

```
/coa "your decision question"   ← get 6 expert perspectives
/daily-summary                   ← capture the rationale before it leaves context
```

Priya (computational biology) runs this chain before committing to any pipeline choice she can't easily reverse. The `/coa` output is advisory — you decide. The `/daily-summary` step makes sure the council's reasoning is on disk, not just in her memory.

### Chain 3: The Session Rhythm

*For every work session, every day.*

```
/startup            ← orient at the start
[do your work]
/pace or /coa       ← verify or decide if needed
/commit             ← checkpoint before closing
/daily-summary       ← record what happened
```

Then next session: `/startup` reads yesterday's `/daily-summary` and you pick up exactly where you left off. The rhythm builds a searchable history of every decision you've made.

---

## Part 3: Five Things the Spec Gets Wrong

The command specs are accurate on behavior but misleading on a few key points. Read these before you hit a confusing error.

**1. `/readable` — the Read tool CAN render PDFs.**
The old documentation said "use `/readable` because Read can't render PDFs." That's wrong. Claude Code's built-in Read tool handles individual PDFs natively. Use `/readable` when you need batch processing across a whole directory, image-based OCR for scanned documents, or persistent `.txt` files you can grep across multiple papers. Not because Read is broken.

**2. `/startup` assumes you write daily summaries.**
`/startup` is a summary reader, not a git reader. If your summary folder is empty, it falls back to `git log` — useful but not the full workstream picture. The fix: run `/daily-summary` at the end of every session. It takes 60 seconds and makes every future `/startup` dramatically more useful.

**3. `/weekly-summary` requires Sonnet and overwrites on re-run.**
On Haiku-only plans, `/weekly-summary` will fail at the summary-writing step. It also overwrites the existing weekly file each time you run it — the weekly summary is a live document until the week closes. If you need to preserve a mid-week snapshot, rename the file before re-running.

**4. `/audit` reports discrepancies — it doesn't give you a verdict.**
MISMATCH and NOT ON DISK are findings, not failures. Some number variations are acceptable ("$340" vs "$340.00"); some aren't. You review the findings and decide what to fix. The command surfaces the issues; you make the call.

**5. `/simplify` does not run tests.**
`/simplify` reads your code and identifies issues — it doesn't execute anything. Always run your test suite separately after applying any `/simplify` suggestions. Use it on working code, not broken code.

---

## Part 4: Quick Reference

| Command | One line | Landing page |
|---|---|---|
| `/setup` | Answer a few questions; writes the config every other command reads | [Source](https://github.com/jbenhart44/Research-Toolkit/blob/main/shared/commands/setup.md) |
| `/audit` | Verify every cited figure against the source paper | [Guide](https://jbenhart44.github.io/toolkit/commands/audit.html) |
| `/coa` | Get 6 expert perspectives on a research decision | [Guide](https://jbenhart44.github.io/toolkit/commands/coa.html) |
| `/commit` | Group and commit changes with clean messages | [Guide](https://jbenhart44.github.io/toolkit/commands/commit.html) |
| `/daily-summary` | Record what happened this session | [Guide](https://jbenhart44.github.io/toolkit/commands/daily-summary.html) |
| `/help` | Not sure which command to use? Start here | [Guide](https://jbenhart44.github.io/toolkit/commands/help.html) |
| `/improve` | Audit your Claude Code setup for stale references and gaps | [Guide](https://jbenhart44.github.io/toolkit/commands/improve.html) |
| `/pace` | Verify a deliverable through two independent agents | [Guide](https://jbenhart44.github.io/toolkit/commands/pace.html) |
| `/pcv` | Plan, construct and verify a project in three auditable phases | [Guide](https://jbenhart44.github.io/toolkit/commands/pcv.html) |
| `/quarto` | Generate a slide deck from background documents | [Guide](https://jbenhart44.github.io/toolkit/commands/quarto.html) |
| `/readable` | Extract text from PDFs for batch search and citation work | [Guide](https://jbenhart44.github.io/toolkit/commands/readable.html) |
| `/review` | Read a paper or memo through three expert lenses | [Guide](https://jbenhart44.github.io/toolkit/commands/review.html) |
| `/run-log` | See how your commands have performed across runs | [Source](https://github.com/jbenhart44/Research-Toolkit/blob/main/shared/commands/run-log.md) |
| `/simplify` | Clean up working code or documents | [Guide](https://jbenhart44.github.io/toolkit/commands/simplify.html) |
| `/startup` | Orient at the start of a session | [Guide](https://jbenhart44.github.io/toolkit/commands/startup.html) |
| `/weekly-summary` | Roll up the week's work by workstream | [Guide](https://jbenhart44.github.io/toolkit/commands/weekly-summary.html) |
