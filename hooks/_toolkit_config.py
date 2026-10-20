#!/usr/bin/env python3
"""_toolkit_config.py — read a key from ~/.claude/toolkit-config.md, for the toolkit's hooks.

The file is `key: value` lines, as /setup writes it. A list is `[a, b, c]`; an item may be quoted to hold a
comma. Everything after the first `#` on a line is a comment, so a key on a commented-out line is never read
(the same rule the usage counter has always used). The first uncommented line for a key wins. Quotes
around a value are dropped.

The usage counter keeps its own copy of this rule, because a counter that cannot import this file would
drop every count; the self-test checks that the two read `evidence_dir` the same way.

File: $TOOLKIT_CONFIG if set, else $HOME/.claude/toolkit-config.md.

    value(key)            -> str or None   None when the file or the key is absent, or the value is empty
    values(key)           -> list[str]     [] when absent; a bare value is a one-item list
    integer(key, default) -> int           default when absent or not a whole number
    path_hit(entries, text) -> str or None the first path entry that text names (see path_pattern), or None

Nothing here raises: a hook that imports it must never break a session, so an unreadable file reads as absent.
Self-test: python3 hooks/_toolkit_config_selftest.py
"""
from __future__ import annotations

import csv
import os
import re
from pathlib import Path


def config_path() -> Path:
    if os.environ.get("TOOLKIT_CONFIG"):
        return Path(os.environ["TOOLKIT_CONFIG"]).expanduser()
    return Path(os.environ.get("HOME", "~")).expanduser() / ".claude" / "toolkit-config.md"


def value(key: str) -> str | None:
    try:
        text = config_path().read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    m = re.search(r"^[ \t]*" + re.escape(key) + r"[ \t]*:[ \t]*(.*)$", text, re.M)
    if not m:
        return None
    v = m.group(1).split("#")[0].strip().strip("\"'")
    return v or None


def values(key: str) -> list[str]:
    v = value(key)
    if v is None:
        return []
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        items = next(csv.reader([inner], skipinitialspace=True))
    else:
        items = [v]
    return [i.strip().strip("\"'") for i in items if i.strip().strip("\"'")]


def integer(key: str, default: int) -> int:
    v = value(key)
    try:
        return int(v) if v is not None else default
    except ValueError:
        return default


def path_pattern(entry: str, single_path: bool = False) -> str:
    """How a hook matches one path entry (from protected_paths or protected_files) in a command or a file path.

    As whole names, so `.claude` never matches `.clauderc` or `backup.claude`, and `main.tex` never matches
    `domain.tex`. An entry ending in `/` is a folder: anything under it matches. A space matches a run of spaces or
    a backslash-escaped space. An entry starting with `~/` also matches `$HOME/`, `${HOME}/` and the home folder's
    full path, and never a relative path of the same name. Callers match it ignoring case.

    In a command (the default) a space also separates arguments, so a name is ended by anything that is not a word
    character or `-`: `rm -rf .claude other` names `.claude`. The cost is that an entry with spaces in it also
    matches a longer name that starts with it (`Daily Summary` in `Daily Summary Archive`), an over-match a guard
    accepts. With single_path=True the text is one path, and a name runs from a `/` (or the start) to the next `/`
    (or the end), so that over-match does not happen.
    """
    anchored = entry.startswith("~/")
    body = entry[2:] if anchored else entry
    folder = body.endswith("/")
    body = r"(?:\\\s|\s)+".join(re.escape(tok) for tok in body.split())
    if single_path:
        head, tail = r"(?:^|(?<=/))", "" if folder else r"(?=/|$)"
    else:
        head, tail = r"(?<![\w.-])", "" if folder else r"(?![\w-])"
    if anchored:
        home = os.environ.get("HOME", "").rstrip("/")
        prefixes = [r"~/", r"\$HOME/", r"\$\{HOME\}/"] + ([re.escape(home + "/")] if home else [])
        return r"(?:" + "|".join(prefixes) + r")" + body + tail
    return head + body + tail


def path_hit(entries, text: str, single_path: bool = False):
    """The first entry that text names (see path_pattern), or None."""
    for entry in entries:
        if re.search(path_pattern(entry, single_path), text, re.IGNORECASE):
            return entry
    return None
