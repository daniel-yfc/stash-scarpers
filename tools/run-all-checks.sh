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
#   bash tools/run-all-checks.sh --report [輸出檔]
#                                             # 全跑 + 依 docs/evaluation-report-template.md
#                                             # 自動產生評估報告（預設 docs/reports/evaluation-YYYYMMDD-HHMMSS.md）
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
declare -a RESULTS=()  # "層級|狀態|說明|耗時"
declare -a FAIL_DETAILS=()  # "層級|狀態|名稱|錯誤摘要"
OVERALL_FAIL=0
REPORT_MODE=0
REPORT_FILE=""

# --- 輸出函式 ---
info()  { echo -e "${CYAN}[訊息]${NC} $*"; }
ok()    { echo -e "${GREEN}[通過]${NC} $*"; }
err()   { echo -e "${RED}[失敗]${NC} $*"; }
warn()  { echo -e "${YELLOW}[警告]${NC} $*"; }
step()  { echo -e "\n${BOLD}${BLUE}▶ $*${NC}"; }
divider() { echo -e "${BLUE}────────────────────────────────────────${NC}"; }

record() {
  # $1=層級 $2=狀態(PASS/FAIL/WARN/SKIP) $3=說明 $4=耗時
  RESULTS+=("$1|$2|$3|${4:-—}")
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
  local output exit_code start_ts dur detail

  step "[$level] $name"
  echo -e "${CYAN}  執行：${NC}$cmd"

  start_ts=$(date +%s)
  output=$(eval "$cmd" 2>&1)
  exit_code=$?
  # 注意：不要在此處加 pipe，否則 $? 會是 pipe 最後一個命令的 exit code
  dur="$(( $(date +%s) - start_ts ))s"

  if [ $exit_code -eq 0 ]; then
    ok "$name 通過（${dur}）"
    record "$level" "PASS" "$name" "$dur"
  else
    # 錯誤摘要：取最後 5 行，轉為單行（供報告用）
    detail=$(printf '%s' "$output" | tail -5 | sed 's/|/\\|/g' | paste -sd '<' - | sed 's/</<br>/g')
    if [ "$advisory" -eq 1 ]; then
      warn "$name 未通過（建議性，不影響總結果）"
      echo -e "${YELLOW}  摘要：${NC}$(echo "$output" | tail -3)"
      record "$level" "WARN" "$name（advisory）" "$dur"
      FAIL_DETAILS+=("$level|WARN|$name|$detail")
    else
      err "$name 失敗"
      echo -e "${RED}  錯誤摘要：${NC}"
      echo "$output" | tail -10 | sed 's/^/    /'
      record "$level" "FAIL" "$name" "$dur"
      FAIL_DETAILS+=("$level|FAIL|$name|$detail")
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
LEVEL_DEPS=(
  "—"
  "L0"
  "L1"
  "L1"
  "L0"
  "—"
  "—"
  "—"
  "—"
  "—"
  "—"
  "L1–L10"
  "—"
)
LEVEL_NOTES=(
  "失敗則中止後續"
  "validator -a --ci"
  "validator -a -s --ci"
  "16 scraper 逐檔"
  "Gender enum、movieByURL、parseDate"
  "entity 欄位、entry points、operators"
  "內嵌 YAML 範例"
  "index.yml 文件註冊"
  "1 正例 6 負例"
  ""
  ""
  "最終閘門"
  "建議性，不影響 verdict"
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
  printf "${BOLD}%-6s %-8s %-8s %s${NC}\n" "層級" "狀態" "耗時" "說明"
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r lv st desc dur <<< "$r"
    case "$st" in
      PASS) st_colored="${GREEN}通過${NC}" ;;
      FAIL) st_colored="${RED}失敗${NC}" ;;
      WARN) st_colored="${YELLOW}警告${NC}" ;;
      SKIP) st_colored="${CYAN}跳過${NC}" ;;
    esac
    printf "%-6s %-8b %-8s %s\n" "$lv" "$st_colored" "$dur" "$desc"
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

