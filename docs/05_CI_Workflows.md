---
doc_id: DOC-OPS-40
title: CI Workflows
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - ci
  - testing
last_verified: "2026-10-01"
authority: canonical
routing:
  intents:
    - ci
    - workflows
---

# CI Workflows

GitHub Actions workflows live under `.github/workflows/`.

## 1. Full Validation Suite (`validate.yml`)

The blocking repository gate runs on matching pushes to `main` and pull requests changing scrapers, validator, tools, docs, evidence, fixtures, or other configured paths. It runs the local checks in sequence:

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

The fixture command here tests the runner, not Gayerdar or any other site fixture. The CDP status command does not launch Stash or prove live extraction. Python dependencies are installed between the Node/policy steps and pytest in the workflow.

## 2. Pull Request Scraper Check (`pr-check.yml`)

For matching scraper pull requests, detects changed scrapers with `tj-actions/changed-files`, runs `tools/scraper-quality-gate.sh` per file and `check_scraper_docs.py`, and attempts a PR status comment. This is distinct from the full validation job.

## 3. Fixture Manifest Verification (`fixture-manifests.yml`)

For matching pushes and pull requests affecting fixtures, the runner, its discovery script or tests, installs Node and Python, tests manifest discovery, and executes each committed `tests/fixtures/**/*-fixtures.yml` manifest. No manifest reports `UNVERIFIED`, not a site-fixture pass. `--expect` must be supplied when a specific scraper's fixture is claimed; it is not inferred from prose.

## 4. Evidence Contract (`evidence-contract.yml`)

For matching evidence, fixture, script or workflow changes, and weekly schedule or manual dispatch, validates `evidence/status/*.yml` and its regression tests. Its artifact existence and digest checks validate provenance metadata, not live Stash behavior.

## 5. CDP Evidence Gate (`cdp-evidence-gate.yml`)

Runs on matching evidence changes and manual dispatch. It checks a claimed artifact path; it does not launch Stash or a browser and must not be described as live CDP verification.

## 6. Live Scraper Scrutiny (`scrutiny.yml`)

Manual raw-response probe using `tools/scrutiny.js` with scraper path, search, pagination, URL and probe inputs. It fetches HTTP and parses with JSDOM; it does not execute site JavaScript.

## 7. Evaluation Workflows (`eval.yml`, `test-eval.yml`)

`eval.yml` manually runs the pytest evaluation pack. `test-eval.yml` manually runs the quality gate on one selected scraper (default `ACCEED.yml`). Neither proves live selector correctness.

## 8. Documentation Link Checker (`link-check.yml`)

Checks Markdown links on pull requests and a schedule. The documentation index and example checks are also part of `validate.yml`; they are distinct from link checking.

## Interpretation

A green validation job means only that the steps actually executed passed. It does not establish live-search verification, live-detail verification, rendered-DOM coverage, authorized Stash/CDP extraction, image availability, or production readiness. Record the corresponding evidence in [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md) and applicable status records without session values.
