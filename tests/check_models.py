#!/usr/bin/env python3
"""Model gate: every place a toolkit command starts a subagent names the model the role table gives that role.

The role table is shared/model-roles.json. A spawn site carries a marker on the first line of its block:

    <!-- spawn: role=reasoner model=sonnet site=pace#coach-c -->
    <!-- spawn: role=chair model=config:model_chair floor=sonnet site=coa#chair -->
    <!-- spawn: external route=crossmodel reason="..." -->
    <!-- spawn: none reason="..." -->            (the block matches a spawn pattern but starts no agent)
    # spawn: role=probe model=haiku              (Python)

A block is a run of lines with no blank line between them; a heading on its own merges with the block under it. The
finder reads each block whole, so "spawn" on one line and "agent" on the next still match. A block is a spawn site if
it contains "Agent tool" or "Task tool", subagent_type, a word starting with "spawn" within 80 characters of "agent",
headless_agent, "claude -p" or "--model".

  M1  unmarked_spawn     a site block with no marker; a command or skill whose allowed-tools lists Agent and that has
                         no marker; a role marker in a file whose allowed-tools omits Agent
  M2  stale_marker       a role or none marker on a block with no spawn pattern; an external marker with no crossmodel
                         call or non-Claude model in its block
  M3  no_model           a role marker with no model=, or model=inherit
  M4  literal_mismatch   a role marker whose block has no literal model: "<alias>", or one that differs from model=
                         (from floor= for a config: marker)
  M5  table_mismatch     a role or site not in the table; model= not the role's sonnet-ceiling value; a config: key
                         that is not the role's key; a role whose two ceilings differ, marked with a fixed model
  M6  pinned_id          a full model ID (claude-opus-5-5, anthropic.claude-...) in a shipped file, outside the dated
                         appendix of references/model-roles.md, the DESIGN.md changelogs, pcv/ and mutation files
  M7  fable              fable as a model value anywhere but references/model-roles.md
  M8  seat_frontmatter   a seat file in coa/agents/ whose name: is not its stem, whose model: is not the reasoner
                         value, or whose tools: lists Agent
  M9  frontmatter_model  model: in a command's or skill's own frontmatter without context: fork
  M10 old_wording        "Task tool" or "best available model" in a command, skill or seat file
  M11 table_integrity    a role missing a cell; an opus-ceiling value below the sonnet-ceiling one; writer on haiku;
                         haiku on a role that is not haiku_ok; a table site with no marker; a role with no site
  M12 upstream_drift     a pcv/agents/*.md model: that differs from the table's recorded PCV rows
  M13 block_drift        a generated block that differs from --render; a MODEL FAILURE block that is not byte-identical
                         to the one in references/model-roles.md; a config: marker without the chair sentence
  M14 script_model       a Python --model default that differs from its # spawn: marker's model
  M15 external_unmarked  mcp__crossmodel__query_model or model: gemini|openai|perplexity outside an external block,
                         in a command, skill or seat file (documents that describe the route are not scanned)
  M16 facts_age          facts_retrieved older than 60 days: a notice, a finding under --release

Exit codes: 0 clean, 1 findings, 2 cannot judge (no or invalid table; a spawning command missing or with no site).
Usage:  python3 tests/check_models.py [--root DIR] [--report | --render | --release]
        python3 tests/check_models.py --self-test          Mutation proof: tests/check_models_mutations.py

What it cannot prove: that a run used the model (/tasks shows that); that the account answer is right; a spawn phrased
with none of the patterns and no marker; managed settings, CLAUDE_CODE_SUBAGENT_MODEL_FORCE, an availableModels
allowlist, or anything else that overrides what a file requests; what an alias resolves to on a given day.
"""
from __future__ import annotations

import datetime
import json
import re
import shlex
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLE = Path("shared/model-roles.json")
SKIP_DIRS = {".git", "pcv"}
FACTS_MAX_DAYS = 60
SITE_PATTERNS = [re.compile(p) for p in (r"\b(?:Agent|Task) tool\b", r"subagent_type", r"headless_agent",
                                          r"\bclaude -p\b", r"--model\b")]
