#!/bin/bash
# usage_counter.sh — PostToolUse (Skill) and UserPromptSubmit hook.
#
# Thin launcher. All logic lives in usage_counter.py, which records one row per tool use and never
# blocks or prints. See its docstring for where the log goes. Counts: python3 scripts/usage_counts.py
# Self-test: python3 hooks/usage_counter_selftest.py

exec python3 "$(dirname "$0")/usage_counter.py"
