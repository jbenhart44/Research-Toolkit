#!/usr/bin/env python3
"""Per-command usage counts from the usage counter, optionally backfilled from an older command log.

The hook hooks/usage_counter.py writes one row per command use to <evidence_dir>/usage_events.csv
(evidence_dir from ~/.claude/toolkit-config.md, default .toolkit/evidence). This script turns those
rows into counts.

COUNTING RULES
--------------
  - One use = one Skill call or one typed /command.
  - A typed /x and a Skill call for x in the same session within MERGE_SECONDS are ONE use (the user
    typed it, then the assistant ran it).
  - A typed name that is not a known tool (/clear, /effort, /goal ...) is dropped and reported, never
    counted. Known = a .claude/skills/<name>/ directory, a .claude/commands/<name>.md file, or any name
    seen through the Skill tool (which only runs real skills).
  - Backfill (optional, --backfill FILE): headings `## /name — YYYY-MM-DD` in an older command log
    count as uses ONLY for dates before the counter's first row, so no day is counted twice. Such a
    log may have skipped some commands, so backfilled counts are a floor, and the report says so.

Balance check printed on every run: live + backfilled = total, per row and overall.

Usage:
    python3 scripts/usage_counts.py [--events FILE] [--backfill FILE] [--tools a,b] [--json OUT]
    python3 scripts/usage_counts.py --self-test
Mutation proof: scripts/usage_counts_mutations.py
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime
from pathlib import Path

MERGE_SECONDS = 600
HEADING = re.compile(r"^## /([A-Za-z][A-Za-z0-9_.:-]*)\s+[—-]+\s+(\d{4}-\d{2}-\d{2})", re.M)
EVIDENCE_KEY = re.compile(r"^\s*evidence_dir:\s*(.+?)\s*$", re.M)


def default_events(project: Path) -> Path:
    """Same rule as hooks/usage_counter.py: evidence_dir from the config, else .toolkit/evidence."""
    cfg = Path.home() / ".claude" / "toolkit-config.md"
    evidence = ".toolkit/evidence"
    if cfg.exists():
        m = EVIDENCE_KEY.search(cfg.read_text(encoding="utf-8", errors="replace"))
        if m:
            evidence = m.group(1).split("#")[0].strip().strip("\"'") or evidence
    ev = Path(evidence).expanduser()
    return (ev if ev.is_absolute() else project / ev) / "usage_events.csv"


def known_names(project: Path) -> set[str]:
    """Commands and skills installed for this user or this project."""
    names = set()
    for base in (Path.home() / ".claude", project / ".claude"):
        names |= {p.name for p in (base / "skills").glob("*/") if (p / "SKILL.md").exists()}
        names |= {p.stem for p in (base / "commands").glob("*.md")}
    return names


def load_events(path: Path) -> tuple[list[dict], int]:
    """Rows with a parsed timestamp, and the count of rows that could not be parsed."""
    if not path.exists():
        return [], 0
    good, bad = [], 0
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                r["ts"] = datetime.strptime(r["ts_utc"], "%Y-%m-%dT%H:%M:%SZ")
                if not r["name"] or r["source"] not in ("skill", "typed"):
                    raise ValueError
                good.append(r)
            except (KeyError, ValueError, TypeError):
                bad += 1
    return good, bad


def merge_uses(events: list[dict], known: set[str]) -> tuple[list[dict], dict]:
    """One record per use. Returns (uses, dropped-unknown-typed counts)."""
    known = known | {e["name"] for e in events if e["source"] == "skill"}
    dropped = defaultdict(int)
    skills = defaultdict(list)
    for e in events:
        if e["source"] == "skill":
            skills[(e["session_id"], e["name"])].append(e)
    used = set()
    uses = [e for e in events if e["source"] == "skill"]
    for e in events:
        if e["source"] != "typed":
            continue
        if e["name"] not in known:
            dropped[e["name"]] += 1
            continue
        partner = next((s for s in skills[(e["session_id"], e["name"])]
                        if id(s) not in used and abs((s["ts"] - e["ts"]).total_seconds()) <= MERGE_SECONDS), None)
        if partner is not None:
            used.add(id(partner))
            continue
        uses.append(e)
    return uses, dict(dropped)


def backfill(perf_log: Path, cutover: str | None) -> list[tuple[str, str]]:
    if not perf_log.exists():
        return []
    text = perf_log.read_text(encoding="utf-8", errors="replace")
    return [(n, d) for n, d in HEADING.findall(text) if cutover is None or d < cutover]


def count(events_path: Path, perf_log: Path, known: set[str], tools: set[str] | None = None) -> dict:
    events, bad = load_events(events_path)
    uses, dropped = merge_uses(events, known)
    cutover = min((e["ts"].strftime("%Y-%m-%d") for e in events), default=None)
    rows = defaultdict(lambda: {"live": 0, "backfilled": 0, "first": None, "last": None})
    for u in uses:
        r = rows[u["name"]]
        r["live"] += 1
        d = u["ts"].strftime("%Y-%m-%d")
        r["first"] = min(filter(None, [r["first"], d]))
        r["last"] = max(filter(None, [r["last"], d]))
    for name, d in backfill(perf_log, cutover):
        r = rows[name]
        r["backfilled"] += 1
        r["first"] = min(filter(None, [r["first"], d]))
        r["last"] = max(filter(None, [r["last"], d]))
    if tools:
        rows = {k: v for k, v in rows.items() if k in tools}
    for v in rows.values():
        v["total"] = v["live"] + v["backfilled"]
    return {"rows": dict(rows), "cutover": cutover, "unparsed_rows": bad, "dropped_unknown_typed": dropped}


# ---------------------------------------------------------------------------------------------- self-test

def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def run(events, log="", known=("pace", "coa", "audit", "pcv-research"), tools=None):
        d = Path(tempfile.mkdtemp(prefix="usagecounts_"))
        ev, pl = d / "usage_events.csv", d / "perf.md"
        with open(ev, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ts_utc", "session_id", "source", "name"])
            w.writerows(events)
        pl.write_text(log, encoding="utf-8")
        return count(ev, pl, set(known), tools)

    t = "2026-10-19T12:00:00Z"
    res = run([[t, "s1", "skill", "pace"], ["2026-10-19T13:00:00Z", "s1", "skill", "pace"]])
    check("two Skill calls count 2 (positive control)", res["rows"]["pace"]["live"] == 2)

    res = run([[t, "s1", "typed", "coa"], ["2026-10-19T12:02:00Z", "s1", "skill", "coa"]])
    check("typed then run in the same session within 10 min counts once", res["rows"]["coa"]["live"] == 1)

    res = run([[t, "s1", "typed", "coa"], ["2026-10-19T14:00:00Z", "s1", "skill", "coa"]])
    check("the same pair two hours apart counts twice", res["rows"]["coa"]["live"] == 2)

    res = run([[t, "s1", "typed", "coa"], ["2026-10-19T12:02:00Z", "s2", "skill", "coa"]])
    check("the same pair in different sessions counts twice", res["rows"]["coa"]["live"] == 2)

    res = run([[t, "s1", "typed", "coa"], [t, "s1", "typed", "coa"], ["2026-10-19T12:01:00Z", "s1", "skill", "coa"]])
    check("one Skill call absorbs only one typed row", res["rows"]["coa"]["live"] == 2)

    log = "## /pace — 2026-10-01\n## /pace — 2026-10-18\n## /pace — 2026-10-19\n## /audit — 2026-10-20\n"
    res = run([[t, "s1", "skill", "pace"]], log=log)
    check("backfill counts only days before the counter's first row", res["rows"]["pace"]["backfilled"] == 2 and "audit" not in res["rows"])

    res = run([], log=log)
    check("with no counter rows, all backfill counts", res["rows"]["pace"]["backfilled"] == 3 and res["rows"]["audit"]["backfilled"] == 1)

    res = run([[t, "s1", "typed", "clear"], [t, "s1", "typed", "pace"]])
    check("an unknown typed name is dropped and reported", "clear" not in res["rows"] and res["dropped_unknown_typed"].get("clear") == 1)
    check("a known typed name with no Skill partner counts", res["rows"]["pace"]["live"] == 1)

    res = run([[t, "s1", "skill", "brand-new-skill"]])
    check("a name seen through the Skill tool counts even if not in the known dirs", res["rows"]["brand-new-skill"]["live"] == 1)

    res = run([[t, "s1", "skill", "pace"], [t, "s1", "skill", "coa"]], tools={"pace"})
    check("--tools limits the rows", set(res["rows"]) == {"pace"})

    res = run([[t, "s1", "skill", "pace"], ["not-a-time", "s1", "skill", "pace"], [t, "s1", "bogus", "pace"]])
    check("malformed rows are skipped and counted, never crash", res["unparsed_rows"] == 2 and res["rows"]["pace"]["live"] == 1)

    res = run([[t, "s1", "skill", "pace"]], log="## /pace — 2026-10-01\n")
    r = res["rows"]["pace"]
    check("balance: live + backfilled = total", r["total"] == r["live"] + r["backfilled"] == 2)
    check("first and last dates span backfill and live", r["first"] == "2026-10-01" and r["last"] == "2026-10-19")

    print(f"usage_counts self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--events", help="the counter's CSV (default: <evidence_dir>/usage_events.csv)")
    ap.add_argument("--backfill", help="an older command log with '## /name — YYYY-MM-DD' headings")
    ap.add_argument("--tools", help="comma-separated names to report")
    ap.add_argument("--json", dest="json_out")
    a = ap.parse_args()
    tools = set(a.tools.split(",")) if a.tools else None
    project = Path.cwd()
    events = Path(a.events) if a.events else default_events(project)
    backfill_log = Path(a.backfill) if a.backfill else Path("/nonexistent-backfill")
    res = count(events, backfill_log, known_names(project), tools)
    rows = sorted(res["rows"].items(), key=lambda kv: -kv[1]["total"])
    print(f"{'tool':<28} {'live':>6} {'backfill':>9} {'total':>7}  first       last")
    for name, r in rows:
        print(f"{name:<28} {r['live']:>6} {r['backfilled']:>9} {r['total']:>7}  {r['first']}  {r['last']}")
    live = sum(r["live"] for _, r in rows)
    back = sum(r["backfilled"] for _, r in rows)
    print(f"{'TOTAL':<28} {live:>6} {back:>9} {live + back:>7}   (balance: {live} + {back} = {live + back})")
    print(f"\nevents: {events}\ncounter started: {res['cutover'] or 'no counter rows yet'}"
          + (f"; backfill = headings in {backfill_log} before that date (a floor)" if a.backfill else ""))
    if res["unparsed_rows"]:
        print(f"unparsed counter rows skipped: {res['unparsed_rows']}")
    if res["dropped_unknown_typed"]:
        print(f"typed names that are not tools, not counted: {res['dropped_unknown_typed']}")
    if a.json_out:
        Path(a.json_out).write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
