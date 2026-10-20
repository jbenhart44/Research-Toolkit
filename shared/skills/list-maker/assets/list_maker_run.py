#!/usr/bin/env python3
"""
list_maker_run.py -- the deterministic half of /list-maker. A meeting transcript, an email
thread or any notes go in, a numbered work list comes out, and an item keeps its number for life.

THE SPECIFICATION, in four properties
-------------------------------------
The point of the list is that "we're on number 14" means the same thing in a daily summary
written three sessions from now. Four properties follow from that, and they are the whole
specification:

1. ONE CUMULATIVE LEDGER PER STREAM, NOT ONE LIST PER MEETING. "Number 14" only means
   anything if 14 is the same item next week. The ledger spans every meeting of a stream.
2. AN ID IS ASSIGNED ONCE AND NEVER REUSED. Not after the item is done, not after it is
   dropped. `next_id` only ever increases. A number that gets recycled makes every summary
   that cited it retroactively wrong.
3. TIER IS SEPARATE FROM ID. "Do that one first" is about PRIORITY, and priority moves
   while the id does not. Conflating the two is the obvious implementation and it destroys
   property 2 the first time anything is reprioritised.
4. A DEFERRED ITEM IS STILL IN THE LEDGER. Deferring changes a status field and nothing
   else; work set aside is not work finished.

WHAT THIS SCRIPT DOES NOT DO, AND MUST NOT
-------------------------------------------
It does not decide WHAT IS AN ITEM. `scan` finds candidate lines by cue and prints them
with line numbers; a person or the model reads them and decides. A regex cannot tell
"I'll send you an email about the infrastructure" (an item) from "I'll be retiring before
I ever get around to that" (not one), and a script that guesses produces a list nobody
trusts, which is worse than no list.

It also does not decide WHO OWNS AN ITEM. Meeting transcription tools often label every
speaker with the account that recorded the meeting, whoever is talking. Owner is a
judgment call from content, so it is an input to this script, never an output of it.

Usage
-----
  list_maker_run.py scan   --input F          a transcript, an email thread saved as text, or notes
                                              (--transcript is the same option)
  list_maker_run.py add    --items items.json [--owners me,them,both]
  list_maker_run.py bump   --id N [--tier T] [--rank R] [--why "..."]
  list_maker_run.py status --id N --set open|done|deferred|dropped [--why "..."]
  list_maker_run.py list   [--tier T] [--owner O] [--all]
  list_maker_run.py next   [--owner O]
  list_maker_run.py active [--owner O]          the short "right now" list (tier 1)
  list_maker_run.py --self-test

Every action except scan reads and writes ONE ledger: --ledger PATH, else $LIST_MAKER_LEDGER,
else worklist.json in the working directory. One ledger per stream of work.

Exit codes
  0  did the job
  1  nothing to report (an empty list, no next item, nothing new added)
  2  refused: a bad id, a bad tier, a corrupt ledger, a malformed input
  3  `active` only: THE ACTIVE LIST IS CLEARED. Distinct from 0 and from 1 on purpose --
     a caller must be able to tell "nothing left to do right now" from "here is the list"
     and from "the ledger is empty", because clearing it is when the user gets asked
     whether to start a new one.
Mutation proof: list_maker_mutations.py beside this file.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import sys

SCHEMA = 1
TIERS = {1: "now", 2: "this week", 3: "when it comes up", 4: "someday"}

# THE ACTIVE LIST. It should be short: what fits in one sitting, not everything that matters.
#
# Tier 1 IS the active list. There is no second storage and no renumbering, because the
# ledger's whole promise is that item 14 is item 14 in every summary ever written
# (property 2 above). A "new list" with fresh numbers would break every citation.
# So a new list is made by CLEARING tier 1 and promoting the next few, and the ids ride
# along unchanged.
#
# The cap is advisory, not enforced: `active` warns and still prints. A hard refusal here
# would block the one moment the list legitimately runs long -- mid-session, when work is
# being added to a list already in flight -- and a gate that fires during normal work is a
# gate that gets removed.
ACTIVE_CAP = 7
STATUSES = ("open", "done", "deferred", "dropped")

# WHO CAN OWN AN ITEM is a property of the STREAM, not of the script. A ledger records its
# vocabulary at creation (`--owners me,client,both`), and a ledger without the field reads
# as the default. Fixed at creation on purpose: an owner name is cited in summaries the same
# way an id is.
DEFAULT_OWNERS = ("me", "them", "both")

# Cues that an utterance CREATES AN OBLIGATION. Deliberately over-inclusive: a false
# positive costs one line of reading, a false negative loses an item, and losing an item
# is the failure this whole tool exists to prevent.
CUES = [
    r"\bi'?ll\b", r"\bi will\b", r"\bi'?m going to\b", r"\bi need to\b",
    r"\bwe need to\b", r"\byou need to\b", r"\bwe should\b", r"\bwe have to\b",
    r"\bcan you\b", r"\bcould you\b", r"\bplease\b", r"\blet me know\b",
    r"\bthe target is\b", r"\bto-?do\b", r"\bnext step\b", r"\bby tomorrow\b",
    r"\bby monday\b", r"\bthis afternoon\b", r"\bthis evening\b", r"\btonight\b",
    r"\bsend (?:you|me|him|her|them|it)\b", r"\bget back to\b", r"\bfollow up\b",
    r"\bwait(?:ing)? (?:on|for|till|until)\b", r"\bwork on\b", r"\bwrite up\b",
]
CUE_RE = re.compile("|".join(CUES), re.I)

# Lines that match a cue but never carry work. Checked BEFORE the cue, so a hedge wins.
NOISE = re.compile(
    r"\b(?:i'?ll be retiring|i'?ll see|i'?ll let you guys|i'?ll talk to you|"
    r"i'?ll bet|thank you|good deal|no worries|sounds good)\b", re.I)

# A speaker-and-time header line, as transcription tools write them: "[Name] 12:10:14".
TS = re.compile(r"^\[(?P<who>[^\]]+)\]\s+(?P<time>\d{1,2}:\d{2}:\d{2})\s*$")

# Email: a quoted earlier message ("> ..."), a reply attribution ("On Mon, 3 Oct, A wrote:") and header lines carry no
# new work. The quoted text was already scanned when that message arrived; scanning it again turns one promise into two.
EMAIL_SKIP = re.compile(r"^(?:>|On .{1,200} wrote:\s*$|(?:From|To|Cc|Bcc|Sent|Date|Subject|Reply-To):\s)", re.I)


def default_ledger() -> pathlib.Path:
    """Resolved on every call, never at import, so the environment can still change it."""
    return pathlib.Path(os.environ.get("LIST_MAKER_LEDGER") or "worklist.json")


# ------------------------------------------------------------------ ledger
class Refuse(Exception):
    pass


def load(path: pathlib.Path) -> dict:
    if not path.exists():
        return {"schema": SCHEMA, "next_id": 1, "items": []}
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise Refuse(f"{path} is not JSON: {e}")
    if d.get("schema") != SCHEMA:
        raise Refuse(f"{path}: schema {d.get('schema')}, expected {SCHEMA}")
    # THE CORRUPTION GUARD. If next_id ever falls to or below an id already issued, the
    # very next add REUSES a number, and every summary that cited it silently starts
    # pointing at different work. Refuse rather than repair: a wrong number that looks
    # right is the expensive failure here.
    ids = [i["id"] for i in d["items"]]
    if ids and d["next_id"] <= max(ids):
        raise Refuse(
            f"{path}: next_id is {d['next_id']} but id {max(ids)} is already issued. "
            f"The next add would REUSE a number. Find out what edited the ledger, then fix "
            f"next_id to {max(ids) + 1} by hand; this script will not repair it silently.")
    return d


def is_tracked(path: pathlib.Path) -> bool | None:
    """Is the ledger in git? None if the question does not apply (no repo)."""
    import subprocess
    try:
        r = subprocess.run(["git", "-C", str(path.parent), "ls-files", "--error-unmatch",
                            path.name], capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if r.returncode == 0:
        return True
    inside = subprocess.run(["git", "-C", str(path.parent), "rev-parse",
                             "--is-inside-work-tree"], capture_output=True, text=True)
    return False if inside.stdout.strip() == "true" else None


def save(path: pathlib.Path, led: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(led, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # THE NUMBERS ARE THE PRODUCT. An untracked ledger loses every one of them on a cleared
    # disk, and every summary that said "we're on number 14" then points at nothing.
    # This warns rather than refuses: refusing to record work because the file is untracked
    # would lose the work too, which is the wrong trade.
    if is_tracked(path) is False:
        print(f"\n  !! {path} is NOT TRACKED BY GIT. The numbers are the product and they "
              f"live only on this disk.\n     git add -- {path.name!r} && git commit",
              file=sys.stderr)


def norm(text: str) -> str:
    """Normalise for duplicate detection: case, punctuation and spacing do not make an item new."""
    return re.sub(r"[^a-z0-9 ]", "", text.lower()).strip()


def ledger_owners(led: dict) -> tuple[str, ...]:
    """The owner vocabulary this ledger was created with; the default when absent."""
    ow = led.get("owners")
    return tuple(ow) if ow else DEFAULT_OWNERS


def find(led: dict, iid: int) -> dict:
    for it in led["items"]:
        if it["id"] == iid:
            return it
    raise Refuse(f"no item {iid} in the ledger")


# ------------------------------------------------------------------ scan
def scan(source: pathlib.Path) -> list[tuple[int, str]]:
    """Candidate obligation lines, with line numbers, from a transcript, an email thread or notes. JUDGMENT stays with
    the reader."""
    if not source.exists():
        raise Refuse(f"no input at {source}")
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    for i, l in enumerate(lines, 1):
        s = l.strip()
        if not s or TS.match(s) or EMAIL_SKIP.match(s):
            continue
        if NOISE.search(s):
            continue
        if CUE_RE.search(s):
            out.append((i, s))
    return out


# ------------------------------------------------------------------ add
def add(led: dict, items: list[dict], today: str) -> tuple[list[dict], list[dict]]:
    """Merge items. Returns (added, already_present). Never renumbers anything."""
    seen = {norm(i["text"]): i for i in led["items"]}
    added, dup = [], []
    owners = ledger_owners(led)
    for raw in items:
        text = str(raw.get("text", "")).strip()
        if not text:
            raise Refuse("an item with no text; every item needs text a person can act on")
        tier = int(raw.get("tier", 3))
        if tier not in TIERS:
            raise Refuse(f"tier {tier} is not one of {sorted(TIERS)}")
        owner = str(raw.get("owner", owners[0])).lower()
        if owner not in owners:
            raise Refuse(f"owner {owner!r} must be one of {', '.join(owners)} "
                         f"(this ledger's owners; set with --owners when a ledger is created)")
        k = norm(text)
        if k in seen:
            # Re-scanning the same meeting must not create a second number for one item.
            it = seen[k]
            it["last_seen"] = today
            dup.append(it)
            continue
        it = {"id": led["next_id"], "text": text, "owner": owner, "tier": tier,
              "status": "open", "source": raw.get("source", ""),
              "first_seen": today, "last_seen": today, "note": raw.get("note", "")}
        if raw.get("outward"):
            it["outward"] = True     # an email, a push, a send: /step-by-step stops for approval
        led["next_id"] += 1          # only ever increases
        led["items"].append(it)
        seen[k] = it
        added.append(it)
    return added, dup


# ------------------------------------------------------------------ render
def active_items(led: dict, owner=None) -> list[dict]:
    """The active list: tier-1 work that is not finished, in priority order.

    A MODULE FUNCTION rather than a few lines inside main(), so the self-test exercises the
    code that actually runs. A suite that re-implements the rule it is checking passes
    whatever the production path does.

    `deferred` counts as active on purpose: it was set aside, not finished, and a list that
    quietly drops deferred work would report CLEARED while work remained.
    """
    rows = [r for r in led["items"]
            if r["tier"] == 1 and r["status"] in ("open", "deferred")]
    if owner:
        rows = [r for r in rows if r["owner"] in (owner, "both")]
    rows.sort(key=rank_key)
    return rows


def next_item(led: dict, owner=None) -> dict | None:
    """The single item to start on: lowest tier first, then PRIORITY, then id.

    `next` and `active` once sorted differently, so `active` put one item at the top and
    `next` answered another. Two orderings of one list is two answers to "what now". One
    ordering, defined once, used by both.
    """
    rows = [r for r in led["items"] if r["status"] == "open"]
    if owner:
        rows = [r for r in rows if r["owner"] in (owner, "both")]
    if not rows:
        return None
    rows.sort(key=lambda r: (r["tier"],) + rank_key(r))
    return rows[0]


def rank_key(r: dict):
    """Sort PRIORITY FIRST, id second, so a session starts on the most important thing.

    An unranked item sorts AFTER every ranked one, by id, rather than to the front. A
    default of 0 would put brand-new items ahead of work already deliberately ordered,
    which is the opposite of what ranking is for -- and it would happen silently, every
    time anything was added mid-session.
    """
    return (r.get("rank") if r.get("rank") is not None else 10**6, r["id"])


def render(led: dict, tier=None, owner=None, show_all=False) -> list[str]:
    rows = led["items"]
    if not show_all:
        rows = [r for r in rows if r["status"] in ("open", "deferred")]
    if tier is not None:
        rows = [r for r in rows if r["tier"] == tier]
    if owner:
        rows = [r for r in rows if r["owner"] in (owner, "both")]
    rows.sort(key=lambda r: (r["tier"], r["id"]))
    out = []
    for r in rows:
        mark = {"open": " ", "deferred": "~", "done": "x", "dropped": "-"}[r["status"]]
        out.append(f"[{mark}] {r['id']:>3}. (T{r['tier']} {TIERS[r['tier']]:<16}) "
                   f"{r['owner']:<5} {r['text']}" + ("  [outward: approve before sending]" if r.get("outward") else ""))
    return out


# ------------------------------------------------------------------ self-test
def self_test() -> int:
    import tempfile
    passed = failed = 0

    def ck(name, cond):
        nonlocal passed, failed
        passed, failed = (passed + 1, failed) if cond else (passed, failed + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    tmp = pathlib.Path(tempfile.mkdtemp())
    led = {"schema": SCHEMA, "next_id": 1, "items": []}
    T = "2026-09-10"

    a, d = add(led, [{"text": "Send the project infrastructure email", "tier": 1},
                     {"text": "Release the second homework", "tier": 1, "owner": "me"},
                     {"text": "Short answers for the study guide", "tier": 3, "owner": "them"}], T)
    ck("three items get ids 1, 2, 3", [i["id"] for i in a] == [1, 2, 3])
    ck("next_id advanced to 4", led["next_id"] == 4)
    ck("an item with no owner gets the ledger's first owner", a[0]["owner"] == "me")

    # --- IDS ARE STABLE. The whole point.
    a2, d2 = add(led, [{"text": "A brand new thing", "tier": 2}], T)
    ck("a new item does not renumber the old ones",
       [i["id"] for i in led["items"][:3]] == [1, 2, 3])
    ck("the new item gets 4", a2[0]["id"] == 4)

    # --- re-scanning the same meeting must not duplicate
    a3, d3 = add(led, [{"text": "release the SECOND homework!", "tier": 1}], T)   # case and punctuation differ
    ck("the same item re-added creates no second number", not a3 and len(d3) == 1)
    ck("and it is recognised as item 2", d3 and d3[0]["id"] == 2)

    # --- THE ACTIVE LIST. Tier 1 is the short "right now" list, and a CLEARED list must be
    #     distinguishable from a full one or the ask never fires.
    ck("the active list is tier 1 only, not the whole ledger",
       {r["id"] for r in active_items(led)} == {1, 2})
    ck("a tier-3 item is not on the active list",
       3 not in {r["id"] for r in active_items(led)})

    for _i in (1, 2):
        find(led, _i)["status"] = "done"
    ck("an emptied tier 1 renders as CLEARED, not as an ordinary empty list",
       active_items(led) == [])
    ck("and work still waits below it, so 'cleared' never means 'nothing left'",
       [r for r in led["items"] if r["status"] == "open"] != [])
    # restoring one must un-clear it -- a one-way clear would make the ask fire forever
    find(led, 1)["status"] = "open"
    ck("reopening a tier-1 item un-clears the active list",
       [r["id"] for r in active_items(led)] == [1])
    find(led, 1)["status"] = "done"

    find(led, 2)["status"] = "deferred"
    ck("a deferred tier-1 item keeps the list active, since deferred is not done",
       [r["id"] for r in active_items(led)] == [2])
    find(led, 2)["status"] = "done"

    # --- PRIORITY ORDER. Rank first, id second, and an unranked item falls to the END.
    led_r = {"schema": SCHEMA, "next_id": 1, "items": []}
    add(led_r, [{"text": "third by id, first by rank", "tier": 1},
                {"text": "first by id, last by rank", "tier": 1},
                {"text": "unranked, must sort last", "tier": 1}], T)
    find(led_r, 1)["rank"] = 9
    find(led_r, 2)["rank"] = 1
    ck("the active list sorts by rank, not by id",
       [r["id"] for r in active_items(led_r)] == [2, 1, 3])
    ck("an UNRANKED item falls to the end, never to the front",
       active_items(led_r)[-1]["id"] == 3)
    find(led_r, 3)["rank"] = 0
    ck("giving it rank 0 moves it to the front, so rank actually drives the order",
       [r["id"] for r in active_items(led_r)][0] == 3)
    nx_led = {"schema": SCHEMA, "next_id": 4, "items": [
        {"id": 1, "text": "a", "owner": "me", "tier": 1, "status": "open"},
        {"id": 2, "text": "b", "owner": "me", "tier": 1, "status": "open", "rank": 1},
        {"id": 3, "text": "c", "owner": "me", "tier": 2, "status": "open", "rank": 1}]}
    ck("next honours rank before id, like active does", next_item(nx_led)["id"] == 2)
    nx_led["items"][2]["tier"] = 1
    nx_led["items"][2]["rank"] = 0
    ck("next: a lower rank wins within the tier", next_item(nx_led)["id"] == 3)
    nx_led["items"][2]["tier"] = 2
    ck("next: tier beats rank", next_item(nx_led)["id"] == 2)
    ck("next: nothing open is None, not a crash",
       next_item({"schema": SCHEMA, "next_id": 1, "items": []}) is None)
    ck("ranks that tie fall back to id, so the order is never arbitrary",
       [r["id"] for r in active_items({"schema": SCHEMA, "next_id": 4, "items": [
           dict(find(led_r, i), rank=5) for i in (1, 2, 3)]})] == [1, 2, 3])

    # --- tier moves, id does not
    it = find(led, 3)
    before = it["id"]
    it["tier"] = 1
    ck("raising a tier does not change the id", find(led, 3)["id"] == before)
    ck("and the tier actually moved", find(led, 3)["tier"] == 1)

    # --- a deferred item survives
    find(led, 4)["status"] = "deferred"
    ck("a deferred item is still in the ledger", any(i["id"] == 4 for i in led["items"]))
    ck("a deferred item still renders", any(" 4." in r for r in render(led)))
    ck("a deferred item is marked, not hidden", any(r.startswith("[~]") for r in render(led)))

    # --- a DONE item keeps its number forever
    find(led, 1)["status"] = "done"
    a4, _ = add(led, [{"text": "Something after item 1 was finished", "tier": 2}], T)
    ck("an id is never reused after the item is done", a4[0]["id"] == 5)
    ck("the done item is still in the ledger", any(i["id"] == 1 for i in led["items"]))
    ck("done is hidden by default", not any(" 1." in r for r in render(led)))
    ck("done is visible with --all", any(" 1." in r for r in render(led, show_all=True)))

    a5, _ = add(led, [{"text": "Email the client the revised scope", "tier": 2, "outward": True}], T)
    ck("an outward-facing item is marked so the walk stops for approval",
       a5[0].get("outward") is True and any("[outward" in r for r in render(led)))

    for label, bad_item in (("an item with no text is refused", {"tier": 1}),
                            ("a tier outside 1-4 is refused", {"text": "x", "tier": 9}),
                            ("an unknown owner is refused", {"text": "y", "owner": "somebody"})):
        try:
            add(led, [bad_item], T)
            ck(label, False)
        except Refuse:
            ck(label, True)

    # --- the owner vocabulary belongs to the ledger, not the script
    client_led = {"schema": SCHEMA, "next_id": 1, "items": [], "owners": ["me", "client", "both"]}
    try:
        a_c, _ = add(client_led, [{"text": "Recolour the overlay by family", "owner": "client", "tier": 1}], T)
        ck("a ledger created with owners me/client/both accepts client", bool(a_c) and a_c[0]["owner"] == "client")
    except Refuse:
        ck("a ledger created with owners me/client/both accepts client", False)
    try:
        add(client_led, [{"text": "z", "owner": "them"}], T)
        ck("that ledger refuses an owner from another stream", False)
    except Refuse:
        ck("that ledger refuses an owner from another stream", True)
    pp = tmp / "client.json"
    save(pp, client_led)
    ck("owners survive a save/load round trip", ledger_owners(load(pp)) == ("me", "client", "both"))

    try:
        find(led, 999)
        ck("a missing id is refused", False)
    except Refuse:
        ck("a missing id is refused", True)

    # --- the corruption guard, which is the one that protects every past summary
    bad = tmp / "bad.json"
    bad.write_text(json.dumps({"schema": SCHEMA, "next_id": 2,
                               "items": [{"id": 7, "text": "t", "owner": "me", "tier": 1,
                                          "status": "open", "source": "", "first_seen": T,
                                          "last_seen": T, "note": ""}]}))
    try:
        load(bad)
        ck("a ledger whose next_id would reuse a number is refused", False)
    except Refuse as e:
        ck("a ledger whose next_id would reuse a number is refused", "REUSE" in str(e))

    p = tmp / "w.json"
    save(p, led)
    ck("the ledger round-trips", [i["id"] for i in load(p)["items"]] == [i["id"] for i in led["items"]])

    # --- scan finds obligations and skips the hedges
    t = tmp / "t.txt"
    t.write_text("[Speaker] 12:10:14\n"
                 "I'll send you an email about the infrastructure.\n"
                 "I think I'll be retiring before I ever get around to that.\n"
                 "So the biggest issue with undergrads is time.\n"
                 "I need to make a to-do for me for this afternoon.\n")
    hits = scan(t)
    ck("scan finds the two real obligations", [n for n, _ in hits] == [2, 5])
    ck("scan skips the hedge", not any("retiring" in s for _, s in hits))
    ck("scan skips the speaker header", not any(TS.match(s) for _, s in hits))
    mail = tmp / "thread.txt"
    mail.write_text("From: Alex <alex@example.org>\n"
                    "Subject: I'll need the draft\n"
                    "Thanks for this. Could you send me the revised budget by Friday?\n"
                    "\n"
                    "On Mon, 3 Oct 2026, Sam wrote:\n"
                    "> I'll send the slides tomorrow.\n"
                    "> We need to book the room.\n")
    mhits = scan(mail)
    ck("an email's own request is a candidate", [n for n, _ in mhits] == [3])
    ck("quoted lines of an earlier message are skipped", not any("slides" in s or "book the room" in s for _, s in mhits))
    ck("header and attribution lines are skipped", not any(s.startswith(("Subject:", "On Mon")) for _, s in mhits))
    try:
        scan(tmp / "nope.txt")
        ck("a missing transcript is refused", False)
    except Refuse:
        ck("a missing transcript is refused", True)

    old = os.environ.get("LIST_MAKER_LEDGER")
    os.environ["LIST_MAKER_LEDGER"] = str(tmp / "env.json")
    ck("LIST_MAKER_LEDGER names the ledger when --ledger does not", default_ledger() == tmp / "env.json")
    os.environ.pop("LIST_MAKER_LEDGER")
    ck("the default ledger is worklist.json in the working directory", default_ledger() == pathlib.Path("worklist.json"))
    if old is not None:
        os.environ["LIST_MAKER_LEDGER"] = old

    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"list-maker self-test: {passed} passed, {failed} failed")
    return 1 if failed else 0


# ------------------------------------------------------------------ main
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", nargs="?",
                    choices=["scan", "add", "bump", "status", "list", "next", "active"])
    ap.add_argument("--input", "--transcript", dest="transcript", type=pathlib.Path,
                    help="a transcript, an email thread saved as text, or notes")
    ap.add_argument("--items", type=pathlib.Path)
    ap.add_argument("--ledger", type=pathlib.Path, default=None,
                    help="default: $LIST_MAKER_LEDGER, else worklist.json in the working directory")
    ap.add_argument("--id", type=int)
    ap.add_argument("--tier", type=int)
    ap.add_argument("--rank", type=int)
    ap.add_argument("--set", dest="newstatus", choices=STATUSES)
    ap.add_argument("--owner")
    ap.add_argument("--owners", help="comma-separated owner vocabulary for a NEW ledger, "
                    "e.g. me,client,both; refused on a ledger that already has a different one")
    ap.add_argument("--why", default="")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args(argv)

    if a.self_test:
        return self_test()
    if not a.action:
        ap.print_usage()
        return 2

    today = dt.date.today().isoformat()
    ledger = a.ledger or default_ledger()
    try:
        if a.action == "scan":
            if not a.transcript:
                raise Refuse("scan needs --input <file>")
            hits = scan(a.transcript)
            for n, s in hits:
                print(f"{n:>5}: {s}")
            print(f"\n{len(hits)} candidate line(s). "
                  f"THESE ARE CANDIDATES, NOT ITEMS -- read them and decide.", file=sys.stderr)
            return 0 if hits else 1

        led = load(ledger)
        if a.owners:
            wanted = tuple(o.strip().lower() for o in a.owners.split(",") if o.strip())
            if not wanted:
                raise Refuse("--owners needs at least one name")
            if ledger.exists() and ledger_owners(led) != wanted:
                raise Refuse(f"{ledger} already names its owners "
                             f"({', '.join(ledger_owners(led))}); a stream's owner vocabulary "
                             f"is fixed at creation. Use a different --ledger for a different stream.")
            led["owners"] = list(wanted)

        if a.action == "add":
            if not a.items:
                raise Refuse("add needs --items <file.json>")
            payload = json.loads(a.items.read_text(encoding="utf-8"))
            items = payload["items"] if isinstance(payload, dict) else payload
            added, dup = add(led, items, today)
            save(ledger, led)
            for it in added:
                print(f"  NEW  {it['id']:>3}. (T{it['tier']}) {it['owner']:<5} {it['text']}")
            for it in dup:
                print(f"  seen {it['id']:>3}. already on the list, last seen {it['last_seen']}")
            print(f"\n{len(added)} new, {len(dup)} already present. "
                  f"next id is {led['next_id']}.")
            return 0 if added else 1

        if a.action == "bump":
            if a.id is None or (a.tier is None and a.rank is None):
                raise Refuse("bump needs --id and at least one of --tier or --rank")
            if a.tier is not None and a.tier not in TIERS:
                raise Refuse(f"tier {a.tier} is not one of {sorted(TIERS)}")
            it = find(led, a.id)
            if a.rank is not None:
                print(f"  {it['id']}. rank {it.get('rank')} -> {a.rank} (priority within its tier)")
                it["rank"] = a.rank
            if a.tier is not None:
                print(f"  {it['id']}. tier {it['tier']} -> {a.tier} ({TIERS[a.tier]}); "
                      f"the id is unchanged, which is the point.")
                it["tier"] = a.tier
            it["last_seen"] = today
            if a.why:
                it["note"] = (it["note"] + " | " if it["note"] else "") + a.why
            save(ledger, led)
            return 0

        if a.action == "status":
            if a.id is None or not a.newstatus:
                raise Refuse("status needs --id and --set")
            it = find(led, a.id)
            old = it["status"]
            it["status"] = a.newstatus
            it["last_seen"] = today
            if a.why:
                it["note"] = (it["note"] + " | " if it["note"] else "") + a.why
            save(ledger, led)
            print(f"  {it['id']}. {old} -> {a.newstatus}. It keeps id {it['id']} for life.")
            return 0

        if a.action == "list":
            rows = render(led, a.tier, a.owner, a.all)
            print("\n".join(rows) if rows else "nothing open.")
            return 0 if rows else 1

        if a.action == "active":
            # The short "what are we doing right now" list. Exit 3 means CLEARED, which is
            # the signal /step-by-step stops on to ask whether to restart. It is deliberately
            # NOT exit 0: a cleared list and a list with work left must not look the same to
            # a caller, or the ask never happens.
            rows = active_items(led, a.owner)
            if not rows:
                print("ACTIVE LIST CLEARED: every tier-1 item is done, deferred out, or dropped.")
                print("STOP. Ask the user whether to restart the list before promoting anything.")
                nxt = [r for r in led["items"] if r["status"] == "open"]
                nxt.sort(key=lambda r: (r["tier"],) + rank_key(r))
                if nxt:
                    print(f"\n{len(nxt)} item(s) wait below tier 1. The next few:")
                    for r in nxt[:ACTIVE_CAP]:
                        print(f"    {r['id']:>3}. (T{r['tier']}) {r['owner']:<5} {r['text']}")
                else:
                    print("\nNothing waits below it either. The ledger has no open work.")
                return 3
            print(f"ACTIVE LIST: {len(rows)} item(s), what we are doing right now:")
            for r in rows:
                mark = {"open": " ", "deferred": "~"}[r["status"]]
                print(f"  [{mark}] {r['id']:>3}. {r['owner']:<5} {r['text']}"
                      + ("  [outward: approve before sending]" if r.get("outward") else ""))
            if len(rows) > ACTIVE_CAP:
                print(f"\n  !! {len(rows)} items is longer than the cap of {ACTIVE_CAP}. "
                      f"This is meant to be what fits in one sitting.")
                print("     Demote the ones that are not now: "
                      "list_maker_run.py bump --id N --tier 2 --why '...'")
            return 0

        if a.action == "next":
            r = next_item(led, a.owner)
            if r is None:
                print("nothing open.")
                return 1
            print(f"{r['id']}. (T{r['tier']} {TIERS[r['tier']]}) {r['owner']}: {r['text']}"
                  + ("  [outward: approve before sending]" if r.get("outward") else ""))
            if r["source"]:
                print(f"    source: {r['source']}")
            return 0

    except Refuse as e:
        print(f"REFUSED: {e}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    sys.exit(main())
