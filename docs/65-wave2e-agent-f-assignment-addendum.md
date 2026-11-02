---
doc_id: DOC-E2E-65
title: Wave 2E Agent F Integration Assignment Addendum
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
    - agent-f
    - dvd-implementation
    - integration
---

# Wave 2E — Agent F Assignment Addendum (sole integration owner)

**Assignment:** `WAVE2E-F-DVD-INTEGRATION-20261102` / `WS-2E-30/50/70`.  
**Proposed branch:** `feat/e2e-bravo-dvds`; **sole ownership** of production `scrapers/BRAVO.yml` and coordinated existing Clips-test edits.  
**Base:** [Wave 2E detailed plan](61-bravo-dvd-wave-2e.md). This addendum supersedes only outdated Agent F assumptions about missing DVD DOM/Title/Image; all authorization, dependency and quality gates continue to apply. **No YAML implementation or merger is authorized by publication of this document.**

## Gate status and evidence classification (2026-11-02 snapshot)

| Gate | Status | Requirement |
| --- | --- | --- |
| **G0 — Clips baseline** | **BLOCKED_LIVE_QA** | [Agent D report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/wave2e-d-baseline-ci-20261102/docs/WAVE2E-D-BASELINE-CI-REPORT.md): PR #93 exact-head CI passed but independent Gate B not run; merge not authorized |
| **Agent A author handoff** | **READY (source agent's report)** | [Raw-DOM verification 16224b4](https://github.com/daniel-yfc/stash-scarpers/blob/16224b4039e05b3acc675a219066cfd88172db80/docs/research/wave2e/RAW-DOM-VERIFICATION-ADDENDUM.md) reports 9/9 product XPath checks and 2 negative pages |
| **Independent A evidence acceptance** | **CHANGES_REQUESTED** | [Independent QA 0160f6](https://github.com/daniel-yfc/stash-scarpers/blob/0160f664888dd69e4fe33d6de2f632282d8af3c3/docs/research/wave2e/RAW-DOM-HANDOFF-QA-REVIEW.md) requests source/provenance and machine-readable XPath results; do not claim this gate is independently signed off |
| **G1 — DVD DOM evidence** | **PROVISIONAL / NOT_INDEPENDENTLY_ACCEPTED** | Obtain reviewed evidence bundle, or Controller records explicitly scoped risk acceptance; don't invent external verification |
| **G2 — Integration** | NOT_STARTED | Wait for G0 and G1 acceptance |
| **Gate A / B / C** | NOT_RUN (DVD feature) | Complete exact-head offline, independent Stash live QA and CI respectively |

Agent F **may now** review selector candidates, draft code/tests in isolated planning artifacts, reconcile A/B/C handoffs and prepare an integration strategy. Agent F **must not** modify accepted runtime YAML until G0 is satisfied and the G1 source evidence/verdict is reconciled, per the current controller plan. Independent QA must operate `stash-test` under an exclusive lease.

## Updated selector implementation specification

The following XPath strings are **source-agent tested**, not independently replayed by this editorial change. Pin them to exact source evidence inputs and rerun on sanitized fixtures and installed Stash before declaring verified:

| Field | Evidence-reported XPath | Acceptance / policy |
| --- | --- | --- |
| Title | `//h2[contains(.,'品番')]/preceding::h2[2]` | 9/9 source-reported, including 046; protect against extra/missing headings |
| Code | `//h2[contains(.,'品番')]/following::h2[1]` | Retain literal `046` and verify Code/canonical identity |
| URLs | `//link[@rel='canonical']/@href` | 9/9 source-reported; **404 has canonical too — not an independent validity test** |
| Details | `//p[contains(@class,'font_8')]` | 084: node exists (n=1) but empty string; no fabricated fallback |
| Image | `//img[@alt!='' and contains(@src,'wixstatic')]/@src` | Product hero source-reported 9/9; **084 sold-out graphic requires suppression or explicit Controller override**; test valid DVD with missing cover/logo |
| Date | `//h2[contains(.,'発売日')]/following::h2[1]` | Parse Japanese date with both padded and unpadded month/day |
| Source Label | `//h2[contains(.,'レーベル')]/preceding::h2[1]` | This is a **label**, not automatically a Stash Studio; defer Studio mapping pending semantic decision |
| Total DVD minutes | `//h2[contains(.,'収録時間')]/following::h2[1]` | Multiply ×60 **only** when accepted policy maps whole DVD to a single Scene, otherwise omit |
| Tags | `//meta[@name='keywords']/@content` | **Omit**: generic on all nine products and both error pages |
| Performers | None | Omit: no structured source evidence |

**Driver requirement:** Keep `driver.useCDP: true`. Agent A reported that unrendered SSR lacks product fields. Validate candidate under actual Stash CDP, not merely historical HTML. Keep Clips' accepted `clipSceneScraper` and URL-only semantics intact.

### New task F-08 — Validity, 404 and partial-result guard

The report indicates `/dvds/00` and `/dvds/999999` have canonical links but lack `品番` and normal product title. Thus `sceneByURL` may match them yet `scrapeXPath` produce partial fields. Stash `scene` fields are independent: selecting a canonical URL does not prove success.

1. Evaluate an **officially valid** way to condition output fields on evidence of a legitimate `品番`/Title/Code product, while recognizing YAML cannot necessarily express whole-object validation. Do not assume the field guard is transitive; validate each field or consumer acceptance rule.
2. Test 404, challenge/error page, wrong Code/canonical identity and empty Title. Mark `FALSE_METADATA_BLOCKER` if a partial object would be accepted as a successful scene.
3. Handle DVD URL input to the existing Clips-only `sceneByQueryFragment`. If it returns plausible wrong data, mark `RELEASE_BLOCKER=QUERY_FRAGMENT_FALSE_METADATA` and request a scoped design decision. No undocumented second query-fragment handler.
4. Preserve separate upstream Stash unmatched-URL panic [#97](https://github.com/daniel-yfc/stash-scarpers/issues/97); a newly matched DVD is **not** a core fix.

### New task F-09 — Metadata mapping policies (explicit decisions)

| Decision | Recommended default | Reversal condition |
| --- | --- | --- |
| **DVD 084 Image** | Exclude `BR-084soldout.jpg` from covers; keep empty | Controller determines sold-out image is intentionally valid product artwork and documents semantics |
| **Tags** | Omit generic keywords | Independent work-specific tags demonstrated |
| **Label → Studio** | **Do not automatically set Studio** | Controller explicitly accepts mapping label/brand to Stash Studio, with QA examples |
| **DVD duration → Scene duration** | Omit by default unless the Scene models the **whole DVD** | Controller approves whole-DVD-to-one-Scene mapping and discloses aggregate-duration semantics |
| **Scene vs DVD collection** | No automatic Group/`groupByURL` | Separate future scope and schema validation |

These are **recommended defaults / review decisions**, not silently approved production behavior. Log each mapping choice and use fail-closed omissions when unresolved.

## Agent F integration, tests, and release checklist

1. Collect immutable Agent A author addendum and independent review, Agent B route tests, Agent C fixtures, Agent D baseline. Every handoff identifies `BASE_SHA`, `HEAD_SHA`, `CHANGED_FILES`, evidence, test results and blockers.
2. Do not cherry-pick Agent A historical conclusions that the later raw-DOM author report retracts. Also do not silently discard the independent review's `CHANGES_REQUESTED`; confirm private evidence replay with an authorized reviewer.
3. Gate B for PR #93 must pass and its merge be authorized and performed before changing the Wave 2E runtime YAML branch as final implementation baseline.
4. Single-writer F integrates the second `sceneByURL` handler → `dvdSceneScraper`, modifies shared `test_bravo_clips.py` exact two-route assertions, adopts independently reviewed C fixtures and B routing tests; **preserve** archived `bravo-fixtures.yml` SHA `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`.
5. Required negative tests: both 404 pages, valid DVD without cover/logo, 084 sold-out art, 084 empty Details, leading zero 046, added/missing heading, generic keyword contamination, QueryFragment DVD misroute, strictness limits of substring URL matching, mismatched Code/canonical.
6. Validate the **exact candidate HEAD**: official validator, quality gate, full Python/fixture/security/doc checks, source-package digest; verify Stash actually loads that revision under an authorized `stash-test` lease.
7. Independent QA executes DVD 234/084 plus representative samples and Clips 284/282, records GraphQL request/response, field-level expected/actual, Stash build and package SHA, failure classification and negative cases. Do not treat no-panic or fixture-only as `DVD_URL_SCRAPING_FIXED_VERIFIED`.
8. Controller approves Gate C, rollback and merge separately. No changes to production or upstream Stash under this task.

## Mandatory handoff update

~~~yaml
ASSIGNMENT_ID: WAVE2E-F-DVD-INTEGRATION-20261102
WORKSTREAM_ID: WS-2E-30
AGENT_ROLE: Agent F
ASSIGNMENT_STATUS: ASSIGNED
BASE_SHA: "<accepted Clips main SHA, after PR #93 authorization/merge>"
BRANCH: feat/e2e-bravo-dvds
HEAD_SHA: "<actual integration commit or NOT_COMMITTED>"
CHANGED_FILES: []
DELIVERABLES: []
EVIDENCE:
  - "Agent A 16224b4 source-reported 11 DOM captures; independent review 0160f6 CHANGES_REQUESTED"
TEST_RESULTS: []
KNOWN_LIMITATIONS:
  - "G0 clips live Gate B incomplete"
  - "G1 source evidence not independently replayed"
DEPENDENCIES:
  - "Agent A: independent evidence review / reconciliation"
  - "Agent B: effective routing and 404 validity tests"
  - "Agent C: sanitized DVD fixtures / negative assertions"
  - "Agent D: PR #93 independent Gate B and authorized merge"
  - "Controller: metadata mapping policy and merge authorization"
RISKS_AND_DECISIONS:
  - "084 sold-out image exclusion recommended"
  - "No site-generic Tags; Label is not assumed Studio"
  - "DVD total duration only when approved for whole-DVD Scene mapping"
GATE_0: BLOCKED
GATE_1: PROVISIONAL_NOT_INDEPENDENTLY_ACCEPTED
GATE_A: NOT_RUN
GATE_B: NOT_RUN
GATE_C: NOT_RUN
RELEASE_BLOCKERS: []
HANDOFF_STATUS: BLOCKED
MERGE_STATUS: NOT_AUTHORIZED
~~~

**Scope priority:** credible product metadata and **independently reviewable** evidence > green tests > broader fields. Do not modify `scrapers/BRAVO.yml` until the documented G0/G1 dependencies are resolved.
