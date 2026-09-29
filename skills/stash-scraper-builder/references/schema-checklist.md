# Schema Validation Checklist

Use this checklist before emitting a scraper YAML file. Run the official CommunityScrapers validator after each change when available.

## Required Structure

- [ ] `name` key present and matches CamelCase filename
- [ ] File parses as YAML before committing (validator load would catch this; verify locally with `python -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" <file>`)
- [ ] At least one entry point (`sceneByURL`, `sceneByName`, etc.)
- [ ] Each entry has the fields required by its action and entry-point schema
- [ ] Fragment XPath/JSON entry points include the required `queryURL`; script actions follow their own script contract
- [ ] No root keys `documentHeader` or `$vars`
- [ ] `url` arrays are sorted A–Z (`validator -s`)

## Authority

- [ ] Official CommunityScrapers schema and validator are authoritative
- [ ] Local `references/scraper.schema.json` is a minimal offline stub ("Not a full validator" by its own title) — never a pass/fail authority; use the official validator for acceptance

## Scraper Definition

- [ ] All referenced keys exist (no dangling refs)
- [ ] Page classified before selector assessment: completed target page vs. bot-challenge / login / paywall / age-gate / 404 / app-error or partial render
- [ ] XPath selectors tested with `$x("...")` on live pages, or against a completed sanitized rendered-DOM fixture when the page is JS-rendered
- [ ] Raw HTTP response compared with browser-rendered DOM; differences documented
- [ ] JSON paths tested on real API responses
- [ ] No invented search modes (`sceneByName` / `sceneByQueryFragment` without real search)

## Data Model

- [ ] Title cleaned per `title-patterns.md`
- [ ] Date uses Go layout (`2006-01-02`), not `YYYY-MM-DD`
- [ ] Studio mapping correct (メーカー ≠ レーベル / シリーズ)
- [ ] Image uses `|` fallbacks, upgrades `/thumb/` → `/poster/`, prefixes `^//` with `https:`
- [ ] Performers cleaned per `performer-cleaning.md`, no default `Gender`

## Selector Assertions

- [ ] Cardinality asserted per selector (`min`/`max` match counts), not just presence
- [ ] Locale asserted: `<html lang>`, canonical URL locale segment, and at least one expected source-language text field
- [ ] At least one missing/optional-field case tested — output must remain a valid partial result, not unrelated fallback data

## Driver Configuration Rules

- [ ] `driver.useCDP` (if present) is in the top-level `driver` block only, not inside any entry point
- [ ] Public scrapers (`scrapers/*.yml`) do not contain `driver.cookies`
- [ ] Session cookies appear only in `scrapers/private/*.yml`

## Secrets and Session Material

- [ ] No credentials, session cookies, clearance tokens, CSRF values, browser-profile data, or analytics identifiers committed to YAML, fixtures, evidence, logs, or documentation
- [ ] Private-scraper session state is referenced by status only — never reconstructed or copied

## Output

- [ ] Key fields (Title, Date, Studio, Image) match expected values on tested URLs
- [ ] Untested selectors marked `# UNVERIFIED`
- [ ] `# Last Updated YYYY-MM-DD` at end of file (optional but recommended)
- [ ] Explanations in English + short zh-TW orientation; scraped values in source language

## CI/CD Checks

On every push and PR, GitHub Actions runs (all against the upstream stashapp/CommunityScrapers validator and schema):

- **Schema validation** — `validate.yml` runs the upstream validator with `-a --ci`
- **URL sorting** — `validate.yml` runs the upstream validator with `-a -s --ci`
- **Python tests** — `test-eval.yml` runs `pytest`
- **Link check** — `link-check.yml` runs `lychee` on all Markdown files

Ensure all checks pass locally before pushing to avoid CI failures.
