---
doc_id: DOC-TEST-50
title: Testing Guide
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - testing
  - validator
last_verified: "2026-10-06"
authority: canonical
routing:
  intents:
    - testing
    - live-scrutiny
---

# Testing Guide

## Scope and evidence

This guide covers local schema, URL ordering, repository policy, regression tests, rendered-DOM fixtures, documentation checks, and responsible live scrutiny. The date above records a documentation review, not a successful CI or live-site run. A green check establishes only what its actual command exercised; record schema pass, policy pass, automated tests, snapshot verification, live search, live detail, and production readiness separately.

## Local checks

Run commands from the repository root. Install dependencies first with `npm ci` and `python -m pip install -r requirements.txt`.

```bash
# Repository policy for one scraper, then all public and private scrapers
bash tools/scraper-quality-gate.sh scrapers/ACCEED.yml
bash tools/validate-all.sh

# Schema and deterministic URL order
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci

# Regression tests and documentation checks
python -m pytest tools/tests/ -v
python tools/check_scraper_docs.py
python tools/check_docs_index.py
npm run format:check
```

The repository's Node validator/schema expectations derive from upstream CommunityScrapers; see [`validator/scraper.schema.json`](../validator/scraper.schema.json) and [`UPSTREAM_SOURCES.md`](../skills/stash-scraper-builder/references/UPSTREAM_SOURCES.md). A successful schema check does not establish the quality gate, live page matching, or Stash runtime extraction. The formatter is a separate local check; its result must not be inferred from documentation-index success.

## Raw-response scrutiny

When the target permits responsible live access, inspect configured search and detail independently:

```bash
node tools/scrutiny.js scrapers/CK-Download.yml --search
node tools/scrutiny.js scrapers/CK-Download.yml --paginate --multi
node tools/scrutiny.js scrapers/CK-Download.yml --url="<detail-url>"
```

`tools/scrutiny.js` fetches HTTP and parses with JSDOM; it does not execute website JavaScript, complete an interactive login, or prove a live Stash/CDP extraction. Record response date, source URL, response type, access state, extracted values, and failures. A search result does not verify its detail scraper unless the detail page is tested separately.

### Test sidecar files (`*.test.yaml`)

`tools/scrutiny.js` auto-loads `scrapers/<name>.test.yaml` (same directory as the
scraper, including `scrapers/private/`) when present. Sidecars keep reusable
live-test inputs next to the scraper so `test-all.sh` can rerun the suite.
Supported keys:

| Key        | Type            | Meaning                                                          |
| ---------- | --------------- | ---------------------------------------------------------------- |
| `url`      | string \| array | Detail URL(s) to evaluate (array auto-enables multi)             |
| `urls`     | array           | Alias for multiple detail URLs                                   |
| `probe`    | string \| array | Custom search probe term(s): performer name, code, partial title |
| `probes`   | array           | Alias for multiple probe terms                                   |
| `multi`    | boolean         | Test multiple candidate scene URLs (default: auto)               |
| `search`   | boolean         | Evaluate searchScraper (default true; `false` disables)          |
| `paginate` | boolean         | Walk search result pages                                         |

Rules: never store credentials, cookies, or session material in a sidecar —
use a logged-in browser session or `--cookie` at runtime. Prefer at least three
detail URLs and one probe each of performer name, code, and partial title per
site where the site supports search.

Before assessing selectors, classify the fetched page as a completed target page, bot-management challenge, login/paywall/age gate, not-found or HTTP error, or client-side application error/partial render. Inspect document title, canonical URL, a main body marker, and known failure markers. Do not score target-field coverage against a failure page.

## Rendered-DOM fixtures

For JavaScript-dependent sites, capture completed browser-rendered DOM only after rendering finishes. Sanitize fixtures and logs: never copy or reconstruct credentials, cookies, clearance or CSRF tokens, browser profiles, analytics identifiers, or other session material. Keep raw HTTP, rendered snapshot, and live Stash/CDP evidence distinct.

```bash
node tools/verify-scraper-fixtures.mjs --self-test
python tools/run_fixture_manifests.py
python tools/run_fixture_manifests.py --expect tests/fixtures/<scraper>-fixtures.yml
```

The self-test checks the runner only. Discovery reports `UNVERIFIED` when no manifests are committed; `--expect` fails if the named manifest is absent. A manifest pass proves only its included cases and assertions, not all configured search modes or live runtime behavior. Follow [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) for the current executable contract versus broader authoring expectations.

For meaningful site coverage, include detail layouts where variation is plausible, a populated search fixture for each configured search entity, an optional/missing-field case, and a separately classified failure page. Assert XPath cardinality and representative values; when localized, assert `<html lang>`, canonical URL locale, and source-language text. Do not promote an authoring expectation to an enforced runner check without a test.

## CI workflow map

`validate.yml` runs path-filtered schema, URL sort, repository policy, pytest, safeguards, and documentation checks. `pr-check.yml` gives changed-scraper policy feedback. `fixture-manifests.yml`, `evidence-contract.yml`, and `cdp-evidence-gate.yml` have distinct fixture/claim scopes. `scrutiny.yml` is deliberately manual and raw-response only; `link-check.yml` is an advisory Markdown link check on Markdown PRs, weekly, and manually. Read [`05_CI_Workflows.md`](05_CI_Workflows.md) for the exact seven-workflow inventory, triggers, and proof boundaries.

The five-task authoring evaluation in [`eval-pack.md`](../skills/stash-scraper-builder/references/eval-pack.md) is not an executable GitHub Actions evaluation. No workflow result should be represented as its 5/5 score. Neither fixture control nor the CDP claim gate launches a live Stash browser session.

## Submission checklist

- [ ] Schema validation, URL order, repository policy, and relevant regression tests were run with results recorded separately.
- [ ] Search and detail entry points were tested on real completed pages where access permits; blocked or skipped cases are `UNVERIFIED`.
- [ ] Dynamic pages have sanitized completed rendered-DOM fixture evidence for cases actually tested and a separate live Stash/CDP status.
- [ ] Documentation examples, index, formatting, and advisory links were checked as applicable; actual commands and outcomes are recorded.
- [ ] Evidence includes revision, date, URL, expected and actual values, provenance, limitations, and unresolved selectors.

## Troubleshooting

- Missing root `name:`: ensure it is nonempty at column zero; a filename alone does not satisfy the schema.
- Public `driver.cookies`: remove session material; private scraper policy is separate from upstream schema support.
- Invalid `parseDate`: use a Go layout such as `2006-01-02`, not `YYYY` or `%Y` tokens.
- Missing Python dependencies: install `requirements.txt`. For script syntax, use `bash -n tools/<script>.sh` or invoke scripts with `bash`.
- Raw response differs from rendered DOM: save and classify both sanitized responses before revising selectors; do not turn snapshot evidence into a live-CDP claim.

## Related documents

- [`01_System_Architecture.md`](01_System_Architecture.md) — Architecture and verification layers.
- [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md) — Repository policy rules.
- [`04_Production_Gate.md`](04_Production_Gate.md) — A–H production gate.
- [`05_CI_Workflows.md`](05_CI_Workflows.md) — Current CI roles and triggers.
- [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) — Fixture contract and page classification.
- [`test-report-template.md`](test-report-template.md) — Durable test report format.
