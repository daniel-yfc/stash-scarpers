# Field quality

**Load when:** building Title cleaning or Performer Name (and optionally Gender).

> **概要（zh-TW）：** Title 有序 `replace`：去標籤括號 → 去副檔名 → 折疊空白 → trim；Performer 漢字 > 英語 > 假名，保留 `・` / `-`，無明確性別欄位時不寫 Gender。

Canonical reference: https://deepwiki.com/stashapp/CommunityScrapers/10.3-best-practices

## Title patterns

Apply in this order. Do not hard-code expected titles.

```yaml
postProcess:
  - replace:
      # 1. Strip bracket tags that are not part of the real title
      - regex: "\\s*\\[.*?\\]\\s*$"
        with: ""
      - regex: "\\s*【.*?】\\s*$"
        with: ""
      - regex: "\\s*（.*?）\\s*$"
        with: ""
      # 2. Strip file extensions
      - regex: "\\.(mp4|mkv|avi|wmv|flv|ts|mpg|mpeg|rmvb|mov|m4v|iso)\\s*$"
        with: ""
      # 3. Collapse whitespace
      - regex: "\\s{2,}"
        with: " "
      # 4. Trim
      - regex: "^\\s+|\\s+$"
        with: ""
```

## Site-specific studio prefix

If the site always prefixes titles with the studio/brand, add one more `replace` before step 3:

```yaml
- regex: "^(BrandName\\s*[:：-]?\\s*)"
  with: ""
```

Do not translate the remaining title. Keep the source language.

## CJK punctuation

For sites that mix full/half-width punctuation, adjust step 1 to include full-width brackets or add a dedicated pass:

```yaml
- regex: "\\s*[\u3000-\u303f].*?\\s*$"
  with: ""
```

Tune per site; do not apply blindly.

## Performer name cleaning

| Input                              | Output     | Pattern                    |
| ---------------------------------- | ---------- | -------------------------- |
| `東出省吾 Shogo`                   | `東出省吾` | Hanzi (+ optional English) |
| `大河 (たいが)` / `大河（たいが）` | `大河`     | Hanzi + kana in parens     |
| `うる Uru`                         | `Uru`      | kana + English → English   |
| `たろう`                           | `たろう`   | pure kana                  |

## Canonical block (copy verbatim)

goja engine; input is `value`; must `return` a string. This is the canonical block used by this skill.

**goja constraints** (ES5.1-era engine): no named capture groups, no ES6+ syntax (`let`/`const`/arrow functions), and only ES5 built-ins. On an engine error goja returns the **original value** — a failed clean is silent, so test the block against real inputs rather than assuming an exception will surface.

```yaml
postProcess:
  - javascript: |
      var cleaned = value.replace(/\s+/g, ' ').trim();
      var m1 = cleaned.match(/^([\u4e00-\u9fff\u3400-\u4dbf]+(?:\s+[\u4e00-\u9fff\u3400-\u4dbf]+)*)(?:\s+[A-Za-z]+)?$/);
      if (m1) return m1[1].replace(/\s+/g, '');
      var m2 = cleaned.match(/^([\u4e00-\u9fff\u3400-\u4dbf]+)\s*[\(（][^\)）]+[\)）]$/);
      if (m2) return m2[1];
      var m3 = cleaned.match(/^[\u3041-\u3093\u30a1-\u30f6\u30fc\u3005\u309b\u309c]+\s+([A-Za-z]+)$/);
      if (m3) return m3[1];
      if (/^[\u3041-\u3093\u30a1-\u30f6\u30fc\u3005\u309b\u309c\s]+$/.test(cleaned)) return cleaned.replace(/\s+/g, '');
      return cleaned;
```

`\u4e00-\u9fff\u3400-\u4dbf` = CJK Unified + Ext. A. `\u3041-\u3093\u30a1-\u30f6` = hiragana + katakana. `\u30fc\u3005\u309b\u309c` = `ー々゛゜`.

## Preserve symbols

- Keep `・` and `-` unless the site standardizes names without them.
- Do not translate or romanize.

## Gender

Default: do not write Gender when no explicit field exists.

Single-gender sites may use `fixed` with a stated reason:

```yaml
Gender:
  fixed: "Female" # all performers on this site are female
```

When an explicit field exists, map to the schema enum (case-insensitive; capitalize output):

```yaml
Gender:
  selector: "//dt[contains(text(),'性別')]/following-sibling::dd[1]/text()"
  postProcess:
    - map:
        "男": "Male"
        "男性": "Male"
        "女": "Female"
        "女性": "Female"
```

## Aliases

If the site appends aliases like `Name / Alias`, strip the alias:

```yaml
postProcess:
  - replace:
      - regex: "\\s*/.*$"
        with: ""
```

## Unmatched regex

If none of the patterns match, return the original string. Do not force a rewrite.
