#!/usr/bin/env bash
# =============================================================================
# run-all-checks.sh — 本機完整測試整合腳本
#
# 將所有本地可執行的檢查依依賴順序整合為單一互動式腳本。
# 彩色輸出，訊息以繁體中文為主。
#
# 測試層級與依賴順序：
#   L0  YAML 解析          — 最基礎；失敗則後續無意義
#   L1  Schema 驗證        — 依賴 L0
#   L2  URL 排序           — 依賴 L1
#   L3  Quality gate       — 依賴 L1（含 validator + 額外政策檢查）
#   L4  Scraper 語義       — 依賴 L0（Gender enum、movieByURL、parseDate）
#   L5  文件-vs-schema     — 獨立（文件聲稱 vs schema 定義）
#   L6  Scraper 文件       — 獨立（內嵌 YAML 範例）
#   L7  文件索引           — 獨立（index.yml 註冊表）
#   L8  Fixture 自測       — 獨立（runner 自身）
#   L9  機密掃描           — 獨立
#   L10 證據標籤           — 獨立
#   L11 Pytest 全套件      — 最終閘門（含上述多項的單元測試）
#   L12 格式檢查           — 建議性（advisory），不影響總 verdict
#
# 用法：
#   bash tools/run-all-checks.sh              # 互動選單
#   bash tools/run-all-checks.sh --all         # 直接全跑
#   bash tools/run-all-checks.sh --step        # 逐步確認模式
#   bash tools/run-all-checks.sh --list        # 列出所有層級
# =============================================================================
set -u

# --- 顏色定義 ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- 全域狀態 ---
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0
SKIP_COUNT=0
declare -a RESULTS=()  # "層級|狀態|說明"
OVERALL_FAIL=0

# --- 輸出函式 ---
info()  { echo -e "${CYAN}[訊息]${NC} $*"; }
ok()    { echo -e "${GREEN}[通過]${NC} $*"; }
err()   { echo -e "${RED}[失敗]${NC} $*"; }
warn()  { echo -e "${YELLOW}[警告]${NC} $*"; }
step()  { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }
divider() { echo -e "${BLUE}────────────────────────────────────────${NC}"; }

record() {
  # $1=層級 $2=狀態(PASS/FAIL/WARN/SKIP) $3=說明
  RESULTS+=("$1|$2|$3")
  case "$2" in
    PASS) PASS_COUNT=$((PASS_COUNT+1)) ;;
    FAIL) FAIL_COUNT=$((FAIL_COUNT+1)); OVERALL_FAIL=1 ;;
    WARN) WARN_COUNT=$((WARN_COUNT+1)) ;;
    SKIP) SKIP_COUNT=$((SKIP_COUNT+1)) ;;
  esac
}

run_check() {
  # $1=層級代號 $2=中文名稱 $3=命令 $4=是否為advisory(0/1)
  local level="$1" name="$2" cmd="$3" advisory="${4:-0}"
  local output exit_code

  step "[$level] $name"
  echo -e "${CYAN}  執行：${NC}$cmd"

  output=$(eval "$cmd" 2>&1)
  exit_code=$?
  # 注意：不要在此處加 pipe，否則 $? 會是 pipe 最後一個命令的 exit code

  if [ $exit_code -eq 0 ]; then
    ok "$name 通過"
    record "$level" "PASS" "$name"
  else
    if [ "$advisory" -eq 1 ]; then
      warn "$name 未通過（建議性，不影響總結果）"
      echo -e "${YELLOW}  摘要：${NC}$(echo "$output" | tail -3)"
      record "$level" "WARN" "$name（advisory）"
    else
      err "$name 失敗"
      echo -e "${RED}  錯誤摘要：${NC}"
      echo "$output" | tail -10 | sed 's/^/    /'
      record "$level" "FAIL" "$name"
    fi
  fi
  return $exit_code
}

confirm_step() {
  # 逐步模式：每層前詢問
  local level="$1" name="$2"
  echo -e "${YELLOW}  是否執行 [$level] $name？ [Y/n/s(跳過)]${NC}"
  read -r ans
  case "$ans" in
    [Nn]) return 1 ;;
    [Ss]) record "$level" "SKIP" "$name（使用者跳過）"; info "已跳過 [$level] $name"; return 2 ;;
    *) return 0 ;;
  esac
}

# --- 各層級定義 ---
check_L0()  { run_check "L0" "YAML 解析" "python3 tools/parse_committed_yaml.py"; }
check_L1()  { run_check "L1" "Schema 驗證" "node validator/index.mjs -a --ci"; }
check_L2()  { run_check "L2" "URL 排序檢查" "node validator/index.mjs -a -s --ci"; }
check_L3()  { run_check "L3" "Quality Gate 全站" "bash tools/validate-all.sh"; }
check_L4()  { run_check "L4" "Scraper 語義檢查" "python3 tools/check_scraper_semantics.py"; }
check_L5()  { run_check "L5" "文件-vs-Schema 對齊" "python3 tools/check_docs_official.py"; }
check_L6()  { run_check "L6" "Scraper 文件檢查" "python3 tools/check_scraper_docs.py"; }
check_L7()  { run_check "L7" "文件索引檢查" "python3 tools/check_docs_index.py"; }
check_L8()  { run_check "L8" "Fixture Runner 自測" "node tools/verify-scraper-fixtures.mjs --self-test"; }
check_L9()  { run_check "L9" "機密資料掃描" "python3 tools/scan_session_material.py"; }
check_L10() { run_check "L10" "證據標籤檢查" "python3 tools/check_evidence_labels.py"; }
check_L11() { run_check "L11" "Pytest 完整套件" "python3 -m pytest tools/tests/ -q"; }
check_L12() { run_check "L12" "程式碼格式檢查" "npm run format:check" 1; }

