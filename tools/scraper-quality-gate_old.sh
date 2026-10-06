#!/usr/bin/env bash
# Scraper Quality Gate
# Usage: bash tools/scraper-quality-gate.sh <scraper.yml>
#
# Optional schema validation uses the official stashapp/CommunityScrapers
# validator. Set CS_VALIDATOR_DIR to a prepared upstream checkout containing
# validator/index.mjs, validator/scraper.schema.json, and installed Node
# dependencies. Without it, only the repository policy checks run.

set -uo pipefail

SCRAPER_FILE="${1:-}"
FAILED=0

fail() {
  echo "::error file=${SCRAPER_FILE}::$1"
  FAILED=1
}

if [[ -z "${SCRAPER_FILE}" ]]; then
  echo "Usage: bash tools/scraper-quality-gate.sh <scraper.yml>" >&2
  exit 2
fi

if [[ ! -f "${SCRAPER_FILE}" ]]; then
  echo "::error::Scraper file not found: ${SCRAPER_FILE}" >&2
  exit 2
fi

if [[ "${SCRAPER_FILE}" != scrapers/*.yml ]]; then
  fail "Expected a .yml scraper path under scrapers/: ${SCRAPER_FILE}"
fi

# Optional official schema validation (stashapp/CommunityScrapers).
if [[ -n "${CS_VALIDATOR_DIR:-}" ]]; then
  if [[ ! -f "${CS_VALIDATOR_DIR}/validator/index.mjs" ]]; then
    echo "::error::CS_VALIDATOR_DIR does not contain validator/index.mjs: ${CS_VALIDATOR_DIR}" >&2
    exit 2
  fi
  if [[ ! -f "${CS_VALIDATOR_DIR}/validator/scraper.schema.json" ]]; then
    echo "::error::CS_VALIDATOR_DIR does not contain validator/scraper.schema.json: ${CS_VALIDATOR_DIR}" >&2
    exit 2
  fi
  mkdir -p "${CS_VALIDATOR_DIR}/$(dirname "${SCRAPER_FILE}")"
  cp "${SCRAPER_FILE}" "${CS_VALIDATOR_DIR}/${SCRAPER_FILE}"
  if ! (cd "${CS_VALIDATOR_DIR}" && node validator/index.mjs "${SCRAPER_FILE}"); then
    fail "Official CommunityScrapers validation failed"
  fi
fi

# XPath scrapers must have a non-empty root name. Anchoring at column 0
# excludes nested metadata Name: fields from this check.
if grep -qE '^[[:space:]]*xPathScrapers:' "${SCRAPER_FILE}" && ! grep -qE '^name:[[:space:]]*[^[:space:]#]' "${SCRAPER_FILE}"; then
  fail "XPath scrapers require a non-empty root name: field"
fi

# sceneByQueryFragment is a direct URL scraping path. If declared, it must
# preserve the incoming URL instead of routing it through a search endpoint.
if grep -qE '^sceneByQueryFragment:' "${SCRAPER_FILE}"; then
  QUERY_FRAGMENT_BLOCK=$(sed -n '/^sceneByQueryFragment:/,/^[^[:space:]#][^:]*:/p' "${SCRAPER_FILE}")
  if ! grep -qE "^[[:space:]]*queryURL:[[:space:]]*['\"]?\{url\}['\"]?[[:space:]]*(#.*)?$" <<< "${QUERY_FRAGMENT_BLOCK}"; then
    fail "sceneByQueryFragment must contain queryURL: \"{url}\""
  fi
fi

# Public root scraper files must never contain session cookies. Private files
# under scrapers/private/ are exempt per repository policy.
if [[ "${SCRAPER_FILE}" =~ ^scrapers/[^/]+\.yml$ ]] && grep -qE '^[[:space:]]*cookies:' "${SCRAPER_FILE}"; then
  fail "Public scraper files must not contain driver.cookies; move session-dependent scrapers under scrapers/private/"
fi

# parseDate must use Go reference-time layouts (2006-01-02). Reject common
# non-Go tokens: YYYY/YY/DD (Moment-style) and %Y/%m/%d (strftime-style).
while IFS= read -r layout; do
  [[ -z "${layout}" ]] && continue
  if grep -qiE 'yyyy|yy|dd|%[a-z]' <<< "${layout}"; then
    fail "parseDate must use a Go layout (e.g. 2006-01-02); found ${layout}"
  fi
done < <(sed -nE "s/^[[:space:]]*-[[:space:]]*parseDate:[[:space:]]*['\"]?([^'\"[:space:]#]+).*/\1/p" "${SCRAPER_FILE}")

if [[ "${FAILED}" -ne 0 ]]; then
  echo "Quality gate failed: ${SCRAPER_FILE}" >&2
  exit 1
fi

echo "Quality gate passed: ${SCRAPER_FILE}"
