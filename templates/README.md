# Template — Scraper Scaffolding Templates

> **概要（zh-TW）：** 本目錄收錄 Stash scraper 的起始範本，包括宣告式 YAML 範本與 script-based 範本。YAML 範本負責 Stash entry-point 設定；script 範本由 YAML wrapper 加上 Python implementation 組成。複製範本、改檔名、填入 `name` 與選擇器或 script 參數後，務必先跑官方驗證器與品質閘門再提交。

This directory contains scaffolding templates for Stash scrapers. Declarative templates are YAML-only; script-based scrapers use a YAML entry-point wrapper plus a Python implementation scaffold. Templates are starting points, not working scrapers.

## Files

| File                                      | Object / role                     | Entry point or interface                             |
| ----------------------------------------- | --------------------------------- | ---------------------------------------------------- |
| `SceneScraperTemplate.yml`                | Scene                             | `sceneByURL`                                         |
| `WordpressSceneScraper.yml`               | Scene (WordPress `og:` meta)      | `sceneByURL`                                         |
| `PerformerScraperTemplate.yml`            | Performer                         | `performerByURL`                                     |
| `GroupScraperTemplate.yml`                | Group                             | `groupByURL`                                         |
| `GalleryScraperTemplate.yml`              | Gallery                           | `galleryByURL`                                       |
| `ImageScraperTemplate.yml`                | Image                             | `imageByURL`                                         |
| `ScriptScraper/ScriptScraperTemplate.yml` | Script-based multi-object wrapper | Stash `*ByURL`, `*ByName`, and fragment entry points |
| `ScriptScraper/ScriptScraperTemplate.py`  | Python implementation scaffold    | Operation argument received from the YAML wrapper    |

## Script template relationship

`ScriptScraper/ScriptScraperTemplate.yml` is the Stash-facing configuration. Each entry point selects `action: script` and invokes `ScriptScraperTemplate.py` with an operation such as `scene-by-url`, `scene-by-name`, or `performer-by-fragment`.

`ScriptScraperTemplate.py` is the implementation scaffold. It reads the operation and JSON input, returns a Stash-compatible JSON object or list, and writes diagnostics to stderr. Replace its example functions and operation coverage with the target site's real implementation; do not treat placeholder URLs, names, images, or metadata as verified data.

The two files are intentionally edited together:

1. Copy and rename the YAML wrapper into `scrapers/`.
2. Copy the Python scaffold into the matching dependency or scraper directory under `scrapers/`.
3. Keep operation names and relative paths synchronized.
4. Add the required root `name` to the YAML and remove unsupported modes.
5. Verify stdin/stdout behavior, dependencies, and error handling before validation.

## How to use

1. Choose the closest YAML template and copy it into `scrapers/` using a CamelCase filename.
2. For a script scraper, copy both `ScriptScraper/ScriptScraperTemplate.yml` and `ScriptScraper/ScriptScraperTemplate.py`; keep them as a matched pair.
3. Keep root `name:` in the YAML and make it conventionally match the filename.
4. Replace placeholder domains, selectors, operation names, and example metadata with site-specific values.
5. Include only entry points that the target site actually supports. `sceneByName` requires a real search flow and should be paired with `sceneByQueryFragment` when used.
6. For XPath/JSON fragment entry points, provide the required `queryURL`; script actions follow their script contract.
7. Validate with the official CommunityScrapers validator, then run the repository tests and quality gate.

Suggested checks:

```bash
npm run validate
npm run validate-sort
python -m pytest tools/tests/
python tools/check_scraper_docs.py
```

These templates contain placeholders and may not extract data until implementation details are filled in and tested.

## Documentation map

| Need                                | Read                                                                                                 |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------- |
| Repository-wide agent rules         | [`AGENTS.md`](../AGENTS.md)                                                                          |
| Repository workflow and ownership   | [`docs/repository-documentation-architecture.md`](../docs/repository-documentation-architecture.md)  |
| Skill contract and workflow         | [`skills/stash-scraper-builder/SKILL.md`](../skills/stash-scraper-builder/SKILL.md)                  |
| Script YAML and Python I/O contract | [`references/script-actions.md`](../skills/stash-scraper-builder/references/script-actions.md)       |
| Schema and entry-point checklist    | [`references/schema-checklist.md`](../skills/stash-scraper-builder/references/schema-checklist.md)   |
| Five-task regression pack           | [`references/eval-pack.md`](../skills/stash-scraper-builder/references/eval-pack.md)                 |
| Skill-local template checklist      | [`references/authoring-checklist.md`](../skills/stash-scraper-builder/references/authoring-checklist.md) |

## Naming and format rules

- New Markdown files use lowercase kebab-case; existing numbered documentation files remain stable.
- Scraper/template YAML files use CamelCase site/object names and `.yml`.
- Paired Python implementation files use the same CamelCase base name and `.py`.
- Use ISO dates (`YYYY-MM-DD`) in metadata and `# Last Updated` comments.

## Provenance

- **Source:** [stashapp/CommunityScrapers template set](https://github.com/stashapp/CommunityScrapers/tree/master/templates); script templates mirror upstream [`templates/ScriptScraper/`](https://github.com/stashapp/CommunityScrapers/tree/master/templates/ScriptScraper).
- **Retrieved:** 2026-08-30; script-template relationship documented 2026-09-03; script pair re-nested under `ScriptScraper/` to match upstream layout 2026-09-12.
- **Local changes:** directory layout and documentation cross-references only; template implementation files are byte-identical to upstream.
