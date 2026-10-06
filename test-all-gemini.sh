#!/usr/bin/env bash
# test-all.sh - Stash 擷取器整合測試套件 / Integrated Test Suite
# 位置：專案根目錄（與 validator/、tools/、scrapers/ 同層）
# 執行：bash test-all.sh
#
# 設計重點：
# - 不使用 set -e：單一檢查失敗只計入失敗數，不會中止整體流程
# - run_check 統一包裝：以 if 直接取得退出碼
# - 自動修正 CRLF 與 tools/*.sh 執行權限
# - Python 依賴預設使用 --break-system-packages --user；失敗才退回 venv
# - 每次執行建立獨立日誌：./.log/runs/<時間>/
# - 最新執行捷徑：./.log/latest/
# - scrutiny 保留每個 scraper 的完整 log，並產生完整合併報告

set -uo pipefail

# ---------- 專案與日誌 ----------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_BASE="${PROJECT_ROOT}/.log"
RUN_ID="$(date '+%Y%m%d-%H%M%S')"
LOGDIR="${LOG_BASE}/runs/${RUN_ID}"

mkdir -p "$LOGDIR"
ln -sfn "$RUN_ID" "${LOG_BASE}/latest"
ln -sfn "${LOG_BASE}/latest" "${LOG_BASE}/latest-run"

SESSION_LOG="${LOGDIR}/run.log"

# ---------- 樣式 ----------
readonly RED=$'\033[0;31m'
readonly GREEN=$'\033[0;32m'
readonly YELLOW=$'\033[1;33m'
readonly BLUE=$'\033[0;34m'
readonly CYAN=$'\033[0;36m'
readonly BOLD=$'\033[1m'
readonly NC=$'\033[0m'

# ---------- 計數 ----------
total=0
passed=0
failed=0
skipped=0
warnings=0
failed_labels=()

# ---------- 旗標 ----------
INTERACTIVE=false
LANG_ZH_TW=true
VERBOSE=false
USE_VENV=false
SKIP_SCRUTINY=false
SKIP_DEPS=false
SKIP_VALIDATOR=false
SKIP_TESTS=false
SKIP_DOCS=false

# ---------- Python ----------
PY="python3"

# ---------- 基本函數 ----------
ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

logline() {
  [[ -n "$SESSION_LOG" ]] || return 0
  printf '[%s] [%s] %s\n' "$(ts)" "$1" "$2" >> "$SESSION_LOG"
}

# t <中文> <英文>
t() {
  if $LANG_ZH_TW; then
    printf '%s' "$1"
  else
    printf '%s' "$2"
  fi
}

usage() {
  cat <<EOF
用法：$(basename "$0") [選項]

選項：
  -h, --help          顯示說明
  -i, --interactive   互動模式（每區段確認）
  -e, --en            英文輸出
  -v, --verbose       顯示檢查輸出；scrutiny 會顯示完整內容
  --skip-deps         跳過依賴安裝（npm / pip）
  --skip-validator    跳過驗證器檢查
  --skip-tests        跳過 Python 測試集
  --skip-docs         跳過文件檢查
  --skip-scrutiny     跳過網站實測
  --quick             快速模式（= --skip-deps --skip-docs --skip-scrutiny）
  --venv              強制使用 Python venv
  --ci                CI 模式（verbose、非互動）

Python 依賴策略：
  預設：python3 -m pip install --break-system-packages --user
  失敗時：自動退回 .venv
  強制 venv：--venv

日誌：
  每次執行：./.log/runs/<時間>/
  執行日誌：./.log/runs/<時間>/run.log
  最新捷徑：./.log/latest/
  完整網站實測：./.log/latest/scrutiny.log
  單一 scraper：./.log/latest/scrutiny-<名稱>.log

範例：
  bash test-all.sh
  bash test-all.sh --quick
  bash test-all.sh -i -v
  cat .log/latest/run.log
  less .log/latest/scrutiny.log
EOF
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage ;;
    -i|--interactive) INTERACTIVE=true ;;
    -e|--en) LANG_ZH_TW=false ;;
    -v|--verbose) VERBOSE=true ;;
    --skip-deps) SKIP_DEPS=true ;;
    --skip-validator) SKIP_VALIDATOR=true ;;
    --skip-tests) SKIP_TESTS=true ;;
    --skip-docs) SKIP_DOCS=true ;;
    --skip-scrutiny) SKIP_SCRUTINY=true ;;
    --quick)
      SKIP_DEPS=true
      SKIP_DOCS=true
      SKIP_SCRUTINY=true
      ;;
    --venv) USE_VENV=true ;;
    --ci)
      VERBOSE=true
      INTERACTIVE=false
      ;;
    *)
      echo "未知選項：$1"
      usage
      ;;
  esac
  shift
