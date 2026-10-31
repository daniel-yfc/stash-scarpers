---
doc_id: REF-OPS-01
title: Portable Schema and Runtime Provenance
status: active
layer: skill
owner: maintainer
audience:
  - agent
applies_to:
  - scrapers
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - schema-provenance
---

# Schema and Runtime Provenance

Read this reference only when deciding authoritative sources for a scraper compatibility or validation claim.

- The **official CommunityScrapers schema and validator** are the authority for their supported scraper YAML contract: https://github.com/stashapp/CommunityScrapers/tree/master/validator
- For ScraperDevelopment behavior and supported operations, consult https://docs.stashapp.cc/in-app-manual/scraping/scraperdevelopment/ and the current upstream implementation when a rule differs.
- The repository copy at `validator/scraper.schema.json` is derived from upstream; confirm its revision and compatibility before a normative claim. The skill's bundled `references/scraper.schema.json` is a minimal, non-authoritative offline stub.
- Only a **successful actual Stash runtime loader** proves a particular committed YAML can be loaded by the Stash version tested. Passing parsing/schema checks is not loader evidence.
- Raw HTTP, completed rendered DOM, fixtures, live Stash search, live detail extraction and CDP are distinct evidence levels. Record what ran, its version/revision, result, and missing layers instead of promoting one pass into another.

This is runtime provenance, not a workflow router, documentation inventory, test pack or historical incident log. Maintainer-only upstream inventories and historical records belong in repository documentation.
