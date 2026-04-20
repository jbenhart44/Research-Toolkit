#!/bin/bash
# rollback-pcv-v314.sh — restore PCV to pre-v3.14 state from the most recent backup tarball.
#
# Usage:
#   bash rollback-pcv-v314.sh           # execute rollback
#   bash rollback-pcv-v314.sh --dry-run # print actions without executing
#
# Restores:
#   ~/.claude/skills/pcv/                (personal PCV skill)
#   ~/.claude/agents/pcv-{builder,critic,research,verifier}.md
#
# Expects the backup tarball at ~/.claude/_backups/pcv-v3.9-YYYYMMDD-HHMMSS.tar.gz
# (created by Phase 1 of the v3.14 migration). Uses the most recent matching tarball.

set -euo pipefail

DRY_RUN=0
if [ "${1:-}" = "--dry-run" ]; then
  DRY_RUN=1
fi

BACKUP_GLOB=~/.claude/_backups/pcv-v3.9-*.tar.gz
LATEST=$(ls -t $BACKUP_GLOB 2>/dev/null | head -1 || true)

if [ -z "$LATEST" ]; then
  echo "ERROR: no backup tarball found matching $BACKUP_GLOB" >&2
  exit 1
fi

echo "Rollback source: $LATEST"
echo "Tarball contents:"
tar tzf "$LATEST" | sed 's/^/  /'

if [ $DRY_RUN -eq 1 ]; then
  echo ""
  echo "DRY-RUN: would remove these paths, then extract the tarball:"
  echo "  ~/.claude/skills/pcv/"
  echo "  ~/.claude/agents/pcv-builder.md"
  echo "  ~/.claude/agents/pcv-critic.md"
  echo "  ~/.claude/agents/pcv-research.md"
  echo "  ~/.claude/agents/pcv-verifier.md"
  echo ""
  echo "DRY-RUN: no changes made."
  exit 0
fi

echo ""
echo "Removing current PCV install..."
rm -rf ~/.claude/skills/pcv/
rm -f ~/.claude/agents/pcv-builder.md \
      ~/.claude/agents/pcv-critic.md \
      ~/.claude/agents/pcv-research.md \
      ~/.claude/agents/pcv-verifier.md

echo "Extracting backup..."
tar xzf "$LATEST" -C ~

echo ""
echo "Rollback complete. Verifying:"
echo "  VERSION: $(cat ~/.claude/skills/pcv/VERSION 2>/dev/null | head -1 || echo MISSING)"
echo "  skill file count: $(find ~/.claude/skills/pcv/ -type f | wc -l)"
echo "  agent file count: $(ls ~/.claude/agents/pcv-*.md 2>/dev/null | wc -l)"
echo ""
echo "Next: run Phase 5 Tier 1 smoke test to confirm restored state is functional."
