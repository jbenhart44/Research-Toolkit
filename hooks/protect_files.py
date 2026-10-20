#!/usr/bin/env python3
"""protect_files.py — PreToolUse hook: a write lock over the files and folders you name.

It denies an Edit, Write, MultiEdit or NotebookEdit whose target is protected, and a Bash command that WRITES and
names a protected path. A Bash command that only reads (`cat`, `grep`, `sed -n`, `git log`) passes, because a
write lock that blocks reading gets removed.

Your list, from ~/.claude/toolkit-config.md:

    protected_files: [paper/main.tex, docs/from-advisor/, ~/Archive/thesis.pdf]

No list, or an empty one, protects nothing: the hook ships with no files of its own. How an entry matches is
_toolkit_config.path_pattern: whole path components ignoring case, a trailing `/` for a folder and everything under
it, and `~/` for your home folder.

What counts as a Bash write: cp, mv, rm, rmdir, touch, mkdir, tee, dd, install, truncate, ln, chmod, chown, rsync,
patch, sponge; a redirect into a file (`>` or `>>`, but not `2>&1` or `>&2`, which only point one descriptor at
another); `sed -i` and `perl -i`; `git rm`, `git mv`, `git checkout`, `git restore`, `git apply`, `git am`; and
Python's `write_text(`, `write_bytes(` or `open(…, "w")`. `git add` and `git commit` do not count: they change no
file's bytes.

Why it parses JSON. A shell version extracted the command with `grep -o '"command"…"[^"]*"'`, which stops at the
first quote inside the value, so a protected name inside a quoted `python3 -c "…"` never reached the matcher.
Register it with no `if:` condition: an `if:` pattern matches by prefix, and `sed -i … main.tex` or `> main.tex`
would never reach the hook.

The known false positive: a Bash command that writes one file while only NAMING a protected one (a heredoc or an
echo into notes.md that mentions main.tex) is denied. Write the other file with the Write tool, whose target is
read from file_path and never from content. What it cannot see: a write inside a script it does not open
(`bash build.sh`), a path built at run time (`cp x "$OUT"`), and any tool other than these five; on Windows, the
PowerShell tool runs shell commands too and is not checked.
Each denial is logged, after the refusal is printed, to <evidence_dir>/protect_files_audit.log in the project.
Never breaks a session: a payload it cannot parse is allowed silently, and a log it cannot write is skipped.
Self-test: python3 hooks/protect_files_selftest.py   Mutations: python3 hooks/protect_files_mutations.py
"""
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    import _toolkit_config as config  # noqa: E402
except ImportError:  # copied without its config reader: no list can be read, so nothing is protected
    class config:  # noqa: N801
        value = staticmethod(lambda key: None)
        values = staticmethod(lambda key: [])
        path_hit = staticmethod(lambda entries, text: None)

WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")

# Broad and not clever: no shell quoting is parsed, because parsing quotes inside a guard is how its ancestor's
# hole was made. A false positive costs one call through the Write tool.
BASH_WRITE = re.compile(
    r"(?:^|[\s;&|(`])(?:cp|mv|rm|rmdir|touch|mkdir|tee|dd|install|truncate|ln|chmod|chown|rsync|patch|sponge)"
    r"(?=\s|$)"
    r"|>>?\s*(?![&|\s])[^|\s]"  # into a file; `>&` duplicates a descriptor and writes nothing
    r"|\bsed\b[^|;]*(?:^|\s)-i(?:\s|$|'|\")"  # the flag must stand alone, or `from-instructor` reads as -i
    r"|\bperl\b[^|;]*(?:^|\s)-i(?:\s|$|'|\")"
    r"|\bgit\b[^|;]*\b(?:rm|mv|checkout|restore|apply|am)\b"
    r"|\.write_text\(|\.write_bytes\(|\bopen\([^)]*['\"][wax]",
    re.IGNORECASE,
)


def target(payload):
    """(tool, text to match), or (tool, None) when this call is not one the lock judges."""
    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    if tool in WRITE_TOOLS:
        # NotebookEdit names its file notebook_path; reading only file_path let every notebook edit through.
        return tool, tool_input.get("file_path") or tool_input.get("notebook_path") or None
    if tool == "Bash":
        command = tool_input.get("command") or ""
        return tool, command if BASH_WRITE.search(command) else None
    return tool, None


def log_block(entry: str, text: str) -> None:
    try:
        root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd())
        ev = Path(config.value("evidence_dir") or ".toolkit/evidence").expanduser()
        log = (ev if ev.is_absolute() else root / ev) / "protect_files_audit.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        with open(log, "a", encoding="utf-8") as f:
            f.write(f"[{stamp}] BLOCKED write naming protected file {entry!r}: {text}\n")
    except OSError:
        pass  # a log that cannot be written never undoes the block


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        return 0  # cannot parse, cannot judge: a malformed payload is a harness problem, not an edit
    if not isinstance(payload, dict):
        return 0
    tool, text = target(payload)
    if not text:
        return 0
    # A write tool's target is one path; a Bash command is text whose arguments are separated by spaces.
    entry = config.path_hit(config.values("protected_files"), text, single_path=tool != "Bash")
    if entry is None:
        return 0
    reason = (f"BLOCKED: {entry!r} is listed in protected_files in ~/.claude/toolkit-config.md, so it is not written "
              "without the user's say-so. Reading it is still allowed. If the change is intended, ask the user to "
              "make it, or to remove the entry.")
    if tool == "Bash":
        reason += (" If this command writes some OTHER file and only names this one (a heredoc or an echo into "
                   "notes), write that file with the Write tool instead; do not disguise the path.")
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }}))
    sys.stdout.flush()  # the decision is out before the log is touched
    log_block(entry, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
