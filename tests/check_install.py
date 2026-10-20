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
  config_overwritten  a re-install changes a toolkit-config.md the user already filled in
  upgrade_stale       with --previous DIR: after installing DIR and then ROOT, an installed command is not ROOT's
  bootstrap_gap       student/bootstrap.md (the in-session installer) has no step for a surface the arrays fill:
                      scripts/ for RUNTIME_SCRIPTS, shared/skills/ for SKILLS, coa/agents/ for SEAT_AGENTS
                      (a static check: the bootstrap is prose and cannot be run here)
  skill_missing       a SKILLS entry is absent after a full install
  skill_in_minimal    a SKILLS entry is installed by --minimal
  seat_missing        a SEAT_AGENTS entry is absent from ~/.claude/agents/ after an install in some mode
  backup_in_skills    a backup folder lands inside ~/.claude/skills/, where it could load as a second skill
  skill_contract      a skill folder holds anything but SKILL.md and assets/, or its SKILL.md name: is not the folder
  unshipped_skill     a folder in shared/skills/ or a file in coa/agents/ that is in neither array
  catalog_gap         a skill not named as /<name> in README.md, shared/commands/help.md and
                      shared/proactive_fragment.md; a seat not named in README.md and shared/commands/coa.md;
                      an OPTIONAL_HOOKS entry not named in hooks/README.md
  unshipped_hook      a runtime file in hooks/ that is not <name>.sh or <name>.py of an OPTIONAL_HOOKS entry, nor
                      <name>.py of a HOOK_LIBS entry, so --hooks never copies it
  hook_without_flag   an install without --hooks puts a hook in ~/.claude/hooks/
  addon_seat          --addon-seats leaves out an ADDON_SEATS entry, an install without it copies one, or a file in
                      coa/agents/addon/ is in no array
  pointer             a POINTER_COMMANDS entry has no shared/pointers/ file, a pointer file is in no array, or it
                      points at a command the arrays do not install
  settings_written    an install writes ~/.claude/settings.json: the installer copies hooks and never registers them

Exit codes: 0 clean, 1 findings, 2 usage.
Usage:  python3 tests/check_install.py [ROOT] [--previous DIR]      python3 tests/check_install.py --self-test
        --previous DIR installs an older checkout first (e.g. a clone at the previous tag), then ROOT over it.
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
MODES = [(), ("--minimal",), ("--hooks",), ("--addon-seats",)]
USER_CONFIG = "# filled in by the user\n## Folder Paths\nevidence_dir: notes/evidence\n"


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


def surface_findings(root: Path, runtime: list[str], skills: list[str], seats: list[str]) -> list[tuple[str, str]]:
    """Contracts for the skill and seat surfaces, and the bootstrap's steps (plan check C14)."""
    out = []
    skill_root = root / "shared" / "skills"
    for d in sorted(p for p in skill_root.glob("*") if p.is_dir()):
        if d.name not in skills:
            out.append(("unshipped_skill", f"shared/skills/{d.name}"))
    for s in skills:
        d = skill_root / s
        if not (d / "SKILL.md").is_file():
            out.append(("skill_contract", f"shared/skills/{s}/SKILL.md is missing"))
            continue
        # __pycache__ is written by running a skill's self-test in the clone; git ignores it and the installer copies
        # only files directly in assets/, so it is never shipped and is not a breach of the folder contract.
        for p in sorted(x for x in d.rglob("*") if x.is_file() and "__pycache__" not in x.parts):
            rel = p.relative_to(d)
            if not (rel.as_posix() == "SKILL.md" or (rel.parts[0] == "assets" and len(rel.parts) == 2)):
                out.append(("skill_contract", f"shared/skills/{s}/{rel.as_posix()} is neither SKILL.md nor assets/<file>"))
        m = re.search(r"^name:\s*(\S+)", (d / "SKILL.md").read_text(encoding="utf-8"), re.M)
        if not m or m.group(1) != s:
            out.append(("skill_contract", f"shared/skills/{s}/SKILL.md name: is {m.group(1) if m else 'missing'}"))
    for p in sorted((root / "coa" / "agents").glob("*.md")):
        if p.stem not in seats:
            out.append(("unshipped_skill", f"coa/agents/{p.name}"))
    for a in seats:
        if not (root / "coa" / "agents" / f"{a}.md").is_file():
            out.append(("seat_missing", f"coa/agents/{a}.md is in SEAT_AGENTS but not in the tree"))

    def text(rel):
        p = root / rel
        return p.read_text(encoding="utf-8") if p.is_file() else ""
    for s in skills:
        for rel in ("README.md", "shared/commands/help.md", "shared/proactive_fragment.md"):
            if f"/{s}" not in text(rel):
                out.append(("catalog_gap", f"/{s} is not named in {rel}"))
    for a in seats:
        for rel in ("README.md", "shared/commands/coa.md"):
            if a not in text(rel):
                out.append(("catalog_gap", f"{a} is not named in {rel}"))
    boot = text("student/bootstrap.md")
    if boot:
        for needed, anchor in ((runtime, "Research-Toolkit/scripts/"), (skills, "Research-Toolkit/shared/skills/"),
                               (seats, "Research-Toolkit/coa/agents/")):
            if needed and anchor not in boot:
                out.append(("bootstrap_gap", f"student/bootstrap.md has no step that copies from {anchor}"))
    return out


