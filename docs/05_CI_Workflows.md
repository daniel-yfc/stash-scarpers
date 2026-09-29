# CI Workflows

GitHub Actions workflows live under `.github/workflows/`.

## 1. Full Validation Suite (`validate.yml`)

The primary blocking CI gate. It runs the repository checks in this order:

```bash
npm ci || npm install
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_live_cdp_status.py
python tools/self_evaluate.py
python tools/check_scraper_docs.py
python tools/check_docs_index.py
```

The fixture command above is a runner self-test. It does not prove that a site-specific fixture corpus exists. The CDP command records `UNVERIFIED` when Stash is absent and rejects an unsupported verified claim.

## 2. Pull Request Scraper Check (`pr-check.yml`)

Runs on pull requests modifying scraper files. It executes `tools/scraper-quality-gate.sh` on each changed file and posts a status table.

## 3. Live Scraper Scrutiny (`scrutiny.yml`)

Manual workflow for raw-response probing with `tools/scrutiny.js`.

- `tools/scrutiny.js` uses HTTP fetch plus JSDOM. It does not execute site JavaScript and is not rendered-DOM or live Stash/CDP verification.
- Inputs: scraper path, `--search`, `--paginate`, `--url`, and `--probe`.

## 4. CDP Evidence Gate (`cdp-evidence-gate.yml`)

Runs on evidence changes and manual dispatch. It checks whether a live CDP claim has an artifact. It does not launch Stash or a browser.

## 5. Evaluation Pack Runner (`eval.yml`)

Manual workflow for the Python pytest suite.

## 6. Documentation Link Checker (`link-check.yml`)

Checks Markdown links on pull requests and a schedule.

## Interpretation

A green validation job means the executed repository checks passed. It does not establish live selector correctness, rendered-DOM coverage, live Stash/CDP extraction, or production readiness.
