#!/bin/bash
# usage_counter.sh — PostToolUse (Skill) and UserPromptSubmit hook.
#
# Thin launcher. All logic lives in usage_counter.py, which records one row per tool use and never
# blocks or prints. See its docstring for where the log goes. Counts: python3 scripts/usage_counts.py
# Self-test: python3 hooks/usage_counter_selftest.py
#
# It must never break a session, so with no python3 on PATH it exits 0 and prints nothing. It uses no
# external command (not even dirname) before that check, so a bare PATH cannot make it print.

command -v python3 >/dev/null 2>&1 || exit 0
case "$0" in
    */*) here="${0%/*}" ;;
    *) here=. ;;
esac
exec python3 "$here/usage_counter.py"
