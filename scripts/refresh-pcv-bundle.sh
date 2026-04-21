#!/bin/bash
# refresh-pcv-bundle.sh — refresh the bundled PCV skill from Kay's upstream repo.
#
# Usage:
#   scripts/refresh-pcv-bundle.sh --version 3.14
#
# Requires explicit --version argument (no default) so the maintainer pins the
# upstream version intentionally. Clones Kay's upstream repo shallow, verifies
# VERSION matches, archives the current bundle to pcv.previous/, rsyncs the new
# files into pcv/, writes upstream provenance metadata, and prints a diff
# summary. Does NOT auto-commit — the maintainer reviews, tests, and commits.
#
# Upstream repo: https://github.com/mgkay/mgkay.github.io
#   PCV files live under mgkay.github.io/pcv/skill/ and mgkay.github.io/pcv/agents/

set -euo pipefail

VERSION=""
while [ $# -gt 0 ]; do
  case "$1" in
    --version) VERSION="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if [ -z "$VERSION" ]; then
  echo "ERROR: --version is required. Example: scripts/refresh-pcv-bundle.sh --version 3.14" >&2
  exit 2
fi

TOOLKIT_ROOT=$(cd "$(dirname "$0")/.." && pwd)
BUNDLE_DIR="$TOOLKIT_ROOT/pcv"
TMP_CLONE=$(mktemp -d -t pcv-refresh-XXXXXXXX)
trap "rm -rf $TMP_CLONE" EXIT

UPSTREAM_REPO="https://github.com/mgkay/mgkay.github.io.git"

echo "=== refresh-pcv-bundle.sh ==="
echo "Toolkit root: $TOOLKIT_ROOT"
echo "Bundle dir:   $BUNDLE_DIR"
echo "Requested version: $VERSION"
echo "Temp clone:   $TMP_CLONE"
echo ""

echo "[1/6] Shallow-cloning upstream repo..."
git clone --depth 1 "$UPSTREAM_REPO" "$TMP_CLONE/upstream" 2>&1 | tail -5

UPSTREAM_PCV="$TMP_CLONE/upstream/pcv"
if [ ! -d "$UPSTREAM_PCV/skill" ] || [ ! -d "$UPSTREAM_PCV/agents" ]; then
  echo "ERROR: upstream repo does not contain expected pcv/skill and pcv/agents directories" >&2
  exit 1
fi

UPSTREAM_VERSION=$(head -1 "$UPSTREAM_PCV/skill/VERSION" | tr -d '[:space:]')
UPSTREAM_SHA=$(cd "$TMP_CLONE/upstream" && git rev-parse HEAD)

echo "[2/6] Upstream VERSION reports: $UPSTREAM_VERSION"
echo "       Upstream commit SHA:      $UPSTREAM_SHA"

if [ "$UPSTREAM_VERSION" != "$VERSION" ]; then
  echo "ERROR: requested --version $VERSION but upstream VERSION is $UPSTREAM_VERSION" >&2
  echo "       Either bump upstream or re-run with --version $UPSTREAM_VERSION" >&2
  exit 1
fi

echo "[3/6] Archiving current bundle to pcv.previous/..."
if [ -d "$BUNDLE_DIR" ]; then
  rm -rf "$TOOLKIT_ROOT/pcv.previous"
  cp -r "$BUNDLE_DIR" "$TOOLKIT_ROOT/pcv.previous"
  echo "       Archived: $TOOLKIT_ROOT/pcv.previous"
else
  echo "       (no existing bundle to archive)"
fi

echo "[4/6] Syncing upstream pcv/ into bundle..."
rm -rf "$BUNDLE_DIR"
mkdir -p "$BUNDLE_DIR"
cp -r "$UPSTREAM_PCV/skill" "$BUNDLE_DIR/skill"
cp -r "$UPSTREAM_PCV/agents" "$BUNDLE_DIR/agents"

echo "[5/6] Writing provenance metadata..."
echo "$UPSTREAM_VERSION" > "$BUNDLE_DIR/.upstream-version"
echo "$UPSTREAM_SHA"     > "$BUNDLE_DIR/.upstream-sha"
date -u +%Y-%m-%dT%H:%M:%SZ > "$BUNDLE_DIR/.upstream-fetched-at"

echo "[6/6] Diff summary vs pcv.previous/:"
if [ -d "$TOOLKIT_ROOT/pcv.previous" ]; then
  added=$(comm -13 \
    <(cd "$TOOLKIT_ROOT/pcv.previous" && find . -type f | sort) \
    <(cd "$BUNDLE_DIR" && find . -type f | sort) | wc -l)
  removed=$(comm -23 \
    <(cd "$TOOLKIT_ROOT/pcv.previous" && find . -type f | sort) \
    <(cd "$BUNDLE_DIR" && find . -type f | sort) | wc -l)
  common=$(comm -12 \
    <(cd "$TOOLKIT_ROOT/pcv.previous" && find . -type f | sort) \
    <(cd "$BUNDLE_DIR" && find . -type f | sort) | wc -l)
  echo "       added:   $added files"
  echo "       removed: $removed files"
  echo "       common:  $common files (may have content changes)"
fi

echo ""
echo "=== DONE ==="
echo "Bundle at: $BUNDLE_DIR"
echo "Provenance: $BUNDLE_DIR/.upstream-version, .upstream-sha, .upstream-fetched-at"
echo ""
echo "NEXT STEPS (not automated — maintainer responsibility):"
echo "  1. Review file diffs:   diff -rq pcv.previous/ pcv/"
echo "  2. Run smoke tests:     scripts/refresh-pcv-bundle.sh does NOT invoke /pcv"
echo "  3. Commit:              git add pcv/ && git commit -m 'chore(pcv): bump bundled PCV to v$VERSION'"
echo "  4. Clean up archive:    rm -rf pcv.previous/ after commit"
