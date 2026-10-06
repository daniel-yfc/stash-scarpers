#!/usr/bin/env bash
# test-all.sh - Stash 擷取器整合測試套件 / Integrated Test Suite
# 位置：專案根目錄（與 validator/、tools/、scrapers/ 同層）
# 執行：bash test-all.sh

# 設計重點：
# - 不使用 set -e：單一檢查失敗只計入失敗數，不會中止整體流程
# - run_check 統一包裝：直接以 if 取得退出碼，避免 PIPESTATUS 假陽性
# - 自動修正 CRLF 與 tools/*.sh 執行權限
# - Python 依賴原則用 --break-system-packages --user；失敗才退回 venv
# - 每次執行獨立日誌：./.log/runs/<時間>/ 資料夾
# - 最新執行捷徑：./.log/latest/ 符號連結

set -uo pipefail

# ---------- 專案根目錄與日誌目錄 ----------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_BASE="${PROJECT_ROOT}/.log"
RUN_ID="$(date '+%Y%m%d-%H%M%S')"
LOGDIR="${LOG_BASE}/runs/${RUN_ID}"

# ---------- 樣式 ----------
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'
BLUE=$'\033[0;34m'; CYAN=$'\033[0;36m'; BOLD=$'\033[1m'; NC=$'\033[0m'

# ---------- 計數 ----------
TOTAL=0; PASSED=0; FAILED=0; SKIPPED=0; WARNINGS=0
FAILED_LABELS=()

# ---------- 旗標 ----------
INTERACTIVE=false
LANG_ZH_TW=true
VERBOSE=false
USE_VENV=false
SKIP_SCRUTINY=false

SESSION_LOG=""

# ---------- 日誌 ----------
ts() { date '+%Y-%m-%d %H:%M:%S'; }

logline() {
[[ -n "$SESSION_LOG" ]] || return 0
printf '[%s] [%s] %s\n' "$(ts)" "$1" "$2" >> "$SESSION_LOG"
}

usage() {
echo "用法：$(basename "$0") [選項]"
echo ""
echo "選項："
echo " -h, --help 顯示說明"
echo " -i, --interactive 互動模式（每區段確認）"
echo " -e, --en 英文輸出"
echo " -v, --verbose 顯示各檢查輸出結尾"
echo " --skip-deps 跳過依賴安裝（npm / pip）"
echo " --skip-validator 跳過驗證器檢查"
echo " --skip-tests 跳過 Python 測試集"
echo " --skip-docs 跳過文件檢查"
echo " --skip-scrutiny 跳過網站實測"
echo " --quick 快速模式（= --skip-deps --skip-docs --skip-scrutiny）"
echo " --venv 強制使用 Python venv（例外路徑）"
echo " --ci CI 模式（verbose、非互動）"
echo ""
echo "Python 依賴策略："
echo " 預設 --break-system-packages --user（系統 pip）"
echo " 失敗時自動退回 .venv；--venv 可強制直接走 venv"
echo ""
echo "日誌："
echo " 每次執行獨立日誌：./.log/runs/<時間>/"
echo " 執行日誌（通過/失敗 + 時間戳）：./.log/runs/<時間>/run.log"
echo " 各檢查完整輸出：./.log/runs/<時間>/<檢查名>.log"
echo " 最新執行捷徑：./.log/latest/ -> runs/<時間>/"
echo ""
echo "範例："
echo " bash test-all.sh # 完整執行"
echo " bash test-all.sh --quick # 快速檢查（不含 npm / 文件 / 網站實測）"
echo " bash test-all.sh -i -v # 互動 + 詳細"
echo " cat .log/latest/run.log # 查看最新執行摘要"
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
--quick) SKIP_DEPS=true; SKIP_DOCS=true; SKIP_SCRUTINY=true ;;
--venv) USE_VENV=true ;;
--ci) VERBOSE=true; INTERACTIVE=false ;;
*) echo "未知選項：$1"; usage ;;
esac
shift
done

# ---------- 輸出輔助 ----------
t() {
if $LANG_ZH_TW; then printf '%s' "$1"; else printf '%s' "$2"; fi
}

section() {
echo ""
echo "${BLUE}========================================================${NC}"
echo "${BLUE} ${BOLD}$(t "$1" "$2")${NC}"
echo "${BLUE}========================================================${NC}"
TOTAL=$((TOTAL + 1))
logline "SECTION" "$(t "$1" "$2")"
}

