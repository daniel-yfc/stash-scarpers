---
doc_id: DOC-E2E-98
title: "Wave 1C Agent Prompt - ACCEED Auth Guard"
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
    - wave-1c
    - acceed-auth-guard
---


# English implementation prompt — Wave 1C: ACCEED Authentication-Page Guard

## Mission and authority

You are the **Wave 1C implementation agent** for `daniel-yfc/stash-scarpers`. Once authorized, create `fix/e2e-acceed-auth-guard` from current `origin/main` and a **Draft PR → main** (historical base `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`). Independently investigate and narrowly address **STASH-E2E-09**: unauthenticated ACCEED detail pages were reported by Muse QA v2 to return a misleading `ログイン` Scene Title. You must **prove the mechanism before changing selectors**.

## Required reference URLs

- [Repository policies — AGENTS.md](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/AGENTS.md)
- [Stash Scraper Skill — REVISE and fail-closed rules](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/SKILL.md)
- [Parallel implementation plan / ACCEED-only ownership](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/92-fix-implementation-spec.md)
- [Muse QA v2 reported ACCEED evidence](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/91-live-e2e-evidence.md)
- [Candidate Stash Live Delta acceptance gates](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/94-delta-acceptance.md)
- [ACCEED.yml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/ACCEED.yml), [ACCEED.test.yaml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/ACCEED.test.yaml), [ACCEED fixtures](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tests/fixtures/acceed/acceed-fixtures.yml)
- [Quality Gate Rules](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/21-quality-gate-rules.md), [Testing Guide](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/50-testing-guide.md)
- [Secrets policy](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/references/phase0-secrets-policy.md), [CDP guidance](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/references/cdp-workflow.md)

Until PR #92 merges, these planning links refer to its docs branch. Create your implementation branch **from main, not the docs branch**.

## Exact task and evidence boundary

Muse's live Stash report v2: `ACSM051` and `ACST431` detail URLs redirect to a login page in an anonymous session and Scene Title is `ログイン`; anonymous `sceneByName` search for `ACST431` returned a real result. That report does **not** prove that the current `//div[@id='content4']//blockquote/h2...` selector itself matched the login page, nor does it prove how Stash builds a fallback Scene. Do not begin with arbitrary Title blacklists.

Exclusive editable files: `scrapers/ACCEED.yml`, `scrapers/ACCEED.test.yaml`, `tests/fixtures/acceed/`, and new dedicated ACCEED regression tests. Do **not** edit the Wave-1A Justice01/KOShop/CK-Download files, BRAVO, other scrapers, shared schema/validator/workflows, docs index or workbench.

## Required investigation and implementation

1. Pin actual main HEAD and inspect ACCEED's `sceneByURL`, `sceneByName` and `sceneByQueryFragment` definitions. Compare an authorized sanitized **completed login page**, expected product-only nodes, exact GraphQL output and the mode Stash selected. Separate actual selector matches from Stash normalization/fallback behavior. Without runtime access, report `ROOT_CAUSE_NOT_CONFIRMED`.
2. Add a reliable, sanitized offline negative fixture and verify a regression is **red on the original YAML** before changing anything. Also preserve a valid anonymous search control (`ACST431`) and an authorized product-page fixture where possible.
3. Implement the smallest schema-legal **product-page guard**. An unauthorized/login/error/challenge response must return **no misleading writable Scene metadata** across Title, Code, Studio, URLs, Tags and Performers—not just a blank Title. Do not suppress a valid product page. If Stash/YAML cannot express a safe fail-closed response, document the residual Stash limitation; do not pretend the behavior is fixed.
4. Preserve anonymous `sceneByName` and correctly selected `sceneByQueryFragment: "{url}"`. Do not add a direct Fragment mode. Avoid credentials, cookies, browser profiles or bypass instructions. **Do not attempt authenticated-site extraction** without separate lawful authorization, and never commit session material.
5. Run `npm ci`, `node validator/index.mjs -a --ci`, `bash tools/validate-all.sh`, `python tools/run_fixture_manifests.py`, `python -m pytest tools/tests/ -v` and `python tools/scan_session_material.py`; report PASS, FAIL or NOT_RUN with actual evidence.
6. Build exact PR candidate ZIP with full Git history using `python tools/build_scraper_source.py --output <isolated-preview-dir>` and `--verify-only`; document ACCEED revision and ZIP SHA-256. Open a focused **Draft PR** with a clear diagnosis, tests, rollback and Gate A/B/C status.
7. Shared stash-test may be operated **only by an authorized independent QA under exclusive lease** after M0. It must install the exact PR candidate, verify revision, test unauthenticated `ACSM051` and `ACST431` detail negative cases, and preserve `ACST431` anonymous Search. If authenticated positive tests are not authorized/available, mark `BLOCKED_AUTH` or `NOT_RUN`; **never claim logged-in Detail PASS**.
8. No production operations, no full 21-site live regression, no cross-branch edits and **no merge**.

## Final report contract

`BRANCH, PR_URL, HEAD_SHA, ROOT_CAUSE_EVIDENCE_OR_BLOCKER, CHANGED_FILES, NEGATIVE_AND_CONTROL_CASES, RED_GREEN_TESTS, GATE_A/B/C, EXACT_PACKAGE_VERSION_SHA256, AUTHENTICATED_CASE_STATUS, RESIDUAL_RISK, ROLLBACK, MERGE_STATUS=NOT_AUTHORIZED`.
