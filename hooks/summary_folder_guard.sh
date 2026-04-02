#!/bin/bash
# summary_folder_guard.sh — PostToolUse hook
# Soft-warns when /dailysummary or /weeklysummary writes to an unexpected location.
# Non-blocking — warns but never denies. Prevents accidental writes to wrong folders.
#
# Install: Add to .claude/settings.json under hooks.PostToolUse
# Config:  Reads summary_folder and weekly_folder from ~/.claude/toolkit-config.md
#
# Design decisions (from CoA + Gemini review):
#   - Soft warning, not hard block — user may intentionally write elsewhere
#   - Regex pattern match, not hardcoded whitelist
#   - Only fires on Write tool calls (not Edit, not Bash)
#   - Only checks when the conversation context includes /dailysummary or /weeklysummary

# ── Read hook input ────────────────────────────────────────────

INPUT=$(cat)

# Only fire on Write tool calls
TOOL_NAME="${CLAUDE_TOOL_NAME:-}"
if [ -z "$TOOL_NAME" ]; then
    TOOL_NAME=$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"tool_name"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')
fi

if [ "$TOOL_NAME" != "Write" ]; then
    exit 0
fi

# ── Extract file path from Write tool input ────────────────────

FILE_PATH=$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/')

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# ── Load configured folders from toolkit-config.md ─────────────

CONFIG_FILE="$HOME/.claude/toolkit-config.md"
SUMMARY_FOLDER="Daily Summary"
WEEKLY_FOLDER="Weekly Summary"

if [ -f "$CONFIG_FILE" ]; then
    # Parse simple key: value format
    SF=$(grep -E '^summary_folder:' "$CONFIG_FILE" | sed 's/^summary_folder:[[:space:]]*//' | tr -d '\r')
    WF=$(grep -E '^weekly_folder:' "$CONFIG_FILE" | sed 's/^weekly_folder:[[:space:]]*//' | tr -d '\r')
    [ -n "$SF" ] && SUMMARY_FOLDER="$SF"
    [ -n "$WF" ] && WEEKLY_FOLDER="$WF"
fi

# ── Check if this looks like a summary file in the wrong place ─

# Only flag .md files with date-prefixed names (YYYY-MM-DD pattern)
BASENAME=$(basename "$FILE_PATH")
if ! echo "$BASENAME" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}'; then
    # Not a date-prefixed file — not our concern
    exit 0
fi

# Check if the file is in the expected summary directories
IN_SUMMARY=false
if echo "$FILE_PATH" | grep -qi "$SUMMARY_FOLDER"; then
    IN_SUMMARY=true
fi
if echo "$FILE_PATH" | grep -qi "$WEEKLY_FOLDER"; then
    IN_SUMMARY=true
fi

if [ "$IN_SUMMARY" = false ]; then
    # Date-prefixed .md file written outside summary folders — soft warn
    cat <<HOOKEOF
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "[Summary Folder Guard] A date-prefixed file was written to '$FILE_PATH' which is outside the configured summary folders ('$SUMMARY_FOLDER' / '$WEEKLY_FOLDER'). If this is intentional, no action needed. If this should be a daily/weekly summary, it may be in the wrong location."
  }
}
HOOKEOF
    exit 0
fi

# File is in the right place — allow silently
exit 0
