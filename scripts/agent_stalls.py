#!/usr/bin/env python3
"""agent_stalls.py -- a ledger of subagent stalls, so a stall is on record the moment it happens and the next run reads it.

    python3 scripts/agent_stalls.py record --tool pcv-research --run-dir <dir> --agents "df1-A,df1-B" \
        --model sonnet --reason "no progress for 600 s" --probe "haiku READY in 4 s" --files-written 0
    python3 scripts/agent_stalls.py recent --hours 6     # exit 1 = a stall in the window: start agents one at a time
    python3 scripts/agent_stalls.py --self-test

`record` appends ONE row per stall event to the ledger and, when --run-dir holds an instrumentation.csv, one row per
stalled agent there (notes "STALLED: <reason>"), so the run's own receipt shows it. `recent` is what makes the ledger
read rather than filed: a command runs it before it starts agents, and a stall in the window means starting one agent
first and the rest only if it finishes.

Why a ledger at all: when every long agent in a run stalls with no file written, the only record is otherwise prose in
a run folder, which nothing reads when the next run starts.

Ledger: --ledger PATH, else $AGENT_STALLS_CSV, else .toolkit/evidence/agent_stalls.csv in the working directory.
Columns: timestamp, tool, run_dir, agents, n_agents, model, reason, probe, files_written, session, notes.
Exit: 0 recorded, or no stall in the window · 1 a stall in the window · 2 usage (a record with no agent or no reason).
Mutation proof: scripts/agent_stalls_mutations.py
"""
from __future__ import annotations

# spawn: none reason="--model records the model a stalled agent requested; this script starts no agent"
import argparse
import csv
import datetime as dt
import os
import sys
import tempfile
from pathlib import Path

FIELDS = ["timestamp", "tool", "run_dir", "agents", "n_agents", "model", "reason", "probe", "files_written", "session",
          "notes"]
INSTR = ["run_id", "mode", "instance", "step", "agent_role", "question_number", "prompt_chars", "completion_chars",
         "prompt_tokens_est", "completion_tokens_est", "wall_clock_ms", "convergence_tag", "convergence_scope",
         "decision_summary", "notes"]


def ledger_path(arg: str = "") -> Path:
    return Path(arg or os.environ.get("AGENT_STALLS_CSV") or Path(".toolkit") / "evidence" / "agent_stalls.csv")