def hook_findings(root: Path, optional: list[str], libs: list[str]) -> list[tuple[str, str]]:
    """The hooks surface: every runtime file in hooks/ belongs to an array, every array entry has its files, and
    every optional hook is named in hooks/README.md."""
    out = []
    expected = {f"{h}.{ext}" for h in optional for ext in ("sh", "py")} | {f"{lib}.py" for lib in libs}
    for p in sorted((root / "hooks").glob("*")):
        if p.suffix in (".sh", ".py") and not TEST_FILE.search(p.name) and p.name not in expected:
            out.append(("unshipped_hook", f"hooks/{p.name}"))
    for name in sorted(expected):
        if not (root / "hooks" / name).is_file():
            out.append(("hook_missing", f"hooks/{name} is in an array but not in the tree"))
    readme = root / "hooks" / "README.md"
    text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for h in optional:
        if h not in text:
            out.append(("catalog_gap", f"{h} is not named in hooks/README.md"))
    return out


def addon_pointer_findings(root: Path, addon: list[str], pointers: list[str], installed: set[str]) -> list[tuple[str, str]]:
    """The add-on seats live in coa/agents/addon/ and only there; each pointer file names a command that installs."""
    out = []
    for p in sorted((root / "coa" / "agents" / "addon").glob("*.md")):
        if p.stem not in addon:
            out.append(("addon_seat", f"coa/agents/addon/{p.name} is in no array"))
    for a in addon:
        if not (root / "coa" / "agents" / "addon" / f"{a}.md").is_file():
            out.append(("addon_seat", f"coa/agents/addon/{a}.md is in ADDON_SEATS but not in the tree"))
    for p in sorted((root / "shared" / "pointers").glob("*.md")):
        if p.stem not in pointers:
            out.append(("pointer", f"shared/pointers/{p.name} is in no array"))
    for c in pointers:
        p = root / "shared" / "pointers" / f"{c}.md"
        if not p.is_file():
            out.append(("pointer", f"shared/pointers/{c}.md is in POINTER_COMMANDS but not in the tree"))
            continue
        targets = re.findall(r"is now `?/([a-z0-9-]+)", p.read_text(encoding="utf-8")) or ["?"]
        for t in sorted(set(targets) - installed):
            out.append(("pointer", f"shared/pointers/{c}.md points at /{t}, which no array installs"))
    return out