done

# ---------- 顯示函數 ----------
section() {
  echo ""
  echo "${BLUE}========================================================${NC}"
  echo "${BLUE} ${BOLD}$(t "$1" "$2")${NC}"
  echo "${BLUE}========================================================${NC}"

  total=$((total + 1))
  logline "SECTION" "$(t "$1" "$2")"
}

info() {
  echo "${CYAN}[INFO] $1${NC}"
  logline "INFO" "$1"
}

skip_msg() {
  echo "${YELLOW}[SKIP] $1${NC}"
  skipped=$((skipped + 1))
  logline "SKIP" "$1"
}

warn_msg() {
  echo "${YELLOW}[WARN] $1${NC}"
  warnings=$((warnings + 1))
  logline "WARN" "$1"
}

confirm() {
  local section_name="$1"
  local prompt

  if ! $INTERACTIVE; then
    return 0
  fi

  prompt="$(t \
    "[$section_name] 繼續？(y/n)" \
    "[$section_name] Continue? (y/n)")"

  read -r -p "$prompt " -n 1
  echo

  [[ "${REPLY:-}" =~ ^[Yy]$ ]]
}

# ---------- 日誌解析 ----------
extract_failed_files() {
  local log="$1"

  grep -E '\.yml Valid: false$' "$log" 2>/dev/null \
    | sed 's/ Valid: false$//' \
    | sed "s|^$PROJECT_ROOT/||" \
    | head -n 5
}

print_scrutiny_summary() {
  local log="$1"
  local summary
  local ok_count
  local skip_count
  local fail_count

  [[ -f "$log" ]] || return 0

  summary="$(sed -n '/^========== SUMMARY ==========/,$p' "$log")"

  if [[ -z "$summary" ]]; then
    echo "${YELLOW}  $(t \
      "未找到 scrutiny SUMMARY 區塊" \
      "scrutiny SUMMARY block not found")${NC}"
    return 0
  fi

  ok_count="$(
    printf '%s\n' "$summary" \
      | grep -c '^OK[[:space:]]' || true
  )"

  skip_count="$(
    printf '%s\n' "$summary" \
      | grep -c '^SKIP[[:space:]]' || true
  )"

  fail_count="$(
    printf '%s\n' "$summary" \
      | grep -Ec '^(FETCH_FAIL|NO_SCENE_SCRAPER|ERROR)[[:space:]]' || true
  )"

  echo "${CYAN}--- $(t "網站實測摘要" "Live scrutiny summary") ---${NC}"
  echo "  ${GREEN}OK${NC}: $ok_count"
  echo "  ${YELLOW}SKIP${NC}: $skip_count"
  echo "  ${RED}FAIL${NC}: $fail_count"

  if [[ "$fail_count" -gt 0 ]]; then
    echo "  $(t "失敗項目" "Failed items"):"

    printf '%s\n' "$summary" \
      | grep -E '^(FETCH_FAIL|NO_SCENE_SCRAPER|ERROR)[[:space:]]' \
      | head -n 10 \
      | while IFS= read -r line; do
          echo "    - $line"
        done
  fi

  echo "${CYAN}---${NC}"
}

