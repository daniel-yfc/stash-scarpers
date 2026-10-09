---
doc_id: DOC-OPS-40
title: CI Workflows
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - ci
  - testing
last_verified: "2026-10-06"
authority: canonical
routing:
  intents:
    - ci
    - workflows
---

# CI Workflows

This map describes the eight workflow definitions in `.github/workflows/` reviewed on 2026-10-06. The date records a documentation review, not a passing run. GitHub Actions results must be checked for the exact commit; a skipped, filtered-out, or unrun job supplies no verification evidence.

## Repository checks

| Workflow file (display name)                            | Trigger                                                        | Scope and result                                                                                                                                                                                     |
| ------------------------------------------------------- | -------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `validate.yml` (Validate Scrapers)                      | Path-filtered push to `main` and PR                            | Main schema, URL sort, repository quality gate, regression tests, safeguards, and documentation checks. Only the commands actually executed are passes; its fixture self-test is not a site fixture. |
| `pr-check.yml` (Changed Scraper PR Check)               | Path-filtered PR                                               | Changed scraper files pass the per-file quality gate; documentation examples check separately. PR comment is feedback, not additional verification.                                                  |
| `fixture-manifests.yml` (Fixture Manifest Verification) | Fixture/runner-related push to `main` or PR                    | Discovers and executes committed fixture manifests. When none exist, discovery reports `UNVERIFIED` despite a successful workflow exit. A pass covers only present cases and assertions.             |
| `evidence-contract.yml` (Evidence Contract)             | Evidence/contract-related push to `main` or PR; weekly; manual | Checks structured evidence metadata, artifact paths and digests. Does not prove a site's live behavior.                                                                                              |
| `cdp-evidence-gate.yml` (Live CDP Evidence Gate)        | Evidence/checker-related push to `main`; manual                | Rejects certain unsupported CDP claims. Does not launch Stash or a browser and cannot produce live-CDP verification.                                                                                 |

## Validation commands

The main `validate.yml` checkout sets up Node and Python, then executes these repository checks in order. This is an implementation map, not a claim that a specific run passed:

```bash
npm ci || npm install
node validator/index.mjs -a --ci
node validator/index.mjs --ci templates/*.yml
node validator/index.mjs -a -s --ci
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/parse_committed_yaml.py
node tools/verify-scraper-fixtures.mjs --self-test
python tools/scan_session_material.py
python tools/check_evidence_labels.py
python tools/check_live_cdp_status.py
python tools/self_evaluate.py
python tools/check_scraper_docs.py
python tools/check_docs_index.py
python3 tools/check_docs_official.py
python3 tools/check_scraper_semantics.py
python tools/check_metadata_feed.py
```

`tools/verify-scraper-fixtures.mjs --self-test` tests only the fixture runner. Site-specific manifest discovery and assertions belong to `fixture-manifests.yml`; the absence of manifests is `UNVERIFIED`, even if its discovery command exits successfully. `npm run format:check` is a separate local formatting check, not a `validate.yml` step.

## Manual and scheduled checks

| Workflow file (display name)                          | Trigger                                     | Scope and result                                                                                                                                                                                           |
| ----------------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scrutiny.yml` (Live Raw-Response Scrutiny)           | Manual                                      | Fetches HTTP and evaluates via JSDOM. Does not execute site JavaScript, render a browser DOM, or perform live Stash/CDP extraction.                                                                        |
| `verification-staleness.yml` (Verification Staleness) | Weekly; scraper-path push to `main`; manual | Parses `validated_on` metadata and reports STALE / AGING / FRESH / UNKNOWN / NO_META buckets; opens a tracking issue when a scheduled run detects STALE scrapers.                                          |
| `link-check.yml` (Advisory Documentation Links)       | Markdown-path PR; weekly; manual            | Checks repository Markdown links, including hidden `.github` documentation. `fail: false` keeps broken external links advisory: inspect the report; a green workflow is not proof that all links resolved. |

## Evidence boundaries

Schema pass, URL-sort pass, policy-gate pass, regression-test success, fixture/snapshot verification, live-search verification, live-detail verification, live Stash/CDP verification, and production readiness are separate states. For each claim record the workflow run, revision, actual command, target, date, artifact, and limitations. A green job cannot stand in for an absent site manifest, a blocked page, or an authenticated runtime test. Use [`06_Testing_Guide.md`](06_Testing_Guide.md), [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md), and [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md) for the appropriate evidence type.

`eval.yml` and `test-eval.yml` were retired as duplicate manual diagnostics on 2026-10-02. The five-task skill evaluation in `skills/stash-scraper-builder/references/eval-pack.md` remains an authoring checklist, not an executable CI result. Formatting and link checking must be evaluated separately; neither a documentation-index check nor this page proves they passed.