def upgrade(first: Path, root: Path, home: Path, called: list[str], label: str) -> list[tuple[str, str]]:
    """Install `first`, fill in the config as a user would, install `root` over it, and check what is left."""
    if install(first, home):
        return [("install_failed", f"{label}: the first install")]
    cfg = home / ".claude" / "toolkit-config.md"
    cfg.write_text(USER_CONFIG, encoding="utf-8")
    if install(root, home):
        return [("install_failed", f"{label}: the second install")]
    out = []
    for n in called:
        if not (home / ".claude" / "toolkit" / "scripts" / f"{n}.py").is_file():
            out.append(("script_missing", f"{label}: {n}.py is absent after the second install"))
    if cfg.read_text(encoding="utf-8") != USER_CONFIG:
        out.append(("config_overwritten", f"{label}: toolkit-config.md changed"))
    pairs = [(src, home / ".claude" / "commands" / src.name) for src in sorted((root / "shared" / "commands").glob("*.md"))]
    pairs += [(src, home / ".claude" / "agents" / src.name) for src in sorted((root / "coa" / "agents").glob("*.md"))]
    for src, dst in pairs:
        if dst.is_file() and dst.read_bytes() != src.read_bytes():
            out.append(("upgrade_stale", f"{label}: {src.name} is not the new version"))
    for d in (home / ".claude" / "skills").glob("*"):
        if ".bak" in d.name:
            out.append(("backup_in_skills", f"{label}: {d.relative_to(home)}"))
    return out


