---
name: step-by-step
description: One thing at a time, nothing skipped. Two subjects — a git-derived MANIFEST of what a session changed (walk it, explaining each item), or the numbered WORK LIST /list-maker keeps (walk it, or EXECUTE it — take the next item, do it, mark it done with its evidence, stop for adjustments). Use when a session changed several things and the user needs to understand each one, when they ask to be walked through, or when /list-maker hands over a list to work through. One item per turn; never batches on its own.
allowed-tools: Read, Grep, Glob, Bash(python3:*), Bash(git:*), Skill, AskUserQuestion
---

# /step-by-step — one thing at a time, and nothing skipped

**Version**: 1.0 (toolkit v2.2.0).

## The failure this exists to prevent

Not a bad explanation. **A walkthrough that covers seven of nine things while sounding complete**, because the list
of things came out of the same memory doing the explaining. Nobody can audit an omission they were never shown.

So the list is **derived from git, never recalled**, and coverage is tracked against it. The script decides whether
the explaining is finished; you only do the explaining.

The runner is `python3 ~/.claude/skills/step-by-step/assets/step_by_step_run.py` (written `step_by_step_run.py` below).

## Step 1 — The gate

Two questions, usually already answered by the request. **If so, say so in one line and go to Step 2.**

1. **What window and which repositories?** Default: since the session started, across every repository it touched.
   If you cannot name them, ask: a manifest over the wrong set is worse than none.
2. **Anything they already understand and want skipped?** Cover it anyway in one line and mark it covered. Do not
   drop it silently.

## Step 2 — Build the manifest, and show it first

```bash
step_by_step_run.py manifest --since "2026-09-08 20:00" --repo <repo> --repo <other-repo> [--path <subfolder>]
```

It lists the commits in the window **and** everything still uncommitted or untracked, because a session's work is not
only what got committed, and an untracked file is the easiest thing to forget you made. `--path` narrows it to the
part of a large repository the session touched.

**Show the numbered list before explaining anything.** The user was there. They will spot a missing item faster than
you will, and they can say which one to start with.

An unreadable `--since` is refused rather than passed to git: `git log --since=<garbage>` exits 0 and quietly ignores
the filter, handing back a manifest of the wrong size.

## Step 3 — Order the items so each one builds on the last

**Dependency order, not chronological.** The session jumped around; the explanation must not. Start with what
everything else rests on, then what it enabled. When two items are independent, take the finished one first.

## Step 4 — Explain ONE item, then stop

Three beats per item:

1. **What changed.** In plain terms, not the commit subject reworded.
2. **Why.** What was wrong, or what it makes possible. This beat carries the understanding; the other two are its
   context.
3. **Is it closed?** Closed, closed with a caveat, or still open. Say which plainly, and if it is open, say what would
   close it.

Then mark it and stop:

```bash
step_by_step_run.py cover <n>
```

**One item per turn, and never batch on your own initiative.** If the user asks for three, give three. If they say
next, give the next one. Volunteering a batch defeats the point of the skill.

**Do not ask "shall I continue?"** Explain the item, then stop. Their next message is the continue signal; a question
at the end of every item turns nine items into eighteen turns.

## Step 5 — Refuse to call it finished early

```bash
step_by_step_run.py verify
```

Exit 0 means every item was explained. **Exit 1 names what was not, and you do not say the walkthrough is done.** That
refusal is the reason this skill has a script. `status` prints what is left at any point.

## Walking the WORK LIST, and the rule about clearing it

Everything above walks a **manifest**: what a session changed, derived from git. The other subject is the **work
list**, the numbered ledger `/list-maker` keeps (one `worklist.json` per stream of work). Every `list_maker_run.py` call
below takes `--ledger <that file>`.

### Two modes over a work list — say which one you are in

**Walk**: explain one open item (what it is, why it is on the list, what would close it), stop, wait. Read-only.

**Execute**: what `/list-maker` hands over to after a meeting.

```bash
L="<stream>/worklist.json"
python3 ~/.claude/skills/list-maker/assets/list_maker_run.py active --ledger "$L"   # show the list FIRST
python3 ~/.claude/skills/list-maker/assets/list_maker_run.py next   --ledger "$L"   # the one item to do now
```

