# CI Workflows

GitHub Actions workflows live under `.github/workflows/`.

## 1. Full Validation Suite (`validate.yml`)

The primary blocking CI gate. Triggered on push to `main` and pull requests modifying scrapers, validator code, tools, documentation, evidence, or fixtures. It runs the local test layers in sequence:

```bash
# Node layer
npm ci || npm install
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci

# Quality gate
bash tools/validate-all.sh

# Python test suite
python -m pytest tools/tests/ -v

# Safeguard controls
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_live_cdp_status.py
python tools/self_evaluate.py

# Documentation checks
python tools/check_scraper_docs.py
python tools/check_docs_index.py
```

The fixture command is a runner self-test. It does not prove that a site-specific fixture corpus exists. The CDP command records `UNVERIFIED` when Stash is absent and rejects an unsupported verified claim.

## 2. Pull Request Scraper Check (`pr-check.yml`)

Runs on pull requests modifying scraper files. Detects changed scrapers using `tj-actions/changed-files`, executes `tools/scraper-quality-gate.sh` on each changed file, runs `check_scraper_docs.py`, and posts a formatted status table as an inline PR comment.

## 3. Live Scraper Scrutiny (`scrutiny.yml`)

Manual on-demand workflow (`workflow_dispatch`) to execute raw-response probing with `tools/scrutiny.js`.

- `tools/scrutiny.js` uses HTTP fetch plus JSDOM. It does not execute site JavaScript and is not rendered-DOM or live Stash/CDP verification.
- Configurable inputs: target scraper file, `--search` toggle, `--paginate` walking, `--url` direct testing, and custom `--probe` terms.
- Emits raw-response extraction coverage statistics directly into workflow job logs.

## 4. CDP Evidence Gate (`cdp-evidence-gate.yml`)

Runs on evidence changes and manual dispatch. It rejects a live CDP claim that has no artifact. It does not launch Stash or a browser.

## 5. Evaluation Pack Runner (`eval.yml`)

Manual on-demand workflow (`workflow_dispatch`) running the Python pytest suite across specific test targets or the complete suite.

## 6. Documentation Link Checker (`link-check.yml`)

Runs on pull requests and scheduled intervals to detect broken internal and external Markdown links.

## Interpretation

A green validation job means the executed repository checks passed. It does not establish live selector correctness, site availability, login success, rendered-DOM coverage, live Stash/CDP extraction, image CDN accessibility, or production readiness. Those results require separate evidence, tracked in [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md).