info() {
echo "${CYAN}[說明] $1${NC}"
logline "INFO" "$1"
}

skip_msg() {
echo "${YELLOW}[SKIP] $1${NC}"
SKIPPED=$((SKIPPED + 1))
logline "SKIP" "$1"
}

warn_msg() {
echo "${YELLOW}[WARN] $1${NC}"
WARNINGS=$((WARNINGS + 1))
logline "WARN" "$1"
}

confirm() {
if $INTERACTIVE; then
read -p "[$1] $(t "繼續？(y/n)" "Continue? (y/n)") " -n 1 -r
echo
[[ $REPLY =~ ^[Yy]$ ]] || return 1
fi
return 0
}

# run_check <標籤> <日誌名> <指令...>
run_check() {
local label="$1" logname="$2"; shift 2
local log="$LOGDIR/$logname.log"
local rc=0
if "$@" >"$log" 2>&1; then
PASSED=$((PASSED + 1))
echo "${GREEN}[通過] $label${NC}"
logline "PASS" "$label"
if $VERBOSE; then tail -n 25 "$log"; fi
return 0
fi
rc=$?
FAILED=$((FAILED + 1))
FAILED_LABELS+=("$label")
echo "${RED}[失敗] $label${NC} (exit=$rc)"
echo "${YELLOW} $(t "詳情" "details"): $log${NC}"
logline "FAIL" "$label (exit=$rc, log=$log)"
if $VERBOSE; then tail -n 40 "$log"; fi
return 1
}

