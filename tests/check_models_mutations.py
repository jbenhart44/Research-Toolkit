#!/usr/bin/env python3
"""Prove check_models.py --self-test catches each way the model gate could pass a command that names no model.

    python3 tests/check_models_mutations.py    # exit 0 = every mutant caught

One mutant per class M1-M16, plus the four the plan names: the exit code ignored, the pcv/ exemption widened, a
spawning command with no site passing, and matching line by line instead of by block. Each mutant is written beside
the real checker and deleted after its run. A mutant must still run: it is wrong, not broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "check_models.py").read_text(encoding="utf-8")
MUTANTS = {
    "M1: a spawn with no marker passes": (
        '            if pats and not marker:\n                find(rel, start, "M1 unmarked_spawn"',
        '            if False:\n                find(rel, start, "M1 unmarked_spawn"',
        ["M1: a spawn sentence with no marker"]),
    "M2: a marker on a block with no spawn passes": (
        '            if not pats:\n                find(rel, start, "M2 stale_marker"',
        '            if False:\n                find(rel, start, "M2 stale_marker"',
        ["M2: a marker on a block with no spawn pattern"]),
    "M3: model=inherit is accepted": (
        '            if not model or model == "inherit":', "            if not model:",
        ["M3: a role marker with model=inherit"]),
    "M4: a block with no literal model passes": (
        "            if not literals:\n                find(rel, start, \"M4 literal_mismatch\"",
        "            if False:\n                find(rel, start, \"M4 literal_mismatch\"",
        ["M4: a site whose literal model is missing", "corpus: deleting the literal model"]),
    "M5: a model the table does not give the role passes": (
        '                if model != r["sonnet-ceiling"]:', "                if False:",
        ["M5: a marker and literal that agree", "corpus: a reasoner marker changed to opus"]),
    "M6: pinned model IDs are not scanned": (
        "            if PINNED.search(line) and not exempt_pinned(rel, text, n, appendix):", "            if False:",
        ["M6: a pinned model ID in a shipped file"]),
    "M7: fable is caught only after --model": (
        """FABLE = re.compile(r'(?:\\bmodel\\s*[:=]\\s*"?|--model[ =]"?)fable\\b', re.I)""",
        """FABLE = re.compile(r'--model[ =]"?fable\\b', re.I)""",
        ["M7: fable as a model value"]),
    "M8: a seat that lists Agent passes": (
        '            if re.search(r"\\bAgent\\b", fm_value(fm, "tools") or ""):', "            if False:",
        ["M8: a seat file that lists Agent in tools"]),
    "M9: model: in a command's frontmatter passes": (
        'if not is_seat and fm_value(fm, "model") is not None and fm_value(fm, "context") != "fork":', "if False:",
        ["M9: model: in a command's own frontmatter"]),
    "M10: 'best available model' is no longer old wording": (
        'OLD_WORDING = re.compile(r"\\bTask tool\\b|best available model", re.I)',
        'OLD_WORDING = re.compile(r"\\bTask tool\\b", re.I)',
        ["M10: the old wording"]),
    "M11: a role may lack its reason": (
        '        missing = [k for k in ("sonnet-ceiling", "opus-ceiling", "haiku_ok", "reason") if k not in r]',
        '        missing = [k for k in ("sonnet-ceiling", "opus-ceiling") if k not in r]',
        ["M11: a role missing a cell"]),
    "M11: a table site with no marker passes": (
        "            if s not in marker_sites:", "            if False:",
        ["M11: a table site with no marker is refused", "corpus: a spawn reworded past every pattern"]),
    "M12: PCV's agent models are not compared": (
        '        if got != want:\n            findings.append((f"pcv/agents/',
        '        if False:\n            findings.append((f"pcv/agents/',
        ["M12: PCV's critic model drifting"]),
    "M13: a MODEL FAILURE copy only has to exist": (
        "            if failure is None or copy != failure:", "            if failure is None:",
        ["M13: a MODEL FAILURE copy that differs"]),
    "M13: a generated block only has to exist": (
        "            if got is None or got.strip() != render(t, name):", "            if got is None:",
        ["M13: a generated README table that differs"]),
    "M13: the config sentence is not required": (
        '                if sentence not in body.replace("\\n", " ").replace("> ", ""):', "                if False:",
        ["M13: a config: marker without the chair sentence"]),
    "M13: the config sentence is always the Chair's": (
        '                sentence = config_sentence(r.get("config_key", "?"), r["sonnet-ceiling"], r["opus-ceiling"])',
        "                sentence = CHAIR_SENTENCE",
        ["M13: a transcriber marker carrying the Chair's sentence is caught"]),
    "M14: a script's --model default is not compared": (
        "            if model != m.group(1):", "            if False:",
        ["M14: a script whose --model default differs"]),
    "M15: a crossmodel call outside an external block passes": (
        "            if EXTERNAL.search(body) and not ext:", "            if False:",
        ["M15: a crossmodel call outside an external block"]),
    "M16: old facts never fail, even under --release": (
        '        if release:\n            findings.append((str(TABLE), "M16 facts_age", msg))',
        '        if False:\n            findings.append((str(TABLE), "M16 facts_age", msg))',
        ["M16: old facts are a finding under --release"]),
    "the exit code is ignored": (
        "    return (1 if findings else 0), findings, rows, notices", "    return 0, findings, rows, notices",
        ["M1: a spawn sentence with no marker", "M6: a pinned model ID in a shipped file"]),
    "the pcv/ exemption is widened to shared/": (
        'SKIP_DIRS = {".git", "pcv"}', 'SKIP_DIRS = {".git", "pcv", "shared"}',
        ["M6: a pinned model ID in a shipped file", "M7: fable as a model value"]),
    "the test-fixture exemption is widened to every script": (
        '    return bool(re.search(r"_(?:selftest|mutations)\\.py$", rel.name)) or str(rel) == "tests/check_models.py"',
        '    return rel.suffix == ".py"',
        ["the same line in a shipped script is caught (M6 and M7)"]),
    "a spawning command with no site passes": (
        '        if not (root / "shared" / "commands" / f"{cmd}.md").is_file() or not sites_per_cmd.get(cmd):',
        '        if not (root / "shared" / "commands" / f"{cmd}.md").is_file():',
        ["a spawning command with no site is exit 2"]),
    "the finder matches line by line, not by block": (
        "            pats = site_patterns(body)",
        "            pats = sorted({p for x in body.splitlines() for p in site_patterns(x)})",
        ["M1: spawn and agent on different lines"]),
}

base = subprocess.run([sys.executable, str(HERE / "check_models.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_check_models.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True)
    finally:
        mut.unlink()
    if "self-test:" not in p.stdout:
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
