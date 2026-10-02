# Full-stack image for stash-scarpers tooling:
#   - Node validator (npm ci) + Python regression tests
#   - tools/livetest.py with Playwright (recommended) / websockets CDP backends
#   - Chromium for Mode B CDP login flows (headless, container-safe)
#   - Optional build arg INSTALL_GSK=true adds the Genspark CLI for Mode A
#     anonymous crawls (metered cloud service; set GSK_API_KEY at runtime)
#
# Build:
#   docker build -f deploy/Dockerfile -t stash-scarpers .
#   docker build -f deploy/Dockerfile \
#     --build-arg INSTALL_GSK=true --build-arg GSK_CLI_VERSION=<verified> \
#     -t stash-scarpers .
#
# Run Mode B (in-container Chromium; cookie-file / form auth only — a fresh
# container Chrome has no logged-in sessions):
#   docker run --rm -v "$PWD/.local:/app/.local:ro" stash-scarpers \
#     python3 tools/livetest.py --cases tools/test-cases.yaml.template \
#       --cdp-url ws://localhost:9222
#
# Run Mode A (anonymous sweep; needs GSK_API_KEY and INSTALL_GSK=true):
#   docker run --rm -e GSK_API_KEY=... stash-scarpers python3 tools/livetest.py
#
# Run the validator + tests:
#   docker run --rm stash-scarpers bash -lc \
#     "node validator/index.mjs -a -s scrapers && python -m pytest tools/tests/"
#
# Note: START_CHROME=1 (default) starts headless Chromium with CDP on :9222
# via deploy/entrypoint.sh; set START_CHROME=0 to attach to an external Chrome.
FROM python:3.12-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Node.js 22 (validator runtime) via the official NodeSource APT repository
# (apt signature verification; no downloaded shell executed as root) +
# Chromium (CDP target) + basics
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl git chromium gnupg \
    && install -d -m 0755 /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key \
        | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" \
        > /etc/apt/sources.list.d/nodesource.list \
    && chmod 644 /etc/apt/keyrings/nodesource.gpg /etc/apt/sources.list.d/nodesource.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Python deps: repo requirements (pytest/pyyaml/jsonschema) + harness deps.
# lxml = XPath evaluation; websockets = fallback CDP backend;
# playwright = recommended CDP backend (connect_over_cdp needs no browsers).
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt lxml websockets playwright \
    && rm -rf /root/.cache

# Node deps for the official validator
COPY package.json package-lock.json ./
RUN npm ci --omit=dev || npm install --omit=dev

# Repository sources (scrapers/, validator/, tools/, skills/, docs/)
COPY . .

# Optional: Genspark CLI for Mode A anonymous crawls (metered cloud service).
# Supply-chain policy: installs default to immutable content — pass an exact
# verified version, never a moving tag. Look it up once with:
#   npm view @genspark/cli version
ARG INSTALL_GSK=false
ARG GSK_CLI_VERSION=""
RUN if [ "$INSTALL_GSK" = "true" ]; then \
        if [ -z "$GSK_CLI_VERSION" ]; then \
            echo "ERROR: INSTALL_GSK=true requires --build-arg GSK_CLI_VERSION=<exact version>" >&2; \
            exit 1; \
        fi; \
        npm install -g "@genspark/cli@${GSK_CLI_VERSION}"; \
    fi

ENTRYPOINT ["bash", "deploy/entrypoint.sh"]
CMD ["python3", "tools/livetest.py", "--help"]