SPAWN, AGENT = re.compile(r"spawn\w*", re.I), re.compile(r"agent", re.I)
MARKER = re.compile(r"^\s*<!--\s*spawn:\s*(.*?)\s*-->\s*$")
PY_MARKER = re.compile(r"^\s*#\s*spawn:\s*(.*?)\s*$")
LITERAL = re.compile(r'\bmodel:\s*"([A-Za-z0-9._-]+)"')
PINNED = re.compile(r"\b(?:anthropic\.)?claude-(?:\d|[a-z]+-\d)")
FABLE = re.compile(r'(?:\bmodel\s*[:=]\s*"?|--model[ =]"?)fable\b', re.I)
EXTERNAL = re.compile(r'mcp__crossmodel__query_model|\bmodel:\s*"?(?:gemini|openai|perplexity)\b', re.I)
OLD_WORDING = re.compile(r"\bTask tool\b|best available model", re.I)
PY_MODEL_DEFAULT = re.compile(r'add_argument\(\s*"--model"[^)]*default\s*=\s*"([^"]+)"')
CHAIR_SENTENCE = ("pass `model` = the value of `model_chair` in `~/.claude/toolkit-config.md` if it is `sonnet` or "
                  "`opus`; otherwise pass `sonnet` and print one line.")
FAILURE_BEGIN, FAILURE_END = "<!-- BEGIN MODEL FAILURE -->", "<!-- END MODEL FAILURE -->"
APPENDIX_HEADING = "## Appendix: what each alias resolved to"
GENERATED = {"README.md": ["role-table"], "references/model-roles.md": ["role-table", "accounts"],
             "shared/commands/setup.md": ["accounts"]}


# ---------------------------------------------------------------- reading files

def frontmatter(text: str) -> tuple[str, int]:
    """(frontmatter text, number of lines it occupies) for a file that opens with ---."""
    lines = text.splitlines()
    if lines and lines[0].strip() == "---":
        for i in range(1, min(len(lines), 40)):
            if lines[i].strip() == "---":
                return "\n".join(lines[1:i]), i + 1
    return "", 0


def fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    return m.group(1).strip() if m else None


def blocks(text: str) -> list[tuple[int, list[str]]]:
    """(first line number, lines) per blank-line block after the frontmatter; heading-only blocks join the next."""
    lines = text.splitlines()
    _, skip = frontmatter(text)
    out, cur, start, pending = [], [], 0, None
    for n in range(skip, len(lines) + 1):
        line = lines[n] if n < len(lines) else ""
        if line.strip():
            if not cur:
                start = n + 1
            cur.append(line)
            continue
        if cur:
            if all(x.lstrip().startswith("#") for x in cur):
                pending = pending or (start, [])
                pending[1].extend(cur)
            else:
                if pending:
                    start, cur = pending[0], pending[1] + cur
                    pending = None
                out.append((start, cur))
            cur = []
    if pending:
        out.append(pending)
    return out


def parse_marker(body: str) -> dict:
    tokens = shlex.split(body)
    m = {"kind": "role"}
    for t in tokens:
        if t in ("none", "external"):
            m["kind"] = t
        elif "=" in t:
            k, _, v = t.partition("=")
            m[k] = v
    return m


def site_patterns(text: str) -> list[str]:
    hits = [p.pattern for p in SITE_PATTERNS if p.search(text)]
    spawns = [s.start() for s in SPAWN.finditer(text)]
    agents = [a.start() for a in AGENT.finditer(text)]
    if any(abs(s - a) <= 80 for s in spawns for a in agents):
        hits.append("spawn~agent")
    return hits


def text_files(root: Path):
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if not p.is_file() or rel.parts[0] in SKIP_DIRS or ".git" in rel.parts:
            continue
        try:
            yield rel, p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue


def site_files(root: Path) -> list[Path]:
    files = sorted((root / "shared" / "commands").glob("*.md")) if (root / "shared" / "commands").is_dir() else []
    files += sorted((root / "shared" / "skills").glob("*/SKILL.md"))
    files += sorted((root / "coa" / "agents").glob("*.md"))
    return files


def py_files(root: Path) -> list[Path]:
    out = []
    for d in ("scripts", "hooks"):
        out += sorted((root / d).glob("*.py"))
    out += sorted((root / "shared" / "skills").glob("*/assets/*.py"))
    return [p for p in out if not re.search(r"_(?:selftest|mutations)\.py$", p.name)]


def between(text: str, begin: str, end: str) -> str | None:
    i, j = text.find(begin), text.find(end)
    return text[i + len(begin):j].strip("\n") if 0 <= i < j else None


# ---------------------------------------------------------------- the table and what is rendered from it

def load_table(root: Path) -> tuple[dict | None, str]:
    p = root / TABLE
    if not p.is_file():
        return None, f"{TABLE} is missing"
    try:
        t = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        return None, f"{TABLE} is not valid JSON: {e}"
    for key in ("roles", "accounts", "account_classes", "spawning_commands", "aliases", "alias_order", "facts_retrieved"):
        if key not in t:
            return None, f"{TABLE} has no '{key}'"
    return t, ""


def class_of(t: dict, account: str) -> str:
    return next(c for c, accts in t["account_classes"].items() if account in accts)


