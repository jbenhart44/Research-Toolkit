#!/usr/bin/env python3
"""register_hooks.py — print the settings.json entries that turn on the hooks you name. It never edits a file.

    python3 scripts/register_hooks.py --list                       # every hook, its event and what it does
    python3 scripts/register_hooks.py protect_files usage_counter  # the "hooks" block for those, to paste in
    python3 scripts/register_hooks.py --all

`install.sh --hooks` copies the hooks to ~/.claude/hooks/ and registers none: which guards run in your sessions is
your decision, and a settings file is yours to edit. Paste the printed block into .claude/settings.json (a project)
or ~/.claude/settings.json (every project), merging it with any "hooks" you already have.

Every entry is unconditional: no `if:` condition, because an `if:` pattern matches by prefix and a chained command
(`cd x && cat > notes.txt`) would never reach the hook. The hooks filter inside themselves.

The hook list is install.sh's OPTIONAL_HOOKS, read from the clone this script sits in; a name not in it is refused.
EXIT  0 printed · 2 a name is unknown, or none given
Self-test: python3 scripts/register_hooks.py --self-test   Mutations: python3 scripts/register_hooks_mutations.py
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# hook -> ([(event, matcher or None)], what it does). The order of events is the order they are printed.
REGISTRATION = {
    "usage_counter": ([("UserPromptSubmit", None), ("PostToolUse", "Skill")], "records each command use (silent)"),
    "token_budget_guard": ([("PreToolUse", "Agent")], "asks before an agent call once a session's estimate is high"),
    "summary_folder_guard": ([("PostToolUse", "Write")], "notes a dated summary written outside the summary folders"),
    "protect_files": ([("PreToolUse", "Edit|Write|MultiEdit|NotebookEdit|Bash")], "blocks a write to protected_files"),
}


def optional_hooks(root: Path = ROOT) -> list[str]:
    text = (root / "install.sh").read_text(encoding="utf-8")
    m = re.search(r"^OPTIONAL_HOOKS=\(([^)]*)\)", text, re.M)
    return m.group(1).split() if m else []


def block(names: list[str]) -> dict:
    hooks: dict[str, list] = {}
    for name in names:
        for event, matcher in REGISTRATION[name][0]:
            entry = {"hooks": [{"type": "command", "command": f"~/.claude/hooks/{name}.sh", "timeout": 5}]}
            if matcher:
                entry = {"matcher": matcher, **entry}
            hooks.setdefault(event, []).append(entry)
    return {"hooks": hooks}


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        return self_test()
    shipped = optional_hooks()
    if "--list" in args:
        for name in shipped:
            events, what = REGISTRATION.get(name, ([], "NO REGISTRATION ON RECORD"))
            where = ", ".join(e + (f" ({m})" if m else "") for e, m in events)
            print(f"  {name:<24} {where:<44} {what}")
        return 0
    names = shipped if "--all" in args else [a for a in args if not a.startswith("--")]
    if not names:
        print("usage: python3 scripts/register_hooks.py <hook> [<hook> ...] | --all | --list", file=sys.stderr)
        return 2
    unknown = [n for n in names if n not in shipped or n not in REGISTRATION]
    if unknown:
        print(f"unknown hook(s): {', '.join(unknown)}. Known: {', '.join(shipped)}", file=sys.stderr)
        return 2
    print(json.dumps(block(names), indent=2))
    return 0


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    import contextlib
    import io

    def run(argv):
        """(exit code, stdout, stderr); an exception is recorded as the code, so its case fails and the run goes on."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = main(argv)
            except Exception as e:  # noqa: BLE001
                code = f"raised {type(e).__name__}"
        return code, out.getvalue(), err.getvalue()

    shipped = optional_hooks()
    check("install.sh's OPTIONAL_HOOKS is read", len(shipped) > 0)
    check("every hook install.sh ships has a registration on record", set(shipped) <= set(REGISTRATION))
    check("no registration is on record for a hook install.sh does not ship", set(REGISTRATION) <= set(shipped))
    code, out, _ = run(["protect_files"])
    data = json.loads(out) if code == 0 else {}
    entry = (data.get("hooks", {}).get("PreToolUse") or [{}])[0]
    check("one hook prints a PreToolUse block for it", code == 0 and entry.get("matcher", "").startswith("Edit|")
          and entry["hooks"][0]["command"] == "~/.claude/hooks/protect_files.sh")
    code, out, _ = run(["usage_counter"])
    data = json.loads(out) if code == 0 else {}
    check("a hook on two events prints both", set(data.get("hooks", {})) == {"UserPromptSubmit", "PostToolUse"})
    check("an event with no matcher prints no matcher key", "matcher" not in data["hooks"]["UserPromptSubmit"][0])
    code, out, _ = run(["token_budget_guard", "protect_files"])
    check("hooks on the same event share its list", code == 0 and len(json.loads(out)["hooks"]["PreToolUse"]) == 2)
    code, out, _ = run(["--all"])
    blob = json.loads(out) if code == 0 else {}
    check("--all prints every shipped hook", sorted({h["hooks"][0]["command"].split("/")[-1][:-3]
                                                     for es in blob.get("hooks", {}).values() for h in es}) == sorted(shipped))
    check("no entry carries an if: condition", code == 0 and '"if"' not in out)
    check("protect_files covers all four write tools and Bash",
          all(t in REGISTRATION["protect_files"][0][0][1] for t in ("Edit", "Write", "MultiEdit", "NotebookEdit", "Bash")))
    code, _, err = run(["protect_file"])
    check("an unknown name is refused (exit 2), never printed", code == 2 and "unknown hook" in err)
    check("no names is exit 2", run([])[0] == 2)
    code, out, _ = run(["--list"])
    check("--list names every shipped hook", code == 0 and all(n in out for n in shipped))
    import os
    cwd, home = Path(tempfile.mkdtemp(prefix="reghooks_cwd_")), Path(tempfile.mkdtemp(prefix="reghooks_home_"))
    old_cwd, old_home = os.getcwd(), os.environ.get("HOME")
    os.chdir(cwd)
    os.environ["HOME"] = str(home)
    try:
        code, out, _ = run(["--all"])
    finally:
        os.chdir(old_cwd)
        os.environ["HOME"] = old_home or ""
    check("it writes no file, in the working folder or in HOME", code == 0 and not any(cwd.iterdir())
          and not any(home.iterdir()))
    print(f"register_hooks self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
