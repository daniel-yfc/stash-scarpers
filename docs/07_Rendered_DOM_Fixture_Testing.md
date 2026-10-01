---
doc_id: DOC-TEST-51
title: Rendered-DOM Fixture Testing
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - testing
  - fixtures
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - testing
    - rendered-dom
    - fixtures
---

# Rendered-DOM Fixture Testing

## Purpose

Use rendered-DOM fixtures for sites where the needed DOM appears only after JavaScript execution, CDP rendering, SPA routing, or an approved browser session. This complements raw-response scrutiny; it does not replace schema validation, policy gates, or a live Stash runtime test.

The `last_verified` field above records the historical documentation review. The runner was changed after that date; its new behavior and GitHub Actions result have not been verified by this field.

## Failure-page classification

Before evaluating any selector, classify the captured document as exactly one of:

- Completed target page
- Bot-management challenge
- Login, paywall, or age-verification gate
- Not-found / HTTP error page
- Client-side application error or partial render

Do not evaluate target-field coverage against a failure page. Check document title, canonical URL, a major body marker, and known challenge/error markers first. The runner uses a limited set of known failure markers; human scrutiny remains necessary for new gate types.

## Fixture policy

Fixtures must be completed target-page DOM snapshots. They must never contain credentials, session cookies, clearance tokens, CSRF values, analytics identifiers, browser-profile values, or any other session material.

Authoring expectations (not all enforced by the runner):

1. At least two detail records when layout variation is plausible.
2. A populated search-result fixture for each configured search entity.
3. An optional/missing-field case.
4. XPath cardinality assertions (`min`/`max`) and representative values.
5. Locale assertions for `<html lang>`, canonical URL locale, and source-language text.

The current runner requires a completed case, a recognized failure case, and an optional-field absence case per manifest. It checks parsed `<html lang>`, a canonical path locale segment, source-language text, XPath bounds, and any `values` assertions provided. It does not count detail pages by entity or prove that all configured search modes have populated result fixtures. Passing the runner therefore cannot establish those broader coverage expectations.

## Evidence labels

Record evidence separately:

| Label | Meaning |
|---|---|
| Schema validation | YAML shape accepted by the authoritative validator |
| Policy gate | Repository policy checks accepted the file |
| Rendered fixture verification | Selectors matched a captured completed browser DOM for the cases actually present |
| Live raw-response verification | Selectors matched direct HTTP response HTML |
| Live CDP verification | Stash or an equivalent CDP runtime fetched and extracted live data |
| Production readiness | All required evidence has been recorded; not implied by any single row |

## Commands

```bash
node tools/verify-scraper-fixtures.mjs --self-test
python tools/run_fixture_manifests.py
python tools/run_fixture_manifests.py --expect tests/fixtures/<scraper>-fixtures.yml
```

The self-test proves the runner only. Discovery runs each committed manifest matching `tests/fixtures/**/*-fixtures.yml`; no manifests reports `UNVERIFIED`, not a site pass. Use `--expect` when the evidence record claims a specific manifest. A site fixture pass proves only the cases and assertions present. Run schema validation, URL sorting, the quality gate, evidence-label checks, and live Stash/CDP status separately.