def render(t: dict, name: str) -> str:
    if name == "role-table":
        sc, oc = (", ".join(f"`{a}`" for a in t["account_classes"][c]) for c in ("sonnet-ceiling", "opus-ceiling"))
        rows = [f"| Role | Where it runs | {sc} | {oc} |", "|---|---|---|---|"]
        for role, r in t["roles"].items():
            where = {}
            for s in r.get("sites", []):
                cmd, _, label = s.partition("#")
                where.setdefault(cmd, []).append(label)
            places = " · ".join(f"/{c}: {', '.join(ls)}" for c, ls in where.items())
            hi = r["opus-ceiling"] + (f" (`{r['config_key']}`)" if "config_key" in r else "")
            rows.append(f"| `{role}` | {places} | {r['sonnet-ceiling']} | {hi} |")
        return "\n".join(rows)
    if name == "accounts":
        rows = ["| Answer | Stored as | Class |", "|---|---|---|"]
        for a in t["accounts"]:
            rows.append(f"| {'not sure' if a == 'unknown' else a} | `{a}` | {class_of(t, a)} |")
        return "\n".join(rows)
    raise KeyError(name)


def generated_block(text: str, name: str) -> str | None:
    return between(text, f"<!-- BEGIN GENERATED: {name} -->", f"<!-- END GENERATED: {name} -->")


# ---------------------------------------------------------------- the checks

