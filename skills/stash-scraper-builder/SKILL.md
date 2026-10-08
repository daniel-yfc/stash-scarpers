---
name: stash-scraper-builder
description: >-
  Build, modify, validate, and debug StashApp scraper YAML files using XPath,
  JSON, script, and CDP modes. Use when creating a scraper for a supported
  site, fixing empty fields, nil dates, or nil pointer errors, validating
  scraper YAML, or mapping studio, performer, or group extraction.
  Do not use for generic web scraping, generic YAML, Identify or stash-box
  scrapers, fabricated search endpoints, or CommunityScrapers PR submission.
metadata:
  version: "2026-10-09"
  canonical-schema: "https://github.com/stashapp/CommunityScrapers/blob/master/validator/scraper.schema.json"
---

# Skill: stash-scraper-builder

**Version**: 2026-10-09
**Scope**: Generate Stash scraper YAML files that load and scrape correctly.
**Canonical runtime**: Official CommunityScrapers validator and schema.
**Standalone use**: This skill works outside the `stash-scarpers` repo. Steps marked **repo-only** apply inside that repo; otherwise use the official CommunityScrapers validator/schema and skip repo-specific commands.

## When to use

Use this skill when authoring, modifying, validating, or debugging a Stash scraper. **Repo-only**: for repository setup, CI, contribution, or project-wide documentation, see [`docs/repository-documentation-architecture.md`](../../docs/repository-documentation-architecture.md), the root README, and `docs/` instead.

## Entry contract

Emit a complete YAML file using a root `name:` and only entry points and actions verified for the target site. Use the official CommunityScrapers schema and validator as the authority.

```yaml
name: ExampleScraper
sceneByURL:
  - action: scrapeXPath
    url:
      - example.com
    scraper: sceneScraper

xPathScrapers:
  sceneScraper:
    scene:
      Title: //h1/text()
```

## Authoring workflow

1. Inspect the site, entity type, page/response format, authentication requirements, and real URL patterns.
2. Read [`references/skill-read-order.md`](references/skill-read-order.md), then select the smallest viable runtime: XPath, JSON, script, or CDP.
3. Add only verified entry points. Do not invent search modes or query endpoints.
4. Use stable selectors and preserve scraped values in the source language.
5. Mark unverified selectors and assumptions with `# UNVERIFIED`.
6. Validate with the official CommunityScrapers validator when available; the local schema stub is non-authoritative.
7. Return the complete YAML, verification status, and only the relevant script/CDP prerequisites.

## Runtime selection

Choose the simplest viable implementation path before writing any scraper.

| Situation                                            | Approach                                                               | Avoid when                                     |
| ---------------------------------------------------- | ---------------------------------------------------------------------- | ---------------------------------------------- |
| Public HTML, stable fields                           | `scrapeXPath` with `xPathScrapers`                                     | Content is JavaScript-only or requires login   |
| Real JSON body or endpoint                           | `scrapeJson` with `jsonScrapers`                                       | Response only appears after browser automation |
| Existing shared Python implementation                | `script`                                                               | A simpler declarative scraper is enough        |
| Login, paywall, JavaScript-only, or human-check flow | CDP (`driver.useCDP: true`) after reading `references/cdp-workflow.md` | Direct HTTP scraping already works             |

- Start with the least complex path that reliably extracts the target metadata.
- Prefer declarative YAML over scripts when XPath or JSON selectors are sufficient.
- Use CDP only when direct requests are blocked by login, JavaScript rendering, or anti-bot interstitials.
- Stash-box / Stash GraphQL is out of scope for this skill (see `references/out-of-scope.md`).

## Core constraints

- Root `name:` is required and should conventionally match the CamelCase filename.
- Do not emit unsupported root keys `documentHeader` or `$vars`.
- For XPath/JSON fragment entry points, provide the action-required `queryURL`; script actions follow their script contract.
- Mapped scrapers place scraped fields under the entity block (`scene:`, `performer:`, `group:`, `gallery:`); `common:` holds only `$name` string fragments.
- `sceneByFragment` is not a nil-pointer workaround. Test non-matching fragment input and report upstream runtime failures.
- Keep public scrapers free of cookies and browser state; use private paths for authenticated variants.

## Reference map

| Need                      | Reference                                                                             |
| ------------------------- | ------------------------------------------------------------------------------------- |
| Read order and ownership  | `references/skill-read-order.md`                                                      |
| Source selection & scope  | `SKILL.md` § Runtime selection, `references/out-of-scope.md`                          |
| Security & secrets policy | `references/phase0-secrets-policy.md`                                                 |
| Authoring checklist       | `references/authoring-checklist.md`                                                   |
| XPath extraction          | `references/xpath-patterns.md`                                                        |
| JSON extraction           | `references/json-patterns.md` and `references/json-examples.md`                       |
| Script actions            | `references/script-actions.md`                                                        |
| CDP / Headless workflow   | `references/cdp-workflow.md`                                                          |
| Dates & formatting        | `references/post-processing.md` (§ Date formats)                                      |
| Post-processing           | `references/post-processing.md`                                                       |
| Field quality             | `references/field-quality.md`, `references/entity-fields.md`                          |
| Best practices & patterns | `references/best-practices.md`, `references/multi-site-network-scrapers.md`           |
| Debugging                 | `references/debugging.md`, `references/incident-reviews.md`                           |
| Examples & validation     | `references/examples.md`, `references/schema-checklist.md`, `references/eval-pack.md` |
| Upstream sources          | `references/UPSTREAM_SOURCES.md`                                                      |

## Output contract

- Explanations are in English with a short zh-TW orientation.
- Scraped values remain in the source language.
- Emit the entire YAML, not a diff or fragment.
- Include verification status and mark untested selectors.
- Include script installation prerequisites or CDP setup only when those paths are used.

## Definition of done

- [ ] Root `name:` is present.
- [ ] Only verified modes are included.
- [ ] Required fragment `queryURL` is present for XPath/JSON actions.
- [ ] Official validator passes, or local-stub limitations are documented.
- [ ] The committed blob loads in the Stash runtime; a validator pass alone is not load evidence (see `references/debugging.md`, Incident 3).
- [ ] URL arrays are sorted.
- [ ] Key fields are verified on the target pages/responses.
- [ ] No credentials appear in public files.
- [ ] **Repo-only**: repository tests and quality gates are run when the task changes repository files.

## Notes

The official CommunityScrapers schema and validator override local stubs and prose. Use repository-level documentation for commands and governance; use this skill and its references for scraper authoring.
