---
doc_id: HANDOFF-PR93-DEF01-R3-20261104
title: PR #93 DEF-01 R3 — Controller Decision and Execution Handoff
status: superseded
layer: qa
owner: controller
audience:
  - agent
  - maintainer
applies_to:
  - pr-93
  - wave-1b
  - wave-2e
last_verified: "2026-11-04"
authority: assignment
---

# Controller Handoff — PR #93 DEF-01 R3 / Wave 2E dependencies

> **SUPERSEDED FOR IMMEDIATE ACTION (2026-11-04):** Controller has explicitly authorized **temporarily omitting Clips Scene.Duration from the *next* PR #93 candidate**, pausing A2/Core repair while preserving the source extraction XPath, seconds recipe and full history for later re-enable. **Current decision:** [WS-2E-DEF01-DEFER-20261104](PR93-DEF01-DURATION-DEFER-DECISION-20261104.md). **Current binding assignment:** [Duration Defer Handoff](PR93-DEF01-DURATION-DEFER-HANDOFF-20261104.md). This R3 document, including A2-priority and DURATION_WAIVER_APPROVED=false, describes the **earlier historical state**; it must not be read as the current execution directive. v1–v4 QA verdicts remain unchanged (v4 FAIL); G0 and Agent F remain blocked pending a new exact-head Gate B under the revised scope.


