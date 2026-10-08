# Out of Scope

**Load when:** you are unsure whether a task belongs to this skill.

This skill covers CommunityScrapers-style YAML, JSON, and script scrapers only.

## Included

- Declarative XPath scraping (`scrapeXPath`)
- JSON endpoint scraping (`scrapeJson`)
- Script-based scraping (`script`)
- CDP-assisted login workflows for browser-gated targets
- Validation, quality-gate, and review practices for public and private scraper variants

## Excluded

- `action: stash` workflows
- Stash-box integration
- Stash GraphQL API usage and `ApiKey`-based authentication
- Generic third-party API-auth scraper patterns (unless added as a separate future expansion)

### `action: stash` reference (excluded from authoring)

For completeness: the official docs define a `stash` action that uses another
Stash server as a scrape source. It requires a top-level `stashServer` field
with `url` (may embed `username:password@host`, or use `apiKey`
authentication). It applies only to `performerByName`, `performerByFragment`,
`sceneByName`, `sceneByQueryFragment`, and `sceneByFragment`. This skill does
not author `stash`-action scrapers; see the official ScraperDevelopment page
for the full specification.

## Reading guidance for upstream docs

| Upstream doc                           | Treatment                                                             |
| -------------------------------------- | --------------------------------------------------------------------- |
| `docs.stashapp.cc/api/`                | Background context only — not implemented here                        |
| `docs.stashapp.cc/metadata-sources/`   | Broader ecosystem view — this skill covers the scraper branch only    |
| DeepWiki architecture and driver pages | Design context — not a claim that all integration paths are supported |
