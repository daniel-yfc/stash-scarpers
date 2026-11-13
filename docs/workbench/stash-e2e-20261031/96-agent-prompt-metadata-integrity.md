---
doc_id: DOC-E2E-96
title: "Wave 1A Agent Prompt - Metadata Integrity"
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - live-e2e
last_verified: "2026-10-31"
authority: derived
routing:
  intents:
    - agent-prompt
    - wave-1a
    - metadata-integrity
---


# English implementation prompt — Wave 1A: Metadata Integrity

## Mission and authority

You are the **Wave 1A implementation agent** for `daniel-yfc/stash-scarpers`. Once explicitly authorized to implement, create the branch `fix/e2e-metadata-integrity` from the latest `origin/main` and a **Draft PR targeting main**. Historical baseline: `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`. Record if main has advanced. You are the sole owner of **Justice01, KOShop and CK-Download** fixes (STASH-E2E-05, 06a/06b, 08). Wave 1B BRAVO and Wave 1C ACCEED run concurrently on separate branches. Do not merge, push to main, modify production Stash or bypass authentication.

## Read these exact repository references first

- [AGENTS.md — repository rules](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/AGENTS.md)
- [Stash Scraper Builder Skill — REVISE, P0–P6](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/SKILL.md)
- [Implementation Plan — branch ownership and dependencies](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/92-fix-implementation-spec.md)
- [Muse Live E2E v2 evidence ledger — reported, not independently replayed](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/91-live-e2e-evidence.md)
- [Stash Delta QA acceptance and exact-package provenance](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/94-delta-acceptance.md)
- [Quality Gate Rules](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/21-quality-gate-rules.md); [Testing Guide](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/50-testing-guide.md); [Scraper Source Builder](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tools/build_scraper_source.py)
- [Justice01.yml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/Justice01.yml), [Justice01 fixture manifest](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tests/fixtures/justice01/justice01-fixtures.yml)
- [KOShop.yml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/KOShop.yml), [KOShop fixture manifest](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tests/fixtures/koshop/koshop-fixtures.yml)
- [CK-Download.yml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/CK-Download.yml), [CK-Download fixture manifest](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tests/fixtures/ckdownload/ckdownload-fixtures.yml)

Until PR #92 merges, read the planning docs from its **docs branch** as linked above; create implementation branches **from main, never from PR #92**.

## Strict files allowed

Only `scrapers/Justice01.yml`, `scrapers/KOShop.yml`, `scrapers/CK-Download.yml`, the corresponding `scrapers/*.test.yaml` sidecars, `tests/fixtures/{justice01,koshop,ckdownload}/`, and dedicated *new* regression tests with Wave-1A-specific names. Do not edit `BRAVO.yml`, `ACCEED.yml`, `docs/workbench/**`, `docs/index.yml`, `validator/**`, workflows, other scrapers, or shared test files without explicit Controller scope approval.

## Required changes

**Justice01 — STASH-E2E-05.** Current detail `URLs` concatenate canonical and og:url, causing a newline/duplicate value. Make canonical the primary URL with og:url **only if canonical is missing**; emit one valid URL, no newline or duplicate. Test the known `justice115th` case plus a controlled no-canonical fallback fixture. Do not split a bad concatenated value and claim it repairs the XPath semantics.

**KOShop — STASH-E2E-06a.** Search-result URL postProcess deletes all query parameters, including the required `product_id`. Preserve and safely normalize the identity parameter. The `KERO256` query must return a URL with `?product_id=...` which can be selected and scraped as the correct detail.

**KOShop — STASH-E2E-06b.** A missing item (`product_id=99999999`) returns an error-page Title that could be saved as Scene metadata. Only accept proven product detail structure. Assert that **all writable metadata fields** avoid misleading values; an empty Title with a bogus URL/Code/Studio is not a pass. Verify the valid `41979` control still returns Code `BWB365_DVD`. If the YAML schema cannot fail closed safely, report the precise blocker instead of inventing unsupported keys.

**CK-Download — STASH-E2E-08.** The detail Title XPath combines `DVDタイトル` td, product h3 and `//title` in a union, but XPath union uses document order, not priority. Use actual completed product DOM to implement explicit, guarded Title selection; avoid generic site title fallback. On `detail/34418`, the URL-mode Title should match the correct Search result `ORCOAV028`; also test a different DVD product and an error-page negative case.

## Development order, tests and deliverables

1. Inspect exact main HEAD and source pages/fixtures, classify source state (product/login/error/blocked) and record root-cause evidence. **Do not invent DOM, metadata or source URLs.**
2. Create meaningful offline regression tests **red before fix → green after**, then make narrow YAML changes. Prefer **three reviewable commits**: Justice01, KOShop (both findings), CK-Download. Avoid unnecessary refactors.
3. Run, report actual output and reasons for any NOT_RUN:
   - `npm ci`
   - `node validator/index.mjs -a --ci` and `node validator/index.mjs -a -s --ci`
   - `bash tools/validate-all.sh`
   - `python tools/run_fixture_manifests.py`
   - `python -m pytest tools/tests/ -v`
   - `python tools/scan_session_material.py`
4. With full Git history, build branch-specific candidate packages using `python tools/build_scraper_source.py --output <isolated-preview-dir>`, then rerun with `--verify-only`. Record index version, package ZIP SHA-256 and exact PR head for all three edited scrapers.
5. Open a **Draft PR → main** with changed-file whitelist, detailed before/after field expectations, negative-case results, tests, hashes, rollback and Gate A/B/C table. Use the PR conversation to report results; do not modify PR #92 workbench docs in parallel.
6. Shared `stash-test` is managed by an **independent QA lease**. Do not install candidate ZIPs, reload scrapers or write to Stash unless separately authorized. Gate B must prove the exact candidate installed (not existing main), then test original failing probes, positive controls and negative cases. No live access → `GATE_B_NOT_RUN` and PR remains Draft.
7. Do not execute 21-site live E2E, do not commit cookies, credentials or browser state, do not merge.

## Required final report (English or zh-TW)

Return `BRANCH, PR_URL, HEAD_SHA, CHANGED_FILES, FINDING_IDS, SOURCE_DOM_EVIDENCE, RED_GREEN_TESTS, GATE_A/B/C, CANDIDATE_VERSION_AND_ZIP_SHA256, LIVE_E2E_CASES_AND_EVIDENCE_REFS, BLOCKERS, ROLLBACK, MERGE_STATUS=NOT_AUTHORIZED`. Do not mark `FIXED_VERIFIED` until independent live QA of the exact PR package is complete.
