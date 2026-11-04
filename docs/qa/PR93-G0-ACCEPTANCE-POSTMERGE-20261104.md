---
doc_id: PR93-G0-ACCEPTANCE-POSTMERGE-20261104
decision_id: G0-ACCEPTED-PR93-20261104
status: accepted
date: "2026-11-04"
branch: docs/pr93-def01-controller-handoff-20261104
merge_sha: ff236c9e91e27321e93f59d2bf12488db714dfc7
reviewed_head_sha: 88d27a5764c30fec1ab8bb5a325382e72a2ef09e
---

# Controller Decision Record — G0 Accepted (PR #93)

**Decision:** `G0_ACCEPTED / PR93_MERGED / PUBLIC_SOURCE_DEPLOY_SUCCESS`  
**Date:** 2026-11-04 (Asia/Taipei)  
**Repository:** [daniel-yfc/stash-scarpers](https://github.com/daniel-yfc/stash-scarpers)  
**PR:** [#93 — Wave 1B Clips](https://github.com/daniel-yfc/stash-scarpers/pull/93)  
**Authority:** User instructed “proceed” immediately after Controller's `CONDITIONAL_APPROVE_FOR_MERGE` review, which explicitly disclosed public-source deployment and known functional limitations. The merge was executed with exact-head protection and **normal merge commit**, not squash/rebase.

## 1. Immutable accepted baseline

| Role | Exact identifier |
| --- | --- |
| Pre-merge main | `2c328362df04e20790b5ce517fb09453caa5ad8a` |
| Independently reviewed PR HEAD | `88d27a5764c30fec1ab8bb5a325382e72a2ef09e` |
| **Accepted main merge SHA** | **`ff236c9e91e27321e93f59d2bf12488db714dfc7`** |
| Merge parents | `2c328362df04e20790b5ce517fb09453caa5ad8a` and `88d27a5764c30fec1ab8bb5a325382e72a2ef09e` |
| BRAVO YAML last-touch source version | `f4be5cf456ff5c7ba56e2d89ca29a13fec467b63` |
| BRAVO ZIP SHA-256 (independent QA / deterministic preview) | `004ef0679152fc954822ebadaaf534c050ec2a2fb3e710612d7e6280a863dbcf` |
| BRAVO YAML Git blob | `44e9dd18a32f2a8085a22abca49ccb92b0931d97` |

The source package version reflects the last commit touching `scrapers/BRAVO.yml`, not the merge commit or the test-only `88d27a5` commit. `main` contains the verified same YAML blob.

## 2. Gates and audit evidence

- **Gate A/C on PR HEAD:** 10 success, 1 skipped, 0 failed, including CodeQL, full validation, source build and fixture manifests.
- **Independent Gate B:** `GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE` by Agent D, [QA report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-20261103/docs/qa/PR93-GATEB-DURATION-DEFER-QA-20261104.md) and [41-file evidence package](https://github.com/daniel-yfc/stash-scarpers/tree/docs/qa-pr93-gateb-20261103/docs/qa/evidence/pr93-gateb-duration-defer-20261104) on QA branch `3707e867a7a550fe476594b4c35c27fd170f6edd`; Clips 284/282/283 twice, QF 284, negatives, control and rollback passed. The original v2-v4 `GATE_B_FAIL` history remains immutable.
- **Premerge code review:** 15 changed files, no path overlap with newer GVDB main changes; GitHub `mergeable_state=clean`; exact-head merge guard used.
- **Postmerge:** Six workflows **all completed with success** and nine checks **all success** at `ff236c9e91e27321e93f59d2bf12488db714dfc7`, including CodeQL (actions/python/javascript-typescript), Full Test & Validation Suite, Evidence Contract, Fixture Manifest Verification, Verification Staleness, source Build and GitHub Pages deploy.
- [Publish Stash Scraper Source action](https://github.com/daniel-yfc/stash-scarpers/actions/runs/41780521625): source generated **22 public packages**, `index.yml` and `BRAVO.zip`; `--verify-only` passed and Pages deploy reported success at Git SHA `ff236c9e91e27321e93f59d2bf12488db714dfc7`.
- [Validate Scrapers action](https://github.com/daniel-yfc/stash-scarpers/actions/runs/41780521906) and [CodeQL action](https://github.com/daniel-yfc/stash-scarpers/actions/runs/41780521712) completed successfully.

**Verification boundary:** The documented Stash source URL is `https://daniel-yfc.github.io/stash-scarpers/main/index.yml`. The Actions deployment succeeded, but a direct public HTTP read of the deployed index/ZIP bytes was unavailable from this review environment. Therefore **do not claim the CDN response digest was independently downloaded and matched**. Postmerge repository blob identity and source builder's verification were independently checked. A future external source fetch can close the CDN direct-read item; this does not invalidate the successful Actions deployment verdict.

## 3. Scope and accepted restrictions

- **Clips production `Scene.Duration`:** intentionally unmapped under `WS-2E-DEF01-DEFER-20261104`; upstream typed-duration bug not fixed. [Source-only mapping recipe and re-enable gates](https://github.com/daniel-yfc/stash-scarpers/blob/main/docs/qa/PR93-DURATION-DEFERRED-SPEC.md) preserved.
- **Clips Details (DEF-02):** verified corrected. Title, Code, URLs and existing URL/QF paths verified.
- **QueryFragment:** kept for this Clips-only baseline; `WS-2E-QF-001` removal remains a **separate future Wave 2E change**, subject to caller compatibility and live Gate B.
- **Negative and Image limits:** Title-less result must not be treated as success; invalid URL may still return generic tags; poster-present live positive not yet verified.
- **No DVD route** in the accepted Clips-only baseline; `dvdSceneScraper` not implemented.
- **No Stash runtime/production mutation** occurred as part of this merge. Source publication is **not** evidence of any runtime auto-install or safe unattended production scraping.

## 4. Post-G0 next stage

**G0:** `ACCEPTED_CLOSED` for merge, tested Clips baseline and successful Pages Actions publication; direct CDN artifact read remains an explicitly non-gating verification follow-up.

**G1:** `PROVISIONAL_NOT_INDEPENDENTLY_ACCEPTED`; requires independent Agent A DOM evidence acceptance.

**Agent F:** `OFFICIAL_DVD_INTEGRATION_BLOCKED_UNTIL_G1`; no runtime YAML implementation authorized by this record. Agent B's divergent routing branch should be **selectively integrated** (own tests/report only) after G1; Agent C v2.3 maintains no DVD Scene.Duration or Label→Studio mapped fields. Upstream Issue #97 panic remains separate and unresolved.

## 5. Machine-readable status

```yaml
DECISION_ID: G0-ACCEPTED-PR93-20261104
PR: 93
MERGE_EXECUTED: true
MERGE_METHOD: merge
ACCEPTED_MAIN_SHA: ff236c9e91e27321e93f59d2bf12488db714dfc7
REVIEWED_PR_HEAD: 88d27a5764c30fec1ab8bb5a325382e72a2ef09e
POSTMERGE_WORKFLOWS: 6_SUCCESS_0_FAILED
POSTMERGE_CHECK_RUNS: 9_SUCCESS_0_FAILED
PUBLIC_SOURCE_ACTION_DEPLOY: SUCCESS
PUBLIC_CDN_BYTES_DIRECTLY_VERIFIED: false
SOURCE_PACKAGES_BUILT: 22
BRAVO_PACKAGE_VERSION: f4be5cf
BRAVO_PACKAGE_SHA256_FROM_QA: 004ef0679152fc954822ebadaaf534c050ec2a2fb3e710612d7e6280a863dbcf
CLIPS_DURATION: DEFERRED_UNMAPPED_RESTORABLE
QF_ISSUE: WAVE2E_PENDING
G0: ACCEPTED_CLOSED
G1: PROVISIONAL
AGENT_F_RUNTIME_IMPLEMENTATION: BLOCKED_UNTIL_G1
PRODUCTION_STASH_DEPLOYED: false
```
