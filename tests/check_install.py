#!/usr/bin/env python3
"""Install gate: a real install.sh run into a temporary HOME gives a user every file the commands rely on.

Written for v2.0.2. From v1.1 to v2.0.1 seven commands called a run-report helper the installer never copied, so no
run report ever reached a user, and nothing noticed: the CI step counted installed commands against a typed 15. This
check derives every expectation from install.sh's own arrays and from what the command files call:

  install_failed      install.sh exits non-zero in a mode (default, --minimal, --hooks, --dry-run, a re-install)
  commands            the installed commands are not exactly SHARED_COMMANDS (+ STUDENT_ONLY unless --minimal)
  unshipped_command   a shared/commands/*.md is in neither array, so no install mode ever copies it
  uninstalled_call    a command calls $HOME/.claude/toolkit/scripts/<name>.py and <name> is not in RUNTIME_SCRIPTS
  script_missing      a script a command calls is absent after an install in some mode
  script_broken       the installed run-report helper does not write its row in a temporary project
  clone_path_call     a command calls $TOOLKIT_ROOT or a scripts/ or hooks/ path, which exists only in a clone
  permission          a command calls python3 without Bash(python3:*) in its allowed-tools
  test_file_installed a *_selftest.py or *_mutations.py file lands anywhere under ~/.claude
  hook_missing        --hooks leaves out a runtime hook from hooks/
  pcv_missing         the PCV skill's SKILL.md is not installed
  dry_run_wrote       --dry-run writes any file

Exit codes: 0 clean, 1 findings, 2 usage.
Usage:  python3 tests/check_install.py [ROOT]      python3 tests/check_install.py --self-test
Mutation proof: tests/check_install_mutations.py
"""
from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CALL = re.compile(r'\$HOME/\.claude/toolkit/scripts/([A-Za-z0-9_]+)\.py')
CLONE_CALL = re.compile(r'\$TOOLKIT_ROOT|\b(?:bash|python3)\s+"?(?:\./)?(?:scripts|hooks)/')
TEST_FILE = re.compile(r'_(?:selftest|mutations)\.py$')
MODES = [(), ("--minimal",), ("--hooks",)]


def array(installer: str, name: str) -> list[str]:
    m = re.search(rf"^{name}=\(([^)]*)\)", installer, re.M)
    return m.group(1).split() if m else []


def install(root: Path, home: Path, *flags: str) -> int:
    home.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="checkinstall_cwd_"))  # no CLAUDE.md here for the fragment notice to find
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    env["HOME"] = str(home)
    p = subprocess.run(["bash", str(root / "install.sh"), *flags], cwd=work, env=env,
                       capture_output=True, text=True, timeout=300)
    return p.returncode


def files_under(home: Path) -> list[Path]:
    return [p for p in home.rglob("*") if p.is_file()]


def helper_writes_row(script: Path) -> bool:
    proj = Path(tempfile.mkdtemp(prefix="checkinstall_proj_"))
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_MODEL"}
    env["CLAUDE_PROJECT_DIR"] = str(proj)
    subprocess.run([sys.executable, str(script), "--command", "audit", "--run-dir", str(proj / "r"),
                    "--outcome", "complete", "--task-summary", "install gate"], cwd=proj, env=env,
                   capture_output=True, timeout=60)
    log = proj / ".toolkit" / "evidence" / "run_log.csv"
    if not log.exists():
        return False
    rows = list(csv.reader(open(log, newline="", encoding="utf-8")))
    return len(rows) == 2 and rows[1][1] == "audit"


def static_findings(root: Path, runtime: list[str], shipped: set[str]) -> list[tuple[str, str]]:
    out = []
    for cmd in sorted((root / "shared" / "commands").glob("*.md")):
        text = cmd.read_text(encoding="utf-8")
        if cmd.stem not in shipped:
            out.append(("unshipped_command", cmd.name))
        for name in sorted(set(CALL.findall(text))):
            if name not in runtime:
                out.append(("uninstalled_call", f"{cmd.name} calls {name}.py"))
        for n, line in enumerate(text.splitlines(), 1):
            if CLONE_CALL.search(line):
                out.append(("clone_path_call", f"{cmd.name}:{n}  {line.strip()[:90]}"))
        head = text.split("\n---", 1)[0]
        tools = re.search(r"^allowed-tools:(.*)$", head, re.M)
        if re.search(r"^\s*python3\s", text, re.M) and tools and "Bash(python3:*)" not in tools.group(1):
            out.append(("permission", f"{cmd.name} calls python3 but its allowed-tools lack Bash(python3:*)"))
    return out


