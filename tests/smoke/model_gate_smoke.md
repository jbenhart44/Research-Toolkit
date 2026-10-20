# Smoke fixture: the models agents actually run on

`tests/check_models.py` proves what the command files **request**. Only a live session shows what **ran**, and only
on your account. Run this by hand after installing, and after any change to `shared/model-roles.json`.

## Setup

1. Run `/status` and note the account. Run `/model` and note whether an Opus model is listed.
2. Run `/setup`, answer the account question, and check that `~/.claude/toolkit-config.md` now has a
   `## Claude Account` block whose `model_chair` follows the rule in `references/model-roles.md`: `opus` only for an
   opus-ceiling account whose `/model` lists Opus, otherwise `sonnet`.
3. Pick a small, reversible question for the council, for example: *"Should this repository's README lead with the
   install steps or with the command list?"*

## Run

1. `/coa --quick <the question>`. Before the Chair starts, the session report header should print
   `requested: seats sonnet | chair <model_chair>`.
2. While the agents run, or right after, run `/tasks`. Each agent's row names the model it ran on.
3. Edit `model_chair` to the other value (`sonnet` ↔ `opus`), run the same `/coa --quick` again, and run `/tasks`.
4. `/pace` on a small task, for example *"Write a one-paragraph summary of tests/README.md"*, then `/tasks`.

## Success

| Agent | Expected model in `/tasks` |
|---|---|
| `/coa` seats and cross-check | Sonnet |
| `/coa` Chair, run 1 | the model `model_chair` named |
| `/coa` Chair, run 2 | the other model |
| `/pace` players, coaches, cross-reviewer | Sonnet |

Record the `/tasks` rows with the date, the Claude Code version (`claude --version`) and the account. These rows are
the observed evidence for the role table; paste them into the release review.

## Failure modes, and what they mean

- **Every agent on the session's model.** `CLAUDE_CODE_SUBAGENT_MODEL_FORCE` may be set, or Claude Code is older than
  v2.1.251, when the model a command passes did not come first.
- **A Sonnet request ran on another Sonnet.** A family alias requested from a session already on that family runs on
  the session's exact model; that is expected.
- **The Chair ran on Sonnet although `model_chair` is `opus`.** Check the run report for `fallback_from: opus`
  (MODEL FAILURE rule 2) and for an Opus limit message; or the account lacks Opus.
- **A seat ran on a model nobody requested.** An organization allowlist (`availableModels`) can run a blocked
  subagent on another model. `/setup` reports whether one is set in the settings files it can read.
