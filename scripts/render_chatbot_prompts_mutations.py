#!/usr/bin/env python3
"""Prove render_chatbot_prompts.py --self-test catches each way the chatbot prompts could ship wrong or unlabelled.

    python3 scripts/render_chatbot_prompts_mutations.py    # exit 0 = every mutant caught

Each mutant is written beside the real script and deleted after its run. A mutant must still run: it is wrong, not
broken.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = (HERE / "render_chatbot_prompts.py").read_text(encoding="utf-8")
MUTANTS = {
    "a command with no row passes": (
        '    out = [f"/{n} has no row in shared/chatbot.json" for n in sorted(set(have) - set(table))]',
        "    out = []",
        ["a command with no row is caught"]),
    "an unknown label passes": (
        '        if row.get("fit") not in FITS:', "        if False:",
        ["an unknown label is caught"]),
    "the honesty rule is left out of the preface": (
        "2. Never say you ran, read, checked or verified something you did not.",
        "2. Be helpful.",
        ["the preface says never to claim a check that did not happen"]),
    "the frontmatter is kept": (
        '    text = re.sub(r"\\A---\\n.*?\\n---\\n", "", text, count=1, flags=re.S)', "    text = text",
        ["frontmatter is removed"]),
    "the model-failure block is kept": (
        '    text = re.sub(r"<!-- BEGIN MODEL FAILURE -->.*?<!-- END MODEL FAILURE -->\\n?", "", text, flags=re.S)',
        "    text = text",
        ["the model-failure block and its rule-2 line are removed"]),
    "$ARGUMENTS is kept": (
        '    text = text.replace("$ARGUMENTS", "")', "    text = text",
        ["$ARGUMENTS is removed"]),
    "a Claude Code-only tool gets a prompt": (
        '            if r["fit"] != "none" and n in have}', "            if n in have}",
        ["a Claude Code-only tool gets no prompt file"]),
    "--check never compares the prompt files": (
        "        if not p.is_file() or p.read_text(encoding=\"utf-8\") != body_text:", "        if not p.is_file():",
        ["a hand-edited prompt file is caught"]),
    "a stray prompt file passes": (
        '    stale += [f"chatbot/{x} has no tool behind it" for x in extra]', "    stale += []",
        ["a prompt file with no tool behind it is caught"]),
    "the ZIP is never compared": (
        "    if read_zip(site / ZIP) != members:", "    if False:",
        ["a ZIP whose files differ is caught", "a missing ZIP is caught"]),
    "the ZIP leaves out the README": (
        '    members["README.txt"] = readme(table, tools(root), {Path(m).stem: t for m, t in members.items()})', "    pass",
        ["the ZIP holds every chat prompt and a README"]),
    "the copy button loses its name": (
        'data-src="{src}" aria-label="Copy the /{n} prompt">', 'data-src="{src}">',
        ["each button, link and prompt box names its tool"]),
    "a URL in a note stays plain text": (
        "    return re.sub(r\"https?://[^\\s<]*[^\\s<.,;:)]\", lambda m: f'<a href=\"{m.group(0)}\">{m.group(0)}</a>', escaped)",
        "    return escaped",
        ["a URL in a Claude Code-only note becomes a link"]),
    "the size note never names a long prompt": (
        "    names = sorted(n for n, s in sizes.items() if s >= LONG)", "    names = []",
        ["a long prompt is named in the size note", "the README names the long prompt"]),
    "a note reaches the page unescaped": (
        '            note = html.escape(table[n]["note"].strip())', '            note = table[n]["note"].strip()',
        ["a note is HTML-escaped on the page"]),
}

base = subprocess.run([sys.executable, str(HERE / "render_chatbot_prompts.py"), "--self-test"], capture_output=True, text=True)
if base.returncode != 0:
    print("SETUP ERROR: the unmutated self-test is red:\n" + base.stdout)
    sys.exit(2)
holes = []
for name, (old, new, must) in MUTANTS.items():
    if SRC.count(old) != 1:
        print(f"SETUP ERROR (stale anchor, the code moved): '{name}' anchor found {SRC.count(old)} times")
        sys.exit(2)
    mut = HERE / "_mutant_render_chatbot_prompts.py"
    mut.write_text(SRC.replace(old, new), encoding="utf-8")
    try:
        p = subprocess.run([sys.executable, str(mut), "--self-test"], capture_output=True, text=True)
    finally:
        mut.unlink()
    if "self-test:" not in p.stdout:
        print(f"BROKEN  {name}: the mutant did not run\n{(p.stdout + p.stderr)[-400:]}")
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
