---
doc_id: STATUS-LIVE-60
title: Live Test Status
status: active
layer: status
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - live-verification
    - testing
---

# Live Test Status

This table separates schema validation from live-page verification. `Schema` means the official validator accepts the YAML; it does not mean the website selectors are currently working.

The `Scraper` column uses the YAML filename (without `.yml`), matching `scrapers/*.yml` and `scrapers/private/*.yml`.

Last full live verification: 2026-10-06 (browser DOM verification + scrutiny.js; read-only).

| Scraper     | Schema |                      Live search |         Live detail | Auth/CDP                            | Status                                                                                                                                                 |
| ----------- | -----: | -------------------------------: | ------------------: | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| ACCEED      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: sceneScraper rewritten against live DOM (h2/ul.thongso/ul.select); 8 fields regression-verified HIT                                  |
| BRAVO       |   Pass |                   Not configured | Verified 2026-10-06 | Public + age gate                   | OK (Tags empty on tested page; no site search)                                                                                                         |
| CK-Download |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Image set-page branch added (div.set_photo)                                                                                          |
| ClubCK      |   Pass |                       Unverified | Verified 2026-10-06 | Login (coat.co.jp)                  | Fixed 2026-10-06: Performers added; Tags decontaminated; Code direct source                                                                            |
| fc2         |   Pass |                   Not applicable | Verified 2026-10-06 | Public + age gate                   | OK (9/9; no search endpoint; eKYC wall intermittent)                                                                                                   |
| GAMES       |   Pass | Verified 2026-10-06 (title-only) | Verified 2026-10-06 | Public + age gate                   | Fixed 2026-10-06: URLs og:url fallback added                                                                                                           |
| GV-Wiki     |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login (private)                     | Fixed 2026-10-06: Details now reads text nodes; Added 2026-10-14: performerByName (r=m model-only, login) + performerByURL, fixture-verified (5 cases) |
| HunkCh      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | OK (og: branches miss but unions hit)                                                                                                                  |
| JGVData     |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public                              | OK (8/8 via scrutiny.js)                                                                                                                               |
| Justice01   |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate                   | Fixed 2026-10-06: Image @src fallback added                                                                                                            |
| KOShop      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Details class typo; Tags headings corrected                                                                                          |
| KOTube      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: h3 title, th/td table, dual-template Details, package performer block                                                                |
| KOVideo     |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate (no login needed) | Fixed 2026-10-06: Title ancestor path corrected                                                                                                        |
| MensRushTV  |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Performers exact links; Image video-poster/img union                                                                                 |
| RGBEE       |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate (no login needed) | OK (Date page-dependent: no 發行 field on some pages)                                                                                                  |
| gayerdar    |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login for detail pages (private)    | Fixed 2026-10-06: Tags plain-text fallback added                                                                                                       |

## Test protocol

For each site, record:

1. One known detail URL.
2. One scene-name search URL, if supported.
3. Extracted title, code, date, image, studio, tags, performers, and URL.
4. Whether the page required CDP, login, age verification, or cookies.
5. The date and site response status.

Do not promote a scraper from `Unverified` based only on schema validation.

## 2026-10-31 Stash GraphQL E2E addendum (not a replacement for older browser verification)

Independent stash-test QA (QA-STASH-LIVE-E2E-20261031-01, Stash `v0.31.1-182-g9e9ad972`) recorded BRAVO `/dvds/234` and `/dvds/084` returning `runtime error: index out of range [0] with length 0` (2/2). The baseline `sceneByURL` supported `/clips/` but not `/dvds/`, and an unrelated unmatched example.com URL produced the same error class. The live verdict for BRAVO as tested in this round is **FAIL**; prior 2026-10-06 browser DOM status is not a passing Stash GraphQL E2E result.

- **Wave 1B:** [PR #93](https://github.com/daniel-yfc/stash-scarpers/pull/93) provides Clips-only changes; Draft and independent live Gate B not yet proven here. Do not promote to verified on the basis of its local tests.
- **Wave 2E:** [dedicated DVD route plan](61-bravo-dvd-wave-2e.md) — `dvdSceneScraper` on `/dvds/`; **PLANNED / NOT_IMPLEMENTED / NOT_LIVE_VERIFIED**. Requires Wave 1B acceptance and user-authorized merge first.
- **Upstream panic:** [STASH-E2E-02 bug preparation](62-stash-panic-upstream-report.md), [local tracking #97](https://github.com/daniel-yfc/stash-scarpers/issues/97). **UPSTREAM_NOT_FILED**; GraphQL original request and server stack trace still to collect. DVD routing does not fix arbitrary unmatched-URL panic.
