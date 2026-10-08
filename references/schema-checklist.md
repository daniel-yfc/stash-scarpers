# Schema Validation Checklist

**Load when:** doing the final pre-emit verification pass.

Use this checklist before emitting a scraper YAML file. Run the repository's Node validator against its schema; its expectations derive from upstream CommunityScrapers (see `UPSTREAM_SOURCES.md`). A checklist is not a validator result.

## Contents

- [Top-Level Entry Points](#top-level-entry-points)
- [Required Structure](#required-structure)
- [Regex, XPath, and YAML Escaping](#regex-xpath-and-yaml-escaping)
- [Authority](#authority)
- [Scraper Definition](#scraper-definition)
- [Data Model and Selectors](#data-model-and-selectors)
- [Driver and Session Safety](#driver-and-session-safety)
- [Output and Evidence](#output-and-evidence)
- [Validation](#validation)

## Top-Level Entry Points

Official top-level fields (`name` is mandatory, all others optional).
Each entry point needs at least an `action` field; remaining fields depend
on the action. See `references/entity-fields.md` for the per-entity field lists.

| Entry point            | Scrapes                                                        |
| ---------------------- | -------------------------------------------------------------- |
| `performerByName`      | Performer by name search                                       |
| `performerByFragment`  | Performer by file fragment (script action only for XPath/JSON) |
| `performerByURL`       | Performer by URL                                               |
| `sceneByName`          | Scene by name search                                           |
| `sceneByQueryFragment` | Scene by query fragment                                        |
| `sceneByFragment`      | Scene by file fragment                                         |
| `sceneByURL`           | Scene by URL                                                   |
| `groupByURL`           | Group by URL (replaces deprecated `movieByURL`)                |
| `galleryByFragment`    | Gallery by file fragment                                       |
| `galleryByURL`         | Gallery by URL                                                 |
| `imageByFragment`      | Image by file fragment                                         |
| `imageByURL`           | Image by URL                                                   |

`movieByURL` is deprecated; use `groupByURL`.

URL-based entry points accept multiple configurations, each with a `url`
field. Stash compares them in order and executes the first configuration
whose `url` value is contained in the target URL.

## Required Structure

- [ ] Root `name` is present; matching the CamelCase filename is a convention, not an additional upstream schema requirement.
- [ ] File parses as YAML before committing (e.g. `python -c "import yaml,sys;yaml.safe_load(open(sys.argv[1]))" <file>`).
- [ ] At least one supported entry point (`sceneByURL`, `sceneByName`, etc.).
- [ ] Each entry has the fields required by its action and entry-point schema.
- [ ] `queryURLReplace` appears only under `*ByURL` / `*ByFragment` entry points; the current Stash runtime rejects it under `*ByName` (`ByNameDefinition`), even though some upstream corpus files carry the legacy shape.
- [ ] Fragment XPath/JSON entry points include the action-required `queryURL`; script actions follow their script contract.
- [ ] No unsupported root keys `documentHeader` or `$vars`.
- [ ] URL arrays are sorted with the validator's `-s` check.

## Regex, XPath, and YAML Escaping

> **概要（zh-TW）：** 所有 regex、XPath 與 YAML scalar 須以 YAML parser round-trip 交互驗證；雙引號 regex 值中每個要傳給正則引擎的反斜線，檔案內必須寫成 `\`；完整檔案以 `yaml.safe_load()` 驗證可解析。

- [ ] Every `regex:` value, XPath selector, and YAML scalar round-trips through a YAML parser: load the file, then confirm the loaded string equals the string the regex or XPath engine must receive.
- [ ] In double-quoted `regex:` scalars, each backslash intended for the regex engine is written as `\\` in the file (e.g. `\\d+`, `\\.`); single-quoted scalars need no doubling.
- [ ] The complete committed file parses with `yaml.safe_load()`.

## Authority

- [ ] Normative schema claims are checked against the official CommunityScrapers validator/schema; check `UPSTREAM_SOURCES.md` for provenance and compare with upstream when compatibility is in question.
- [ ] `references/scraper.schema.json` is a minimal offline stub, not a full validator or a pass/fail authority.

## Scraper Definition

- [ ] All referenced scraper keys exist.
- [ ] Mapped scrapers place scraped fields under the entity block (`scene:`, `performer:`, `group:`, `gallery:`); `common:` holds only `$name` string fragments, never field maps.
- [ ] `postProcess` is a list of operations (`- replace:`, `- parseDate:`), not a bare map.
- [ ] Classify pages before selector assessment: completed target versus challenge, login, paywall, age-gate, 404, application error, or partial render.
- [ ] Test XPath selectors on completed live pages or sanitized completed rendered-DOM fixtures when JavaScript rendering is required; label the actual evidence type.
- [ ] Compare raw HTTP and browser-rendered DOM where they differ; do not infer live Stash/CDP success from a snapshot.
- [ ] Test JSON paths on real JSON API responses.
- [ ] Do not invent search modes or endpoints.

## Data Model and Selectors

- [ ] Preserve meaningful title/source-language text; apply site-specific cleaning only where supported by examples.
- [ ] Date parsing uses Go layouts such as `2006-01-02`, not `YYYY-MM-DD` layout tokens.
- [ ] Studio mapping distinguishes source labels such as メーカー, レーベル, and シリーズ according to the site evidence.
- [ ] Image URL transformations and fallbacks are verified for the site; do not assume `/thumb/` to `/poster/` always works.
- [ ] Preserve performer names; omit a default `Gender` unless supported by the source.
- [ ] Assert selector cardinality (`min`/`max`) and representative expected values.
- [ ] For localized pages assert `<html lang>`, canonical URL locale, and source-language text where applicable.
- [ ] Test at least one missing/optional-field case without unrelated fallback data.

## Driver and Session Safety

- [ ] `driver.useCDP`, if used, is inside the top-level `driver` block only.
- [ ] Public scrapers (`scrapers/*.yml`) do not contain `driver.cookies`; session-dependent files are restricted to `scrapers/private/` under the local policy.
- [ ] No credentials, session cookies, clearance tokens, CSRF values, browser-profile data, or analytics identifiers are committed or reconstructed in YAML, fixtures, evidence, logs, or documentation.

## Output and Evidence

- [ ] Key fields (Title, Date, Studio, Image) match expected values on the pages actually tested.
- [ ] Untested selectors and assumptions are marked `# UNVERIFIED` with limitations recorded separately.
- [ ] An ISO `# Last Updated` comment is present; scraped values remain in the source language.
- [ ] Schema, URL sorting, policy, pytest, fixture, runtime load, live search, live detail, live Stash/CDP, and production readiness are recorded as separate states.
- [ ] A committed scraper that has never been loaded by the Stash runtime has no load evidence; a validator pass is not a loader pass.

## Validation

Run the mechanical pre-check first, then the official validator. Repeat until clean:

```bash
python scripts/check-scraper.py <file>.yml
# then the official CommunityScrapers validator against its schema
```

A passing check covers only its executed scope. A validator pass is not a Stash runtime load pass, and neither is a live-site scrape — record each evidence type separately.
