#!/bin/bash
# token_budget_guard.sh — PreToolUse (Agent) hook.
#
# Thin launcher. All logic lives in token_budget_guard.py, which keeps an estimated token total per session and
# asks before an Agent call once the total passes session_limit in ~/.claude/token-budget.json.
# Self-test: python3 hooks/token_budget_guard_selftest.py
#
# With no python3 on PATH it exits 0 and prints nothing.

command -v python3 >/dev/null 2>&1 || exit 0
case "$0" in
    */*) here="${0%/*}" ;;
    *) here=. ;;
esac
exec python3 "$here/token_budget_guard.py"
