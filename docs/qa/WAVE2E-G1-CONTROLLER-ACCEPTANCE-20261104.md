---
doc_id: WAVE2E-G1-CONTROLLER-ACCEPTANCE-20261104
title: Wave 2E — Controller G1 Source-Evidence Acceptance
status: accepted
layer: qa
owner: controller
audience: [agent, maintainer]
applies_to: [wave-2e, g1, dvd-dom-evidence]
last_verified: "2026-11-04"
authority: decision
---

# Wave 2E — G1 Controller Acceptance (2026-11-04)

**Decision ID:** `WS-2E-G1-ACCEPTED-20261104`  
**Verdict:** **`G1_ACCEPTED_FIVE_PAGE_SCOPE / SOURCE_EVIDENCE_ONLY`**.  
**Date:** 2026-11-04 (Asia/Taipei)  
**Repository:** [daniel-yfc/stash-scarpers](https://github.com/daniel-yfc/stash-scarpers)  
**G0 accepted main baseline:** `ff236c9e91e27321e93f59d2bf12488db714dfc7` ([PR #93 merged](https://github.com/daniel-yfc/stash-scarpers/pull/93)).  
**Agent A source:** `research/e2e-bravo-dvd-dom@b2f41e179984049940a1e3b1d0754d8c25b0b0da` (SHA-256 correction, original source XPath evaluation at `4963523`).  
**Independent QA package:** `docs/qa-pr93-gateb-20261103@37ea85192aa31da83e39c52d5c0649561523b77d` (10 newly committed files).  
**Earlier review:** [`WAVE2E-G1-INDEPENDENT-EVIDENCE-QA-20261104.md`](WAVE2E-G1-INDEPENDENT-EVIDENCE-QA-20261104.md), previous `CHANGES_REQUESTED` verdict based on absent independent raw-DOM replay. **Preserve it as valid chronological history, superseded by the specific later evidence below.**

## 1. Scope and two independent replay evidence streams

The required *five-page* G1 source-reproducibility scope is DVD `234`, `084`, `046`, `00` and `999999`. This is **not** independent review of all 11 source captures or an executable Stash DVD scraper.

| Source | Independence and method | Recorded result |
| --- | --- | --- |
| Agent A (author) | Eleven source DOM records, nine products/two content-404 cases; 5 priority structure excerpts; authored XPath matrix | `AUTHOR_READY`, not self-certifying |
| Agent D — Perplexity platform | Independent direct replay of five **author original restricted capture byte streams** against author XPath and expected values; reports 5/5 raw SHA-256 matches, five 17-field XPath replays | **`G1_PASS` for source content and XPath**, HTTP layer **NOT_CAPTURED** in that stream |
| Agent D — Muse/isolated CDP session | Independent **fresh** five-page CDP captures and lxml replay of the 17 exact author XPath expressions per page, including HTTP Document responses | **`G1_PASS`; 5/5 pages, 85/85 field node/value comparisons** with documented normalization notes |

These two reviewer streams are distinct platforms/methods. They are recorded under Agent D and **must not be represented as two named human reviewers**. The Controller independently verified their machine-readable results, but **did not receive the five restricted raw DOM files** and cannot personally rehash those bytes.

**Verified source-level outcomes:** Three products have HTTP Document status `200`, the two negative pages `404`; fresh final URLs match requested URLs. DVD `046`/`084` retain leading-zero Codes; DVD `084` Details node is present with normalized empty value; `234`/`046` Details differ only at inline-element whitespace boundaries; three valid products have 22 `h2`, two negatives have 2; the negatives have no valid `品番`, Title, Code or Image. Canonical is present even on negative pages; it **cannot by itself** establish a valid product.

### 1.1 HTTP/redirect provenance qualification

The published `capture_cdp.py` loops through CDP `Network.responseReceived` events with `type=Document` to report a final `200/404` response and one observed document-response event per target. It **does not** independently record `Network.requestWillBeSent.redirectResponse` events. Accordingly, the published `navigation_chain` does **not prove a complete zero-redirect history**, even though final URLs equal requested and the HTTP Document statuses are supported. Record `REDIRECT_CHAIN_COMPLETENESS_NOT_VERIFIED`, a **non-blocking provenance limitation** at this G1 source-selector gate. Any downstream process needing full redirect-chain guarantees must instrument the missing CDP event path and document it.

### 1.2 Reviewer environment qualification

The fresh-capture script obtains the CDP path using a read-only Stash GraphQL configuration query and creates/closes Chrome targets on the environment labeled `stash-test`. This is **not** production Stash metadata modification or a Stash scene scrape, but it is **not literally zero use of stash-test infrastructure**. The G1 evidence does not include an exclusive lease or before/after CDP target inventory. This environment-governance note is non-blocking for the *source DOM* verdict; **all future Stash Gate B work still requires explicit M0, exclusive lease, exact package provenance and rollback**.

## 2. Controller verification against committed Repository

Reviewed exact `37ea851` package and `b2f41e1` Agent A correction:

- Ten added QA files, including report, handoff, convergence note, second-platform report/results, independent fresh-capture provenance/results, capture+replay scripts and manifest.
- **Public file SHA-256 independently recomputed: 9/9 match** `MANIFEST.sha256`. Five raw rendered-HTML files appear only as digests in manifest and are **RESTRICTED / NOT REHASHED BY CONTROLLER**; they were not placed in GitHub.
- `replay-results.json`: five page results × 17 fields = **85 field comparisons**, `all_pages_ok=true`, no false `nodes_match` / `values_match`. The special result modes for two Details fields (`whitespace_boundary_only`) and three `h2_total` fields (`stored_prefix`) are explicit; do not call all 85 values byte-identical.
- `g1-independent-replay-results.json`: five pages `sha_match=true` and `all_pass=true`, with reviewer/report metadata. Its file SHA-256 in manifest is `7f78e7f2e4e94f569969ca3afaa076ddc245adb66dc889a2c3e4c258436f000c`.
- `capture-provenance.json`: final `200/200/200/404/404`, exact-page URLs, completion conditions and **five fresh input hashes**, distinct as expected from Agent A source SHA.
- Agent A’s `G1-CLOSURE-ADDENDUM.md` was updated at `b2f41e1` with the committed **7,900-byte** excerpts SHA-256 `f8c3da0a2c8c33753d55c4ca80122e567eb5c73eace1214d1f0ee3dba141d8dc`. Earlier `055aff…` referred to the same JSON with **no final LF (7,899 bytes)**; `F-G1-01` is **CLOSED_NONBLOCKING**.

## 3. Gate decision and strict limits

**Decision:** The previously blocking lack of independently replayed DOM and lack of HTTP page-status evidence have been resolved at the agreed five-page acceptance scope. **`G1=ACCEPTED_CLOSED_FOR_SOURCE_EVIDENCE`**. The earlier independent `CHANGES_REQUESTED` verdict remains retained as the correct historical pre-handoff status.

**Not accepted/not implied:**
- The other six Agent A samples were not independently replayed during this five-page QA; their authored evidence remains available for later regression coverage.
- `HTTP_REDIRECT_CHAIN_FULLY_VERIFIED`: **false** (CDP event limitation above).
- Tested Stash effective DVD handler, DVD Gate B, merge, deployment or production Stash modifications: **NOT_RUN/NOT_AUTHORIZED**.
- Source media presence alone never authorizes target Scene Image, Studio, Duration or Tags.

**Binding policy (Controller and Agent C v2.3):**

| Field | Decision |
| --- | --- |
| DVD Title/Code/URL/Details/Date | Can be proposed from independently accepted source; live integration must independently gate validity and fail-closed on 404/challenge |
| DVD `Duration_min` | Retain source whole-DVD minutes, **do not map to Stash Scene.Duration** |
| DVD source `Studio_label` | Retain source Label, **do not map to Stash Studio** |
| DVD `084` sold-out art | **Not approved as actual cover; omit Scene Image for 084** |
| Site-wide `meta keywords` | **Do not map as product Tags** |
| Clips `Scene.Duration` | Remains temporarily unmapped at G0; restoration recipe preserved |
| QueryFragment | `WS-2E-QF-001` selected future orphan removal; must audit direct callers and independently verify change |

**Agent F gate:** Both hard dependencies are satisfied: `G0=ACCEPTED_CLOSED` and `G1=ACCEPTED_CLOSED_FOR_SOURCE_EVIDENCE`. **Agent F is no longer blocked by G0/G1**, but this G1 source decision **does not itself authorize Stash runtime access, merge or deployment**. Controller implementation handoff must pin the accepted SHAs and source/target mapping decisions; only then the sole-writer Agent F may begin official DVD YAML changes in a separate Draft implementation PR.

## 4. Status contract

~~~yaml
DECISION_ID: WS-2E-G1-ACCEPTED-20261104
G0: ACCEPTED_CLOSED
G0_MAIN_SHA: ff236c9e91e27321e93f59d2bf12488db714dfc7
G1: ACCEPTED_CLOSED_FOR_SOURCE_EVIDENCE
G1_SCOPE: FIVE_PRIORITY_PAGES_234_084_046_00_999999
AGENT_A_HEAD: b2f41e179984049940a1e3b1d0754d8c25b0b0da
INDEPENDENT_QA_EVIDENCE_SHA: 37ea85192aa31da83e39c52d5c0649561523b77d
PUBLIC_EVIDENCE_MANIFEST_SHA256: PASS_9_OF_9
RESTRICTED_RAW_DOM_SHA256: REFERENCED_5_NOT_REHASHED_BY_CONTROLLER
INDEPENDENT_REPLAY: PASS_TWO_DISTINCT_AGENT_D_METHODS
FRESH_DOCUMENT_HTTP_STATUS: PASS_3X200_2X404
REDIRECT_CHAIN_COMPLETE: NOT_VERIFIED_NONBLOCKING
SOURCE_DIGEST_FINDING_F_G1_01: CLOSED_NONBLOCKING
DVD_DURATION_TO_SCENE: OMIT
DVD_LABEL_TO_STUDIO: OMIT
DVD_084_SOLDOUT_IMAGE: OMIT
DVD_SITE_GENERIC_TAGS: OMIT
STASH_DVD_GATE_B: NOT_RUN
AGENT_F_G0_G1_BLOCK: CLEARED
AGENT_F_IMPLEMENTATION_AUTHORIZATION: REQUIRES_CONTROLLER_ASSIGNMENT
STASH_TEST_LEASE_AUTHORIZED: false
PRODUCTION_STASH_CHANGE_AUTHORIZED: false
MERGE_AUTHORIZATION: NOT_GRANTED
~~~ 
