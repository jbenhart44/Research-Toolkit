#!/usr/bin/env python3
"""step_by_step_run.py -- the deterministic core of /step-by-step: build the manifest of
everything a session actually changed, then refuse to call the walkthrough finished
while any item is unexplained.

WHY A SCRIPT AND NOT JUST TALKING
---------------------------------
The failure this exists to prevent is not a bad explanation. It is a walkthrough that
covers seven of nine things while sounding complete, because the list of things came
out of the same memory that is doing the explaining. Nobody can audit an omission they
were never shown.

So the list is derived from git, not recalled, and coverage is tracked against it. The
model explains; the script decides whether the explaining is done.

Commands
--------
  manifest --since <when> [--repo PATH]...   enumerate and number every item
  show [<n>]                                 print one item, or the whole list
  cover <n> [<n>...]                         mark items as explained
  status                                     what is covered, what is left
  verify                                     exit 1 if anything is unexplained
  reset                                      discard the manifest

Exit codes
----------
  0  fine / everything covered
  1  items remain unexplained  <- the refusal that makes this worth having
  2  could not run: no repos, bad date, bad index, no manifest

State: ~/.claude/toolkit/state/step-by-step.json. STEP_BY_STEP_STATE_FILE relocates it.
Resolved on every call and never at import, because a path frozen at import cannot be
overridden.
Self-test: step_by_step_selftest.py beside this file (Part B removes each guard in turn).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

OK, INCOMPLETE, CANTRUN = 0, 1, 2


def state_path() -> Path:
    return Path(os.environ.get(
        "STEP_BY_STEP_STATE_FILE", Path.home() / ".claude" / "toolkit" / "state" / "step-by-step.json"))


def git(repo: Path, *args: str, keep_space: bool = False) -> tuple[int, str]:
    """keep_space matters for `status --porcelain`: its format is two status characters
    then a space then the path, and a modified-not-staged file leads with a SPACE. A
    blanket .strip() ate that space off the first line only, so the first uncommitted
    file in every repository lost the first letter of its path -- 'docs/...' came back as
    'ocs/...'. Found by running the manifest against a real tree."""
    r = subprocess.run(["git", "-C", str(repo), *args],
                       capture_output=True, text=True)
    return r.returncode, (r.stdout if keep_space else r.stdout.strip())


def is_repo(p: Path) -> bool:
    return p.is_dir() and git(p, "rev-parse", "--git-dir")[0] == 0


# `git log --since=<garbage>` exits 0 and quietly ignores the filter, so a typo'd
# window yields a manifest of the WRONG SIZE with no error anywhere. Found by this
# skill's own self-test: the case expected a refusal and got a clean pass. So the
# date is validated here rather than trusted to git.
_UNITS = ("second", "minute", "hour", "day", "week", "month", "year")
_WORDS = ("yesterday", "today", "midnight", "noon", "now")


def valid_since(text: str) -> bool:
    s = (text or "").strip().lower()
    if not s:
        return False
    if s in _WORDS:
        return True
    parts = s.split()
    # "6 hours ago", "2 days ago", and the same without the trailing "ago"
    if len(parts) in (2, 3) and parts[0].isdigit():
        unit = parts[1].rstrip("s")
        if unit in _UNITS and (len(parts) == 2 or parts[2] == "ago"):
            return True
    # ISO-ish: YYYY-MM-DD, optionally with a time
    head = parts[0]
    bits = head.split("-")
    if len(bits) == 3 and all(b.isdigit() for b in bits) and len(bits[0]) == 4:
        if len(parts) == 1:
            return True
        clock = parts[1].split(":")
        return 1 <= len(clock) <= 3 and all(c.isdigit() for c in clock)
    return False


def collect(repo: Path, since: str, paths: list[str] | None = None) -> list[dict]:
    """Commits in the window, plus anything still uncommitted. Both, deliberately:
    a session's work is not only what got committed, and an untracked file is the
    easiest thing in the world to forget you made.

    `paths` narrows to the part of a repository the session touched. A monorepo that
    also holds months of unrelated uncommitted state will otherwise bury the nine
    items that matter under fifty that do not, and a manifest nobody reads to the end
    is the same as no manifest."""
    limit = ["--", *paths] if paths else []
    items: list[dict] = []
    code, out = git(repo, "log", f"--since={since}", "--format=%h\x1f%ad\x1f%s",
                    "--date=format:%Y-%m-%d %H:%M", *limit)
    if code != 0:
        raise RuntimeError(f"git log failed in {repo}: check --since and --path")
    for line in (l for l in out.splitlines() if l.strip()):
        sha, when, subject = line.split("\x1f", 2)
        items.append({"kind": "commit", "repo": repo.name, "ref": sha,
                      "when": when, "what": subject})
    code, out = git(repo, "status", "--porcelain", *limit, keep_space=True)
    if code == 0:
        for line in (l for l in out.splitlines() if l.strip()):
            flag, path = line[:2].strip(), line[3:].strip()
            kind = "untracked" if flag == "??" else "uncommitted"
            items.append({"kind": kind, "repo": repo.name, "ref": flag,
                          "when": "", "what": path})
    return items


def cmd_manifest(a) -> int:
    if not valid_since(a.since):
        print(f"step-by-step: cannot read --since {a.since!r}. git would ignore it silently "
              f"and hand back a manifest of the wrong size.\n"
              f"  use: 2026-09-08, '2026-09-08 20:00', '6 hours ago', yesterday",
              file=sys.stderr)
        return CANTRUN
    repos = [Path(r).expanduser() for r in (a.repo or [Path.cwd()])]
    good = [r for r in repos if is_repo(r)]
    if not good:
        print(f"step-by-step: none of {[str(r) for r in repos]} is a git repository",
              file=sys.stderr)
        return CANTRUN
    items: list[dict] = []
    try:
        for r in good:
            items.extend(collect(r, a.since, a.path))
    except RuntimeError as exc:
        print(f"step-by-step: {exc}", file=sys.stderr)
        return CANTRUN
    if not items:
        # Not a pass. An empty manifest and a wrong --since look identical, and
        # "nothing happened" is the one answer a walkthrough must never invent.
        print(f"step-by-step: nothing found since {a.since!r} in "
              f"{[r.name for r in good]}. Widen the window or name the right repos.",
              file=sys.stderr)
        return CANTRUN
    for i, it in enumerate(items, 1):
        it["n"] = i
        it["covered"] = False
    st = {"since": a.since, "repos": [str(r) for r in good], "items": items}
    p = state_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(st, indent=2))
    print(f"MANIFEST  {len(items)} item(s) since {a.since}  "
          f"across {', '.join(r.name for r in good)}")
    for it in items:
        print(f"  {it['n']:>3}. [{it['kind']:<11}] {it['repo']:<22} {it['what'][:78]}")
    print("\nEvery item above has to be explained before `verify` returns 0.")
    return OK


def load() -> dict | None:
    try:
        return json.loads(state_path().read_text())
    except (OSError, ValueError):
        return None


def need(st) -> int | None:
    if st is None:
        print("step-by-step: no manifest. Run `manifest --since ...` first.",
              file=sys.stderr)
        return CANTRUN
    return None


def cmd_show(a) -> int:
    st = load()
    if (rc := need(st)) is not None:
        return rc
    if a.n is None:
        for it in st["items"]:
            mark = "x" if it["covered"] else " "
            print(f"  [{mark}] {it['n']:>3}. [{it['kind']}] {it['repo']}  {it['what']}")
        return OK
    hit = [i for i in st["items"] if i["n"] == a.n]
    if not hit:
        print(f"step-by-step: no item {a.n}. Manifest has 1..{len(st['items'])}.",
              file=sys.stderr)
        return CANTRUN
    it = hit[0]
    print(f"ITEM {it['n']} of {len(st['items'])}   [{it['kind']}]  {it['repo']}")
    it["when"] and print(f"  when: {it['when']}")
    it["ref"] and print(f"  ref:  {it['ref']}")
    print(f"  what: {it['what']}")
    left = sum(1 for i in st["items"] if not i["covered"])
    print(f"\n{left} item(s) still unexplained, this one included."
          if not it["covered"] else f"\nAlready explained.")
    return OK


def cmd_cover(a) -> int:
    st = load()
    if (rc := need(st)) is not None:
        return rc
    valid = {i["n"] for i in st["items"]}
    bad = [n for n in a.n if n not in valid]
    if bad:
        print(f"step-by-step: no item(s) {bad}. Manifest has 1..{len(st['items'])}.",
              file=sys.stderr)
        return CANTRUN
    for it in st["items"]:
        if it["n"] in a.n:
            it["covered"] = True
    state_path().write_text(json.dumps(st, indent=2))
    left = [i["n"] for i in st["items"] if not i["covered"]]
    print(f"covered {sorted(a.n)}; {len(left)} left"
          + (f": {left}" if left else " -- all explained"))
    return OK


def cmd_status(a) -> int:
    st = load()
    if (rc := need(st)) is not None:
        return rc
    done = [i for i in st["items"] if i["covered"]]
    left = [i for i in st["items"] if not i["covered"]]
    print(f"STATUS  {len(done)}/{len(st['items'])} explained, since {st['since']}")
    for it in left:
        print(f"  LEFT  {it['n']:>3}. [{it['kind']}] {it['repo']}  {it['what'][:70]}")
    return OK if not left else INCOMPLETE


def cmd_verify(a) -> int:
    st = load()
    if (rc := need(st)) is not None:
        return rc
    left = [i for i in st["items"] if not i["covered"]]
    if left:
        print(f"INCOMPLETE: {len(left)} of {len(st['items'])} item(s) were never "
              f"explained:", file=sys.stderr)
        for it in left:
            print(f"  {it['n']:>3}. [{it['kind']}] {it['repo']}  {it['what'][:70]}",
                  file=sys.stderr)
        print("\nDo not tell the user the walkthrough is finished.", file=sys.stderr)
        return INCOMPLETE
    print(f"COMPLETE: all {len(st['items'])} item(s) explained.")
    return OK


def cmd_reset(a) -> int:
    st = load()
    if (rc := need(st)) is not None:
        return rc
    try:
        state_path().unlink()
    except OSError:
        pass
    print("manifest discarded")
    return OK


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="step_by_step_run.py", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("manifest")
    s.add_argument("--since", required=True, help='e.g. "2026-09-08 20:00" or "6 hours ago"')
    s.add_argument("--repo", action="append", help="repeatable; defaults to cwd")
    s.add_argument("--path", action="append",
                   help="repeatable; narrow to these paths inside every repo")
    s.set_defaults(func=cmd_manifest)

    s = sub.add_parser("show")
    s.add_argument("n", nargs="?", type=int)
    s.set_defaults(func=cmd_show)

    s = sub.add_parser("cover")
    s.add_argument("n", nargs="+", type=int)
    s.set_defaults(func=cmd_cover)

    for name, fn in (("status", cmd_status), ("verify", cmd_verify), ("reset", cmd_reset)):
        sub.add_parser(name).set_defaults(func=fn)

    a = p.parse_args(argv)
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())
