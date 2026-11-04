---
doc_id: DEC-PR93-DEF01-DURATION-DEFER-20261104
title: PR #93 Controller Decision — Defer Clips Scene Duration without losing restore path
status: active
layer: qa
owner: controller
audience:
  - agent
  - maintainer
applies_to:
  - scrapers/BRAVO.yml
  - pr-93
  - wave-1b
  - wave-2e
last_verified: "2026-11-04"
authority: decision
---

# Controller Decision — Clips Duration temporarily unmapped; future restoration preserved

**Decision ID:** `WS-2E-DEF01-DEFER-20261104`  
**Decision date:** 2026-11-04 (Asia/Taipei)  
**Controller directive:** “Clips 同樣暫不映射 Duration，目前修復暫停，但記錄過程；需留下可後續轉換為繼續映射 Duration 的彈性。”  
**Decision:** `CLIPS_SCENE_DURATION_TEMPORARILY_UNMAPPED / ROOT_CAUSE_REPAIR_PAUSED / RE_ENABLE_PATH_PRESERVED`  
**Decision state:** **`POLICY_APPROVED / CODE_CHANGE_NOT_YET_APPLIED / NEW_GATE_B_REQUIRED`**  
**Related [current handoff](PR93-DEF01-DURATION-DEFER-HANDOFF-20261104.md)**; [historical R3 handoff](PR93-DEF01-R3-CONTROLLER-HANDOFF-20261104.md) is superseded where it treated A2 repair and mandatory Clips Duration as the current critical path.

## 1. Intent and non-negotiable distinctions

**Temporarily omit the production `Scene.Duration` mapping from BRAVO Clips** to keep Wave 1B delivery independent of an upstream Stash typed-conversion defect. **Do not erase the original extracted source duration, XPath research, post-processing logic, fixtures, negative tests, or QA history.** Re-enabling the field later must be a controlled, testable change rather than redoing the web-source research.

This is a **prospective change of feature scope**, not proof that the original defect was fixed.

