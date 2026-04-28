#!/usr/bin/env bash
# fresh_clone_test.sh — verify toolkit commands have no project-specific path defaults.
#
# Smoke: copy the toolkit to /tmp, scan for project-specific tokens, verify the
# frontmatter contract on every command, and confirm no command uses CC_Workflow/
# (or other Jake-specific paths) as a hardcoded default.
#
# Motivated by the 2026-04-27 audit where CC_Workflow/evidence/ was hardcoded as
# the default evidence_dir in runlog.md (8x) and help.md (3x), silently breaking
# /runlog for non-author users until the council's adversarial Red Teamer caught
# it. This test would have caught the bug at write-time.
#
# Exit codes: 0 clean, 1 leak detected, 2 frontmatter violation.

set -uo pipefail

TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

TOOLKIT_ROOT="${TOOLKIT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null)/ai-research-toolkit}"
if [ ! -d "$TOOLKIT_ROOT" ]; then
    echo "FAIL: TOOLKIT_ROOT not found at $TOOLKIT_ROOT" >&2
    exit 2
fi

cp -r "$TOOLKIT_ROOT" "$TMP_DIR/toolkit"
cd "$TMP_DIR/toolkit"

# ── Smoke 1: project-specific tokens in command/script files ──────────────
# Whitelist: refresh-pcv-bundle.sh's "Kay's upstream" attribution (legitimate
# co-author credit per MEMORY.md toolkit_kay_coauthor.md rule).
LEAKS=$(grep -rn -E "CC_Workflow|/mnt/c/Users/17247|jbenhart44\.github\.io|Strategic Driver|Paper [13]|ISE 754|advisor_feedback" \
        shared/commands/ scripts/ toolkit-config.md 2>/dev/null \
        | grep -v "^scripts/refresh-pcv-bundle.sh.*Kay's upstream" \
        || true)
if [ -n "$LEAKS" ]; then
    echo "FAIL: project-specific tokens found in toolkit:"
    echo "$LEAKS"
    exit 1
fi

# ── Smoke 2: frontmatter contract — every command has description + when-to-use ──
MISSING=""
for f in shared/commands/*.md; do
    [ -f "$f" ] || continue
    grep -q "^description:" "$f" || MISSING="$MISSING\n$f: missing description"
    grep -q "> \*\*When to use\*\*:" "$f" || MISSING="$MISSING\n$f: missing When to use"
done
if [ -n "$MISSING" ]; then
    echo -e "FAIL: command frontmatter contract violations:$MISSING"
    exit 2
fi

# ── Smoke 3: no command references CC_Workflow/ as a hardcoded default ────
DEFAULTS=$(grep -rn -i "default.*CC_Workflow\|CC_Workflow.*default" shared/commands/ 2>/dev/null || true)
if [ -n "$DEFAULTS" ]; then
    echo "FAIL: CC_Workflow/ used as a default path (project-specific):"
    echo "$DEFAULTS"
    exit 1
fi

# ── Smoke 4: every command file is parseable as a Claude Code skill ───────
# Frontmatter must be a closed YAML block (--- ... ---) at the top of the file.
# Closing --- must appear within the first 10 lines (frontmatter is short).
# Horizontal-rule --- separators in the body don't count.
BAD_FRONT=""
for f in shared/commands/*.md; do
    [ -f "$f" ] || continue
    head -1 "$f" | grep -q "^---$" || BAD_FRONT="$BAD_FRONT\n$f: missing opening ---"
    # Closing --- in lines 2-10 (search a tight window so body separators don't count)
    sed -n '2,10p' "$f" | grep -q "^---$" || BAD_FRONT="$BAD_FRONT\n$f: missing closing --- in first 10 lines"
done
if [ -n "$BAD_FRONT" ]; then
    echo -e "FAIL: command frontmatter not parseable as YAML block:$BAD_FRONT"
    exit 2
fi

echo "PASS: toolkit clean for fresh-clone install ($(ls shared/commands/*.md 2>/dev/null | wc -l) commands checked)."
exit 0
