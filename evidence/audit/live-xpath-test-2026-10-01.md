# Stash Scraper Test Report

**Repository**: `daniel-yfc/stash-scarpers@main`
**Skill**: `stash-scraper-builder` v2026-09-03
**Validator**: Python port of upstream `stashapp/CommunityScrapers/validator/validator.ts`
**Schema source**: `stashapp/CommunityScrapers/validator/scraper.schema.json` (canonical)
**Run date**: 2026-10-01

## TL;DR

- **Skill**: installed at `~/.config/opencode/skills/stash-scraper-builder/` (SKILL.md + 24 reference files, 25 docs total). Restart opencode to activate.
- **Scrapers tested**: 13 / 13 PASS schema + mapping validation
- **Browser control**: not used — targets are age-gated adult sites; CDP login state is out of scope for anonymous structural validation. Anonymously-verifiable selectors could be spot-checked via `gsk crawl --render_js` only if you provide a CDP-authenticated Chrome session.

| File                    | `name`              | useCDP | Last Updated |
| ----------------------- | ------------------- | :----: | :----------: |
| ACCEED.yml              | ACCEED              |   ✅   | 2026-09-06   |
| Bravo-Japan.yml         | Bravo-Japan         |   ✅   | 2026-09-06   |
| CK-Download.yml         | CK-Download         |   ✅   | 2026-08-28   |
| Coat.yml                | COAT                |   ✅   | 2026-08-28   |
| Games-Video.yml         | Games-Video         |   ❌   | 2026-09-06   |
| Hunks-Ch.yml            | Hunk's Channel      |   ✅   | 2026-09-06   |
| JGVData.yml             | JGVData             |   ❌   | 2026-09-05   |
| Justice01.yml           | Justice01           |   ✅   | 2026-09-06   |
| KO-Shop.yml             | KO Shop             |   ✅   | 2026-08-28   |
| KO-Tube.yml             | KO-Tube             |   ✅   | 2026-09-06   |
| Ko-Video.yml            | KO Video            |   ✅   | 2026-08-28   |
| Mens-RushTV.yml         | Men's Rush TV       |   ✅   | 2026-09-07   |
| fc2.yml                 | fc2                 |   ❌   | (missing)    |

## Validator Scope

The Python harness reproduces the upstream **stashapp/CommunityScrapers** validator:

1. **YAML 1.2 parse** that mirrors the official `yaml` npm package (date scalars stay as strings).
2. **JSON-schema validation** against `validator/scraper.schema.json` (Ajv-equivalent).
3. **Mapping checks** (mirrors `getMappingErrors()`):
   - `sceneByName` → requires `sceneByQueryFragment`
   - `scrapeXPath` → `xPathScrapers.<name>` defined and contains the matching object kind
   - `scrapeJson` → `jsonScrapers.<name>` defined and contains the matching object kind
   - `ByFragment` actions require an in-band `queryURL`
   - Stash server symbiosis: any `action: stash` triggers a `stashServer` block, and a `stashServer` block must be referenced
   - `driver.cookies` ↔ `driver.useCDP` consistency
4. **Repository policy** (README.md + schema-checklist.md):
   - Public files (`scrapers/*.yml`) must NOT contain `driver.cookies`
   - No credential-like tokens (`PHPSESSID`, `JSESSIONID`, `Bearer …`)
   - Root keys `documentHeader` and `$vars` are rejected
5. **URL array sorting** (the official `-s` flag is on by default) — all 13 clean.
6. **Documentation conventions**: `# Last Updated:` ISO date presence flagged.

YAML auto-parse quirk handled: pyyaml would interpret `parseDate: 2006-01-02` as a
`datetime.date`, breaking schema validation. A custom `SafeLoader` with overridden
`!!timestamp` and `!!date` constructors keeps them as strings — matching the
official `parseScraperYaml` behaviour (`yaml` npm pkg, version 1.2).

## Results — All 13 PASS

### Schema validation (canonical `scraper.schema.json`)

- 0 schema errors across all 13 files
- 0 mapping errors across all 13 files
- 0 driver-policy errors across all 13 files
- 0 credential leaks in 13 public files

### Stylistic notes (informational, not violations)

Five files use a display name different from the filename stem. The `schema-checklist.md`
says matching the CamelCase filename "is a repository convention, not an additional
upstream schema requirement" — these are notes only:

- `Coat.yml` → `name: COAT`
- `Hunks-Ch.yml` → `name: Hunk's Channel`
- `KO-Shop.yml` → `name: KO Shop`
- `Ko-Video.yml` → `name: KO Video`
- `Mens-RushTV.yml` → `name: Men's Rush TV`

One file (`fc2.yml`) is missing the `# Last Updated:` comment — schema doesn't require
it but the repo convention does.

### CDP / Cookie coverage

10 scrapers rely on `driver.useCDP: true` (login via visible Chrome, no cookies
embedded in YAML — safe for public sharing). 3 scrapers don't use CDP at all
because their target pages are publicly fetchable:
- `Games-Video.yml`: comment notes "No age gate; plain HTML 200 without cookies — CDP not required."
- `JGVData.yml`: no `driver:` block
- `fc2.yml`: no `driver:` block

No scraper embeds `driver.cookies` — every public file is safe to share.

## Browser Control

The user asked to "control this browser if need". Decision and rationale:

- **Was it needed?** Not for the static validation above. The 13 YAML files
  validate against the canonical schema and pass all structural/policy checks
  without network access.
