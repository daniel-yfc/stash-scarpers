---
doc_id: DOC-E2E-66
title: Wave 2E Controller Decision WS-2E-QF-001 — BRAVO QueryFragment
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
    - query-fragment
    - controller-decision
    - bravo
---

# Wave 2E — Controller Design Decision: QueryFragment Risk

**Decision ID:** `WS-2E-QF-001`  
**Decision date:** 2026-11-03 (Asia/Taipei)  
**Selected design:** `REMOVE_ORPHAN_QUERY_FRAGMENT_IN_WAVE2E`  
**Decision status:** **`DESIGN_SELECTED / IMPLEMENTATION_NOT_STARTED / LIVE_UNVERIFIED`**  
**Applies only to:** `scrapers/BRAVO.yml` in the **future Wave 2E candidate**, not all scrapers and not the pending Clips-only PR #93.  
**Implementation owner:** **Agent F**, the sole editor of the official BRAVO YAML.  
**Execution/merge:** G0 (Clips baseline) and G1 (DVD source evidence) remain binding; this decision **does not authorize** bypassing gates, merging PRs, live-instance changes or production deployment.

## 1. Verified problem and evidence level

In the [Wave 1B candidate BRAVO YAML](https://github.com/daniel-yfc/stash-scarpers/blob/86e34a24642dad2e64ae984e7e9182605e98cbcf/scrapers/BRAVO.yml), `sceneByURL` targets `/clips/` through `clipSceneScraper` and the separate `sceneByQueryFragment` uses `queryURL: "{url}"` with `scraper: clipSceneScraper`. There is **no** `sceneByName` or `sceneByFragment`.

In the tested Stash source revision `9e9ad972`:

- [`pkg/scraper/definition.go`](https://github.com/stashapp/stash/blob/9e9ad972/pkg/scraper/definition.go) defines `SceneByQueryFragment *ByFragmentDefinition` as a **single**, not per-URL, handler; `SceneByURL []*ByURLDefinition` is a separate list. Scene Name is advertised only when both `SceneByName` and `SceneByQueryFragment` exist.
- [`pkg/scraper/defined_scraper.go`](https://github.com/stashapp/stash/blob/9e9ad972/pkg/scraper/defined_scraper.go) uses the configured QueryFragment handler for Scene fragment input; it **does not** dispatch to DVD `sceneByURL` based on the requested URL. A caller directly invoking the fragment scraper remains a possibility even if the usual Name-search UI is not advertised.
- The [Agent B offline routing and QueryFragment report](https://github.com/daniel-yfc/stash-scarpers/blob/test/e2e-bravo-dvd-routing/WAVE2E-B-ROUTING-REPORT.md), `7/`11, applies Clips XPath selectors to four historical DVD DOM fixtures (046/281/173/215). It reports **empty Title/Code/Duration/Details/Image but a plausible canonical URL and shared site-generic Tags**. Verdict `FALSE_METADATA_RISK_CONFIRMED` is **offline only**, not proof of an actual Stash database write.
- Agent B's latest updated tests separate URL routing from product validity and pin 404 partial-metadata hazards. DVD mode's independent live Gate B is still missing.

The existing generic [Quality Gate Rule 4](21-quality-gate-rules.md) previously claimed `sceneByQueryFragment: "{url}"` is necessarily safe. That claim concerns **URL placeholder expansion**, not correctness of the **selected field-mapping handler**. A valid expanded DVD URL can still be processed by the wrong Clips XPath. The narrowly scoped BRAVO policy clarification is recorded in that rule.

## 2. Alternatives evaluated

| Option | Benefit | Cost and residual failure | Decision |
| --- | --- | --- | --- |
| **A — Keep current QF and document DVD as URL-only** | No change to existing direct fragment clients | A direct DVD QF invocation can still produce misleading partial metadata; documentation does not prevent it | **REJECTED** |
| **B — Keep QF with validated Clips-only guards** | Could preserve proven direct QF callers | Requires proving every populated field (including canonical/Tags) is guarded in the actual Stash XPath engine; more moving parts and risk of silent failure | **CONDITIONAL FALLBACK ONLY** |
| **C — Remove orphan `sceneByQueryFragment` in Wave 2E** | Removes the configured cross-mode QueryFragment route; minimal and reversible; retains both URL modes | May break existing automation directly invoking BRAVO's QF entry; requires caller audit and runtime negative verification | **SELECTED** |

**Rationale:** Without `sceneByName`, BRAVO has no complete advertised Name-search flow that needs this QueryFragment. URL scraping does not depend on the QueryFragment setting. Avoiding wrong-but-plausible metadata has priority over preserving an unverified direct-call compatibility path.

This is **not** a claim that no direct caller exists: caller discovery and independent runtime testing remain prerequisites.

## 3. Binding implementation contract for Agent F

1. **Preflight:** search repo workflows/tests/GraphQL integrations and known authorized instance usage for direct BRAVO `sceneByQueryFragment` callers. Document actual search scope and limitations, and whether they can migrate to URL mode. If an indispensable caller exists, set `DECISION_EXCEPTION=REQUIRED_QUERY_FRAGMENT_CONSUMER_FOUND`, **stop the removal** and request Controller review of option B. Do not silently restore the unsafe original handler.
2. **G0/G1 first:** PR #93 must pass independent Clips Gate B, be explicitly authorized and merged; Agent A source evidence must be independently accepted or have a documented limited Controller risk decision. Until then, produce only planning/design/test work, **not official runtime YAML changes**.
3. **Target candidate:** on `feat/e2e-bravo-dvds`, **remove** the entire `sceneByQueryFragment` entry; keep `sceneByFragment` **absent**. Add exactly the expected `sceneByURL` route families: `/clips/` → `clipSceneScraper` and `/dvds/` → `dvdSceneScraper`. Do not rewrite existing Clips XPath as a side effect. Do not change PR #93 retroactively.
4. **Test-contract migration:** replace the old `tools/tests/test_bravo_clips.py::test_query_fragment_preserves_url` expectation with a **QF-absent** assertion. Preserve test coverage for Clips Title, Code, URL, duration, poster-only Image, Title-less behavior and archived evidence. Update Agent B's isolated QF tests to assert the new contract without hiding the original risk reproduction. Retire strict `EXPECTED_RED` only when the DVD feature is present; keep independent `KNOWN_UPSTREAM_LIMITATION` cases.
5. **Actual behavior:** run authorized independent Stash/CDP Gate B against the exact installed package. A config assertion alone **cannot** prove that direct fragment calls return a safe unsupported result; an upstream panic, silent invalid object or wrong metadata is **not** a passing negative case.
6. **No scope expansion:** do not add a new `sceneByName`, second QF handler, undocumented custom dispatch, Stash core patch or generic framework refactor under this decision. Track unmatched-URL panic separately under [local #97](https://github.com/daniel-yfc/stash-scarpers/issues/97).

### Required independent QA matrix (exact-head, installed candidate)

| Case | Entry / input | Acceptance oracle |
| --- | --- | --- |
| QF-01 | URL Clips 284 | Clips fields and original accepted behavior retained |
| QF-02 | URL Clips 282 | Same; no regression |
| QF-03 | URL DVD 234 | DVD handler, source-true Title/Code/URLs |
| QF-04 | URL DVD 084 | DVD handler; no fabricated Details/cover |
| QF-05 | QueryFragment DVD 234 | **Safe unsupported**; no Clips-derived partial scene |
| QF-06 | QueryFragment DVD 084 | **Safe unsupported**; no Clips-derived partial scene |
| QF-07 | QueryFragment Clips 284 | Intentionally unsupported; record actual direct-caller compatibility effect |
| QF-08 | Scene Fragment input | No `sceneByFragment` reintroduced |

On QF-05/06/07, report actual supported GraphQL operation, response, errors, Stash build, candidate package SHA and trace. **An unhandled panic is FAIL/UPSTREAM_BLOCKED, not an acceptable unsupported outcome.** Do not invent a GraphQL field if the installed schema lacks it.

The selected design addresses **QF cross-mode misuse** only. It does **not** fix Stash `strings.Contains` host-lookalike URL matching, product-invalid 404 canonical results, or the separate upstream unmatched-URL panic.

## 4. Policy exception and impact

[`docs/21-quality-gate-rules.md`](21-quality-gate-rules.md) now clarifies:
- `sceneByQueryFragment`, **when present**, must preserve the selected URL with `queryURL: "{url}"` under the existing local policy.
- It is **not globally mandatory** for URL-only scrapers; preserving a correct URL does not prove the handler's field mapping is safe.
- **BRAVO Wave 2E has a specific selected-design exception** to omit the orphaned QF entry, subject to compatibility preflight and live verification. This does **not** waive other scraper policies.

Keep [Agent B report](https://github.com/daniel-yfc/stash-scarpers/blob/test/e2e-bravo-dvd-routing/WAVE2E-B-ROUTING-REPORT.md) as the **historical risk reproduction**. Agent F's updated [v2 assignment](67-wave2e-agent-f-assignment-v2.md) supersedes earlier “preserve existing Clips QueryFragment” instructions in [v1 Addendum](65-wave2e-agent-f-assignment-addendum.md) and [Wave 2E master plan](61-bravo-dvd-wave-2e.md) **only for this narrowly decided configuration**.

## 5. Release, rollback and stop conditions

- **Design selected ≠ mitigation implemented.** On YAML change but before live QA use `MITIGATION_IMPLEMENTED_UNVERIFIED`. Only independently verified behavior allows `RESOLVED_VERIFIED`.
- **Stop** for direct callers that cannot migrate, stale baseline, unresolved G1, schema rejection, newly failing Clips URL tests, returning false metadata, QF panic, or lack of exclusive authorized `stash-test` access.
- **Rollback:** restore the accepted Clips-only package version and SHA and document that its orphaned QueryFragment risk remains; a rollback is a feature rollback, **not** a security fix. No unapproved production install or data writes.
- **Merge:** maintain Draft until exact-head CI/CodeQL, Gate A, independent Gate B, Gate C, and explicit maintainer decision. Do not auto-merge.

## 6. Machine-readable decision record

~~~yaml
DECISION_ID: WS-2E-QF-001
DECISION_DATE: "2026-11-03"
DECISION_STATUS: DESIGN_SELECTED_IMPLEMENTATION_PENDING
DECISION: REMOVE_ORPHAN_QUERY_FRAGMENT_IN_WAVE2E
SCOPE: "BRAVO Wave 2E candidate only"
EVIDENCE_LEVEL: "Agent B offline CONFIRMED; Stash live QueryFragment not verified"
SOURCE_BUILD: "Stash 9e9ad972 / PR #93 86e34a2 reference"
RATIONALE: PREVENT_CROSS_MODE_FALSE_METADATA
URL_MODE_CLIPS: PRESERVE
URL_MODE_DVD: IMPLEMENT
SCENE_BY_FRAGMENT: KEEP_ABSENT
SCENE_BY_QUERY_FRAGMENT: REMOVE_AFTER_COMPATIBILITY_PREFLIGHT
COMPATIBILITY_EXCEPTION: REQUIRED_QUERY_FRAGMENT_CONSUMER_FOUND
IMPLEMENTATION_OWNER: Agent F
IMPLEMENTATION_STATUS: NOT_STARTED
G0_DEPENDENCY: BLOCKED_LIVE_QA
G1_DEPENDENCY: INDEPENDENT_ACCEPTANCE_PENDING
RELEASE_BLOCKER: MITIGATION_APPROVED_PENDING_VERIFICATION
GATE_B_REQUIREMENT: INDEPENDENT_NEGATIVE_E2E
STASH_INSTANCE_CHANGE: NOT_AUTHORIZED
MERGE_AUTHORIZATION: NOT_GRANTED
~~~