# ---------- 主流程 ----------
main() {
# 建立日誌目錄
mkdir -p "$LOGDIR"

# 更新 latest 符號連結
ln -sfn "$RUN_ID" "${LOG_BASE}/latest"
ln -sfn "${LOG_BASE}/latest" "${LOG_BASE}/latest-run"

SESSION_LOG="$LOGDIR/run.log"
logline "START" "test-all.sh $(t "開始執行" "started") (root=$PROJECT_ROOT) (run=$RUN_ID)"

echo "${CYAN}"
echo "+------------------------------------------------------+"
echo "| $(t "整合測試套件" "Integrated Test Suite") - stash-scarpers |"
echo "+------------------------------------------------------+"
echo "${NC}"
echo "$(t "專案根目錄" "Project root"): $PROJECT_ROOT"
echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
echo "$(t "檢查日誌" "Check logs"): $LOGDIR"
echo "$(t "最新捷徑" "Latest symlink"): ${LOG_BASE}/latest/"

# 前置檢查：目錄結構
for d in validator tools scrapers; do
if [[ ! -d "$d" ]]; then
echo "${RED}[失敗] $(t "找不到 $d/，請在專案根目錄執行" "missing $d/, run from repo root")${NC}"
logline "FAIL" "missing directory: $d"
exit 1
fi
done

# ========== 0. CRLF / 權限修正 ==========
section "0. CRLF / 權限修正" "0. CRLF / Permission Fix"
info "$(t "檢查並修正所有 .sh 檔的 CRLF 與執行權限" "Check and fix CRLF and execute permissions for all .sh files")"
fix_crlf() {
local fixed=0
local f
for f in "$PROJECT_ROOT"/*.sh "$PROJECT_ROOT"/tools/*.sh; do
[[ -f "$f" ]] || continue
if grep -q $'\r' "$f"; then
sed -i 's/\r$//' "$f"
info "CRLF $(t "已修正" "fixed"): ${f#$PROJECT_ROOT/}"
fixed=$((fixed + 1))
fi
done
chmod +x "$PROJECT_ROOT"/tools/*.sh 2>/dev/null
if [[ $fixed -eq 0 ]]; then
PASSED=$((PASSED + 1))
echo "${GREEN}[通過] $(t "CRLF 檢查：無需修正" "CRLF check: nothing to fix")${NC}"
logline "PASS" "CRLF check: nothing to fix"
else
warn_msg "$(t "已自動修正 $fixed 個檔案的 CRLF" "auto-fixed CRLF in $fixed file(s)")"
fi
}
fix_crlf

# Python 直譯器：預設系統 python3
PY="python3"

# ========== 1. 環境檢查 ==========
section "1. 環境檢查" "1. Environment Check"
info "$(t "確認 Node.js、npm、Python 3 已安裝" "Verify Node.js, npm, and Python 3 are installed")"
if ! command -v node >/dev/null 2>&1; then
echo "${RED}[失敗] Node.js $(t "未安裝" "missing")${NC}"; logline "FAIL" "Node.js missing"; exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
echo "${RED}[失敗] npm $(t "未安裝" "missing")${NC}"; logline "FAIL" "npm missing"; exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
echo "${RED}[失敗] Python 3 $(t "未安裝" "missing")${NC}"; logline "FAIL" "python3 missing"; exit 1
fi
echo "${GREEN}[通過] Node.js $(node --version)${NC}"
echo "${GREEN}[通過] npm $(npm --version)${NC}"
echo "${GREEN}[通過] $("$PY" --version 2>&1)${NC}"
logline "PASS" "Node.js $(node --version)"
logline "PASS" "npm $(npm --version)"
logline "PASS" "$("$PY" --version 2>&1)"
confirm "$(t "環境" "Environment")" || exit 1

# ========== 2. 安裝依賴 ==========
section "2. 安裝依賴" "2. Dependencies Installation"
info "$(t "安裝 Node.js 與 Python 依賴套件" "Install Node.js and Python dependencies")"
if [[ "${SKIP_DEPS:-false}" != true ]]; then
if [[ -f package-lock.json ]]; then
run_check "npm ci" npm-ci npm ci
else
run_check "npm install" npm-install npm install --prefer-offline
fi

if $USE_VENV; then
info "$(t "使用 venv（--venv）" "using venv (--venv)")"
if [[ ! -x ".venv/bin/python" ]]; then
python3 -m venv .venv
fi
if [[ -x ".venv/bin/python" ]]; then
PY=".venv/bin/python"
run_check "pip install（venv）" pip-install \
"$PY" -m pip install --quiet --upgrade pip -r requirements.txt pyyaml jsonschema
else
echo "${RED}[失敗] $(t "venv 建立失敗" "venv creation failed")${NC}"
logline "FAIL" "venv creation failed"
fi
else
if run_check "pip install（--break-system-packages）" pip-install \
python3 -m pip install --quiet --break-system-packages --user \
-r requirements.txt pyyaml jsonschema; then
:
else
warn_msg "$(t "系統 pip 失敗，退回 venv" "system pip failed, falling back to venv")"
if [[ ! -x ".venv/bin/python" ]]; then
python3 -m venv .venv
fi
if [[ -x ".venv/bin/python" ]]; then
PY=".venv/bin/python"
run_check "pip install（venv 退回）" pip-venv \
"$PY" -m pip install --quiet --upgrade pip -r requirements.txt pyyaml jsonschema
else
echo "${RED}[失敗] $(t "venv 建立也失敗" "venv creation also failed")${NC}"
logline "FAIL" "venv creation also failed"
fi
fi
fi
confirm "$(t "依賴" "Dependencies")" || exit 1
else
section "2. 安裝依賴" "2. Dependencies Installation"
skip_msg "$(t "已跳過 --skip-deps" "skipped (--skip-deps)")"
fi

# ========== 3. 安全性檢查 ==========
section "3. 安全性檢查" "3. Security Self-Assessment"
info "$(t "檢查 Python、Shell、JavaScript 工具腳本的安全性" "Check Python, Shell, and JavaScript tool scripts for security risks")"
run_check "安全性檢查－Python、Shell、JavaScript" self-eval "$PY" tools/self_evaluate.py
confirm "$(t "安全性檢查" "Security Check")" || exit 1

# ========== 4. 文件檢查 ==========
section "4. 文件檢查" "4. Documentation Checks"
info "$(t "檢查文件索引與 YAML 範例結構" "Check documentation index and YAML example structure")"
run_check "文件－範例結構" scraper-docs "$PY" tools/check_scraper_docs.py
run_check "文件－索引清單" docs-index "$PY" tools/check_docs_index.py
confirm "$(t "文件檢查" "Documentation Check")" || exit 1

# ========== 5. 驗證器檢查 ==========
section "5. 驗證器檢查" "5. Validator Checks"
info "$(t "執行結構驗證、URL 排序、政策檢查" "Run schema validation, URL sorting, and policy compliance checks")"
run_check "驗證器－結構驗證" schema node validator/index.mjs -a --ci
run_check "驗證器－URL 排序" url-sort node validator/index.mjs -a -s --ci
run_check "政策檢查" gate bash tools/validate-all.sh
confirm "$(t "驗證器檢查" "Validator Checks")" || exit 1

# ========== 6. Python 測試集 ==========
section "6. Python 測試集" "6. Python Test Suite"
info "$(t "執行 tools/tests/ 下的所有 pytest 測試" "Run all pytest tests under tools/tests/")"
if run_check "Python 測試集" pytest "$PY" -m pytest tools/tests -v; then
:
else
local_fc=$(grep -c 'FAILED' "$LOGDIR/pytest.log" 2>/dev/null || true)
echo "${YELLOW} $(t "失敗測試數" "failed tests"): ${local_fc:-?}${NC}"
fi
confirm "$(t "測試" "Tests")" || exit 1

# ========== 7. 網站實測 ==========
section "7. 網站實測" "7. Live Scrutiny"
info "$(t "對公開擷取器執行實際網站 XPath 驗證" "Test public scrapers against live websites with XPath validation")"
if [[ "${SKIP_SCRUTINY:-false}" != true ]]; then
# 測試所有公開擷取器（排除 scrapers/private/）
PUBLIC_SCRAPERS=$(find scrapers -maxdepth 1 -name '*.yml' | grep -v '^scrapers/private' | sort)
if [[ -n "$PUBLIC_SCRAPERS" ]]; then
SCRAPER_COUNT=$(echo "$PUBLIC_SCRAPERS" | wc -l)
info "$(t "將測試 $SCRAPER_COUNT 個公開擷取器" "Will test $SCRAPER_COUNT public scrapers")"
# 執行所有公開擷取器
ALL_PASSED=true
for scraper in $PUBLIC_SCRAPERS; do
if ! run_check "網站實測" scrutiny node tools/scrutiny.js "$scraper" --search; then
ALL_PASSED=false
fi
done
if $ALL_PASSED; then
:
else
warn_msg "$(t "部分擷取器網站實測失敗" "Some scrapers failed live scrutiny")"
fi
else
skip_msg "$(t "無公開擷取器可供實測" "No public scrapers found for scrutiny")"
fi
confirm "$(t "網站實測" "Live Scrutiny")" || exit 1
else
section "7. 網站實測" "7. Live Scrutiny"
skip_msg "$(t "已跳過 --skip-scrutiny" "skipped (--skip-scrutiny)")"
fi

# ========== 總結 ==========
echo ""
echo "${CYAN}========================================================${NC}"
echo "${CYAN} ${BOLD}$(t "測試總結" "Test Summary")${NC}"
echo "${CYAN}========================================================${NC}"
echo ""
echo " $(t "總計" "Total")     : $TOTAL"
echo " ${GREEN}$(t "通過" "Passed") : $PASSED${NC}"
echo " ${RED}$(t "失敗" "Failed") : $FAILED${NC}"
echo " ${YELLOW}$(t "跳過" "Skipped"): $SKIPPED${NC}"
echo " $(t "Python 直譯器" "Python interpreter") : $PY"
echo ""

logline "SUMMARY" "sections=$TOTAL passed=$PASSED failed=$FAILED skipped=$SKIPPED warnings=$WARNINGS python=$PY"

if [[ ${#FAILED_LABELS[@]} -gt 0 ]]; then
echo " ${RED}$(t "失敗項目" "Failed items")${NC}:"
for lb in "${FAILED_LABELS[@]}"; do
echo " - $lb"
done
echo ""
fi

if [[ $FAILED -eq 0 ]]; then
echo "${GREEN}== $(t "所有檢查通過" "All checks passed") ==${NC}"
echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
echo "$(t "最新捷徑" "Latest symlink"): ${LOG_BASE}/latest/"
logline "END" "all checks passed"
exit 0
fi

echo "${RED}== $(t "部分檢查失敗" "Some checks failed") ==${NC}"
echo ""
echo "$(t "修復建議" "Fix suggestions"):"
echo "  1. $(t "驗證器失敗：檢查 ./.log/latest/schema.log" "Validator failed: see ./.log/latest/schema.log")"
echo "  2. $(t "文件檢查失敗：檢查 ./.log/latest/scraper-docs.log" "Documentation check failed: see ./.log/latest/scraper-docs.log")"
echo "  3. $(t "網站實測失敗：檢查 ./.log/latest/scrutiny.log" "Scrutiny failed: see ./.log/latest/scrutiny.log")"
echo "  4. $(t "使用 -v 或 --ci 查看完整輸出" "Use -v or --ci for full output")"
echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
echo "$(t "最新捷徑" "Latest symlink"): ${LOG_BASE}/latest/"
logline "END" "some checks failed"
exit 1
}

main
