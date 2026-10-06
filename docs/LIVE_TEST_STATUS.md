# Live Test Status

This table separates schema validation from live-page verification. `Schema` means the official validator accepts the YAML; it does not mean the website selectors are currently working.

Last full live verification: 2026-10-06 (browser DOM verification + scrutiny.js; read-only).

| Scraper       | Schema |                      Live search |         Live detail | Auth/CDP                            | Status                                                                                                                |
| ------------- | -----: | -------------------------------: | ------------------: | ----------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| ACCEED        |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: sceneScraper rewritten against live DOM (h2/ul.thongso/ul.select); 8 fields regression-verified HIT |
| Bravo-Japan   |   Pass |                   Not configured | Verified 2026-10-06 | Public + age gate                   | OK (Tags empty on tested page; no site search)                                                                        |
| CK-Download   |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Image set-page branch added (div.set_photo)                                                         |
| ClubCK        |   Pass |                       Unverified | Verified 2026-10-06 | Login (coat.co.jp)                  | Fixed 2026-10-06: Performers added; Tags decontaminated; Code direct source                                           |
| fc2           |   Pass |                   Not applicable | Verified 2026-10-06 | Public + age gate                   | OK (9/9; no search endpoint; eKYC wall intermittent)                                                                  |
| Games-Video   |   Pass | Verified 2026-10-06 (title-only) | Verified 2026-10-06 | Public + age gate                   | Fixed 2026-10-06: URLs og:url fallback added                                                                          |
| GV-Wiki       |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login (private)                     | Fixed 2026-10-06: Details now reads text nodes                                                                        |
| Hunks-Ch      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | OK (og: branches miss but unions hit)                                                                                 |
| JGVData       |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public                              | OK (8/8 via scrutiny.js)                                                                                              |
| Justice01     |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate                   | Fixed 2026-10-06: Image @src fallback added                                                                           |
| KO-Shop       |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Details class typo; Tags headings corrected                                                         |
| KO-Tube       |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: h3 title, th/td table, dual-template Details, package performer block                               |
| Ko-Video      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate (no login needed) | Fixed 2026-10-06: Title ancestor path corrected                                                                       |
| Men's Rush TV |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login                               | Fixed 2026-10-06: Performers exact links; Image video-poster/img union                                                |
| RGBEE         |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Public + age gate (no login needed) | OK (Date page-dependent: no 發行 field on some pages)                                                                 |
| gayerdar      |   Pass |              Verified 2026-10-06 | Verified 2026-10-06 | Login for detail pages (private)    | Fixed 2026-10-06: Tags plain-text fallback added                                                                      |

## Test protocol

For each site, record:

1. One known detail URL.
2. One scene-name search URL, if supported.
3. Extracted title, code, date, image, studio, tags, performers, and URL.
4. Whether the page required CDP, login, age verification, or cookies.
5. The date and site response status.

Do not promote a scraper from `Unverified` based only on schema validation.
