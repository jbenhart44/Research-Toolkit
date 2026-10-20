# Model gate triage (v2.1.0)

The model gate (`tests/check_models.py`) finds the places where a command starts a subagent and checks that each one
names its model. Before its exit code was trusted, every hit it reported was sorted by hand into this file. This file
is in two parts, in the order they were written:

1. **The Prior**, written and committed before the gate existed. A prediction made after seeing the gate's output
   checks nothing, so this part is not edited after the run. Mistakes in it stay, and part 2 says what they were.
2. **The run and the reconciliation**, written after the first report-only run.

Units. A **role-site** is one role at one place: one kind of agent that a command starts at one step (for example,
`/pace` Coach C). A **block** is a run of lines with no blank line between them, which is what the gate reads; a
heading on its own merges with the block under it. One block can hold several role-sites (`/pace` starts both Players
from one paragraph) and one role-site can need several blocks (`/weekly-summary` names its writer twice).

## Part 1 — Prior (committed before any gate run)

Tree: the v2.0.2 branch, whose six spawning commands are unchanged from v2.0.1 apart from line 2 and the run-report
call. Read by hand; no script was run.

**Bracket for v2.1.0 after the edits: 14 role-sites in 6 commands; 14 to 18 marked blocks.** Point estimate: 14 marked
blocks and 16 blocks marked `spawn: none`.

### The 14 role-sites

| # | Command | Role-site | Where (v2.0.2 line) | Block the marker goes on | Model named today |
|---|---|---|---|---|---|
| 1 | coa | council members | `coa.md:381` ("Dispatch each member with the Agent tool") | `:381` | none |
| 2 | coa | local cross-check fallback | `coa.md:442` and `:445` | `:439-443` and `:445-447` (two blocks, one role-site) | `sonnet` in `:442` only |
| 3 | coa | Chair | `coa.md:519` | `:517-519` (heading merged) | none |
| 4 | coa | rebuttal round | `coa.md:712` ("Spawn 1-2 selected members") | `:712`, after a reword | none |
| 5 | pace | Player A | `pace.md:219`, `:225` | `:217-219` (one block for both Players) | `sonnet` |
| 6 | pace | Player B | `pace.md:219`, `:262` | `:217-219` | `sonnet` |
| 7 | pace | Coach C | `pace.md:301` | `:299-301` (one block for both Coaches) | `sonnet` |
| 8 | pace | Coach D | `pace.md:301` | `:299-301` | `sonnet` |
| 9 | pace | Cross-Reviewer | `pace.md:401` | `:401` | `sonnet` |
| 10 | pace | revision reviewer | `pace.md:614` ("spawn ONE reviewer") | `:614`, after a reword | `sonnet` |
| 11 | review | the three lens agents | `review.md:65` | `:63-65` (heading merged) | none |
| 12 | daily-summary | writer | `daily-summary.md:113` | `:113` | `sonnet` |
| 13 | weekly-summary | writer | `weekly-summary.md:20`, `:106` | `:20` and `:106` (two blocks, one role-site) | `sonnet` |
| 14 | readable | transcriber | `readable.md:47` | `:45-51` | none |

Not role-sites: the crossmodel route at `coa.md:400-404` (an external model, outside the Claude account; it gets a
`spawn: external` marker) and the four PCV agents in `pcv/` (upstream, compared by equality, never edited).

### What the gate should report on the untouched tree (C8, Landmark)

**28 hit blocks**: 12 role-site blocks and 16 that are not spawns.