# run_check <標籤> <日誌名> <指令...>
run_check() {
  local label="$1"
  local logname="$2"
  shift 2

  local log="$LOGDIR/${logname}.log"
  local rc=0
  local rel_log="${log#$PROJECT_ROOT/}"

  if "$@" >"$log" 2>&1; then
    passed=$((passed + 1))

    echo "${GREEN}[通過] $label${NC}"
    echo "${YELLOW} $(t "詳情" "details"): $rel_log${NC}"

    logline "PASS" "$label (log=$log)"

    if [[ "$logname" == scrutiny-* ]]; then
      print_scrutiny_summary "$log"
    elif $VERBOSE; then
      tail -n 25 "$log"
    fi

    return 0
  fi

  rc=$?
  failed=$((failed + 1))
  failed_labels+=("$label")

  echo "${RED}[失敗] $label${NC} (exit=$rc)"
  echo "${YELLOW} $(t "詳情" "details"): $rel_log${NC}"

  logline "FAIL" "$label (exit=$rc, log=$log)"

  if [[ "$logname" == scrutiny-* ]]; then
    print_scrutiny_summary "$log"

  elif [[ "$logname" == "validator" ]]; then
    local additional_count
    local required_count

    additional_count="$(
      grep -c '^ADDTIONAL PROPERTY' "$log" 2>/dev/null || true
    )"

    required_count="$(
      grep -c '^REQUIRED' "$log" 2>/dev/null || true
    )"

    echo "${CYAN}--- $(t "錯誤摘要" "Error summary") ---${NC}"

    if [[ "$additional_count" -gt 0 ]]; then
      echo "  ${RED}✗${NC} ADDITIONAL PROPERTY: $additional_count"
    fi

    if [[ "$required_count" -gt 0 ]]; then
      echo "  ${RED}✗${NC} REQUIRED: $required_count"
    fi

    echo "  $(t "失敗檔案" "Failed files"):"

    extract_failed_files "$log" | while IFS= read -r file; do
      echo "    - $file"
    done

    echo "${CYAN}---${NC}"

  else
    echo "${CYAN}--- $(t "錯誤摘要" "Error summary") ---${NC}"

    grep -E \
      '^(Documentation|ERROR|FAILED|AssertionError|Traceback|ADDTIONAL|REQUIRED)' \
      "$log" 2>/dev/null \
      | head -n 5 \
      | while IFS= read -r line; do
          echo "  $line"
        done

    echo "${CYAN}---${NC}"
  fi

  if $VERBOSE; then
    if [[ "$logname" == scrutiny-* ]]; then
      cat "$log"
    else
      tail -n 40 "$log"
    fi
  fi

  return 1
}

