---
doc_id: DOC-E2E-63
title: Wave 2E Agent B Routing Assignment Addendum
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-11-02"
authority: informational
routing:
  intents:
    - wave-2e
    - agent-b
    - route-validation
    - query-fragment
---

# Wave 2E — Agent B Assignment Addendum (routing and product validity)

**Assignment:** `WAVE2E-B-ROUTING-20261102` / `WS-2E-20`.  
**Proposed branch:** `test/e2e-bravo-dvd-routing`. **Status:** amendment published; agent execution and branch contents require separate verification.  
**Base:** [Wave 2E plan](61-bravo-dvd-wave-2e.md). This addendum **supplements**, rather than replaces, the initial Agent B routing/testing assignment. No authority to modify `scrapers/BRAVO.yml` or the existing `tools/tests/test_bravo_clips.py`.

## New evidence and scope change

Agent A's [raw-DOM report at commit 16224b4](https://github.com/daniel-yfc/stash-scarpers/blob/16224b4039e05b3acc675a219066cfd88172db80/docs/research/wave2e/RAW-DOM-VERIFICATION-ADDENDUM.md) **reports** nine real DVD product pages and two error pages, with lxml XPath cardinalities. A separate [independent reviewer at commit 0160f6](https://github.com/daniel-yfc/stash-scarpers/blob/0160f664888dd69e4fe33d6de2f632282d8af3c3/docs/research/wave2e/RAW-DOM-HANDOFF-QA-REVIEW.md) classified independent evidence reproducibility as `CHANGES_REQUESTED` because the raw sources and per-page machine-readable evaluator results were unavailable to that reviewer. Record both statuses: `AUTHOR_HANDOFF=READY`, `INDEPENDENT_EVIDENCE_ACCEPTANCE=CHANGES_REQUESTED`; do not call G1 independently accepted yet.

A claimed 404-page canonical is still present even where the product marker `品番` is absent. This adds a new requirement: **route matched ≠ valid product parsed ≠ safe Stash metadata**.

## New task B-08 — Separate route selection from product validity

| Case | Expected URL handler | Source-product verdict / key oracle |
| --- | --- | --- |
| `/dvds/234` | `dvdSceneScraper` | Product Title + Code 234 + matching canonical |
| `/dvds/084` | `dvdSceneScraper` | Product with Code 084; Details may be empty; do not invent |
| `/dvds/046` | `dvdSceneScraper` | Code is string `046`, not integer 46 |
| `/dvds/00` | `dvdSceneScraper` by route shape | 404 / **not a successful scene**, even with canonical |
| `/dvds/999999` | `dvdSceneScraper` by route shape | 404 / **not a successful scene**, even with canonical |
| `/clips/284`, `/clips/282` | `clipSceneScraper` | Preserve Clips extraction; no DVD handler |
| `example.com` unmatched control | No matching scraper | Stash upstream panic #97 remains an independent finding |

Implement two independent assertions: **(1)** Stash-compatible first-match handler selection; **(2)** content/response validity. Do not infer (2) from (1). In the tested build, URL matching is `strings.Contains`: include host-lookalike, embedded-query, path boundary, overlapping-pattern and route-order negative tests. Label intrinsic substring-matching limitations rather than pretending strict hostname validation is enforced by this schema.

### New task B-09 — 404 fail-closed runtime contract

- Assert that a missing product marker `//h2[contains(.,'品番')]`, empty Title/Code, an error/challenge page, or a Code/URL identity mismatch is not accepted as successful metadata.
- **Important:** Stash declarative XPath fields run independently. A 404 canonical URL could remain populated even if the DVD Title/Code XPath returns empty; the test must detect and reject **wrong-but-plausible partial metadata**. Do not assume a single Title XPath condition automatically guards all fields.
- Review whether a validated XPath-level condition on each relevant field, a documented consumer validity gate, or another officially supported mechanism is needed; provide exact schema/fixture/GraphQL evidence and trade-offs. Do not implement speculative Stash core changes.
- Verify that a valid DVD without a product image does not fall back to site artwork; `/dvds/084` is a different *sold-out artwork* policy case, not proof of generic image absence.

### New task B-10 — QueryFragment and test-harness independence

- Existing Wave 1B `sceneByQueryFragment` maps `queryURL: "{url}"` to `clipSceneScraper`. Do not assume that DVD `sceneByURL` is consulted in this mode. If DVD data produces plausible but false Clips metadata, mark `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA`; propose minimal mitigations and seek Controller decision.
- The current fixture helper's explicit `mappedExpect.scraper` can test the DVD XPath without proving that Stash chooses the DVD handler. **Separate** effective-routing tests from field tests and preserve Clips tests.
- New isolated tests may be `EXPECTED_RED` before Agent F's implementation. Never change production YAML or delete the one-route assertion in the shared Clips test; Agent F owns that edit.

## Test evidence & delivery

Deliver executable `tools/tests/test_bravo_dvd_routes.py` (or another separately justified new filename) and `WAVE2E-B-ROUTING-REPORT.md`, including an effective-route matrix, 404 product-validity matrix, QueryFragment risk classification, exact baseline SHA, reproducible commands/results, and explicit handoff to F. Do not operate `stash-test` without a separately authorized exclusive lease.

~~~yaml
ASSIGNMENT_ID: WAVE2E-B-ROUTING-20261102
WORKSTREAM_ID: WS-2E-20
AGENT_ROLE: Agent B
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "<verify actual base SHA>"
BRANCH: test/e2e-bravo-dvd-routing
HEAD_SHA: "<actual commit or NOT_COMMITTED>"
CHANGED_FILES: []
DELIVERABLES: []
EVIDENCE: []
TEST_RESULTS: []
KNOWN_LIMITATIONS: []
DEPENDENCIES:
  - "Agent A: raw-DOM source report + independently reviewable XPath evidence"
  - "Agent F: sole runtime YAML integration and real route verification"
RISKS_AND_DECISIONS:
  - "Route match is not product validity; 404 canonical remains populated"
  - "QueryFragment false metadata is a release blocker"
HANDOFF_STATUS: READY | BLOCKED | CHANGES_REQUESTED
~~~

**Release boundary:** B may finish routing test engineering before G0/G1, but cannot certify DVD runtime `FIXED_VERIFIED`. No merge, no original fixture modifications, no Stash production changes.
