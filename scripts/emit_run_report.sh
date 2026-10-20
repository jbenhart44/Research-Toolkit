#!/bin/bash
# emit_run_report.sh — launcher kept for maintainers working from a clone.
#
# All logic now lives in emit_run_report.py (v2.0.2), which the installer copies to
# ~/.claude/toolkit/scripts/ and which the commands call directly. Same arguments.
# Never breaks the caller: with no python3 on PATH it exits 0 silently.
#
# Self-test: python3 scripts/emit_run_report_selftest.py

command -v python3 >/dev/null 2>&1 || exit 0
case "$0" in
    */*) here="${0%/*}" ;;
    *) here=. ;;
esac
exec python3 "$here/emit_run_report.py" "$@"
