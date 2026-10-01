# Schema Validation Checklist

Use this checklist before emitting a scraper YAML file. Run the repository's Node validator against its schema; its expectations derive from upstream CommunityScrapers (see `UPSTREAM_SOURCES.md`). A checklist is not a validator result.

## Required Structure

- [ ] Root `name` is present; matching the CamelCase filename is a repository convention, not an additional upstream schema requirement.
- [ ] File parses as YAML before committing (e.g. `python -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" <file>`).
- [ ] At least one supported entry point (`sceneByURL`, `sceneByName`, etc.).
- [ ] Each entry has the fields required by its action and entry-point schema.
- [ ] Fragment XPath/JSON entry points include the action-required `queryURL`; script actions follow their script contract.
- [ ] No unsupported root keys `documentHeader` or `$vars`.
- [ ] URL arrays are sorted with the validator's `-s` check.

## Authority

- [ ] The repository's `validator/index.mjs` and `validator/scraper.schema.json` encode schema checks derived from upstream CommunityScrapers; check `UPSTREAM_SOURCES.md` for provenance and compare with upstream when compatibility is in question.
- [ ] `references/scraper.schema.json` is a minimal offline stub, not a full validator or a pass/fail authority.

## Scraper Definition

- [ ] All referenced scraper keys exist.
- [ ] Classify pages before selector assessment: completed target versus challenge, login, paywall, age-gate, 404, application error, or partial render.
- [ ] Test XPath selectors on completed live pages or sanitized completed rendered-DOM fixtures when JavaScript rendering is required; label the actual evidence type.
- [ ] Compare raw HTTP and browser-rendered DOM where they differ; do not infer live Stash/CDP success from a snapshot.
- [ ] Test JSON paths on real JSON API responses.
- [ ] Do not invent search modes or endpoints.

## Data Model and Selectors

- [ ] Preserve meaningful title/source-language text; apply site-specific cleaning only where supported by examples.
- [ ] Date parsing uses Go layouts such as `2006-01-02`, not `YYYY-MM-DD` layout tokens.
- [ ] Studio mapping distinguishes source labels such as メーカー, レーベル, and シリーズ according to the site evidence.
- [ ] Image URL transformations and fallbacks are verified for the site; do not assume `/thumb/` to `/poster/` always works.
- [ ] Preserve performer names; omit a default `Gender` unless supported by the source.
- [ ] Assert selector cardinality (`min`/`max`) and representative expected values.
- [ ] For localized pages assert `<html lang>`, canonical URL locale, and source-language text where applicable.
- [ ] Test at least one missing/optional-field case without unrelated fallback data.

## Driver and Session Safety

- [ ] `driver.useCDP`, if used, is inside the top-level `driver` block only.
- [ ] Public scrapers (`scrapers/*.yml`) do not contain `driver.cookies`; session-dependent files are restricted to `scrapers/private/` under the local policy.
- [ ] No credentials, session cookies, clearance tokens, CSRF values, browser-profile data, or analytics identifiers are committed or reconstructed in YAML, fixtures, evidence, logs, or documentation.

## Output and Evidence

- [ ] Key fields (Title, Date, Studio, Image) match expected values on the pages actually tested.
- [ ] Untested selectors and assumptions are marked `# UNVERIFIED` with limitations recorded separately.
- [ ] An ISO `# Last Updated` comment follows repository convention; scraped values remain in the source language.
- [ ] Schema, URL sorting, policy, pytest, fixture, live search, live detail, live Stash/CDP, and production readiness are recorded as separate states.

## CI and Local Checks

`validate.yml` runs path-filtered schema, URL sorting, repository policy, Python regression tests, safeguards, and documentation checks. `pr-check.yml` reports changed-scraper policy results. `fixture-manifests.yml`, `evidence-contract.yml`, and `cdp-evidence-gate.yml` have separate evidence scopes. `link-check.yml` is advisory; `scrutiny.yml` is manual raw-response inspection. See [`docs/05_CI_Workflows.md`](../../../docs/05_CI_Workflows.md) for triggers and all seven workflow responsibilities.

```bash
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/check_scraper_docs.py
python tools/check_docs_index.py
```

A passing check covers only its executed scope. No current workflow runs the five-task skill evaluation pack or a live Stash/CDP scrape.
