# CI Workflows

GitHub Actions workflows live under `.github/workflows/`.

## 1. Full Validation Suite (`validate.yml`)

The primary blocking CI gate. Triggered on push to `main` and pull requests modifying scrapers, validator code, or tools. It orchestrates all local test layers in sequence:

```bash
# Node layer
npm ci || npm install
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci

# Quality gate
bash tools/validate-all.sh

# Python test suite & doc check
python -m pytest tools/tests/ -v
python tools/check_scraper_docs.py
```

The workflow also runs `node tools/verify-scraper-fixtures.mjs --self-test` and `python tools/safeguard_audit.py`. Those checks prove the control scripts run. They do not prove that a site-specific fixture corpus or live Stash/CDP extraction exists.

## 2. Pull Request Scraper Check (`pr-check.yml`)

Runs on pull requests modifying scraper files. Detects changed scrapers using `tj-actions/changed-files`, executes `tools/scraper-quality-gate.sh` on each changed file, runs `check_scraper_docs.py`, and posts a formatted status table as an inline PR comment.

## 3. Live Scraper Scrutiny (`scrutiny.yml`)

Manual on-demand workflow (`workflow_dispatch`) to execute raw-response probing with `tools/scrutiny.js`.

- `tools/scrutiny.js` uses HTTP fetch plus JSDOM. It does not execute site JavaScript and is not rendered-DOM or live Stash/CDP verification.
- Configurable inputs: target scraper file, `--search` toggle, `--paginate` walking, `--url` direct testing, and custom `--probe` terms.
- Emits raw-response extraction coverage statistics into workflow job logs.

## 4. Evaluation Pack Runner (`eval.yml`)

Manual on-demand workflow (`workflow_dispatch`) running the Python pytest suite across specific test targets or the complete suite.

## 5. Documentation Link Checker (`link-check.yml`)

Runs on pull requests and scheduled intervals to detect broken internal and external Markdown links.

## Interpretation

A green schema and quality gate job means YAML conforms to official syntax and repository policy. It does not establish live selector correctness, site availability, login success, rendered-DOM coverage, or image CDN accessibility. Those results require separate evidence and must not be inferred from a green workflow.
