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
last_verified: "2026-10-02"
authority: canonical
routing:
  intents:
    - ci
    - workflows
---

# CI Workflows

This map describes the workflow definitions in `.github/workflows/` reviewed on 2026-10-02. The date records a documentation review, not a passing run. GitHub Actions results must be checked for the exact commit; a skipped, filtered-out, or unrun job supplies no verification evidence.

## Repository checks

| Workflow file (display name) | Trigger | Scope and result |
| --- | --- | --- |
| `validate.yml` (Validate Scrapers) | Path-filtered push to `main` and PR | Main schema, URL sort, repository quality gate, regression tests, safeguards, and documentation checks. Only the commands actually executed are passes; its fixture self-test is not a site fixture. |
| `pr-check.yml` (Changed Scraper PR Check) | Path-filtered PR | Changed scraper files pass the per-file quality gate; documentation examples check separately. PR comment is feedback, not additional verification. |
| `fixture-manifests.yml` (Fixture Manifest Verification) | Fixture/runner-related push to `main` or PR | Discovers and executes committed fixture manifests. When none exist, discovery reports `UNVERIFIED` despite a successful workflow exit. A pass covers only present cases and assertions. |
| `evidence-contract.yml` (Evidence Contract) | Evidence/contract-related push to `main` or PR; weekly; manual | Checks structured evidence metadata, artifact paths and digests. Does not prove a site's live behavior. |
| `cdp-evidence-gate.yml` (Live CDP Evidence Gate) | Evidence/checker-related push to `main`; manual | Rejects certain unsupported CDP claims. Does not launch Stash or a browser and cannot produce live-CDP verification. |

## Manual and scheduled checks

| Workflow file (display name) | Trigger | Scope and result |
| --- | --- | --- |
| `scrutiny.yml` (Live Raw-Response Scrutiny) | Manual | Fetches HTTP and evaluates via JSDOM. Does not execute site JavaScript, render a browser DOM, or perform live Stash/CDP extraction. |
| `eval.yml` (Manual Python Regression Tests) | Manual | Runs all or one selected `tools/tests/test_*.py` file. Does not execute the five-task skill evaluation described in `references/eval-pack.md`. |
| `test-eval.yml` (Single Scraper Policy Check) | Manual | Runs the repository policy gate on one selected public scraper. Does not test `eval.yml` or replace schema, URL sorting, or full validation. |
| `link-check.yml` (Advisory Documentation Links) | Markdown-path PR; weekly; manual | Checks repository Markdown links, including hidden `.github` documentation. `fail: false` keeps broken external links advisory: inspect the report; a green workflow is not proof that all links resolved. |

## Evidence boundaries

Schema pass, URL-sort pass, policy-gate pass, regression-test success, fixture/snapshot verification, live-search verification, live-detail verification, live Stash/CDP verification, and production readiness are separate states. For each claim record the workflow run, revision, actual command, target, date, artifact, and limitations. A green job cannot stand in for an absent site manifest, a blocked page, or an authenticated runtime test. Use [`06_Testing_Guide.md`](06_Testing_Guide.md), [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md), and [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md) for the appropriate evidence type.

`eval.yml` and `test-eval.yml` are retained as narrow manual diagnostics pending confirmation that no required-status rule depends on their job IDs. They are not an Eval Pack, and no removal, consolidation, or live/CDP pass is implied by this map. Formatting (`npm run format:check`) and link checking must be evaluated separately; neither a documentation-index check nor this page proves they passed.
