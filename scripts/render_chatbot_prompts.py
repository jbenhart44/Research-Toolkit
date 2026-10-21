#!/usr/bin/env python3
"""render_chatbot_prompts.py -- turn the toolkit's commands into prompts a person can paste into an ordinary chatbot.

    python3 scripts/render_chatbot_prompts.py --check                      # every command and skill has a row
    python3 scripts/render_chatbot_prompts.py --site <site>/toolkit        # write the prompts and the page section
    python3 scripts/render_chatbot_prompts.py --site <site>/toolkit --check   # exit 1 if the site's copies are stale
    python3 scripts/render_chatbot_prompts.py --self-test

`shared/chatbot.json` labels every command and skill: `full` (works in a chat), `limited` (works, with what changes
stated) or `none` (Claude Code only), each with a note. This script refuses a command or skill with no row, a row with
no command, an unknown label or a missing note, so a new command cannot reach the site unlabelled.

For `full` and `limited` it writes `<site>/chatbot/<name>.txt`: a short preface telling the chatbot what it cannot do
in a chat (run commands, open files, start agents) and that it must never claim to have done them, then the command's
own instructions with the Claude Code parts removed (frontmatter, agent markers, the model-failure block, $ARGUMENTS).
It writes the page section between `<!-- BEGIN GENERATED: chatbot -->` and `<!-- END GENERATED: chatbot -->` in the
site's index.html: one collapsible block per tool, and a table of the Claude Code-only tools with the reason for each.

Exit 0 clean or written · 1 a row is missing, stale or wrong, or the site's copies differ · 2 usage (no table, no markers).
Mutation proof: scripts/render_chatbot_prompts_mutations.py
"""
from __future__ import annotations

import html
import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FITS = ("full", "limited", "none")
BEGIN, END = "<!-- BEGIN GENERATED: chatbot -->", "<!-- END GENERATED: chatbot -->"
ZIP = "chatbot/research-toolkit-chat-prompts.zip"
REPO = "https://github.com/jbenhart44/Research-Toolkit/blob/main/"

PREFACE = ('You are running "/{name}", one tool from the Research Amp Toolkit (https://github.com/jbenhart44/Research-Toolkit). '
           "It was written for Claude Code. Here it runs in a chat, so follow the instructions below with these changes:\n\n"
           "1. You cannot run commands, open files on my computer, search my folders or start other agents. Where a step "
           "says to do one of those, tell me exactly what you need and wait for me to paste it, or say what you would do "
           "and that it was not done.\n"
           '2. Never say you ran, read, checked or verified something you did not. "Not checked" is an acceptable answer; '
           "a guessed result is not.\n"
           "3. Where the instructions start separate agents (a council seat, a player, a coach, a reviewer), play each "
           "role in turn, label each one, and say at the end that one model wrote every role, so their agreement is weak "
           "evidence.\n"
           "4. Ignore the parts about installing, hooks, configuration files, run reports and logs, unless I ask about "
           "them.\n"
           "5. Before you start, ask me for what this tool works on.\n\n"
           "{fit_line}\n")
FIT_LINE = {"full": "What works here: {note}", "limited": "What works here, and what does not: {note}"}


def tools(root: Path) -> dict[str, Path]:
    found = {p.stem: p for p in (root / "shared" / "commands").glob("*.md")}
    found.update({p.parent.name: p for p in (root / "shared" / "skills").glob("*/SKILL.md")})
    if (root / "pcv" / "skill" / "SKILL.md").is_file():
        found["pcv"] = root / "pcv" / "skill" / "SKILL.md"
    return found


def load_table(root: Path) -> dict | None:
    p = root / "shared" / "chatbot.json"
    try:
        return json.loads(p.read_text(encoding="utf-8"))["tools"]
    except (OSError, ValueError, KeyError):
        return None


