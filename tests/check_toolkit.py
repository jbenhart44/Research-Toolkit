#!/usr/bin/env python3
"""Release gate for the toolkit tree: command contract, and nothing machine-specific or secret.

Replaces tests/smoke/fresh_clone_test.sh (v1.x), which was a bash grep over a hand-picked token list
that skipped coa/, docs/ and pcv/. This check scans the whole tree (only .git is skipped) for things
that are wrong in ANY fork of this toolkit, so it can run in public CI:

  frontmatter    every shared/commands/*.md opens with ---, closes within lines 2-10, and carries
                 `description:` and `> **When to use**:`
  home_path      an absolute home directory (/Users/<name>, /home/<name>, /mnt/<drive>/Users/<name>,
                 C:\\Users\\<name>) — a path that only works on one machine
  credential     a token shape (GitHub, Anthropic, AWS, Slack, a private-key block, a bearer token)
  email          an address outside ALLOWED_EMAIL_DOMAINS / ALLOWED_EMAILS
  private_token  a line of YOUR private-token file: project names, course codes, folder names that
                 must never ship. One regular expression per line; blank lines and # comments are
                 ignored. pcv/ is not scanned for these (it is the upstream bundle). The file is read
                 from --tokens FILE, else $TOOLKIT_PRIVATE_TOKENS, else ~/.claude/toolkit-private-tokens.txt.
                 It lives outside the repository on purpose: a list of private terms is itself private.
                 With no file the scan is reported as SKIPPED, never as clean; a file that was named
                 but is missing is exit 2.

Exit codes: 0 clean, 1 findings, 2 usage.
Usage:  python3 tests/check_toolkit.py [ROOT] [--tokens FILE]      python3 tests/check_toolkit.py --self-test
Mutation proof: tests/check_toolkit_mutations.py
"""
from __future__ import annotations

import os
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOME_PATH = re.compile(r"(?:/Users/|/home/|/mnt/[a-z]/Users/)[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[A-Za-z0-9._-]+")
HOME_OK = {"/Users/you", "/home/you", "/Users/username", "/home/username", "/Users/name", "/home/user"}
CREDENTIAL = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-ant-[A-Za-z0-9_-]{10,}|AKIA[0-9A-Z]{16}"
                        r"|xox[abpr]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|Bearer\s+[A-Za-z0-9._-]{24,}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})")
ALLOWED_EMAIL_DOMAINS = {"example.com", "example.org", "example.net", "anthropic.com", "users.noreply.github.com"}
ALLOWED_EMAILS = {"jebenhar@ncsu.edu"}
TOKENS_ENV = "TOOLKIT_PRIVATE_TOKENS"
DEFAULT_TOKENS = Path.home() / ".claude" / "toolkit-private-tokens.txt"
TOKEN_SKIP_DIRS = {"pcv"}


SELF = Path(__file__).resolve()


def load_tokens(path: Path) -> list[tuple[str, re.Pattern]]:
    """(pattern text, compiled) for each non-blank, non-comment line of a private-token file."""
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.append((line, re.compile(line)))
    return out


def resolve_tokens(argv: list[str], env: dict, default: Path) -> tuple[int, Path | None, str]:
    """(exit code, token file or None, how it was found). A file named by flag or env must exist."""
    if "--tokens" in argv:
        i = argv.index("--tokens")
        if i + 1 >= len(argv):
            return 2, None, "--tokens needs a file"
        p = Path(argv[i + 1]).expanduser()
        return (0, p, "--tokens") if p.is_file() else (2, None, f"--tokens file not found: {p}")
    if env.get(TOKENS_ENV):
        p = Path(env[TOKENS_ENV]).expanduser()
        return (0, p, f"${TOKENS_ENV}") if p.is_file() else (2, None, f"${TOKENS_ENV} file not found: {p}")
    return (0, default, "default") if default.is_file() else (0, None, "no token file")


def token_status(tokens: list | None, source: str) -> str:
    if tokens is None:
        return f"private-token scan: SKIPPED ({source}; see --tokens)"
    return f"private-token scan: {len(tokens)} pattern(s) from {source}"