def scan(root: Path, release: bool = False, today: datetime.date | None = None):
    """(exit code, findings, report rows, notices). findings: (rel:line, class, text)."""
    t, why = load_table(root)
    if t is None:
        return 2, [], [], [why]
    findings, rows, notices = [], [], []

    def find(rel, line, cls, text):
        findings.append((f"{rel}:{line}", cls, text))

    roles, order = t["roles"], t["alias_order"]
    marker_sites: set[str] = set()
    sites_per_cmd: dict[str, int] = {}
    failure = between((root / "references/model-roles.md").read_text(encoding="utf-8"), FAILURE_BEGIN, FAILURE_END) \
        if (root / "references/model-roles.md").is_file() else None

    for path in site_files(root):
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        fm, _ = frontmatter(text)
        tools = fm_value(fm, "allowed-tools")
        restricted, has_agent = tools is not None, tools is not None and re.search(r"\bAgent\b", tools) is not None
        is_seat = rel.parts[0] == "coa"
        markers = 0
        if not is_seat and fm_value(fm, "model") is not None and fm_value(fm, "context") != "fork":
            find(rel, 1, "M9 frontmatter_model", "model: in the file's own frontmatter without context: fork")
        for start, lines in blocks(text):
            mk = [(i, MARKER.match(x)) for i, x in enumerate(lines) if MARKER.match(x)]
            body = "\n".join(x for x in lines if not MARKER.match(x))
            pats = site_patterns(body)
            literals = LITERAL.findall(body)
            lead = next((i for i, x in enumerate(lines) if not x.lstrip().startswith("#")), len(lines))
            if mk and mk[0][0] != lead:
                find(rel, start + mk[0][0], "M2 stale_marker", "a marker must be the block's first line after any heading")
            marker = parse_marker(mk[0][1].group(1)) if mk else None
            if pats or marker:
                rows.append((f"{rel}:{start}", marker["kind"] if marker else "-", ",".join(pats) or "-",
                             "yes" if literals else "no"))
                cmd = rel.stem if rel.parts[:2] == ("shared", "commands") else None
                if cmd and (pats or (marker and marker["kind"] == "role")):
                    sites_per_cmd[cmd] = sites_per_cmd.get(cmd, 0) + 1
            if marker:
                markers += 1
            if pats and not marker:
                find(rel, start, "M1 unmarked_spawn", f"spawn pattern ({','.join(pats)}) and no marker")
                continue
            if not marker:
                continue
            kind = marker["kind"]
            if kind == "external":
                if not EXTERNAL.search(body):
                    find(rel, start, "M2 stale_marker", "external marker with no crossmodel call or non-Claude model")
                continue
            if not pats:
                find(rel, start, "M2 stale_marker", f"{kind} marker on a block with no spawn pattern")
            if kind == "none":
                continue
            if restricted and not has_agent:
                find(rel, start, "M1 unmarked_spawn", "role marker in a file whose allowed-tools omits Agent")
            model, role = marker.get("model"), marker.get("role")
            r = roles.get(role)
            for s in filter(None, marker.get("site", "").split(",")):
                marker_sites.add(s)
                if r is not None and s not in r.get("sites", []):
                    find(rel, start, "M5 table_mismatch", f"site {s} is not a {role} site in the table")
            if not model or model == "inherit":
                find(rel, start, "M3 no_model", f"role={role} with model={model or '(none)'}")
                continue
            want = marker.get("floor") if model.startswith("config:") else model
            if not literals:
                find(rel, start, "M4 literal_mismatch", f'no literal model: "{want}" in the block')
            elif any(x != want for x in literals):
                find(rel, start, "M4 literal_mismatch", f"literal {sorted(set(literals))} differs from {want}")
            if r is None:
                find(rel, start, "M5 table_mismatch", f"role {role} is not in the table")
                continue
            if model.startswith("config:"):
                if model[7:] != r.get("config_key"):
                    find(rel, start, "M5 table_mismatch", f"{model} is not {role}'s key ({r.get('config_key')})")
                if want != r["sonnet-ceiling"]:
                    find(rel, start, "M5 table_mismatch", f"floor={want}, the table says {r['sonnet-ceiling']}")
                if CHAIR_SENTENCE not in body.replace("\n", " ").replace("> ", ""):
                    find(rel, start, "M13 block_drift", "config: marker without the verbatim chair sentence")
            else:
                if model != r["sonnet-ceiling"]:
                    find(rel, start, "M5 table_mismatch", f"model={model}, the table says {r['sonnet-ceiling']}")
                if r["opus-ceiling"] != r["sonnet-ceiling"]:
                    find(rel, start, "M5 table_mismatch", f"{role} differs by account; mark it model=config:<key>")
        if not is_seat and has_agent and markers == 0:
            find(rel, 1, "M1 unmarked_spawn", "allowed-tools lists Agent and the file has no marker")
        if is_seat:
            stem = rel.stem
            if fm_value(fm, "name") != stem:
                find(rel, 1, "M8 seat_frontmatter", f"name: {fm_value(fm, 'name')} is not {stem}")
            if fm_value(fm, "model") != roles.get("reasoner", {}).get("sonnet-ceiling"):
                find(rel, 1, "M8 seat_frontmatter", f"model: {fm_value(fm, 'model')} is not the reasoner value")
            if re.search(r"\bAgent\b", fm_value(fm, "tools") or ""):
                find(rel, 1, "M8 seat_frontmatter", "tools: lists Agent")
        if OLD_WORDING.search(text):
            for n, line in enumerate(text.splitlines(), 1):
                if OLD_WORDING.search(line):
                    find(rel, n, "M10 old_wording", line.strip()[:80])
        if rel.parts[:2] == ("shared", "commands") and rel.stem in t["spawning_commands"]:
            copy = between(text, FAILURE_BEGIN, FAILURE_END)
            if failure is None or copy != failure:
                find(rel, 1, "M13 block_drift", "MODEL FAILURE block missing or not identical to references/model-roles.md")

    for path in py_files(root):
        rel = path.relative_to(root)
        text = path.read_text(encoding="utf-8")
        mk = [parse_marker(m.group(1)) for m in map(PY_MARKER.match, text.splitlines()) if m]
        for m in PY_MODEL_DEFAULT.finditer(text):
            model = mk[0].get("model") if mk else None
            if model != m.group(1):
                find(rel, text[:m.start()].count("\n") + 1, "M14 script_model",
                     f"--model default {m.group(1)} and marker model {model}")
        if (re.search(r"--model\b|\bclaude -p\b", text)) and not mk:
            find(rel, 1, "M1 unmarked_spawn", "passes --model or runs claude -p with no # spawn: marker")

    for rel, text in text_files(root):
        appendix = text.find(APPENDIX_HEADING) if str(rel) == "references/model-roles.md" else -1
        for n, line in enumerate(text.splitlines(), 1):
            if PINNED.search(line) and not exempt_pinned(rel, text, n, appendix):
                find(rel, n, "M6 pinned_id", PINNED.search(line).group(0))
            if FABLE.search(line) and str(rel) != "references/model-roles.md" and not is_test_fixture(rel):
                find(rel, n, "M7 fable", line.strip()[:80])

    for path in site_files(root):
        rel = path.relative_to(root)
        for start, lines in blocks(path.read_text(encoding="utf-8")):
            body = "\n".join(lines)
            ext = any(MARKER.match(x) and parse_marker(MARKER.match(x).group(1))["kind"] == "external" for x in lines)
            if EXTERNAL.search(body) and not ext:
                find(rel, start, "M15 external_unmarked", EXTERNAL.search(body).group(0))

    for role, r in roles.items():
        missing = [k for k in ("sonnet-ceiling", "opus-ceiling", "haiku_ok", "reason") if k not in r]
        if missing:
            findings.append((str(TABLE), "M11 table_integrity", f"{role} has no {', '.join(missing)}"))
            continue
        lo, hi = (order.index(r[c]) if r[c] in order else -1 for c in ("sonnet-ceiling", "opus-ceiling"))
        if min(lo, hi) < 0:
            findings.append((str(TABLE), "M11 table_integrity", f"{role} names a model that is not an alias"))
        elif hi < lo:
            findings.append((str(TABLE), "M11 table_integrity", f"{role}: opus-ceiling below sonnet-ceiling"))
        if role == "writer" and "haiku" in (r["sonnet-ceiling"], r["opus-ceiling"]):
            findings.append((str(TABLE), "M11 table_integrity", "writer on haiku"))
        if "haiku" in (r["sonnet-ceiling"], r["opus-ceiling"]) and not r["haiku_ok"]:
            findings.append((str(TABLE), "M11 table_integrity", f"{role} on haiku but not haiku_ok"))
        seat = role == "reasoner" and any((root / "coa" / "agents").glob("*.md"))
        if not r.get("sites") and not seat:
            findings.append((str(TABLE), "M11 table_integrity", f"{role} has no site"))
        for s in r.get("sites", []):
            if s not in marker_sites:
                findings.append((str(TABLE), "M11 table_integrity", f"table site {s} has no marker"))
    accounts = set(t["accounts"])
    classed = set(a for v in t["account_classes"].values() for a in v)
    if accounts != classed:
        findings.append((str(TABLE), "M11 table_integrity", f"accounts and classes differ: {sorted(accounts ^ classed)}"))

    for agent_file in sorted((root / "pcv" / "agents").glob("*.md")):
        got = fm_value(frontmatter(agent_file.read_text(encoding="utf-8"))[0], "model")
        want = t.get("pcv_upstream", {}).get(agent_file.stem)
        if got != want:
            findings.append((f"pcv/agents/{agent_file.name}:5", "M12 upstream_drift", f"model {got}, recorded {want}"))

    for rel, names in GENERATED.items():
        p = root / rel
        text = p.read_text(encoding="utf-8") if p.is_file() else ""
        for name in names:
            got = generated_block(text, name)
            if got is None or got.strip() != render(t, name):
                findings.append((rel, "M13 block_drift", f"generated block '{name}' missing or differs from --render"))

    age = ((today or datetime.date.today()) - datetime.date.fromisoformat(t["facts_retrieved"])).days
    if age > FACTS_MAX_DAYS:
        msg = f"facts_retrieved is {age} days old (limit {FACTS_MAX_DAYS}); re-fetch Anthropic's pages"
        if release:
            findings.append((str(TABLE), "M16 facts_age", msg))
        else:
            notices.append("notice: " + msg)

    for cmd in t["spawning_commands"]:
        if not (root / "shared" / "commands" / f"{cmd}.md").is_file() or not sites_per_cmd.get(cmd):
            return 2, findings, rows, notices + [f"cannot judge: spawning command '{cmd}' is missing or has no site"]
    return (1 if findings else 0), findings, rows, notices