def coverage(root: Path, table: dict) -> list[str]:
    have = tools(root)
    out = [f"/{n} has no row in shared/chatbot.json" for n in sorted(set(have) - set(table))]
    out += [f"shared/chatbot.json row '{n}' names no command or skill" for n in sorted(set(table) - set(have))]
    for n, row in sorted(table.items()):
        if row.get("fit") not in FITS:
            out.append(f"'{n}': fit is {row.get('fit')!r}, not one of {', '.join(FITS)}")
        if len(str(row.get("note", "")).strip()) < 20:
            out.append(f"'{n}': the note is missing or under 20 characters")
    return out


def body(text: str) -> str:
    text = re.sub(r"\A---\n.*?\n---\n", "", text, count=1, flags=re.S)
    text = re.sub(r"<!-- BEGIN MODEL FAILURE -->.*?<!-- END MODEL FAILURE -->\n?", "", text, flags=re.S)
    text = re.sub(r"^.*(?:starts no Chair|has no Chair), so rule 2 never applies here\.\s*\n", "", text, flags=re.M)
    text = re.sub(r"<!--.*?-->\n?", "", text, flags=re.S)
    text = text.replace("$ARGUMENTS", "")
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def prompt(name: str, row: dict, source: Path) -> str:
    head = PREFACE.format(name=name, fit_line=FIT_LINE.get(row["fit"], "Note: {note}").format(note=row["note"].strip()))
    return head + "\n---\n\n" + body(source.read_text(encoding="utf-8"))


LONG = 30000      # characters; a prompt this long is named in the size note


def long_prompts(want: dict[str, str]) -> tuple[list[str], list[int], int]:
    """The long prompts' names, their lengths, and the longest of the rest, computed so the note cannot go stale."""
    sizes = {Path(rel).stem: len(text) for rel, text in want.items()}
    names = sorted(n for n, s in sizes.items() if s >= LONG)
    return names, [sizes[n] for n in names], max([s for n, s in sizes.items() if n not in names], default=0)


