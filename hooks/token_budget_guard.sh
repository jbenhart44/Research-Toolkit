#!/bin/bash
# token_budget_guard.sh — PreToolUse hook
# Tracks estimated token usage per session and warns when thresholds are exceeded.
# Designed for <100ms execution — uses /tmp text file, not JSON parsing.
#
# Install: Add to .claude/settings.json under hooks.PreToolUse
# Config:  ~/.claude/token-budget.json (optional — defaults are sensible)
#
# How it works:
#   - Fires on every Agent tool invocation (subagent spawns)
#   - Estimates tokens from prompt character count / 3 (conservative for code-heavy prompts)
#   - Tracks cumulative session usage in /tmp/claude_session_tokens
#   - Warns (soft block — user can proceed) when session threshold is exceeded
#   - Resets on new session (new terminal / new day)

# ── Configuration ──────────────────────────────────────────────

# Session token limit (default: 500K tokens — roughly /pace + /coa in one session)
DEFAULT_SESSION_LIMIT=500000

# Per-command estimated costs (tokens) — used when exact prompt size unavailable
declare -A COMMAND_COSTS=(
    ["pace"]=150000
    ["coa"]=100000
)

# Session tracker file — in /tmp for speed, resets on reboot
SESSION_FILE="/tmp/claude_session_tokens"
SESSION_DATE_FILE="/tmp/claude_session_date"

# ── Read hook input ────────────────────────────────────────────

INPUT=$(cat)

# Only fire on Agent tool calls (subagent spawns are the expensive operations)
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
fi

# Only track Agent calls — other tools are cheap
if [ "$TOOL_NAME" != "Agent" ]; then
    exit 0
fi

# ── Session management ─────────────────────────────────────────

TODAY=$(date +%Y-%m-%d)

# Reset session if it's a new day
if [ -f "$SESSION_DATE_FILE" ]; then
    LAST_DATE=$(cat "$SESSION_DATE_FILE")
    if [ "$LAST_DATE" != "$TODAY" ]; then
        echo "0" > "$SESSION_FILE"
        echo "$TODAY" > "$SESSION_DATE_FILE"
    fi
else
    echo "0" > "$SESSION_FILE"
    echo "$TODAY" > "$SESSION_DATE_FILE"
fi

# Read current session total
if [ -f "$SESSION_FILE" ]; then
    CURRENT_TOTAL=$(cat "$SESSION_FILE")
else
    CURRENT_TOTAL=0
fi

# ── Estimate this call's token cost ────────────────────────────

# Extract prompt content length (char/3 for conservative estimate per Gemini recommendation)
PROMPT_CHARS=$(echo "$INPUT" | grep -o '"prompt"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | wc -c)
if [ "$PROMPT_CHARS" -gt 0 ]; then
    EST_TOKENS=$((PROMPT_CHARS / 3))
    # Minimum 5K tokens per agent call (even small prompts generate substantial output)
    if [ "$EST_TOKENS" -lt 5000 ]; then
        EST_TOKENS=5000
    fi
else
    # Fallback: assume a medium agent call
    EST_TOKENS=15000
fi

# ── Update session total ───────────────────────────────────────

NEW_TOTAL=$((CURRENT_TOTAL + EST_TOKENS))
echo "$NEW_TOTAL" > "$SESSION_FILE"

# ── Load user config (optional) ────────────────────────────────

SESSION_LIMIT=$DEFAULT_SESSION_LIMIT

CONFIG_FILE="$HOME/.claude/token-budget.json"
if [ -f "$CONFIG_FILE" ]; then
    # Lightweight parse — no jq dependency, just grep the number
    USER_LIMIT=$(grep -o '"session_limit"[[:space:]]*:[[:space:]]*[0-9]*' "$CONFIG_FILE" | grep -o '[0-9]*$')
    if [ -n "$USER_LIMIT" ] && [ "$USER_LIMIT" -gt 0 ] 2>/dev/null; then
        SESSION_LIMIT=$USER_LIMIT
    fi
fi

# ── Check thresholds ───────────────────────────────────────────

# Warning at 80% of limit
WARNING_THRESHOLD=$((SESSION_LIMIT * 80 / 100))

if [ "$NEW_TOTAL" -gt "$SESSION_LIMIT" ]; then
    # Over limit — soft warning (ask, not deny)
    USED_K=$((NEW_TOTAL / 1000))
    LIMIT_K=$((SESSION_LIMIT / 1000))
    cat <<HOOKEOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "ask",
    "permissionDecisionReason": "TOKEN BUDGET WARNING: This session has used ~${USED_K}K estimated tokens (limit: ${LIMIT_K}K). This Agent call will add more. Consider deferring expensive operations (/pace, /coa) to a fresh session. Proceed anyway?"
  }
}
HOOKEOF
    exit 0
elif [ "$NEW_TOTAL" -gt "$WARNING_THRESHOLD" ]; then
    # Approaching limit — informational warning via additionalContext
    USED_K=$((NEW_TOTAL / 1000))
    LIMIT_K=$((SESSION_LIMIT / 1000))
    cat <<HOOKEOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Token Budget: ~${USED_K}K / ${LIMIT_K}K session limit ($(( NEW_TOTAL * 100 / SESSION_LIMIT ))%). Consider session break before next expensive command.]"
  }
}
HOOKEOF
    exit 0
fi

# Under threshold — allow silently
exit 0
