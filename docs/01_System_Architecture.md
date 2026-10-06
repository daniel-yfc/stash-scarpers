---
doc_id: DOC-CORE-10
title: System Architecture
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - verification
last_verified: "2026-10-06"
authority: canonical
routing:
  intents:
    - architecture
    - verification-layers
---

# System Architecture

This repository stores Stash scraper YAML under `scrapers/`, with private variants under `scrapers/private/`. It derives its validator expectations from upstream CommunityScrapers; it is not the upstream Stash application or its scraper corpus. See [`UPSTREAM_SOURCES.md`](../skills/stash-scraper-builder/references/UPSTREAM_SOURCES.md) for provenance.

## Verification layers

| Layer                 | Check                                                                      | Evidence boundary                                                                               |
| --------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| YAML parse and schema | `python tools/parse_committed_yaml.py`; `node validator/index.mjs -a --ci` | File parses and passes schema/mapping validation, not selector correctness                      |
| URL ordering          | `node validator/index.mjs -a -s --ci`                                      | Deterministic URL-array order                                                                   |
| Repository policy     | `bash tools/validate-all.sh`                                               | Local rules such as public/private placement and date syntax                                    |
| Automated regression  | `python -m pytest tools/tests/ -v`                                         | Covered script and documentation behavior only                                                  |
| Fixture runner        | `node tools/verify-scraper-fixtures.mjs --self-test`                       | Runner self-test, not site fixture verification                                                 |
| Site fixture          | `python tools/run_fixture_manifests.py`                                    | Selectors match committed completed-DOM fixtures, when present; no manifests means `UNVERIFIED` |
| Evidence metadata     | `python tools/check_evidence_contract.py`                                  | Record fields and artifact digest, not proof of live execution                                  |
| Live raw response     | `node tools/scrutiny.js scrapers/<Scraper>.yml --search`                   | Direct HTTP response plus JSDOM; no site JavaScript execution                                   |
| Live Stash/CDP        | Authorized Stash runtime test with recorded output                         | Separate live-search and live-detail evidence; a CDP artifact-existence gate is not this test   |
| Production gate       | [`04_Production_Gate.md`](04_Production_Gate.md)                           | Promotion only after all required evidence is reviewed                                          |

## Routing

Start with [`06_Testing_Guide.md`](06_Testing_Guide.md) for commands, [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) for fixture policy, and [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md) for live status. Schema, policy, test, snapshot, live-search, live-detail, CDP, and production states must be recorded separately. A green workflow does not substitute for a missing evidence state.
