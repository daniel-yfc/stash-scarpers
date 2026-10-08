# XPath patterns

**Load when:** writing or fixing `scrapeXPath` selectors.

> **概要（zh-TW）：** `common` 鍵必須 `$` 開頭且不可互相引用；多節點預設只取第一個；用 `$x()` 五步驗證；關鍵欄位加 `|` 後援。

Canonical reference:

- https://deepwiki.com/stashapp/CommunityScrapers/8.2-selector-syntax
- https://deepwiki.com/stashapp/CommunityScrapers/4.3-advanced-xpath-techniques

## 1. `common` block

- Optional object; keys must match `^[$].+$` (start with `$`).
- Values are XPath **strings**, not selector objects.
- **No `$vars` key.** There is no `$vars` block in Stash YAML.
- **No common-to-common references.** `$row: "$info//dl/dd"` will not expand. Repeat the prefix, or use `$info` only inside field selectors.

```yaml
xPathScrapers:
  myScraper:
    common:
      $info: "//div[@class='detail-area']"
      $actorLink: "//a[contains(@href,'/actor/')]"
    scene:
      Title: "$info/h1"
      Performers:
        Name: "$actorLink"
```

Reject: `common.infoRow`, `common.$b: "$a/span"`, or `common.$info: { selector: "..." }`.

Always quote XPath in YAML.

## 2. Verify with `$x()` (5 steps)

1. Open the live URL in the browser (use visible Chrome / CDP if the page is JS-rendered or gated).
2. Compare view-source vs inspector. If the value lives in `application/ld+json` or `__NEXT_DATA__`, prefer that over the visual DOM (JSON/`script` may be better).
3. Inspect the element and write a semantic XPath (see §3).
4. Run `$x("//your-xpath")` in the console.
5. Confirm a non-empty result. Empty `$x()` = fail-to-fetch: fix or mark `# UNVERIFIED`.

## 3. Anchor priority

1. Unique / semantic attributes: `//div[@itemprop='video']`, `//a[@data-video-id]`, `//meta[@property='og:image']/@content`
2. Label text with `contains()`, not exact `text()='...`
3. Structural class (`concat(' ', normalize-space(@class), ' ')` when needed)
4. Positional index last; if unavoidable, add a text guard and a comment

## 4. Multi-selector fallbacks

`|` is XPath union. **Unions return nodes in document order, not expression order** — listing a preferred selector first does not guarantee it supplies the value when multiple alternatives match. Prefer mutually exclusive alternatives; if two hooks can coexist, test a page where both appear:

```yaml
Title:
  selector: "//h1[@class='title'] | //h1[@itemprop='name'] | //meta[@property='og:title']/@content"
```

Give every key field (Title, Date, Image, Studio) at least one fallback when the page has an alternative hook.

## 5. Evaluation order

1. Selector execution
2. Attribute-level `concat` (before `postProcess`)
3. `postProcess[]` — one operator per item
4. Attribute-level `split` (after `postProcess`)

Multiple matches return only the **first** value unless `concat` is set. Performers/Tags that should be a list must match multiple nodes (or `split` after concat).

Failed `parseDate` → empty. Unmatched `replace` / `map` → original string.

## 6. Placeholders

`{inputURL}` and `{inputHostname}` work in `selector` / `fixed` (after `queryURLReplace`). They do **not** apply to `queryURL` (`{}`, `{url}`, `{filename}`).

```yaml
URLs:
  fixed: "{inputURL}"
Studio:
  Name:
    fixed: "{inputHostname}"
```

## 7. Japanese shop patterns

- `dl/dt/dd` metadata: メーカー，レーベル，シリーズ，発売日，商品コード
- Image hrefs may be `upload/save_image/` or flattened `uploadsaveimage...jpg`
- Details often live in mixed text + `<br>` blocks — use `concat`
