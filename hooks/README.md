# Hooks — Optional Automation Layer

These hooks add measurement, warnings and one guard. **All are optional**: every command works without them, and the
installer copies them without turning any of them on.

## Available hooks

Each hook is a `.sh` launcher (the shell only starts Python) and a `.py` that decides, parsing the payload as real
JSON. Each has a `<hook>_selftest.py` and a `<hook>_mutations.py` beside it, and states in its docstring what it
cannot see.

| Hook | Event (matcher) | What it does | Posture | Reads from your config |
|---|---|---|---|---|
| `usage_counter` | UserPromptSubmit; PostToolUse (Skill) | records one row per command use; `python3 scripts/usage_counts.py` reports the counts | silent | `evidence_dir` |
| `token_budget_guard` | PreToolUse (Agent) | keeps an estimated token total per session and asks before an agent call once it passes your limit | asks | `~/.claude/token-budget.json`: `session_limit` |
| `summary_folder_guard` | PostToolUse (Write) | notes a dated `.md` written outside your summary folders | notes | `summary_folder`, `weekly_folder` |
| `protect_files` | PreToolUse (Edit\|Write\|MultiEdit\|NotebookEdit\|Bash) | blocks a write to a protected file or folder; reading stays allowed | blocks, if set | `protected_files: [...]` |

`_toolkit_config.py` is not a hook: it is the reader the hooks share for `~/.claude/toolkit-config.md`, with its own
self-test and mutation check. It decides how a path entry matches: as whole names, ignoring case, with `~/` for your
home folder and a trailing `/` for a folder and everything under it.

**`protect_files` holds no list of its own.** With no config it allows everything. Turn it on by naming what it
protects:

```
## Hooks (in ~/.claude/toolkit-config.md)
protected_files: [paper/main.tex, docs/from-advisor/]
```

## Installation

### 1. Copy them

`bash install.sh --hooks` copies every hook in `OPTIONAL_HOOKS` (both files) and `_toolkit_config.py` to
`~/.claude/hooks/`. Self-tests and mutation checks stay in the clone. The hooks need `python3`; with none on `PATH`
each launcher exits 0 and prints nothing.

### 2. Register the ones you want

The installer **never edits a settings file**. Print the entries and paste them yourself:

```bash
python3 scripts/register_hooks.py --list                       # every hook, its event and what it does
python3 scripts/register_hooks.py protect_files usage_counter  # the "hooks" block for those
python3 scripts/register_hooks.py --all
```

Paste the block into `.claude/settings.json` (one project) or `~/.claude/settings.json` (every project), merging it
with any `"hooks"` you already have. Every entry is **unconditional**: no `if:` condition. An `if:` pattern matches by
prefix, so a chained command (`cd paper && cat > main.tex`) would never reach a guard behind `if: Bash(cat *)`. The
hooks filter inside themselves.

### 3. Test one live call

A hook added in the middle of a session has been seen both to fire at once and not to fire until the next session.
Before you rely on `protect_files`, make one write it should refuse (to a scratch file you listed) and see the
refusal.

### Where the usage log goes

`<evidence_dir>/usage_events.csv`, with `evidence_dir` read from `~/.claude/toolkit-config.md` (set by `/setup`;
default `.toolkit/evidence` in the project). Set `USAGE_EVENTS_CSV` to override. A typed `/x` that Claude then runs
through the Skill tool counts once, not twice. Typed built-ins such as `/clear` are not counted.

```bash
python3 scripts/usage_counts.py                 # per-command counts, first and last use
python3 scripts/usage_counts.py --tools coa,pace
```

---

## What the hooks cannot see

- **Anything inside a script they do not open.** `bash build.sh` is one command to them; what the script writes is
  not.
- **A path built at run time.** `cp x "$TARGET"` names no protected path in its text.
- **Other tools.** `protect_files` reads the Bash tool's `command`. On Windows, Claude Code's PowerShell tool also runs
  shell commands, and the hook is not registered for it.
- **Prose that only quotes a command.** The guard tests command text, so a commit message or a heredoc that merely
  quotes a write to a protected file is refused. The refusal names the way round it (the Write tool, splitting the
  call, or `git commit -F <file>`).

## Design principles

- **Copied, never registered.** Which guards run in your sessions is your decision.
- **No list ships inside a guard.** A guard that blocks reads what it protects from your config, so it protects your
  files and nobody else's.
- **Never break a session.** A hook that cannot parse its payload, or fails in any way, exits 0 and stays silent; a
  guard whose audit log cannot be written still blocks.
- **Bash launches, Python decides.** A shell parser that read the payload with `grep -o` stopped at the first quote
  inside the JSON value, which is how real hooks have let through the very commands they existed to stop.
- **Every guard has been made to fail.** Each `<hook>_mutations.py` plants the defects its hook could have and
  requires the self-test to catch every one.

## Troubleshooting

**Hook not firing?** Check the launcher is executable (`chmod +x ~/.claude/hooks/*.sh`), the path in `settings.json`
matches the file, the entry has no `if:` condition, and `timeout` is set (5 seconds is plenty).

**Token warning too early?** Raise `session_limit` in `~/.claude/token-budget.json` (default 500000). The figure is
an estimate of agent prompts, not a measurement of usage.

**State files.** `token_budget_guard` keeps a small state file in `~/.claude/toolkit/state/`. Deleting it resets the
session total.