# --- 評估報告產生 ---
generate_report() {
  # $1=輸出檔路徑。依 docs/evaluation-report-template.md 填入實測結果。
  local out="$1"
  mkdir -p "$(dirname "$out")"

  local report_date commit branch env_info executor method verdict
  local level_rows="" issue_rows="" results_ser=""
  local r lv st desc dur dep note st_zh
  local i f_n=0 w_n=0 code

  report_date=$(date '+%Y-%m-%d %H:%M %Z')
  commit=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
  branch=$(git branch --show-current 2>/dev/null || echo "unknown")
  env_info="$(uname -s) $(uname -r) / Node $(node -v 2>/dev/null || echo ?) / $(python3 -V 2>&1 || echo ?)"
  executor=$(git config user.name 2>/dev/null || whoami)
  method="bash tools/run-all-checks.sh --report"

  if [ $OVERALL_FAIL -eq 0 ]; then verdict="✅ 通過"; else verdict="❌ 失敗"; fi

  # 層級結果矩陣（L0–L12 全列，未執行者標「—」）
  for i in "${!LEVELS[@]}"; do
    lv="${LEVELS[$i]}"
    st="—"; dur="—"
    for r in "${RESULTS[@]}"; do
      IFS='|' read -r rlv rst _ rdur <<< "$r"
      if [ "$rlv" = "$lv" ]; then st="$rst"; dur="$rdur"; fi
    done
    case "$st" in
      PASS) st_zh="通過" ;; FAIL) st_zh="失敗" ;;
      WARN) st_zh="警告" ;; SKIP) st_zh="跳過" ;; *) st_zh="—" ;;
    esac
    dep="${LEVEL_DEPS[$i]}"; note="${LEVEL_NOTES[$i]}"
    level_rows+="| $lv | ${LEVEL_NAMES[$i]} | $dep | $st_zh | $dur | $note |"$'\n'
    results_ser+="$lv|$st"$'\n'
  done

  # 失敗與警告明細（fd 格式：層級|狀態|名稱|錯誤摘要）
  for fd in "${FAIL_DETAILS[@]}"; do
    IFS='|' read -r lv st desc detail <<< "$fd"
    if [ "$st" = "FAIL" ]; then f_n=$((f_n+1)); code=$(printf 'F-%02d' $f_n)
    else w_n=$((w_n+1)); code=$(printf 'W-%02d' $w_n); fi
    issue_rows+="| $code | $lv | $desc | $detail | （待人工填寫） | （待人工填寫） |"$'\n'
  done
  if [ -z "$issue_rows" ]; then
    issue_rows="| 無 | — | — | 本次執行無失敗或警告 | — | — |"$'\n'
  fi

  # 通過率：L0–L11（L12 建議性不計）
  local pass_n=0
  for r in "${RESULTS[@]}"; do
    IFS='|' read -r rlv rst _ _ <<< "$r"
    if [ "$rlv" != "L12" ] && [ "$rst" = "PASS" ]; then pass_n=$((pass_n+1)); fi
  done

  R_REPORT_DATE="$report_date" \
  R_EXECUTOR="$executor" \
  R_COMMIT="$commit" \
  R_BRANCH="$branch" \
  R_ENV="$env_info" \
  R_METHOD="$method" \
  R_VERDICT="$verdict" \
  R_LEVEL_ROWS="$level_rows" \
  R_ISSUE_ROWS="$issue_rows" \
  R_RESULTS="$results_ser" \
  R_PASS_RATE="通過 $pass_n / 12" \
  python3 - "$REPO_ROOT/docs/evaluation-report-template.md" "$out" <<'PYEOF'
import os, re, sys

tpl_path, out_path = sys.argv[1], sys.argv[2]
with open(tpl_path, encoding='utf-8') as f:
    tpl = f.read()

subs = {
    '{{REPORT_DATE}}': os.environ['R_REPORT_DATE'],
    '{{EXECUTOR}}':    os.environ['R_EXECUTOR'],
    '{{COMMIT}}':      os.environ['R_COMMIT'],
    '{{BRANCH}}':      os.environ['R_BRANCH'],
    '{{ENV}}':         os.environ['R_ENV'],
    '{{METHOD}}':      os.environ['R_METHOD'],
    '{{VERDICT}}':     os.environ['R_VERDICT'],
    '{{LEVEL_ROWS}}':  os.environ['R_LEVEL_ROWS'].rstrip('\n'),
    '{{ISSUE_ROWS}}':  os.environ['R_ISSUE_ROWS'].rstrip('\n'),
    '{{PASS_RATE}}':   os.environ['R_PASS_RATE'],
}
for k, v in subs.items():
    if k not in tpl:
        print(f'警告：模板缺少佔位符 {k}', file=sys.stderr)
    tpl = tpl.replace(k, v)

# 覆蓋聲明 checkbox：該層級 PASS 則打勾
status = {}
for line in os.environ['R_RESULTS'].split('\n'):
    line = line.strip()
    if line and '|' in line:
        lv, s = line.split('|', 1)
        status[lv] = s

def flip(m):
    lv, text = m.group(1), m.group(2)
    mark = 'x' if status.get(lv) == 'PASS' else ' '
    return f'- [{mark}] {text}'

tpl = re.sub(r'<!-- CHECKBOX:(L\d+) -->- \[ \] (.*)', flip, tpl)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(tpl)
print(f'評估報告已產生：{out_path}')
PYEOF
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
  --report)
    REPORT_MODE=1
    if [ -n "${2:-}" ] && [[ "${2:-}" != -* ]]; then
      REPORT_FILE="$2"
    else
      REPORT_FILE="docs/reports/evaluation-$(date +%Y%m%d-%H%M%S).md"
    fi
    run_all 0
    ;;
  --help|-h)
    echo "用法：bash tools/run-all-checks.sh [選項]"
    echo "  （無選項）  互動選單"
    echo "  --all       直接執行全部"
    echo "  --step      逐步確認模式"
    echo "  --list      列出測試層級"
    echo "  --report [輸出檔]"
    echo "              執行全部並依 docs/evaluation-report-template.md 自動產生評估報告"
    echo "              未指定輸出檔時寫入 docs/reports/evaluation-YYYYMMDD-HHMMSS.md"
    exit 0
    ;;
  "") show_menu ;;
  *) err "未知選項：$1（用 --help 看說明）"; exit 1 ;;
esac

print_summary

if [ $REPORT_MODE -eq 1 ]; then
  echo ""
  generate_report "$REPORT_FILE"
fi

exit $OVERALL_FAIL
