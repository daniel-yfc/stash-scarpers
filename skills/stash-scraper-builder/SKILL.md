---
name: stash-scraper-builder
description: >-
  Use for creating, revising, reviewing, validating, or debugging StashApp
  CommunityScrapers-style scraper YAML (XPath, JSON, script, or CDP; extraction,
  date parsing, and loader errors). Do not use for generic crawling/YAML,
  Stash-box/Identify, action: stash, skill maintenance, repository administration,
  or CommunityScrapers PR submission.
metadata:
  version: "2026-10-27"
  canonical-schema: "https://github.com/stashapp/CommunityScrapers/blob/master/validator/scraper.schema.json"
---

# Skill: stash-scraper-builder

**Version:** 2026-10-27
**Authority:** The pinned upstream CommunityScrapers validator/schema is normative. The checked-in repository validator is a derived validation implementation and must be named separately. Only Stash runtime evidence establishes loader/live behavior.
**Portability:** Use this `SKILL.md` as the single workflow entry in a repository or standalone. Repository commands and governance apply only in `stash-scarpers`; otherwise use the official upstream validator if available. Do not require repository documents for standalone use.

## Trigger, intent, and authorization (P0)

Read this file first. Run exactly one workflow here; do not load a second route map, router, or an entire reference tree. Classify the requested intent before using tools:

| Intent | Requested job | Write authorization and output |
| --- | --- | --- |
| `CREATE` | Build a new scraper | Author a complete YAML only when requested; writing to disk/Git requires explicit authorization. |
| `REVISE` | Implement a named scraper fix | Return the complete revised YAML; change repository files only when authorized. |
| `VALIDATE_ONLY` | Assess an existing YAML or schema compliance | Read-only report. Never edit, commit, or open a PR by default. |
| `DEBUG` | Diagnose scraping, mapping, loader or parsing failures | Analyze and propose causes/fixes; do not implement unless the user requests a fix, in which case reclassify as `REVISE`. |
| `REVIEW_ONLY` | Review/audit scraper behavior or design | Read-only findings with evidence and limitations; never author changes, commit, or open a PR. |

Exclude generic scraping/YAML, Stash-box/Identify, `action: stash`, skill administration, general GitHub/CI work, and upstream PR submission. If excluded, stop and route the user to the appropriate owning workflow without doing scraper work. If authorization or task intent is unclear, ask for the smallest necessary fact or report `BLOCKED`; never infer permission to write from tool availability.

## Workflow and phase exits

Run P0 through P6 in order. Each exit is a check, not an aspiration. On `FAIL` or `BLOCKED`, stop work dependent on that phase; still deliver a bounded diagnostic in P6. A `NOT_RUN` verification is not a pass. Mark `N/A` only with a reason.

| Phase | Required input / action | Exit check and evidence | Stop / boundary |
| --- | --- | --- | --- |
| **P0 SCOPE_CONFIRMED** | Classify intent, target entity, authorizations, repo versus standalone, and prohibited operations. | Intent and write permission are stated; out-of-scope work excluded. | Ambiguous permission or out-of-scope request: `BLOCKED` or stop. |
| **P1 SOURCE_CLASSIFIED** | Inspect supplied YAML and/or real site URL, response type, access state, language, and known entry points. | Record what was actually observed and the evidence source; separate completed content from login/age/challenge/error pages. | Do not invent URLs, data, page content or successful access. Block any claim requiring unavailable evidence. |
| **P2 MODE_SELECTED** | For CREATE/REVISE choose the least complex supported XPath, JSON, script, or CDP mode; for review, examine existing modes. | Mode and entry points have real site/API or existing-code support, or are explicitly `UNVERIFIED`; read only the corresponding reference. | If an essential endpoint/mode is unsupported, stop dependent authoring; do not synthesize search APIs. `N/A` if no mode selection is requested. |
| **P3 ARTIFACT_READY** | CREATE/REVISE produce one complete YAML (root `name:`) with only supported mappings; REVIEW_ONLY/VALIDATE_ONLY/DEBUG produce findings instead. | Full YAML or clear findings, with assumptions and untested selectors marked; no unauthorized writes. | Structural or scope failure blocks claiming an authored artifact. |
| **P4 SCHEMA_CHECKED** | For an available YAML candidate run parse, the repo validator and, when required/available, a pinned upstream CommunityScrapers validator; run repository policy checks separately. | Record command, schema implementation, exact upstream/ref or repo commit, and `PASS`/`FAIL`/`NOT_RUN`. Report `SCHEMA_REPO_PASS` only for the checked-in validator and `SCHEMA_UPSTREAM_PASS` only for the verified upstream one. | Never call a repo-only check an `official upstream pass`; failure blocks validation promotion. Missing validator is `NOT_RUN`; bundled stub is never authoritative. |
| **P5 RUNTIME_EVIDENCE** | Independently check available fixtures, Stash loader, live search, live detail and CDP; label source/date/runtime. | Each axis independently `PASS`, `FAIL`, `NOT_RUN` or `N/A` with evidence. | Never infer Stash loader/live success from schema, a fixture-runner self-test, Scrutiny/JSDOM, or a green CI run. No production-ready claim without required runtime evidence. |
| **P6 DELIVERY_COMPLETE** | Return output for the classified intent, phase outcomes, unmet checks, next steps, and conditional prerequisites. | The user can distinguish authored, validated, loaded and live-verified claims; no secret or unwarranted certainty. | Report `BLOCKED` or `NOT_RUN` instead of asserting unsupported success. |

