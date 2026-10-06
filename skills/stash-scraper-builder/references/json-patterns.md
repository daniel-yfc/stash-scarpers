# JSON Patterns

Patterns and guidance for JSON-based scrapers.

## queryURL rules

| Mode                             | queryURL value                                                                                                                                                         |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sceneByName`                    | `{}` (empty object for search endpoint)                                                                                                                                |
| `sceneByQueryFragment`           | `{url}` of the selected hit, optionally rewritten with `queryURLReplace`.                                                                                              |
| `sceneByURL` / `sceneByFragment` | Use a direct API URL or an action-supported rewrite of the pasted URL. For XPath/JSON fragment actions, provide the required `queryURL`; do not assume it is optional. |

**Official queryURL placeholders:**

- `{}` — empty object (used for `sceneByName` search endpoint)
- `{url}` — the selected hit URL (used for `sceneByQueryFragment`)
- `{filename}` — the scraper filename (fragment modes)
- `{title}` — official for `sceneByFragment`; use it only where that entry point and the target site’s URL contract support it

**Important:** For `sceneByQueryFragment`, use `{url}` to pass the selected scene URL. Do not construct queryURLs pointing to search endpoints for fragment queries. A fragment action that requires a queryURL must include one; script actions follow their script contract.

`queryURLReplace` keys are **official placeholder names only** (verified against the v0.31.1 runtime and the upstream schema): `url` for all ByURL entry points; `checksum`, `filename`, `oshash`, `phash`, `title`, `url` for fragment modes. Each key's value is an array of `{regex, with}` replacements. Custom capture names such as `id` or `slug` are silently ignored by the runtime (`applyReplacements` looks up only the built-in parameter map) and rejected by the schema.

```yaml
name: ExampleJsonScraper
sceneByName:
  action: scrapeJson
  queryURL: "https://api.example.com/search?q={}"
  scraper: searchJson

sceneByQueryFragment:
  action: scrapeJson
  queryURL: "{url}"
  scraper: sceneJson
```

## GJSON patterns

- Use `items.#.field` notation for arrays
- Filters like `[?(@.type=='scene')]` may return null; prefer direct path or use `script`
- Test GJSON expressions in validator before deploying

## jsonScrapers structure

```yaml
jsonScrapers:
  scene:
    Title: $.title
    Date: $.date
    Studio:
      name: $.studio.name
    Image: $.poster_url
    Performers: $.actors.#.name
```

## Common patterns

### Nested objects

```yaml
Studio:
  name: $.studio.name
  url: $.studio.url
```

### Arrays

```yaml
Performers: $.cast.#.name
Tags: $.tags.#.name
```

### Conditional fields

```yaml
Date:
  selector: $.release_date
  postProcess:
    - parseDate: 2006-01-02
```

## References

- `references/json-examples.md` — Complete JSON scraper templates
- `references/script-actions.md` — When JSON isn't enough, use `script`
