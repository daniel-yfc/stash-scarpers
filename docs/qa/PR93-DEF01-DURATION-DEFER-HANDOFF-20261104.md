---
doc_id: HANDOFF-PR93-DEF01-DURATION-DEFER-20261104
title: Controller Handoff — BRAVO Clips Scene Duration temporarily unmapped
status: active
layer: qa
owner: controller
audience: [agent, maintainer]
applies_to: [pr-93, wave-1b, wave-2e]
last_verified: "2026-11-04"
authority: assignment
---

# Current Controller Handoff — Clips Duration omission with restoration path

**Assignment ID:** `WAVE2E-CONTROLLER-PR93-DURATION-DEFER-HANDOFF-20261104`  
**Decision:** [`WS-2E-DEF01-DEFER-20261104`](PR93-DEF01-DURATION-DEFER-DECISION-20261104.md), the authoritative temporary-omission policy and **non-active exact original XPath + JS restoration recipe**.  
**Supersedes immediate A2 work:** [Historical R3 handoff](PR93-DEF01-R3-CONTROLLER-HANDOFF-20261104.md), retained for its root-cause report and option analysis.  
**Repository:** [daniel-yfc/stash-scarpers](https://github.com/daniel-yfc/stash-scarpers).  
**PR #93 reference HEAD:** `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6`, still Draft/unmerged and **still contains active Duration** at the time of this handoff.

## 1. Binding policy and boundaries

- **Clips Scene.Duration:** TEMPORARILY **not** mapped to production. **Do not remove source extraction knowledge**: 30 minutes on 284/282/283, synthetic 45 minutes on 285, XPath, seconds conversion, source fixtures and negative cases. Keep a small future code-change path to restore production Duration once supported and verified. Do not invent an unsupported `enabled: false` key.
- **Duration defect status:** `DEFERRED_BY_CONTROLLER_SCOPE` after the new omission commit; `UPSTREAM_BUG_OPEN`; **not** `FIXED`. Agent G R3 Go root cause is reproduced by the author, independent Go replay still pending. A2/Stash Core repair and further XPath iteration **paused** for now.
- **Historical independent Gate B:** v1 NOT_RUN, v2 FAIL, v3 FAIL, v4 @ `d6d6fbf` FAIL; **do not retroactively label any PASS**. New scope requires a new candidate SHA and new independent Gate B.
- **Other fields:** preserve DEF-02 Details (live-verified), Title, Code, URLs, Tags, Date, Studio, Image poster-only, Clips URL and original QueryFragment, Title-less and nonexistent URL negative guards. No DVD routes or `dvdSceneScraper` in PR #93.
- **DVD policy is separate:** [Agent C v2.3 PR #99](https://github.com/daniel-yfc/stash-scarpers/pull/99) `8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5` intentionally omits source whole-DVD Duration from Scene and source Label from Studio. Source `expect` data remains. Do not re-enable DVD Duration merely because Clips gains support later.

## 2. P0 — Agent G: narrow omission implementation (existing PR #93)

**Assignment ID:** `WAVE2E-G-PR93-DURATION-OMISSION-20261104`

1. Refresh exact PR #93 HEAD and latest main. On `fix/e2e-bravo-clips`, remove the `clipSceneScraper.Scene.Duration` mapped selector + JS postProcess block. No dummy zero, fallback, fake null or dormant active YAML field.
2. Retain exact `d6d6fbf` Duration selector and JS `minutes × 60` mapping in [decision `4 restoration recipe](PR93-DEF01-DURATION-DEFER-DECISION-20261104.md); **do not delete** the source minutes/selector research or the R1–R3 and v1–v4 records.
3. Update current `tests/fixtures/bravo/bravo-clips-fixtures.yml` to remove `Duration` from **production** `mappedExpect`. Keep source values in supported source-only tests/cases. In `tools/tests/test_bravo_clips.py` assert mapped Duration is absent, and independently verify 284/282/283 = 30 source minutes, 285 = 45, missing-minutes/price/spacer controls and the seconds conversion contract for future use. Do not add unknown manifest keys or mutate archived `bravo-fixtures.yml`.
4. Preserve other BRAVO mappings and current QueryFragment byte-identically wherever possible. Future `WS-2E-QF-001` QueryFragment removal is for Wave 2E, **not** this Clips PR.
5. Run exact-HEAD validators, pytest, manifests, evidence/archive-digest checks, CodeQL/CI and package-provenance build. Update PR #93 body to disclose `CLIPS_DURATION_DEFERRED` and new SHA, leaving v4 FAIL as history; mark `NEW_SCOPE_GATE_B_NOT_RUN`.
6. Deliver a new commit, test logs, source extraction/restore-recipe evidence, digest, known limitations and exact HEAD. Keep PR Draft, not merged. No Stash operations authorized.

**Exit:** New PR #93 HEAD with no active Duration mapping; source-only data preserved; Gate A and exact-head CI recorded; new-scope Gate B remains NOT_RUN pending independent QA.

## 3. P0 — Agent D: independent revised-scope Gate B (future)

**Assignment ID:** `WAVE2E-D-PR93-DURATION-DEFER-GATEB-20261104`  
**Preconditions:** Agent G's new SHA and acceptable exact-head checks; **fresh** explicit M0 and exclusive `stash-test` lease (all v1–v4 leases released).

Verify installed candidate SHA + ZIP SHA, Clips 284/282/283 URLs and Clips QueryFragment, exact Title/Code/URLs/Details and other retained fields, poster-only Image, negatives and safe environment behavior. **Scene.Duration must be absent/null by policy**, not guessed 0. Preserve sanitized actual GraphQL evidence, control scrape, rollback, version history and independent verdict `GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE` or `FAIL`. PASS does not authorize merge.

## 4. Paused A2 and future restoration

**PAUSED:** Upstream/Stash Core A2 patch or push, fourth XPath replacement, unrelated live probes. R3 independent Go replay is desirable for future restoration but **not mandatory for new scope G0**. Keep root-cause analysis and source-code provenance.

**FUTURE RE-ENABLE CONTRACT:** Separate Controller decision and reviewed PR; prove deployable Stash typed-duration correction or accepted alternative; replay Go root-cause and fix tests; verify current site DOM/XPath, 30→1800 and 45→2700, malformed/zero/overflow and missing input; restore exact `Duration` mapping after review; restore `mappedExpect.Duration` and regressions; run exact-head Gate A and new authorized independent Gate B/C with rollback. No automatic activation on Stash upgrade. DVD remains blocked by its distinct whole-DVD-to-Scene semantic policy.

## 5. Wave 2E dependence

`G0` stays blocked until revised-scope independent Gate B PASS, exact-head checks, separate Controller merge authorization and actual PR #93 merge. `G1` remains provisional until Agent A independent DOM evidence acceptance. Agent F only performs design/readiness; **no official DVD YAML implementation** before G0/G1. Issue #97 upstream unmatched-URL panic remains separate.

## 6. Machine-readable handoff

~~~yaml
ASSIGNMENT_ID: WAVE2E-CONTROLLER-PR93-DURATION-DEFER-HANDOFF-20261104
DECISION_ID: WS-2E-DEF01-DEFER-20261104
PR: 93
PR93_REFERENCE_HEAD: d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6
PR93_STATE: DRAFT_UNMERGED
CLIPS_DURATION_PRODUCTION_MAPPING: OMIT_PENDING_IMPLEMENTATION
CLIPS_DURATION_SOURCE_MINUTES: PRESERVE_WITH_SOURCE_ONLY_TESTS
CLIPS_DURATION_RESTORE_RECIPE: VERSIONED_NON_ACTIVE
CLIPS_DURATION_RE_ENABLE: FUTURE_EXPLICIT_PR_PLUS_RUNTIME_AND_INDEPENDENT_GATES
DURATION_BUG: OPEN_DEFERRED_BY_CONTROLLER_SCOPE
G_R3_ROOT_CAUSE: REPRODUCED_BY_AGENT_G
GO_REPRO_INDEPENDENT_REPLAY: PENDING_NON_BLOCKING_WHILE_PAUSED
A2_CORE_REPAIR: PAUSED
DEF_02_DETAILS: CLOSED_LIVE_VERIFIED
GATE_B_V4_HISTORICAL: FAIL
GATE_B_REVISED_SCOPE: NOT_RUN
AGENT_G_NEXT: WAVE2E-G-PR93-DURATION-OMISSION-20261104
AGENT_D_NEXT: WAVE2E-D-PR93-DURATION-DEFER-GATEB-20261104
AGENT_C_V23_HEAD: 8c9daf2ddfbdd06877c850608ee3f8b366b0e8f5
DVD_DURATION_TO_SCENE: OMIT
DVD_LABEL_TO_STUDIO: OMIT
DVD_SOURCE_EXPECT: PRESERVE
G0: BLOCKED
G1: PROVISIONAL
AGENT_F_RUNTIME_INTEGRATION: BLOCKED
STASH_TEST_AUTHORIZATION: NONE
STASH_CORE_CHANGE_AUTHORIZATION: NONE
MERGE_AUTHORIZATION: NOT_GRANTED
HANDOFF_STATUS: ASSIGNED_NEEDS_NEW_PR93_HEAD
~~~
