#!/usr/bin/env bash
# Entrypoint wrapper for the stash-scarpers image: optionally starts an
# in-container headless Chromium with CDP on ws://localhost:9222, then execs
# the requested command.
#
# Env:
#   START_CHROME (default 1)  start Chromium for Mode B CDP flows
#   CHROME_FLAGS              extra Chromium flags
#                             (default: "--no-sandbox --disable-gpu" —
#                              --no-sandbox is required inside containers)
#
# A fresh container Chromium has NO logged-in sessions: use `auth: cookies`
# or `auth: form` test cases (see tools/test-cases.yaml.template). The
# `auth: cdp` pre-logged-in mode only makes sense against your own Chrome.
set -euo pipefail

START_CHROME="${START_CHROME:-1}"
CHROME_FLAGS="${CHROME_FLAGS:---no-sandbox --disable-gpu}"

if [ "${START_CHROME}" = "1" ] && command -v chromium >/dev/null 2>&1; then
    echo "[entrypoint] starting Chromium (headless, CDP on ws://localhost:9222)"
    chromium --headless=new ${CHROME_FLAGS} \
        --remote-debugging-port=9222 \
        --user-data-dir=/tmp/chrome-cdp \
        about:blank >/tmp/chromium.log 2>&1 &

    # Wait for the CDP endpoint to answer
    for _ in $(seq 1 60); do
        if curl -fsS http://localhost:9222/json/version >/dev/null 2>&1; then
            echo "[entrypoint] Chromium CDP ready (http://localhost:9222/json/version)"
            break
        fi
        sleep 0.5
    done
else
    echo "[entrypoint] START_CHROME=${START_CHROME} — skipping in-container Chromium"
fi

exec "$@"
