# Gayerdar Scraper Development Record

**Date:** 2026-09-28  
**Status:** Evidence record only. It is not a schema pass, policy-gate pass, reproducible fixture pass, live Stash/CDP pass, or production-readiness assertion.

## Reported inspection

A completed zh-TW browser-rendered page was inspected during development. That inspection is historical and is not a committed fixture suite.

| Capability | Recorded observation | Reproducible fixture |
|---|---|---|
| Performer detail | IDs 7, 12, 60, 65, 69, and 76 | Not committed |
| Performer search | Name observed from cover `img/@alt` | Not committed |
| Missing social link | Model 60: canonical URL only was the intended result | Not committed |
| Scene detail | GDSR-002-2, GD-007, GD-018, GD-022, and MGV-001 | Not committed |
| Scene search URL | `/videos/{code}` card links | Not committed |
| Scene search title | Card text was a category badge, not a title | Not committed |

## Selector notes

- zh-TW title: `<title>`, split before `｜`
- code and URL: canonical `/videos/{code}` URL
- date: `.trending-year` in compact `YYYYMMDD`; Go layout `20060102`
- details: `meta[name="description"]`
- tags: `ul.iq-blogtag a.title`
- performers: `/models/{id}` cards with descendant `h6`
- cover: hero image under `.iq-main-slider`

## Lessons learned

1. A selector without a completed, committed DOM fixture is a hypothesis, not verified implementation.
2. Classify challenge, login, age-gate, 404, and application-error pages before treating an empty selector as layout drift.
3. Rendering, access control, and extraction are separate failure domains.
4. Missing optional data must remain partial output, not unrelated fallback data.
5. Session material must never be committed, reconstructed, or copied.
6. A documentation command is not a control until the referenced script exists and CI runs it.
7. A local reconstruction is not evidence that the committed file parses. Validate the committed blob.

## Remaining verification

- YAML parse and schema validation: pending CI rerun after escape repair
- URL sorting: pending CI rerun
- Policy gate: pending CI rerun
- Reproducible rendered-DOM fixtures: not established
- Live Stash CDP: unverified
- Production readiness: unverified
