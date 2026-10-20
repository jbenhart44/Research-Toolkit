---
allowed-tools: Read, Write, Edit, Glob, Bash(git:*), Bash(ls:*), Bash(python3:*), Bash(claude --version)
description: One-time setup interview — asks about your project and writes ~/.claude/toolkit-config.md, which every other command reads instead of hard-coded paths
---

# /setup — Toolkit Setup Interview

> **When to use**: Once, right after installing the toolkit, and again whenever your project changes shape (a new workstream, a moved folder). Other commands still work without it; they fall back to defaults and ask for a missing value the first time they need it.

You are executing the `/setup` command. Your job is to interview the user briefly and write `~/.claude/toolkit-config.md`, the one file the other commands read for project-specific values (names, workstreams, folders) and for which Claude account you use, which decides the model the `/coa` Chair requests. Nothing in the toolkit hard-codes these values; this file is where they live.

**Goal**: a complete, correct config in under two minutes, with no question the user has already answered.

---

## STEP 0: Read what already exists

1. If `~/.claude/toolkit-config.md` exists, read it. This run **updates** it: show each current value as the default and change only what the user changes. Never discard a key you do not recognise; carry it over unchanged.
2. If it does not exist, start from the template `toolkit-config.md` in the toolkit repository (or the keys in STEP 1).
3. Look before asking. Offer detected values as defaults:
   - `project_name`: the git repository name (`git rev-parse --show-toplevel`), or the current folder name.
   - `author_name`: `git config user.name`.
   - `workstreams`: the top-level folders of the repository that hold work (`ls -d */`, skipping hidden folders, `node_modules`, build output and the summary folders).
   - `summary_folder` / `weekly_folder`: an existing folder whose name contains "summary", if there is one.

## STEP 1: Ask, in at most four short rounds

Ask with the `AskUserQuestion` tool when available (plain questions otherwise). Put the detected value first and mark it `(detected)`, so a user can accept everything in a few clicks.

| Key | Question | Default |
|---|---|---|
| `project_name` | What is this project called? | detected repo name |
| `author_name` | Whose name goes on summaries and headers? | `git config user.name` |
| `workstreams` | Which folders or threads are separate workstreams? (used by `/commit` to stop cross-workstream commits, and by `/startup` and `/weeklysummary` to organise reports) | detected top-level folders |
| `summary_folder` | Where should daily summaries go? | `Daily Summary` |
| `weekly_folder` | Where should weekly summaries go? | `Weekly Summary` |
| `evidence_dir` | Where should run evidence (run logs, per-run reports) go? | `.toolkit/evidence` |
| `project_type` | Research or teaching? (changes how `/startup` frames its briefing) | `research` |
| `claude_account` | Which Claude account does Claude Code use here? (STEP 1b) | `unknown` |

Round 1: project, author, project type, account. Round 2, only when it is needed: the account's tier, and the `/model` question (STEP 1b). Round 3: workstreams. Round 4: the three folders, offered as one "accept the defaults?" question first.

Do not ask for anything else. These optional keys are asked by the command that needs them, the first time it needs them, so `/setup` only mentions that they exist:

| Key | Asked by | Meaning |
|---|---|---|
| `startup_exclude` | `/startup` | workstreams never reported |
| `backlog_file` | `/startup` | backlog whose deferred items it checks (`none` disables) |
| `scheduled_jobs` | `/startup` | `name \| cadence \| log path` entries checked for missed runs |
| `extra_repos` | `/dailysummary` | other repositories this project's sessions commit to |
| `commit_mode` | `/commit` | `ask` (default), `auto` or `review` |
| `shared_code_dirs` | `/simplify` | folders checked for cross-file duplication |
| `author_affiliation` | `/quarto` | affiliation under the author name, and a branded footer |
| `quarto_theme_dir` | `/quarto` | folder holding your branded RevealJS theme |
| `slides_folder` | `/quarto` | where decks go when they belong to no project folder |

A command that needs a value not listed anywhere here asks the user once and offers to add the key to this file itself.

## STEP 1b: The account, and what it sets

Ask: *"Which Claude account does Claude Code use here? Run `/status` if unsure."* With `AskUserQuestion`, which takes at most four options, ask the kind first (**Pro or Max**, **Team or Enterprise**, **API key or Console**, **Cloud provider or gateway**) and then, only for a kind with tiers, the tier: Pro, Max 5x or Max 20x; a Team Standard seat, a Team Premium seat, or Enterprise. "Other" or "not sure" stores `unknown`. Asked as plain text, offer the nine answers below. Tell the user: on an older seat-based Enterprise plan, answer team-standard or team-premium to match the seat; `api` means the Claude Console or an API key; `cloud` means Amazon Bedrock, Google Cloud's Agent Platform, Microsoft Foundry, Claude Platform on AWS or a gateway.

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

