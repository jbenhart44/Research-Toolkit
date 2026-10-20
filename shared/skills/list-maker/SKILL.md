---
name: list-maker
description: Turn a meeting transcript, an email thread, notes, or any session that produced more work than one sitting holds into a numbered, tiered work list that survives across sessions, so /step-by-step can walk it one item at a time and a summary can say "we're on number 14". Every item keeps its number for life, priority moves without the number moving, and a deferred item is never lost. One ledger per stream of work. Ends by handing the list to /step-by-step. Invoke as /list-maker <file>, or bare /list-maker to see what is open.
allowed-tools: Read, Grep, Glob, Write, Edit, Bash(python3:*), Bash(git:*), Skill, AskUserQuestion
---

# /list-maker — the numbered list a meeting leaves behind

**Version**: 1.0 (toolkit v2.2.0).

**The promise is a stable number.** Number 14 is the same piece of work next week, next month, and in a summary
written three sessions from now. Everything else here exists to protect that.

The runner is `python3 ~/.claude/skills/list-maker/assets/list_maker_run.py` (written `list_maker_run.py` below).

---

## Streams — one ledger per stream of work

A number only means something inside one file, so one client's item 14 must never be another's. **Each stream of work
gets its own ledger**, usually a `worklist.json` in the folder where that stream's transcripts live. Every command
takes `--ledger <path>`; without it the script uses `$LIST_MAKER_LEDGER`, then `worklist.json` in the working
directory.

A ledger records who can own an item the first time it is written, for example
`list_maker_run.py add --items items.json --owners me,client,both --ledger "Client A/worklist.json"`. Afterwards a
different `--owners` is refused, because an owner name is cited the same way a number is. A ledger with no owners
recorded uses `me, them, both`. A new stream is a new ledger, never new numbers in an old one.

**Commit the ledger.** The numbers are the product, and an untracked ledger lives on one disk. The script warns on
every save of an untracked ledger.

If a stream already has its own numbering that other people see (a tracker, a ticket system), put that number in an
item's `note` so the two never compete. The ledger number is the one summaries cite.

## Step 1 — The gate: three questions, and skip it when they are answered

The script cannot make these calls. **If the request already answers them, say so in one line and go to Step 2**: a
gate with nothing to ask is friction, and friction gets routed around.

1. **Which stream's ledger is this run adding to?** Almost always the standing cumulative one. A separate ledger is
   for a genuinely separate stream, and it costs the one thing the ledger is for.
2. **Where does the tier line sit for this meeting?** Tier 1 is "before the next deadline, the next send or the next
   meeting"; tier 2 is "this week". If the meeting named a date, the date decides it and there is nothing to ask.
3. **Is anything outward-facing?** An email, a push, anything another person receives. Those get a human approval
   when the item is executed, not when it is listed, but they are marked now (`"outward": true`) so `/step-by-step`
   stops on them.

Ask with `AskUserQuestion` only where a different answer visibly changes the list.

---

## Step 2 — Scan the input for candidates

```bash
python3 ~/.claude/skills/list-maker/assets/list_maker_run.py scan --input "<folder>/<file>.txt"
```

The input is any text: a meeting transcript, an email thread saved as text, meeting notes, a chat export. In an email
thread, quoted earlier messages (lines starting `>`), "On … wrote:" lines and header lines are skipped, because the
quoted text was scanned when that message arrived and scanning it again makes one promise into two items. Something
the script cannot read (a PDF, a Word file) is extracted to text first, with `/readable`.

It prints every line carrying an obligation cue ("I'll", "we need to", "can you", "by tomorrow", "follow up"), with its
line number. **These are candidates, not items**, and the script says so. It is deliberately over-inclusive: a false
positive costs one line of reading and a false negative loses work, which is the failure this tool exists to prevent.

**Read them. You decide what is an item.** A regex cannot tell *"I'll send you an email about the infrastructure"*
from *"I'll be retiring before I ever get around to that"*, and a list that contains the second is a list nobody
trusts.

### Two things the scan cannot do, and you must

**It cannot tell you who owns an item.** Transcription tools often label every speaker with the name of the account
that recorded the meeting, whoever is talking. Owner comes from content: who says "I'll", what they are describing,
whose half of the work it is. Get it wrong and the list tells one person to do another's work.

**It cannot tell an obligation from a musing.** *"It'd be nice if you could just click through that"* is an idea;
*"I'll send you that email"* is an item. When it is genuinely ambiguous, put it in at tier 4 rather than dropping it.
A someday item costs one line; a dropped one costs the work.

---

## Step 3 — Write the items and add them

