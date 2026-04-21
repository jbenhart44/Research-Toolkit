# Hooks — Optional Automation Layer

These hooks extend the toolkit with automated safety and hygiene checks. **All hooks are optional** — the 11 core commands work without them.

## Available Hooks

| Hook | Type | Purpose | Blocking? |
|------|------|---------|-----------|
| `token_budget_guard.sh` | PreToolUse | Warns when session token usage approaches a configurable limit | Soft (ask) |
| `summary_folder_guard.sh` | PostToolUse | Warns when date-prefixed files are written outside configured summary folders | Soft (info) |
| `command_evidence.sh` | PostToolUse | Auto-logs pros/cons/disagreements after each command run | Silent (appends log) |

## Installation

### 1. Copy hooks to your Claude Code config

```bash
mkdir -p ~/.claude/hooks
cp hooks/token_budget_guard.sh ~/.claude/hooks/
cp hooks/summary_folder_guard.sh ~/.claude/hooks/
cp hooks/command_evidence.sh ~/.claude/hooks/
chmod +x ~/.claude/hooks/*.sh
```

### 2. Register hooks in `.claude/settings.json`

Add to your project's `.claude/settings.json` (or create one):

```json
{
  "hooks": {
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
            "command": "~/.claude/hooks/command_evidence.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### 3. Configure token budget (optional)

Create `~/.claude/token-budget.json`:

```json
{
  "session_limit": 500000
}
```

Default is 500K tokens per session (~1 PACE run + 1 CoA session). Adjust based on your API plan.

### 4. Create the command performance log (for command_evidence.sh)

Create `evidence/command_performance_log.md` in your project root:

```markdown
# Command Performance Log

Append one entry per command invocation. Each entry captures what the command produced,
where it succeeded, where it failed, and any disagreements surfaced.

**Format**: Append entries chronologically. Do NOT edit previous entries — they are immutable records.

---

<!-- APPEND NEW ENTRIES BELOW THIS LINE -->
```

The hook will remind the orchestrator to append entries after each `/pace`, `/coa`, `/improve`, `/dailysummary`, `/weeklysummary`, and `/quarto` run. Lightweight commands (`/commit`, `/readable`, `/startup`, `/simplify`) are skipped.

Each entry captures:
- **Pros**: What the command did well
- **Cons**: What caused friction or was suboptimal
- **Disagreements**: Where multi-agent commands had divergence (and how it was resolved)
- **Evidence quality**: Whether run reports and CSV rows were generated
- **Improvement signal**: What would make the next run better

Review the log periodically with `/improve --tools` or manually to spot patterns.

---

## Design Principles

- **Soft warnings, not hard blocks.** Hooks inform; you decide.
- **Fast execution (<100ms).** Uses `/tmp/` text files for state, not JSON parsing. No `jq` dependency.
- **Session-aware.** Token counter resets daily. No persistent state beyond `/tmp/`.
- **Zero config required.** Sensible defaults work out of the box. Config files are optional overrides.

## Troubleshooting

**Hook not firing?** Check:
- `chmod +x` on the hook script
- Path in `settings.json` matches actual file location
- `timeout` is set (recommended: 5 seconds)

**Hook too noisy?** Increase `session_limit` in `token-budget.json`. Default 500K is conservative.

**WSL2 latency?** The hooks use `/tmp/` for all read/write operations to avoid OneDrive filesystem latency. If you still see >100ms execution, check `free -h` for memory pressure.
