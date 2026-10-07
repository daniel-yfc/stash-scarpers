# JSON scraper examples

**Load when:** you need a complete-file `scrapeJson` template.

> **概要（zh-TW）：** `scrapeJson` 定義只能放 `jsonScrapers`。root `name:` 為官方 schema 必填，通常與 CamelCase 檔名一致。先用真實 API 回應驗證路徑。

## 1. Scene + search (real JSON API)

```yaml
name: ExampleJson
# Last Updated: YYYY-MM-DD
sceneByURL:
  - action: scrapeJson
    url:
      - "api.examplesite.test/v1/scene/"
    scraper: sceneJson

sceneByName:
  action: scrapeJson
  queryURL: "https://api.examplesite.test/search?q={}"
  scraper: sceneSearch

sceneByQueryFragment:
  action: scrapeJson
  queryURL: "{url}"
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
      Details:
        selector: "data.description"
      Image:
        selector: "data.cover_url"
      Studio:
        Name:
          selector: "data.studio.name"
      Performers:
        Name:
          selector: "data.performers.#.name"
      Tags:
        Name:
          selector: "data.tags.#.name"
  sceneSearch:
    scene:
      Title:
        selector: "results.#.title"
      URL:
        selector: "results.#.url"
      Image:
        selector: "results.#.cover_url"
```

If search hits omit a detail API URL, rewrite `{url}` with `queryURL` + `queryURLReplace` on `sceneByQueryFragment` (see `json-patterns.md`). Never set `sceneByQueryFragment`'s `queryURL` to `.../search?q={title}`.

## 2. Page URL → API (`queryURLReplace`)

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

Test the regex against a real page URL before output. `sceneByName` cannot use `queryURLReplace`. For a `sceneByURL` entry, the official schema permits only the `url` replacement key; fragment modes permit `checksum`, `filename`, `oshash`, `phash`, `title`, or `url`. Custom names such as `id` and `slug` are not valid replacement keys.

An API `error` field does not crash YAML `scrapeJson`; selectors just come back empty. Checking `error` and returning `{}` belongs in a `script` scraper (`script-actions.md`).