- **What would require a browser?** Verifying XPath selectors against live
  rendered pages, especially the CDP-gated ones. The ACCEED comment ("sceneScraper:
  UNVERIFIED — detail pages redirect anonymous sessions to /login.php") already
  records the only publicly-known live limitation. Anything beyond this requires
  **a Chrome instance with cookies for each site** running at `ws://localhost:9222`,
  plus a Stash instance.
- **What is available locally?** `gsk crawl --render_js` is the proxy-driven
  crawler available in the sandbox; it renders JS but does NOT carry authenticated
  sessions. It would be appropriate only for the anonymously-fetchable sites
  (Games-Video, JGVData, fc2, ACCEED search page). I did not run it because the
  user gave no target URLs to spot-check, and the upstream README already records
  the verification status for each public search.

If you want me to actually drive a browser:
1. Spin up Chrome with `--remote-debugging-port=9222` (or have Stash do it).
2. Tell me which scraper(s) and which concrete scene URLs to verify.
3. I'll attach Playwright/Chrome DevTools Protocol via the
   `~/.config/opencode/opencode.json` `mcp.playwright` entry (or use `chrome-remote-interface`).

## Notes for the Maintainer

Quick wins (all repo-policy cosmetic, none blocking):

1. **fc2.yml**: add `# Last Updated: 2026-10-01` (only file missing it).
2. **Coat.yml**: `name: COAT` is unusual — consider a lowercase `name: Coat`
   to match the filename.
3. The `# UNVERIFIED` markers present on the page-required selectors (e.g.
   ACCEED's sceneScraper) are correctly in place and pass the schema-checklist's
   "Untested selectors and assumptions are marked" criterion.

## Live-Site Test (`live_test.py`)

A second harness crawls each scraper's target URL through `gsk crawl --raw`,
parses the response with `lxml`, and evaluates every XPath selector declared
in the scraper against the rendered DOM. Stash `$variables` defined in `common:`
blocks are resolved before evaluation. Results per scraper go to
`/tmp/stash-test/results/live-test.json` (mirrored to
`/home/user/output/live-test.json`).

### Crawl-decision policy
| Status             | # of files | Reason                                                  |
| ------------------ | :--------: | ------------------------------------------------------- |
| `login_required`   |   **10**   | `useCDP: true` or `driver.cookies` — anonymous test impossible |
| `domain_skipped`   |    **1**   | Target host matches `SKIP_DOMAINS` (e.g. `adult.contents.fc2.com`) |
| `no_target_url`    |    **1**   | Only a bare-host URL is declared; no usable scene URL   |
| `ok`               |    **1**   | Crawled + rendered + evaluated selectors                |

For the one scraper that ran:

- **Games-Video.yml** — target: `https://www.games-video.co.jp/dvd_detail.php?code=WIG-387`
  - 13 selectors collected; 13 evaluable; **3 matched**, **10 returned 0**, **0 errors**.
  - **Matched**: Title (`h2` in `div.titlebar`), Code (`input[name=code]/@value`), Image (`a[rel=lightbox]/@href`).
  - **Zero-match but parseable** (search-scraper `$card` references a completely different page; `$prop` selectors reference a `#property` table that does not exist in the live HTML at the time of this crawl — DOM drift suspected).
  - **Notes**: `//link[@rel='canonical']/@href` returned 0 — there is no `<link rel="canonical">` on this Dreamweaver-templated page.

### Selector results breakdown (Games-Video.yml, detail page)

| Status      | Count | Examples (≤90 chars)                                                                                  |
| ----------- | :---: | ---------------------------------------------------------------------------------------------------- |
| matched ≥ 1 |   3   | Title, Code, Image                                                                                   |
| zero        |  10   | 4× `$card` (wrong page), 5× `$prop` (table drift), `rel=canonical` (no tag), `Details` (heading drift) |
| error       |   0   | —                                                                                                     |

### What this means for the maintainer

- The 10 login-required scrapers need a CDP-attached Chrome to test
  end-to-end. Once you spin up `ws://localhost:9222`, point the harness at
  that and re-run.
- The 10 zero-match selectors in Games-Video suggest either (a) site changes
  since the scraper was authored, (b) scraping a search page vs. detail page
  mismatch, or (c) the `#property` table is rendered by JS that `--raw` doesn't
  reach. The YAML comment ("VERIFIED against …_detail.php?code=WIG-387") suggests
  the prior author verified similar fields by hand — they need re-verification
  through this harness to keep the comment accurate.
- fc2 is intentionally not crawled even though it has no driver block, because
  its host matches `SKIP_DOMAINS`. Edit `SKIP_DOMAINS` in `live_test.py` if you
  want to verify it on a private host.

## Reproduction

```bash
# Pull canonical validator + schema
mkdir -p /tmp/stash-test
curl -fsSL https://raw.githubusercontent.com/stashapp/CommunityScrapers/master/validator/scraper.schema.json \
  -o /tmp/stash-test/scraper.schema.json

# Pull scrapers
for f in ACCEED.yml Bravo-Japan.yml CK-Download.yml Coat.yml Games-Video.yml \
         Hunks-Ch.yml JGVData.yml Justice01.yml KO-Shop.yml KO-Tube.yml \
         Ko-Video.yml Mens-RushTV.yml fc2.yml; do
  curl -fsSL "https://raw.githubusercontent.com/daniel-yfc/stash-scarpers/main/scrapers/$f" \
    -o "/tmp/stash-test/scrapers/$f"
done

# Run structural validator
python3 /tmp/stash-test/validate.py

# Run live XPath test (skips CDP-gated + adult domains by default)
python3 /tmp/stash-test/live_test.py
```

Raw structural: `validation.json` (per-file schema/mapping/policy).
Raw live: `live-test.json` (per-file XPath match counts and resolved XPath).
