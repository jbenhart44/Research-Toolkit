#!/bin/bash
# protect_files.sh — PreToolUse hook (Edit, Write, MultiEdit, NotebookEdit and Bash).
#
# Thin launcher. All logic lives in protect_files.py, which denies a write to a path listed in protected_files in
# ~/.claude/toolkit-config.md. Self-test: python3 hooks/protect_files_selftest.py
#
# With no python3 on PATH it exits 0 and prints nothing.

command -v python3 >/dev/null 2>&1 || exit 0
case "$0" in
    */*) here="${0%/*}" ;;
    *) here=. ;;
esac
exec python3 "$here/protect_files.py"
