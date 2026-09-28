# Rendered-DOM Fixture Testing

## Purpose

Use rendered-DOM fixtures for sites where the needed DOM appears only after JavaScript execution, CDP rendering, SPA routing, or an approved browser session. This complements raw-response scrutiny; it does not replace schema validation, policy gates, or a live Stash runtime test.

## Failure-page classification

Before evaluating any selector, classify the captured document as exactly one of:

- Completed target page
- Bot-management challenge
- Login, paywall, or age-verification gate
- Not-found / HTTP error page
- Client-side application error or partial render

Do not evaluate target-field coverage against a failure page. Check document title, canonical URL, a major body marker, and known challenge/error markers first.

## Fixture policy

Fixtures must be completed target-page DOM snapshots. They must never contain credentials, session cookies, clearance tokens, CSRF values, analytics identifiers, browser-profile values, or any other session material.

A fixture test should include:

1. At least two detail records when layout variation is plausible
2. A populated search result fixture for each configured search entity
3. An optional/missing-field case
4. XPath cardinality assertions (`min`/`max`) and representative values
5. Locale assertions for `<html lang>`, canonical URL locale, and source-language text

## Evidence labels

Record evidence separately:

| Label | Meaning |
|---|---|
| Schema validation | YAML shape accepted by the authoritative validator |
| Policy gate | Repository policy checks accepted the file |
| Rendered fixture verification | Selectors matched a captured completed browser DOM |
| Live raw-response verification | Selectors matched direct HTTP response HTML |
| Live CDP verification | Stash or an equivalent CDP runtime fetched and extracted live data |
| Production readiness | All required evidence has been recorded; not implied by any single row |

## Recommended command

```bash
node tools/verify-scraper-fixtures.mjs tests/fixtures/<scraper>-fixtures.yml
```

Fixture success proves the recorded selector contract only. Run the normal validator, URL sorting, quality gate, documentation check, and live Stash/CDP test separately.
