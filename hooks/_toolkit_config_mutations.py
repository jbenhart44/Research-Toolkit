#!/usr/bin/env python3
"""Prove _toolkit_config_selftest.py catches each way the config reader could misread a hook's settings.

    python3 hooks/_toolkit_config_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real module and deleted after its run; the self-test is pointed at it with
TOOLKIT_CONFIG_MODULE. A mutant must still run: it is wrong, not broken.

One mutation is deliberately absent: removing the `if not inner: return []` guard changes nothing observable,
because the CSV reader turns an empty string into an empty row. The guard is there for a reader, not a test.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "_toolkit_config.py").read_text(encoding="utf-8")
SELFTEST = HERE / "_toolkit_config_selftest.py"
MUTANTS = {
    "a trailing comment is kept as part of the value": (
        'v = m.group(1).split("#")[0].strip().strip("\\"\'")', 'v = m.group(1).strip().strip("\\"\'")',
        ["a trailing comment is not part of the value"]),
    "a commented-out key is read": (
        'm = re.search(r"^[ \\t]*" + re.escape(key)', 'm = re.search(r"^[ \\t#]*" + re.escape(key)',
        ["a commented-out key is not read"]),
    "a longer key with the same start is read": (
        'r"[ \\t]*:[ \\t]*(.*)$"', 'r"\\w*[ \\t]*:[ \\t]*(.*)$"',
        ["a longer key with the same start is a different key"]),
    "quotes are kept": (
        'v = m.group(1).split("#")[0].strip().strip("\\"\'")', 'v = m.group(1).split("#")[0].strip()',
        ["quotes around a value are dropped"]),
    "a quoted comma splits an item": (
        "items = next(csv.reader([inner], skipinitialspace=True))", 'items = inner.split(",")',
        ["a quoted list item may hold a comma"]),
    "a bad number gives zero, not the default": (
        "    except ValueError:\n        return default", "    except ValueError:\n        return 0",
        ["a value that is not a whole number gives the default"]),
    "an unreadable file raises inside a hook": (
        "    except OSError:\n        return None", "    except KeyError:\n        return None",
        ["an unreadable config reads as absent and never raises"]),
    "TOOLKIT_CONFIG is ignored": (
        'if os.environ.get("TOOLKIT_CONFIG"):', "if False:",
        ["TOOLKIT_CONFIG overrides the file in HOME"]),
    "a path entry may sit at the end of a longer name": (
        r'''        head, tail = r"(?<![\w.-])", "" if folder else r"(?![\w-])"''',
        r'''        head, tail = "", "" if folder else r"(?![\w-])"''',
        ["path: '.claude' does not match 'rm -rf backup.claude'", "path: 'main.tex' does not match 'cp x domain.tex'",
         "path: 'data/raw' does not match 'rm -rf mydata/raw'"]),
    "a path entry may sit at the start of a longer name": (
        r'''        head, tail = r"(?<![\w.-])", "" if folder else r"(?![\w-])"''',
        r'''        head, tail = r"(?<![\w.-])", ""''',
        ["path: '.claude' does not match 'rm .clauderc'", "path: 'data/raw' does not match 'rm -rf data/rawdata'"]),
    "a folder entry must end where its name ends": (
        '    folder = body.endswith("/")', "    folder = False",
        ["path: 'docs/from-instructor/' matches 'echo x > docs/from-instructor/a.md'",
         "single path: a folder entry matches a file under it"]),
    "single-path mode lets a name run past the next slash boundary": (
        r'''        head, tail = r"(?:^|(?<=/))", "" if folder else r"(?=/|$)"''',
        r'''        head, tail = r"(?<![\w.-])", "" if folder else r"(?![\w-])"''',
        ["single path: an entry with spaces does not match a longer name"]),
    "single-path mode is never used": (
        "        if re.search(path_pattern(entry, single_path), text, re.IGNORECASE):",
        "        if re.search(path_pattern(entry), text, re.IGNORECASE):",
        ["single path: an entry with spaces does not match a longer name"]),
    "a space in a path entry matches only one plain space": (
        '    body = r"(?:\\\\\\s|\\s)+".join(re.escape(tok) for tok in body.split())', "    body = re.escape(body)",
        ["path: 'Shared Team' matches 'rm -rf Shared\\\\ Team/x'","path: 'Shared Team' matches \"rm -rf 'Shared   Team'\""]),
    "a ~/ entry matches only when written as ~/": (
        '        prefixes = [r"~/", r"\\$HOME/", r"\\$\\{HOME\\}/"] + ([re.escape(home + "/")] if home else [])',
        '        prefixes = [r"~/"]',
        ["path: '~/Archive' matches 'rm -rf $HOME/Archive'", "path: '~/Archive' matches 'rm -rf ${HOME}/Archive'"]),
    "a ~/ entry loses its home anchor": (
        '        return r"(?:" + "|".join(prefixes) + r")" + body + tail', "        return head + body + tail",
        ["path: '~/Archive' does not match 'rm -rf ./Archive'"]),
    "paths match case-sensitively": (
        "        if re.search(path_pattern(entry, single_path), text, re.IGNORECASE):",
        "        if re.search(path_pattern(entry, single_path), text):",
        ["path: '.claude' matches 'rm -rf .Claude/x'"]),
    "the last line for a key wins": (
        "    if not m:\n        return None\n    v = m.group(1)",
        "    ms = list(re.finditer(r\"^[ \\t]*\" + re.escape(key) + r\"[ \\t]*:[ \\t]*(.*)$\", text, re.M))\n"
        "    m = ms[-1] if ms else None\n    if not m:\n        return None\n    v = m.group(1)",
        ["the first uncommented line for a key wins"]),
}

base = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_toolkit_config.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(SELFTEST)], capture_output=True, text=True,
                           env=dict(os.environ, TOOLKIT_CONFIG_MODULE=str(mut)))
    finally:
        mut.unlink()
    if "_toolkit_config self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{p.stderr[-400:]}")
        holes.append(name)
        continue
    red = [ln.strip()[5:] for ln in p.stdout.splitlines() if ln.strip().startswith("FAIL ")]
    missing = [m for m in must if not any(r.startswith(m) for r in red)]
    caught = bool(red) and not missing
    print(f"{'CAUGHT' if caught else 'MISSED'}  {name}: {len(red)} red" + (f"; expected red but green: {missing}" if missing else ""))
    if not caught:
        holes.append(name)
print(f"\n{len(MUTANTS) - len(holes)}/{len(MUTANTS)} mutants caught" + (f"; HOLES: {holes}" if holes else " (PROVEN)"))
sys.exit(1 if holes else 0)
