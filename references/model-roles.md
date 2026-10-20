# Which model each toolkit agent requests, and why

Several toolkit commands start subagents: `/coa` seats and its Chair, `/pace` players and coaches, `/review` lenses,
the `/daily-summary` and `/weekly-summary` writers, the `/readable` and `/acquire` transcribers, and the
`/meeting-breakdown` agents. Each one now names the model it
requests instead of inheriting whatever model your session runs. This page says which model each kind of agent
requests on which kind of account, and why.

The table lives in `shared/model-roles.json`. The tables on this page, in the README and in `/setup` are generated from
it, and `tests/check_models.py` fails if they differ, or if any command starts an agent without naming its model.

All Anthropic facts on this page were read on **2026-10-20** from the pages linked beside them. Anthropic changes
models, plans and limits; the toolkit re-reads these pages before each release.

## The table

<!-- BEGIN GENERATED: role-table -->
| Role | Where it runs | `pro`, `team-standard`, `unknown` | `max5x`, `max20x`, `team-premium`, `enterprise`, `api`, `cloud` |
|---|---|---|---|
| `reasoner` | /coa: members, cross-check, rebuttal · /pace: player-a, player-b, coach-c, coach-d, cross-reviewer, revision-reviewer · /review: lenses · /quick-ten: council · /meeting-breakdown: player-a, player-b, coach-c, coach-d, cross-reviewer | sonnet | sonnet |
| `chair` | /coa: chair | sonnet | opus (`model_chair`) |
| `writer` | /daily-summary: writer · /weekly-summary: writer | sonnet | sonnet |
| `transcriber` | /readable: transcriber · /acquire: transcriber | haiku | sonnet (`model_transcriber`) |
<!-- END GENERATED: role-table -->

`/setup` asks which account Claude Code uses and stores it as `claude_account` in `~/.claude/toolkit-config.md`:

<!-- BEGIN GENERATED: accounts -->
| Answer | Stored as | Class |
|---|---|---|
| pro | `pro` | sonnet-ceiling |
| max5x | `max5x` | opus-ceiling |
| max20x | `max20x` | opus-ceiling |
| team-standard | `team-standard` | sonnet-ceiling |
| team-premium | `team-premium` | opus-ceiling |
| enterprise | `enterprise` | opus-ceiling |
| api | `api` | opus-ceiling |
| cloud | `cloud` | opus-ceiling |
| not sure | `unknown` | sonnet-ceiling |
<!-- END GENERATED: accounts -->

