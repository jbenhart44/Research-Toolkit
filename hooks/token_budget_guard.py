#!/usr/bin/env python3
"""token_budget_guard.py — PreToolUse (Agent) hook: a soft warning when a session's agent work gets expensive.

On each Agent call it adds an ESTIMATE of that call's tokens to the session's running total: the prompt's length in
characters divided by 3, and at least 5,000 (a small prompt still produces a substantial agent run). It is an
estimate of input, not a measurement of what the agent used; Claude Code's own usage view is the measurement.

  over 80% of the limit  -> one line of context for Claude, the call proceeds
  over the limit         -> permissionDecision "ask": you decide whether this agent call runs

The limit is `session_limit` in ~/.claude/token-budget.json (default 500000). The running total is kept per session
(by the payload's session_id) in ~/.claude/toolkit/state/token_budget.json, and starts again with each new session.

Why Python. The shell version measured the prompt with `grep -o '"prompt"…"[^"]*"'`, which stops at the first quote
inside the value, so a prompt holding a quotation counted as a few characters.
Never breaks a session: any error exits 0 and prints nothing.
Self-test: python3 hooks/token_budget_guard_selftest.py   Mutations: python3 hooks/token_budget_guard_mutations.py
"""
import json
import os
import sys
from pathlib import Path

DEFAULT_LIMIT = 500000
MIN_CALL = 5000


def home():
    return Path(os.environ.get("HOME", "~")).expanduser()


def session_limit():
    try:
        text = (home() / ".claude" / "token-budget.json").read_text(encoding="utf-8")
        value = json.loads(text).get("session_limit")
        return value if isinstance(value, int) and value > 0 else DEFAULT_LIMIT
    except (OSError, ValueError, AttributeError):
        return DEFAULT_LIMIT


def estimate(prompt):
    return max(len(prompt) // 3, MIN_CALL)


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        if not isinstance(payload, dict) or payload.get("tool_name") != "Agent":
            return 0
        prompt = (payload.get("tool_input") or {}).get("prompt") or ""
        session = str(payload.get("session_id") or "unknown")
        state_path = home() / ".claude" / "toolkit" / "state" / "token_budget.json"
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            state = {}
        total = (state.get("total", 0) if state.get("session_id") == session else 0) + estimate(prompt)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps({"session_id": session, "total": total}), encoding="utf-8")
        limit = session_limit()
        used, cap = total // 1000, limit // 1000
        if total > limit:
            out = {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                   "permissionDecisionReason": f"TOKEN BUDGET: this session's agent calls are estimated at ~{used}K "
                                               f"tokens (limit {cap}K, from ~/.claude/token-budget.json). This "
                                               "Agent call adds more. Consider a fresh session for the next "
                                               "expensive command. Proceed anyway?"}
        elif total > limit * 80 // 100:
            out = {"hookEventName": "PreToolUse",
                   "additionalContext": f"[Token budget: ~{used}K of {cap}K estimated for this session "
                                        f"({total * 100 // limit}%). Consider a session break before the next "
                                        "expensive command.]"}
        else:
            return 0
        print(json.dumps({"hookSpecificOutput": out}))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
