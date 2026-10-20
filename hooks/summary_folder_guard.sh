#!/bin/bash
# summary_folder_guard.sh — PostToolUse (Write) hook.
#
# Thin launcher. All logic lives in summary_folder_guard.py, which adds a note when a dated .md lands outside the
# summary folders named in ~/.claude/toolkit-config.md. Self-test: python3 hooks/summary_folder_guard_selftest.py
#
# With no python3 on PATH it exits 0 and prints nothing.

command -v python3 >/dev/null 2>&1 || exit 0
case "$0" in
    */*) here="${0%/*}" ;;
    *) here=. ;;
esac
exec python3 "$here/summary_folder_guard.py"
