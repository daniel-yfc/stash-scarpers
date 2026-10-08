# Template Workflow Checklist

**Load when:** starting a new scraper from a template in `assets/`.

Scaffold with `python scripts/new-scraper.py --name SiteName --mode xpath|json|performer`, or copy the matching asset by hand.

## Select

- [ ] Choose the smallest viable runtime: XPath, JSON, script, or CDP.
- [ ] Copy the matching template from `assets/` (`scene-xpath-template.yml`, `scene-json-template.yml`, `performer-xpath-template.yml`).
- [ ] For script scrapers, start from the upstream [`templates/ScriptScraper/`](https://github.com/stashapp/CommunityScrapers/tree/master/templates/ScriptScraper) pair (`.yml` + `.py`) instead.

## Adapt

- [ ] Rename the YAML to the site's CamelCase name.
- [ ] Keep the required root `name` key.
- [ ] Replace placeholder domains, paths, selectors, and metadata.
- [ ] Remove unsupported entry points; do not invent search modes.
- [ ] Keep YAML operation arguments synchronized with Python dispatch.
- [ ] Keep scraped values in the source language.

## Validate

- [ ] Fragment XPath/JSON modes include the required `queryURL`.
- [ ] Script stdin/stdout follows `script-actions.md`.
- [ ] `*ByName` returns a list; other operations return the expected object shape.
- [ ] Dependencies and relative paths exist.
- [ ] Run `python scripts/check-scraper.py`, then the official validator and URL sorting checks.
- [ ] Mark untested assumptions as `# UNVERIFIED`.

## Documentation relationships

- Skill contract: `SKILL.md`
- Script operations: `references/script-actions.md`
- Schema checks: `references/schema-checklist.md`
- Regression tests: `references/eval-pack.md`

Templates are scaffolds, not verified scrapers. The official CommunityScrapers schema and validator override local examples and offline stubs.
