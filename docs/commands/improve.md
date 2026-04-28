# /improve — Infrastructure Improvement Scanner

You've been using Claude Code for three months and suspect your setup has accumulated inefficiencies you can't see.

## When you need this

- After a session where something felt harder than it should have been
- Monthly as a routine infrastructure audit
- After major project milestones, when your workflow has evolved but your setup hasn't

## What it does — and what it won't

`/improve` scans your session context, git history, and Claude Code infrastructure files (CLAUDE.md, slash commands, JIT references, settings) for specific improvement opportunities. It produces a structured report with prioritized findings — not a vague "you could do better" but "this specific reference file is stale and here's the fix."

**Note**: `/improve` produces a report and recommendations — it does not apply changes automatically. You review and decide what to action.

## Worked example

Dario has been using Claude Code on his wage analysis project for three months. He keeps re-explaining the same context at the start of sessions, and a reference file he created in January is now out of date.

```
/improve
```

`/improve` returns four findings: (1) his CLAUDE.md JIT table is missing an entry for the new `placebo_tests.md` reference file — proposes the table row; (2) `/startup` isn't finding daily summaries because the summary folder path in his config points to an old location — proposes the fix; (3) he ran `/pace` twice this session and got the same discrepancy both times — the underlying script likely has a persistent bug; (4) an `/improve` candidate flagged in yesterday's summary was never actioned — surfaces it again.

## Try it

```
/improve
/improve all
```

> *After actioning findings from this report, run `/commit` to checkpoint the infrastructure changes — improvements applied but not committed are easy to lose across sessions.*
