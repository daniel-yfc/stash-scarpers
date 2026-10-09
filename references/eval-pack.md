# Eval Pack — 5 Tasks

**Load when:** you modified the skill itself and need to verify it still works end-to-end, or you were asked to self-test the skill.

> **Status:** not wired into CI — run manually. If any task fails, fix the workflow or checklists, then re-run.

> **概要（zh-TW）：** 五個任務，各對應一種失敗模式。每題都要輸出完整 YAML、勾選 checklist、標記 selector 驗證狀態（`# UNVERIFIED` 加註解說明原因）。

## Contents

- [Pass criteria (all tasks)](#pass-criteria-all-tasks)
- [Test matrix (H1 / #31)](#test-matrix-h1-31)
- [Verification checklist (Expected vs Actual)](#verification-checklist-expected-vs-actual)
- [Task 1 — New XPath site (public HTML)](#task-1-new-xpath-site-public-html)
- [Task 2 — New `scrapeJson` site (real JSON API)](#task-2-new-scrapejson-site-real-json-api)
- [Task 3 — Script + dependency](#task-3-script-dependency)
- [Task 4 — Date `&nbsp;` fix (complete file)](#task-4-date-nbsp-fix-complete-file)
- [Task 5 — Login-gated site](#task-5-login-gated-site)
- [Scoring](#scoring)

## Pass criteria (all tasks)

- [ ] Output is a **complete** YAML file (no fragments, no "unchanged" placeholders).
- [ ] Only modes the site verifiably supports are present.
- [ ] `sceneByName` ⇒ `sceneByQueryFragment` present; otherwise both omitted.
- [ ] Every selector is either verified on a real page/response or marked `# UNVERIFIED` with an explanation.
- [ ] Official CommunityScrapers validator passes (or local stub with known limitations noted).
- [ ] The complete YAML loads in the Stash runtime (loader pass). A validator pass alone is not load evidence (see `debugging.md`, Incident 3).
- [ ] Script tasks include the three install prerequisites in the **response**.
- [ ] CDP task includes visible-CDP setup steps (or explicitly states "out of scope").

## Test matrix (H1 / #31)

Test each task against these scenarios:

| Scenario                                   | Purpose                                     |
| ------------------------------------------ | ------------------------------------------- |
| **New** (recent scene)                     | Verify current HTML structure               |
| **Old** (archive scene)                    | Catch selector drift over time              |
| **Missing field** (no performers, no date) | Ensure graceful handling of optional fields |
| **Multi-performer** (3+ performers)        | Verify array handling, not single-value     |
| **Non-ASCII** (CJK, accented Latin)        | Ensure encoding and regex handling          |

**Network scrapers:** test 3–5 domains from the network to confirm template consistency.

## Verification checklist (Expected vs Actual)

For each task, verify:

- [ ] Title matches expected (no studio prefix, correct brackets preserved)
- [ ] Date is ISO `YYYY-MM-DD` and matches expected calendar day
- [ ] Studio.Name matches expected (not parent/child confusion)
- [ ] Image is HTTPS and high quality (not a thumb)
- [ ] Details has no HTML tags

A scraper that returns the wrong studio is a fail, even if the YAML is valid.

## Task 1 — New XPath site (public HTML)

**Site:** Use any real public HTML site with scene pages.

**Requirements:**

- `sceneByURL` required; add `sceneByFragment` only if the site verifiably supports fragment scraping (never as a nil-pointer workaround).
- Title cleaning from `field-quality.md`.
- Date with `parseDate` (Go layout matching the site).
- Performers with canonical JS from `field-quality.md`; `Gender` omitted unless explicit.
- Studio `Name` only (or `fixed` for single-brand).

**Expected output:** one complete YAML, all selectors verified or marked `# UNVERIFIED`.

**Failure modes to catch:**

- Fragment-only output.
- Missing title cleaning or wrong `parseDate` layout.
- Invented `sceneByName`.
- Mapped-shape errors: scraped fields under `common:` (or a doubled block) instead of `scene:`/`performer:`; `queryURLReplace` under `*ByName`.

## Task 2 — New `scrapeJson` site (real JSON API)

**Site:** Use any real JSON API that returns scene metadata.

**Requirements:**

- `sceneByURL` (mandatory) + `sceneByName` + `sceneByQueryFragment` (**only if the API has a real search endpoint**).
- `action: scrapeJson` with GJSON selectors.
- Title cleaning + `parseDate` on the release date field.
- Performers array with canonical JS.
- Use `jsonScrapers` (not `xPathScrapers`).

**Expected output:** one complete YAML using `jsonScrapers`.

**Failure modes to catch:**

- Invented GJSON paths not tested on the real response.
- Using `scrapeXPath` on a JSON-only endpoint.
- Putting `scrapeJson` definitions in `xPathScrapers`.

## Task 3 — Script + dependency

**Site:** Use any site that already has a shared Python scraper.

**Requirements:**

- `sceneByURL` required; add `sceneByFragment` only if the site verifiably supports fragment scraping (or more supported modes).
- `action: script` with `# requires:` and the dependency path.
- If the site supports `performerByFragment`, test it (script-only mode).
- Response must state: Python on PATH, pip packages, dependency files exist.

**Expected output:** one complete YAML + install prerequisites in the explanation.

**Failure modes to catch:**

- Missing `# requires:` or wrong relative path.
- No install notice in the response.
- `*ByName` returning a bare object instead of an array.

## Task 4 — Date `&nbsp;` fix (complete file)

**Input:** Existing scraper that fails on `15&nbsp;Jan&nbsp;2024`.

**Requirements:**

- Fix the Date field with `replace` then `parseDate`.
- Return the **entire** scraper file, not just the Date block.

**Expected output:** full YAML with the corrected Date `postProcess`.

**Failure modes to catch:**

- Fragment output ("only the changed section").
- `parseDate` before `replace` (still fails).

## Task 5 — Login-gated site

**Site:** Any real login/paywall/human-check site.

**Requirements:**

- Do **not** emit a scraper that silently returns nothing.
- Either:
  - Emit `driver: useCDP: true` **and** the visible-CDP steps, or
  - State that login-gated scraping is out of scope for this skill.

**Expected output:** YAML + CDP steps, or an explicit "out of scope" explanation.

**Failure modes to catch:**

- `useCDP: true` without the setup steps.
- Plain HTTP scraper that will fail on a gated page.

## Scoring

| Task      | Pass   | Fail |
| --------- | ------ | ---- |
| 1 XPath   | 1      | 0    |
| 2 JSON    | 1      | 0    |
| 3 Script  | 1      | 0    |
| 4 Date    | 1      | 0    |
| 5 CDP     | 1      | 0    |
| **Total** | **/5** |      |

Target: **5/5** before calling the skill "done." If any task fails, fix the workflow or checklists, then re-run.