1. **Show the active list, then name the one item you are taking**, by number. The user may reorder first
   (`bump --id N --rank 1`).
2. **Do that one item in full, under the project's own discipline**: its tests, its gates, its commit conventions. An
   item marked `outward` (an email, a push, a send) stops for the user's approval before the send, in the turn of the
   send. One approval covers that one send.
3. **Mark it, citing the evidence**, then stop:
   ```bash
   list_maker_run.py status --id N --set done --why "commit <hash>; check <name> passed" --ledger "$L"
   ```
   If the item turned out to be a decision for someone rather than work to build, use
   `--set deferred --why "owner: <the question>"`. Deferred still counts as active, and the question goes in the note.
4. **One item per turn.** After the mark, say in one line what is next and stop. The pause is where the plan gets
   adjusted; that is its point, not a formality.
5. **Work surfaces work.** Anything an item turns up goes on the ledger at the tier it deserves (`add`), never into
   your head. A tier-1 add joins the active list, and the cap warns.
6. **When `active` exits 3, stop and ask** whether to start a new active list, and out of which items.

A daily summary written after an execute session names the numbers that moved and the numbers still open, and cites
the ledger as the record.

### The three rules about the active list

1. **Tier 1 IS the active list, and it is short.** Seven items at most: what fits in one sitting, not everything that
   matters. Everything else lives at tier 2 and below.
2. **Adding mid-walk is allowed and expected.** A new item goes on at the tier it deserves. The cap **warns and still
   prints** rather than refusing: a gate that fires in the middle of ordinary work gets routed around.
3. **When it clears, stop and ask. Never promote the next batch on your own.** `active` exits **3** when every tier-1
   item is done, deferred or dropped, and 3 is not 0 on purpose: a caller must be unable to confuse "cleared" with
   "here is your list". Say the list is clear, show what waits below it, and ask whether to start a new one. Promoting
   silently turns a short list the user agreed to into an endless one they did not.

### Why there is no second list and no renumbering

A new list does **not** mean new numbers. The ledger's whole promise is that item 14 is item 14 in every summary,
commit message and email that ever cited it. Renumbering would make every one of those citations point at different
work, and nothing about the artifact would look wrong afterwards. So a new list is made by clearing tier 1 and
promoting the next few; the numbers ride along unchanged.

### A deferred item still counts as active

`deferred` is not `done`: it was set aside, not finished. A list that dropped deferred work would report CLEARED while
work remained, which is the one thing exit 3 must never do.

## What this skill does not do

- **It does not judge the work.** It explains what happened. If an item was a mistake, say so in the "why" beat, but a
  walkthrough is not a review.
- **It does not change anything** while walking. Read-only, except its own manifest state. Execute mode does the work
  of one item at a time, under the project's own rules.
- **It does not write a summary.** `/daily-summary` owns that.

## The script

| Command | Does | Exit |
|---|---|---|
| `manifest --since <when> [--repo P]... [--path P]...` | list and number every item | 0, or 2 on a bad date, no repository, or an empty window |
| `show [<n>]` | one item, or the whole list with ticks | 0, 2 if out of range or no manifest |
| `cover <n> [<n>...]` | mark items explained | 0, 2 on a bad index |
| `status` | what is covered, what is left | 0 if complete, 1 if not |
| `verify` | the refusal | 0 complete, 1 incomplete, 2 no manifest |
| `reset` | discard the manifest | 0 |

An empty window is exit 2, not 0. An empty manifest and a wrong `--since` look identical, and "nothing happened" is
the one answer a walkthrough must never invent.

State lives in `~/.claude/toolkit/state/step-by-step.json`. In the toolkit repository,
`shared/skills/step-by-step/assets/step_by_step_selftest.py` runs 15 cases against real temporary git repositories, then
removes each of the 10 guards in turn and requires the case aimed at it to turn green. A case that still blocks
without its own guard was blocking for another reason and proves nothing.

## Related

`/list-maker` (writes the work list) · `/daily-summary` (the written record; this is the spoken one) · `/bulletproof`
(why the guard removals are one at a time).