def run(root: Path, previous: Path | None = None) -> tuple[int, list[tuple[str, str]]]:
    if not (root / "install.sh").is_file() or not (root / "shared" / "commands").is_dir():
        return 2, []
    installer = (root / "install.sh").read_text(encoding="utf-8")
    shared, student, runtime, skills, seats, optional, libs, addon, pointers = (array(installer, n) for n in (
        "SHARED_COMMANDS", "STUDENT_ONLY", "RUNTIME_SCRIPTS", "SKILLS", "SEAT_AGENTS", "OPTIONAL_HOOKS", "HOOK_LIBS",
        "ADDON_SEATS", "POINTER_COMMANDS"))
    out = static_findings(root, runtime, set(shared) | set(student))
    out += surface_findings(root, runtime, skills, seats)
    out += hook_findings(root, optional, libs)
    out += addon_pointer_findings(root, addon, pointers, set(shared) | set(student))
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
        want = sorted(shared + ([] if "--minimal" in flags else student + pointers))
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
        for s in skills:
            present = (claude / "skills" / s / "SKILL.md").is_file()
            if "--minimal" in flags and present:
                out.append(("skill_in_minimal", f"{label}: {s}"))
            elif "--minimal" not in flags and not present:
                out.append(("skill_missing", f"{label}: {s}"))
        for a in seats:
            if not (claude / "agents" / f"{a}.md").is_file():
                out.append(("seat_missing", f"{label}: {a}.md"))
        for a in addon:
            present = (claude / "agents" / f"{a}.md").is_file()
            if "--addon-seats" in flags and not present:
                out.append(("addon_seat", f"{label}: {a}.md was not copied"))
            elif "--addon-seats" not in flags and present:
                out.append(("addon_seat", f"{label}: {a}.md was copied without --addon-seats"))
        if "--hooks" in flags:
            for h in hooks:
                if not (claude / "hooks" / h).is_file():
                    out.append(("hook_missing", h))
        elif any((claude / "hooks" / h).is_file() for h in hooks):
            out.append(("hook_without_flag", f"{label}: ~/.claude/hooks/ holds a toolkit hook"))
        if (claude / "settings.json").exists():
            out.append(("settings_written", f"{label}: ~/.claude/settings.json was written"))

    out += upgrade(root, root, base / "upgrade", called, "re-install")
    if previous is not None:
        out += upgrade(previous, root, base / "from_previous", called, f"upgrade from {previous.name}")

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
        return edits([(rel, old, new)])

    def edits(changes):
        """A copy with several changes; old=None writes a new file. None if an anchor moved."""
        d = copy()
        for rel, old, new in changes:
            p = d / rel
            if old is None:
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(new, encoding="utf-8")
                continue
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
          "permission" in kinds(defect("shared/commands/run-log.md", "Bash(awk:*), Bash(python3:*), Glob",
                                       "Bash(awk:*), Glob")))
    check("a command file in neither array is caught",
          "unshipped_command" in kinds(defect("install.sh", "SHARED_COMMANDS=(setup coa", "SHARED_COMMANDS=(coa")))
    check("an installer that copies hook test files is caught",
          "test_file_installed" in kinds(defect("install.sh",
                                                '        install_file "$TOOLKIT_DIR/hooks/$l.py" "$HOOKS_DIR/$l.py" "hooks/$l.py"',
                                                '        install_file "$TOOLKIT_DIR/hooks/$l.py" "$HOOKS_DIR/$l.py" "hooks/$l.py"\n'
                                                '        install_file "$TOOLKIT_DIR/hooks/${l}_selftest.py" "$HOOKS_DIR/${l}_selftest.py" "t"')))
    check("a runtime script installed only in the full install is caught in --minimal",
          "script_missing" in kinds(defect("install.sh", 'for s in "${RUNTIME_SCRIPTS[@]}"; do',
                                           'for s in $([ "$MINIMAL" = false ] && echo "${RUNTIME_SCRIPTS[@]}"); do')))
    check("a re-install that backs up the script and never copies the new one is caught",
          "script_missing" in kinds(defect("install.sh", loop,
                                           '    [ -f "$RUNTIME_DIR/$s.py" ] && mv "$RUNTIME_DIR/$s.py" "$RUNTIME_DIR/$s.py.bak" || '
                                           + loop.strip())))
    check("a re-install that overwrites the user's config is caught",
          "config_overwritten" in kinds(defect("install.sh", 'if [ ! -f "$CONFIG_FILE" ]; then', "if true; then")))
    older = defect("shared/commands/audit.md", 'python3 "$HOME/.claude/toolkit/scripts/emit_run_report.py"',
                   'bash "$TOOLKIT_ROOT/scripts/emit_run_report.sh"')
    code, f = run(copy(), older) if older else (None, [])
    check("an upgrade from an older checkout leaves the new commands and the user's config (positive control)",
          code == 0 and not f)
    never_overwrites = defect("install.sh", '        cp "$src" "$dst"\n', '        [ -e "$dst" ] || cp "$src" "$dst"\n')
    check("an upgrade that keeps the old command files is caught",
          bool(never_overwrites and older)
          and "upgrade_stale" in {k for k, _ in run(never_overwrites, older)[1]})
    check("a bootstrap installer with no runtime-scripts step is caught",
          "bootstrap_gap" in kinds(defect("student/bootstrap.md", "Copy each one from `Research-Toolkit/scripts/` to",
                                          "Copy each one to")))
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
          "hook_missing" in kinds(defect("install.sh", "        for ext in sh py; do", "        for ext in sh; do")))
    check("a hook file in no array is caught",
          "unshipped_hook" in kinds(edits([("hooks/extra_guard.py", None, "print('x')\n")])))
    check("an array entry with no hook file is caught",
          "hook_missing" in kinds(defect("install.sh", "OPTIONAL_HOOKS=(usage_counter", "OPTIONAL_HOOKS=(ghost_hook usage_counter")))
    check("a hook installed without --hooks is caught",
          "hook_without_flag" in kinds(defect("install.sh", 'if [ "$INSTALL_HOOKS" = true ]; then\n    HOOKS_DIR=',
                                              'if true; then\n    HOOKS_DIR=')))
    check("an installer that writes settings.json is caught",
          "settings_written" in kinds(defect("install.sh", '        chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null\n    fi',
                                             '        chmod +x "$HOOKS_DIR"/*.sh 2>/dev/null\n        echo "{}" > "$HOME/.claude/settings.json"\n    fi')))
    check("a hook the hooks README does not name is caught",
          "catalog_gap" in kinds(edits([("hooks/README.md", None, "# Hooks\n\nNothing listed.\n")])))
    skill_copy = '            cp "$src/SKILL.md" "$SKILLS_DIR/$s/SKILL.md"'
    check("a skill the full install leaves out is caught",
          "skill_missing" in kinds(defect("install.sh", skill_copy, "            :")))
    check("a skill installed by --minimal is caught",
          "skill_in_minimal" in kinds(defect("install.sh", 'if [ "$MINIMAL" = false ]; then\n    echo ""\n    echo "Installing skills..."',
                                             'if true; then\n    echo ""\n    echo "Installing skills..."')))
    check("a seat agent no install copies is caught",
          "seat_missing" in kinds(defect("install.sh",
                                         '    install_file "$TOOLKIT_DIR/coa/agents/$a.md" "$AGENTS_DIR/$a.md" "agents/$a.md"',
                                         "    :")))
    check("a backup written inside ~/.claude/skills/ is caught",
          "backup_in_skills" in kinds(defect("install.sh", 'cp -r "$SKILLS_DIR/pcv" "$BACKUP_ROOT/skills/pcv"',
                                             'cp -r "$SKILLS_DIR/pcv" "$SKILLS_DIR/pcv.bak.old"')))
    check("a skill folder holding more than SKILL.md and assets/ is caught",
          "skill_contract" in kinds(edits([("shared/skills/quick-ten/BRIEF.md", None, "notes\n")])))
    check("a __pycache__ folder left by a self-test run is not a contract breach",
          "skill_contract" not in kinds(edits([("shared/skills/quick-ten/assets/__pycache__/x.cpython-312.pyc", None, "")])))
    check("a skill whose name: is not its folder is caught",
          "skill_contract" in kinds(defect("shared/skills/quick-ten/SKILL.md", "name: quick-ten", "name: quickten")))
    check("a skill folder in no array is caught",
          "unshipped_skill" in kinds(edits([("shared/skills/extra/SKILL.md", None, "---\nname: extra\n---\n")])))
    check("a seat file in no array is caught",
          "unshipped_skill" in kinds(edits([("coa/agents/coa-extra.md", None, "---\nname: coa-extra\n---\n")])))
    check("a skill /help does not name is caught",
          "catalog_gap" in kinds(defect("shared/commands/help.md", "- `/quick-ten` — before", "- `quick-ten` — before")))
    check("an add-on seat copied without --addon-seats is caught",
          "addon_seat" in kinds(defect("install.sh", 'if [ "$ADDON" = true ]; then\n    for a in',
                                       'if true; then\n    for a in')))
    check("--addon-seats that copies nothing is caught",
          "addon_seat" in kinds(defect("install.sh", '        install_file "$TOOLKIT_DIR/coa/agents/addon/$a.md"',
                                       '        : install_file "$TOOLKIT_DIR/coa/agents/addon/$a.md"')))
    check("an add-on seat file in no array is caught",
          "addon_seat" in kinds(edits([("coa/agents/addon/coa-extra.md", None, "---\nname: coa-extra\n---\n")])))
    check("a pointer to a command no array installs is caught",
          "pointer" in kinds(defect("shared/pointers/runlog.md", "# /runlog is now /run-log", "# /runlog is now /run-logs")))
    check("a pointer file in no array is caught",
          "pointer" in kinds(edits([("shared/pointers/oldname.md", None, "# /oldname is now /audit\n")])))
    check("a seat the README does not name is caught",
          "catalog_gap" in kinds(defect("README.md", "`coa-economist`, ", "")))
    check("a bootstrap with no skills step is caught",
          "bootstrap_gap" in kinds(edits([("student/bootstrap.md", "- skills: each folder in `Research-Toolkit/shared/skills/`\n", ""),
                                          ("student/bootstrap.md", "For each folder in `Research-Toolkit/shared/skills/`, copy",
                                           "For each skill folder, copy")])))
    check("a tree with no install.sh is exit 2", run(Path(tempfile.mkdtemp(prefix="checkinstall_empty_")))[0] == 2)

    print(f"check_install self-test: {ok} passed, {bad} failed")
    return 1 if bad else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()
    args = sys.argv[1:]
    previous = None
    if "--previous" in args:
        i = args.index("--previous")
        if i + 1 >= len(args) or not (Path(args[i + 1]) / "install.sh").is_file():
            print("usage: --previous needs a checkout that has install.sh")
            return 2
        previous = Path(args[i + 1]).resolve()
        args = args[:i] + args[i + 2:]
    root = Path(args[0]).resolve() if args else ROOT
    code, findings = run(root, previous)
    if code == 2:
        print(f"usage: {root} has no install.sh or shared/commands/")
        return 2
    for kind, detail in findings:
        print(f"{kind:<20} {detail}")
    installer = (root / "install.sh").read_text(encoding="utf-8")
    print(f"\n{len(findings)} finding(s); modes: default, --minimal, --hooks, --addon-seats, re-install, --dry-run"
          + (f", upgrade from {previous}" if previous else "") + "; "
          f"runtime scripts: {array(installer, 'RUNTIME_SCRIPTS')}" + (" — clean" if code == 0 else ""))
    return code


if __name__ == "__main__":
    sys.exit(main())
