# JSON Patterns

**Load when:** writing GJSON selectors or JSON entry points.

Patterns and guidance for JSON-based scrapers.

## Contents

- [queryURL rules](#queryurl-rules)
- [GJSON patterns](#gjson-patterns)
- [jsonScrapers structure](#jsonscrapers-structure)
- [Common patterns](#common-patterns)
- [Page URL → API rewrite (worked example)](#page-url--api-rewrite-worked-example)
- [References](#references)

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
- Filters use GJSON `#()` syntax, e.g. `items.#(type=="scene")#.title` —
  `[?(@.type=='scene')]` is JSONPath, not GJSON, and will not work
- Test GJSON expressions against a real API response before deploying
  (the schema validator does not execute them)

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

## Page URL → API rewrite (worked example)

Use when the user pastes an HTML page URL but metadata lives on a JSON endpoint.

```yaml
name: ExampleJson
# Last Updated: YYYY-MM-DD
sceneByURL:
  - action: scrapeJson
    url:
      - "examplesite.test/works/"
    queryURL: "{url}"
    queryURLReplace:
      url:
        - regex: ".*/works/([^/?#]+).*"
          with: "https://api.examplesite.test/v1/scene/$1"
    scraper: sceneJson

jsonScrapers:
  sceneJson:
    scene:
      Title:
        selector: "data.title"
      Date:
        selector: "data.release_date"
        postProcess:
          - parseDate: "2006-01-02"
      Image:
        selector: "data.cover_url"
      Studio:
        Name:
          fixed: "ExampleSite"
```

Test the regex against a real page URL before output. `sceneByName` cannot use `queryURLReplace`.

An API `error` field does not crash YAML `scrapeJson`; selectors just come back empty. Checking `error` and returning `{}` belongs in a `script` scraper (`script-actions.md`).

## References

- `references/script-actions.md` — When JSON isn't enough, use `script`
