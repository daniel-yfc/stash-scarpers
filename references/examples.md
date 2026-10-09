# Examples

**Load when:** you want to see a pattern applied in a real scraper before writing your own. Prefer copying these shapes over inventing new ones.

## Minimal performer entry point

Start from [`assets/performer-xpath-template.yml`](../assets/performer-xpath-template.yml) (see `SKILL.md` § Entry contract). `performerByFragment` works only with `action: script`, when that mode is actually supported by the target and the required script dependency exists.

## CJK / performer separator fixtures

When testing scrapers against Japanese or Chinese sites, include at least one fixture with:

- A CJK title (e.g., `魔法少女ほむら`)
- A bracketed title variant (e.g., `[ABC-123] タイトル`)
- A performer separator (e.g., `・` between co-performers)

These catch normalisation bugs in `replace`, `concat`, and post-processing rules early.

## Curated real-world examples

| Example  | Source                                                                                               | Pattern demonstrated                                          |
| -------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- |
| KOVideo  | [KOVideo](https://github.com/daniel-yfc/stash-scarpers/blob/main/scrapers/KOVideo.yml)               | XPath union fallbacks; slider-clone exclusion                 |
| ACCEED   | [ACCEED](https://github.com/daniel-yfc/stash-scarpers/blob/main/scrapers/ACCEED.yml)                 | CDP + commented login-cookie template                         |
| HunkCh   | [HunkCh](https://github.com/daniel-yfc/stash-scarpers/blob/main/scrapers/HunkCh.yml)                 | FlexSlider clone exclusion; parenthesized union               |
| Andomark | [upstream](https://github.com/stashapp/CommunityScrapers/blob/master/scrapers/Andomark/Andomark.yml) | Multi-site network: URL groups → named scrapers; studio `map` |
| AyloAPI  | [upstream](https://github.com/stashapp/CommunityScrapers/tree/master/scrapers/AyloAPI)               | Script action + Python dependency package                     |

### KOVideo — union fallback with clone exclusion (local)

```yaml
Image:
  # bxSlider clones li.bx-clone nodes — exclude them. First branch is the
  # current template; second branch keeps the older template as fallback.
  # Verified 2026-10-08 round 3.
  selector: "(//ul[@id='main_item']/li[not(contains(@class,'bx-clone'))][1]//img/@src | //div[contains(@class,'detail_main_col')]//li[not(contains(@class,'bx-clone'))]//a[contains(@class,'fancybox') and not(contains(@href,'/gallery/'))][1]/@href)"
```

### ACCEED — CDP login cookie template (local)

```yaml
driver:
  useCDP: true
  # ... headers ...
#  cookies:                       # uncomment and fill your own values;
#    - Cookies:                   # never commit real values to a public repo
#        - Name: "LOGIN_KEEP_INFO"
#          Value: "請填入實際值"
#          Domain: ".acceed.jp"
#          Path: "/"
```

### HunkCh — parenthesized union (local)

```yaml
# FlexSlider injects li.clone nodes in live DOM — exclude them.
selector: "($product//div[contains(concat(' ',normalize-space(@class),' '),' flexslider ')]//ul[contains(@class,'slides')]/li[not(contains(@class,'clone'))][1]//img/@src | //meta[@property='og:image']/@content)"
```

### Andomark — network scraper (upstream)

One file serves 70+ sites: URL groups route to named scrapers (`oldStyle`, `newStyle`, `proSceneScraper`, …), shared `common:` blocks hold `$scene` anchors, and `Studio.Name.postProcess` normalizes domains via `map`. Date parsing chains fallbacks:

```yaml
postProcess:
  - replace:
      - regex: ".*?([0-9]{2}/[0-9]{2}/[0-9]{4}).*"
        with: $1
  - parseDate: 01/02/2006
  - parseDate: January 2, 2006
```

### AyloAPI — script package (upstream)

A Python package (`scrape.py`, `domains.py`, `package/`) behind `action: script`. See `script-actions.md` for the I/O contract and `# requires:` convention this example follows.