- **Two role-sites are invisible to the patterns until reworded**: the `/coa` rebuttal (`:712`, "Spawn 1-2 selected
  members" names no agent) and the `/pace` revision reviewer (`:614`, "spawn ONE reviewer" names no agent). The plan's
  C8 expected the rebuttal to print as a site with no literal; this Prior predicts the gate does not see it at all.
- **Literal model in the block, among the 12 role-site blocks: 7 yes, 5 no.** The five `no`: `coa.md:381` (members),
  `coa.md:445-447` (the cross-check's second block), `coa.md:517-519` (Chair), `review.md:63-65` (lenses),
  `readable.md:45-51` (transcriber). This differs from the plan's C8 list (members, Chair, rebuttal, lenses, readable):
  the rebuttal is unseen, and the cross-check's second block is a `no` the plan did not count.

**The 16 blocks that are not spawns** (each will get `<!-- spawn: none reason="..." -->`):

| File | Block | Why it matches | What it is |
|---|---|---|---|
| coa | `:8-10` | "Spawns … cross-check agent" | cost note |
| coa | `:317` | "Agent tool call" | the no-simulation warning |
| coa | `:729-730` | "Subagent spawning unavailable" | edge-case heading |
| pace | `:8-10` | "spawns 5 subagents" | cost warning |
| pace | `:133` | "subagents actually spawned" | rationale |
| pace | `:180-182` | "before any agent is spawned" (heading merged) | the declaration rule |
| pace | `:205` | "Agent tool", "spawns" | the model policy paragraph |
| pace | `:207` | "PACE spawns five of them" | why the model is explicit |
| pace | `:221` | "Agent tool calls" | the no-simulation warning |
| pace | `:606` | "spawn two Players" near "multi-agent" | rationale |
| pace | `:643-647` | "Subagent spawning is not available" | edge case |
| review | `:12` | "Spawns 3 subagents" | cost note |
| review | `:203-205` | "Do NOT spawn a 4th agent" | the Chair is the Clerk |
| review | `:241-243` | the same words in a comment | the Chair is the Clerk |
| commit | `:217-222` | "agent spawning" | an example commit message |
| improve | `:234` | "uses the Agent tool" | a question in a checklist |

Other predictions: no Python file in `scripts/` or `hooks/` passes `--model` or calls `claude -p`; `audit.md` and
`quarto.md` list `Agent` in `allowed-tools` and start no agent (removed in v2.1.0); the five "best available model"
sentences are `daily-summary.md:117`, `pace.md:205`, `weekly-summary.md:10`, `:24`, `:288`; no shipped command says
"Task tool".

## Part 2 — Run and reconciliation

**First run**: `python3 tests/check_models.py --report` on 2026-10-20, on the v2.0.2 commands before any edit (commit
`71f6c32`), after the gate's self-test passed 30/30. Output: 32 hit blocks, 0 Python hits.

| Prior said | The run found | Verdict |
|---|---|---|
| 28 hit blocks | 32 | Prior wrong by 4: four blocks the reading missed, listed below |
| 12 role-site blocks | 12, the same twelve | accept |
| literal model: 7 yes, 5 no; the five named | 7 yes, 5 no; the same five | accept |
| rebuttal and revision reviewer unseen | neither appears | accept (and the plan's C8 list was wrong about the rebuttal) |
| 16 blocks that are not spawns | 20 | the 16 predicted, plus 4 |
| no Python hits | none | accept |

**The four blocks the Prior missed.** All four are not spawns; each gets `spawn: none`.

| Block | Why it matches |
|---|---|
| `coa.md:617` | the verdict table's `fallback` row: "a session where the Agent tool is available" |
| `pace.md:580` | the verdict list: "written by the orchestrator rather than by two spawned agents" |
| `pace.md:586` | the verdict table's `fallback` row: "the Agent tool is available" |
| `pace.md:743` | the run-report template: `agent_count: {total agents spawned}` |

**Line numbers.** Ten blocks start one or more lines above where the Prior placed them (`coa.md:6`, `:517`, `:727`;
`pace.md:131`, `:178`, `:604`; `commit.md:216`; `improve.md:232`; `readable.md:43`; `weekly-summary.md:104`), because a
heading merges with the block under it. Same blocks; the Prior quoted the content line.

**Two design gaps found by the run, fixed before any marker was written.**

1. `coa.md:445-447` starts the local Sonnet cross-check **and** calls `mcp__crossmodel__query_model`. One block takes one
   marker, so the block is split: the external call gets a `spawn: external` block, the Sonnet fallback a role block.
2. M15 scanned every Markdown file, so README, DESIGN and `coa/CROSSMODEL_SETUP.md`, which describe the crossmodel
   route, would all be findings. M15 is now scoped to the files that instruct an agent: commands, skills and seat files.

**Rewordings so the patterns see a spawn** (no change to what the command does):

- `coa.md:712`, the rebuttal: "Spawn 1-2 selected members, each as its own Agent tool call".
- `pace.md:614`, the revision reviewer: "spawn ONE reviewer subagent".

**Two hits could not take a marker**, because they sit inside a fenced template the command prints: a marker there
would appear in the user's output. Their wording changed instead, "spawn" to "start": `review.md`'s comment in the
Chair-synthesis template, and `pace.md`'s `agent_count: {total agents started}` in the run-report template. So 20
non-spawn blocks became 18 `none` markers.

### After the edits

`python3 tests/check_models.py --report`, same day:

```
balance: 36 blocks | by pattern 32 | role 14 | none 18 | external 4 | unmarked 0
```

| Count | Prior | After | Verdict |
|---|---|---|---|
| role-sites (distinct `site=` values) | 14 | 14, and each equals a table site (M11 passes both ways) | accept |
| marked role blocks | 14 to 18, point 14 | 14 | accept: inside the bracket, on the point |
| role blocks with a literal `model: "<alias>"` | all | 14 of 14 | accept |
| `none` blocks | 16 | 18: the 16, plus the 4 the Prior missed, minus the 2 reworded | accept, reconciled |
| `external` blocks | 1 (the crossmodel route) | 4: the route, the Pre-flight check, the split half of the cross-check, and the persona-routing sentence | the Prior counted the route as one place; M15 marks each block that names it |
| unmarked pattern blocks | 0 | 0 | accept |

Balance: 32 pattern blocks = 14 role + 18 `none`; the 4 external blocks match no spawn pattern (they are found by
M15's crossmodel pattern instead); 32 + 4 = 36.

**Corpus controls (C13)**, now in the gate's `--self-test` so they re-run: deleting the literal at the `/pace` Player
spawn exits 1 naming that block (M4); a `reasoner` marker changed to `opus` is M5; a spawn sentence reworded with its
marker deleted is M1; a spawn reworded past every pattern with its marker deleted is still caught, by the table's site
list (M11). That last case is the gate's honest limit: it catches a deleted marker at a listed site, not a new site
that nobody added to the table.