def run(root: Path) -> tuple[int, list[tuple[str, str]]]:
    if not (root / "install.sh").is_file() or not (root / "shared" / "commands").is_dir():
        return 2, []
    installer = (root / "install.sh").read_text(encoding="utf-8")
    shared, student, runtime = (array(installer, n) for n in ("SHARED_COMMANDS", "STUDENT_ONLY", "RUNTIME_SCRIPTS"))
    out = static_findings(root, runtime, set(shared) | set(student))
    called = sorted({n for c in (root / "shared" / "commands").glob("*.md")
                     for n in CALL.findall(c.read_text(encoding="utf-8"))})
    hooks = sorted(p.name for p in (root / "hooks").glob("*") if p.suffix in (".sh", ".py") and not TEST_FILE.search(p.name)) \
        if (root / "hooks").is_dir() else []
    base = Path(tempfile.mkdtemp(prefix="checkinstall_"))

    for flags in MODES:
        label = " ".join(flags) or "default"
        home = base / (label.strip("-") or "default")
        if install(root, home, *flags):
            out.append(("install_failed", label))
            continue
        claude = home / ".claude"
        got = sorted(p.stem for p in (claude / "commands").glob("*.md"))
        want = sorted(shared + ([] if "--minimal" in flags else student))
        if got != want:
            out.append(("commands", f"{label}: installed {len(got)}, expected {len(want)}; "
                                    f"missing {sorted(set(want) - set(got))}, extra {sorted(set(got) - set(want))}"))
        for name in called:
            script = claude / "toolkit" / "scripts" / f"{name}.py"
            if not script.is_file():
                out.append(("script_missing", f"{label}: {name}.py"))
            elif name == "emit_run_report" and not helper_writes_row(script):
                out.append(("script_broken", f"{label}: {name}.py wrote no row"))
        for p in files_under(home):
            if TEST_FILE.search(p.name):
                out.append(("test_file_installed", f"{label}: {p.relative_to(home)}"))
        if not (claude / "skills" / "pcv" / "SKILL.md").is_file():
            out.append(("pcv_missing", label))
        if "--hooks" in flags:
            for h in hooks:
                if not (claude / "hooks" / h).is_file():
                    out.append(("hook_missing", h))

    home = base / "upgrade"
    if install(root, home) or install(root, home):
        out.append(("install_failed", "re-install over an existing install"))
    elif any(not (home / ".claude" / "toolkit" / "scripts" / f"{n}.py").is_file() for n in called):
        out.append(("script_missing", "re-install: a called script is gone after the second install"))

    home = base / "dry"
    if install(root, home, "--dry-run"):
        out.append(("install_failed", "--dry-run"))
    wrote = files_under(home)
    if wrote:
        out.append(("dry_run_wrote", f"{len(wrote)} file(s), e.g. {wrote[0].relative_to(home)}"))
    return (1 if out else 0), out