Phase outcomes: `PASS` = check satisfied with evidence; `FAIL` = exercised and failed; `BLOCKED` = required input/access unavailable; `NOT_RUN` = not exercised; `N/A` = irrelevant to this intent (include why). A phase cannot be upgraded using a different phase's evidence. Draft delivery is allowed with honest `NOT_RUN` validation/runtime fields; production acceptance is not.

## Runtime selection (P2)

| Observed source | Preferred route | Conditional reference |
| --- | --- | --- |
| Stable accessible HTML | `scrapeXPath` in `xPathScrapers` | `references/xpath-patterns.md` |
| Real JSON response or supported endpoint | `scrapeJson` in `jsonScrapers` | `references/json-patterns.md`; `references/json-examples.md` for a whole-file example |
| Required existing Python implementation | `action: script` | `references/script-actions.md` |
| JavaScript-only or login-gated content | `driver.useCDP: true` after direct access proves insufficient | `references/cdp-workflow.md` and `references/phase0-secrets-policy.md` |

Do not choose CDP merely because it exists. An HTTP/JSDOM inspection does not constitute a browser-rendered DOM or Stash/CDP test. Use `references/out-of-scope.md` only when the scope boundary is disputed.

## Conditional references (one level below SKILL.md)

Load only what the current phase needs; do not pre-read this table or follow references as a second workflow:

| Need | Read only when necessary |
| --- | --- |
| Scraper scaffolding/template | `references/authoring-checklist.md` |
| XPath, JSON, script, CDP | P2 runtime-specific references above |
| Auth, cookies, logged-in sessions | `references/phase0-secrets-policy.md` |
| Dates, regex, post-processing | `references/post-processing.md` |
| Title, studio, performer, group quality | `references/field-quality.md`, then `references/entity-fields.md` if needed |
| Network/multi-site special cases | `references/multi-site-network-scrapers.md` |
| Schema errors, field shapes | `references/schema-checklist.md` |
| Empty fields, nil pointer, loader failures | `references/debugging.md` |
| Schema provenance or compatibility ambiguity | `references/upstream-sources.md` |
| Additional examples or patterns | `references/examples.md`, `references/best-practices.md` |

Evaluation prompts, historical incident reviews, document registries and authoring test packs are maintainer tools, **not required runtime routes**. Repo-only verification and commands belong to `AGENTS.md` / `docs/50-testing-guide.md`. Do not open them merely to decide what scraper phase comes next.

## Non-negotiable constraints

- Keep root `name:`; match the CamelCase filename by repository convention. Do not emit unsupported `documentHeader` or `$vars`.
- Verify each entry point. XPath/JSON fragment modes require the action-appropriate `queryURL`. Never fabricate a name-search endpoint or treat `sceneByFragment` as a nil-pointer workaround.
- Put field mappings under `scene:`, `performer:`, `group:` or `gallery:`; `common:` stores only named string fragments. Keep scraped values in the source language.
- Reject credential-bearing output. No tracked scraper (including `scrapers/private/`) may include active cookies, authentication headers, session values, or browser profile data. Only fully commented placement examples with explicit placeholders are permitted. Personal deployment files and profiles must remain outside this Git working tree. Read the security reference when authentication is involved.
- Preserve `# UNVERIFIED` markers on untested selectors, and do not treat a template, test fixture, schema stub or old incident as present-day site verification.
- The upstream CommunityScrapers schema/validator is normative; record `SCHEMA_VALIDATED` with its precise provenance (repo-derived versus pinned upstream), not a generic unqualified `PASS`. Neither proves Stash runtime load or metadata correctness.

## Output contract (P6)

- `CREATE`: complete YAML, evidence, verification matrix, and only needed script/CDP prerequisites.
- `REVISE`: complete revised YAML, change summary, regression results and unresolved checks.
- `VALIDATE_ONLY`: scope of validation, actual command/output or reason not run, violations, and no edits.
- `DEBUG`: confirmed causes versus hypotheses, reproduction evidence and proposed fixes; no edits unless explicitly requested.
- `REVIEW_ONLY`: read-only findings with severity, file/line provenance, uncertainty and recommendations; report `REPOSITORY_UNCHANGED`.

Match the user's requested language; otherwise explain in English with a short zh-TW orientation. Always preserve source-language scraped values. State repository branch/commit and exact checks when using Git, but do not open an issue/PR or modify Git for REVIEW_ONLY or VALIDATE_ONLY. A complete YAML requirement applies only to CREATE/REVISE, not to reviews or validation reports.

## Exit check

Declare `DELIVERY_COMPLETE` only when P0 intent matches the output, every executed check has evidence, failed/blocked/not-run checks remain visible, and no downstream verification has been promoted without its own evidence. If a user requires production readiness, missing Stash loader/live verification is `BLOCKED`, not a success.