def is_test_fixture(rel: Path) -> bool:
    """The gate and the mutation files plant bad values on purpose."""
    return bool(re.search(r"_mutations\.py$", rel.name)) or str(rel) == "tests/check_models.py"


def exempt_pinned(rel: Path, text: str, n: int, appendix: int) -> bool:
    if is_test_fixture(rel):
        return True
    if str(rel) == "references/model-roles.md":
        return 0 <= appendix < sum(len(x) + 1 for x in text.splitlines()[:n])
    if str(rel) == "DESIGN.md":
        heads = [h for h in re.finditer(r"^## .*$", text, re.M)]
        offset = sum(len(x) + 1 for x in text.splitlines()[:n - 1])
        current = [h.group(0) for h in heads if h.start() <= offset]
        return bool(current) and "Changelog" in current[-1]
    return False


def balance(rows) -> str:
    kinds = [r[1] for r in rows]
    return (f"balance: {len(rows)} blocks | by pattern {sum(1 for r in rows if r[2] != '-')} | "
            f"role {kinds.count('role')} | none {kinds.count('none')} | external {kinds.count('external')} | "
            f"unmarked {kinds.count('-')}")


# ---------------------------------------------------------------- self-test

FAILURE_TEXT = "\n".join([
    "**MODEL FAILURE.** When an agent this command starts cannot run on its model:",
    "1. A session or weekly limit: stop, quote the error and the reset time, offer wait or stop. No retry.",
    "2. An Opus limit or an unavailable model on the Chair's `opus` request: retry once on `sonnet` and record it.",
    "3. Anything else: stop that role, quote the error and offer the choices. Never change a model on your own.",
])


