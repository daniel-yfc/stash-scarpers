---
doc_id: DOC-E2E-64
title: Wave 2E Agent C Fixture Assignment Addendum
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
    - agent-c
    - dvd-fixtures
    - regression
---

# Wave 2E — Agent C Assignment Addendum (DVD fixtures)

**Assignment:** `WAVE2E-C-DVD-FIXTURES-20261102` / `WS-2E-40`.  
**Proposed branch:** `test/e2e-bravo-dvd-fixtures`. **Status:** amendment published; not a claim implementation is committed.  
**Base:** [Wave 2E detailed plan](61-bravo-dvd-wave-2e.md). This amends the initial Agent C fixture assignment's evidence assumptions; it does not authorize changes to archived fixtures, shared tools, or runtime YAML.

## Evidence precedence and limits

Use the newer [Agent A Raw-DOM Verification Addendum](https://github.com/daniel-yfc/stash-scarpers/blob/16224b4039e05b3acc675a219066cfd88172db80/docs/research/wave2e/RAW-DOM-VERIFICATION-ADDENDUM.md) as the **source-reported selector contract** over the earlier text-only guesses. It reports **9 product DOM pages (046/234/084/281/377/383/384/304/315) + 2 not-found pages (00/999999)**. However, the later [independent QA review](https://github.com/daniel-yfc/stash-scarpers/blob/0160f664888dd69e4fe33d6de2f632282d8af3c3/docs/research/wave2e/RAW-DOM-HANDOFF-QA-REVIEW.md) has `INDEPENDENT_ACCEPTANCE=CHANGES_REQUESTED` pending access to source snapshots and machine-readable XPath results. Do not claim independent 9/9 verification or `G1_PASS` on the report alone.

The earlier claim "084 has no heading" was an extraction-layer artifact; the source report now says nine product DOMs share **22 h2** nodes. The earlier rejection of `preceding::h2[2]` and image-is-always-absent assumptions are superseded. Historical 2026-10-14 HTML snapshots remain **historical**, never silently replaced.

## Updated tasks

| Task | Fixture/test change | Exact acceptance |
| --- | --- | --- |
| **C-02** | Build representative DVD positive cases for 234, 084, 046, 281; extend coverage from 377/383/384/304/315 when sanitized structural DOM is available | Each expected value cites Agent A evidence ID/source SHA, not URL-derived Title/Code |
| **C-03** | Add **2 real not-found cases** 00 and 999999; source report identifies `404 \| bravo-works` with missing `品番` | Title/Code cannot yield a valid product; canonical alone must never be a PASS |
| **C-04** | Test each field's XPath value **and cardinality**; check Title preceding-2, Code following-1, canonical, Details, Image, Date, Label, Duration | Product cards match independently reviewable source values; Code `046` preserved |
| **C-05** | Distinguish **empty string** from absent node: 084 `p.font_8` exists (n=1) but is empty | Details remains semantically absent; no fallback to price, nearby product or "sold out" |
| **C-06** | Add `BR-084soldout.jpg` as a **non-cover negative policy** and create valid-DVD-without-cover plus unrelated-logo synthetic cases | 084 sold-out artwork is not silently accepted as genuine cover; other product covers may be verified |
| **C-07** | Verify DVD meta keywords are identical across product and 404 pages | **No product Tags** generated from site-generic keywords |
| **C-08** | Distinguish CDP rendered DOM from raw pre-render SSR | Demonstrate no relevant product fields in provided unrendered HTML; `driver.useCDP: true` remains required |
| **C-09** | Add mutation-style wrong-title/wrong-code/wrong-canonical/wrong-image/404-partial-data failures | Tests go red for deliberate bad selectors or contamination, not just for empty XPath |

### Candidate selectors (evidence-reported, not independently re-run in this review)

~~~text
Title     //h2[contains(.,'品番')]/preceding::h2[2]
Code      //h2[contains(.,'品番')]/following::h2[1]
URLs      //link[@rel='canonical']/@href
Details   //p[contains(@class,'font_8')]
Image     //img[@alt!='' and contains(@src,'wixstatic')]/@src
Date      //h2[contains(.,'発売日')]/following::h2[1]
Label     //h2[contains(.,'レーベル')]/preceding::h2[1]
Duration  //h2[contains(.,'収録時間')]/following::h2[1]  (minutes; target policy pending)
~~~

**Do not infer Studio=Label or a scene-specific Duration.** Those are Controller mapping decisions; source extraction correctness does not establish target semantic equivalence. Tags and Performers remain omitted unless independently verifiable.

### Fixture hygiene / integration

- Use a **new** `tests/fixtures/bravo/bravo-dvds-fixtures.yml` and new sanitized DOM fixtures; reference `scrapers/BRAVO.yml` and explicit `mappedExpect.scraper: dvdSceneScraper`. Route selection itself belongs to Agent B and Gate B, not the explicit fixture helper selector.
- Keep archived `tests/fixtures/bravo/bravo-fixtures.yml` **byte-identical**, preserving SHA-256 `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`. Do not alter the archived evidence status.
- Never push unreviewed raw CDP HTML containing session material. Obtain permission for access to private source DOM; publish only privacy-reviewed structural fixtures with enough hierarchy/attributes to preserve XPath behavior. Synthetic fixtures must be marked `SYNTHETIC_REGRESSION` and are not live evidence.
- When raw DOM or verified expected-value traces are not available, deliver fixture scaffolding with `BLOCKED_SOURCE_EVIDENCE` / `EXPECTED_RED`, not fabricated product data or a fake passing test.
- Leave `tools/tests/test_bravo_clips.py` and shared fixture runners to Agent F / separate approved review. Add independent tests under `tools/tests/test_bravo_dvds.py`.

## Deliverables and mandatory handoff

Submit isolated fixture manifest, sanitized HTML cases, executable tests, mutation/negative results, a field-level provenance matrix, `WAVE2E-C-DVD-FIXTURE-REPORT.md`, source commits, and a precise list of items F must import. Unit fixture PASS does not replace independent live Stash Gate B.

~~~yaml
ASSIGNMENT_ID: WAVE2E-C-DVD-FIXTURES-20261102
WORKSTREAM_ID: WS-2E-40
AGENT_ROLE: Agent C
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "<verify actual base SHA>"
BRANCH: test/e2e-bravo-dvd-fixtures
HEAD_SHA: "<actual commit or NOT_COMMITTED>"
CHANGED_FILES: []
DELIVERABLES: []
EVIDENCE: []
TEST_RESULTS: []
KNOWN_LIMITATIONS: []
DEPENDENCIES:
  - "Agent A: source-derived expected values and independently reviewable DOM evidence"
  - "Agent B: effective-route and 404-validity contracts"
  - "Agent F: sole DVD YAML integration"
RISKS_AND_DECISIONS:
  - "084 Details n=1 but empty; absent value not absent element"
  - "084 sold-out artwork is not a trusted product cover"
  - "Canonical exists on 404; test false-positive prevention"
HANDOFF_STATUS: READY | BLOCKED | CHANGES_REQUESTED
~~~

**Stop:** A failed evidence contract, invented expected metadata, changed historical digest, or false successful 404 is a blocker. Do not change Stash test/production instances.
