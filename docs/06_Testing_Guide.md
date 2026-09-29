# Testing Guide

## Overview

This guide covers local testing, schema validation, CI/CD checks, Python regression tests, rendered-DOM fixture checks, and responsible live-site scrutiny for the Stash Scraper Quality Gate system.

## Test Types

### 1. Local Quality Gate Testing

Run the quality gate script against individual scraper files to test repository policy rules:

```bash
# Test a single scraper
bash tools/scraper-quality-gate.sh scrapers/ACCEED.yml

# Test all public scrapers
for file in scrapers/*.yml; do
  bash tools/scraper-quality-gate.sh "$file"
done
```

### 2. Schema and URL Validation

Validate scraper files against `validator/scraper.schema.json` using the canonical validator runner:

```bash
# Validate all scrapers
node validator/index.mjs -a --ci

# Check URL alphabetical sorting
node validator/index.mjs -a -s --ci
```

### 3. Python Test Suite

Run the Python test suite to check script executability, directory structures, and skill reference integrity:

```bash
python -m pytest tools/tests/
```

### 4. Live Scraper Scrutiny

Run live-site evaluation to verify selectors against real DOM responses:

```bash
# Evaluate sceneScraper and searchScraper with probes
node tools/scrutiny.js scrapers/CK-Download.yml --search

# Walk pages and test multiple scene candidates
node tools/scrutiny.js scrapers/CK-Download.yml --paginate --multi

# Evaluate a specific scene URL directly
node tools/scrutiny.js scrapers/CK-Download.yml --url="<URL>"
```

### Rendered-DOM fixture testing and failure-page classification

`tools/scrutiny.js` uses HTTP `fetch()` plus JSDOM. It is useful for raw-response scrutiny, but it does **not** execute site JavaScript. It therefore cannot by itself verify selectors that depend on client-side hydration, CDP, SPA routing, browser-only age gates, or a completed JavaScript-rendered DOM.

Before treating a selector miss as a site-layout change, classify the fetched document as one of the following:

- Completed target page
- Cloudflare or other bot-management challenge
- Login, paywall, or age-verification gate
- Not-found / HTTP error page
- Application-error or partial-render page

Do not evaluate target selectors against a failure page. Check at least the document title, canonical URL, a major body marker, and known challenge/error-vendor markers before reporting field coverage.

For JavaScript-dependent scrapers, maintain sanitized rendered-DOM fixtures in the test tree. A fixture must be a completed target page captured from a browser after rendering finishes. Never store cookies, clearance tokens, CSRF tokens, browser-profile data, analytics identifiers, or credentials in fixture HTML, manifests, logs, or documentation.

Run fixture checks separately from live scrutiny:

```bash
node tools/verify-scraper-fixtures.mjs tests/fixtures/<scraper>-fixtures.yml
```

Fixture success proves selector behavior against the recorded completed DOM. It does not prove that Stash can obtain the same page at runtime. Record live Stash/CDP verification separately.

#### Fixture expectations

- Include at least two detail fixtures when the site layout may vary
- Include one populated search fixture for each configured search entity
- Include one valid missing/optional-field case, such as a performer with no social URL
- Assert selector cardinality (`min`/`max`) as well as representative values
- Assert locale through `<html lang>`, canonical URL locale segment, and at least one expected source-language text field
- Fail fast when fixture HTML contains known challenge, login, application-error, partial-render, or not-found markers

### 5. Documentation Verification

Validate Markdown documentation structure and references:

```bash
python tools/check_scraper_docs.py
```

## CI/CD Testing Pipeline

GitHub Actions automatically run tests on pushes and pull requests:

- **`validate.yml`**: Blocking gate for schema validation, URL sorting, full quality gate policy rules, Python regression tests, and documentation checks across all scraper files.
- **`pr-check.yml`**: Validates modified scraper files in pull requests and posts inline status feedback.
- **`scrutiny.yml`**: On-demand live scraper scrutiny runner executing probe queries and scene extraction tests.
- **`link-check.yml`**: Periodically checks Markdown documentation link validity.
- **`eval.yml`**: Evaluates scraper quality against standard evaluation pack scenarios.

## Standard Verification Checklist

Before submitting a scraper change, confirm:

- [ ] `node validator/index.mjs -a --ci` passes without schema errors.
- [ ] `node validator/index.mjs -a -s --ci` confirms URL ordering.
- [ ] `bash tools/scraper-quality-gate.sh <scraper.yml>` passes all policy checks.
- [ ] `python -m pytest tools/tests/` passes all unit tests.
- [ ] `node tools/scrutiny.js <scraper.yml> --search` verifies raw live selectors when site is accessible.
- [ ] Dynamic/SPA sites have completed, sanitized rendered-DOM fixture coverage and an explicitly recorded live Stash/CDP status.
- [ ] `python tools/check_scraper_docs.py` reports no documentation errors.

## Troubleshooting

### Common Issues

#### Quality Gate Failure (`scraper-quality-gate.sh`)

- **Missing root name**: Ensure `name:` is declared at column 0 in XPath scrapers.
- **`driver.cookies` in public directory**: Move session-dependent scrapers to `scrapers/private/`.
- **Invalid parseDate layout**: Use Go reference time formats (for example, `2006-01-02`), not Moment/strftime tokens (`YYYY`, `%Y`).

#### Python Test Failures

- **Executable bit missing**: Run `chmod +x tools/*.sh`.
- **Missing dependencies**: Install requirements with `pip install -r requirements.txt`.

#### Raw response differs from browser DOM

- Save both the raw HTTP response and a completed browser-rendered snapshot.
- Classify Cloudflare challenges, login/age gates, not-found pages, and client-side application errors before changing selectors.
- Do not copy browser cookies, session state, clearance tokens, CSRF values, or browser-profile data into a scraper, fixture, issue, test log, or documentation.
- Mark snapshot verification and live Stash/CDP verification as separate evidence states.

## Related Documents

- [01_System_Architecture.md](01_System_Architecture.md) — System design and component map
- [03_Quality_Gate_Rules.md](03_Quality_Gate_Rules.md) — Detailed 5 quality rules
- [04_Production_Gate.md](04_Production_Gate.md) — Business readiness checklist
- [05_CI_Workflows.md](05_CI_Workflows.md) — CI/CD workflow details
- [test-report-template.md](test-report-template.md) — Standard markdown full-suite test report format
