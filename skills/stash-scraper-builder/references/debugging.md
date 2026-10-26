---
doc_id: REF-OPS-72
title: Debugging
status: active
layer: skill
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
    - debugging
---

# Debugging

**Load when:** a scraper returns empty/wrong fields, crashes, or hits access walls.

> **概要（zh-TW）：** 先查常見故障表（空值、日期 nil、403、nil pointer），依技術條件採用已驗證的防錯規則。修復前先分類失敗頁面；證據分層記錄（raw / rendered / live runtime）。

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
3. Verify `useCDP` and the locally authenticated session; never commit cookies or browser profiles
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
2. For login-required pages, use an isolated, authenticated local CDP browser profile; never commit session material or enable cookies in tracked scraper YAML
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

## Transferable failure controls

- **Source classification:** Separate completed target pages from challenge, login, age-gate, 404 and partially rendered application responses. Empty selectors on failure pages are not evidence of selector drift.
- **Raw versus rendered:** Capture sanitized raw response and completed rendered DOM separately when needed; neither alone demonstrates live Stash/CDP extraction. Test both populated and missing-field cases, near-match URLs, localized paths and decoy elements.
- **Runtime load:** A parsed/schema-valid YAML can still fail Go unmarshalling. Confirm the exact committed file loads into the Stash version before claiming loader success. Do not place field maps under `common:` or `queryURLReplace` beneath a ByName entry.
- **Regex dialect:** PostProcess regex is executed by Go's RE2, not Node/Python regular expressions. Check it with the target engine; see `post-processing.md`.
- **Historical provenance:** `docs/archive/incident-reviews-2026-10.md` stores case-specific history, not a runtime instruction, schema authority, or current site verification.

## Prevention checklist

- Compare each normative schema claim to the local validator/schema derived from upstream, and consult `schema-provenance.md` when provenance matters.
- Search the full reference tree for a changed rule; update duplicates, examples and ownership routes together.
- Parse and validate complete YAML examples; check the committed file, not only a local reconstruction.
- Mark `Source:` facts, `Heuristic:` transfers and evidence status distinctly; require a cross-site counterexample before declaring a generic pattern.
- Classify failure pages before selector work; separate raw, rendered fixture and live runtime evidence.
- Load the committed scraper in a real Stash instance before recording any status beyond authored; keep loader evidence separate from schema and live-extraction evidence.
- Run documentation and fixture controls and report what each pass does **not** establish.

## Further references

- `references/cdp-workflow.md` — CDP configuration
- `references/script-actions.md` — Script scraper patterns
