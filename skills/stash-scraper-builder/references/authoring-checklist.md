# Template Workflow Checklist

Use this checklist when starting from a file in `templates/`.

## Select

- [ ] Choose the smallest viable runtime: XPath, JSON, script, or CDP.
- [ ] Copy a matching object template from `templates/`.
- [ ] For script scrapers, copy both `ScriptScraper/ScriptScraperTemplate.yml` and `ScriptScraper/ScriptScraperTemplate.py` as a matched pair (upstream: [`stashapp/CommunityScrapers` › `templates/ScriptScraper/`](https://github.com/stashapp/CommunityScrapers/tree/master/templates/ScriptScraper)).

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
- [ ] Run the official validator and URL sorting checks.
- [ ] Run `python -m pytest tools/tests/` and the repository quality gate.
- [ ] Mark untested assumptions as `# UNVERIFIED`.

## Documentation relationships

- Repository-wide rules: `AGENTS.md`
- Skill contract: `skills/stash-scraper-builder/SKILL.md`
- Script operations: `references/script-actions.md`
- Schema checks: `references/schema-checklist.md`
- Regression tests: `references/eval-pack.md`
- Repository workflow: `docs/template-workflow.md`

Templates are scaffolds, not verified scrapers. The official CommunityScrapers schema and validator override local examples and offline stubs.
