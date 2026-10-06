#!/usr/bin/env bash
set -uo pipefail

# ASCII-colored bilingual wrapper / ASCII 彩色雙語可執行包裝器
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VALIDATOR="/home/yfc/stash-scarpers/validator/index.mjs"
RED=$'\033[31m'; GREEN=$'\033[32m'; YELLOW=$'\033[33m'; RESET=$'\033[0m'

fail() { echo "${RED}[error] $1 / $2${RESET}" >&2; exit 1; }
ok() { echo "${GREEN}[ok] $1 / $2${RESET}"; }

if ! command -v node >/dev/null 2>&1; then
  fail "Node.js is required" "需要 Node.js"
fi

if [[ $# -eq 0 ]]; then
  echo "${YELLOW}Usage: $0 --all | SCRAPER.yml... / 使用方式：$0 --all 或 SCRAPER.yml...${RESET}"
  exit 2
fi

if [[ "$1" == "--all" ]]; then
  mapfile -t files < <(find "$REPO_ROOT/scrapers" -maxdepth 1 -type f -name '*.yml' | sort)
else
  files=("$@")
fi

for file in "${files[@]}"; do
  [[ -f "$file" ]] || fail "File not found: $file" "找不到檔案：$file"
  echo "${YELLOW}[validate] $file / 驗證檔案：$file${RESET}"
  node "$VALIDATOR" --ci "$file" || fail "Validation failed: $file" "驗證失敗：$file"
done

ok "Validation completed" "驗證完成"