LEVELS=(L0 L1 L2 L3 L4 L5 L6 L7 L8 L9 L10 L11 L12)
LEVEL_NAMES=(
  "YAML 解析"
  "Schema 驗證"
  "URL 排序檢查"
  "Quality Gate 全站"
  "Scraper 語義檢查"
  "文件-vs-Schema 對齊"
  "Scraper 文件檢查"
  "文件索引檢查"
  "Fixture Runner 自測"
  "機密資料掃描"
  "證據標籤檢查"
  "Pytest 完整套件"
  "程式碼格式檢查（建議性）"
)

list_levels() {
  echo -e "${BOLD}測試層級一覽：${NC}"
  for i in "${!LEVELS[@]}"; do
    echo -e "  ${CYAN}${LEVELS[$i]}${NC}  ${LEVEL_NAMES[$i]}"
  done
}

run_all() {
  local step_mode="${1:-0}"
  for i in "${!LEVELS[@]}"; do
    local lv="${LEVELS[$i]}" nm="${LEVEL_NAMES[$i]}"
    if [ "$step_mode" -eq 1 ]; then
      confirm_step "$lv" "$nm"
      local rc=$?
      [ $rc -eq 1 ] && { info "使用者中止"; break; }
      [ $rc -eq 2 ] && continue
    fi
    "check_$lv"
    # L0 失敗則後續無意義，直接中止
    if [ "$lv" = "L0" ] && [ $OVERALL_FAIL -eq 1 ]; then
      err "L0 YAML 解析失敗，後續檢查無意義，中止執行"
      break
    fi
  done
}

selective() {
  list_levels
  echo ""
  echo -e "${YELLOW}請輸入要執行的層級代號（空白分隔，如：L0 L1 L3，或 all）：${NC}"
  read -r selection
  if [ "$selection" = "all" ]; then
    run_all 0
    return
  fi
  for sel in $selection; do
    local found=0
    for i in "${!LEVELS[@]}"; do
      if [ "${LEVELS[$i]}" = "$sel" ]; then
        "check_$sel"
        found=1
        break
      fi
    done
    [ $found -eq 0 ] && warn "未知層級：$sel，已跳過"
  done
}

print_summary() {
  divider
  echo -e "${BOLD}測試總結${NC}"
  divider
  printf "${BOLD}%-6s %-8s %s${NC}\n" "層級" "狀態" "說明"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r lv st desc <<< "$r"
    case "$st" in
      PASS) st_colored="${GREEN}通過${NC}" ;;
      FAIL) st_colored="${RED}失敗${NC}" ;;
      WARN) st_colored="${YELLOW}警告${NC}" ;;
      SKIP) st_colored="${CYAN}跳過${NC}" ;;
    esac
    printf "%-6s %-8b %s\n" "$lv" "$st_colored" "$desc"
  done
  divider
  echo -e "通過：${GREEN}$PASS_COUNT${NC}  失敗：${RED}$FAIL_COUNT${NC}  警告：${YELLOW}$WARN_COUNT${NC}  跳過：${CYAN}$SKIP_COUNT${NC}"
  echo ""
  if [ $OVERALL_FAIL -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ 總 verdict：通過${NC}"
    if [ $WARN_COUNT -gt 0 ]; then
      echo -e "${YELLOW}（有 $WARN_COUNT 個警告，建議檢視但不影響通過）${NC}"
    fi
  else
    echo -e "${RED}${BOLD}❌ 總 verdict：失敗（$FAIL_COUNT 個層級未通過）${NC}"
  fi
}

show_menu() {
  echo -e "${BOLD}${CYAN}════════════════════════════════════════${NC}"
  echo -e "${BOLD}  Stash Scrapers 本機完整測試${NC}"
  echo -e "${BOLD}${CYAN}════════════════════════════════════════${NC}"
  echo ""
  echo "  1) 全部執行（依依賴順序自動跑完）"
  echo "  2) 逐步確認模式（每層前詢問）"
  echo "  3) 選擇性執行（自選層級）"
  echo "  4) 列出所有測試層級"
  echo "  q) 離開"
  echo ""
  echo -e "${YELLOW}請選擇 [1/2/3/4/q]：${NC} "
  read -r choice
  case "$choice" in
    1) run_all 0 ;;
    2) run_all 1 ;;
    3) selective ;;
    4) list_levels; echo ""; show_menu ;;
    [Qq]) info "已離開"; exit 0 ;;
    *) warn "無效選項"; echo ""; show_menu ;;
  esac
}

# --- 主程式 ---
cd "$REPO_ROOT" || { err "無法進入 repo 目錄：$REPO_ROOT"; exit 1; }

case "${1:-}" in
  --all)  run_all 0 ;;
  --step) run_all 1 ;;
  --list) list_levels; exit 0 ;;
  --help|-h)
    echo "用法：bash tools/run-all-checks.sh [選項]"
    echo "  （無選項）  互動選單"
    echo "  --all       直接執行全部"
    echo "  --step      逐步確認模式"
    echo "  --list      列出測試層級"
    exit 0
    ;;
  "") show_menu ;;
  *) err "未知選項：$1（用 --help 看說明）"; exit 1 ;;
esac

print_summary
exit $OVERALL_FAIL
