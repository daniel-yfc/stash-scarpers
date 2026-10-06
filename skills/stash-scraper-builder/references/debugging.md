# Debugging

**Load when:** a scraper returns empty/wrong fields, crashes, or hits access walls.

> **概要（zh-TW）：** 先查常見故障表（空值、日期 nil、403、nil pointer），再讀事件回顧裡的可遷移教訓。修復前先分類失敗頁面；證據分層記錄（raw / rendered / live runtime）。

## Common failure catalog

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
- Report upstream to Stash issue tracker if encountered

**Reference:** Stash issue #6921 (https://github.com/stashapp/stash/issues/6921)

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

## Incident reviews: transferable lessons

**Last reviewed:** 2026-10-05  
**Scope:** Scraper authoring, documentation and evidence controls. An incident review is not a schema pass, site fixture pass, live runtime result, or production approval.

### Incident 1: Schema drift in guidance

**Date:** 2026-09-03  
**Related:** Issues #21, #22, #23, #24, #25, #26, #28.

**What happened:** A false heuristic — that the filename supplies the scraper name and therefore the root `name` key should be omitted — was copied into several reference documents. A separate incorrect causal claim said adding `sceneByFragment` prevents a nil-pointer panic. A third documentation error incorrectly described the `{title}` placeholder as unsupported. The rules were repeated in the skill entry point, checklists, examples, and specialized references. Repetition made the claims appear authoritative even though they contradicted the schema or upstream issue evidence.

**Why review missed it:** the local schema stub was treated as a convenient reference instead of an explicitly incomplete compatibility aid; documentation examples were not extracted and validated as test fixtures; heuristics and verified schema rules were not labeled differently; review focused on individual files instead of searching for repeated claims across the reference tree; the evaluation pack checked generated output shapes but did not lint every embedded example.

**Detection and correction:** the Phase 1 audit compared local documentation with upstream schema material. A control test showed that script guidance without `name:` fails with `'name' is a required property`. Extracting corrected examples and validating them against schema rules caught additional `queryURLReplace` and entry-point errors, including omission of a valid `phash` key. The response was to require root `name:` in complete examples, distinguish schema-backed rules from heuristics, validate embedded full-document YAML, and centralize provenance in `UPSTREAM_SOURCES.md`. For any changed rule, search all references and update duplicates together. A rule repeated across files is not independently verified.

### Incident 2: Rendered page versus scraper runtime

**Provenance:** a historical browser-rendered zh-TW inspection of gayerdar (2026-09-28, record not committed to this repo) covering an optional-field observation, selector fragilities, and an absent committed site fixture suite. This single-site record motivates the patterns below; it does not prove them on another site or establish live Stash/CDP extraction.

**Transfer by page family, not brand:** for each prospective reuse, record the actual CMS/framework or rendering behavior when known, page template, locale/route shape, and response type. Similar appearance, CSS class, language, or domain ownership alone does not establish shared implementation. Label the row `Heuristic` until independently tested on a second layout or site; keep schema requirements separate.

| Candidate site family or failure class  | Apply when evidence shows                                                                                                                         | Counterexample or limit                                                                                                                      | General test/control                                                                                                                                               |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Hydrated SPA or JS-rendered template    | Needed fields appear in completed browser DOM but not raw HTTP; identify embedded JSON or an accessible endpoint before escalating to script/CDP. | Static HTML, public JSON, or a 404 does not need CDP merely because a site uses JavaScript elsewhere.                                        | Save sanitized raw and completed rendered responses; classify both; assert the field source and transport separately.                                              |
| Utility-class or generated-class layout | A selector depends on styling tokens (for example, a generated color/spacing class) rather than a semantic attribute.                             | The same utility class on a navigation card or a rebuild with changed CSS does not identify the target field.                                | Prefer structural/semantic anchors; test old/new layout and a decoy element with the same class.                                                                   |
| Localized routes and page chrome        | Language route, canonical locale, `<html lang>`, or punctuation in a title affects parsing.                                                       | A different language may change labels or title separators without changing the content entity.                                              | Assert language, canonical route and source-language text; test at least two locales before making a locale-agnostic claim. Preserve meaningful title punctuation. |
| Shared CMS or network template          | Two domains have independently verified equivalent DOM shape, routing and field semantics.                                                        | Matching branding or a similar card design does not imply selectors or studio mapping can be shared.                                         | Test a detail and populated search page per template/domain; use separate routing blocks for different page types and regressions for near-match URLs.             |
| Broad result-anchor selectors           | A search selector can also match header, related-content or navigation links.                                                                     | A populated page can still produce wrong URLs even when XPath cardinality is nonzero.                                                        | Assert card-scoped counts and representative URLs; include decoy navigation and related cards as negative cases.                                                   |
| URL rewriting and YAML regex            | Locale/domain rewrites, escaping and prefix rules are needed for canonical or result URLs.                                                        | A second rewrite can be unreachable, double-prefix a URL, or cause the committed YAML to fail parsing.                                       | Parse the exact committed YAML; test absolute, relative, localized and near-match URLs, then schema and URL-sort checks independently.                             |
| Optional or absent fields               | A source record genuinely omits a social link, performer, date or image.                                                                          | A missing value must not fall back to an unrelated page value or be interpreted as a layout failure without page classification.             | Assert an intentional absent value and a valid partial result alongside a populated case.                                                                          |
| Challenge, login or application failure | Raw or rendered response is not a completed target page.                                                                                          | Empty target selectors on a challenge or not-found page do not demonstrate selector drift; CDP does not fix an invalid URL or access denial. | Classify title/canonical/body/failure markers before field assertions; keep access and extraction outcomes separate. Never copy session material.                  |

