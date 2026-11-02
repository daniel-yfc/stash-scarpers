# STASH-E2E-02-UPSTREAM-REPORT-DRAFT.md
**Status: DRAFT — NOT FILED. Pending Controller review and authorization.**
**Do not submit without explicit authorization from the tracking owner.**

---

## Title

`scrapeSceneURL` panics with `index out of range [0] with length 0` when no installed scraper matches the URL (same pattern in all six `scrape*URL` queries at source level)

## Environment

- **Stash version:** `v0.31.1-182-g9e9ad972` (commit [`9e9ad972`](https://github.com/stashapp/stash/commit/9e9ad972643320e737c711884f10e4285f0f3a88), built 2026-10-27)
- **Source verification:** as of 2026-11-02, `pkg/scraper/cache.go` and `internal/api/scraped_content.go` on `develop` HEAD are byte-identical (same git blob) to the tested build, so the code path below also applies to current `develop`.
- **Setup:** standard GraphQL API usage against a local server with community scrapers installed; no plugins or exotic configuration involved.

## Minimal reproduction

Prerequisite: at least one scene-by-URL scraper installed, but **no** installed `sceneByURL` rule matches the URL below (e.g., a scraper whose URL patterns only match `/clips/` paths).

```graphql
query ReproUnmatchedSceneURL($url: String!) {
  scrapeSceneURL(url: $url) {
    title
    code
    urls
  }
}
```

```json
{"url": "https://example.com/__stash-unmatched-url-repro__"}
```

The URL is a placeholder control value — the only requirement is that no installed `sceneByURL` scraper matches it.

## Expected behavior

A normal GraphQL response: either a `null` result or a controlled, descriptive error such as "no scraper matches this URL". No runtime panic.

## Actual behavior

The query fails with a Go runtime panic surfaced as a GraphQL error:

```text
runtime error: index out of range [0] with length 0
```

The panic is deterministic: 5/5 attempts against URLs not matched by any installed `sceneByURL` rule reproduced it (see matrix below), while a URL matched by an existing rule returned valid scraped data.

## Exact error text

- GraphQL error message: `runtime error: index out of range [0] with length 0`
- `STACK_TRACE_NOT_CAPTURED`: a full goroutine stack trace was not captured in the saved evidence for this run. The server log shows the recovered panic entry for the request, but the complete goroutine dump is not available; it can be re-captured on request with troubleshooting mode enabled.

## Reproduction matrix

| Case | URL (sanitized) | Matched by installed sceneByURL? | Result | Runs |
|---|---|---|---|---|
| Unmatched control | `https://example.com/__stash-unmatched-url-repro__` | No | panic | 2/2 |
| Unmatched real-site control | `https://www.bravo-japan.com/dvds/234` | No (installed scraper routes only `/clips/`) | panic | 2/2 |
| Unmatched real-site control | `https://www.bravo-japan.com/dvds/084` | No (same) | panic | 1/1 |
| Matched control | a `/clips/` URL supported by the installed scraper | Yes | normal scraped scene returned | pass |

Total: 5/5 unmatched-URL attempts panicked; the matched-URL control behaved normally. All runs used the same Stash build and the same scraper set. Site URLs above are from a publicly accessible site and contain no private data.

## Source-level call chain (exact commit `9e9ad972`)

1. `internal/api/resolver_query_scraper.go` — `queryResolver.ScrapeSceneURL` calls `scrapeCache().ScrapeURL(ctx, url, ScrapeContentTypeScene)`; on `err == nil` it unconditionally calls `marshalScrapedScene(content)`.
2. `pkg/scraper/cache.go:312-333` — `Cache.ScrapeURL` iterates installed scrapers; only a scraper whose `supportsURL(url, ty)` matches is invoked. **When no scraper matches, it returns `(nil, nil)` at line 332** — a nil `ScrapedContent` with a nil error.
3. `internal/api/scraped_content.go:164-171` — `marshalScrapedScene(content)` delegates to `marshalScrapedScenes([]scraper.ScrapedContent{content})`. The plural helper **skips nil entries** (`if c == nil { continue }`, line 15), so for nil input it returns an **empty slice and a nil error**. Line 170 then executes `return s[0], nil` on the empty slice — the panic.

The same unguarded `[0]` index exists in all six single-object marshalling helpers and is reachable from all six URL-scraping queries; only `scrapeSceneURL` has been runtime-verified in this report:

| Query | Marshal helper | Unguarded index (commit `9e9ad972`) | Evidence level |
|---|---|---|---|
| `scrapeSceneURL` | `marshalScrapedScene` | `scraped_content.go:170` | runtime-reproduced (5/5) |
| `scrapePerformerURL` | `marshalScrapedPerformer` | `scraped_content.go:160` | source-level only |
| `scrapeGalleryURL` | `marshalScrapedGallery` | `scraped_content.go:180` | source-level only |
| `scrapeImageURL` | `marshalScrapedImage` | `scraped_content.go:190` | source-level only |
| `scrapeMovieURL` | `marshalScrapedMovie` | `scraped_content.go:200` | source-level only |
| `scrapeGroupURL` | `marshalScrapedGroup` | `scraped_content.go:210` | source-level only |

Additionally, `Cache.ScrapeURL` returns a nil result with no error when no scraper matches, so there is currently no way for a client to distinguish "no scraper for this URL" from "scraper returned nothing".

## Stack trace availability

`STACK_TRACE_NOT_CAPTURED` — see "Exact error text" above. This report's root-cause analysis is based on the runtime error text plus source inspection at the exact build commit (file-level identity verified against git blob hashes), not on a captured goroutine dump.

## Related issues

- #7275 — describes this exact marshalling path (typed-nil and empty-slice indexing in the single-object helpers). It was closed as **not planned** on 2026-10-12 with no linked PR and no fix landing; the affected files are unchanged on `develop` as of 2026-11-02. This report provides an independent, template-compliant reproduction with runtime evidence.
- #7315 / #6921 / PR #6857 — a **different** panic (nil pointer dereference in `mappedScraper.processSceneRelationships`, `pkg/scraper/mapped.go:89`), fixed by PR #6857. Not the root cause here.
- #4415 — queryURL/fragment placeholder behavior; unrelated mechanism.

## Security / privacy review

- Reproduction uses only `example.com` placeholder URLs and public site URLs; no scene IDs, filenames, or library metadata are included.
- No API keys, cookies, auth headers, internal IPs/hostnames, or account information appear in this report.
- Server logs referenced in the internal evidence package are **not** attached here; only the error text above is quoted.

## Suggested fix direction (optional)

- In the six single-object marshalling helpers, check the slice length before indexing and return `(nil, nil)` when empty (mirroring the nil-skip already performed by the plural helpers).
- Optionally, have `Cache.ScrapeURL` return a descriptive typed error (or an explicit "no matching scraper" signal) instead of `(nil, nil)`, so clients can distinguish unmatched URLs.
- Unit tests: empty content, typed-nil content, valid content preservation, and wrong content types for each helper — the same coverage outlined in #7275.

---

*Prepared as part of internal tracking `daniel-yfc/stash-scarpers#97` (WS-D / STASH-E2E-02). This draft has not been submitted to the upstream repository.*
