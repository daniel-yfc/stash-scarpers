---
doc_id: DOC-E2E-62
title: STASH-E2E-02 Upstream Panic Report Preparation
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-11-01"
authority: informational
routing:
  intents:
    - stash-panic
    - upstream-issue
    - graphql
    - e2e
---

# STASH-E2E-02 — Upstream unmatched-URL panic (WS-D)

**Tracking:** [Local issue #97 — PREPARING_UPSTREAM_REPORT](https://github.com/daniel-yfc/stash-scarpers/issues/97). **Upstream: NOT_FILED.** Separate from [Wave 2E DVD routing](61-bravo-dvd-wave-2e.md), which addresses valid DVD URL coverage, not the Stash runtime error on arbitrary unmatched URLs.

## Confirmed reproduction evidence (2026-10-31)

| Item | Status / provenance |
| --- | --- |
| Environment | Independent stash-test instance, LIVE_INSTANCE_E2E through Stash GraphQL, QA-STASH-LIVE-E2E-20261031-01 |
| Stash version | `v0.31.1-182-g9e9ad972` (build 2026-10-27), as recorded in QA handoff; reconfirm before filing |
| Repo baseline | `daniel-yfc/stash-scarpers main@4bbafca9cf7b5d67117ac41136e74a303c28e4f4` |
| Positive control /dvd | BRAVO `https://www.bravo-japan.com/dvds/234` and `/dvds/084`: 2/2 returned panic; no DVD route in baseline `sceneByURL` |
| Unmatched control | An example.com URL with no matching scraper returned the same error class; original exact query/URL not published in QA summary |
| Error text | `Internal system error: runtime error: index out of range [0] with length 0` (minor wrapper variants in QA); **not a full server stack trace** |
| Original GraphQL request/variables | **NOT_CAPTURED_IN_PUBLIC_REPORT**; retrieve from private QA evidence, do not invent |
| Server stack trace/file and line | **STACK_TRACE_NOT_CAPTURED** in available summary; request troubleshooting logs |

## Minimal reproduction for new evidence

1. Confirm active Stash build and scraper inventory (especially no route for `https://example.com/__stash-unmatched-url-repro__`).
2. Send a read-only GraphQL `scrapeSceneURL` query. The following is a **proposed reproducible template**, not the verbatim 2026-10-31 QA request:
```graphql
query ReproduceUnmatchedSceneURL($url: String!) {
  scrapeSceneURL(url: $url) {
    title
    code
    urls
  }
}
```
```json
{"url":"https://example.com/__stash-unmatched-url-repro__"}
```
3. Record sanitized raw GraphQL request, `errors` and `data`, timestamp, correlated Stash troubleshooting log and full stack trace (if accessible). Expected: clear no-matching-scraper error; observed historically: index-out-of-range panic.
4. Re-run with `https://www.bravo-japan.com/dvds/234` and `/dvds/084` on baseline with no DVD route. Run again with Wave 2E candidate as a routing comparison; **do not mistake absence of the panic after matching DVD URLs for an upstream Stash fix**.

## Evidence and upstream-submission gate

Private QA evidence inventory (not committed): `qa-stash-live-e2e-20261031/evidence/url_tests.json`, `extra_tests.json`, `fragment_failure_tests.json`; scripts `run_url_tests.py`, `run_extra_tests.py` and `run_fragment_failure_tests.py`. Access/replay by authorized QA only; sanitize API keys, cookies, session identifiers, instance network addresses, and private scene data.

- [ ] Verify exact Stash build, repro environment and installed scraper config.
- [ ] Recover **actual** original GraphQL operation, variables and raw response; keep proposed template labelled as proposed.
- [ ] Capture full Stash server panic stack including path/line, or explicitly state unavailable.
- [ ] Show control unmatched URL versus baseline BRAVO DVDs; expected/actual and case timestamps.
- [ ] Confirm whether the defect still reproduces on a supported newer upstream build; label older-only findings accordingly.
- [ ] Check for duplicates; [stashapp/stash#4415](https://github.com/stashapp/stash/issues/4415) covers missing queryURL/fragment placeholders, and [#5793](https://github.com/stashapp/stash/issues/5793) describes a groupByURL index-out-of-range case. **Neither is established to have the identical scrapeSceneURL root cause.**
- [ ] Draft separate upstream issue with steps, GraphQL payload, version, error and stack, expected behavior, sanitized logs; have maintainer review before submission.
- [ ] Once submitted, place upstream issue URL, owner, status, target fix version, and regression evidence in [tracking issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97) and this page.

**Do not file upstream or claim fixed merely because these tracking docs exist.** Related placeholder behavior (STASH-E2E-04) is separately scoped and should not obscure the minimal unmatched-URL panic reproduction.
