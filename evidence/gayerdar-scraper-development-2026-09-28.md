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
8. A scraper that has never been loaded by the Stash runtime has no load evidence. Loader unmarshal errors are a distinct verification layer, and upstream corpus precedent is not proof of runtime compatibility.

## 2026-10-05 runtime load defects and repairs

Live Stash reported three loader errors against the deployed scraper copy. These are runtime-load findings, distinct from schema, policy, fixture, and extraction evidence.

| Runtime error (abridged) | Defect | Fix commit |
|---|---|---|
| `field queryURLReplace not found in type scraper.ByNameDefinition` | `queryURLReplace` is not a valid key under `sceneByName` / `performerByName` in the running Stash build | `268cd046` |
| `performerScraper should create an object of type performer` | `performerScraper` defined fields under `common:` instead of a `performer:` block | `3417a7e9` |
| `cannot unmarshal !!map into string` (seven fields) | Scene fields nested under a doubled `common:` block; `common:` holds only string `$name` fragments, and scraped fields belong under `scene:` | `6cf19994` |

Commit `6cf19994` additionally converted the `Date` postProcess to a list (`- parseDate: "20060102"`), renamed detail-scraper `URL` to `URLs`, and nested `Studio`, `Tags`, and `Performers` under `Name:` keys, per the upstream scraper-development documentation (https://docs.stashapp.cc/in-app-manual/scraping/scraperdevelopment/).

## Remaining verification

- YAML parse and schema validation: pending CI rerun after commit `6cf19994`
- URL sorting: pending CI rerun
- Policy gate: pending CI rerun
- Runtime load: loader defects fixed; clean reload of commit `6cf19994` in the live instance not yet captured as evidence
- Reproducible rendered-DOM fixtures: not established
- Live Stash CDP extraction: unverified
- Search-scraper field alignment (positional Title/Image/URL matching across cards): unverified
- Production readiness: unverified