def and_list(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def size_note(want: dict[str, str]) -> str:
    names, sizes, rest = long_prompts(want)
    if not names:
        return ""
    lo, hi = (round(min(sizes), -3), round(max(sizes), -3))
    span = f"about {hi:,}" if lo == hi else f"about {lo:,} to {hi:,}"
    under = -(-rest // 10000) * 10000
    noun = "prompts are" if len(names) > 1 else "prompt is"
    return (f" The {and_list([f'<code>/{n}</code>' for n in names])} {noun} the longest, {span} characters"
            + (f"; the others are under {under:,}." if rest else "."))


def linkify(escaped: str) -> str:
    """Turn a URL in an already-escaped note into a link; a trailing full stop stays outside it."""
    return re.sub(r"https?://[^\s<]*[^\s<.,;:)]", lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', escaped)


def section(root: Path, table: dict) -> str:
    have = tools(root)
    rel = lambda n: have[n].relative_to(root).as_posix()  # noqa: E731
    out = [BEGIN,
           '<h2 id="chatbot">Use the Tools in a Chatbot</h2>',
           "<p>No Claude Code? Some tools also work in an ordinary chat. Open one, copy its prompt into a new chat, "
           "and give it your material when it asks. Each prompt starts with a short note that tells the chatbot what it "
           "cannot do in a chat, such as run commands or open your files, and never to claim it did.</p>",
           '<div class="callout"><p><strong>Made for Claude, works in other chatbots.</strong> The tools were written '
           "and tested with Claude. You can paste them into ChatGPT, Gemini or Copilot, but nobody has measured the "
           "results there, so check the answers the way each prompt asks. If a chatbot asks which Claude account you "
           "use, say you are not using Claude Code.</p></div>",
           f"<p>A chat may refuse a long prompt.{size_note(outputs(root, table))} If it does, open the prompt as text, "
           "save it, and attach the file.</p>",
           f'<p><a class="hero-cta" href="{ZIP}" download>Download all {len(outputs(root, table))} chat prompts (ZIP)'
           "</a> with a README that says what each one is for.</p>"]
    for fit, title, lead in (("full", "Works in a Chat", ""),
                             ("limited", "Works in a Chat, with Limits",
                              "<p>Read each note. Where a tool uses several agents, one chatbot plays all of them, so "
                              "their agreement proves little.</p>")):
        names = sorted(n for n, r in table.items() if r["fit"] == fit and n in have)
        out += [f"<h3>{title}</h3>"] + ([lead] if lead else [])
        for n in names:
            src = f"chatbot/{n}.txt"
            note = html.escape(table[n]["note"].strip())
            out.append(
                f'<details class="chatbot" id="chatbot-{n}">\n'
                f"  <summary><code>/{n}</code></summary>\n"
                f'  <p class="chatbot-note">{note}</p>\n'
                f'  <p class="chatbot-actions" aria-live="polite"><button type="button" class="chatbot-copy" '
                f'data-src="{src}" aria-label="Copy the /{n} prompt">Copy the prompt</button> <a href="{src}" '
                f'aria-label="Open the /{n} prompt as text">Open it as text</a> &middot; <a href="{REPO}{rel(n)}" '
                f'aria-label="The /{n} Claude Code file on GitHub">The Claude Code file</a></p>\n'
                f'  <pre class="chatbot-prompt" data-src="{src}" tabindex="0" role="region" '
                f'aria-label="Prompt text for /{n}"><code>Loading the prompt. If nothing appears, use &ldquo;Open it as '
                f"text&rdquo; above.</code></pre>\n"
                "</details>")
    out += ["<h3>Claude Code Only</h3>",
            "<table>", "  <thead><tr><th>Tool</th><th>Why it needs Claude Code</th></tr></thead>", "  <tbody>"]
    for n in sorted(n for n, r in table.items() if r["fit"] == "none" and n in have):
        out.append(f"    <tr><td><code>/{n}</code></td><td>{linkify(html.escape(table[n]['note'].strip()))}</td></tr>")
    out += ["  </tbody>", "</table>", SCRIPT, END]
    return "\n".join(out)


SCRIPT = """<script>
(function () {
  function load(pre) {
    if (pre.dataset.loaded) return Promise.resolve(pre.textContent);
    return fetch(pre.dataset.src).then(function (r) {
      if (!r.ok) throw new Error(r.status);
      return r.text();
    }).then(function (t) {
      pre.firstElementChild.textContent = t;
      pre.dataset.loaded = "1";
      return t;
    });
  }
  document.querySelectorAll("details.chatbot").forEach(function (d) {
    d.addEventListener("toggle", function () {
      if (!d.open) return;
      var pre = d.querySelector("pre.chatbot-prompt");
      load(pre).catch(function () {
        pre.firstElementChild.textContent = "Could not load the prompt here. Use \\u201cOpen it as text\\u201d above.";
      });
    });
  });
  document.querySelectorAll("button.chatbot-copy").forEach(function (b) {
    b.addEventListener("click", function () {
      var pre = b.closest("details").querySelector("pre.chatbot-prompt");
      if (!pre.dataset.loaded) { b.textContent = "Still loading, try again"; return; }
      navigator.clipboard.writeText(pre.firstElementChild.textContent).then(function () {
        b.textContent = "Copied";
      }, function () {
        b.textContent = "Copy failed: open it as text";
      });
      setTimeout(function () { b.textContent = "Copy the prompt"; }, 2500);
    });
  });
})();
</script>"""


def outputs(root: Path, table: dict) -> dict[str, str]:
    have = tools(root)
    return {f"chatbot/{n}.txt": prompt(n, r, have[n]) for n, r in sorted(table.items())
            if r["fit"] != "none" and n in have}


def readme(table: dict, have: dict, want: dict[str, str]) -> str:
    """The index that travels in the ZIP: what each prompt is for, and what needs Claude Code."""
    lines = ["Research Amp Toolkit: prompts for an ordinary chatbot",
             "https://jbenhart44.github.io/toolkit/#chatbot", "",
             "Open a prompt file, copy all of it into a new chat (or attach the file), and give the chatbot your",
             "material when it asks. Each prompt starts with rules for working in a chat.", ""]
    names = long_prompts({f"chatbot/{n}.txt": t for n, t in want.items()})[0] if want else []
    start = ["Not sure where to start? Use help.txt."] if "help" in want else []
    if names:
        start.append(f"{and_list([f'{n}.txt' for n in names])} {'are' if len(names) > 1 else 'is'} the longest; "
                     "if a chat will not take one, attach the file instead.")
    lines += start + ([""] if start else [])
    lines += ["The tools were written for Claude Code and tested with Claude models. You can paste the",
              "prompts into ChatGPT, Gemini, Copilot or any other assistant. A few lines still name Claude",
              "Code or a Claude account. Their results there have not been measured, so check what comes back.", ""]
    for fit, title in (("full", "Works in a Chat"), ("limited", "Works in a Chat, with Limits")):
        lines += [title, "-" * len(title)]
        lines += [f"{n}.txt  /{n}: {table[n]['note'].strip()}" for n in sorted(table)
                  if table[n]["fit"] == fit and n in have] + [""]
    lines += ["Needs Claude Code (No Prompt Here)", "-" * len("Needs Claude Code (No Prompt Here)")]
    lines += [f"/{n}: {table[n]['note'].strip()}" for n in sorted(table) if table[n]["fit"] == "none" and n in have]
    return "\n".join(lines) + "\n"


def zip_members(root: Path, table: dict) -> dict[str, str]:
    members = {rel.split("/", 1)[1]: text for rel, text in outputs(root, table).items()}
    members["README.txt"] = readme(table, tools(root), {Path(m).stem: t for m, t in members.items()})
    return members


def write_zip(path: Path, members: dict[str, str]) -> None:
    import zipfile
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(members):
            info = zipfile.ZipInfo(f"research-toolkit-chat-prompts/{name}", date_time=(1980, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, members[name])


def read_zip(path: Path) -> dict[str, str] | None:
    import zipfile
    try:
        with zipfile.ZipFile(path) as z:
            return {n.split("/", 1)[1]: z.read(n).decode("utf-8") for n in z.namelist() if not n.endswith("/")}
    except (OSError, zipfile.BadZipFile, UnicodeDecodeError, IndexError):
        return None


def write_site(root: Path, site: Path, table: dict, check: bool) -> tuple[int, list[str]]:
    page = site / "index.html"
    if not page.is_file():
        return 2, [f"no index.html in {site}"]
    text = page.read_text(encoding="utf-8")
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        return 2, [f"{page} needs exactly one {BEGIN} and one {END}"]
    a, b = text.index(BEGIN), text.index(END) + len(END)
    new_page = text[:a] + section(root, table) + text[b:]
    want = outputs(root, table)
    stale = [] if new_page == text else ["index.html: the chatbot section differs"]
    for rel, body_text in want.items():
        p = site / rel
        if not p.is_file() or p.read_text(encoding="utf-8") != body_text:
            stale.append(f"{rel} is missing or differs")
    extra = sorted(p.name for p in (site / "chatbot").glob("*.txt") if f"chatbot/{p.name}" not in want) \
        if (site / "chatbot").is_dir() else []
    stale += [f"chatbot/{x} has no tool behind it" for x in extra]
    members = zip_members(root, table)
    if read_zip(site / ZIP) != members:     # compared by content, so a different zlib cannot make it stale
        stale.append(f"{ZIP} is missing or its files differ")
    if check:
        return (1 if stale else 0), stale
    (site / "chatbot").mkdir(exist_ok=True)
    for rel, body_text in want.items():
        (site / rel).write_text(body_text, encoding="utf-8")
    write_zip(site / ZIP, members)
    page.write_text(new_page, encoding="utf-8")
    return 0, [f"wrote {len(want)} prompt(s), {ZIP} and the page section" + (
        f"; {len(extra)} stray file(s) left for you to remove: {extra}" if extra else "")]


def self_test() -> int:
    ok = bad = 0

    def check(name, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {name}")

    with tempfile.TemporaryDirectory() as d:
        r = Path(d) / "tk"
        (r / "shared" / "commands").mkdir(parents=True)
        (r / "shared" / "skills" / "quick-ten").mkdir(parents=True)
        (r / "shared" / "commands" / "audit.md").write_text(
            "---\nallowed-tools: Read\ndescription: x\n---\n\n# /audit\n\n<!-- spawn: none reason=\"x\" -->\nCheck each "
            "citation.\n\n<!-- BEGIN MODEL FAILURE -->\nrules\n<!-- END MODEL FAILURE -->\n\n`/audit` starts no Chair, so "
            "rule 2 never applies here.\n\nDone.\n\n$ARGUMENTS\n", encoding="utf-8")
        (r / "shared" / "commands" / "commit.md").write_text("---\nx: y\n---\n# /commit\n", encoding="utf-8")
        (r / "shared" / "skills" / "quick-ten" / "SKILL.md").write_text("---\nname: quick-ten\n---\n# /quick-ten\nAsk.\n")
        table = {"audit": {"fit": "limited", "note": "Paste the document and the text of each source."},
                 "commit": {"fit": "none", "note": "It reads and writes your git repository."},
                 "quick-ten": {"fit": "full", "note": "Describe what you are about to build."}}
        check("positive control: a complete table has no coverage finding", coverage(r, table) == [])
        check("a command with no row is caught", any("/commit has no row" in x for x in coverage(r, {k: v for k, v in table.items() if k != "commit"})))
        check("a row with no command behind it is caught", any("names no command" in x for x in coverage(r, {**table, "gone": {"fit": "none", "note": "x" * 30}})))
        check("an unknown label is caught", any("fit is" in x for x in coverage(r, {**table, "audit": {"fit": "maybe", "note": "x" * 30}})))
        check("a missing note is caught", any("note is missing" in x for x in coverage(r, {**table, "audit": {"fit": "full", "note": ""}})))
        p = prompt("audit", table["audit"], r / "shared" / "commands" / "audit.md")
        check("the prompt opens with the preface naming the tool", p.startswith('You are running "/audit"'))
        check("the preface says never to claim a check that did not happen", "Never say you ran, read, checked" in p)
        check("a limited tool's note is in the preface", "What works here, and what does not: Paste the document" in p)
        check("frontmatter is removed", "allowed-tools" not in p)
        check("agent markers and HTML comments are removed", "spawn:" not in p and "<!--" not in p)
        check("the model-failure block and its rule-2 line are removed", "rules" not in p and "rule 2 never applies" not in p)
        check("$ARGUMENTS is removed", "$ARGUMENTS" not in p)
        check("the instructions themselves are kept", "Check each citation." in p and "Done." in p)
        site = Path(d) / "site"
        site.mkdir()
        (site / "index.html").write_text(f"<html>\n{BEGIN}\nold\n{END}\n</html>\n", encoding="utf-8")
        code, _ = write_site(r, site, table, check=True)
        check("a site that was never written is stale (exit 1)", code == 1)
        code, _ = write_site(r, site, table, check=False)
        check("writing the site succeeds", code == 0 and (site / "chatbot" / "audit.txt").is_file())
        check("a Claude Code-only tool gets no prompt file", not (site / "chatbot" / "commit.txt").exists())
        page = (site / "index.html").read_text()
        check("each chatbot tool gets one collapsible block", page.count('<details class="chatbot"') == 2)
        check("the Claude Code-only tool is in the table with its reason", "<td><code>/commit</code></td><td>It reads" in page)
        check("text outside the markers is kept", page.startswith("<html>\n") and page.endswith("</html>\n"))
        code, _ = write_site(r, site, table, check=True)
        check("positive control: a site just written passes --check", code == 0)
        (site / "chatbot" / "audit.txt").write_text("edited by hand\n")
        code, why = write_site(r, site, table, check=True)
        check("a hand-edited prompt file is caught", code == 1 and any("audit.txt" in w for w in why))
        write_site(r, site, table, check=False)
        (site / "chatbot" / "old.txt").write_text("x")
        code, why = write_site(r, site, table, check=True)
        check("a prompt file with no tool behind it is caught", code == 1 and any("old.txt" in w for w in why))
        (site / "chatbot" / "old.txt").unlink()
        got = read_zip(site / ZIP) or {}
        check("the ZIP holds every chat prompt and a README", set(got) == {"audit.txt", "quick-ten.txt", "README.txt"})
        check("the ZIP's prompts are the prompt files", got.get("audit.txt") == (site / "chatbot" / "audit.txt").read_text())
        check("the README names each chat tool and each Claude Code-only one, with its note",
              "quick-ten.txt  /quick-ten: Describe" in got.get("README.txt", "") and "/commit: It reads" in got.get("README.txt", ""))
        check("the page links the ZIP", ZIP in (site / "index.html").read_text())
        write_zip(site / ZIP, {**got, "audit.txt": "edited\n"})
        code, why = write_site(r, site, table, check=True)
        check("a ZIP whose files differ is caught", code == 1 and any("zip" in w for w in why))
        (site / ZIP).unlink()
        code, why = write_site(r, site, table, check=True)
        check("a missing ZIP is caught", code == 1 and any("zip" in w for w in why))
        write_site(r, site, table, check=False)
        (site / "index.html").write_text("<html>no markers</html>")
        check("a page with no markers is exit 2", write_site(r, site, table, check=True)[0] == 2)
        (site / "index.html").write_text(f"<html>\n{BEGIN}\n{END}\n</html>\n")
        evil = {**table, "audit": {"fit": "limited", "note": "Paste <script>alert(1)</script> here and more words."}}
        write_site(r, site, evil, check=False)
        check("a note is HTML-escaped on the page", "<script>alert(1)" not in (site / "index.html").read_text().split(SCRIPT)[0])
        write_site(r, site, table, check=False)
        page = (site / "index.html").read_text()
        check("each button, link and prompt box names its tool for a screen reader",
              'aria-label="Copy the /audit prompt"' in page and 'aria-label="Open the /audit prompt as text"' in page
              and 'tabindex="0" role="region" aria-label="Prompt text for /audit"' in page and 'aria-live="polite"' in page)
        check("positive control: with no long prompt, the size note names none", "the longest" not in page)
        linked = {**table, "commit": {"fit": "none", "note": "Its method is at https://example.org/pcv/. It needs git."}}
        write_site(r, site, linked, check=False)
        check("a URL in a Claude Code-only note becomes a link, its full stop outside",
              '<a href="https://example.org/pcv/">https://example.org/pcv/</a>. It needs git.' in (site / "index.html").read_text())
        (r / "shared" / "skills" / "quick-ten" / "SKILL.md").write_text("---\nname: quick-ten\n---\n" + "Ask. " * 7000)
        write_site(r, site, table, check=False)
        page, rd = (site / "index.html").read_text(), (read_zip(site / ZIP) or {}).get("README.txt", "")
        n_long = len((site / "chatbot" / "quick-ten.txt").read_text())
        check("a long prompt is named in the size note, with its length",
              f"The <code>/quick-ten</code> prompt is the longest, about {round(n_long, -3):,} characters; the others are under 10,000." in page)
        check("the README names the long prompt", "quick-ten.txt is the longest" in rd)
    print(f"render_chatbot_prompts self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--self-test" in args:
        return self_test()
    table = load_table(ROOT)
    if table is None:
        print("cannot read shared/chatbot.json", file=sys.stderr)
        return 2
    problems = coverage(ROOT, table)
    for p in problems:
        print(f"  {p}")
    if problems:
        print(f"{len(problems)} problem(s) in shared/chatbot.json")
        return 1
    if "--site" not in args:
        print(f"shared/chatbot.json covers every command and skill ({len(table)} rows) — clean")
        return 0
    i = args.index("--site")
    if i + 1 >= len(args):
        print("usage: --site needs the site's toolkit folder", file=sys.stderr)
        return 2
    code, notes = write_site(ROOT, Path(args[i + 1]), table, check="--check" in args)
    for n in notes:
        print(f"  {n}")
    print("site: " + ("clean" if code == 0 else "stale" if code == 1 else "cannot check"))
    return code


if __name__ == "__main__":
    sys.exit(main())
