#!/usr/bin/env python3
"""headless_agent.py -- run one subagent's work as a restricted headless Claude Code session.

A fallback for when an Agent-tool subagent stalls (no progress and nothing written): the same prompt, run as
`claude -p` in its own working folder, usually finishes where the subagent did not.

Restricted on purpose, and never with --dangerously-skip-permissions:
  model    sonnet unless --model says haiku or opus. fable and full model IDs are refused: in non-interactive mode
           Claude Code "never asks for consent. When a Fable request there would bill to usage credits, Claude Code
           bills it without asking" (https://code.claude.com/docs/en/model-config, read 2026-10-20).
  tools    Read; Edit on ONE output file in the session's own working folder (an Edit(path) rule also covers Write,
           and a Write(path) rule alone is denied by the file permission check); with --bash, also Bash for python3,
           grep and rg. In print mode anything not allowed is denied.
  reads    its working folder plus every --add-dir

The session writes <workdir>/output.md. Nothing is copied anywhere: you check the output, then save it yourself.

What is not known about the cost. The saved Anthropic pages say bare mode (--bare) does not use your subscription
login (https://code.claude.com/docs/en/headless). They do not state how a `claude -p` run without --bare is metered
against a Pro, Max or Team plan. Treat each run as a session's worth of agent work on the model you name.

Usage:
    python3 scripts/headless_agent.py <prompt-file> <workdir> [--add-dir DIR]... [--bash] [--model sonnet] [--timeout-s 3600]
Exit 0 when output.md exists and is over 500 bytes; 1 when it is not (the reply tail says why); 2 for a refused
model or a missing prompt file.
Self-test (no real Claude call; a stand-in `claude` on PATH): python3 scripts/headless_agent_selftest.py
Mutation proof: scripts/headless_agent_mutations.py
"""
# spawn: role=reasoner model=sonnet
import argparse
import pathlib
import subprocess
import sys
import time

MODELS = ("haiku", "sonnet", "opus")  # aliases only: a full ID pins a model, and fable can bill without asking
MIN_BYTES = 500


def command(prompt: str, model: str, add_dirs: list[str], bash: bool) -> list[str]:
    tools = ["Read", "Edit(/output.md)"] + (["Bash(python3:*)", "Bash(grep:*)", "Bash(rg:*)"] if bash else [])
    cmd = ["claude", "-p", prompt, "--model", model, "--allowedTools", *tools]
    if add_dirs:
        cmd += ["--add-dir", *add_dirs]
    return cmd + ["--output-format", "text"]


def run(prompt_file: str, workdir: str, model: str = "sonnet", add_dirs=(), bash: bool = False,
        timeout_s: int = 3600) -> int:
    if model not in MODELS:
        print(f"refused: --model {model!r}. Use one of {', '.join(MODELS)}. A fable run can bill usage credits without "
              "asking in -p mode, and a full model ID pins a model the account may not have.", file=sys.stderr)
        return 2
    pf = pathlib.Path(prompt_file)
    if not pf.is_file():
        print(f"no prompt file at {pf}", file=sys.stderr)
        return 2
    work = pathlib.Path(workdir)
    work.mkdir(parents=True, exist_ok=True)
    prompt = pf.read_text(encoding="utf-8")
    prompt += ("\n\nWrite your complete result to ./output.md in your current working folder (that exact file, "
               "nowhere else), then reply with one line: 'Wrote output.md, N bytes'.")
    t0 = time.time()
    r = subprocess.run(command(prompt, model, list(add_dirs), bash), cwd=str(work), capture_output=True, text=True,
                       timeout=timeout_s)
    out = work / "output.md"
    size = out.stat().st_size if out.exists() else 0
    print(f"exit {r.returncode}, {time.time() - t0:.0f} s, output {size if out.exists() else 'ABSENT'} bytes ({out})")
    print("--- reply tail ---\n" + "\n".join((r.stdout or "").strip().splitlines()[-5:]))
    if r.stderr.strip():
        print("--- stderr tail ---\n" + "\n".join(r.stderr.strip().splitlines()[-5:]))
    return 0 if size > MIN_BYTES else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_file")
    ap.add_argument("workdir")
    ap.add_argument("--add-dir", action="append", default=[])
    ap.add_argument("--bash", action="store_true")
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--timeout-s", type=int, default=3600)
    a = ap.parse_args()
    return run(a.prompt_file, a.workdir, a.model, a.add_dir, a.bash, a.timeout_s)


if __name__ == "__main__":
    sys.exit(main())
