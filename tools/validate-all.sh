#!/usr/bin/env bash
# 驗證所有擷取器的品質閘門
# 用法：bash tools/validate-all.sh
#
# 對 scrapers/ 下所有 *.yml（含 scrapers/private/）執行品質閘門。
# 設定 CS_VALIDATOR_DIR 指向 stashapp/CommunityScrapers 複製目錄，可額外執行官方 schema 驗證。
# 該目錄需包含 validator/index.mjs、validator/scraper.schema.json 與已安裝的 Node 依賴。
#
# 輸出：
# - 每個擷取器一行：[PASS/FAIL] <路徑>
# - 失敗時附加錯誤原因（第一行）
# - 最終總結：通過/失敗計數與失敗清單

set -uo pipefail

TOTAL=0
PASSED=0
FAILED=0
FAILED_LIST=()

while IFS= read -r scraper; do
  TOTAL=$((TOTAL + 1))
  # 執行品質閘門，捕捉 stdout/stderr
  output=$(bash tools/scraper-quality-gate.sh "${scraper}" 2>&1)
  rc=$?
  if [[ $rc -eq 0 ]]; then
    PASSED=$((PASSED + 1))
    echo "[PASS] ${scraper}"
  else
    FAILED=$((FAILED + 1))
    # 從輸出中抽取第一行錯誤訊息（去掉 ::error 前綴）
    first_error=$(echo "${output}" | grep -m1 '::error' | sed 's/^::error file=[^:]*:://' | sed 's/^::error:://')
    if [[ -z "${first_error}" ]]; then
      first_error="quality gate failed (exit=$rc)"
    fi
    echo "[FAIL] ${scraper}: ${first_error}"
    FAILED_LIST+=("${scraper}")
  fi
done < <(find scrapers -type f -name '*.yml' | sort)

echo ""
echo "========================================"
echo "Summary / 總結"
echo "========================================"
echo "Total / 總數   : ${TOTAL}"
echo "Passed / 通過  : ${PASSED}"
echo "Failed / 失敗  : ${FAILED}"

if [[ ${#FAILED_LIST[@]} -gt 0 ]]; then
  echo ""
  echo "Failed scrapers / 失敗的擷取器:"
  for f in "${FAILED_LIST[@]}"; do
    echo "  - ${f}"
  done
  echo ""
  echo "Validation failed for ${FAILED} scraper(s). See individual [FAIL] lines above for details."
  echo "驗證失敗，共 ${FAILED} 個擷取器。詳情請見上方 [FAIL] 行。"
  exit 1
fi

echo ""
echo "All scrapers passed the quality gate."
echo "所有擷取器已通過品質閘門。"
