#!/usr/bin/env bash
# 擷取器品質閘門
# 用法：bash tools/scraper-quality-gate.sh <擷取器.yml>
#
# 官方 schema 驗證預設使用本倉庫內建的 validator（validator/index.mjs）。
# 設定 CS_VALIDATOR_DIR 可改用上游 stashapp/CommunityScrapers 複製目錄驗證，
# 該目錄需包含：
# - validator/index.mjs
# - validator/scraper.schema.json
# - 已安裝的 Node 依賴
# 未設定 CS_VALIDATOR_DIR 時使用本倉庫 validator；其餘為本倉庫的政策檢查。

set -uo pipefail

SCRAPER_FILE="${1:-}"
FAILED=0

fail() {
  # 中英雙語錯誤訊息，供 validate-all.sh 抽取
  echo "::error file=${SCRAPER_FILE}::$1"
  FAILED=1
}

if [[ -z "${SCRAPER_FILE}" ]]; then
  echo "Usage: bash tools/scraper-quality-gate.sh <scraper.yml>" >&2
  echo "用法：bash tools/scraper-quality-gate.sh <擷取器.yml>" >&2
  exit 2
fi

if [[ ! -f "${SCRAPER_FILE}" ]]; then
  echo "::error::Scraper file not found: ${SCRAPER_FILE}" >&2
  echo "::error::找不到擷取器檔案：${SCRAPER_FILE}" >&2
  exit 2
fi

if [[ "${SCRAPER_FILE}" != scrapers/*.yml ]]; then
  fail "Expected a .yml scraper path under scrapers/ | 預期路徑為 scrapers/ 下的 .yml 擷取器檔案"
fi

# 官方 schema 驗證：預設使用本倉庫內建 validator；
# 設定 CS_VALIDATOR_DIR 可改用上游 stashapp/CommunityScrapers 複製目錄驗證。
VALIDATOR_DIR="${CS_VALIDATOR_DIR:-.}"
if [[ ! -f "${VALIDATOR_DIR}/validator/index.mjs" ]]; then
  echo "::error::validator/index.mjs not found under ${VALIDATOR_DIR} | 在 ${VALIDATOR_DIR} 找不到 validator/index.mjs" >&2
  exit 2
fi
if [[ ! -f "${VALIDATOR_DIR}/validator/scraper.schema.json" ]]; then
  echo "::error::validator/scraper.schema.json not found under ${VALIDATOR_DIR} | 在 ${VALIDATOR_DIR} 找不到 validator/scraper.schema.json" >&2
  exit 2
fi
if [[ -n "${CS_VALIDATOR_DIR:-}" ]]; then
  mkdir -p "${CS_VALIDATOR_DIR}/$(dirname "${SCRAPER_FILE}")"
  cp "${SCRAPER_FILE}" "${CS_VALIDATOR_DIR}/${SCRAPER_FILE}"
  if ! (cd "${CS_VALIDATOR_DIR}" && node validator/index.mjs --ci "${SCRAPER_FILE}"); then
    fail "Official CommunityScrapers schema validation failed | 官方 CommunityScrapers schema 驗證失敗"
  fi
elif ! node validator/index.mjs --ci "${SCRAPER_FILE}"; then
  fail "Schema validation failed (repo validator) | Schema 驗證失敗（本倉庫 validator）"
fi

# XPath 擷取器必須在根層包含非空的 name: 欄位（以行首錨定，排除巢狀 metadata）
if grep -qE '^[[:space:]]*xPathScrapers:' "${SCRAPER_FILE}" && ! grep -qE '^name:[[:space:]]*[^[:space:]#]' "${SCRAPER_FILE}"; then
  fail "XPath scrapers require a non-empty root 'name:' field | XPath 擷取器必須在根層包含非空的 'name:' 欄位"
fi

# sceneByQueryFragment 的 queryURL 必須以 {url} 佔位符帶入原始 URL：
# 允許裸 "{url}" 直通，或把 {url} 嵌進端點樣板（API 擷取器把命中 URL 改寫為
# detail 端點，例如 GAYERDAR 的 api/v2/videos/{url}）。與
# tools/tests/test_scrapers.py 的 test_fragment_mapping_is_optional_but_valid_when_present
# 採用同一條規則。
if grep -qE '^sceneByQueryFragment:' "${SCRAPER_FILE}"; then
  QUERY_FRAGMENT_BLOCK=$(sed -n '/^sceneByQueryFragment:/,/^[^[:space:]#][^:]*:/p' "${SCRAPER_FILE}")
  if ! grep -qE "^[[:space:]]*queryURL:.*\{url\}" <<< "${QUERY_FRAGMENT_BLOCK}"; then
    fail "sceneByQueryFragment queryURL must use the '{url}' placeholder | sceneByQueryFragment 的 queryURL 必須使用 '{url}' 佔位符"
  fi
fi

# All tracked scrapers (including private/) must omit active cookie blocks.
if grep -qE '^[[:space:]]*cookies:[[:space:]]*' "${SCRAPER_FILE}"; then
  fail "Active cookies are not permitted in tracked scrapers"
fi

# parseDate 必須使用 Go 參考時間格式（2006-01-02），拒絕 YYYY/YY/DD 或 %Y/%m/%d 等非 Go 格式
while IFS= read -r layout; do
  [[ -z "${layout}" ]] && continue
  if grep -qiE 'yyyy|yy|dd|%[a-z]' <<< "${layout}"; then
    fail "parseDate must use a Go layout (e.g. 2006-01-02); found '${layout}' | parseDate 必須使用 Go 格式（例如 2006-01-02）；發現 '${layout}'"
  fi
done < <(sed -nE "s/^[[:space:]]*-[[:space:]]*parseDate:[[:space:]]*['\"]?([^'\"[:space:]#]+).*/\1/p" "${SCRAPER_FILE}")

if [[ "${FAILED}" -ne 0 ]]; then
  echo "Quality gate failed: ${SCRAPER_FILE}" >&2
  echo "品質閘門失敗：${SCRAPER_FILE}" >&2
  exit 1
fi

echo "Quality gate passed: ${SCRAPER_FILE}"
echo "品質閘門通過：${SCRAPER_FILE}"
