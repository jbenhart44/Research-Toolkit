#!/usr/bin/env python3
"""Self-test for usage_counter.py — the per-tool usage counter hook.

Run:
    python3 hooks/usage_counter_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch.
Each case pipes a hook payload into the hook with USAGE_EVENTS_CSV pointed at a temporary file, then reads
the rows it wrote. Point it at a different hook with USAGE_COUNTER_HOOK=<path> (the mutation proof does).

Why the cases look like this: a counter that undercounts looks exactly like low usage, so every way a call
could be dropped (a quote in the arguments, a typed command, a plugin skill) has a case; and a counter hook
must never break a session, so malformed input and an unwritable log must still exit 0 with nothing on stdout.
"""
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HOOK = Path(os.environ.get("USAGE_COUNTER_HOOK", Path(__file__).resolve().parent / "usage_counter.py"))
LAUNCHER = Path(os.environ.get("USAGE_COUNTER_LAUNCHER", Path(__file__).resolve().parent / "usage_counter.sh"))
FAILS = []


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def fire(payload, csv_path, raw=False):
    data = payload if raw else json.dumps(payload)
    env = dict(os.environ, USAGE_EVENTS_CSV=str(csv_path))
    return subprocess.run([sys.executable, str(HOOK)], input=data, capture_output=True, text=True, env=env, timeout=20)


def rows(csv_path):
    if not Path(csv_path).exists():
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def fresh():
    return Path(tempfile.mkdtemp(prefix="usagecounter_")) / "usage_events.csv"


def post_skill(name, args="", session="s1"):
    return {"hook_event_name": "PostToolUse", "session_id": session, "tool_name": "Skill",
            "tool_input": {"skill": name, "args": args}}


def typed(prompt, session="s1"):
    return {"hook_event_name": "UserPromptSubmit", "session_id": session, "prompt": prompt}


def main():
    p = fresh()
    r = fire(post_skill("pace"), p)
    got = rows(p)
    check("a Skill call writes one row (positive control)", len(got) == 1 and got[0]["name"] == "pace" and got[0]["source"] == "skill")
    check("the row carries the session id and a UTC timestamp", got and got[0]["session_id"] == "s1" and got[0]["ts_utc"].endswith("Z"))
    check("the hook prints nothing (it never injects context)", r.stdout == "" and r.returncode == 0)

    p = fresh()
    fire(post_skill("coa", args='review "the plan" --quick'), p)
    got = rows(p)
    check("quotes inside the arguments do not truncate the name", len(got) == 1 and got[0]["name"] == "coa")

    p = fresh()
    fire(post_skill("dropbox:find-dropbox-content"), p)
    got = rows(p)
    check("a plugin skill name is kept whole", len(got) == 1 and got[0]["name"] == "dropbox:find-dropbox-content")

    p = fresh()
    fire({"hook_event_name": "PostToolUse", "session_id": "s1", "tool_name": "Bash", "tool_input": {"command": "ls"}}, p)
    check("a non-Skill tool call writes nothing", rows(p) == [])

    p = fresh()
    fire(typed("/coa --quick should we ship this now?"), p)
    got = rows(p)
    check("a typed slash command writes one row", len(got) == 1 and got[0]["name"] == "coa" and got[0]["source"] == "typed")

    p = fresh()
    fire(typed("  /quick-ten the questions"), p)
    got = rows(p)
    check("leading whitespace before a typed command is tolerated", len(got) == 1 and got[0]["name"] == "quick-ten")

    p = fresh()
    fire(typed("please run /coa on this"), p)
    check("a slash word mid-sentence is not a command", rows(p) == [])

    p = fresh()
    fire(typed("/opt/project/file.md is the path"), p)
    check("an absolute path is not a command", rows(p) == [])

    p = fresh()
    fire(typed("plain message with no command"), p)
    check("an ordinary prompt writes nothing", rows(p) == [])

    p = fresh()
    fire(post_skill("pace"), p)
    fire(post_skill("audit"), p)
    text = p.read_text(encoding="utf-8") if p.exists() else ""
    check("two calls give two rows under one header", len(rows(p)) == 2 and text.count("ts_utc") == 1)

    p = fresh()
    r = fire("{not json", p, raw=True)
    check("malformed input exits 0, prints nothing, writes nothing", r.returncode == 0 and r.stdout == "" and rows(p) == [])

    blocked = Path(tempfile.mkdtemp(prefix="usagecounter_ro_"))
    target = blocked / "sub" / "usage_events.csv"
    (blocked / "sub").write_text("a file where the directory should be", encoding="utf-8")
    r = fire(post_skill("pace"), target)
    check("an unwritable log never breaks the session (exit 0, nothing on stdout)", r.returncode == 0 and r.stdout == "")

    # Where the log lands without $USAGE_EVENTS_CSV: the config's evidence_dir, else .toolkit/evidence
    def fire_default(payload, home, project):
        env = {k: v for k, v in os.environ.items() if k != "USAGE_EVENTS_CSV"}
        env.update(HOME=str(home), CLAUDE_PROJECT_DIR=str(project))
        return subprocess.run([sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True,
                              text=True, env=env, timeout=20)

    home, proj = Path(tempfile.mkdtemp(prefix="uc_home_")), Path(tempfile.mkdtemp(prefix="uc_proj_"))
    (home / ".claude").mkdir()
    (home / ".claude" / "toolkit-config.md").write_text("## Folder Paths\nevidence_dir: runs/evidence  # mine\n", encoding="utf-8")
    fire_default(post_skill("pace"), home, proj)
    got = rows(proj / "runs" / "evidence" / "usage_events.csv")
    check("without USAGE_EVENTS_CSV the log goes to the config's evidence_dir", len(got) == 1 and got[0]["name"] == "pace")

    home2, proj2 = Path(tempfile.mkdtemp(prefix="uc_home_")), Path(tempfile.mkdtemp(prefix="uc_proj_"))
    fire_default(post_skill("audit"), home2, proj2)
    got = rows(proj2 / ".toolkit" / "evidence" / "usage_events.csv")
    check("with no config the log goes to .toolkit/evidence in the project", len(got) == 1 and got[0]["name"] == "audit")

    # The launcher Claude Code actually runs (usage_counter.sh), not only the Python it starts
    def fire_launcher(payload, csv_path, path_env=None, cwd=None, argv0=None):
        env = dict(os.environ, USAGE_EVENTS_CSV=str(csv_path))
        if path_env is not None:
            env["PATH"] = path_env
        cmd = ["/bin/bash", argv0 or str(LAUNCHER)]
        return subprocess.run(cmd, input=json.dumps(payload), capture_output=True, text=True, env=env, cwd=cwd, timeout=20)

    p = fresh()
    r = fire_launcher(post_skill("pace"), p)
    check("the launcher records a call (positive control)", r.returncode == 0 and len(rows(p)) == 1)
    p = fresh()
    r = fire_launcher(post_skill("pace"), p, cwd=str(LAUNCHER.parent), argv0=LAUNCHER.name)
    check("the launcher works when started from its own folder by bare name", r.returncode == 0 and len(rows(p)) == 1)
    p = fresh()
    no_tools = tempfile.mkdtemp(prefix="usagecounter_nopath_")
    r = fire_launcher(post_skill("pace"), p, path_env=no_tools)
    check("with no python3 on PATH the launcher exits 0 and prints nothing",
          r.returncode == 0 and r.stdout == "" and r.stderr == "")

    print(f"usage_counter self-test: {len(FAILS)} failed" if FAILS else "usage_counter self-test: all passed")
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