Write a JSON file, then:

```bash
list_maker_run.py add --items items.json --ledger <ledger>
```

```json
{"items": [
  {"text": "Send the project infrastructure email with the repository pointers",
   "owner": "me", "tier": 1, "outward": true,
   "source": "2026-09-10 transcript:623",
   "note": "\"I'll send you an email about the infrastructure for the project\""}
]}
```

`owner` is one of the ledger's owners. `tier` is 1 to 4. **`source` is a file and a line**, so a later reader can
check what was actually said rather than trusting the paraphrase. **Quote, do not paraphrase, in `note`**: the
source's own words are the evidence, and a paraphrase in the ledger becomes the record within a week.

**Re-running `add` on the same meeting is safe.** Duplicates are found by normalised text, so case and punctuation do
not make an item new; an item already on the list gets its `last_seen` refreshed instead of a second number.

---

## Step 4 — Tier it, and re-tier it when asked

```bash
list_maker_run.py bump --id 14 --tier 1 --why "asked for the study guide first" --ledger <ledger>
list_maker_run.py bump --id 14 --rank 1 --ledger <ledger>          # order within a tier
```

**The id does not move.** That is the whole design, and the script says so on every bump. A tier is a claim about
what to do next; a number is the item's name.

| Tier | Means |
|---|---|
| 1 | now: before the next deadline, the next send, or the next meeting. **This is the active list.** |
| 2 | this week |
| 3 | when it comes up |
| 4 | someday, or too vague to act on yet |

**Tier 1 is short**: what fits in one sitting, not everything that matters. `active` warns past seven items and still
prints, because a gate that fires during ordinary work gets routed around.

---

## Step 5 — Hand it to `/step-by-step`, which walks it or works it

`/list-maker` ends by invoking `/step-by-step` on the ledger it just wrote. That skill has two modes over a work list:
**walk** (explain each open item, one per turn) and **execute** (take `next`, do that one item, mark it `done` with
its evidence, stop). Say which mode you are handing to; after a fresh list the default is execute, one item per turn.

```bash
list_maker_run.py active --ledger <ledger>          # the short "right now" list; exit 3 when it is cleared
list_maker_run.py list   --ledger <ledger>          # everything open and deferred, tier order
list_maker_run.py next   --ledger <ledger>          # the single item to start on
```

**Show the numbered list before doing anything.** The person was in the meeting; they will spot a missing item faster
than you will, and they will say which number to start on.

When an item is finished:

```bash
list_maker_run.py status --id 14 --set done --why "pushed at 287a5c9" --ledger <ledger>
```

**A finished item keeps its number forever.** It stops rendering by default and is still there under `list --all`.
Nothing is ever removed from the ledger.

---

## Step 6 — Cite the number, everywhere

In the daily summary, in a commit message, in a reply: **"item 14"**, not "the study guide thing". A number resolves; a
description drifts. A `/daily-summary` written after a session over a work list names the numbers that moved and the
numbers still open.

---

## The one thing that must never happen

**An id must never be reused.** Not after an item is done, not after it is dropped, not after a hand edit of the
ledger. Every summary, commit message and email that cited a number becomes silently wrong the moment that number
points at different work, and nothing about the artifact looks wrong afterwards.

The script guards it two ways: `next_id` only ever increases, and loading refuses a ledger whose `next_id` has fallen
to or below an issued id, naming the repair rather than performing it. **If that refusal ever fires, do not quietly
fix the number**: find out what edited the ledger first.

## Standing rules

- **Never delete an item.** Status changes; rows stay. Removing one needs the user to name it.
- **Never send or push from this skill.** It builds a list. An outward-facing item is marked, and the approval happens
  when that item is executed, in the turn it is executed.
- **`[GAP: …]` binds.** If an item's owner or date is genuinely unclear, write the gap into the text rather than
  guessing.

## Exit codes

| Code | Means |
|---|---|
| 0 | did the job |
| 1 | nothing to report: an empty list, no next item, nothing new added |
| 2 | refused: a bad id, a bad tier, an owner the ledger does not know, a corrupt ledger |
| 3 | `active` only: the active list is CLEARED. Stop and ask whether to start a new one |

## Verification

```bash
python3 ~/.claude/skills/list-maker/assets/list_maker_run.py --self-test    # the logic
```

In the toolkit repository, `shared/skills/list-maker/assets/list_maker_selftest.py` checks the command-line surface
(exit codes, a real round trip, the untracked-ledger warning), and `list_maker_mutations.py` proves both suites catch
each named defect: a reused number, a disabled corruption guard, a hidden deferred item, a cleared list that exits 0.
