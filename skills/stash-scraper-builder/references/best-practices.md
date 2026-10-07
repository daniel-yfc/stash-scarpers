# Best practices for maintainable scrapers

Canonical reference:

- https://deepwiki.com/stashapp/CommunityScrapers/10.3-best-practices

## Structure & reuse

- Use YAML anchors (`&` / `*`) for shared scene/group selectors **only within the same file**, and only when a block is reused **3+ times**. Anchors live inside the **root-level** `xPathScrapers` block; entry points reference it via `scraper:` (entry points have `additionalProperties: false` and must not carry an inline `xPathScrapers:`).

```yaml
name: ExampleAnchors

sceneByURL:
  - action: scrapeXPath
    url:
      - https://example.test
    scraper: sceneScraper

sceneByFragment:
  action: scrapeXPath
  queryURL: https://example.test/search?q={url}
  scraper: sceneScraper

xPathScrapers:
  sceneScraper: &scene_selectors
    scene:
      Title: //h1/text()
      Date: //span[@class="date"]/text()
```

- Use `fixed:` studio for single-studio sites; use `map` for known variants (missed keys pass through unchanged).
- Add `# Last Updated: YYYY-MM-DD` in the file header (top comment block).
- Filename: CamelCase (site or network name).

## Studio normalization (G3)

Build a small matrix: domain → display name, handling:

- Apostrophe / hyphen variants (`Staggers'`, `Staggers-`)
- HD / POV casing (`HD`, `POV`)
- Parent / child studio relationships

Normalize site names to canonical studio names with `map` inside `Name.postProcess` (the official `studioObject` allows only `Name` / `URL` / `URLs`, so `map` cannot be a sibling of `Name:`).

```yaml
Studio:
  Name:
    selector: "//span[@class='studio']/text()"
    postProcess:
      - map:
          "SiteA": "Site A"
          "SiteB HD": "Site B"
          "SiteC POV": "Site C"
```

## Selector stability

- Prefer `|` fallbacks for sites that churn: `//h1[@class='new']//text() | //h1[@class='old']//text()`
- Image upgrade: `trailer` > `poster` > `thumb`
- Avoid hardcoded expected values inside XPath.

## Anti-patterns

- Overly deep or fragile XPath (`/html/body/div[3]/...`)
- Assuming every field exists on every page
- Using `subScraper` by default (see Legacy patterns below)
- Not testing with recent, old, and edge-case scenes

## Legacy patterns

`subScraper` chains a second scraper call to enrich initial results. It is no longer recommended for new scrapers because it adds maintenance complexity.

If you encounter an existing scraper that uses `subScraper`, prefer rewriting it as a script action or a single consolidated XPath/JSON scraper unless the chained lookup is genuinely unavoidable.

## Minimal Nubiles-style template (G1)

```yaml
# @meta
# Last Updated: 2026-08-26
# requires: py_common (if using script)

name: Nubiles

sceneByURL:
  - action: scrapeXPath
    url:
      - "nubiles.net/video/watch/"
    scraper: sceneScraper

xPathScrapers:
  sceneScraper:
    scene:
      Title:
        selector: "//h1[@itemprop='name']//text()"
      Date:
        selector: "//span[@itemprop='datePublished']//text()"
        postProcess:
          - parseDate: "2 Jan 2006"
      Image:
        selector: "//meta[@property='og:image']/@content"
      Studio:
        Name:
          fixed: "Nubiles"
      Performers:
        Name:
          selector: "//a[contains(@href,'/model/')]/text()"
      Tags:
        Name:
          selector: "//a[contains(@href,'/category/')]/text()"
```

## Header (G4)

- **Header** (top comment): list restrictions — UA, cookie, CDP, Python prerequisites — and `# Last Updated: YYYY-MM-DD`.
- Cookie scrapers: note that users must edit the YAML file to refresh cookies.
