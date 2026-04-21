#!/bin/bash
# check-pcv-upstream.sh — detect drift between bundled PCV and upstream.
#
# Exits 0 if bundled version matches upstream; exits 1 on drift.
# Intended for CLAUDE.md audit-flag table and periodic maintenance.
#
# Usage:
#   scripts/check-pcv-upstream.sh           # normal check
#   scripts/check-pcv-upstream.sh --quiet   # summary only
#
# Upstream lookup strategy: GitHub raw URL for the VERSION file on main branch.
# Low bandwidth (single HEAD/GET). No clone.

set -euo pipefail

QUIET=0
if [ "${1:-}" = "--quiet" ]; then
  QUIET=1
fi

TOOLKIT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUNDLE_DIR="$TOOLKIT_ROOT/pcv"

UPSTREAM_VERSION_URL="https://raw.githubusercontent.com/mgkay/mgkay.github.io/main/pcv/skill/VERSION"

if [ ! -f "$BUNDLE_DIR/.upstream-version" ]; then
  echo "ERROR: $BUNDLE_DIR/.upstream-version missing — refresh-pcv-bundle.sh has not been run" >&2
  exit 1
fi

BUNDLED=$(head -1 "$BUNDLE_DIR/.upstream-version" | tr -d '[:space:]')

UPSTREAM_RAW=$(curl -fsSL "$UPSTREAM_VERSION_URL" 2>/dev/null | head -1 | tr -d '[:space:]')

if [ -z "$UPSTREAM_RAW" ]; then
  echo "ERROR: could not fetch upstream VERSION from $UPSTREAM_VERSION_URL" >&2
  exit 1
fi

if [ $QUIET -eq 0 ]; then
  echo "Bundled PCV version:  $BUNDLED"
  echo "Upstream PCV version: $UPSTREAM_RAW"
fi

if [ "$BUNDLED" = "$UPSTREAM_RAW" ]; then
  [ $QUIET -eq 0 ] && echo "OK: bundle matches upstream."
  exit 0
else
  echo "DRIFT: bundled v$BUNDLED differs from upstream v$UPSTREAM_RAW"
  echo "       Run: scripts/refresh-pcv-bundle.sh --version $UPSTREAM_RAW"
  exit 1
fi
