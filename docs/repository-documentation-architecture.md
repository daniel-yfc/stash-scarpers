---
doc_id: DOC-GOV-00
title: Repository Documentation Architecture
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - documentation
  - repository
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - documentation-policy
    - naming
    - indexing
    - formatter-policy
---

# Repository Documentation Architecture

## Purpose

This document is the canonical policy for repository documentation numbering, naming, metadata, indexing, routing, and formatting. It defines the boundary between repository-level documentation and the `stash-scraper-builder` skill without duplicating rules in both places.

## Agent routing

1. Repository administration, CI, paths, or contribution: `README.md` → `AGENTS.md` → `docs/README.md` → `docs/index.yml` → the owning repository document.
2. Scraper authoring or debugging: `skills/stash-scraper-builder/SKILL.md` → `references/skill-read-order.md` → the selected specialized reference.
3. Schema or validation questions: official `validator/index.mjs` and official schema first, then repository policy.
4. Live verification: `docs/06_Testing_Guide.md` → `docs/07_Rendered_DOM_Fixture_Testing.md` → `docs/LIVE_TEST_STATUS.md`. `tools/scrutiny.js` is raw HTTP plus JSDOM, not rendered-DOM or live Stash/CDP verification.
5. Authentication, cookies, or private variants: the skill secrets reference, then `scrapers/private/`.

If documentation conflicts, resolve in this order: official CommunityScrapers schema/validator, executable repository tools, canonical repository docs, skill references, examples.

## Canonical command policy

- `npm run validate` — validate all scrapers.
- `npm run validate-sort` — check URL ordering.
- `python -m pytest tools/tests/` — run Python tests.
- `bash tools/scraper-quality-gate.sh <scraper.yml>` — run the quality gate on one scraper.
- `bash tools/validate-all.sh` — run the quality gate over all scrapers.
- `node tools/scrutiny.js scrapers/<Scraper>.yml --search` — raw HTTP plus JSDOM scrutiny only.
- `node tools/verify-scraper-fixtures.mjs --self-test` — fixture-runner self-test, not site evidence.
- `python tools/parse_committed_yaml.py` — parse committed scraper YAML.
- `python tools/scan_session_material.py` — scan for session-material assignments without printing values.
- `python tools/check_evidence_labels.py` — reject unsupported verification claims.
- `python tools/check_live_cdp_status.py` — fail closed; not a live Stash run.
- `python tools/self_evaluate.py` — run the safeguard controls and print their boundaries.
- `python tools/check_scraper_docs.py` — check documentation examples and contradictions.
- `python tools/check_docs_index.py` — check the documentation registry.
- `npm run format:check` — check formatting locally; CI does not currently fail on formatting drift.

Every new documentation file must be listed in `docs/README.md` and `docs/index.yml`. When front matter contains `doc_id`, it must match the index.
