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
from one paragraph) and one role-site can need several blocks (`/weeklysummary` names its writer twice).

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
| 12 | dailysummary | writer | `dailysummary.md:113` | `:113` | `sonnet` |
| 13 | weeklysummary | writer | `weeklysummary.md:20`, `:106` | `:20` and `:106` (two blocks, one role-site) | `sonnet` |
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
sentences are `dailysummary.md:117`, `pace.md:205`, `weeklysummary.md:10`, `:24`, `:288`; no shipped command says
"Task tool".

## Part 2 — Run and reconciliation

[GAP: written after the first report-only run of `tests/check_models.py`; nothing here before that run.]
