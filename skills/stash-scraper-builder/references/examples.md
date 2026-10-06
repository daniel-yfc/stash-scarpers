# Examples

## Minimal performer entry point

For an XPath performer scraper, use `performerByURL`; the official schema does not permit `scrapeXPath` or `scrapeJson` for `performerByFragment`.

```yaml
name: ExamplePerformer
performerByURL:
  - action: scrapeXPath
    url:
      - example.test/performers/
    scraper: performerScraper

xPathScrapers:
  performerScraper:
    performer:
      Name:
        selector: "//h1[@class='performer-name']/text()"
```

Use `performerByFragment` only with `action: script`, when that mode is actually supported by the target and the required script dependency exists. `action: stash` is outside this skill's scope. Entry-point mappings reference root-level scraper definitions; they do not contain an inline `xPathScrapers` block.

## CJK / performer separator fixtures

When testing scrapers against Japanese or Chinese sites, include at least one fixture with:

- A CJK title (e.g., `魔法少女ほむら`)
- A bracketed title variant (e.g., `[ABC-123] タイトル`)
- A performer separator (e.g., `・` between co-performers)

These catch normalisation bugs in `replace`, `concat`, and post-processing rules early.