# ---------- 修正 CRLF 與權限 ----------
fix_crlf_and_permissions() {
  local fixed=0
  local file

  for file in "$PROJECT_ROOT"/*.sh "$PROJECT_ROOT"/tools/*.sh; do
    [[ -f "$file" ]] || continue

    if grep -q $'\r' "$file"; then
      sed -i 's/\r$//' "$file"
      fixed=$((fixed + 1))
    fi
  done

  chmod +x "$PROJECT_ROOT"/tools/*.sh 2>/dev/null || true

  if [[ "$fixed" -eq 0 ]]; then
    passed=$((passed + 1))
    echo "${GREEN}[通過] $(t \
      "CRLF 檢查：無需修正" \
      "CRLF check: nothing to fix")${NC}"
    logline "PASS" "CRLF check: nothing to fix"
  else
    warn_msg "$(t \
      "已自動修正 $fixed 個檔案的 CRLF" \
      "auto-fixed CRLF in $fixed file(s)")"
  fi
}

# ---------- 主流程 ----------
main() {
  local directory
  local local_fc
  local scraper
  local scraper_name
  local scraper_logname
  local scraper_log
  local combined_scrutiny_log
  local scraper_count
  local all_passed

  cd "$PROJECT_ROOT" || exit 1

  logline "START" \
    "test-all.sh $(t "開始執行" "started") (root=$PROJECT_ROOT) (run=$RUN_ID)"

  echo "${CYAN}"
  echo "+------------------------------------------------------+"
  echo "| $(t "整合測試套件" "Integrated Test Suite") - stash-scrapers |"
  echo "+------------------------------------------------------+"
  echo "${NC}"

  echo "$(t "專案根目錄" "Project root"): $PROJECT_ROOT"
  echo "$(t "執行日誌" "Run log"): ${SESSION_LOG#$PROJECT_ROOT/}"
  echo "$(t "檢查日誌" "Check logs"): ${LOGDIR#$PROJECT_ROOT/}"
  echo "$(t "最新捷徑" "Latest symlink"): .log/latest/"

  # ---------- 前置檢查 ----------
  for directory in validator tools scrapers; do
    if [[ ! -d "$directory" ]]; then
      echo "${RED}[失敗 / Failed] $(t \
        "找不到 $directory/，請在專案根目錄執行" \
        "missing $directory/, run from repository root")${NC}"

      logline "FAIL" "missing directory: $directory"
      exit 1
    fi
  done

  # ---------- 0. CRLF / 權限 ----------
  section "0. CRLF / 權限修正" "0. CRLF / Permission Fix"
  info "$(t \
    "檢查並修正所有 .sh 檔的 CRLF 與執行權限" \
    "Check and fix CRLF and execute permissions for all .sh files")"

  fix_crlf_and_permissions

  # ---------- 1. 環境 ----------
  section "1. 環境檢查" "1. Environment Check"
  info "$(t \
    "確認 Node.js、npm、Python 3 已安裝" \
    "Verify Node.js, npm, and Python 3 are installed")"

  if ! command -v node >/dev/null 2>&1; then
    echo "${RED}[失敗 / Failed] Node.js $(t "未安裝" "missing")${NC}"
    logline "FAIL" "Node.js missing"
    exit 1
  fi

  if ! command -v npm >/dev/null 2>&1; then
    echo "${RED}[失敗 / Failed] npm $(t "未安裝" "missing")${NC}"
    logline "FAIL" "npm missing"
    exit 1
  fi

  if ! command -v python3 >/dev/null 2>&1; then
    echo "${RED}[失敗 / Failed] Python 3 $(t "未安裝" "missing")${NC}"
    logline "FAIL" "python3 missing"
    exit 1
  fi

  echo "${GREEN}[通過] Node.js $(node --version)${NC}"
  echo "${GREEN}[通過] npm $(npm --version)${NC}"
  echo "${GREEN}[通過] $("$PY" --version 2>&1)${NC}"

  logline "PASS" "Node.js $(node --version)"
  logline "PASS" "npm $(npm --version)"
  logline "PASS" "$("$PY" --version 2>&1)"

  confirm "$(t "環境" "Environment")" || exit 1

  # ---------- 2. 依賴 ----------
  if ! $SKIP_DEPS; then
    section "2. 安裝依賴" "2. Dependencies Installation"
    info "$(t \
      "安裝 Node.js 與 Python 依賴套件" \
      "Install Node.js and Python dependencies")"

    if [[ -f package-lock.json ]]; then
      run_check "npm ci" "npm-ci" npm ci
    else
      run_check "npm install" "npm-install" npm install --prefer-offline
    fi

    if $USE_VENV; then
      info "$(t "使用 venv（--venv）" "Using venv (--venv)")"

      if [[ ! -x ".venv/bin/python" ]]; then
        python3 -m venv .venv
      fi

      if [[ -x ".venv/bin/python" ]]; then
        PY=".venv/bin/python"

        run_check \
          "$(t "pip install（venv）" "pip install (venv)")" \
          "pip-install" \
          "$PY" -m pip install --quiet --upgrade pip \
          -r requirements.txt pyyaml jsonschema
      else
        failed=$((failed + 1))
        failed_labels+=("$(t "venv 建立" "venv creation")")

        echo "${RED}[失敗 / Failed] $(t \
          "venv 建立失敗" \
          "venv creation failed")${NC}"

        logline "FAIL" "venv creation failed"
      fi
    else
      if run_check \
        "$(t \
          "pip install（--break-system-packages）" \
          "pip install (--break-system-packages)")" \
        "pip-install" \
        python3 -m pip install --quiet --break-system-packages --user \
        -r requirements.txt pyyaml jsonschema; then
        :
      else
        warn_msg "$(t \
          "系統 pip 安裝失敗，改用 venv" \
          "System pip installation failed; falling back to venv")"

        if [[ ! -x ".venv/bin/python" ]]; then
          python3 -m venv .venv
        fi

        if [[ -x ".venv/bin/python" ]]; then
          PY=".venv/bin/python"

          run_check \
            "$(t "pip install（venv 退回）" "pip install (venv fallback)")" \
            "pip-venv" \
            "$PY" -m pip install --quiet --upgrade pip \
            -r requirements.txt pyyaml jsonschema
        else
          failed=$((failed + 1))
          failed_labels+=("$(t "venv 建立" "venv creation")")

          echo "${RED}[失敗 / Failed] $(t \
            "venv 建立也失敗" \
            "venv creation also failed")${NC}"

          logline "FAIL" "venv creation also failed"
        fi
      fi
    fi

    confirm "$(t "依賴" "Dependencies")" || exit 1
  else
    section "2. 安裝依賴" "2. Dependencies Installation"
    skip_msg "$(t "已跳過 --skip-deps" "Skipped (--skip-deps)")"
  fi

  # ---------- 3. 安全性 ----------
  section "3. 安全性檢查" "3. Security Self-Assessment"
  info "$(t \
    "檢查 Python、Shell、JavaScript 工具腳本的安全性" \
    "Check Python, Shell, and JavaScript tool scripts for security risks")"

  run_check \
    "$(t \
      "安全性檢查－Python、Shell、JavaScript" \
      "Security check - Python, Shell, JavaScript")" \
    "self-eval" \
    "$PY" tools/self_evaluate.py

  confirm "$(t "安全性檢查" "Security Check")" || exit 1

  # ---------- 4. 文件 ----------
  if ! $SKIP_DOCS; then
    section "4. 文件檢查" "4. Documentation Checks"
    info "$(t \
      "檢查文件索引與 YAML 範例結構" \
      "Check documentation index and YAML example structure")"

    run_check \
      "$(t "文件－範例結構" "Documentation - example structure")" \
      "scraper-docs" \
      "$PY" tools/check_scraper_docs.py

    run_check \
      "$(t "文件－索引清單" "Documentation - index list")" \
      "docs-index" \
      "$PY" tools/check_docs_index.py

    confirm "$(t "文件檢查" "Documentation Check")" || exit 1
  else
    section "4. 文件檢查" "4. Documentation Checks"
    skip_msg "$(t "已跳過 --skip-docs" "Skipped (--skip-docs)")"
  fi

  # ---------- 5. 驗證器 ----------
  if ! $SKIP_VALIDATOR; then
    section "5. 驗證器檢查" "5. Validator Checks"
    info "$(t \
      "執行結構驗證、URL 排序、政策檢查" \
      "Run schema validation, URL sorting, and policy compliance checks")"

    # -s 已包含結構驗證，避免與純 schema 驗證重複。
    run_check \
      "$(t \
        "驗證器－結構與 URL 排序" \
        "Validator - schema & URL sorting")" \
      "validator" \
      node validator/index.mjs -a -s --ci

    run_check \
      "$(t "政策檢查" "Policy check")" \
      "gate" \
      bash tools/validate-all.sh

    confirm "$(t "驗證器檢查" "Validator Checks")" || exit 1
  else
    section "5. 驗證器檢查" "5. Validator Checks"
    skip_msg "$(t "已跳過 --skip-validator" "Skipped (--skip-validator)")"
  fi

  # ---------- 6. Python 測試 ----------
  if ! $SKIP_TESTS; then
    section "6. Python 測試集" "6. Python Test Suite"
    info "$(t \
      "執行 tools/tests/ 下的所有 pytest 測試" \
      "Run all pytest tests under tools/tests/")"

    if run_check \
      "$(t "Python 測試集" "Python test suite")" \
      "pytest" \
      "$PY" -m pytest tools/tests -v; then
      :
    else
      local_fc="$(grep -c 'FAILED' "$LOGDIR/pytest.log" 2>/dev/null || true)"
      echo "${YELLOW} $(t "失敗測試數" "Failed tests"): ${local_fc:-?}${NC}"
    fi

    confirm "$(t "測試" "Tests")" || exit 1
  else
    section "6. Python 測試集" "6. Python Test Suite"
    skip_msg "$(t "已跳過 --skip-tests" "Skipped (--skip-tests)")"
  fi

  # ---------- 7. 網站實測 ----------
  if ! $SKIP_SCRUTINY; then
    section "7. 網站實測" "7. Live Scrutiny"
    info "$(t \
      "對公開擷取器執行實際網站 XPath 驗證" \
      "Test public scrapers against live websites with XPath validation")"

    mapfile -t public_scrapers < <(
      find scrapers -maxdepth 1 -type f -name '*.yml' -print | sort
    )

    if [[ "${#public_scrapers[@]}" -gt 0 ]]; then
      scraper_count="${#public_scrapers[@]}"

      info "$(t \
        "將測試 $scraper_count 個公開擷取器" \
        "Will test $scraper_count public scrapers")"

      all_passed=true
      combined_scrutiny_log="$LOGDIR/scrutiny.log"

      {
        echo "# Scrutiny combined report"
        echo "# Run ID: $RUN_ID"
        echo "# Generated: $(ts)"
        echo "# Public scrapers: $scraper_count"
        echo
      } > "$combined_scrutiny_log"

      for scraper in "${public_scrapers[@]}"; do
        scraper_name="$(basename "$scraper" .yml)"
        scraper_logname="scrutiny-${scraper_name}"
        scraper_log="$LOGDIR/${scraper_logname}.log"

        if ! run_check \
          "$(t "網站實測" "Live scrutiny")-${scraper_name}" \
          "$scraper_logname" \
          node tools/scrutiny.js "$scraper" --search; then
          all_passed=false
        fi

        {
          echo
          echo "================================================================"
          echo "## $scraper"
          echo "================================================================"
          echo

          if [[ -f "$scraper_log" ]]; then
            cat "$scraper_log"
          else
            echo "[MISSING LOG] $scraper_log"
          fi
        } >> "$combined_scrutiny_log"
      done

      echo ""
      echo "${CYAN}$(t \
        "完整網站實測報告" \
        "Full live-scrutiny report"): ${combined_scrutiny_log#$PROJECT_ROOT/}${NC}"

      logline "INFO" "full scrutiny report: $combined_scrutiny_log"

      if ! $all_passed; then
        warn_msg "$(t \
          "部分擷取器網站實測失敗；完整結果見 scrutiny.log" \
          "Some scrapers failed live scrutiny; see scrutiny.log for full results")"
      fi
    else
      skip_msg "$(t \
        "無公開擷取器可供實測" \
        "No public scrapers found for scrutiny")"
    fi

    confirm "$(t "網站實測" "Live Scrutiny")" || exit 1
  else
    section "7. 網站實測" "7. Live Scrutiny"
    skip_msg "$(t "已跳過 --skip-scrutiny" "Skipped (--skip-scrutiny)")"
  fi

  # ---------- 總結 ----------
  echo ""
  echo "${CYAN}========================================================${NC}"
  echo "${CYAN} ${BOLD}$(t "測試總結" "Test Summary")${NC}"
  echo "${CYAN}========================================================${NC}"
  echo ""

  echo " $(t "總計區段" "Sections") : $total"
  echo " ${GREEN}$(t "通過" "Passed")${NC} : $passed"
  echo " ${RED}$(t "失敗" "Failed")${NC} : $failed"
  echo " ${YELLOW}$(t "跳過" "Skipped")${NC} : $skipped"
  echo " $(t "警告" "Warnings") : $warnings"
  echo " $(t "Python 直譯器" "Python interpreter") : $PY"
  echo ""

  logline "SUMMARY" \
    "sections=$total passed=$passed failed=$failed skipped=$skipped warnings=$warnings python=$PY"

  if [[ "${#failed_labels[@]}" -gt 0 ]]; then
    echo " ${RED}$(t "失敗項目" "Failed items")${NC}:"

    for label in "${failed_labels[@]}"; do
      echo " - $label"
    done

    echo ""
  fi

  if [[ "$failed" -eq 0 ]]; then
    echo "${GREEN}== $(t "所有檢查通過" "All checks passed") ==${NC}"
    echo "$(t "執行日誌" "Run log"): ${SESSION_LOG#$PROJECT_ROOT/}"
    echo "$(t "最新捷徑" "Latest symlink"): .log/latest/"

    if [[ -f "$LOGDIR/scrutiny.log" ]]; then
      echo "$(t "完整網站實測" "Full live scrutiny"): .log/latest/scrutiny.log"
    fi

    logline "END" "all checks passed"
    exit 0
  fi

  echo "${RED}== $(t "部分檢查失敗" "Some checks failed") ==${NC}"
  echo ""
  echo "$(t "修復建議" "Fix suggestions"):"

  echo "  1. $(t \
    "驗證器或 URL 排序失敗：檢查 ./.log/latest/validator.log" \
    "Validator or URL sorting failed: see ./.log/latest/validator.log")"

  echo "  2. $(t \
    "文件檢查失敗：檢查 ./.log/latest/scraper-docs.log" \
    "Documentation check failed: see ./.log/latest/scraper-docs.log")"

  echo "  3. $(t \
    "Python 測試失敗：檢查 ./.log/latest/pytest.log" \
    "Python tests failed: see ./.log/latest/pytest.log")"

  echo "  4. $(t \
    "網站實測完整結果：檢查 ./.log/latest/scrutiny.log" \
    "Full live scrutiny results: see ./.log/latest/scrutiny.log")"

  echo "  5. $(t \
    "使用 -v 或 --ci 查看更多即時輸出" \
    "Use -v or --ci to show more immediate output")"

  echo ""
  echo "$(t "執行日誌" "Run log"): ${SESSION_LOG#$PROJECT_ROOT/}"
  echo "$(t "最新捷徑" "Latest symlink"): .log/latest/"

  logline "END" "some checks failed"
  exit 1
}

main