**The two classes are a toolkit cost policy, not a claim about which models an account can use.** Anthropic's pricing
page marks Opus as included on Pro, Max 5x and Max 20x, and not on Free (the Opus row of the plan table,
https://claude.com/pricing, retrieved 2026-10-20). The split is about allowance. A Pro plan has "a weekly usage limit
that applies across all models" (https://support.claude.com/en/articles/8325606-what-is-the-pro-plan). Team Standard
seats include "1.25x the Pro plan's per-session usage allowance", Premium seats "6.25x"
(https://support.claude.com/en/articles/9266767-what-is-the-team-plan), and Max 5x and Max 20x include five and 20
times the Pro per-session allowance (https://support.claude.com/en/articles/11049741-what-is-the-max-plan). Usage-based
Enterprise plans "have no plan or seat-level usage limits"
(https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan), and an API key or cloud provider is
"Pay-as-you-go, billed per token" with "No hard stop"
(https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code). Only one role changes with the
class: the Chair.

## Why each role requests what it does

**`reasoner` → sonnet on every account.** Council seats, PACE players, coaches and reviewers, review lenses and the
local cross-check. Anthropic's cost guidance for Claude Code says "Use Sonnet for teammates"
(https://code.claude.com/docs/en/costs, retrieved 2026-10-20), and describes Sonnet 5.5 as "The best combination of
speed and intelligence" (https://platform.claude.com/docs/en/models/overview). Before v2.1.0, `/coa` seats, `/review`
lenses and the `/readable` transcriber requested no model and ran on your session's model, which defaults to Opus 5.5 on
Pro, Max, Team, Enterprise and the Anthropic API (https://code.claude.com/docs/en/model-config). Requesting Sonnet costs
less; whether it changes what a council finds has not been measured.

**`chair` → opus on opus-ceiling accounts when `/model` lists Opus; otherwise sonnet.** The Chair writes the one
synthesis the user reads. Anthropic says "Opus costs several times more per turn than Sonnet, and Sonnet more than
Haiku" and that Opus "uses meaningfully more of your quota"
(https://support.claude.com/en/articles/14552983-models-usage-and-limits-in-claude-code). One Chair call per council is
where the toolkit spends that. `/setup` writes `model_chair: opus` only when your account is opus-ceiling **and** you
confirm that `/model` lists an Opus model, because "The /model command is always the source of truth for your account"
(same page). It never writes a value above the class default; edit the key if you want more. When `model_chair` is
missing, the Chair requests sonnet.

**`writer` → sonnet, never Haiku.** The summary commands state the reason themselves: smaller models have been observed
to produce inaccurate numerical figures, wrong file orderings and incorrect parameter values when summarizing technical
sessions.

**`transcriber` → haiku on sonnet-ceiling accounts, sonnet on opus-ceiling accounts (`model_transcriber`).**
Extraction is one of Haiku's listed uses ("For high-volume, latency-sensitive tasks such as classification, extraction,
and routing", https://platform.claude.com/docs/en/models/overview). The risk is a misread digit, which becomes a false
result in `/audit`. So on Haiku two readers transcribe the same pages independently, and
`scripts/check_transcription.py` refuses the transcription unless they agree on every number, page by page, along with
six checks on the text itself (page markers, page length, refusal text, vocabulary, expected names, extracted words). On
Sonnet one reader runs and the same six checks apply. When `model_transcriber` is missing, the transcriber requests
haiku, the sonnet-ceiling value, like every other role.

Against the admission test below, the Haiku transcriber meets 1 to 3: a script checks its output before anything is
installed, a number reaches a document only when two readers agree on it, and it is not a summary, a review or a
synthesis. **It does not yet meet 4**: no logged Haiku transcription run exists. Running it on smaller plans is the
author's decision of 2026-10-20, made with that gap stated; the first logged runs are the evidence that closes it.

## The Haiku admission test

A role runs on Haiku only if all four hold:

1. a script or the orchestrator checks its output against the files before anyone relies on it;
2. it writes no figure, count, quote or conclusion that reaches the user unchecked;
3. it is not a summary, a review or a synthesis;
4. a logged Haiku run of that kind exists without a stall.

No role in v2.1.0 passed, so no role requested Haiku. From v2.2.0 the transcriber requests Haiku on smaller plans with
criterion 4 still open, as stated above; no other role requests it. Anthropic's advice "For simple subagent tasks, specify model: haiku"
(https://code.claude.com/docs/en/costs) is the reason the test exists; the test is the toolkit's reading of "simple".
Counting and extraction that a script can do are moved into Python instead.

## How a command requests a model

Every place a command starts an agent carries the model on the call itself, as `model: "sonnet"`, because Claude Code
resolves a subagent's model in this order: "The per-invocation model parameter", then "The subagent definition’s model
frontmatter", then "The CLAUDE_CODE_SUBAGENT_MODEL environment variable", then "The main conversation’s model"
(https://code.claude.com/docs/en/sub-agents, retrieved 2026-10-20). Commands set no `model:` in their own frontmatter:
for a skill or command that setting applies "for the rest of the current turn" to the whole session
(https://code.claude.com/docs/en/skills).

The Chair's call is the one place that reads your config at run time. Its instruction is to pass `model` = the value of
`model_chair` in `~/.claude/toolkit-config.md` if it is `sonnet` or `opus`, and otherwise `sonnet`.

## MODEL FAILURE

The same block is copied into every command that starts agents. `tests/check_models.py` fails if a copy differs.

<!-- BEGIN MODEL FAILURE -->
**MODEL FAILURE — when an agent cannot run on the model it requested.**
1. **A session or weekly limit** ("You've hit your session limit"). These limits are shared across all models, so another model does not help. Stop starting agents, quote the error and its reset time, and offer two choices: wait, or stop. Do not retry.
2. **An Opus limit, or a model the account cannot use, on the Chair's `opus` request** ("You've hit your Opus limit"; "There's an issue with the selected model"). Retry the Chair once on `sonnet`. Write `fallback_from: opus` and the error text into the run report, and name the model that ran in the printed model line.
3. **Any other error, or any other role.** Stop that role, quote the error, and offer the choices: retry as written, run that role on the session's model, or stop. Never change a role's model on your own; rule 2 is the only exception.
4. Do not rely on a fallback-model setting for this: Claude Code never switches models on an authentication, billing or rate-limit error.
<!-- END MODEL FAILURE -->

Sources for the rules: the limit messages and "The session and weekly limits are shared across all models, so switching
models doesn’t restore access" (https://code.claude.com/docs/en/errors); the unavailable-model message
(https://code.claude.com/docs/en/model-config and /errors); "Authentication, billing, rate-limit, request-size, and
transport errors ... never trigger a switch" (https://code.claude.com/docs/en/model-config). All retrieved 2026-10-20.

## What these files cannot guarantee

The files name the model each agent **requests**. What runs can differ, and no test in this repository can see it:

- `CLAUDE_CODE_SUBAGENT_MODEL_FORCE=1` makes Claude Code ignore "the model field in subagent definitions, and Claude
  can’t pass a model when it starts a subagent" (https://code.claude.com/docs/en/sub-agents).
- An organization's `availableModels` allowlist runs a blocked subagent "on a fallback model rather than failing the
  request" (https://code.claude.com/docs/en/model-config).
- A family alias requested from a session already on that family runs on "the main conversation’s exact model"
  (https://code.claude.com/docs/en/sub-agents), so a `sonnet` request from a Sonnet session uses that Sonnet.
- An alias moves: "Aliases point to the recommended version for your provider and update over time"
  (https://code.claude.com/docs/en/model-config).
- The account answer is what you told `/setup`. Run `/status` to see the account and `/model` to see the models.
- With `ANTHROPIC_API_KEY` set, "Claude Code will use this API key for authentication instead of your Claude
  subscription" (https://support.claude.com/en/articles/11145838-use-claude-code-with-your-pro-or-max-plan), whatever
  account you named. `/setup` checks whether it is set, without printing it.
- The bundled `/pcv` keeps its own agent models, which you approve when it runs; this table does not change them.
- `/pace` lets you raise its agents to a stronger model for one run (its `opus players` option).

To see what an agent ran on: "run /tasks. Claude Code names the model on the subagent’s row"
(https://code.claude.com/docs/en/sub-agents).

## Where Anthropic's pages disagree, or say nothing

- **Opus on Pro.** The pricing page lists Opus for Pro, and Claude Code's default on Pro is Opus 5.5, but the Claude Code
  error reference shows "Claude Opus is not available with the Claude Pro plan" as an example message. Pro is
  sonnet-ceiling either way, so the table does not depend on which is right. Run `/model` to settle it for your account.
- **Default effort for Sonnet 5.5** is medium in Claude Code and high on the API models page. The toolkit sets no effort.
- **Not stated anywhere read:** the absolute usage allowance per session or week, and how much of it one turn on each
  model uses; whether the Opus and Sonnet family limits apply to subagent requests the same way; what a subagent does
  when the account lacks its model and no allowlist applies. The toolkit states no saving figure.

## Appendix: what each alias resolved to on 2026-10-20

From https://code.claude.com/docs/en/model-config (retrieved 2026-10-20):

| Provider | `opus` | `sonnet` | `haiku` |
|---|---|---|---|
| Anthropic API | Opus 5.5 | Sonnet 5.5 | Haiku 5.5 |
| Claude Platform on AWS | Opus 5.5 | Sonnet 4.6 | Haiku 4.5 |
| Amazon Bedrock, Google Cloud's Agent Platform | Opus 5.5 | Sonnet 4.5 | Haiku 4.5 |
| Microsoft Foundry | Opus 4.6 | Sonnet 4.5 | Haiku 4.5 |

Claude API IDs (https://platform.claude.com/docs/en/models/overview): claude-opus-5-5, claude-sonnet-5-5,
claude-haiku-5-5. Amazon Bedrock adds the prefix `anthropic.` (anthropic.claude-sonnet-5-5).

Minimum Claude Code versions: "Sonnet 5.5 requires Claude Code v2.1.284 or later, and Opus 5.5 requires v2.1.280 or
later", and "Use v2.1.293 or later with Haiku 5.5" (https://code.claude.com/docs/en/model-config). The subagent model
order above holds from v2.1.251: "Before v2.1.251, CLAUDE_CODE_SUBAGENT_MODEL came first in this order"
(https://code.claude.com/docs/en/sub-agents).

**Cloud accounts.** On Amazon Bedrock and Google Cloud's Agent Platform, `sonnet` resolves to Sonnet 4.5. Anthropic's
deprecation page lists claude-sonnet-4-5-20250929 as deprecated September 30, 2026 with a tentative retirement date of
November 30, 2026, and claude-haiku-4-5-20251001 as retiring not sooner than October 15, 2026
(https://platform.claude.com/docs/en/about-claude/model-deprecations, retrieved 2026-10-20). That page covers the Claude
API; whether the same dates apply on each cloud provider is not stated there. Check `/model` on your account.

**Fable.** No role requests a Fable model. On Pro and Team Standard seats Fable runs on pay-as-you-go usage credits, and
in a non-interactive run "When a Fable request there would bill to usage credits, Claude Code bills it without asking"
(https://code.claude.com/docs/en/model-config). The gate refuses `fable` as a model value anywhere but this page.
