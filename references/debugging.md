# Debugging

**Load when:** a scraper returns empty/wrong fields, crashes, or hits access walls.

> **概要（zh-TW）：** 先查常見故障表（空值、日期 nil、403、nil pointer），再讀事件回顧裡的可遷移教訓。修復前先分類失敗頁面；證據分層記錄（raw / rendered / live runtime）。

## Contents

- [Common failure catalog](#common-failure-catalog)
  - [Dump raw HTML/JSON](#dump-raw-htmljson)
  - [All fields empty](#all-fields-empty)
  - [Only Date is nil](#only-date-is-nil)
  - [Studio or Details wrong](#studio-or-details-wrong)
  - [Nil pointer dereference](#nil-pointer-dereference)
  - [403 / Access denied](#403-access-denied)
  - [Turnstile / reCAPTCHA](#turnstile-recaptcha)
  - [Fragment queryURL note](#fragment-queryurl-note)
- [Incident reviews](#incident-reviews)
  - [Prevention checklist](#prevention-checklist)
- [Further references](#further-references)

## Common failure catalog

### Dump raw HTML/JSON

Add `debug: printHTML: true` to the scraper YAML to print the received
HTML/JSON to the Stash log file. Useful when selectors return nothing and
you need to see what Stash actually received.

### All fields empty

**Symptoms:** All scraped fields return empty/null values.

**Causes:**

- Selectors are wrong
- Age-gate or interstitial blocking access
- Site requires cookies or CDP that aren't configured

**Debug steps:**

1. `$x()` your selectors in browser console to verify they match
2. Check for age-gate or interstitial pages
3. Verify `useCDP` and cookie configuration
4. Check HTTP status codes (403 → User-Agent / headers issue)

### Only Date is nil

**Symptoms:** All fields scrape correctly except Date returns nil.

**Causes:**

- Raw date string doesn't match Go layout
- `replace` not applied before `parseDate`

**Debug steps:**

1. Check the raw date string format
2. Verify `parseDate` uses Go layout (`2006-01-02`), not `YYYY-MM-DD`
3. Apply `replace` before `parseDate` if needed (e.g., remove time, timezone)
4. Test with compact dates (`20060102`) if site uses that format

### Studio or Details wrong

**Symptoms:** Studio shows manufacturer when it should show label; Details has HTML tags.

**Causes:**

- Using メーカー (manufacturer) as studio when レーベル (label) is correct
- Not stripping HTML from Details field

**Debug steps:**

1. For JP sites: prefer レーベル over メーカー for Studio.Name
2. Use `concat` or post-process to strip HTML from Details
3. Check if シリーズ is being confused with Group (only use if user asks)

### Nil pointer dereference

**Symptoms:** Stash runtime crashes with "nil pointer dereference" error when processing scene metadata.

**Cause:** This may be an **upstream Stash bug** when `mappedScraper.processSceneRelationships` processes a fragment result with zero rows while the scene block defines relationships (Performers/Tags/Studio).

**Important:** This is not a scraper-authoring workaround. Adding `sceneByFragment` with relationship mappings can create the trigger condition rather than preventing it.

**Mitigation:**

- Test fragment modes against non-matching input before deployment
- Verify fragment scrapers return valid results on test scenes
- If a site doesn't support fragment scraping, omit `sceneByFragment`

**Upstream fix:** Stash PR #6857 (merged 2026-05-28 into `develop`) initializes the scene result to prevent the nil dereference. Stash v0.31.1 and earlier are still affected; upgrade to a release containing the fix, or use the `development` Docker tag.

**Reference:** Stash issue #6921 (https://github.com/stashapp/stash/issues/6921), fix PR #6857 (https://github.com/stashapp/stash/pull/6857)

### 403 / Access denied

**Symptoms:** HTTP 403 errors when fetching pages.

**Causes:**

- Missing or incorrect User-Agent
- Site requires authentication (cookies)
- AJAX/JavaScript-rendered content

**Debug steps:**

1. Add custom User-Agent via `driver.headers`
2. Configure cookies if site requires login
3. Use CDP for JavaScript-rendered content
4. Add `sleep` between requests (min 1 second)

### Turnstile / reCAPTCHA

**Symptoms:** Site requires human verification

**Mitigation:**

- Use CDP with visible browser
- Solve CAPTCHA manually in browser
- Consider whether site is appropriate for automation

### Fragment queryURL note

For XPath/JSON fragment actions, include the required `queryURL` for the entry point and target site. Script actions follow their script contract. Do not add fragment entry points merely to address a runtime panic.

## Incident reviews

Past incident write-ups live in [`incident-reviews.md`](incident-reviews.md). They are single-site records: label transfers `Heuristic` until independently tested on a second layout or site.

### Prevention checklist

- Compare each normative schema claim to the official CommunityScrapers validator/schema, and consult `UPSTREAM_SOURCES.md` when provenance matters.
- Search the full reference tree for a changed rule; update duplicates, examples and ownership routes together.
- Parse and validate complete YAML examples; check the committed file, not only a local reconstruction.
- Mark `Source:` facts, `Heuristic:` transfers and evidence status distinctly; require a cross-site counterexample before declaring a generic pattern.
- Classify failure pages before selector work; separate raw, rendered fixture and live runtime evidence.
- Load the committed scraper in a real Stash instance before recording any status beyond authored; keep loader evidence separate from schema and live-extraction evidence.
- Run documentation and fixture controls and report what each pass does **not** establish.

## Further references

- `references/cdp-workflow.md` — CDP configuration
- `references/script-actions.md` — Script scraper patterns