- Historical independent Gate B: **v1 NOT_RUN; v2 FAIL @ `86e34a2`; v3 FAIL @ `ce7ef6c`; v4 FAIL @ `d6d6fbf`**. Preserve all verdicts and exact HEADs. Under the new contract, the old FAIL is **not** retroactively converted to PASS.
- `DEF_01` becomes `DEFERRED_BY_CONTROLLER_SCOPE / UPSTREAM_BUG_OPEN` **only after the omission is implemented** on a new PR #93 HEAD. The currently installed/pinned `d6d6fbf` remains `DEF_01_OPEN_P1 / GATE_B_V4_FAIL`.
- `DEF_02` Details remains `CLOSED_LIVE_VERIFIED`. Title, Code, URLs, Tags, image poster-only, QF behavior, Title-less/invalid negatives and other applicable fields remain mandatory.
- Source observations (e.g. 30 source minutes for Clips 284/282/283; 45 in the 285 synthetic fixture) remain **true source-level values**, distinct from production `Scene.Duration`.
- DVD has a **separate policy reason** for omitting Duration: source `収録時間` is **whole-DVD length**, not automatically one Stash Scene; [Agent C v2.3](https://github.com/daniel-yfc/stash-scarpers/pull/99) also omits production Studio sourced from Label. These omissions must not be conflated with the Clips Stash type bug.
- No deployment, Stash test lease, upstream PR/issue, merge or any PR #93 change is authorized by publishing this decision alone.

## 2. Why the field is temporarily omitted

The checked Stash build `v0.31.1-182-g9e9ad972` (source `9e9ad972643320e737c711884f10e4285f0f3a88`) maps XPath-derived scene fields as strings but `mappedResult.scrapedScene` consumes Duration through `r.IntPtr("Duration")`, strictly asserting Go `int`. The result is null on every tried Clips selector despite successful XPath extraction.

Agent G's [R3 report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/pr93-def01-r3-type-isolation/docs/qa/PR93-DEF01-R3-TYPE-ISOLATION-REPORT.md) reports A/B/C end-to-end Go tests PASS and a source-version comparison. The **executable test source is still only in Agent G's isolated local copy**, not repository-archived; independent reproduction remains pending. Agent D independently observed v4 Duration null on three Clips and QF, while all other focused fields passed: [v4 report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-INDEPENDENT-QA-20261104-v4.md).

**Pause now:** further XPath-only revisions, A2 Stash Core implementation/push, deployment planning and additional live leases solely to prove the same failed Duration behavior. Preserve the R3 A2 proposal as a **future repair option**; it is not a current dependency for the reduced-scope Wave 1B release.

## 3. Required implementation on PR #93 — output disabled, source knowledge retained

**Assignment owner:** Agent G, existing sole writer of `fix/e2e-bravo-clips`. Starting reference `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6`; refresh remote HEAD before writing.

1. **Omit from official mapped output:** remove the entire `Duration` mapping block from `clipSceneScraper.Scene` in `scrapers/BRAVO.yml`. Do not write fixed `0`, empty string, guessed seconds or fallback. Do not add undocumented YAML `enabled` feature flags; the scraper schema has not been verified to support them.
2. **Archive reinstatement recipe:** copy the exact prior selector and JS transform from pinned `d6d6fbf` into a **versioned, non-executed restoration recipe** (this decision `4 or a companion research document). Preserve the selector's literal U+200B and cite its source commit SHA. This recipe is documentary reference, **not executable current YAML** and not proof the old selector will work after upgrade.
3. **Preserve source-only tests:** separate (a) source minutes extraction and normalization (`30`→`1800`; `45`→`2700`) from (b) production field mapping currently absent. Source observations must still be regression-tested against the sanitized fixtures. Retain price/spacer/missing-minutes negative fixtures; do **not** delete Duration evidence or historic expected source values merely to get CI green.
4. **Current production mapping tests:** update `tests/fixtures/bravo/bravo-clips-fixtures.yml` and `tools/tests/test_bravo_clips.py` so `mappedExpect.Duration` is absent for the current scope. Retain source values in existing supported tests or clearly identified source-only cases; do **not** invent unsupported manifest keys. Explicitly assert official YAML lacks active Clips `Duration` mapping. Separately verify absence/null at runtime in the new Gate B, not by offline structure alone.
5. **Preserve unrelated fields:** Title, Code, URLs, Details, Tags, Date/Studio, poster-only Image, Clips URL + current QueryFragment paths, historical fixture digest, negative tests and existing validated behavior. PR #93 must **not** implement DVD routes or prematurely remove QueryFragment (`WS-2E-QF-001` applies to later Wave 2E).
6. **Exact-head audit:** publish new SHA, package hash, current CI/CodeQL, revised acceptance matrix, changes and limitations; mark `GATE_B_NOT_RUN_ON_NEW_HEAD` until independent QA. PR #93 remains Draft until Controller explicitly approves merge.

**No dormant selector in the active scraper config.** The reversible switch is a **small, reviewable future PR** restoring the field from the documented recipe, conditional on fixed runtime, not a pretend runtime toggle.

## 4. Restore-capable mapping recipe (historical, NON-ACTIVE)

**Source:** `fix/e2e-bravo-clips` @ `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6`, `scrapers/BRAVO.yml` lines 116–148. This exact mapping **must not** be left active until runtime compatibility is resolved. The `translate` expression contains **literal U+200B**, which is invisible in many editors.

~~~yaml
# ARCHIVED REINSTATEMENT RECIPE — NOT ACTIVE CONFIG
Duration:
  selector: "//h2[normalize-space()='Clip']/following::h2[normalize-space(translate(., '​', '')) != '' and translate(substring(normalize-space(translate(., '​', '')), 1, 1), '0123456789', '') = ''][1]"
  postProcess:
    - javascript: |
        var v = value || "";
        var m = v.match(/(\d+)/);
        if (!m) return "";
        return String(parseInt(m[1], 10) * 60);
~~~

**Source fixture expectations to retain (not current production `mappedExpect`):** 284/282/283 → `30` minutes → `1800` seconds; synthetic 285 → `45` minutes → `2700` seconds; missing minutes → no source value; price/spacer traps must not fabricate Duration. Preserve provenance of source values and the actual selector limitations (a plain-digit price inserted before true minutes could remain ambiguous); revalidate before re-enabling.

## 5. Explicit re-enable protocol (future decision, not scheduled now)

**Future decision ID:** `WS-2E-DEF01-RESTORE-TBD`. This remains open and reversible; no implied deadline or automatic reactivation.

A dedicated maintainer/Controller-approved PR may reintroduce `clipSceneScraper.Scene.Duration` **only after**:

1. **Runtime compatibility:** identify a Stash release/commit with the required typed conversion, or a separately authorized validated alternative. Test the exact deployed build, not only an upstream merged patch.
2. **Repeatable source and core tests:** archive/replay Agent G's Go Test A/B/C and strict numeric conversion tests; validate actual native `int` and string seconds, missing/invalid/negative/decimal/overflow/zero handling; verify other Scene fields do not regress.
3. **Selector freshness:** re-check current rendered DOM and selected XPath with actual supported Stash runtime against 284/282/283; do not assume historical `d6d6fbf` XPath remains valid indefinitely. Keep neg cases and source-minute regression.
4. **Production mapping:** restore a reviewed `Duration` block from the documented recipe and reinstate `mappedExpect.Duration` in *active* Clips fixtures **only after** source/run-time semantics are demonstrated; ensure declared data is seconds, not raw minutes.
5. **Independent Gate A/B/C:** exact package SHA, live positive 284/282/283 and QF as applicable, missing-minutes fail-closed, Title/Code/URLs/Details/Image regressions, rollback. Releasing the source field cannot rely solely on Go unit tests or browser/lxml XPath.
6. **Explicit decision and rollout:** Controller records `DURATION_MAPPING_RESTORED_VERIFIED` only after independent gate PASS and authorized merge/deployment, with all previous v2–v4 failures still recorded.

**Do not automatically re-enable on Stash upgrade**, and do not apply Clips' restore procedure to DVD Duration until a separate whole-DVD-to-Scene semantic policy is approved.

## 6. Revised Gate B contract for omission candidate (future independent QA)

Revised acceptance is conditional on **new PR #93 HEAD implementing `3`** and a fresh M0 / exclusive `stash-test` lease:

| Check | New expected outcome |
| --- | --- |
| Package provenance | Installed candidate = exact new PR #93 SHA and ZIP digest |
| Clips 284/282/283 + Clips QF | Title/Code/URLs/Details remain source-correct; **Scene.Duration is intentionally absent/null** |
| Image | Poster-only; no unrelated fallback |
| Invalid/Title-less | Fail-closed; no misleading metadata |
| Regression | No loss of already accepted fields, no source Duration provenance deletion |
| Environment | Exclusive QA lease; restored verified; production untouched |

The new independent QA must explicitly say `GATE_B_PASS_UNDER_REVISED_SCOPE` or `FAIL`, never reclassify v4 `FAIL`. **G0 advances only after independent PASS, exact-head CI and an explicit Controller merge decision.**

## 7. Machine-readable current decision

~~~yaml
DECISION_ID: WS-2E-DEF01-DEFER-20261104
DECISION_STATUS: POLICY_APPROVED_IMPLEMENTATION_PENDING
PR93_REFERENCE_HEAD: d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6
CLIPS_DURATION_MAPPING: OMIT_PENDING_CODE_CHANGE
CLIPS_DURATION_SOURCE_EXTRACTION: RETAIN_WITH_TESTS_AND_PROVENANCE
CLIPS_DURATION_RESTORE_RECIPE: DOCUMENTED_IN_SECTION_4_NON_ACTIVE
CLIPS_DURATION_RE_ENABLE_POLICY: EXPLICIT_FUTURE_PR_AND_INDEPENDENT_GATES
DURATION_CORE_FIX: PAUSED
DURATION_ROOT_CAUSE: REPRODUCED_BY_AGENT_G_INDEPENDENT_REPLAY_PENDING
DURATION_BUG: OPEN_DEFERRED_BY_CONTROLLER_SCOPE
OLD_GATE_B_V4: FAIL
NEW_GATE_B_REVISED_SCOPE: NOT_RUN
G0: BLOCKED
G1: PROVISIONAL
AGENT_F_INTEGRATION: BLOCKED
PR93_MERGE: NOT_AUTHORIZED
STASH_CORE_MODIFICATION_AUTHORIZED: false
STASH_TEST_OPERATION_AUTHORIZED: false
UPSTREAM_PR_AUTHORIZED: false
~~~

**Historical decision precedence:** `WS-2E-DEF01-DEFER-20261104` **supersedes** the earlier A2-first recovery assignment **for immediate execution**, but retains it as a reversible future remediation plan. Every already-recorded failure and the original Agent G technical evidence remain intact.
