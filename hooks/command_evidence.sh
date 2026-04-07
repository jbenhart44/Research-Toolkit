#!/bin/bash
# command_evidence.sh — PostToolUse hook for Skill invocations
# Appends a structured performance entry after every slash command completes.
#
# What it captures (via orchestrator, not the hook itself):
#   - Which command ran, when
#   - Pros: what worked well
#   - Cons: what caused friction
#   - Disagreements: where multi-agent commands had divergence
#   - Evidence quality: was the run report / CSV generated?
#   - Improvement signal: what would make the next run better
#
# Install: Add to .claude/settings.json under hooks.PostToolUse
# Fires on: Skill tool completions only (skips lightweight commands)
#
# Design:
#   - Hook injects a structured reminder into context
#   - The orchestrator fills in the actual assessment after delivering results
#   - Entries append to evidence/command_performance_log.md (immutable log)
#   - Entries are silent — user doesn't see them unless they ask

# ── Read hook input ────────────────────────────────────────────

INPUT=$(cat)

# Only fire on Skill tool completions
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
fi

if [ "$TOOL_NAME" != "Skill" ]; then
    exit 0
fi

# Extract which skill was invoked
SKILL_NAME=$(echo "$INPUT" | grep -o '"skill"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"skill"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

if [ -z "$SKILL_NAME" ]; then
    exit 0
fi

# Skip lightweight commands that don't need performance tracking
case "$SKILL_NAME" in
    commit|pdftotxt|startup|simplify)
        exit 0
        ;;
esac

# ── Inject evidence reminder ──────────────────────────────────

TIMESTAMP=$(date '+%Y-%m-%d %H:%M')

cat <<HOOKEOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "[COMMAND EVIDENCE — /$SKILL_NAME completed at $TIMESTAMP]\nAfter delivering results to the user, append a performance entry to evidence/command_performance_log.md using this template:\n\n## /$SKILL_NAME — $TIMESTAMP\n- **Task**: [1-line what was asked]\n- **Outcome**: [complete/partial/failed]\n- **Pros**: [what the command did well — 2-3 bullets]\n- **Cons**: [what caused friction or was suboptimal — 2-3 bullets, or 'None']\n- **Disagreements**: [for multi-agent commands: where agents diverged and how it was resolved — or 'N/A' for single-agent]\n- **Evidence quality**: [for /pace /coa /pcv-research: was the run report generated? CSV appended? — or 'N/A']\n- **User satisfaction**: [did the user accept, override, or reject the output?]\n- **Improvement signal**: [1 sentence: what would make the next run better, or 'None — worked as designed']\n\nDo this SILENTLY — do not show the entry to the user unless they ask. Just append it."
  }
}
HOOKEOF
exit 0