def record(ledger: Path, tool: str, run_dir: str, agents: list[str], reason: str, probe: str, files_written: int,
           model: str = "", session: str = "", notes: str = "", now: dt.datetime | None = None,
           receipt: bool = True) -> dict:
    if not agents or not reason.strip():
        raise ValueError("a stall record needs at least one agent and a reason")
    row = {"timestamp": (now or dt.datetime.now()).isoformat(timespec="seconds"), "tool": tool, "run_dir": run_dir,
           "agents": ";".join(agents), "n_agents": str(len(agents)), "model": model, "reason": reason.strip(),
           "probe": probe, "files_written": str(files_written), "session": session, "notes": notes}
    new = not ledger.exists() or ledger.stat().st_size == 0
    ledger.parent.mkdir(parents=True, exist_ok=True)
    with ledger.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow(row)
    instr = Path(run_dir) / "instrumentation.csv" if run_dir and receipt else None
    if instr and instr.exists():
        with instr.open("a", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            for a in agents:
                w.writerow([Path(run_dir).name, "", "", "stalled", a, "0", "", "0", "", "0", "", "", "", "",
                            f"STALLED: {reason.strip()}; files written {files_written}"])
    return row


def recent(ledger: Path, hours: float, now: dt.datetime | None = None, unreadable: list | None = None) -> list[dict]:
    """Rows in the window. A row whose timestamp does not parse (a second header, a hand edit) is skipped and appended
    to `unreadable`, so the caller can say how many it could not read rather than crash or stay silent."""
    if not ledger.exists():
        return []
    cut = (now or dt.datetime.now()) - dt.timedelta(hours=hours)
    out = []
    with ledger.open(newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                when = dt.datetime.fromisoformat(r.get("timestamp") or "")
            except ValueError:
                if unreadable is not None:
                    unreadable.append(r)
                continue
            if when >= cut:
                out.append(r)
    return out


def self_test() -> int:
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    with tempfile.TemporaryDirectory() as d:
        led, run = Path(d) / "stalls.csv", Path(d) / "run"
        run.mkdir()
        (run / "instrumentation.csv").write_text(",".join(INSTR) + "\n")
        t0 = dt.datetime(2026, 10, 14, 12, 50)
        check("positive control: an empty ledger has no recent stall", recent(led, 6, t0) == [])
        record(led, "pcv-research", str(run), ["df1-A", "df1-B"], "no progress for 600s", "haiku 4 s", 0,
               model="sonnet", now=t0)
        check("a recorded stall is found in the window", len(recent(led, 6, t0 + dt.timedelta(hours=1))) == 1)
        check("and not after the window", recent(led, 6, t0 + dt.timedelta(hours=7)) == [])
        rows = list(csv.DictReader(led.open()))
        check("the row names the agents, their count, the model, the reason and files written",
              rows[0]["agents"] == "df1-A;df1-B" and rows[0]["n_agents"] == "2" and rows[0]["model"] == "sonnet"
              and rows[0]["files_written"] == "0" and rows[0]["reason"] == "no progress for 600s")
        inst = list(csv.DictReader((run / "instrumentation.csv").open()))
        check("the run's instrumentation.csv gets one STALLED row per agent",
              len(inst) == 2 and all(r["notes"].startswith("STALLED:") for r in inst))
        record(led, "coa", str(run), ["skeptic"], "no progress for 600s", "", 0, now=t0, receipt=False)
        check("--no-receipt leaves the run's instrumentation.csv alone",
              len(list(csv.DictReader((run / "instrumentation.csv").open()))) == 2)
        check("a second event appends, with the header written once",
              len(list(csv.DictReader(led.open()))) == 2 and led.read_text().count("timestamp,") == 1)
        bad_led = Path(d) / "bad.csv"
        bad_led.write_text(led.read_text() + ",".join(FIELDS) + "\nnot-a-date,coa,,x,1,,r,,0,,\n", encoding="utf-8")
        skipped: list = []
        try:
            got = recent(bad_led, 100000, t0, unreadable=skipped)
            check("a row with no readable timestamp is skipped and counted, never a crash", len(got) == 2 and len(skipped) == 2)
        except Exception as e:  # noqa: BLE001
            check(f"a row with no readable timestamp is skipped and counted, never a crash (raised {type(e).__name__})", False)
        for bad_agents, bad_reason, label in (([], "x", "no agents"), (["x"], " ", "no reason")):
            try:
                record(led, "coa", "", bad_agents, bad_reason, "", 0)
                check(f"refuses an empty record ({label})", False)
            except ValueError:
                check(f"refuses an empty record ({label})", True)
        old = os.environ.get("AGENT_STALLS_CSV")
        os.environ["AGENT_STALLS_CSV"] = str(Path(d) / "env.csv")
        try:
            check("AGENT_STALLS_CSV names the ledger when --ledger does not", ledger_path() == Path(d) / "env.csv")
            check("--ledger wins over AGENT_STALLS_CSV", ledger_path(str(led)) == led)
        finally:
            if old is None:
                os.environ.pop("AGENT_STALLS_CSV", None)
            else:
                os.environ["AGENT_STALLS_CSV"] = old
        os.environ.pop("AGENT_STALLS_CSV", None)
        check("the default ledger is .toolkit/evidence/ in the working directory",
              ledger_path() == Path(".toolkit") / "evidence" / "agent_stalls.csv")
        if old is not None:
            os.environ["AGENT_STALLS_CSV"] = old
        with open(os.devnull, "w") as null:
            real_out, real_err = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = null
            try:
                code_hit = main(["recent", "--hours", "100000", "--ledger", str(led)])
                code_none = main(["recent", "--hours", "1", "--ledger", str(Path(d) / "absent.csv")])
                code_usage = main(["record", "--tool", "x", "--agents", " ", "--reason", "r", "--ledger", str(led)])
            finally:
                sys.stdout, sys.stderr = real_out, real_err
        check("recent exits 1 when a stall is in the window", code_hit == 1)
        check("recent exits 0 when none is", code_none == 0)
        check("a record with no agent from the command line is exit 2", code_usage == 2)
    print(f"agent_stalls self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", action="store_true")
    sub = ap.add_subparsers(dest="cmd")
    r = sub.add_parser("record")
    r.add_argument("--tool", required=True)
    r.add_argument("--run-dir", default="")
    r.add_argument("--agents", required=True, help="comma-separated agent labels")
    r.add_argument("--model", default="", help="the model the stalled agents requested")
    r.add_argument("--reason", required=True)
    r.add_argument("--probe", default="", help="what a probe agent did just before, if one ran")
    r.add_argument("--files-written", type=int, default=0)
    r.add_argument("--session", default=os.environ.get("CLAUDE_SESSION_ID", ""))
    r.add_argument("--notes", default="")
    r.add_argument("--at", default="", help="when it happened (ISO), for an entry made after the fact; default now")
    r.add_argument("--no-receipt", action="store_true", help="the run's instrumentation.csv already has the rows")
    r.add_argument("--ledger", default="")
    q = sub.add_parser("recent")
    q.add_argument("--hours", type=float, default=6)
    q.add_argument("--ledger", default="")
    a = ap.parse_args(argv)
    if a.self_test:
        return self_test()
    if a.cmd == "record":
        ledger = ledger_path(a.ledger)
        try:
            row = record(ledger, a.tool, a.run_dir, [x.strip() for x in a.agents.split(",") if x.strip()], a.reason,
                         a.probe, a.files_written, a.model, a.session, a.notes,
                         dt.datetime.fromisoformat(a.at) if a.at else None, not a.no_receipt)
        except ValueError as e:
            print(f"refused: {e}", file=sys.stderr)
            return 2
        print(f"recorded: {row['timestamp']} {row['tool']} {row['n_agents']} agent(s) -> {ledger}")
        return 0
    if a.cmd == "recent":
        skipped: list = []
        rows = recent(ledger_path(a.ledger), a.hours, unreadable=skipped)
        for x in rows:
            print(f"{x['timestamp']}  {x['tool']}  {x['n_agents']} agent(s)  {x.get('model', '')}  {x['reason']}")
        print(f"{len(rows)} stall(s) in the last {a.hours:g} h" + (": start one agent first" if rows else ""))
        if skipped:
            print(f"UNCHECKED: {len(skipped)} row(s) with no readable timestamp")
        return 1 if rows else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
