#!/bin/bash
# audit_pcv_trigger_sync.sh — Drift detection between SKILL.md and the fragment's /pcv row.
#
# The proactive_fragment.md /pcv row delegates residual stateful behavior
# (suggest-once, decline-don't-repeat) to pcv/skill/SKILL.md §7. This script
# catches the drift case where SKILL.md's trigger language or §7 anchor moves
# without a corresponding fragment update.
#
# Exit codes:
#   0 = clean (no drift detected)
#   1 = drift detected (action needed)
#   2 = files missing or unparseable
#
# Usage:
#   bash scripts/audit_pcv_trigger_sync.sh                 # Full report
#   bash scripts/audit_pcv_trigger_sync.sh --quiet         # Exit code only
#   bash scripts/audit_pcv_trigger_sync.sh --fix-list      # Print actionable fix list

set -euo pipefail

QUIET=false
FIX_LIST=false
while [ $# -gt 0 ]; do
    case "$1" in
        --quiet)    QUIET=true; shift ;;
        --fix-list) FIX_LIST=true; shift ;;
        --help|-h)
            grep -E '^# ' "$0" | sed 's/^# \{0,1\}//' | head -20
            exit 0
            ;;
        *) echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TOOLKIT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SKILL_MD="$TOOLKIT_DIR/pcv/skill/SKILL.md"
FRAGMENT="$TOOLKIT_DIR/shared/proactive_fragment.md"

log() { [ "$QUIET" = true ] || echo "$*"; }

# ─── Pre-flight ───────────────────────────────────────────────────────────────
if [ ! -f "$SKILL_MD" ]; then
    echo "ERROR: SKILL.md not found at $SKILL_MD" >&2
    exit 2
fi
if [ ! -f "$FRAGMENT" ]; then
    echo "ERROR: proactive_fragment.md not found at $FRAGMENT" >&2
    exit 2
fi

# ─── Drift checks ─────────────────────────────────────────────────────────────
DRIFT=0
FIXES=()

# Check 1: SKILL.md must contain the canonical trigger phrase the fragment
# claims to extend ("complex multi-component project").
if ! grep -qiE 'complex multi-component project|complex.{0,40}components' "$SKILL_MD"; then
    DRIFT=1
    log "[drift] SKILL.md no longer contains the 'complex multi-component project' trigger phrasing the fragment cites."
    FIXES+=("Re-read SKILL.md frontmatter; update fragment row 1 Observable to match new SKILL.md trigger text.")
fi

# Check 2: SKILL.md must still have a §7 (or equivalent) anchor for residual
# stateful mechanics. Look for any 'Always opt-in' / 'suggest once' / 'declined'
# behavioral lock language.
if ! grep -qiE 'always opt-in|suggest.{0,20}once|declined.{0,40}(don.?t|do not) repeat' "$SKILL_MD"; then
    DRIFT=1
    log "[drift] SKILL.md no longer contains the 'always opt-in / suggest once / declined-don't-repeat' behavioral lock the fragment delegates to."
    FIXES+=("Restore the behavioral lock section in SKILL.md, OR move the lock language into the fragment row 1 anti-trigger (and remove the scope-clause delegation footer).")
fi

# Check 3: Fragment must still have the scope-clause footer naming SKILL.md as
# the residual-stateful authority.
if ! grep -qE 'pcv/skill/SKILL\.md|SKILL\.md §7' "$FRAGMENT"; then
    DRIFT=1
    log "[drift] proactive_fragment.md no longer cites pcv/skill/SKILL.md as the residual-stateful authority."
    FIXES+=("Restore the scope-clause footer in fragment row 1 that delegates suggest-once / declined-don't-repeat to SKILL.md.")
fi

# Check 4: Fragment row 1 must still reference the on-disk artifact-check
# pattern (pcvplans/charge.md or pcvplans/research_runs/) per the fragment's
# stateless artifact-check policy.
if ! grep -qE 'pcvplans/(charge\.md|research_runs)' "$FRAGMENT"; then
    DRIFT=1
    log "[drift] proactive_fragment.md /pcv row no longer references the pcvplans/ artifact-check anti-trigger."
    FIXES+=("Restore the 'pcvplans/charge.md' / 'pcvplans/research_runs/' anti-trigger reference in fragment row 1.")
fi

# ─── Verdict ──────────────────────────────────────────────────────────────────
if [ "$DRIFT" = 0 ]; then
    log "[ok] /pcv trigger sync verified — no drift between SKILL.md and proactive_fragment.md."
    exit 0
fi

if [ "$FIX_LIST" = true ]; then
    echo "PCV trigger drift detected. Fix list:"
    i=1
    for fix in "${FIXES[@]}"; do
        echo "  ${i}. ${fix}"
        i=$((i+1))
    done
fi

exit 1