def self_test() -> int:
    ok = bad = 0

    def check(label, cond):
        nonlocal ok, bad
        ok, bad = (ok + 1, bad) if cond else (ok, bad + 1)
        print(f"  {'PASS' if cond else 'FAIL'} {label}")

    def copy():
        d = Path(tempfile.mkdtemp(prefix="checkinstall_tree_")) / "tk"
        shutil.copytree(ROOT, d, ignore=shutil.ignore_patterns(".git"))
        return d

    def defect(rel, old, new):
        """A copy of the real tree with one change; None if the anchor moved (the case then fails, never passes)."""
        d = copy()
        p = d / rel
        text = p.read_text(encoding="utf-8")
        if text.count(old) != 1:
            print(f"  stale anchor in {rel}: {old[:60]!r} found {text.count(old)} times")
            return None
        p.write_text(text.replace(old, new), encoding="utf-8")
        return d

    def kinds(tree):
        return {k for k, _ in run(tree)[1]} if tree else {"<stale anchor>"}

    code, f = run(copy())
    check("the real tree installs clean in every mode (positive control)", code == 0 and not f)
    for k, d in f:
        print(f"      {k}: {d}")

    loop = '    install_file "$TOOLKIT_DIR/scripts/$s.py" "$RUNTIME_DIR/$s.py" "toolkit/scripts/$s.py"'
    check("an installer that never copies the called script is caught",
          "script_missing" in kinds(defect("install.sh", loop, "    :")))
    check("a command calling a script missing from RUNTIME_SCRIPTS is caught",
          "uninstalled_call" in kinds(defect("shared/commands/audit.md", "toolkit/scripts/emit_run_report.py",
                                             "toolkit/scripts/new_helper.py")))
    check("a command calling the clone-only $TOOLKIT_ROOT path is caught",
          "clone_path_call" in kinds(defect("shared/commands/commit.md",
                                            'python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py"',
                                            'bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh"')))
    check("a command calling a repo-relative scripts/ path is caught",
          "clone_path_call" in kinds(defect("shared/commands/help.md",
                                            'python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py"',
                                            "bash scripts/emit_run_report.sh")))
    check("a command calling python3 without the permission is caught",
          "permission" in kinds(defect("shared/commands/runlog.md", "Bash(awk:*), Bash(python3:*), Glob",
                                       "Bash(awk:*), Glob")))
    check("a command file in neither array is caught",
          "unshipped_command" in kinds(defect("install.sh", "SHARED_COMMANDS=(setup coa", "SHARED_COMMANDS=(coa")))
    check("an installer that copies hook test files is caught",
          "test_file_installed" in kinds(defect("install.sh", "*_selftest.py|*_mutations.py) continue ;;",
                                                "*_never_matches_.py) continue ;;")))
    check("a runtime script installed only in the full install is caught in --minimal",
          "script_missing" in kinds(defect("install.sh", 'for s in "${RUNTIME_SCRIPTS[@]}"; do',
                                           'for s in $([ "$MINIMAL" = false ] && echo "${RUNTIME_SCRIPTS[@]}"); do')))
    check("a re-install that backs up the script and never copies the new one is caught",
          "script_missing" in kinds(defect("install.sh", loop,
                                           '    [ -f "$RUNTIME_DIR/$s.py" ] && mv "$RUNTIME_DIR/$s.py" "$RUNTIME_DIR/$s.py.bak" || '
                                           + loop.strip())))
    check("a broken installed helper is caught",
          "script_broken" in kinds(defect("scripts/emit_run_report.py", "            csv.writer(f).writerow(row)",
                                          "            pass")))
    check("a dry run that writes files is caught",
          "dry_run_wrote" in kinds(defect("install.sh", '    mkdir -p "$RUNTIME_DIR"\nfi',
                                          '    mkdir -p "$RUNTIME_DIR"\nfi\nmkdir -p "$RUNTIME_DIR" && : > "$RUNTIME_DIR/x"')))
    check("an installer that exits non-zero is caught",
          "install_failed" in kinds(defect("install.sh", 'echo "Commands installed: $INSTALLED_LIST"',
                                           'echo "Commands installed: $INSTALLED_LIST"; exit 3')))
    check("an installed command set that differs from the arrays is caught",
          "commands" in kinds(defect("install.sh", '    for cmd in "${STUDENT_ONLY[@]}"; do',
                                     '    for cmd in "${STUDENT_ONLY[@]:1}"; do')))
    check("--hooks leaving out a runtime hook is caught",
          "hook_missing" in kinds(defect("install.sh", 'for f in "$TOOLKIT_DIR"/hooks/*.sh "$TOOLKIT_DIR"/hooks/*.py; do',
                                         'for f in "$TOOLKIT_DIR"/hooks/*.sh; do')))
    check("a tree with no install.sh is exit 2", run(Path(tempfile.mkdtemp(prefix="checkinstall_empty_")))[0] == 2)

    print(f"check_install self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT
    code, findings = run(root)
    if code == 2:
        print(f"usage: {root} has no install.sh or shared/commands/")
        return 2
    for kind, detail in findings:
        print(f"{kind:<20} {detail}")
    installer = (root / "install.sh").read_text(encoding="utf-8")
    print(f"\n{len(findings)} finding(s); modes: default, --minimal, --hooks, re-install, --dry-run; "
          f"runtime scripts: {array(installer, 'RUNTIME_SCRIPTS')}" + (" — clean" if code == 0 else ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