def text_files(root: Path):
    """Every text file under root except .git/ and this checker itself (its self-test fixtures are
    deliberate bad examples; skipping the file by resolved path keeps them from flagging the tree)."""
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if ".git" in rel.parts or not p.is_file() or p.resolve() == SELF:
            continue
        data = p.read_bytes()
        if b"\x00" in data[:8192]:
            continue
        yield rel.as_posix(), data.decode("utf-8", errors="replace")


def check_frontmatter(root: Path) -> list[tuple[str, int, str, str]]:
    out = []
    for p in sorted((root / "shared" / "commands").glob("*.md")):
        rel = p.relative_to(root).as_posix()
        lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
        text = "\n".join(lines)
        if not lines or lines[0] != "---":
            out.append((rel, 1, "frontmatter", "missing opening ---"))
        elif "---" not in lines[1:10]:
            out.append((rel, 1, "frontmatter", "missing closing --- in lines 2-10"))
        if not re.search(r"^description:", text, re.M):
            out.append((rel, 0, "frontmatter", "missing description:"))
        if "> **When to use**:" not in text:
            out.append((rel, 0, "frontmatter", "missing > **When to use**:"))
    return out


def check_content(root: Path) -> list[tuple[str, int, str, str]]:
    out = []
    for rel, text in text_files(root):
        for n, line in enumerate(text.splitlines(), 1):
            for m in HOME_PATH.finditer(line):
                if m.group(0) not in HOME_OK:
                    out.append((rel, n, "home_path", m.group(0)))
            for m in CREDENTIAL.finditer(line):
                out.append((rel, n, "credential", m.group(0)[:12] + "…"))
            for m in EMAIL.finditer(line):
                addr, dom = m.group(0).lower(), m.group(1).lower()
                if addr not in ALLOWED_EMAILS and not any(dom == d or dom.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS):
                    out.append((rel, n, "email", m.group(0)))
    return out


def check_tokens(root: Path, tokens: list[tuple[str, re.Pattern]]) -> list[tuple[str, int, str, str]]:
    out = []
    for rel, text in text_files(root):
        if set(Path(rel).parts[:-1]) & TOKEN_SKIP_DIRS:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for pat, rx in tokens:
                m = rx.search(line)
                if m:
                    out.append((rel, n, "private_token", m.group(0)))
    return out


