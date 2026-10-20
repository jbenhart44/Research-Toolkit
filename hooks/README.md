# Hooks — Optional Automation Layer

These hooks extend the toolkit with automated safety, hygiene and measurement. **All hooks are optional** — every command works without them.

## Available Hooks

| Hook | Type | Purpose | Blocking? |
|------|------|---------|-----------|
| `usage_counter.sh` (+ `usage_counter.py`) | PostToolUse (Skill) and UserPromptSubmit | Records one row per command use; `python3 scripts/usage_counts.py` reports the counts | Silent (appends a CSV row; never blocks or prints) |
| `token_budget_guard.sh` | PreToolUse | Warns when session token usage approaches a configurable limit | Soft (ask) |
| `summary_folder_guard.sh` | PostToolUse | Warns when date-prefixed files are written outside configured summary folders | Soft (info) |

`command_evidence.sh`, an empty placeholder since it was added, was removed in v2.0. What it was named for is done by the usage counter (what ran) and `scripts/emit_run_report.sh` (how each run went).

The usage counter is tested: `python3 hooks/usage_counter_selftest.py` checks it, and `python3 hooks/usage_counter_mutations.py` proves the self-test catches nine ways it could miscount or break a session, two of them in the `usage_counter.sh` launcher.

## Installation

### 1. Copy hooks to your Claude Code config

`bash install.sh --hooks` copies every runtime `hooks/*.sh` and `hooks/*.py` file to `~/.claude/hooks/` and marks the scripts executable. The self-tests and mutation checks (`*_selftest.py`, `*_mutations.py`) stay in the clone. By hand:

```bash
mkdir -p ~/.claude/hooks
cp hooks/*.sh hooks/*.py ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

The usage counter needs `python3`.

### 2. Register hooks in `.claude/settings.json`

Add to your project's `.claude/settings.json` (or create one). Register the usage counter on both events, so typed commands and commands Claude runs are both counted:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/usage_counter.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Agent",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/token_budget_guard.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/summary_folder_guard.sh",
            "timeout": 5
          }
        ]
      },
      {
        "matcher": "Skill",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/usage_counter.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### 3. Where the usage log goes

`<evidence_dir>/usage_events.csv`, with `evidence_dir` read from `~/.claude/toolkit-config.md` (set by `/setup`; default `.toolkit/evidence` in the project). Set `USAGE_EVENTS_CSV` to override. Counts:

```bash
python3 scripts/usage_counts.py                 # per-command counts, first and last use
python3 scripts/usage_counts.py --tools coa,pace
```

A typed `/x` that Claude then runs through the Skill tool counts once, not twice. Typed built-ins such as `/clear` are not counted.

### 4. Configure token budget (optional)

Create `~/.claude/token-budget.json`:

```json
{
  "session_limit": 500000
}
```

Default is 500K tokens per session (~1 PACE run + 1 CoA session). Adjust based on your API plan.

---

## Design Principles

- **Soft warnings, not hard blocks.** Hooks inform; you decide.
- **Fast execution (<100ms).** No `jq` dependency.
- **Never break a session.** A hook that fails exits 0 and stays silent rather than interrupting your work.
- **Zero config required.** Sensible defaults work out of the box. Config files are optional overrides.

## Troubleshooting

**Hook not firing?** Check:
- `chmod +x` on the hook script
- Path in `settings.json` matches actual file location
- `timeout` is set (recommended: 5 seconds)

**Hook too noisy?** Increase `session_limit` in `token-budget.json`. Default 500K is conservative.

**Slow filesystem (WSL2, network or cloud-synced folders)?** The token and folder hooks use `/tmp/` for their state to avoid that latency.
