#!/usr/bin/env bash
# Idempotent setup for a VM / cloud instance (Ubuntu 24.04 or Debian 12;
# Python 3.11+ is required by the harness's asyncio.timeout usage).
#
# Installs:
#   - Node.js 22          (official validator)
#   - Python venv         (tests + harness deps: pyyaml/jsonschema/lxml/websockets)
#   - Chromium            (Mode B CDP target)
#   - optional: Playwright + bundled Chromium (--with-playwright-browsers)
#   - optional: Genspark CLI (--with-gsk; Mode A anonymous crawls, metered)
#
# Usage:
#   bash deploy/setup-vm.sh [--with-gsk] [--with-playwright-browsers]
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WITH_GSK=0
WITH_PW_BROWSERS=0
for arg in "$@"; do
    case "$arg" in
        --with-gsk) WITH_GSK=1 ;;
        --with-playwright-browsers) WITH_PW_BROWSERS=1 ;;
        *) echo "unknown option: $arg" >&2; exit 1 ;;
    esac
done

echo "==> System packages (Node.js 22, Chromium, Python)"
if ! command -v apt-get >/dev/null 2>&1; then
    echo "This script targets apt-based systems (Ubuntu/Debian). Adapt manually for others." >&2
    exit 1
fi
sudo apt-get update
sudo apt-get install -y ca-certificates curl git chromium python3 python3-pip python3-venv
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | cut -c2- | cut -d. -f1)" -lt 22 ]; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo "==> Python virtualenv (.venv)"
cd "$REPO_ROOT"
python3 -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt lxml websockets

echo "==> Node dependencies (validator)"
npm ci --omit=dev || npm install --omit=dev

if [ "$WITH_PW_BROWSERS" = "1" ]; then
    echo "==> Playwright + bundled Chromium (optional; not needed when attaching to system Chromium)"
    pip install playwright
    playwright install chromium
fi

if [ "$WITH_GSK" = "1" ]; then
    echo "==> Genspark CLI (Mode A anonymous crawls; metered — export GSK_API_KEY to use)"
    sudo npm install -g @genspark/cli
fi

echo
echo "Setup complete. From the repo root (venv active):"
echo "  Validator : node validator/index.mjs -a -s scrapers"
echo "  Tests     : python -m pytest tools/tests/"
echo "  Mode B    : chromium --headless=new --remote-debugging-port=9222 \
"
echo "                --user-data-dir=\$HOME/.chrome-cdp about:blank &"
echo "              python tools/livetest.py --cases tools/test-cases.yaml.template \
"
echo "                --cdp-url ws://localhost:9222"
echo "  Mode A    : (needs gsk + GSK_API_KEY) python tools/livetest.py"
