#!/usr/bin/env python3
"""Self-test for _toolkit_config.py — the config reader the toolkit's hooks share.

Run:
    python3 hooks/_toolkit_config_selftest.py

Exit 0 = every case behaved as specified. Exit 1 = at least one mismatch. Each case writes a config file into a
temporary HOME and reads it back. Point it at a different module with TOOLKIT_CONFIG_MODULE=<path> (the mutation
proof does).

Why the cases look like this: a hook that reads its protected list wrongly protects nothing and says nothing, so
every way a line could be misread (a comment, a commented-out key, a longer key with the same start, a quoted
comma) has a case, and an unreadable file must read as absent rather than raise inside a hook.
"""
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODULE = Path(os.environ.get("TOOLKIT_CONFIG_MODULE", HERE / "_toolkit_config.py"))
FAILS = []


def check(label, cond):
    print(f"  {'PASS' if cond else 'FAIL'} {label}")
    if not cond:
        FAILS.append(label)


def load(path):
    spec = importlib.util.spec_from_file_location(f"cfg_{abs(hash(str(path)))}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def home_with(text):
    """A temporary HOME whose ~/.claude/toolkit-config.md holds text (None: no file)."""
    home = Path(tempfile.mkdtemp(prefix="tkcfg_"))
    (home / ".claude").mkdir()
    if text is not None:
        (home / ".claude" / "toolkit-config.md").write_text(text, encoding="utf-8")
    os.environ["HOME"] = str(home)
    os.environ.pop("TOOLKIT_CONFIG", None)
    return home


cfg = load(MODULE)

home_with("backlog_threshold: 40\n")
check("a scalar value is read", cfg.value("backlog_threshold") == "40")
home_with("# backlog_threshold: 5\nbacklog_threshold: 40\n")
check("a commented-out key is not read", cfg.value("backlog_threshold") == "40")
home_with("backlog_threshold: 40   # raise it in a busy repo\n")
check("a trailing comment is not part of the value", cfg.value("backlog_threshold") == "40")
home_with("commit_trailer_policy: block\ncommit_trailer_policy: allow\n")
check("the first uncommented line for a key wins", cfg.value("commit_trailer_policy") == "block")
home_with("backlog_threshold_old: 9\nbacklog_threshold: 40\n")
check("a longer key with the same start is a different key", cfg.value("backlog_threshold") == "40")
home_with('evidence_dir: "My Evidence"\n')
check("quotes around a value are dropped", cfg.value("evidence_dir") == "My Evidence")
home_with("commit_trailer_policy:\n")
check("an empty value reads as absent", cfg.value("commit_trailer_policy") is None)

home_with("protected_paths: [secrets, data/raw, ~/notes]\n")
check("a list gives one item per entry", cfg.values("protected_paths") == ["secrets", "data/raw", "~/notes"])
home_with('protected_paths: ["Smith, J. papers", data]\n')
check("a quoted list item may hold a comma", cfg.values("protected_paths") == ["Smith, J. papers", "data"])
home_with("protected_paths: []\n")
check("an empty list is empty", cfg.values("protected_paths") == [])
home_with("protected_paths: secrets\n")
check("a bare value is a one-item list", cfg.values("protected_paths") == ["secrets"])
home_with("# protected_paths: [secrets]\n")
check("a commented-out list is empty", cfg.values("protected_paths") == [])

home_with("backlog_threshold: lots\n")
check("a value that is not a whole number gives the default", cfg.integer("backlog_threshold", 50) == 50)
home_with("backlog_threshold: 40\n")
check("a whole number is read as one", cfg.integer("backlog_threshold", 50) == 40)

def quietly(fn, *args):
    """fn(*args), or the exception it raised: a reader that raises fails its case instead of ending the run."""
    try:
        return fn(*args)
    except Exception as e:  # noqa: BLE001
        return e


home_with(None)
check("no config file: value is None", quietly(cfg.value, "backlog_threshold") is None)
check("no config file: values is empty", quietly(cfg.values, "protected_paths") == [])
check("no config file: integer is the default", quietly(cfg.integer, "backlog_threshold", 50) == 50)

home = home_with(None)
(home / ".claude" / "toolkit-config.md").mkdir()
check("an unreadable config reads as absent and never raises", quietly(cfg.value, "backlog_threshold") is None)

home_with("backlog_threshold: 40\n")
other = Path(tempfile.mkdtemp(prefix="tkcfg_alt_")) / "alt.md"
other.write_text("backlog_threshold: 7\n", encoding="utf-8")
os.environ["TOOLKIT_CONFIG"] = str(other)
check("TOOLKIT_CONFIG overrides the file in HOME", cfg.value("backlog_threshold") == "7")
os.environ.pop("TOOLKIT_CONFIG")

print("PATH MATCHING")
home = home_with(None)


def hits(entry, text):
    return quietly(cfg.path_hit, [entry], text) == entry


for entry, text in ((".claude", "rm -rf .claude/skills"), (".claude", "rm -rf ~/.claude"),
                    (".claude", "rm -rf /srv/work/.claude"), (".claude", "rm -rf .Claude/x"),
                    ("main.tex", "cp x paper/main.tex"), ("docs/from-instructor/", "echo x > docs/from-instructor/a.md"),
                    ("docs/archive", "rm docs/archive/a.md"), ("Shared Team", "rm -rf 'Shared Team'"),
                    ("Shared Team", "rm -rf Shared\\ Team/x"), ("Shared Team", "rm -rf 'Shared   Team'"),
                    ("~/Archive", "rm -rf ~/Archive/x"), ("~/Archive", "rm -rf $HOME/Archive"),
                    ("~/Archive", "rm -rf ${HOME}/Archive"), ("~/Archive", f"rm -rf {home}/Archive")):
    check(f"path: {entry!r} matches {text!r}", hits(entry, text))
for entry, text in ((".claude", "rm .clauderc"), (".claude", "rm -rf backup.claude"), (".claude", "rm my.claude.md"),
                    ("main.tex", "cp x domain.tex"), ("data/raw", "rm -rf data/rawdata"), ("data/raw", "rm -rf mydata/raw"),
                    ("~/Archive", "rm -rf ./Archive"), ("~/Archive", "rm -rf /elsewhere/Archive")):
    check(f"path: {entry!r} does not match {text!r}", not hits(entry, text))
check("path: no entries, no hit", quietly(cfg.path_hit, [], "rm -rf .claude") is None)
check("path: in a command, an entry followed by another argument still matches",
      hits(".claude", "rm -rf .claude other"))
check("single path: an entry with spaces does not match a longer name",
      quietly(cfg.path_hit, ["Daily Summary"], "/p/Daily Summary Archive/x.md", True) is None)
check("single path: an entry with spaces matches its own folder",
      quietly(cfg.path_hit, ["Daily Summary"], "/p/Daily Summary/x.md", True) == "Daily Summary")
check("single path: a relative entry matches at the start of a relative path",
      quietly(cfg.path_hit, ["paper/main.tex"], "paper/main.tex", True) == "paper/main.tex")
check("single path: a name that only ends like the entry does not match",
      quietly(cfg.path_hit, ["main.tex"], "/p/domain.tex", True) is None)
check("single path: a folder entry matches a file under it",
      quietly(cfg.path_hit, ["docs/from-advisor/"], "/p/docs/from-advisor/a.md", True) == "docs/from-advisor/")
check("path: the first entry that matches is the one named",
      quietly(cfg.path_hit, ["nothing-here", "data/raw", ".claude"], "rm -rf data/raw .claude") == "data/raw")

# Parity: the usage counter keeps its own copy of the comment rule (see the module docstring).
counter = HERE / "usage_counter.py"
if counter.is_file():
    uc = load(counter)
    os.environ.pop("USAGE_EVENTS_CSV", None)
    os.environ["CLAUDE_PROJECT_DIR"] = "/project"
    forms = ["evidence_dir: ev/a\n", 'evidence_dir: "ev b"\n', "evidence_dir: ev/c  # note\n",
             "# evidence_dir: wrong\nevidence_dir: ev/d\n"]
    same = True
    for text in forms:
        home_with(text)
        want = Path("/project") / cfg.value("evidence_dir") / "usage_events.csv"
        same = same and uc.log_path() == want
    check("the usage counter reads evidence_dir exactly as this module does", same)
else:
    check("the usage counter sits beside this module, for the parity case", False)

print(f"\n_toolkit_config self-test: {'all passed' if not FAILS else f'{len(FAILS)} failed'}")
sys.exit(1 if FAILS else 0)
