#!/usr/bin/env bash
# test-all.sh - Stash scrapers 整合測試套件 / Integrated Test Suite
# 位置：專案根目錄（與 validator/、tools/、scrapers/ 同層）
# 執行：bash test-all.sh
#
# 設計重點：
#   - 不使用 set -e：單一檢查失敗只計入失敗數，不會中止整體流程
#   - run_check 統一包裝：直接以 if 取得退出碼，避免 PIPESTATUS 假陽性
#   - 自動修正 CRLF 與 tools/*.sh 執行權限
#   - Python 依賴原則用 --break-system-packages --user；失敗才退回 venv
#   - 自動輸出執行日誌：[timestamp] [PASS/FAIL] 前綴，留存於 ./.log/
#   - 各檢查完整輸出留存於 ./.log/<檢查名>.log

set -uo pipefail

# ---------- 專案根目錄與日誌目錄 ----------
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR="${PROJECT_ROOT}/.log"

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

SESSION_LOG=""   # 於 main 開頭設定

# ---------- 日誌 ----------
ts() { date '+%Y-%m-%d %H:%M:%S'; }

# logline <LEVEL> <訊息>：寫入執行日誌（純文字，無色彩碼）
logline() {
    [[ -n "$SESSION_LOG" ]] || return 0
    printf '[%s] [%s] %s\n' "$(ts)" "$1" "$2" >> "$SESSION_LOG"
}

usage() {
    echo "用法：$(basename "$0") [選項]"
    echo ""
    echo "選項："
    echo "  -h, --help          顯示說明"
    echo "  -i, --interactive   互動模式（每區段確認）"
    echo "  -e, --en            英文輸出"
    echo "  -v, --verbose       顯示各檢查輸出結尾"
    echo "  --skip-deps         跳過依賴安裝（npm / pip）"
    echo "  --skip-validator    跳過 schema 驗證與品質閘門"
    echo "  --skip-tests        跳過 pytest"
    echo "  --skip-docs         跳過文件檢查"
    echo "  --quick             快速模式（= --skip-deps --skip-docs）"
    echo "  --venv              強制使用 Python venv（例外路徑）"
    echo "  --ci                CI 模式（verbose、非互動）"
    echo ""
    echo "Python 依賴策略："
    echo "  預設 --break-system-packages --user（系統 pip）"
    echo "  失敗時自動退回 .venv；--venv 可強制直接走 venv"
    echo ""
    echo "日誌："
    echo "  執行日誌（PASS/FAIL + 時間戳）：./.log/run-<時間>.log"
    echo "  各檢查完整輸出：./.log/<檢查名>.log"
    echo ""
    echo "範例："
    echo "  bash test-all.sh            # 完整執行"
    echo "  bash test-all.sh --quick    # 快速檢查（不含 npm / 文件）"
    echo "  bash test-all.sh -i -v      # 互動 + 詳細"
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
        --quick) SKIP_DEPS=true; SKIP_DOCS=true ;;
        --venv) USE_VENV=true ;;
        --ci) VERBOSE=true; INTERACTIVE=false ;;
        *) echo "未知選項：$1"; usage ;;
    esac
    shift
done

# ---------- 輸出輔助 ----------
t() {  # t "中文" "English"
    if $LANG_ZH_TW; then printf '%s' "$1"; else printf '%s' "$2"; fi
}

section() {  # section "中文" "English"
    echo ""
    echo "${BLUE}========================================================${NC}"
    echo "${BLUE}  ${BOLD}$(t "$1" "$2")${NC}"
    echo "${BLUE}========================================================${NC}"
    TOTAL=$((TOTAL + 1))
    logline "SECTION" "$(t "$1" "$2")"
}

info() {
    echo "${CYAN}[INFO] $1${NC}"
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

confirm() {  # 互動模式下每區段確認
    if $INTERACTIVE; then
        read -p "[$1] $(t "繼續？(y/n)" "Continue? (y/n)") " -n 1 -r
        echo
        [[ $REPLY =~ ^[Yy]$ ]] || return 1
    fi
    return 0
}

# run_check <標籤> <日誌名> <指令...>
# 直接以 if 判斷退出碼：失敗一定回報失敗，成功一定是真的成功
run_check() {
    local label="$1" logname="$2"; shift 2
    local log="$LOGDIR/$logname.log"
    local rc=0
    if "$@" >"$log" 2>&1; then
        PASSED=$((PASSED + 1))
        echo "${GREEN}[PASS] $label${NC}"
        logline "PASS" "$label"
        if $VERBOSE; then tail -n 25 "$log"; fi
        return 0
    fi
    rc=$?
    FAILED=$((FAILED + 1))
    FAILED_LABELS+=("$label")
    echo "${RED}[FAIL] $label${NC} (exit=$rc)"
    echo "${YELLOW}       $(t "詳情" "details"): $log${NC}"
    logline "FAIL" "$label (exit=$rc, log=$log)"
    if $VERBOSE; then tail -n 40 "$log"; fi
    return 1
}

# ---------- 專案根目錄 ----------
cd "$PROJECT_ROOT" || { echo "無法進入 $PROJECT_ROOT"; exit 1; }

# ---------- CRLF / 權限自動修正 ----------
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
        echo "${GREEN}[PASS] $(t "CRLF 檢查：無需修正" "CRLF check: nothing to fix")${NC}"
        logline "PASS" "CRLF check: nothing to fix"
    else
        warn_msg "$(t "已自動修正 $fixed 個檔案的 CRLF" "auto-fixed CRLF in $fixed file(s)")"
    fi
}

