---
doc_id: DOC-E2E-97
title: "Wave 1B Agent Prompt - BRAVO Clips"
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
    - wave-1b
    - bravo-clips
---


# English implementation prompt — Wave 1B: BRAVO Clips / Fragment Safety

## Mission and authority

You are the **Wave 1B implementation agent** for `daniel-yfc/stash-scarpers`. Once authorized, create `fix/e2e-bravo-clips` from latest `origin/main` and open a **Draft PR → main**. Starting historical baseline: `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`. Fix **STASH-E2E-03** (Clips Title/Code) and the **BRAVO-specific part of STASH-E2E-04** (empty-title direct Fragment produces bogus URLs). Do **not** add DVD support in this branch; that belongs to `feat/e2e-bravo-dvds` after this PR is merged.

## Required references

- [Repository AGENTS.md](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/AGENTS.md)
- [Stash Scraper Builder Skill — REVISE](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/skills/stash-scraper-builder/SKILL.md)
- [Implementation Plan / Wave 1B ownership](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/92-fix-implementation-spec.md)
- [Reported Live E2E findings](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/91-live-e2e-evidence.md)
- [Design decisions and exclusions](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/93-design-decisions-and-references.md)
- [Gate A/B/C and candidate-package provenance](https://github.com/daniel-yfc/stash-scarpers/blob/docs/workbench-stash-e2e-20261031/docs/workbench/stash-e2e-20261031/94-delta-acceptance.md)
- [BRAVO.yml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/BRAVO.yml), [BRAVO.test.yaml](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/scrapers/BRAVO.test.yaml), [BRAVO fixtures](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/tests/fixtures/bravo/bravo-fixtures.yml)
- [Quality Gate Rules](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/21-quality-gate-rules.md), [Rendered DOM fixture contract](https://github.com/daniel-yfc/stash-scarpers/blob/4bbafca9cf7b5d67117ac41136e74a303c28e4f4/docs/51-rendered-dom-fixture-testing.md)
- [Existing upstream queryURL missing-field issue #4415](https://github.com/stashapp/stash/issues/4415)

Read workbench docs from the linked `docs/workbench-stash-e2e-20261031` branch until PR #92 is merged. Implementation branch base is **main**, not the docs branch.

## Facts to preserve

`BRAVO.yml` currently declares `sceneByURL` routes for **`/clips/` only**, yet Title/Code/Image selectors are annotated as designed/validated on DVD pages. The `/dvds/` fixtures in `BRAVO.test.yaml` are **not** proof that DVD routing exists. The unmatched-URL Stash `index out of range` panic is an **upstream** concern, not a Clips selector bug. Muse QA v2 observed `/clips/284` with Details/Tags/Image but no meaningful Title/Code. Empty scene Title in the direct `sceneByFragment` can send literal `{title}` and produce `clips/%7Btitle%7D` false metadata.

## File ownership and scope

May change only `scrapers/BRAVO.yml` (Clips/Fragment), `scrapers/BRAVO.test.yaml`, `tests/fixtures/bravo/` and new dedicated BRAVO tests. **Do not** edit `Justice01.yml`, `KOShop.yml`, `CK-Download.yml`, `ACCEED.yml`, global Stash/CDP config, workflows, schema, docs index or workbench. Do not add a fabricated `sceneByName` endpoint, change the DVD support policy, or make general-purpose parser changes.

## Detailed implementation

1. Inspect **completed, authorized, sanitized** Wix Clips DOM for `https://www.bravo-japan.com/clips/284` and `/clips/282`. Distinguish rendered DOM from raw HTTP response and cite the actual source of Title, Clip Code, Details, Tags and Image.
2. Route existing `/clips/` patterns to a clearly Clips-specific `clipSceneScraper`; implement its Title/Code with evidence-based selectors. Preserve reliable Details/Tags mapping. Identify valid cover rather than accepting a small Wix placeholder GIF. Source-absent Date/Studio must remain absent: **never fabricate fields just to make tests nonempty**.
3. Remove the unreliable direct `sceneByFragment` declaration. Keep `sceneByQueryFragment` using `queryURL: "{url}"`, which is required by local quality policy. Because BRAVO has no `sceneByName`, do **not** claim a BRAVO Search→QueryFragment run that is impossible in current modes.
4. Build red-before / green-after regression for `clips/284` and second Clips page `clips/282`, with field-level expected values, negative/error page and a missing-title Scene. Removing direct Fragment must prevent BRAVO from producing `clips/%7Btitle%7D`; it does not imply fixing Stash globally.
5. Execute `npm ci`, `node validator/index.mjs -a --ci`, `bash tools/validate-all.sh`, `python tools/run_fixture_manifests.py`, `python -m pytest tools/tests/ -v` and `python tools/scan_session_material.py`; record actual results.
6. Build and verify an exact branch candidate source ZIP (full Git history): `python tools/build_scraper_source.py --output <isolated-preview-dir>` and `--verify-only`. Publish only a **Draft PR**, pinning BRAVO package revision, ZIP SHA-256 and exact head.
7. Gate B is run **only by authorized independent QA** under exclusive stash-test lease after M0. It must verify the candidate BRAVO revision installed and re-run `clips/284`, `clips/282` and an empty-title direct-Fragment negative case. Without this evidence mark `NOT_RUN`, never `FIXED_VERIFIED`.
8. `/dvds/234` and `/dvds/084` are reserved for Wave 2E. Do not attempt to "fix" upstream unmatched-URL panic by further narrowing the already Clips-only route. No production access, secret material or merges.

## Final report contract

`BRANCH, PR_URL, HEAD_SHA, BRAVO_CLIPS_FIELDS_EXPECTED_VS_OBSERVED, DIRECT_FRAGMENT_REMOVAL_EVIDENCE, CHANGED_FILES, OFFLINE_RED_GREEN, GATE_A/B/C, PACKAGE_VERSION_SHA256, DVD_UPSTREAM_EXCLUSIONS, ROLLBACK, MERGE_STATUS=NOT_AUTHORIZED`.