def run(root: Path, tokens: list | None = None) -> tuple[int, list]:
    if not (root / "shared" / "commands").is_dir():
        return 2, [("usage", 0, "usage", f"{root} has no shared/commands/")]
    findings = check_frontmatter(root) + check_content(root) + check_tokens(root, tokens or [])
    return (1 if findings else 0), findings


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    good_cmd = "---\ndescription: does a thing\n---\n\n> **When to use**: when you need it\n\nBody.\n"

    def tree(files):
        d = Path(tempfile.mkdtemp(prefix="checktoolkit_"))
        for rel, body in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(body if isinstance(body, bytes) else body.encode())
        return d

    base = {"shared/commands/a.md": good_cmd, "README.md": "Install it. Contact jebenhar@ncsu.edu or dev@example.com\n"}
    code, f = run(tree(base))
    check("a clean tree passes (positive control)", code == 0 and not f)

    def kinds(files):
        return {k for _, _, k, _ in run(tree({**base, **files}))[1]}

    check("a command without description is caught", "frontmatter" in kinds({"shared/commands/b.md": good_cmd.replace("description: does a thing\n", "")}))
    check("a command without 'When to use' is caught", "frontmatter" in kinds({"shared/commands/b.md": good_cmd.replace("> **When to use**: when you need it\n", "")}))
    check("a command with no opening --- is caught", "frontmatter" in kinds({"shared/commands/b.md": good_cmd[4:]}))
    check("frontmatter closing after line 10 is caught", "frontmatter" in kinds({"shared/commands/b.md": "---\n" + "x: 1\n" * 12 + "---\n> **When to use**: x\ndescription: y\n"}))
    check("a real home path is caught", "home_path" in kinds({"docs.md": "run python3 /Users/alice/proj/x.py"}))
    wsl = run(tree({**base, "x.sh": "cd /mnt/c/Users/alice/OneDrive"}))[1]
    check("a WSL home path is caught as the full /mnt/c/Users/... form", any(k == "home_path" and h.startswith("/mnt/c/Users/") for _, _, k, h in wsl))
    check("a Windows home path is caught", "home_path" in kinds({"x.md": "C:\\Users\\alice\\proj"}))
    code, _ = run(tree({**base, "docs.md": "run python3 /Users/alice/proj/x.py"}))
    check("a content finding makes the exit code 1", code == 1)
    code, _ = run(tree({**base, "shared/commands/b.md": good_cmd.replace("description: does a thing\n", "")}))
    check("a frontmatter finding makes the exit code 1", code == 1)
    check("a placeholder home path is allowed", not kinds({"x.md": "e.g. /Users/you/project or /home/user/x"}) - {"frontmatter"})
    check("a generic WSL mount check is allowed", not kinds({"x.sh": 'grep -qE "/mnt/c/.*/OneDrive"'}))
    check("a credential shape is caught", "credential" in kinds({"cfg.env": "TOKEN=ghp_abcdefghijklmnopqrstuvwx1234"}))
    check("a private email is caught", "email" in kinds({"x.md": "write to someone@private.org"}))
    check("the allowlisted public address is allowed", not kinds({"x.md": "jebenhar@ncsu.edu"}))
    check("a file in docs/, coa/ or pcv/ is scanned too", "home_path" in kinds({"pcv/skill/x.md": "/home/alice/x"}))
    code, f = run(tree({"README.md": "no commands dir"}))
    check("a tree with no shared/commands is exit 2", code == 2)

    tok_dir = Path(tempfile.mkdtemp(prefix="checktoolkit_tokens_"))
    tok_file = tok_dir / "tokens.txt"
    tok_file.write_text("# my private project names\n\nSecret Project\nCOURSE 1[0-9]{2}\n", encoding="utf-8")
    toks = load_tokens(tok_file)
    check("comments and blank lines in the token file are ignored", [t for t, _ in toks] == ["Secret Project", "COURSE 1[0-9]{2}"])
    code, f = run(tree({**base, "notes.md": "see the Secret Project folder"}), toks)
    check("a private token from the token file is caught", code == 1 and any(k == "private_token" and h == "Secret Project" for _, _, k, h in f))
    code, f = run(tree({**base, "x.md": "homework for COURSE 154"}), toks)
    check("a token line is a regular expression", any(k == "private_token" and h == "COURSE 154" for _, _, k, h in f))
    code, f = run(tree({**base, "pcv/skill/x.md": "Secret Project"}), toks)
    check("a token inside pcv/ is not a finding (the upstream bundle)", code == 0)
    code, f = run(tree({**base, "x.md": "a different project"}), toks)
    check("a tree without the tokens passes the token scan", code == 0)
    missing = tok_dir / "nope.txt"
    check("a missing --tokens file is exit 2, never a skip", resolve_tokens(["--tokens", str(missing)], {}, missing)[0] == 2)
    check("a missing $TOOLKIT_PRIVATE_TOKENS file is exit 2", resolve_tokens([], {TOKENS_ENV: str(missing)}, missing)[0] == 2)
    check("--tokens wins over the environment", resolve_tokens(["--tokens", str(tok_file)], {TOKENS_ENV: str(missing)}, missing)[:2] == (0, tok_file))
    check("the default file is used when present", resolve_tokens([], {}, tok_file)[:2] == (0, tok_file))
    check("no token file anywhere is reported as SKIPPED, never as clean",
          resolve_tokens([], {}, missing)[:2] == (0, None) and "SKIPPED" in token_status(None, "no token file"))

    print(f"check_toolkit self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    args = sys.argv[1:]
    tcode, tfile, source = resolve_tokens(args, dict(os.environ), DEFAULT_TOKENS)
    if tcode:
        print(f"usage: {source}")
        return tcode
    tokens = load_tokens(tfile) if tfile else None
    if "--tokens" in args:
        i = args.index("--tokens")
        args = args[:i] + args[i + 2:]
    root = Path(args[0]) if args else ROOT
    code, findings = run(root, tokens)
    for rel, n, kind, hit in findings:
        print(f"{kind:<14} {rel}:{n}  {hit}")
    n_cmd = len(list((root / "shared" / "commands").glob("*.md"))) if code != 2 else 0
    print(f"\n{token_status(tokens, source)}")
    print(f"{len(findings)} finding(s); {n_cmd} commands checked" + (" — clean" if code == 0 else ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