**`model_chair`.** For an opus-ceiling answer only, ask one more question: *"Open `/model`. Is an Opus model listed? (yes/no)"* Yes writes `model_chair: opus`; no writes `model_chair: sonnet`. A sonnet-ceiling answer writes `model_chair: sonnet` without asking. Never write a value above the class default; a user who wants more edits the key. The classes are the toolkit's cost policy, not a claim about which models an account can use (`references/model-roles.md`).

**Read-only checks.** Never print the value of a variable or a setting.
1. Run `python3 -c "import os; print([k for k in ('ANTHROPIC_API_KEY', 'CLAUDE_CODE_SUBAGENT_MODEL', 'CLAUDE_CODE_SUBAGENT_MODEL_FORCE') if os.environ.get(k)])"`. It prints the names that are set, never their values.
   - `ANTHROPIC_API_KEY` set: Claude Code then uses that key instead of the subscription, so usage is billed at API rates. Suggest `api` if that is intended.
   - `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` set: every subagent then ignores the model the toolkit requests.
   - `CLAUDE_CODE_SUBAGENT_MODEL` set: it applies only where neither the call nor the agent file names a model, so it does not change the toolkit's agents.
2. Read `~/.claude/settings.json`, `.claude/settings.json` and `.claude/settings.local.json` where they exist, and say whether any sets `availableModels` or `fallbackModel`. An allowlist can run a blocked subagent on another model.
3. Managed settings, set by an organization, cannot be checked from here. Say so; never say "none found".
4. Run `claude --version` and print the minimums beside it: Sonnet 5.5 needs v2.1.284 or later, Opus 5.5 v2.1.280, Haiku 5.5 v2.1.293. From v2.1.251, the model a command passes to a subagent comes first.
5. For `cloud`: on Amazon Bedrock and Google Cloud's Agent Platform, `sonnet` resolves to Sonnet 4.5 and `haiku` to Haiku 4.5; on Claude Platform on AWS, `sonnet` resolves to Sonnet 4.6; on Microsoft Foundry, `opus` resolves to Opus 4.6 and `sonnet` to Sonnet 4.5. Anthropic lists Sonnet 4.5's API model as deprecated on September 30, 2026, with a tentative retirement on November 30, 2026; whether those dates apply on a cloud provider is not stated. Point to the appendix of `references/model-roles.md` and to `/model`.

Anthropic's pages behind each of these facts, with the date they were read, are linked in `references/model-roles.md`.

**PCV.** `/pcv` asks its own plan-tier question and keeps the answer in `~/.claude/pcv-config.json`; `/setup` never writes that file. Print one line, labelled *a suggestion by the nearest published allowance, not a PCV rule*: pro, team-standard or not sure → (a) Pro; max5x or team-premium → (b) Max 5x, which understates a Team Premium seat's 6.25x; max20x → (c) Max 20x; enterprise, api or cloud → (d) API.

## STEP 2: Show the result, then write it

Show the complete file before writing:

```
Here is your config. Say "yes" to save it to ~/.claude/toolkit-config.md, or correct any line.
```

On "yes", write the file in this format (YAML-style `key: value` lines under `##` headings, comments kept), preserving any unknown keys from STEP 0:

```markdown
# Toolkit Configuration
# Written by /setup on <YYYY-MM-DD>. Edit by hand or re-run /setup.

## Project Identity
project_name: <value>
author_name: <value>

## Workstreams
workstreams: [<a>, <b>, <c>]

## Folder Paths
summary_folder: <value>
weekly_folder: <value>
evidence_dir: <value>

## Project Type
project_type: <research|teaching>

## Claude Account
claude_account: <one of the nine answers in STEP 1b>
claude_account_set: <YYYY-MM-DD>
model_chair: <sonnet|opus>
```

Create `summary_folder`, `weekly_folder` and `evidence_dir` inside the project if they do not exist, and say so.

## STEP 3: Confirm

Report in three lines: the file written, the folders created, and the next command to try (`/startup` for an orientation, `/help` for a menu).

## Rules

- Never write the file without the user's "yes" on the shown content.
- Never print the value of an environment variable or a setting; the checks in STEP 1b report names only.
- Never put a secret (API key, token, password) in this file. If the user offers one, say where it belongs instead (an environment variable or the tool's own credential store).
- Paths are written relative to the project root unless the user gives an absolute path on purpose.