**Assignment ID:** `WAVE2E-CONTROLLER-PR93-DEF01-R3-HANDOFF-20261104`  
**Date:** 2026-11-04 (Asia/Taipei)  
**Repository:** [daniel-yfc/stash-scarpers](https://github.com/daniel-yfc/stash-scarpers)  
**Role:** Controller → independent Agent D, Agent G, Agent C, Agent F  
**Scope:** Evidence publication, root-cause independent replay, decision preparation; **no authorization to modify Stash Core, test/live Stash, PR #93 scraper YAML, or merge.**  
**Status:** `HANDOFF_PUBLISHED / G0_BLOCKED / G1_PROVISIONAL`

## 1. Current exact-source snapshot and evidence hierarchy

| Component | Exact ref / link | Observed status |
| --- | --- | --- |
| `main` | `e1f4ca420eb88b722129a96580f9102bb979fb77` (at handoff preflight) | PR #93 still not merged; future merges must refresh this SHA |
| [PR #93 Clips](https://github.com/daniel-yfc/stash-scarpers/pull/93) | `fix/e2e-bravo-clips` @ `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6` | Draft; unmerged; exact-head CI 9 success, 1 skipped; **Gate B v4 FAIL** |
| [Agent D v4 QA](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261104-v4.md) | branch `docs/qa-pr93-gateb-20261103` @ `654b239ce263208cb71096813e6a674494d1ca37` | Evidence S1–S12 and SHA manifest published; PR #93 [v4 verdict comment](https://github.com/daniel-yfc/stash-scarpers/pull/93#issuecomment-6621303566) posted |
| [Agent G R3 root-cause report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/pr93-def01-r3-type-isolation/docs/qa/PR93-DEF01-R3-TYPE-ISOLATION-REPORT.md) | `docs/pr93-def01-r3-type-isolation` @ `841aa35c8243fcfcf1c40a7af5e49b9060ed1579` | `END_TO_END_REPRODUCED_BY_AGENT_G`; Go test source exists **only in isolated local copy**, not archived for independent execution |
| [Agent G machine handoff](https://github.com/daniel-yfc/stash-scarpers/blob/docs/pr93-def01-r3-type-isolation/docs/qa/PR93-DEF01-R3-HANDOFF.yaml) | same `841aa35` | Go Test A/B/C claimed PASS, Stash `9e9ad972`; Agent D independent replay pending |
| [Agent C DVD fixtures v2.3](https://github.com/daniel-yfc/stash-scarpers/blob/test/e2e-bravo-dvd-fixtures/docs/research/wave2e/BRAVO-DVD-FIXTURE-REPORT.md) | `test/e2e-bravo-dvd-fixtures` @ `8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5` / [Draft PR #99](https://github.com/daniel-yfc/stash-scarpers/pull/99) | **DVD Duration and Studio production mappings omitted**; `expect` preserves source XPath/values. Python 336 passed; two workflow checks fail because official DVD scraper is not implemented |
| [Wave 2E plan and Agent F v2](https://github.com/daniel-yfc/stash-scarpers/blob/docs/e2e-wave-2e-upstream-panic-20261101/docs/67-wave2e-agent-f-assignment-v2.md) | docs PR #98 | F official BRAVO YAML integration remains gated by G0/G1 |

**Do not combine HEAD-specific results.** v1 `NOT_RUN`; v2 @ `86e34a2` `FAIL`; v3 @ `ce7ef6c` `FAIL`; v4 @ `d6d6fbf` `FAIL`. Agent G's R3 Go reproduction **is not another live Gate B run**.

## 2. Controller acceptance / technical finding

**Controller review verdict:** `R3_REPORT_ACCEPTED_FOR_NEXT_STAGE / INDEPENDENT_REPRODUCTION_PENDING`.

Agent G's source-level and locally executed Go evidence at Stash revision `9e9ad972643320e737c711884f10e4285f0f3a88` provides a precise probable root cause for DEF-01:

`xpathQuery.runQuery` returns strings → `mappedConfig.process` stores strings through `setSingleValue` → even JavaScript `postProcess` returns a string → `mappedResult.scrapedScene` uses `r.IntPtr("Duration")`, whose strict `v.(int)` type assertion fails for `"1800"` and returns `nil` → `ScrapedScene.Duration` becomes null.

- **Verified source shape:** `pkg/scraper/mapped_result.go`, `mapped_config.go`, `mapped_postprocessing.go` and `xpath.go` at `9e9ad972` support that flow.
- **Author-side reproduction:** R3 report states Test A (direct int/string), B (full pipeline with three XPath variants), C (no-JS/JS/fixed), and Go scraper-package regression all PASS; `develop` at checked `944dd694` had no relevant fix.
- **Independence gap:** the executable `r3_def01_type_isolation_test.go` is untracked in the author's isolated Stash checkout. The current GitHub report is **not** a reproducible test-source delivery. Independent reviewer must obtain the source under a sanitized, reviewable, pinned commit/artifact and replay. Do not claim `INDEPENDENTLY_VERIFIED` based solely on report assertions.
- **Stop selector churn:** No fourth speculative XPath change to PR #93. Three distinct selector shapes failed live while offline DOM extraction succeeded; type incompatibility is a more causally complete explanation.

**Existing actual Gate B verdict stays `FAIL`.** DEF-02 Details remains `CLOSED_LIVE_VERIFIED`; DEF-01 Duration remains `OPEN_P1`. Reproducing a bug does not fix it.

## 3. Decision: selected design for technical evaluation, not deployment authorization

**Decision ID:** `WS-2E-DEF01-ROOTCAUSE-001`  
**Decision state:** `A2_PREFERRED_FOR_PROPOSAL / FINAL_REMEDIATION_PENDING`.

Three options:

| Option | Trade-off | Current disposition |
| --- | --- | --- |
| **A2 — Dedicated strict Duration conversion in `scrapedScene()`** | Narrow semantic change, preserves strict `IntPtr` expectations and existing other field behavior; requires fork/upstream review, deployable runtime and live QA | **PREFERRED for isolated proposal/tests**, not authorized for Stash deployment |
| A1 — String parse in shared `IntPtr()` | Smaller diff but changes generic helper semantics, and future callers may be affected | Secondary only if upstream maintainers justify |
| B — Scoped missing-Duration acceptance | Could unblock Clips delivery without runtime change, but removes required metadata; must have explicit time-bound risk decision, contract revision and independent QA | **NOT APPROVED**; fallback if deployable fix is unavailable and user accepts feature loss |

No core change is authorized in this handoff. Do **not** alter `stash-scarpers#93` to include `stashapp/stash` Go modifications; do **not** create a new upstream Issue/PR or deploy Stash solely based on this selected research direction.

### A2 numerical contract for the proposed separate runtime patch

- Accept strictly valid decimal nonnegative digit-only string seconds, e.g. `"1800"` → `1800` and `"2700"` → `2700`.
- Distinguish **present zero** `"0"` → `&0` from missing value → `nil`.
- Reject empty, whitespace-only, negative, fractional, contaminated (`"12x"`), invalid and overflow values without truncation, coercion or fabrication.
- Explicitly define whether **leading/trailing whitespace** is rejected or trimmed; do not silently accept values under tests that claim strictness.
- Preserve already supported native-int behavior and other Scene fields.
- Verify no effect on Movie/Group Duration, which use a string mapping path.
- Test exact pipeline, not just parsing helper; confirm postProcess-generated `"1800"` becomes the expected typed `*int`.
- Keep correction separate from BRAVO selector policy and [Issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97) unmatched-URL panic.

## 4. P0 — Agent D independent Go replay and evidence closure

**Assignment ID:** `WAVE2E-D-PR93-DEF01-R3-INDEPENDENT-REPLAY-20261104`

1. Pin Stash source SHA `9e9ad972643320e737c711884f10e4285f0f3a88`; obtain the **complete exact test source** `pkg/scraper/r3_def01_type_isolation_test.go` from Agent G's isolated checkout. Do not represent a descriptive report as executable evidence.
2. Sanitize review artifact; publish the test source in a **separate, clearly scoped QA branch/artifact** or in a controlled verifiable location with SHA-256. **Do not** move PR #93 HEAD. Never publish session tokens/URLs or private rendered DOM.
3. Independently inspect/test A: native int vs string; B: actual mapped pipeline (forward, reverse and literal selectors); C: JS vs no JS vs fixed, and report dynamic types and final `ScrapedScene.Duration`. Use source-build's Go version and `TMPDIR` suitable for available storage.
4. Run `go test ./pkg/scraper/ -count=1` on the exact tested source; record exact command, stdout/stderr, exit codes, versions, test-file digest and limitations.
5. Check latest relevant upstream revisions for fixes; do not extrapolate beyond the checked SHA.
6. Record distinct verdicts: `ROOT_CAUSE_INDEPENDENT_REPLAY=PASS | FAIL | BLOCKED`; `GATE_B_V4=FAIL`; `DEF_01=OPEN_P1`.
7. No new `stash-test` lease required for isolated Go-only replay. Do not install packages, query live Stash, or declare independent Gate B PASS.

**Expected deliverable:** `PR93-DEF01-R3-INDEPENDENT-REPLAY-REPORT.md` + sanitized executable test artifact + machine-readable handoff, linked from the PR #93 audit trail after review.

## 5. P0 — Agent G narrow A2 upstream fix proposal (design/test only)

**Assignment ID:** `WAVE2E-G-PR93-DEF01-A2-PROPOSAL-20261104`

- Supply the exact R3 Go test source to Agent D and document its digest/provenance.
- In a separate Stash source checkout, **design and test** a minimal dedicated `Duration` conversion helper used only by `mappedResult.scrapedScene()`, leaving shared `IntPtr()` semantics untouched.
- Include native int, string seconds, `0`, missing key, empty/spaces, malformed, negative, fractional, overflow, type mismatch, postProcess and fixed-value end-to-end cases. Record tests failing before patch and passing after patch.
- Submit a **reviewable patch/proposal** and A2 vs A1 compatibility assessment only; no upstream push/PR, unauthorized deployment, runtime changes or edits to PR #93.
- If an upstream core fix is necessary, obtain separate explicit authorization for that workstream and separate independent QA before any test-instance changes.

**Expected deliverable:** `PR93-DEF01-A2-PROPOSAL.md`, separate patch/reproducer location, dependency analysis and rollback strategy.

## 6. P1 — Controller resolution and future live QA

After Agent D independently replays and Agent G supplies A2 evidence, Controller chooses:

- **A (default preferred if deployable):** a real corrected Stash build must be authorized, built, installed on isolated `stash-test`, and separately validated with exact Stash + BRAVO package SHAs. Only then Agent D may execute a **new** authorized M0 / exclusive lease Gate B against Clips 284/282/283 + QueryFragment, preserve Details/Title/Code/URLs/Image and negative regressions, and verify rollback.
- **B (conditional only):** if no deployable fix is feasible and the user explicitly accepts losing Duration, create a **new, bounded acceptance contract**, update required tests/evidence and independently verify all remaining obligations. Retain v4 FAIL as historical truth; do not relabel it PASS retroactively.

Until either path is approved and verified, `G0=BLOCKED`, PR #93 remains Draft/unmerged, and `AGENT_F_RUNTIME_INTEGRATION=BLOCKED`.

## 7. P1 — Agent C v2.3 DVD mapping policy (separate from Clips DEF-01)

**Reference:** [PR #99 / Agent C v2.3](https://github.com/daniel-yfc/stash-scarpers/pull/99), `8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5`.

- **DVD Duration:** the observed value is **whole-DVD source minutes**, not automatically a Stash **Scene** duration. Do **not** map to production `Scene.Duration`. Keep exact XPath, cardinality and source minutes in the fixture's `expect` block; omit from `mappedExpect`.
- **DVD Studio:** source `レーベル` is a **Label**, not approved as target Stash Studio. Keep exact XPath/cardinality/value in `expect` but omit production `mappedExpect.Studio`.
- **084 Image:** sold-out artwork is not an approved cover; omit as Scene Image. Site-global keywords must not become Tags.
- **No silent policy reversal:** a future Label→Studio mapping requires a traceable explicit Controller decision; whole-DVD-as-one-Scene policy requires separate approval. A source XPath hit is **not** a target-field authorization.
- **Tests:** `tools/tests/test_bravo_dvds.py` has 24 policy/fixture tests, including `test_metadata_policy_duration_and_studio_not_mapped`. Latest exact-head CI observed 336 Python passed, with **two manifest-related red checks caused by the still-missing DVD scraper**. `READY_FOR_REVIEW` is not Gate A/B PASS.
- **Critical scope separation:** this DVD `Duration/Studio` omission **does not waive** PR #93 **Clips Duration** (expected 1800 seconds for 284/282/283), which remains `DEF-01_OPEN_P1`. Do not apply C's DVD mapping policy to the Clips Gate B contract.

Agent C needs no fourth fixture rework solely to make the absent-handler manifest green. F may integrate C's assets only after accepted Clips G0 and DVD evidence G1, using isolated commits rather than inheriting unrelated PR #93 changes.

## 8. Agent F / Wave 2E stop conditions and handoff statuses

- `G0`: `BASELINE_BLOCKED_LIVE_QA` (PR #93 Gate B v4 FAIL).
- `G1`: `PROVISIONAL_NOT_INDEPENDENTLY_ACCEPTED` (Agent A author-side DOM + machine-readable results present, independent replay not accepted).
- `WS-2E-QF-001`: `DESIGN_SELECTED`, **not implemented**; the future DVD candidate removes orphan BRAVO QueryFragment only after compatibility check and G0/G1. Do **not** retroactively remove QF from PR #93.
- Agent F: read-only design/compatibility work permitted; **official `scrapers/BRAVO.yml` changes, implementation branch, merge, production/test Stash modifications are not authorized** under this handoff.
- Issue #97 unmatched-URL panic remains separate; root-cause fix for Duration does not clear #97.

## 9. Required future handoffs and acceptance

~~~yaml
CONTROLLER_HANDOFF_ID: WAVE2E-CONTROLLER-PR93-DEF01-R3-HANDOFF-20261104
REPOSITORY: daniel-yfc/stash-scarpers
PR: 93
PR93_HEAD_SHA: d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6
PR93_GATE_B_V4: FAIL
DEF_01_DURATION: OPEN_P1
DEF_02_DETAILS: CLOSED_LIVE_VERIFIED
AGENT_G_R3_SOURCE_BRANCH: docs/pr93-def01-r3-type-isolation
AGENT_G_R3_SOURCE_SHA: 841aa35c8243fcfcf1c40a7af5e49b9060ed1579
R3_ROOT_CAUSE_STATUS: END_TO_END_REPRODUCED_BY_AGENT_G
INDEPENDENT_GO_REPLAY: PENDING
REPRODUCER_SOURCE_IN_REPO: false
ROOT_CAUSE_DECISION: A2_PREFERRED_FOR_PROPOSAL
ROOT_CAUSE_FIX_IMPLEMENTED: false
STASH_CORE_MODIFICATION_AUTHORIZED: false
STASH_TEST_OPERATION_AUTHORIZED: false
STASH_TEST_LEASE: NONE
UPSTREAM_ISSUE_OR_PR_AUTHORIZED: false
DURATION_WAIVER_APPROVED: false
AGENT_D_NEXT: WAVE2E-D-PR93-DEF01-R3-INDEPENDENT-REPLAY-20261104
AGENT_G_NEXT: WAVE2E-G-PR93-DEF01-A2-PROPOSAL-20261104
DVD_C_REF: 8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5
DVD_C_DURATION_TO_SCENE: OMIT
DVD_C_STUDIO_FROM_LABEL: OMIT
DVD_C_SOURCE_EXPECT_DURATION_AND_LABEL: RETAIN
DVD_C_FIXTURE_STATUS: READY_FOR_REVIEW_EXPECTED_RED_PENDING_F
G0: BLOCKED
G1: PROVISIONAL
AGENT_F_INTEGRATION: BLOCKED
MERGE_AUTHORIZATION: NOT_GRANTED
HANDOFF_STATUS: ASSIGNED_NO_RUNTIME_AUTHORIZATION
~~~

**Audit rule:** Only independent, exact-source replay may promote `INDEPENDENT_GO_REPLAY` to PASS. Only new authorized live Gate B against a corrected deployed runtime or formally revised contract may change G0. Do not rewrite v1–v4 history or conflate the DVD mapping omission with the Clips defect.
