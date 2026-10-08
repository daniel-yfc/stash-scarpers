# Script Actions

**Load when:** `action: script` (including dependency packages).

> **概要（zh-TW）：** `*ByName` 回傳陣列、其餘回傳物件。`# requires:` 為檔案第一行註解；root `name:` 為官方 schema 必填（通常與 CamelCase 檔名一致）。每次輸出都要寫安裝前置。`performerByFragment` 僅限 script（有時 stash）；無 Python 套件就省略該模式。

## Contents

- [YAML shape](#yaml-shape)
- [Mode coverage (E1)](#mode-coverage-e1)
- [I/O contract (E4)](#io-contract-e4)
- [Script quality (E5)](#script-quality-e5)
- [Pagination (script only — B3)](#pagination-script-only-b3)
- [API error field (B4)](#api-error-field-b4)
- [Install prerequisites (every script-action response)](#install-prerequisites-every-script-action-response)
- [Directory](#directory)
- [Full mode skeleton](#full-mode-skeleton)
- [Python entry (when writing a script)](#python-entry-when-writing-a-script)

## YAML shape

```yaml
name: ExampleScript
# requires: DependencyName
sceneByURL:
  - action: script
    url:
      - sitename.com/en/video/
    script:
      - python
      - ../DependencyName/DependencyName.py
      - sitename
      - scene-by-url
```

- `# requires:` as a first-line comment after the optional YAML document comment/header. Root `name:` is required by the official schema and conventionally matches the CamelCase filename.
- Relative path `../DependencyName/script.py`.
- Typical extras: site id, then operation (`scene-by-url`). Keep that order on every action, including `groupByURL`.

Dependency-only package:

```yaml
name: PyCommon
# script used as a dependency only
# requires: py_common
```

A dependency-only package has no `*ByURL` / `*ByFragment` / `*ByName` entry points, but still uses the required root `name:` field.

## Mode coverage (E1)

- `performerByFragment` accepts **only** `action: script` (sometimes `action: stash`). Never `scrapeXPath` / `scrapeJson`.
- If no Python package exists for the site, **omit the mode entirely** — do not emit a `performerByFragment` block that cannot run.

## I/O contract (E4)

| Type       | stdin                      | stdout                     |
| ---------- | -------------------------- | -------------------------- |
| `*ByName`  | `{"name": "<query>"}`      | `[{...}]` even for one hit |
| All others | object (`url` or fragment) | `{...}` not an array       |

> **Never emit a bare object from a `*ByName` operation.** Stash parses search results as a list; a bare `{...}` yields zero results or a parse error. Zero hits → `[]`. One hit → `[{...}]`.

Empty: `[]` (ByName) or `{}`. Errors on **stderr**. `print(json.dumps(result))` on stdout — nothing else may be printed to stdout.

## Script quality (E5)

- Types: emit correct JSON types (numbers as numbers, lists as lists); do not stringify everything.
- Omit missing fields entirely instead of emitting `null` / empty guesses.
- Log via `py_common.log` (stderr), never `print()` for diagnostics.
- Strip query strings / tracking params from input URLs before matching or re-fetching.
- Cache repeated requests (same URL fetched for multiple fields) to avoid rate limits.
- Wrap every external request in `try/except`; on failure return `{}` / `[]` and log to stderr — never crash into a traceback on stdout.

## Pagination (script only — B3)

A YAML scraper fetches exactly one URL; `hasNextPage` / cursor pagination belongs in Python:

```python
results, cursor = [], None
while True:
    page = fetch_search(query, cursor)
    results.extend(page["items"])
    cursor = page.get("nextCursor")
    if not cursor:
        break
print(json.dumps(results))
```

## API error field (B4)

`scrapeJson` does not crash on an API `error` field, but a script must check it explicitly and return empty:

```python
data = resp.json()
if data.get("error"):
    log.error(f"API error: {data['error']}")
    print(json.dumps([] if op.endswith("by-name") else {}))
    sys.exit(0)
```

## Install prerequisites (every script-action response)

State all three:

- Python on `PATH` (Stash runs `python ...`).
- pip packages, e.g. `python -m pip install stashapp-tools requests beautifulsoup4 lxml` plus site clients (`algoliasearch`, `cloudscraper`, …).
- Every `../Dependency/...` path exists under `scrapers/` (`py_common/` at scrapers root; no `../` for `py_common` imports).

`ensure_requirements("requests", "beautifulsoup4")` may auto-install; still tell the user.

## Directory

```
scrapers/
├── py_common/
├── AlgoliaAPI/
│   ├── AlgoliaAPI.yml
│   └── AlgoliaAPI.py
└── ASGMax/
    └── ASGMax.yml          # script: ../AlgoliaAPI/AlgoliaAPI.py
```

## Full mode skeleton

Use only modes the site supports. `sceneByName` always pairs with `sceneByQueryFragment`. Prefer `group-by-url` for `groupByURL` (legacy scripts may still listen for `movie-by-url`).

```yaml
name: ExampleScript
# requires: SomeDependency
sceneByURL:
  - action: script
    url:
      - example.com/scene/
    script:
      - python
      - ../SomeDependency/script.py
      - example
      - scene-by-url
groupByURL:
  - action: script
    url:
      - example.com/movie/
    script:
      - python
      - ../SomeDependency/script.py
      - example
      - group-by-url
sceneByFragment:
  action: script
  script:
    - python
    - ../SomeDependency/script.py
    - example
    - scene-by-fragment
sceneByName:
  action: script
  script:
    - python
    - ../SomeDependency/script.py
    - example
    - scene-by-name
sceneByQueryFragment:
  action: script
  script:
    - python
    - ../SomeDependency/script.py
    - example
    - scene-by-query-fragment
performerByFragment:
  action: script
  script:
    - python
    - ../SomeDependency/script.py
    - example
    - performer-by-fragment
```

## Python entry (when writing a script)

```python
import json, sys
from py_common import log
from py_common.util import scraper_args
from py_common.deps import ensure_requirements
ensure_requirements("requests", "beautifulsoup4")

if __name__ == "__main__":
    op, args = scraper_args()
    match op, args:
        case "scene-by-url", {"url": url, **_}:
            result = scene_from_url(url)
        case "scene-by-name", {"name": name, **_}:
            result = scene_search(name)
        case "group-by-url", {"url": url, **_}:
            result = group_from_url(url)
        case _:
            log.error(f"Unknown operation: {op}")
            sys.exit(1)
    print(json.dumps(result))
```

ByName search returns `[]` on miss, never `None`. Log failures to stderr; return `None`/`{}`/`[]` rather than printing errors on stdout.

Config files: `Path(__file__).parent / "config.ini"`; create a default on first run if needed.
