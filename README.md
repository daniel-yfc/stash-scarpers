# Stash Scraper Builder

[繁體中文指南](readme-zh-tw.md) · [Documentation index](docs/README.md)

This repository builds and verifies Stash scraper YAML. It is not the upstream Stash application or CommunityScrapers. Its validator and schema expectations derive from CommunityScrapers; see [upstream provenance](skills/stash-scraper-builder/references/upstream-sources.md) and the local [validator schema](validator/scraper.schema.json). A template, schema pass, or green CI run does not prove a scraper works on a live site.

For Identify, Scene Tagger, Auto Tagging and GraphQL integration, see the
[metadata feed contract](docs/80-metadata-feed-integration.md). Website scrapers do
not automatically publish to stash-box. Generate the declared support inventory
with `python tools/check_metadata_feed.py --inventory`.

## Install these scrapers as a Stash source

Stash supports custom **installable Scraper Sources** under **Settings → Metadata Providers → Available Scrapers → Add Source**. The source URL is a published `index.yml` that references downloadable ZIP packages; it is **not** an individual scraper YAML file.

After **GitHub Pages is enabled** for this repository (Settings → Pages → Build and deployment → **GitHub Actions**) and the `Publish Stash Scraper Source` workflow has deployed successfully from `main`, use:

```text
https://daniel-yfc.github.io/stash-scarpers/main/index.yml
```

While reviewing the PR, download the `stash-scraper-source-preview` artifact from the **Publish Stash Scraper Source** GitHub Actions run to inspect the actual generated `index.yml` and ZIP packages. An Actions artifact is a preview, **not** a permanent Stash Source URL.

Choose a local install path such as `daniel-scrapers`, then select the scrapers you want to install. If the URL currently returns 404, the Pages source is **not yet published**; do not assume the index is live until the deployment completes. This is a separate source, not a replacement for Community (stable).

The source is built from the **top-level `scrapers/*.yml` files only**. Files under `scrapers/private/`, test sidecars, templates and fixtures are intentionally excluded. Packages use the committed scraper's Git revision, UTC commit date and a SHA-256 checksum verified against each ZIP.

If you prefer manual installation, place the individual `scrapers/*.yml` files in Stash's configured scraper directory and **Reload Scrapers**. Login/CDP-dependent sites still require separately authorized Stash-side setup; an installable package does not establish live runtime functionality.

Publication commands (from a full Git clone with dependencies installed):

```bash
python -m pytest tools/tests/test_scraper_source.py -v
python tools/build_scraper_source.py --output _site/main
python tools/build_scraper_source.py --output _site/main --verify-only
```

See the [official Stash Source URL documentation](https://docs.stashapp.cc/in-app-manual/scraping/#source-urls) and [Stash Scraper Sources guide](https://docs.stashapp.cc/metadata-sources/scrapers/).

## Build a scraper

1. For scraper tasks start at the single [scraper skill entry](skills/stash-scraper-builder/SKILL.md); it selects references by phase and task. [Repository boundaries](AGENTS.md) remain applicable. Consult [runtime selection](skills/stash-scraper-builder/SKILL.md#runtime-selection) and [security policy](skills/stash-scraper-builder/references/phase0-secrets-policy.md) only when relevant.
2. Inspect actual target URLs and responses. Record the entity, supported entry points, page language, source URL, access restrictions, and a known detail page. Do not invent search endpoints, modes, or selectors. If access fails, label the behavior unverified.
3. Copy the matching scaffold from [templates](templates/README.md) or a verified analogous file. Put public YAML in `scrapers/<CamelCaseName>.yml`; keep root `name:` and repository naming/date conventions. Do not copy credentials or session material, even into private files.
4. Use the smallest demonstrated runtime: public HTML with XPath → an actual JSON response with `scrapeJson` → a necessary script action → CDP only for demonstrated rendering or authorized interaction. Embedded JSON in HTML is not automatically a JSON response. Add only supported entry points and keep scraped values in the source language.
5. Test selectors against completed target pages, not a challenge, login gate, HTTP error, or partial render. For search modes, verify a populated result, its detail URL, and a separate detail extraction. Cover optional/missing values and meaningful layout or locale variants. See the [testing guide](docs/50-testing-guide.md) and [rendered-DOM fixture guide](docs/51-rendered-dom-fixture-testing.md).
6. Record the outcome and limits before proposing promotion; follow the [A–H production gate](docs/30-production-gate.md). Feed selector failures and incidents back into fixtures, tests, and authoring guidance.

## Local checks

From the repository root, install dependencies and run the independent checks:

```bash
npm ci
python -m pip install -r requirements.txt
node validator/index.mjs -a --ci
node validator/index.mjs -a -s --ci
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/run_fixture_manifests.py
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_evidence_contract.py
python tools/check_live_cdp_status.py
python tools/check_scraper_docs.py
python tools/check_docs_index.py
python tools/check_metadata_feed.py
npm run format:check
```

The fixture self-test tests the runner, not a site. Manifest discovery reports `UNVERIFIED` when none exist; to require a particular manifest, run `python tools/run_fixture_manifests.py --expect tests/fixtures/<scraper>-fixtures.yml`. A fixture pass covers only assertions present in that manifest. The quality gate and Python tests are separate from schema and URL-sort validation. Formatting is a local check; do not claim it passed without running it.

For responsible live raw-response scrutiny, when the site permits it:

```bash
node tools/scrutiny.js scrapers/<Scraper>.yml --search
node tools/scrutiny.js scrapers/<Scraper>.yml --url="<detail-url>"
```

`tools/scrutiny.js` fetches HTTP and uses JSDOM; it does not execute the site's JavaScript. Use a separate rendered browser DOM or live Stash/CDP run when required, and do not conflate either with the raw-response result. Respect access limits; never bypass a gate or include credentials, cookies, tokens, or browser-profile values in a report or fixture.

## Evidence to retain

For each requested mode, record the scraper path and revision, date, target source URL, response type (raw HTTP, JSON, rendered DOM, or live Stash/CDP), site access state, exact command and result, expected and actual field values, and unresolved selectors. A useful case set is: completed detail pages with layout variation where plausible; a populated search page and selected detail result for each configured search mode; an optional/missing-field page; locale/language assertions where relevant; and a failure/gate page classified separately. XPath fixtures should assert cardinality and representative values. The runner enforces only its documented manifest contract, not every authoring expectation.

Keep distinct labels for **schema**, URL sort, **policy**, automated tests, snapshot/fixture verification, live-search verification, live-detail verification, and production readiness. Record skipped or blocked checks as `UNVERIFIED`, not pass. Use [live status](docs/60-live-test-status.md) and the [test-report template](docs/71-test-report-template.md) for provenance and limitations; historical `docs/archive/evidence/` is not current policy. A checklist or audit recommendation is not test evidence.

## Repository map

- `scrapers/` and `scrapers/private/`: public and private YAML respectively; neither is a place for real secrets.
- `templates/`: scaffolds, not verified site scrapers.
- `skills/stash-scraper-builder/`: authoring contract and specialized references.
- `validator/` and `tools/`: schema validation, quality checks, fixtures, and scrutiny.
- `docs/README.md` and `docs/index.yml`: human and machine documentation routes.
- `CONTRIBUTING.md`: contribution and review workflow.

New Markdown files use a two-digit prefix followed by lowercase kebab-case, matching the document ID number (e.g. `21-quality-gate-rules.md` for `DOC-QG-21`). Follow the [documentation architecture](docs/00-documentation-architecture.md) for metadata, IDs, indexing, and formatting.
