---
doc_id: DOC-QG-21
title: Quality Gate Rules
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - ci
last_verified: "2026-10-15"
authority: canonical
routing:
  intents:
    - quality-gate
    - validation
---

# Quality Gate Rules

## Overview

The quality gate distinguishes schema validity, repository policy, and live-site behavior.

## Core rules

### Rule 1: Root name

Every XPath/JSON scraper must have a non-empty root `name:`. Matching the filename is recommended but is not an upstream schema requirement.

### Rule 2: Official validator

Use the official Node/Ajv validator and schema:

```bash
node validator/index.mjs -a -s scrapers
```

Do not use the removed Deno/localized validator.

### Rule 3: Credentials

Public files under `scrapers/*.yml` must not contain `driver.cookies`. Authenticated variants belong under `scrapers/private/`.

### Rule 4: Fragment scraping is optional

`sceneByFragment` is not required for every scraper. Omit it when the target site does not support reliable fragment/title lookup.

When `sceneByFragment` uses `scrapeXPath` or `scrapeJson`, it must include the action-required `queryURL`. If present, `sceneByQueryFragment` must preserve the selected URL with `queryURL: "{url}"`.

**Bare `"{url}"` is forbidden in `*ByFragment` queryURLs** (local policy — upstream schema permits `url` in the enum, but no upstream scraper does this in practice; verified 2026-10-15 across ~22 files). `sceneByFragment` / `performerByFragment` with `queryURL: "{url}"` only expands when the fragment already carries a URL; a URL-less fragment passes the literal string `{url}` to CDP (navigation fails), and the zero-row result triggers the upstream Stash nil-pointer panic in `processSceneRelationships` (documented: KOShop removed its `sceneByFragment` 2026-10-05; ACCEED / gayerdar / Pubu removed 2026-10-10). The same mechanism applies to `performerByFragment` — performer fragments built from name-only performer lists carry no URL by construction. Use `{title}` / `{filename}`-based queryURLs with `queryURLReplace` (cf. BRAVO `{title}`, fc2 `{filename}`), or omit the fragment mode. Note: `{code}` is **not** a valid `sceneByFragment` placeholder (absent from both the official docs list and the schema enum) — it exists only for `sceneByQueryFragment`.

`sceneByQueryFragment: "{url}"` remains required and is safe: Stash invokes it only to preserve an already-selected URL, so the placeholder always expands. Do not confuse the two modes.

Placeholder support matrix (verified 2026-10-15 against upstream schema + official docs):

| placeholder  | `sceneByFragment` | `sceneByQueryFragment` | source                    |
| ------------ | ----------------- | ---------------------- | ------------------------- |
| `{checksum}` | ✅                | ❌                     | scene file MD5            |
| `{oshash}`   | ✅                | ❌                     | scene file oshash         |
| `{phash}`    | ✅                | ❌                     | scene file phash          |
| `{filename}` | ✅                | ❌                     | scene filename            |
| `{title}`    | ✅                | ✅                     | fragment title            |
| `{url}`      | ✅                | ✅                     | fragment URL              |
| `{code}`     | ❌                | ✅                     | query-fragment code field |

`sceneByQueryFragment` input is a search-result fragment (no file fingerprints), so `{filename}`/`{checksum}`/`{oshash}`/`{phash}` are unavailable there. In practice all 10 verified upstream instances use `"{url}"`; the sole variant (ManyVids) adds `queryURLReplace` to rewrite the URL to a JSON API endpoint.

Mode → feature mapping: `sceneByFragment` serves Tagger / Identify / the `Scrape…` button (input: the scene's own fragment); `sceneByName` + `sceneByQueryFragment` serve the Scene Edit page query dropdown (input: selected search result). AutoTag uses no scraper. `performerByQueryFragment` does not exist in the schema (`additionalProperties: false`).

Practical notes:

- Search endpoints may need form-specific parameters: KOTube `/search/index` requires `x=0&y=0` (image-button coords) to trigger the 302 redirect to filtered results; without them `kw` is silently ignored (verified 2026-10-15).
- IP-based blocking happens: FC2 search rejects US datacenter IPs (verified 2026-10-15); scrapers relying on such endpoints should note the limitation.

### Rule 5: Date syntax

`parseDate` must use Go reference layouts, such as `2006-01-02`.

### Rule 6: Live verification

Schema validation does not prove that selectors match current site HTML. Record live verification separately in `docs/60-live-test-status.md`.

## Commands

```bash
bash tools/scraper-quality-gate.sh scrapers/ACCEED.yml
bash tools/validate-all.sh
python tools/check_scraper_docs.py
```
