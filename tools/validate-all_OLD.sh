#!/usr/bin/env bash
# Validate every scraper with the repository quality gate.
# Usage: bash tools/validate-all.sh
#
# Runs tools/scraper-quality-gate.sh over every *.yml under scrapers/
# (including scrapers/private/) in deterministic order. Set CS_VALIDATOR_DIR
# to a prepared stashapp/CommunityScrapers checkout to also run the official
# schema validation per file.

set -uo pipefail

FAILED=0

while IFS= read -r scraper; do
  if ! bash tools/scraper-quality-gate.sh "${scraper}"; then
    FAILED=1
  fi
done < <(find scrapers -type f -name '*.yml' | sort)

if [[ "${FAILED}" -ne 0 ]]; then
  echo "Validation failed for one or more scrapers" >&2
  exit 1
fi

echo "All scrapers passed the quality gate"