**Promotion and feedback loop:**

1. Record the incident's source revision, response type, date, completed/error classification, selector or routing hypothesis, expected/actual values and remaining unknowns. Never store credentials, cookies, tokens or browser-profile contents.
2. Choose the smallest verified runtime: XPath on public HTML, then real JSON response, then necessary script action, then CDP only when a simpler path demonstrably fails. A completed saved DOM proves selector behavior on that snapshot only.
3. Add deterministic positive, optional/negative and failure-page cases to the fixture contract for the affected _class_ of problem; test card decoys, locale/layout variation or URL near-matches when relevant. For each configured search entity, author a populated result and separate detail case. The runner enforces only its documented assertions, not every authoring expectation; see [`07_Rendered_DOM_Fixture_Testing.md`](../../../docs/07_Rendered_DOM_Fixture_Testing.md).
4. Run schema, URL sort, policy, tests and documentation checks on the committed revision; record each result separately. No manifests means `UNVERIFIED`, not a fixture pass. Record raw live search and detail separately and require actual Stash/CDP output for a live-CDP claim.
5. Promote a proposed family pattern to [`best-practices.md`](best-practices.md) or a runtime-specific reference only after an independent site/layout test and a counterexample have been reviewed. Then update [`schema-checklist.md`](schema-checklist.md), relevant executable regression tests, and the owning authoring checklist together. If only one site supports it, keep it in the incident record as a site-specific hypothesis.
6. Do not mark production ready until the separate A–H evidence in [`04_Production_Gate.md`](../../../docs/04_Production_Gate.md) exists. An audit recommendation or checklist completion is not verification.

### Incident 3: YAML shape defects surfaced only at runtime load

**Date:** 2026-10-05  
**Provenance:** gayerdar zh-TW inspection record (2026-09-28, not committed); fix commits `268cd046`, `3417a7e9`, `6cf19994`.

**What happened:** a scraper YAML that parsed locally reached the Stash runtime and failed to load three times, each with a different Go unmarshal error: `queryURLReplace` is not a valid key under `sceneByName`/`performerByName` (`ByNameDefinition`); `performerScraper` must contain a `performer:` block rather than `common:`; and seven scene fields nested under a doubled `common:` block produced `cannot unmarshal !!map into string` errors. A fourth latent defect — `postProcess` written as a map instead of a list — was corrected during the same repair before it surfaced. These defects are not site-specific: they are shape violations of the scraper configuration grammar and can occur on any site family.

**Why review missed it:** no verification layer existed between "YAML parses" and "selectors verified"; runtime load was never executed before deployment; local reconstructions and authoring-time inspection stood in for loading the committed blob in a real Stash instance; upstream corpus files exist that place `queryURLReplace` under `sceneByName`, which made the shape look precedented even though the running Stash build rejects it.

**Detection and correction:** the user's live Stash instance reported loader errors with line numbers; fixes were made one error class at a time and verified only as far as the next error. The loader log, not any checklist, was the first control that caught the defects.

**Transferable rules:**

- Entry-point key sets differ by mode: verify the allowed keys per mode against the runtime; corpus precedent is not compatibility proof.
- Mapped scrapers must place scraped fields under `scene:`, `performer:`, `group:`, or `gallery:`; `common:` holds only `$name` string fragments.
- `postProcess` is a list of operations; `parseDate` is one such list item.
- Detail scrapers use `URLs` (plural); search scrapers use `URL` (singular) as the required link field. `Studio`, `Tags`, and `Performers` entries need a `Name:` sub-key.

**Feedback loop:** treat "loads in the Stash runtime" as a distinct evidence layer between schema validation and live extraction; record the loader error (or clean load) for the committed blob. Promote nothing past authored status without it.

### Prevention checklist

- Compare each normative schema claim to the local validator/schema derived from upstream, and consult `UPSTREAM_SOURCES.md` when provenance matters.
- Search the full reference tree for a changed rule; update duplicates, examples and ownership routes together.
- Parse and validate complete YAML examples; check the committed file, not only a local reconstruction.
- Mark `Source:` facts, `Heuristic:` transfers and evidence status distinctly; require a cross-site counterexample before declaring a generic pattern.
- Classify failure pages before selector work; separate raw, rendered fixture and live runtime evidence.
- Load the committed scraper in a real Stash instance before recording any status beyond authored; keep loader evidence separate from schema and live-extraction evidence.
- Run documentation and fixture controls and report what each pass does **not** establish.

## Further references

- `references/cdp-workflow.md` — CDP configuration
- `references/script-actions.md` — Script scraper patterns
