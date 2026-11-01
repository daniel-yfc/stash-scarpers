---
doc_id: DOC-E2E-61
title: BRAVO DVD Wave 2E Detailed Implementation Plan
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
last_verified: "2026-11-02"
authority: informational
routing:
  intents:
    - bravo
    - dvd-routing
    - wave-2e
    - implementation
    - parallel-workstreams
    - live-verification
---

# Wave 2E — BRAVO DVD Detailed Implementation Plan

**Tracking:** STASH-E2E-02a / proposed implementation branch `feat/e2e-bravo-dvds`.  
**Dependencies:** [Wave 1B Clips PR #93](https://github.com/daniel-yfc/stash-scarpers/pull/93), [planning PR #98](https://github.com/daniel-yfc/stash-scarpers/pull/98).  
**Upstream issue:** [STASH-E2E-02 / WS-D local issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97); see [separate upstream-preparation document](62-stash-panic-upstream-report.md).  
**Status (2026-11-02):** `PLANNED / NOT_IMPLEMENTED / NOT_LIVE_VERIFIED`. All agent assignments, work branches, acceptance conditions, and commands below are **proposals**, not claims that work was performed or agents were actually assigned. PR #93 and #98 were Draft at the time of this review. **Do not merge or deploy without controller/maintainer authorization.**

## 1. Objective, constraints, and failure-first decision

Restore **valid BRAVO DVD URL scraping** using a dedicated `dvdSceneScraper`, while preserving the separately verified `clipSceneScraper`. Success means correct routing **and source-grounded metadata** in an actual Stash instance, not merely the absence of a panic.

| Route family | Required `sceneByURL` handler | Scope |
| --- | --- | --- |
| `/clips/` | `clipSceneScraper` | Preserve accepted Wave 1B behavior |
| `/dvds/` | `dvdSceneScraper` | New Wave 2E URL-mode support |
| Unmatched URLs | No BRAVO handler | **Upstream Stash error handling remains WS-D** |

The original `main@4bbafca9cf7b5d67117ac41136e74a303c28e4f4` BRAVO `sceneByURL` matched `/clips/` only, although `BRAVO.test.yaml` included DVD URLs. In the original QA, `/dvds/234` and `/dvds/084` triggered the same Stash `index out of range [0] with length 0` error as unrelated unmatched URLs. The 2026-11-01 QA handoff reported **5/5 reproductions** on Stash `v0.31.1-182-g9e9ad972`, with actual GraphQL responses and in-app logs preserved, but **no goroutine stack**. Its reported source analysis locates an empty-result indexing path; the private evidence bundle was **not re-inspected as part of this documentation change**. Never equate DVD-route coverage with a core Stash bug fix.

**In scope:** a second `sceneByURL` route, DVD-only XPath mapping, sanitized DVD fixtures, independent routing tests, Clips regressions, offline/CI/live QA, package provenance, rollback and document updates.

**Out of scope:** changes to Stash core, arbitrary URL panic workarounds, fabricated Search/Group/Fragment support, unverified fields, changes to production, or altering historical fixture evidence to make gates pass.

**Fail-closed principle:** An empty/wrong title, wrong canonical URL, unrelated cover, challenge/login page presented as a work, or a misleading cross-mode QueryFragment result is **not a successful scrape**. Missing source fields remain missing. A valid DVD product may not map one-to-one to a Stash Scene; document product/scene/group semantics if encountered rather than silently inventing an entity model.

### Design sketch — not deployable YAML

~~~yaml
sceneByURL:
  - action: scrapeXPath
    url:
      - "bravo-japan.com/clips/"
      - "www.bravo-japan.com/clips/"
    scraper: clipSceneScraper
  - action: scrapeXPath
    url:
      - "bravo-japan.com/dvds/"
      - "www.bravo-japan.com/dvds/"
    scraper: dvdSceneScraper

xPathScrapers:
  clipSceneScraper:
    scene: {} # Preserve accepted Wave 1B selectors; sketch only.
  dvdSceneScraper:
    scene: {} # Fill exclusively from verified DVD rendered DOM.
~~~

**Runtime-specific warning:** For the tested upstream Stash build, `ByURLDefinition.matchesURL` uses `strings.Contains`, **not** strict host/path matching or regex. The overlapping substring patterns and route order require deterministic positive **and negative** tests; the YAML patterns alone cannot guarantee host authenticity. Test the effective Stash route, not just the presence of substrings in YAML.

**QueryFragment warning:** The Wave 1B `sceneByQueryFragment` references `clipSceneScraper` via `queryURL: "{url}"`. Adding DVD `sceneByURL` does **not** prove that DVD QueryFragment selects `dvdSceneScraper`. Preserve the existing Clips contract by default; test DVD QueryFragment explicitly. Any plausible but incorrect DVD metadata from the Clips XPath is a release blocker until independently addressed or explicitly re-scoped by the controller.

## 2. Workstreams and parallel assignment

### 2.1 Workstream ownership

| Workstream | Proposed agent / accountable role | Tasks | Deliverables | Can start in parallel? |
| --- | --- | --- | --- | --- |
| **WS-2E-00** | **Agent D — Baseline & CI** | PR #93 Gate B/C, accepted Clips baseline, package/lease authorization | `baseline-lock.md`, accepted HEAD SHA, environment prerequisites | **Yes** |
| **WS-2E-10** | **Agent A — DVD Research** | DVD rendered DOM, field provenance, negative-page classification | sanitized evidence + field matrix + expected-value contract | **Yes** |
| **WS-2E-20** | **Agent B — Routing & Tests** | Stash matching semantics, route-selection unit tests, QueryFragment hazard | isolated route-test proposal/commit + known limitations | **Yes**; tests may initially be red |
| **WS-2E-40 (scaffold)** | **Agent C — Fixture Engineering** | separate DVD fixture manifest, failure cases, test skeleton, archived-evidence protection | new fixture/test files; final expected values await Agent A | **Yes**, with evidence dependency |
| **WS-D** | **Agent E — Upstream Investigation** | independently track unmatched-URL panic, review #7275 relationship, prepare sanitized report | issue #97 handoff; independent upstream report draft | **Yes**; never blocks DVD research |
| **WS-2E-30 + integration** | **Agent F — Sole YAML Integrator** | DVD XPath, second URL route, merge handoffs and repair Clips tests | single integration branch + coherent candidate | **Design review now; YAML edit only after G0/G1** |
| **WS-2E-50** | Agent F with test/CI reviewers | exact-head offline validation, package integrity | Gate A evidence and SHA-256 | After integration |
| **WS-2E-60** | **Independent authorized QA** (not the developer) | exclusive `stash-test` live verification | Gate B verdict and sanitized request/response | After Gate A and environment lease |
| **WS-2E-70** | Controller / Maintainer | exact-head CI/CodeQL, docs, rollback, merge decision | Draft PR and Gate C/release record | After QA (CI may run earlier but final verdict is exact-head) |

**Only Agent F may modify `scrapers/BRAVO.yml` for Wave 2E.** Agents A–E must not independently change or merge that runtime YAML. Ownership is a conflict-prevention rule, not proof that an agent has been assigned.

### 2.2 Parallel DAG and stop points

~~~mermaid
flowchart TD
    A["Agent A: DVD DOM / field evidence"]
    B["Agent B: route & QueryFragment tests"]
    C["Agent C: fixture scaffolding"]
    D["Agent D: PR #93 Gate B/C & baseline"]
    E["Agent E: upstream issue #97"]
    F["Agent F: single-writer DVD integration"]
    GA["Gate A: offline + package integrity"]
    QB["Gate B: exclusive stash-test E2E"]
    GC["Gate C: exact-head CI / maintainer decision"]
    A --> F
    B --> F
    C --> F
    D --> F
    F --> GA
    GA --> QB
    QB --> GC
    E -. "tracked separately; not a DVD merge gate" .-> GC
~~~

- **Immediate parallel batch:** A, B, C, D, E. F may prepare interface contracts and review evidence, but must not treat an unaccepted Clips branch as a finalized implementation base.
- **Evidence dependency:** C may write fixture harnesses and failure classifications without A; C must not create guessed DVD expected values. A signs off source-grounded values before C finalizes assertions.
- **Baseline dependency:** D obtains independent PR #93 Gate B and exact-head CI/Gate C; only after the user's merge authorization can F rebase or start its production YAML modifications on the accepted `main`. If the baseline remains blocked, F records `BLOCKED_BASELINE`, not a fabricated `PASS`.
- **Integration dependency:** F merges/adapts A/B/C handoffs; then runs Gate A. No external QA live pass is inferred from a local fixture success.
- **Live instance dependency:** One authorized QA lease at a time on `stash-test`. Do **not** parallelize live QA, CDP configuration changes, install/reload activity, or stateful Stash operations on the same instance.
- **Independent upstream lane:** E can prepare/report findings to local #97; no Stash upstream issue or PR submission without explicit authorization. The reported `REPRODUCED_NO_STACK` outcome is not `UPSTREAM_FIXED`.

## 3. Branching, file ownership, and collision prevention

### 3.1 Proposed branches and allowed writes

| Agent / lane | Proposed branch or destination | Exclusive write scope | Explicitly forbidden |
| --- | --- | --- | --- |
| A | `research/e2e-bravo-dvd-dom` or restricted evidence workspace | New sanitized DVD research notes, mapping records; private raw DOM stays private | `BRAVO.yml`, historical evidence |
| B | `test/e2e-bravo-dvd-routing` | New route/QueryFragment tests, research notes; no shared Clips test edits | Production YAML; silent runtime behavior changes |
| C | `test/e2e-bravo-dvd-fixtures` | New `bravo-dvds-fixtures.yml` and new sanitized DVD fixture/test files | Overwrite historical `bravo-fixtures.yml`; invent expected data |
| D | Existing PR #93 and QA handoff | Review/QA outputs only unless controller explicitly authorizes a separate PR #93 correction | Merge PR #93 or change Wave 2E YAML |
| E | Local issue #97 / separate upstream draft | Sanitized issue summary and evidence references | Commit private logs; submit upstream issue |
| **F** | **`feat/e2e-bravo-dvds`** | **`scrapers/BRAVO.yml`**, `scrapers/BRAVO.test.yaml`, coordinated edits to `tools/tests/test_bravo_clips.py`, integrated B/C assets | Bypass baseline, rewrite evidence or merge into `main` |

Branch names are **proposed**; do not create duplicate branches or a PR unless the controller assigns execution. A/B/C branches are work products, not automatic `main` PRs. Prefer one final implementation PR; split a generic fixture-runner redesign into its own reviewed PR if it has broad repository impact.

### 3.2 Hard conflict-control rules

1. **Single writer per production file:** F alone edits `scrapers/BRAVO.yml`. A/B/C contribute reviews or isolated tests; never independent competing YAML commits.
2. **Single writer for existing Clips tests:** F owns any modification to `tools/tests/test_bravo_clips.py`, after importing B's new tests. Its current `len(sceneByURL) == 1` assertion must become an exact two-family routing contract, **not** be deleted.
3. **Evidence immutability:** Preserve `tests/fixtures/bravo/bravo-fixtures.yml` byte-for-byte. Its recorded historical SHA-256 is `be1885d2097683e8c4ae5f2440120e8bd7945ac16f62c1910ac87e5d009d39b2`, pinned by archived evidence. Do not update the archived evidence record or digest to obtain a PASS.
4. **No simultaneous shared-instance access:** QA, CDP setup, installed-package changes and reproduction tests require an exclusive `stash-test` lease, M0 preflight, written permission and rollback plan. Production remains out of scope.
5. **No unreviewed cross-mode changes:** A proposed QueryFragment fix belongs in a separately justified subdecision, with Clips regression tests. Do not invent a second unsupported query-fragment route or silently remove the current one.
6. **Evidence-based fields only:** A provides expected values with source proof; C/F must reject fixture-local placeholders as live metadata and must not infer Date/Studio/Image/Code.
7. **Immutable accepted baseline:** Work must cite a `BASE_SHA`, and integration must record imported commit IDs. If PR #93 changes, F rechecks dependencies and reruns affected tests; do not assume older SHA/package evidence remains valid.
8. **No hidden scope creep:** Changes to `validator/`, `tools/verify-scraper-mappings.mjs` or general CI workflows require a separate explicit reviewer decision; no broad test-runner change to force green.
9. **No silent failure promotion:** `BLOCKED`, `NOT_RUN` and `UNVERIFIED` are not `PASS`. A new fixture with only structural XPath hits is not a live parser acceptance.
10. **No automatic release:** Each agent may hand off commits and evidence; only the controller/maintainer can authorize PR merge, source publication or upstream issue filing.

### 3.3 Handoff / integration protocol

1. A/B/C record `BASE_SHA`, changed files, commit SHA, evidence, tests and blockers in their standardized handoff (section 4).
2. F checks each handoff for shared-file violations, incompatible assumptions, source provenance and evidence digest drift.
3. F integrates isolated commits sequentially (cherry-pick or reviewed equivalent), records every source commit, and resolves conflicts without silently discarding assertions.
4. Where B/C tests are written before the YAML exists, label `EXPECTED_RED` and keep them off the accepted green baseline until F integrates the complete feature.
5. F re-runs **all** relevant tests after any conflict resolution, rebase or additional YAML/fixture change; earlier gate results are historical.
6. Controller evaluates exact-head evidence. A, B, C, D or E completion is not a substitute for F's integration, Gate A, independent Gate B or Gate C.

## 4. Mandatory agent delivery contract

Each agent must submit a structured report, even when blocked. Use the following keys; do not substitute a one-line “done” message:

~~~yaml
WORKSTREAM_ID: WS-2E-XX
AGENT_ROLE: Agent A/B/C/D/E/F
ASSIGNMENT_STATUS: ASSIGNED | NOT_ASSIGNED
BASE_SHA: "<exact base commit>"
BRANCH: "<branch or N/A>"
HEAD_SHA: "<exact commit or NOT_COMMITTED>"
CHANGED_FILES: []  # every changed/new path; "none" if read-only
DELIVERABLES: []   # documents, test fixtures, branches or review links
EVIDENCE: []       # IDs/paths + captured_at + provenance + privacy class
TEST_RESULTS: []   # command / version / exact HEAD / PASS, FAIL, BLOCKED, NOT_RUN
KNOWN_LIMITATIONS: []
DEPENDENCIES: []   # other workstream outputs and current readiness
RISKS_AND_DECISIONS: [] # facts vs inferences; deviations needing approval
HANDOFF_STATUS: READY | BLOCKED | CHANGES_REQUESTED
~~~

**READY acceptance:** scope respected; actual files and SHA identified; source assertions trace to evidence; required tests executed or transparently marked `NOT_RUN`; no leaked secrets; no unresolved conflicting edit; integration owner can reproduce the handoff. A research-only handoff may be `READY_FOR_INTEGRATION` without claiming live/runtime verification.

**BLOCKED:** name the exact missing upstream/fixture/environment/permission dependency and a minimal unblock action. **CHANGES_REQUESTED:** list each failed assertion and corrective task. Report expected versus observed outcomes, not just test counts. Private raw evidence must stay in restricted storage; public GitHub comments/docs may link only to sanitized material.

## 5. Detailed implementation tasks with measurable exits

### WS-2E-00 — Baseline, scope freeze and test authorization (Agent D)

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 00-01 | Verify PR #93 independent Clips live Gate B (including poster / title-less limitations) | Independent QA verdict with exact installed package version |
| 00-02 | Verify PR #93 exact-head CI/CodeQL and maintainer merge decision | CI status, approver, accepted `main` SHA |
| 00-03 | Record PR #98 planning status and source baseline | Baseline/decision log; no implied merge |
| 00-04 | Freeze Clips behavior, archived fixture SHA and candidate source package identity | Baseline regression snapshot + SHA |
| 00-05 | Confirm `stash-test` M0, exclusive lease, CDP, GraphQL and change/rollback authority | Explicit preflight result before any live test |

**Stop:** If PR #93 is unaccepted or environment permission is absent, do not modify accepted production YAML or run unauthorized E2E. **Exit:** `G0_BASELINE_LOCKED`.

### WS-2E-10 — DVD DOM capture and field provenance (Agent A)

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 10-01 | Capture complete sanitized rendered DOM for `/dvds/234` and `/dvds/084` | Provenance: URL, timestamp, actual page status, CDP state, canonical, SHA-256 |
| 10-02 | Cross-check historical `dvd-281.html` / `dvd-046.html`; source pages `/dvds/281` / `/dvds/046` if reachable | Distinguish historical fixture from freshly verified live page |
| 10-03 | Create per-URL **Title, Code, URLs, Details, Image, Date, Studio, Duration, Tags** field matrix | Actual source node/value, cardinality, `VERIFIED` / `SOURCE_FIELD_ABSENT` / `UNVERIFIED` |
| 10-04 | Capture a source field-missing page and representative challenge/login/not-found pages | Page classification; no success expectations on failure pages |
| 10-05 | Independently validate product identity, leading-zero codes such as `046`, work-vs-scene semantics and image provenance | Human-reviewed expected values tied to evidence IDs |

**Do not** use a global first `h1`, unrelated Wix component, arbitrary `img`, or URL sequence number as a guessed Title/Code. **Stop:** fewer than two trustworthy completed DVD DOMs or missing core provenance. **Exit:** `G1_DOM_EVIDENCE_ACCEPTED`.

### WS-2E-20 — Routing and QueryFragment safeguards (Agent B)

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 20-01 | Verify applicable Stash `matchesURL` semantics and route priority against the target build | Source/build reference and test design |
| 20-02 | Create deterministic tests: `/dvds/234`, `/dvds/084` → DVD; `/clips/284`, `/clips/282` → Clips | Exact handler selected, not merely any pattern match |
| 20-03 | Test non-target host, path, query embedding, root/category URL, overlap and route order | Negative matrix identifying false matches and residual matching limits |
| 20-04 | Inspect `sceneByQueryFragment` (Wave 1B maps `{url}` to Clips handler) with DVD input | Explicit `PASS_SAFE` / `FALSE_METADATA_BLOCKER` / `NOT_RUN` outcome |
| 20-05 | Assess whether routing tests require a dedicated utility | Prefer isolated route tests; common harness changes require approval |

**Known harness limitation:** `tools/verify-scraper-mappings.mjs` can choose a field by explicitly named scraper while `routeThrough` only checks a URL against any declared pattern. This does **not** itself prove effective routing; create a separate matching/priority test and verify in Stash Gate B. **Exit:** `ROUTING_CONTRACT_READY`.

### WS-2E-30 — Dedicated DVD scraper and integration (Agent F)

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 30-01 | Import accepted Clips baseline and A/B/C handoffs; record source commit SHAs | Audit trail and clean integration base |
| 30-02 | Add DVD `sceneByURL` route → `dvdSceneScraper` without modifying existing Clips field mapping | Schema-valid second handler |
| 30-03 | Implement verified DVD Title/URLs and source-supported Code, Details, Image, and optional fields | Exact expected/actual field comparison on at least two DVD cases |
| 30-04 | Avoid fragile globally-scoped heading and image selectors; guard false metadata | Bad-page, wrong canonical, wrong image regressions |
| 30-05 | Keep `sceneByFragment` absent and protect existing Clips `sceneByQueryFragment` contract | No fabricated URL or unapproved multi-handler design |
| 30-06 | Integrate sidecar, new DVD fixtures, route tests and Clips-test updates | All affected tests run after integration |

**Stop:** missing title, wrong product canonical, image logo, misleading QueryFragment extraction or Clips regression. **Exit:** `DVD_CANDIDATE_INTEGRATED` (not live-verified).

### WS-2E-40 — Fixture engineering and regression (Agent C; integrated by F)

Create `tests/fixtures/bravo/bravo-dvds-fixtures.yml` (new), sanitized DVD HTML snapshots, and `tools/tests/test_bravo_dvds.py` (new). The `mappedExpect` entries for DVD must explicitly include `scraper: dvdSceneScraper` because multi-route `sceneByURL` is otherwise ambiguous to the current fixture helper.

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 40-01 | Add two completed DVD cases using A's verified Title/URL/Code evidence | Field-level `mappedExpect`; accurate leading-zero strings |
| 40-02 | Add absent-field and Cloudflare/error-page negative cases | Missing field stays absent; no bogus metadata |
| 40-03 | Add deterministic route-selection/priority regression | False handler and overlap tests fail correctly |
| 40-04 | Update `test_bravo_clips.py` via F: replace `len(routes) == 1` with exact Clips+DVD routing assertions | Clips regression preserved; not a deleted assertion |
| 40-05 | Verify DVD QueryFragment safety and preserved Clips negative/blank-title cases | No wrong-but-plausible metadata accepted |
| 40-06 | Pin historical fixture digest and evidence contract | Historical `bravo-fixtures.yml` unchanged |

Maintain `bravo-clips-fixtures.yml` separately; fixture-local `example.invalid` images are test controls, **not real live covers**. **Exit:** `REGRESSION_SUITE_READY`.

### WS-2E-50 — Gate A: offline checks and package provenance (Agent F + reviewer)

Run on the **exact integrated HEAD**; record command, exit code, output and SHA. At minimum:

~~~bash
npm ci
node validator/index.mjs -a --ci
npm run validate-sort
bash tools/validate-all.sh
python -m pytest tools/tests/ -v
python tools/run_fixture_manifests.py
python tools/check_evidence_contract.py
python tools/check_docs_index.py
python tools/check_scraper_semantics.py
python tools/scan_session_material.py
npm run format:check
~~~

Build the source into an **isolated output directory** from a complete Git history, then run `python tools/build_scraper_source.py --output <candidate-dir> --verify-only` on that **same directory** (replace `<candidate-dir>` with its actual path). Record generated BRAVO package version, SHA-256, and package contents.

Distinguish pre-existing repository format warnings from new violations; do not use warnings as grounds to skip required checks. A validator pass or fixture pass does **not** establish runtime loading or Stash E2E correctness. **Exit:** `GATE_A_PASS` or evidence-backed failure/blocker.

### WS-2E-60 — Gate B: independent `stash-test` GraphQL E2E

**Executor:** authorized independent QA only; `stash-test` exclusive lease after M0. Confirm installed candidate revision, source ZIP SHA-256, CDP availability, scraper inventory, and GraphQL schema before testing.

| Case | URL / mode | Required outcome |
| --- | --- | --- |
| DVD-01 | `/dvds/234` URL | Correct handler, source-grounded Title and canonical, Code if present |
| DVD-02 | `/dvds/084` URL | Same; no title/code from a neighboring work |
| DVD-03/04 | `/dvds/281` / `/dvds/046` if available | Compare historical identity; preserve leading-zero Code |
| CLIP-01/02 | `/clips/284` / `/clips/282` URL | Regression: accepted Clips Title/Code/URL and documented Image behavior |
| NEG-01 | DVD missing Title or field | Do not mark a partial result as fully successful |
| NEG-02 | Challenge/login/not-found or wrong canonical | No unrelated or false success metadata |
| NEG-03 | DVD input via QueryFragment | No plausible but incorrect Clips-derived DVD metadata |
| CONTROL-01 | Unmatched example.com URL | Track separately under #97; do not use as DVD PASS/FAIL |

The **minimum positive exit** is a fully source-validated Title + correct canonical URL on both primary DVD URLs; validate Code wherever explicitly published, and classify absent/unverified fields transparently. Record every expected/actual field, GraphQL request/response, observed route behavior, Stash and scraper versions, UTC/local times, logs, privacy status and package digest. Never classify blocked site/CDP cases as `PASS`. **Exit:** `GATE_B_PASS` with independent evidence; otherwise `FAIL` / `BLOCKED_SITE` / `BLOCKED_ENVIRONMENT` / `NOT_RUN`.

### WS-2E-70 — Gate C, release decision, docs and rollback (Controller)

| Task ID | Action | Acceptance evidence |
| --- | --- | --- |
| 70-01 | Open one Draft implementation PR to `main` (after accepted baseline) | Limited BRAVO/fixture/test changes, reviewed scope |
| 70-02 | Confirm exact-head CI, CodeQL/security, evidence and documentation checks | Exact commit/build references |
| 70-03 | Update `BRAVO.test.yaml` and `docs/60-live-test-status.md` only with real results | Accurate `FIXED_VERIFIED` / `UNVERIFIED` labels |
| 70-04 | Record installable BRAVO ZIP version/SHA and rollback to accepted Clips package | Reversible release record; no database migration assumed |
| 70-05 | Request explicit controller/maintainer merge authorization | No automatic merge or production deployment |

Generic testing/tooling refactors should use a separate reviewed change where possible. **Exit:** `GATE_C_ACCEPTED` + authorized merge; production readiness is a separate deployment gate.

### WS-D — Upstream panic investigation (Agent E, independent lane)

- Reference [issue #97](https://github.com/daniel-yfc/stash-scarpers/issues/97) and [upstream preparation doc](62-stash-panic-upstream-report.md).
- Prior QA handoff: `REPRODUCED_NO_STACK`, 5/5 unmatched URL cases, matched Clips control passed, Stash `v0.31.1-182-g9e9ad972`, source-level empty-result/indexing finding. Preserve the **lack of a captured goroutine stack** in public claims.
- Inspect [upstream issue #7275](https://github.com/stashapp/stash/issues/7275) (closed, typed-nil/empty marshalling) and its closure/fix history before proposing a duplicate or new issue. Do not assume #7275 fully fixed the tested build.
- Prepare a privacy-reviewed English upstream report; local tracking and actual upstream submission require their own authorization.
- **Not a prerequisite to Wave 2E routing success; never close #97 merely because DVD URLs cease to panic.**

## 6. Assume-failed pre-mortem and mitigations

| Likely failure | Early signal | Required mitigation |
| --- | --- | --- |
| “URL route added” but wrong handler chosen | First-match route test fails | Deterministic Stash-compatible priority test + live verification |
| Overbroad substring matches malicious/unrelated host or query text | Negative URL matrix fails | Document upstream matching limitation; don't claim host-boundary safety |
| DVD selectors target nearby heading/ID | Title/Code mismatch across two DVDs | Localize XPath and verify representative expected values |
| URL number mistaken for verified Code | `046` becomes `46` or invented Code | Preserve source strings; no URL-only assumptions |
| Logo/ad/other work returned as Image | Image provenance mismatch | Product-specific Image or empty |
| QueryFragment invokes Clips selector for DVD | Plausible false metadata on DVD input | **Block release**, require scoped design/decision and independent regression |
| Challenge/login page appears successful | Title matches site brand or error page | Failure-page classification; never mark PASS |
| Evidence CI breaks after fixture edit | Archived digest mismatch | New DVD manifest only; pin historical SHA |
| Offline PASS but Stash still runs old source | Package/version mismatch | Record and inspect installed exact ZIP SHA / version |
| Parallel agents overwrite changes | Same-file commit conflict or lost test | File owner F; sequential integration + rerun gates |
| Independent QA collisions on Stash | Different scraper/CDP instance revision | Exclusive lease, M0 preflight, restore authorized test config |
| DVD item actually maps to several scenes | Metadata accurate but wrong entity semantics | Document modeling choice and avoid fabricated Scene/Group relations |

**Priority of risk control:** wrong-but-plausible metadata > missing optional field > feature breadth. A partial extraction is not a pass simply because the API returned an object.

## 7. Release gates and stop rules

| Gate | Condition | Stop condition |
| --- | --- | --- |
| **G0 — Baseline** | PR #93 Clips Gate B/C and user-authorized merge; accepted SHA fixed | Unaccepted Clips baseline or unauthorized instance |
| **G1 — DOM evidence** | At least two trustworthy current DVD completed pages and field matrix | Guessing XPath from historical or challenge HTML |
| **G2 — Integration** | Single-writer F merges correct route/field/fixture tests | Wrong handler, false metadata or historical digest changed |
| **Gate A — Offline** | Official validator, repository checks, tests, security, package integrity | Any required new failure or unverifiable source package |
| **Gate B — Independent live QA** | Exact package on exclusive `stash-test`; primary DVD + Clips controls correct | Unverified fields called PASS; bad QueryFragment metadata |
| **Gate C — CI / release review** | Exact-head checks, evidence, rollback, maintainer authorization | Draft still unauthorized or CI unresolved |
| **Production gate** | Separately authorized deployment and auth/CDP readiness | Treating test E2E as production validation |

Rebases or changes to `BRAVO.yml`, fixture manifests or candidate package **invalidate older exact-head gate results**. Re-run affected checks and update handoff SHA. An unmet dependency or missing evidence is `BLOCKED`/`NOT_RUN`, never `PASS`.

## 8. Definition of Done and final handoff

- [ ] PR #93 accepted and merged under explicit authorization; Wave 2E uses its exact baseline.
- [ ] `dvdSceneScraper` is the only DVD URL handler, with `clipSceneScraper` preserved.
- [ ] DVD 234 and 084 independently live-verified with correct Title + canonical URL and source-supported Code.
- [ ] Representative historical DVD cases reviewed or explicitly classified as unavailable.
- [ ] No known wrong Title/Code/URL/Image or challenge-page false positive.
- [ ] QueryFragment DVD negative case cannot silently return plausible wrong metadata.
- [ ] Dedicated DVD fixtures and true effective-route tests pass; Clips regression tests are preserved and updated.
- [ ] Archived `bravo-fixtures.yml` and evidence digest remain unchanged.
- [ ] Gate A, independent Gate B and exact-head Gate C evidence are complete.
- [ ] Candidate package SHA-256, rollback, documentation, reviewer decision and source provenance recorded.
- [ ] Controller explicitly authorizes any merge; issue #97 remains independently tracked.

**Final verdict required:** `DVD_URL_SCRAPING_FIXED_VERIFIED` **only** after the above evidence; `PANIC_NOT_OBSERVED`, `YAML_CHANGED`, or `FIXTURES_PASS` alone are insufficient.

**Next actions:** assign Agents A–E as proposed (not yet launched); have F own integration specification now but defer production YAML modifications until G0/G1. A/B/C deliver isolated, traceable handoffs; authorized independent QA alone performs Gate B on `stash-test`.
