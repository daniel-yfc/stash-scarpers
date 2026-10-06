# Post-processing pipeline

Canonical reference: https://deepwiki.com/stashapp/CommunityScrapers/3.3-post-processing-pipeline

## Order of operations

For each field:

1. Selector execution (multiple matches → first value only, unless `concat` is set)
2. `concat` — **attribute-level**, before `postProcess`. Not a `postProcess` operator.
3. `postProcess[]` in array order. Each item has **exactly one** operator.
4. `split` — attribute-level, after `postProcess`.

Putting `concat` inside `postProcess` fails schema validation.

## Operator order (quality)

Inside `postProcess`, go **specific → general**:

1. Extract the target substring (`replace` / `javascript`).
2. `parseDate` or `map`.
3. Only then trim / protocol / whitespace cleanup.

A broad `replace` first can destroy the date or studio token the later step needs.

## Supported operations

- `replace` — regex or plain. Unmatched → original string passes through.
- `parseDate` — Go reference layout (`2006-01-02`). Failed parse → field becomes **empty** (no error).
- `map` — exact-key remap (studio / gender). Prefer `map` over a long `replace` list for known variants. Unmatched key → original usually passes through; still list every real variant.
- `subScraper` — extra HTTP request; do not use by default.
- `javascript` — goja; `return` a string from `value`.
- `subtractDays` — after a day-count extract.
- `feetToCm` / `lbToKg` / `dimensionToMetric` — performer units, not dates.

Deprecated: inline `replace` / `parseDate` / `subScraper` outside `postProcess`.

## Patterns

```yaml
Details:
  selector: "//div[@class='desc']//text()"
  concat: "\n"
  postProcess:
    - replace:
        - regex: "</?[a-zA-Z][^>]*>"
          with: ""
```

```yaml
Studio:
  Name:
    selector: "//span[@class='brand']"
    postProcess:
      - map:
          "ex-site": "Example Site"
          "EXSITE": "Example Site"
```

```yaml
Image:
  selector: "//img[@id='poster']/@src | //meta[@property='og:image']/@content"
  postProcess:
    - replace:
        - regex: "^//"
          with: "https://"
        - regex: "/thumb/"
          with: "/poster/"
```

- Use `concat` when several nodes should become one string (Details, mixed `<br>`).
- Use `split` when one string should become an array.
- Avoid `subScraper` unless the value exists only on a second page.

## Date formats

Stash uses Go-style reference time layouts for `parseDate`. The reference time is `Mon Jan 2 15:04:05 MST 2006`.

| Site format       | Go layout         | Example input    |
| ----------------- | ----------------- | ---------------- |
| `2006-01-02`      | `2006-01-02`      | `2024-03-15`     |
| `02 Jan 2006`     | `02 Jan 2006`     | `15 Mar 2024`    |
| `January 2, 2006` | `January 2, 2006` | `March 15, 2024` |
| `02/01/2006`      | `02/01/2006`      | `15/03/2024`     |

Broken vs. fixed:

```yaml
# Broken — uses non-Go tokens, will silently produce wrong or empty dates
parseDate: "YYYY-MM-DD"

# Fixed — uses Go reference time
parseDate: "2006-01-02"
```

Always apply `replace` before `parseDate` when the raw date string contains noise:

```yaml
Date:
  selector: //span[@class="date"]/text()
  postProcess:
    - replace:
        regex: "Published: "
        with: ""
    - parseDate: "January 2, 2006"
```
