---
doc_id: DOC-E2E-67
title: Wave 2E Agent F Implementation and Integration Assignment v2
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-11-03"
authority: informational
routing:
  intents:
    - wave-2e
    - agent-f
    - dvd-integration
    - query-fragment
---

# AGENT F — Wave 2E DVD Implementation & Integration Assignment v2

**Assignment ID:** `WAVE2E-F-DVD-INTEGRATION-20261103`  
**Version:** v2 — QueryFragment decision incorporated; **supersedes** `WAVE2E-F-DVD-INTEGRATION-20261102` where conflicting.  
**Workstreams:** `WS-2E-30`, `WS-2E-50`, `WS-2E-70`  
**Role:** Sole official BRAVO YAML writer / Test Integrator  
**Repository:** [daniel-yfc/stash-scarpers](https://github.com/daniel-yfc/stash-scarpers)  
**Implementation branch:** `feat/e2e-bravo-dvds` (proposed; verify existence before creating)  
**Target:** `main`; final PR remains **Draft** until Controller authorizes merge  
**Report language:** zh-TW  
**Primary decision:** [`WS-2E-QF-001` — Remove orphaned QueryFragment](66-wave2e-queryfragment-decision.md)  
**Planning:** [Wave 2E DIP](61-bravo-dvd-wave-2e.md); [v1 Agent F Addendum](65-wave2e-agent-f-assignment-addendum.md) is historical for superseded QueryFragment instructions.  
**Status:** **DESIGN/PREFLIGHT ALLOWED NOW; OFFICIAL YAML IMPLEMENTATION BLOCKED BY G0/G1**. Publishing this task does **not** create the implementation branch, execute tests, authorize Stash access, or bypass merge gates.

## 1. Mission and non-negotiable constraints

Implement a **dedicated DVD URL scraper** (`/dvds/` → `dvdSceneScraper`), preserve accepted Clips URL behavior (`/clips/` → `clipSceneScraper`), integrate A/B/C evidence and tests, and retire the unsafe **orphaned** `sceneByQueryFragment` entry per `WS-2E-QF-001`.

Do **not** fix the Stash core unmatched-URL panic as part of this scope; that remains independent [issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97). Do **not** use guessed XPath, broad image fallbacks, unapproved Studio/Scene semantics, or changes to historical fixtures. Do not automatically merge or deploy.

**Single-writer boundary:** Only Agent F may edit `scrapers/BRAVO.yml` and the shared `tools/tests/test_bravo_clips.py` for this Wave 2E implementation. Isolated Agent B/C commits are imported after review; their branches are not automatically mergeable to `main`.

## 2. Check current prerequisites before changing runtime files

At assignment drafting, the following were observed; **refresh exact refs and review newer changes before acting**:

| Input | Reference snapshot | Required before final YAML work |
| --- | --- | --- |
| PR #93 — Clips | `86e34a24642dad2e64ae984e7e9182605e98cbcf`, Draft, CI successes | **G0:** independent Clips live Gate B PASS, explicit Controller approval and actual merge to `main` |
| Agent D baseline | [`docs/WAVE2E-D-BASELINE-CI-REPORT.md`](https://github.com/daniel-yfc/stash-scarpers/blob/docs/wave2e-d-baseline-ci-20261102/docs/WAVE2E-D-BASELINE-CI-REPORT.md) | `BASELINE_BLOCKED_LIVE_QA` is not a PASS |
| Agent A evidence | [`research/e2e-bravo-dvd-dom`](https://github.com/daniel-yfc/stash-scarpers/tree/research/e2e-bravo-dvd-dom), previously `4963523` | Nine product pages, two 404s, per-page machine-readable XPath results; obtain **independent replay** or bounded Controller risk acceptance, not just author READY |
| Agent B routing | [`test/e2e-bravo-dvd-routing`](https://github.com/daniel-yfc/stash-scarpers/tree/test/e2e-bravo-dvd-routing), previously `16bf5a1` | Handler/route semantics, 404 product validity, `QF_FALSE_METADATA` historical reproduction |
| Agent C fixtures | [PR #99](https://github.com/daniel-yfc/stash-scarpers/pull/99), previously `75a0834` | New DVD fixtures, tests, manifest; resolve unintended fixture isolation failure and final `EXPECTED_RED` after implementation |
| Agent E upstream | [issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97) | Independent; never promote URL-route success to upstream panic fixed |

**G0 and G1 are hard dependencies:** If either remains unaccepted, record `IMPLEMENTATION_STATUS=BLOCKED_G0_OR_G1`. Agent F may inspect code, propose tests, evaluate source metadata or prepare a non-runtime integration plan. **Do not make the official `BRAVO.yml` edits** until the accepted baseline SHA and evidence decision are recorded.

## 3. F-00 — Handoff intake and compatibility preflight

For each A/B/C/D handoff require `WORKSTREAM_ID`, `BASE_SHA`, `BRANCH`, `HEAD_SHA`, `CHANGED_FILES`, `DELIVERABLES`, `EVIDENCE`, `TEST_RESULTS`, `KNOWN_LIMITATIONS`, `DEPENDENCIES` and `HANDOFF_STATUS`. Verify source commits, privacy, historical fixture SHA and scope ownership before importing.

**Before removing QueryFragment, audit direct consumers:**
1. Search current repo tests, scripts, GraphQL calls, readmes, workflows and config for calls that explicitly invoke BRAVO `sceneByQueryFragment` rather than normal URL scraping.
2. For accessible authorized environments, request a read-only inventory/usage proof; do not claim no callers exist when log access is incomplete.
3. Identify business-essential callers, their migration to `scrapeSceneURL` / correct installed-schema URL entry, and any blocked migration.
4. If indispensable direct QF use is confirmed, set `DECISION_EXCEPTION=REQUIRED_QUERY_FRAGMENT_CONSUMER_FOUND`, **stop removal**, submit evidence and request Controller to decide whether a strictly Clips-guarded alternative is warranted. Do not restore unsafe unguarded QF.

## 4. F-QF-01 — Implement Controller decision WS-2E-QF-001

On the authorized future Wave 2E candidate:

- **Remove** the entire `sceneByQueryFragment` YAML block.
- **Keep `sceneByFragment` absent**; do not introduce a URL-less name/fragment search or undocumented second QueryFragment handler.
- Keep existing `clipSceneScraper` selectors and `driver.useCDP: true`; ensure Clips `sceneByURL` still works.
- Add exactly two Scene URL route families: Clips -> `clipSceneScraper`, DVDs -> `dvdSceneScraper`.
- If there is a conflict with the earlier general [Rule 4](21-quality-gate-rules.md), follow the **explicit narrow BRAVO Wave 2E exception** in `WS-2E-QF-001`. Other scrapers' QueryFragment behavior remains unchanged.
- Do not retroactively modify pending PR #93 to satisfy this Wave 2E change.

**Route sketch only (not a finished YAML):**

~~~yaml
sceneByURL:
  - action: scrapeXPath
    url:
      - "bravo-japan.com/clips/"
      - "www.bravo-japan.com/clips/"
    scraper: clipSceneScraper
  - action: scrapeXPath
    url:
      - "bravo-japan.com/dvds/"
      - "www.bravo-japan.com/dvds/"
    scraper: dvdSceneScraper
# sceneByQueryFragment: absent under decision WS-2E-QF-001
# sceneByFragment: absent
driver:
  useCDP: true
~~~

Actual URL patterns/routing order must be independently verified against Stash's `strings.Contains` first-match behavior, including lookalike host, embedded query and overlapping-pattern negative cases. Pattern containment alone is not a strict hostname validator.

## 5. F-QF-02 — Update testing contract; preserve risk regression

**Agent F owns `tools/tests/test_bravo_clips.py` changes.** Replace the old `test_query_fragment_preserves_url` expectation with `sceneByQueryFragment` **absent**; assert `sceneByFragment` absent and an exact two-family Clips/DVD `sceneByURL` contract. Preserve all existing Clips Title, Code, URL, Duration, Details, poster-only Image and empty-Title regression tests.

Integrate `tools/tests/test_bravo_dvd_routes.py` and Agent B's **effective route** + **product-validity** tests, but keep its source risk evidence as historical. **Update** QF tests to expect **non-support**, not to accept a partial result. Adjust `EXPECTED_RED` annotations only when feature is truly implemented; preserve any `KNOWN_UPSTREAM_LIMITATION` test as a separately documented Stash matcher limitation.

**Do not convert an unsafe direct QF response into a passing xfail.** For installed Stash, explicitly verify an unsupported/safe rejection is returned and there are no Clips-derived Tags/canonical-only partial scene, unhandled panic, or unintended writes.

## 6. F-DVD-01 — Implement DVD-only source-grounded mappings

Agent A's nine-product/two-negative-page CDP evaluation reports these XPath expressions. They are **candidate inputs** requiring current exact-head fixture/Stash validation, not independent runtime proof:

| Field | Candidate XPath | Correctness / policy |
| --- | --- | --- |
| Title | `//h2[contains(.,'品番')]/preceding::h2[2]` | Source-reported 9/9; test extra headings and real value |
| Code | `//h2[contains(.,'品番')]/following::h2[1]` | Preserve string `046` and cross-check canonical identity |
| URLs | `//link[@rel='canonical']/@href` | Must not count an otherwise invalid 404 as valid product |
| Details | `//p[contains(@class,'font_8')]` | 084 node count 1 but text empty; leave semantic Details absent |
| Image | `//img[@alt!='' and contains(@src,'wixstatic')]/@src` | No logo / unrelated product; default exclude `BR-084soldout.jpg` |
| Date | `//h2[contains(.,'発売日')]/following::h2[1]` | Accept source-supported padded/unpadded Japanese dates |
| Source Label | `//h2[contains(.,'レーベル')]/preceding::h2[1]` | Do **not** map to Stash Studio without explicit approved semantic decision |
| Full DVD Duration | `//h2[contains(.,'収録時間')]/following::h2[1]` | Convert minutes to seconds only if whole DVD is a single Scene by approved policy |
| Tags | Site-generic keywords | **Omit** |
| Performers | No reliable source field | **Omit** |

Agent A reports SSR without product metadata; **`driver.useCDP: true` remains mandatory**. Avoid Wix component IDs, unrelated/global images and URL-derived synthetic Title/Code.

Metadata mapping decisions **must be logged**: 084 sold-out Image default reject; generic Tags omit; Label != Studio by default; whole-DVD total Duration should not be assigned to a component Scene without approval; no `groupByURL` in this Wave.

## 7. F-DVD-02 — Product validity and 404 fail-closed

Routing into `dvdSceneScraper` alone is insufficient. For `/dvds/00` and `/dvds/999999`, Agent A reports canonical URLs despite missing `品番`. Validate the **identity gate** on the source or in the consumer: product marker present, Title nonempty, Code nonempty and string-preserved, canonical/Code match expected product URL. Record expected/actual and reject partial misleading objects. Stash XPath fields are independent; **one gated Title does not automatically suppress URLs, Tags and other fields**.

Add synthetic wrong Title/Code/canonical/Logo, 084 empty Details, 084 sold-out artwork, 046 leading zero, Cloudflare/challenge, wrong product ID, malformed/wrong host and other false-positive tests. If Stash cannot enforce fail-closed semantics at YAML/consumer level, **mark residual data-write risk as BLOCKER**; do not describe API object output as validated product.

## 8. F-INT-01 — Integrate Agent B/C changes safely

- Pin incoming commit SHAs and review all changed paths; one final reviewed feature PR to `main`, not multiple overlapping auto-merges.
- B/C develop independently on the PR #93 Clips base; cherry-pick **only their isolated Wave 2E commits** when the accepted Clips baseline is merged. Do not re-import PR #93 code as extra changes.
- Agent C previously reported a test isolation failure from shared `failure-cloudflare.html` and a manifest `EXPECTED_RED` due to missing `dvdSceneScraper`. Verify latest exact-head results; resolve unexpected isolation failure without modifying archived fixture bytes. Do not disable DVD manifest permanently to force CI green.
- Preserve historical `tests/fixtures/bravo/bravo-fixtures.yml` unchanged, SHA-256 `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`.
- Any general fixture runner / validator redesign requires separate approval; Agent F's official write scope covers `scrapers/BRAVO.yml`, `scrapers/BRAVO.test.yaml` and shared Clips tests with reviewed isolated B/C assets.

## 9. F-QF-03 — Independent live QA matrix and release gates

**Gate A (exact HEAD):** build candidate source from complete Git history in an isolated directory, verify SHA-256/package provenance and run:

~~~bash
npm ci
node validator/index.mjs -a --ci
npm run validate-sort
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/run_fixture_manifests.py
python tools/check_evidence_contract.py
python tools/check_docs_index.py
python tools/check_scraper_semantics.py
python tools/scan_session_material.py
npm run format:check
~~~

Also verify generated BRAVO ZIP with `tools/build_scraper_source.py --verify-only` against that same actual output directory. Record all command exits and differentiate `PASS`, `FAIL`, `EXPECTED_RED`, `KNOWN_UPSTREAM_LIMITATION`, `BLOCKED` and `NOT_RUN`.

**Gate B** requires **authorized independent QA**, M0 preflight, exclusive `stash-test` lease, exact installed source package SHA, CDP operational, no uncontrolled Scene writes, and sanitized GraphQL logs/expected-vs-actual. At minimum:

| Case | Entry | Expected |
| --- | --- | --- |
| QF-01 | Clips 284 via URL | Accepted Clips Title/Code/URLs/Duration; poster-only image |
| QF-02 | Clips 282 via URL | Same, no regression |
| QF-03 | DVD 234 via URL | DVD handler; valid source-derived metadata |
| QF-04 | DVD 084 via URL | Correct handler; empty Details respected, sold-out Image policy |
| QF-05 | DVD 234 via QueryFragment | Safe **unsupported** response, never Clips-derived partial metadata |
| QF-06 | DVD 084 via QueryFragment | Safe **unsupported** response |
| QF-07 | Clips 284 via QueryFragment | Safe unsupported; intentional compatibility change documented |
| QF-08 | Scene Fragment input | No `sceneByFragment` capability |
| DVD-NEG-01/02 | DVD 00 / 999999 via URL | 404 **not** accepted as valid product despite canonical |
| DVD-046/281 | DVD via URL, where available | Code/Title/URL correct; `046` leading zero |
| URL-COLLISION | embedded pattern / host lookalike | Characterize upstream matching limitation; do not silently claim strict host validation |

A config-only missing-key check or offline success does **not** clear QF blocker. If removing the QF handler causes an **unhandled upstream panic**, mark `FAIL/UPSTREAM_BLOCKED`, not a successful unsupported response; coordinate upstream independently under #97.

**Gate C:** review exact-head CI, CodeQL, fixture/evidence contract, package integrity, source-provenance, security, docs, rollback and explicit maintainer approval. **Do not auto-merge or deploy to production.** Rebase or changes to YAML/fixtures/package invalidate old exact-head evidence.

## 10. Stop conditions and rollback

Stop before official YAML modification if G0/G1 not accepted; stop QueryFragment removal if an essential direct caller lacks migration; stop release if false metadata, unhandled panic, loss of Clips URL behavior, invalid/404 accepted as product, leaking session evidence, archive checksum mismatch, missing independent Gate B, or unresolved required CI.

Rollback candidate to the accepted Clips-only source package SHA; log that the old package **still contains orphaned QueryFragment behavior**, so a rollback is not a QF security remediation. Do not assume changing the YAML rolls back previously written Scene metadata.

## 11. Deliverables

1. A Draft Wave 2E implementation PR against `main` after the accepted Clips baseline, with one reviewed BRAVO YAML writer.
2. `WAVE2E-F-DVD-INTEGRATION-REPORT.md`: accepted SHA; handoff and cherry-picked SHA inventory; field mapping; QF caller audit/decision execution; route/fixture negative tests; package provenance; exact-head Gate A; independent Gate B; Gate C; policy choices; risks and rollback.
3. `WS-2E-QF-001` implementation evidence: old QF removed, old assertions updated, direct caller inventory, QF-01..08 outcomes, independent QA verdict.
4. Revised `docs/60-live-test-status.md` / `scrapers/BRAVO.test.yaml` with observed results only, no fabricated PASS.
5. Final Controller review package. An unmerged Draft is an acceptable honest handoff; `DVD_URL_SCRAPING_FIXED_VERIFIED` requires all applicable gates.

## 12. Mandatory handoff YAML

~~~yaml
ASSIGNMENT_ID: WAVE2E-F-DVD-INTEGRATION-20261103
WORKSTREAM_ID: WS-2E-30
AGENT_ROLE: Agent F
ASSIGNMENT_VERSION: v2
ASSIGNMENT_STATUS: ASSIGNED
REPOSITORY: daniel-yfc/stash-scarpers
BRANCH: feat/e2e-bravo-dvds
BASE_SHA: "<accepted Clips main SHA after authorized PR93 merge>"
HEAD_SHA: "<candidate commit or NOT_COMMITTED>"
DECISION_ID: WS-2E-QF-001
QUERY_FRAGMENT_DECISION: REMOVE_ORPHAN_QUERY_FRAGMENT_IN_WAVE2E
QUERY_FRAGMENT_IMPLEMENTATION: NOT_STARTED
QUERY_FRAGMENT_COMPATIBILITY_AUDIT: NOT_RUN
DECISION_EXCEPTION: NONE
CHANGED_FILES: []
DELIVERABLES: []
EVIDENCE: []
TEST_RESULTS: []
KNOWN_LIMITATIONS: []
DEPENDENCIES:
  - "Agent A: G1 independently reviewed evidence or documented Controller risk decision"
  - "Agent B: effective routing, QF and 404 validity tests"
  - "Agent C: DVD fixtures and corrected isolation CI"
  - "Agent D: PR #93 independent live Gate B + approved merge"
  - "Independent QA: DVD/QF negative Gate B"
  - "Controller: metadata semantic policies, Gate C and merge"
GATE_0: BLOCKED
GATE_1: PROVISIONAL_NOT_INDEPENDENTLY_ACCEPTED
GATE_A: NOT_RUN
GATE_B: NOT_RUN
GATE_C: NOT_RUN
QUERY_FRAGMENT_RELEASE_BLOCKER: MITIGATION_APPROVED_PENDING_VERIFICATION
RELEASE_BLOCKERS:
  - "G0_BASELINE_BLOCKED_LIVE_QA"
  - "G1_INDEPENDENT_REPLAY_PENDING"
  - "QF_MITIGATION_NOT_IMPLEMENTED_OR_VERIFIED"
RISKS_AND_DECISIONS: []
HANDOFF_STATUS: BLOCKED
MERGE_STATUS: NOT_AUTHORIZED
~~~

## 13. Definition of Done

- [ ] G0 accepted PR #93 independent live QA + authorized merge, exact accepted SHA known.
- [ ] G1 independent evidence replay or explicitly scoped Controller exception.
- [ ] QF direct-caller audit completed; no unresolved indispensable caller.
- [ ] `sceneByQueryFragment` removed from Wave 2E candidate; `sceneByFragment` remains absent.
- [ ] Clips URL 284/282 preserved; DVD URL 234/084 and sampled 046/281 correct.
- [ ] QF-05/06/07 safe unsupported on installed Stash **without panic or wrong metadata**.
- [ ] DVD 404, wrong identity, challenge, logo and empty Details cases fail closed.
- [ ] Generic Tags omitted; Studio/Duration/084 cover policies recorded.
- [ ] Historical fixture and SHA unchanged; new DVD tests and exact-head Gate A PASS.
- [ ] Independent Gate B PASS; Gate C/CodeQL/CI and package SHA complete.
- [ ] Rollback documented and maintainers explicitly approve merge; **no upstream #97 closure by this task**.

**Final instruction:** Implement the smallest reversible DVD URL feature, prevent QF-derived false metadata, preserve Clips URL mode, and treat evidence gaps or runtime panics as blockers rather than green results.
