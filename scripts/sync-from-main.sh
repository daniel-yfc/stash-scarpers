#!/bin/bash
# sync-from-main.sh — Regenerate standalone skill content from main (Phase 1 of METHODOLOGY.md).
#
# Usage: ./scripts/sync-from-main.sh [main-ref]
#   main-ref defaults to origin/main. Run from the standalone-skill branch checkout.
#   This script performs the MECHANICAL extraction only. Manual reframing
#   (METHODOLOGY.md §5) must be reviewed after each run.
#
# What it does:
#   1. Archives skills/stash-scraper-builder from the given main ref into a temp dir.
#   2. Copies SKILL.md -> ./SKILL.md (overwrites; metadata.version must be bumped manually).
#   3. Syncs references/ (deletes skill-read-order.md per methodology).
#   4. Reports files that need manual reframe review.
# What it does NOT do:
#   - Touch assets/, scripts/, tools/, LICENSE, configs (curated, not mirrored).
#   - Rewrite repo-only links (manual, see METHODOLOGY.md §5).
set -euo pipefail

MAIN_REF="${1:-origin/main}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

if ! git rev-parse --verify "$MAIN_REF" >/dev/null 2>&1; then
  echo "error: cannot resolve main ref '$MAIN_REF'" >&2
  exit 1
fi

echo "==> Extracting skills/stash-scraper-builder from $MAIN_REF"
git archive "$MAIN_REF" skills/stash-scraper-builder | tar -x -C "$WORK"
SRC="$WORK/skills/stash-scraper-builder"

echo "==> Promoting SKILL.md"
cp "$SRC/SKILL.md" ./SKILL.md

echo "==> Syncing references/ (excluding skill-read-order.md)"
mkdir -p references
# remove files that no longer exist upstream (except locally curated ones)
for f in references/*; do
  base="$(basename "$f")"
  if [ "$base" != "scraper.schema.json" ] && [ ! -e "$SRC/references/$base" ]; then
    echo "    - removing stale $f"
    rm -f "$f"
  fi
done
for f in "$SRC"/references/*; do
  base="$(basename "$f")"
  [ "$base" = "skill-read-order.md" ] && continue
  cp "$f" "references/$base"
done

echo ""
echo "==> Manual reframe review needed (METHODOLOGY.md §5):"
echo "    1. Bump metadata.version in SKILL.md to the source date."
echo "    2. diff references/ against $MAIN_REF and check:"
echo "       - repo-only links (../docs/, ../tools/, validator/, .github/)"
echo "       - commands assuming repo tooling (npm run ..., bash tools/...)"
echo "       - references to repo governance docs"
echo "    3. Run Phase 4 validation: prettier, scripts self-test, leakage grep."
echo ""
echo "    Quick leakage check:"
if grep -rn --include="*.md" -E "skills/stash-scraper-builder|docs/0[1-7]_|validator/index|\.github/" SKILL.md references/ 2>/dev/null; then
  echo "    ^^^ LEAKAGE FOUND — fix before committing."
else
  echo "    clean."
fi