def good_tree() -> Path:
    """A small tree that passes every class: one spawning command with a reasoner and a chair site."""
    d = Path(tempfile.mkdtemp(prefix="checkmodels_"))
    t = {"schema": 1, "facts_retrieved": datetime.date.today().isoformat(), "aliases": ["haiku", "sonnet", "opus"],
         "alias_order": ["haiku", "sonnet", "opus"], "accounts": ["pro", "max5x", "unknown"],
         "account_classes": {"sonnet-ceiling": ["pro", "unknown"], "opus-ceiling": ["max5x"]},
         "spawning_commands": ["council"],
         "roles": {"reasoner": {"sonnet-ceiling": "sonnet", "opus-ceiling": "sonnet", "haiku_ok": False,
                                "reason": "r", "sites": ["council#seats"]},
                   "chair": {"sonnet-ceiling": "sonnet", "opus-ceiling": "opus", "config_key": "model_chair",
                             "haiku_ok": False, "reason": "r", "sites": ["council#chair"]}},
         "pcv_upstream": {"pcv-critic": "haiku"}}
    files = {
        "shared/model-roles.json": json.dumps(t),
        "shared/commands/council.md": "\n".join([
            "---", "allowed-tools: Read, Agent", "description: x", "---", "",
            "<!-- spawn: role=reasoner model=sonnet site=council#seats -->",
            'Start each seat with the Agent tool, `model: "sonnet"`.', "",
            "## The Chair",
            "<!-- spawn: role=chair model=config:model_chair floor=sonnet site=council#chair -->",
            "Spawn the Chair as its own agent. For its model, " + CHAIR_SENTENCE + ' The floor is `model: "sonnet"`.',
            "", "<!-- spawn: none reason=\"a warning\" -->", "Never role-play a seat; each is an Agent tool call.", "",
            "<!-- spawn: external route=crossmodel reason=\"non-Claude seat\" -->",
            "Call `mcp__crossmodel__query_model` for an outside model.", "",
            FAILURE_BEGIN, FAILURE_TEXT, FAILURE_END, ""]),
        "shared/commands/notes.md": "---\nallowed-tools: Read\ndescription: y\n---\n\nPlain text.\n",
        "references/model-roles.md": "\n".join([
            "# Roles", "", "<!-- BEGIN GENERATED: role-table -->", render(t, "role-table"),
            "<!-- END GENERATED: role-table -->", "", "<!-- BEGIN GENERATED: accounts -->", render(t, "accounts"),
            "<!-- END GENERATED: accounts -->", "", FAILURE_BEGIN, FAILURE_TEXT, FAILURE_END, "",
            "Fable is not used by any role.", "", APPENDIX_HEADING + " on 2026-10-20", "", "sonnet: claude-sonnet-5-5", ""]),
        "README.md": "# Kit\n\n<!-- BEGIN GENERATED: role-table -->\n" + render(t, "role-table")
                     + "\n<!-- END GENERATED: role-table -->\n",
        "shared/commands/setup.md": "---\nallowed-tools: Read\ndescription: z\n---\n\n<!-- BEGIN GENERATED: accounts -->\n"
                                    + render(t, "accounts") + "\n<!-- END GENERATED: accounts -->\n",
        "DESIGN.md": "# Design\n\n## v1.0 Changelog\n\n- the helper wrote claude-opus-4-7\n",
        "pcv/agents/pcv-critic.md": "---\nname: pcv-critic\ntools: Read\nmodel: haiku\n---\nbody claude-opus-4-5\n",
        "scripts/run.py": '# spawn: role=reasoner model=sonnet\nap.add_argument("--model", default="sonnet")\n',
    }
    for rel, body in files.items():
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
    return d


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def variant(edits: list, removes: tuple = ()):
        """The good tree with (file, old, new) edits applied; old=None writes a new file."""
        d = good_tree()
        for rel, old, new in edits:
            p = d / rel
            text = p.read_text(encoding="utf-8") if p.is_file() else ""
            if old is None:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(new, encoding="utf-8")
                continue
            if text.count(old) != 1:
                raise AssertionError(f"fixture anchor {old!r} in {rel} found {text.count(old)} times")
            p.write_text(text.replace(old, new), encoding="utf-8")
        for rel in removes:
            (d / rel).unlink()
        return d

    def classes(d):
        code, f, _, _ = scan(d)
        return code, {c.split()[0] for _, c, _ in f}

    code, f, rows, _ = scan(good_tree())
    check("the good fixture passes every class (positive control)", code == 0 and not f)
    for x in f:
        print("      ", x)

    council, notes = "shared/commands/council.md", "shared/commands/notes.md"
    seat_line = 'Start each seat with the Agent tool, `model: "sonnet"`.'
    cases = [
        ("M1", "a spawn sentence with no marker", [(council, "<!-- spawn: none reason=\"a warning\" -->\n", "")]),
        ("M1", "spawn and agent on different lines of one block are one site",
         [(notes, "Plain text.\n", "Then spawn the reviewer as a separate\nagent for the second pass.\n")]),
        ("M2", "a marker on a block with no spawn pattern",
         [(council, "Never role-play a seat; each is an Agent tool call.", "Never role-play a seat.")]),
        ("M3", "a role marker with model=inherit",
         [(council, "role=reasoner model=sonnet site", "role=reasoner model=inherit site")]),
        ("M4", "a site whose literal model is missing", [(council, seat_line, "Start each seat with the Agent tool.")]),
        ("M5", "a marker and literal that agree with each other but not with the table",
         [(council, "role=reasoner model=sonnet site", "role=reasoner model=opus site"),
          (council, seat_line, seat_line.replace('"sonnet"', '"opus"'))]),
        ("M6", "a pinned model ID in a shipped file", [(notes, "Plain text.", "Use claude-sonnet-5-5 here.")]),
        ("M7", "fable as a model value", [(notes, "Plain text.", 'Set model: "fable".')]),
        ("M8", "a seat file that lists Agent in tools",
         [("coa/agents/coa-skeptic.md", None, "---\nname: coa-skeptic\nmodel: sonnet\ntools: Read, Agent\n---\nSeat.\n")]),
        ("M9", "model: in a command's own frontmatter", [(notes, "allowed-tools: Read\n", "allowed-tools: Read\nmodel: opus\n")]),
        ("M10", "the old wording 'best available model'",
         [(notes, "Plain text.", "If Sonnet is missing, use the best available model.")]),
        ("M11", "a role missing a cell", [(str(TABLE), '"haiku_ok": false, "reason": "r", "sites": ["council#chair"]',
                                          '"haiku_ok": false, "sites": ["council#chair"]')]),
        ("M12", "PCV's critic model drifting from the recorded row",
         [("pcv/agents/pcv-critic.md", "model: haiku", "model: sonnet")]),
        ("M13", "a MODEL FAILURE copy that differs from the canonical block", [(council, "No retry.", "Retry twice.")]),
        ("M14", "a script whose --model default differs from its marker",
         [("scripts/run.py", 'default="sonnet"', 'default="opus"')]),
        ("M15", "a crossmodel call outside an external block",
         [(notes, "Plain text.", "Then call `mcp__crossmodel__query_model`.")]),
    ]
    for cls, label, edits in cases:
        code, got = classes(variant(edits))
        check(f"{cls}: {label} exits 1 and prints {cls} only", code == 1 and got == {cls})

    writer = '"writer": {"sonnet-ceiling": "haiku", "opus-ceiling": "haiku", "haiku_ok": true, "reason": "r", "sites": []}, '
    code, f, _, _ = scan(variant([(str(TABLE), '"reasoner": {', writer + '"reasoner": {')]))
    check("M11: a writer on haiku is refused", any("writer on haiku" in x for _, c, x in f if c.startswith("M11")))
    code, f, _, _ = scan(variant([(str(TABLE), '"opus-ceiling": "opus"', '"opus-ceiling": "haiku"')]))
    check("M11: an opus-ceiling value below the sonnet-ceiling one is refused",
          any("below" in x for _, c, x in f if c.startswith("M11")))
    code, f, _, _ = scan(variant([(str(TABLE), '"sites": ["council#seats"]', '"sites": ["council#seats", "council#gone"]')]))
    check("M11: a table site with no marker is refused",
          any("council#gone" in x for _, c, x in f if c.startswith("M11")))

    d = good_tree()
    tp = d / TABLE
    tj = json.loads(tp.read_text(encoding="utf-8"))
    tj["facts_retrieved"] = "2000-01-01"
    tp.write_text(json.dumps(tj), encoding="utf-8")
    code, f, _, notices = scan(d)
    check("M16: old facts are a notice in ordinary runs", code == 0 and any("facts_retrieved" in n for n in notices))
    code, f, _, _ = scan(d, release=True)
    check("M16: old facts are a finding under --release", code == 1 and {c.split()[0] for _, c, _ in f} == {"M16"})

    code, _ = classes(variant([], removes=(str(TABLE),)))
    check("a missing table is exit 2", code == 2)
    code, _ = classes(variant([(str(TABLE), '"spawning_commands": ["council"]', '"spawning_commands": ["council", "notes"]')]))
    check("a spawning command with no site is exit 2", code == 2)
    code, got = classes(variant([(council, CHAIR_SENTENCE, "pass the configured model.")]))
    check("M13: a config: marker without the chair sentence is caught", code == 1 and got == {"M13"})
    code, got = classes(variant([("README.md", "| `chair` |", "| `boss` |")]))
    check("M13: a generated README table that differs from --render is caught", code == 1 and got == {"M13"})
    code, got = classes(variant([("references/model-roles.md", "Fable is not used by any role.",
                                  "claude-sonnet-5-5 is written before the appendix.")]))
    check("M6: a pinned ID before the dated appendix is caught (the appendix one is allowed)",
          code == 1 and got == {"M6"})
    code, got = classes(variant([("DESIGN.md", "## v1.0 Changelog", "## Notes")]))
    check("M6: a pinned ID outside a DESIGN.md changelog is caught", code == 1 and got == {"M6"})
    code, got = classes(variant([(council, "## The Chair\n<!--", "## The Chair\n\n<!--")]))
    check("a heading on its own line merges with the block below it", code == 0)
    code, got = classes(variant([(council, '<!-- spawn: none reason="a warning" -->\n',
                                  'Note:\n<!-- spawn: none reason="a warning" -->\n')]))
    check("a marker that is not the block's first line is stale", code == 1 and got == {"M2"})

    # Corpus controls (plan check C13): the same defects planted in a copy of this repository's real commands.
    if (ROOT / TABLE).is_file():
        def corpus(edits):
            d = Path(tempfile.mkdtemp(prefix="checkmodels_corpus_")) / "tk"
            shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns(".git", "_mutant_*"))
            for rel, old, new in edits:
                p = d / rel
                text = p.read_text(encoding="utf-8")
                if text.count(old) != 1:
                    return None, set(), [f"stale anchor in {rel}"]
                p.write_text(text.replace(old, new), encoding="utf-8")
            code, f, _, _ = scan(d)
            return code, {c.split()[0] for _, c, _ in f}, [w for w, _, _ in f]

        pace = "shared/commands/pace.md"
        players = "Spawn two Player subagents **in parallel** using the Agent tool, **each with `model: \"sonnet\"`**"
        code, got, where = corpus([])
        check("corpus: the real commands pass (positive control)", code == 0)
        code, got, where = corpus([(pace, players, "Spawn two Player subagents **in parallel** using the Agent tool")])
        check("corpus: deleting the literal model at the /pace Player spawn is caught at that block",
              code == 1 and got == {"M4"} and any(w.startswith(pace + ":") for w in where))
        code, got, where = corpus([(pace, "<!-- spawn: role=reasoner model=sonnet site=pace#cross-reviewer -->",
                                    "<!-- spawn: role=reasoner model=opus site=pace#cross-reviewer -->")])
        check("corpus: a reasoner marker changed to opus is caught (M5)", code == 1 and "M5" in got)
        code, got, where = corpus([("shared/commands/review.md", "<!-- spawn: role=reasoner model=sonnet site=review#lenses -->\n", ""),
                                   ("shared/commands/review.md", "All three subagents run in parallel", "All three lens agents run together")])
        check("corpus: a reworded spawn sentence with its marker deleted is still caught (M1)", code == 1 and "M1" in got)
        code, got, where = corpus([
            ("shared/commands/review.md", "## STEP 1 — Spawn three lens agents in parallel", "## STEP 1 — Three lenses"),
            ("shared/commands/review.md", "<!-- spawn: role=reasoner model=sonnet site=review#lenses -->\n", ""),
            ("shared/commands/review.md", 'All three subagents run in parallel (single message, three `Agent` tool calls). '
             'Use `subagent_type: "general-purpose"` and `model: "sonnet"` for all three',
             "All three run together in one message, each of the general-purpose type")])
        check("corpus: a spawn reworded past every pattern, marker deleted, is caught by the table's site list (M11)",
              code == 1 and "M1" not in got and "M11" in got)

    print(f"check_models self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


# ---------------------------------------------------------------- main

def main() -> int:
    args = sys.argv[1:]
    if "--self-test" in args:
        return self_test()
    root = ROOT
    if "--root" in args:
        i = args.index("--root")
        if i + 1 >= len(args):
            print("usage: --root needs a folder")
            return 2
        root = Path(args[i + 1]).resolve()
    if "--render" in args:
        t, why = load_table(root)
        if t is None:
            print(why)
            return 2
        for name in ("role-table", "accounts"):
            print(f"<!-- BEGIN GENERATED: {name} -->\n{render(t, name)}\n<!-- END GENERATED: {name} -->\n")
        return 0
    code, findings, rows, notices = scan(root, release="--release" in args)
    if "--report" in args:
        for where, kind, pats, lit in rows:
            print(f"{where:<45} marker={kind:<8} patterns={pats:<28} literal model in block: {lit}")
    else:
        for where, cls, text in findings:
            print(f"{where:<45} {cls:<22} {text}")
    for n in notices:
        print(n)
    print(balance(rows))
    if code == 2:
        print("exit 2: cannot judge")
        return 2
    if "--report" in args:
        return 0
    print(f"{len(findings)} finding(s)" + (" — clean" if code == 0 else ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
