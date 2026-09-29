# CI Workflows

GitHub Actions workflows live under `.github/workflows/`.

## 1. Full Validation Suite (`validate.yml`)

```bash
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

The fixture command is a runner self-test. The CDP command records `UNVERIFIED` when Stash is absent.

## 2. Live Scraper Scrutiny (`scrutiny.yml`)

`tools/scrutiny.js` uses HTTP fetch plus JSDOM. It does not execute site JavaScript and is not rendered-DOM or live Stash/CDP verification.

## 3. CDP Evidence Gate (`cdp-evidence-gate.yml`)

It rejects a live CDP claim that has no artifact. It does not launch Stash or a browser.

## Interpretation

A green validation job means the executed repository checks passed. It does not establish live selector correctness, rendered-DOM coverage, live Stash/CDP extraction, or production readiness.
