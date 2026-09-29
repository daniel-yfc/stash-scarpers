# Gayerdar Scraper Development Record

**Date:** 2026-09-28  
**Status:** Evidence record only; not a schema pass, policy-gate pass, live Stash/CDP pass, or production-readiness assertion.

## Verified outcome

Browser-saved completed zh-TW rendered DOM was used to verify performer detail, performer search, scene detail, and scene-search URL selectors.

| Capability | Evidence |
|---|---|
| Performer detail | IDs 7, 12, 60, 65, 69, and 76 |
| Performer search | Populated result cards; name from cover `img/@alt` |
| Missing social link | Model 60 (A-Wei): canonical URL only is correct |
| Scene detail | GDSR-002-2, GD-007, GD-018, GD-022, and MGV-001 |
| Scene search URL | `/videos/{code}` card links |
| Scene search title | Not available from cards: visible text is a category/type badge, not title |

## Verified scene structure

- zh-TW title: `<title>`, split before `｜`
- code and URL: canonical `/videos/{code}` URL
- date: `.trending-year` in compact `YYYYMMDD`; use Go layout `20060102`
- details: `meta[name="description"]`
- tags: `ul.iq-blogtag a.title`
- performers: `/models/{id}` cards with descendant `h6`
- cover: hero image under `.iq-main-slider`

## Lessons learned

1. A selector without a completed DOM fixture is a hypothesis, not verified implementation.
2. Classify challenge, login, age gate, 404, and application-error pages before treating an empty selector as layout drift.
3. Rendering, access control, and extraction are separate failure domains. A selector can match a rendered fixture without proving live Stash CDP access.
4. Test optional values deliberately; missing social data must return valid partial output rather than unrelated fallback data.
5. Credentials, session cookies, clearance tokens, CSRF values, analytics identifiers, and browser-profile values must never be committed, reconstructed, or copied into YAML, fixtures, evidence, logs, or documentation.

## 2026-09-29 review pass

End-to-end static review of the committed `scrapers/private/gayerdar.yml`:

- Fixed blocking YAML parse defect: misaligned `with:` key in `sceneByQueryFragment.queryURLReplace` (validator could not load the file).
- Simplified both search-scraper URL chains from two prefix rules to one; the second rule was unreachable after the first rewrite.
- Added header annotations recording verification state and known fragilities (`text-D1D0CF` utility class, broad `$result` anchors, zh-TW-only title split).
- Added the recommended `# Last Updated` footer.

## Remaining verification

- Schema validation: pending rerun against corrected YAML
- URL sorting: unverified
- Policy gate: unverified
- Live Stash CDP: unverified
- Production readiness: unverified
