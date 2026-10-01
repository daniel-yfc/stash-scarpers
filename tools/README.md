# Tools

Repository tooling: quality gate, documentation checker, local build/test helpers, and the test suite. Run all commands from the repository root.

## Quality gate

| Script                    | Purpose                                                                                                     |
| ------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `scraper-quality-gate.sh` | Per-scraper policy checks, plus official CommunityScrapers schema validation when `CS_VALIDATOR_DIR` is set |
| `validate-all.sh`         | Run the gate over every `scrapers/**/*.yml` (including `scrapers/private/`)                                 |

```bash
bash tools/scraper-quality-gate.sh scrapers/ACCEED.yml
bash tools/validate-all.sh
```

Set `CS_VALIDATOR_DIR` only when using a prepared `stashapp/CommunityScrapers` checkout that contains `validator/index.mjs`, `validator/scraper.schema.json`, and installed Node dependencies. The repository default validation path is `npm run validate` and `npm run validate-sort`.

## Documentation checker

`check_scraper_docs.py` checks documentation examples and contradictions. It runs automatically in the `pr-check.yml` workflow.

```bash
python tools/check_scraper_docs.py
```

## Live scraper scrutiny

`scrutiny.js` probes direct HTTP responses using JSDOM. It does not execute website JavaScript or prove rendered-DOM or live Stash/CDP extraction. Classify challenge, login, age-gate, not-found, and application-error pages before interpreting missing selectors.

| Script        | Purpose |
| ------------- | --- |
| `scrutiny.js` | Raw-response inspection of `sceneScraper` and `searchScraper` with probe terms and field coverage reporting |

```bash
# Evaluate a single scraper with automatic probes
node tools/scrutiny.js scrapers/CK-Download.yml

# Also test searchScraper selectors on search results
node tools/scrutiny.js scrapers/CK-Download.yml --search

# Walk pages 1-3 and test multiple candidates
node tools/scrutiny.js scrapers/CK-Download.yml --paginate --multi

# Custom probe search terms
node tools/scrutiny.js scrapers/CK-Download.yml --probe=DVD,2026

# Evaluate sceneScraper directly against a specific URL
node tools/scrutiny.js scrapers/CK-Download.yml --url="https://www.ck-download.com/product/detail/27573"
```

## Safeguard controls

Run these from the repository root. A command's pass proves only its named check. Manifest and structured-evidence verification run in their separate workflows, not the main `validate.yml` job.

| Script | What it checks |
| --- | --- |
| `parse_committed_yaml.py` | YAML parses in the checked-out scraper tree; not a schema pass |
| `verify-scraper-fixtures.mjs --self-test` | Fixture runner behavior; not site fixture coverage |
| `run_fixture_manifests.py` | Discovers and executes committed `tests/fixtures/**/*-fixtures.yml` manifests; no manifests reports `UNVERIFIED`; `--expect` fails if a claimed manifest is missing |
| `scan_session_material.py` | Pattern scan of scraper, fixture, evidence, and log files; prints rule and path, never matched values |
| `check_evidence_labels.py` | Rejects certain unsupported prose claims in top-level evidence records |
| `check_evidence_contract.py` | Validates structured evidence states and artifact provenance, not live runtime truth |
| `check_live_cdp_status.py` | Checks CDP claims for artifact references; does not launch Stash or verify extraction |
| `self_evaluate.py` | Aggregates controls and labels their evidence boundaries |

```bash
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/run_fixture_manifests.py
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_evidence_contract.py
python tools/check_live_cdp_status.py
python tools/self_evaluate.py
```

No completed Gayerdar fixture or live Stash/CDP pass is implied by these commands. Never put session material into a command argument, fixture, evidence record, log, or commit.

## Workflow distinction

- `validate.yml` runs schema, URL sorting, policy, pytest, safeguard self-tests, and documentation checks.
- `fixture-manifests.yml` runs manifest discovery and executes each committed manifest when its paths change.
- `evidence-contract.yml` checks status records on relevant changes and a weekly schedule.
- `cdp-evidence-gate.yml` rejects unsupported CDP claims; it is not a live CDP test.
- `test-eval.yml` is a manual single-scraper quality-gate check (default `ACCEED.yml`); `eval.yml` is the manual pytest evaluation pack. Neither establishes live selector correctness.

## Local helpers

| Script          | Purpose                                                   |
| --------------- | --------------------------------------------------------- |
| `install.sh`    | Install Python (`requirements.txt`) and Node dependencies |
| `build-site.sh` | Build the static `site/` directory                        |
| `clean.sh`      | Remove `site/` and `.cache/`                              |
| `test.sh`       | Run the pytest suite in `tools/tests/`                    |

## Tests

```bash
python3 -m pytest tools/tests/ -v
```

## Standalone utilities

| File                       | Purpose                                     |
| -------------------------- | ------------------------------------------- |
| `SPB-2.0.html`             | Scraper pattern builder (open in a browser) |
| `SRB-2.0-documentation.md` | Documentation for the SRB tool              |

## Dependencies

- Node.js `^22.22.2 || ^24.15.0 || >=26.0.0` (`.nvmrc` pins `24.15.0`; required by `jsdom` 30)
- Python 3 + pytest (`requirements.txt`)

Shell scripts are invoked via `bash tools/<script>.sh` so no executable bit is required. Python and Node scripts use the commands shown above.