# ---------- 主流程 ----------
main() {
    # 執行日誌：每次執行一個新檔案，並更新 latest 連結
    SESSION_LOG="$LOGDIR/run-$(date '+%Y%m%d-%H%M%S').log"
    ln -sf "$(basename "$SESSION_LOG")" "$LOGDIR/latest.log"
    logline "START" "test-all.sh $(t "開始執行" "started") (root=$PROJECT_ROOT)"

    echo "${CYAN}"
    echo "+------------------------------------------------------+"
    echo "|        $(t "整合測試套件" "Integrated Test Suite") - stash-scarpers        |"
    echo "+------------------------------------------------------+"
    echo "${NC}"
    echo "$(t "專案根目錄" "Project root"): $PROJECT_ROOT"
    echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
    echo "$(t "檢查日誌" "Check logs"): $LOGDIR/<name>.log"

    # 前置檢查：目錄結構
    for d in validator tools scrapers; do
        if [[ ! -d "$d" ]]; then
            echo "${RED}[FAIL] $(t "找不到 $d/，請在專案根目錄執行" "missing $d/, run from repo root")${NC}"
            logline "FAIL" "missing directory: $d"
            exit 1
        fi
    done

    # ========== 0. CRLF / 權限修正（一律執行） ==========
    section "CRLF / 權限修正" "CRLF / Permission Fix"
    fix_crlf

    # Python 直譯器：預設系統 python3（--break-system-packages 路線）
    PY="python3"

    # ========== 1. 環境 ==========
    section "環境檢查" "Environment"
    if ! command -v node >/dev/null 2>&1; then
        echo "${RED}[FAIL] Node.js $(t "未安裝" "missing")${NC}"; logline "FAIL" "Node.js missing"; exit 1
    fi
    if ! command -v npm >/dev/null 2>&1; then
        echo "${RED}[FAIL] npm $(t "未安裝" "missing")${NC}"; logline "FAIL" "npm missing"; exit 1
    fi
    if ! command -v python3 >/dev/null 2>&1; then
        echo "${RED}[FAIL] Python 3 $(t "未安裝" "missing")${NC}"; logline "FAIL" "python3 missing"; exit 1
    fi
    echo "${GREEN}[PASS] Node.js $(node --version)${NC}"
    echo "${GREEN}[PASS] npm $(npm --version)${NC}"
    echo "${GREEN}[PASS] $("$PY" --version 2>&1)${NC}"
    logline "PASS" "Node.js $(node --version)"
    logline "PASS" "npm $(npm --version)"
    logline "PASS" "$("$PY" --version 2>&1)"
    confirm "$(t "環境" "Environment")" || exit 1

    # ========== 2. 依賴 ==========
    if [[ "${SKIP_DEPS:-false}" != true ]]; then
        section "安裝依賴" "Dependencies"
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
                echo "${RED}[FAIL] $(t "venv 建立失敗" "venv creation failed")${NC}"
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
                    echo "${RED}[FAIL] $(t "venv 建立也失敗" "venv creation also failed")${NC}"
                    logline "FAIL" "venv creation also failed"
                fi
            fi
        fi
        confirm "$(t "依賴" "Dependencies")" || exit 1
    else
        section "安裝依賴" "Dependencies"
        skip_msg "$(t "已跳過 --skip-deps" "skipped (--skip-deps)")"
    fi

    # ========== 3. Schema / 品質閘門 ==========
    if [[ "${SKIP_VALIDATOR:-false}" != true ]]; then
        section "Schema 驗證" "Schema Validation"
        run_check "validator（schema）" schema node validator/index.mjs -a --ci
        run_check "validator（URL 排序）" url-sort node validator/index.mjs -a -s --ci
        run_check "$(t "品質閘門（全部擷取器）" "quality gate (all scrapers)")" gate \
            bash tools/validate-all.sh
        confirm "$(t "驗證" "Validation")" || exit 1
    else
        section "Schema 驗證" "Schema Validation"
        skip_msg "$(t "已跳過 --skip-validator" "skipped (--skip-validator)")"
    fi

    # ========== 4. Python 測試 ==========
    if [[ "${SKIP_TESTS:-false}" != true ]]; then
        section "Python 測試" "Python Tests"
        if run_check "pytest" pytest "$PY" -m pytest tools/tests -v; then
            :
        else
            local_fc=$(grep -c 'FAILED' "$LOGDIR/pytest.log" 2>/dev/null || true)
            echo "${YELLOW}       $(t "失敗測試數" "failed tests"): ${local_fc:-?}${NC}"
        fi
        confirm "$(t "測試" "Tests")" || exit 1
    else
        section "Python 測試" "Python Tests"
        skip_msg "$(t "已跳過 --skip-tests" "skipped (--skip-tests)")"
    fi

    
# ========== 5. Live Scrutiny (tools/scrutiny.js) ==========
if [[ "${SKIP_SCRUTINY:-false}" != true ]]; then
section "Live Scrutiny (scrutiny.js)" "Live Scrutiny (scrutiny.js)"
# 預設只跑一個代表性擷取器，避免 CI 過慢
if [[ -f "scrapers/CK-Download.yml" ]]; then
run_check "scrutiny (CK-Download)" scrutiny node tools/scrutiny.js scrapers/CK-Download.yml --search
else
# 若無 CK-Download，找第一個存在的公開擷取器
FIRST=$(find scrapers -maxdepth 1 -name '*.yml' | grep -v '^scrapers/private' | sort | head -n1)
if [[ -n "$FIRST" ]]; then
run_check "scrutiny ($FIRST)" scrutiny node tools/scrutiny.js "$FIRST" --search
else
skip_msg "$(t "無公開擷取器可供 scrutiny" "No public scrapers found for scrutiny")"
fi
fi
confirm "$(t "Scrutiny" "Scrutiny")" || exit 1
else
section "Live Scrutiny (scrutiny.js)" "Live Scrutiny (scrutiny.js)"
skip_msg "$(t "已跳過 --skip-scrutiny" "skipped (--skip-scrutiny)")"
fi

# ========== 6. 文件檢查 ==========
    if [[ "${SKIP_DOCS:-false}" != true ]]; then
        section "文件檢查" "Documentation"
        run_check "check_scraper_docs" scraper-docs "$PY" tools/check_scraper_docs.py
        run_check "check_docs_index" docs-index "$PY" tools/check_docs_index.py
        confirm "$(t "文件" "Docs")" || exit 1
    else
        section "文件檢查" "Documentation"
        skip_msg "$(t "已跳過 --skip-docs" "skipped (--skip-docs)")"
    fi

    # ========== 7. 安全自評 ==========
    section "安全自評" "Self-Evaluation"
    run_check "self_evaluate" self-eval "$PY" tools/self_evaluate.py

    # ========== 總結 ==========
    echo ""
    echo "${CYAN}========================================================${NC}"
    echo "${CYAN}  ${BOLD}$(t "測試總結" "Test Summary")${NC}"
    echo "${CYAN}========================================================${NC}"
    echo ""
    echo "  $(t "區段" "Sections") : $TOTAL"
    echo "  ${GREEN}$(t "通過" "Passed") : $PASSED${NC}"
    echo "  ${RED}$(t "失敗" "Failed") : $FAILED${NC}"
    echo "  ${YELLOW}$(t "跳過" "Skipped"): $SKIPPED${NC}"
    echo "  $(t "Python" "Python") : $PY"
    echo ""

    logline "SUMMARY" "sections=$TOTAL passed=$PASSED failed=$FAILED skipped=$SKIPPED warnings=$WARNINGS python=$PY"

    if [[ ${#FAILED_LABELS[@]} -gt 0 ]]; then
        echo "  ${RED}$(t "失敗項目" "Failed items")${NC}:"
        for lb in "${FAILED_LABELS[@]}"; do
            echo "    - $lb"
        done
        echo ""
    fi

    if [[ $FAILED -eq 0 ]]; then
        echo "${GREEN}== $(t "所有檢查通過" "All checks passed") ==${NC}"
        echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
        logline "END" "all checks passed"
        exit 0
    fi

    echo "${RED}== $(t "部分檢查失敗" "Some checks failed") ==${NC}"
    echo ""
    echo "$(t "修復建議" "Fix suggestions"):"
    echo "  1. $(t "validator 失敗：檢查 ./.log/schema.log（如 Ajv strict-mode 關鍵字錯誤）" "validator failed: see schema.log")"
    echo "  2. $(t "文件檢查失敗：修正 SKILL.md 與 references/*.md 的 YAML 範例" "doc check failed: fix YAML examples")"
    echo "  3. $(t "使用 -v 或 --ci 查看完整輸出" "use -v or --ci for full output")"
    echo "$(t "執行日誌" "Run log"): $SESSION_LOG"
    logline "END" "some checks failed"
    exit 1
}

main
