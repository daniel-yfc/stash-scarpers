---
doc_id: DOC-E2E-61
title: BRAVO DVD Wave 2E Plan
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
    - bravo
    - dvd-routing
    - wave-2e
    - live-verification
---

# Wave 2E — BRAVO DVD URL routing

**Tracking:** STASH-E2E-02a / `feat/e2e-bravo-dvds` (planned; **not implemented or verified**). **Upstream dependency tracked separately:** [STASH-E2E-02 WS-D issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97).

## Objective and baseline

Restore support for legitimate BRAVO `https://www.bravo-japan.com/dvds/<id>` detail URLs using a **dedicated `dvdSceneScraper`** under `sceneByURL`. Separate DVD selectors from the `clipSceneScraper` introduced in [Wave 1B PR #93](https://github.com/daniel-yfc/stash-scarpers/pull/93). PR #93 is Draft as of this document; its independent live Gate B and approval/merge precede Wave 2E implementation. Do not add DVD logic to or silently merge #93.

The original `main@4bbafca9` BRAVO `sceneByURL` matched `/clips/` only while `BRAVO.test.yaml` included seven DVD URLs. Stash's `scrapeSceneURL` returned `index out of range [0] with length 0` for both `/dvds/234` and `/dvds/084`, and for an unrelated unmatched example.com control. The evidence shows a **routing gap** plus **separate upstream error-handling behavior**, not proof that a DVD selector caused a panic. Source: QA-STASH-LIVE-E2E-20261031-01; upstream report preparation: issue #97.

## Required design (schema sketch, not shippable YAML)

```yaml
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

xPathScrapers:
  clipSceneScraper:
    scene: {} # Existing Wave 1B selectors unchanged.
  dvdSceneScraper:
    scene: {} # Implement only after DVD rendered-DOM evidence.
```

- Confirm the two route families do not overlap and both host variants resolve.
- Build `dvdSceneScraper` selectors from **fresh completed DVD rendered DOM** for Title, Code, URLs and other source-verifiable fields. Evaluate historical `品番`-adjacent selectors cautiously: older /dvds/376, /347, /372 comments are not current live proof.
- Never synthesize missing Date, Studio, Image or Code; do not select site logos/unrelated artwork as covers. Preserve the source language.
- Keep `sceneByQueryFragment` design and any existing Clips modes unchanged for Wave 2E unless a separately reviewed routing solution is verified. A single existing query-fragment selector is not evidence of DVD query-fragment support; **DVD URL mode is the explicit scope**, not Search/Group/Fragment support.
- Restore legitimate DVD URLs to the test sidecar *only when* the DVD route works. Do not mutate archived evidence digests/fixtures to force a pass.

## Scope, sequence, acceptance

1. **Dependency gate:** PR #93 independent stash-test Gate B, exact-head CI and user-authorized merge. Rebase Wave 2E onto the accepted main revision; avoid concurrent edit of BRAVO.yml.
2. **DOM evidence:** capture and sanitize completed CDP DOM for `/dvds/234`, `/dvds/084`; cross-check historical `/dvds/281` and `/dvds/046` HTML fixtures. Check challenge/failure pages. Only record verified fields.
3. **Implementation:** second `sceneByURL` action → `dvdSceneScraper`, dedicated DVD fixtures/structural tests; retain Clips `/clips/284` and `/clips/282` behavior.
4. **Gate A (offline):** official validator, URL sorting, full repo quality gate, fixture manifests, Python tests, docs/index and evidence-contract checks, security scan. Report exact commands and SHA; do not equate fixture success with a live Stash pass.
5. **Gate B (independent stash-test):** verify installed package revision; invoke Stash `scrapeSceneURL` on `/dvds/234`, `/dvds/084`, and available historical DVD cases, checking Title/Code accuracy, canonical URL, absence of false metadata and panic. Re-run `/clips/284`, `/clips/282` plus negative/blank-title cases. Record unsupported URL control separately; **its upstream panic remains open** even if routed DVDs work.
6. **Gate C:** exact-head CI/CodeQL and provenance checks; publish changed-package digest, rollback plan and QA evidence. Remain Draft / do not merge without maintainer approval.

**Exit:** valid DVD URLs select `dvdSceneScraper` and return source-grounded metadata without Stash panic; Clips regressions absent. No claim that unmatched-URL behavior across Stash is fixed. Production readiness requires separate deploy and auth/CDP assessment.

## Status (2026-11-01)

`PLANNED / NOT_IMPLEMENTED / GATE_A_NOT_RUN / GATE_B_NOT_RUN`. The historical DVD fixtures remain valuable evidence, **not** a DVD runtime acceptance result. Upstream panic issue: [#97](https://github.com/daniel-yfc/stash-scarpers/issues/97).
