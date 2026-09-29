---
doc_id: DOC-GOV-00
title: Repository Documentation Architecture
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - documentation
  - repository
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - documentation-policy
    - naming
    - indexing
    - formatter-policy
---

# Repository Documentation Architecture

## Purpose

This document is the canonical policy for repository documentation numbering, naming, metadata, indexing, routing, and formatting. It defines the boundary between repository-level documentation and the `stash-scraper-builder` skill without duplicating rules in both places.

## Ownership model

| Layer | Owns | Must not own |
|---|---|---|
| Root `README.md` | Project purpose, quick start, canonical commands, directory map | Detailed scraper selector or runtime semantics |
| `AGENTS.md` | Repository-wide agent constraints, safety, and routing pointers | A second copy of detailed repository or skill rules |
| `CLAUDE.md` | Claude-specific behavior that differs from repository-wide rules | A second copy of `AGENTS.md` or skill references |
| `CONTRIBUTING.md` | Human contribution and review workflow | Runtime implementation details |
| `templates/README.md` | Template inventory, pairing, provenance, naming, copy workflow | Full scraper authoring manual |
| `docs/` | Repository architecture, CI, testing, production gates, maintenance, and status | Per-field scraper rules |
| `skills/stash-scraper-builder/SKILL.md` | Skill purpose, trigger conditions, output contract, authoring workflow | Repository administration and CI policy |
| `skills/stash-scraper-builder/references/` | Specialized XPath, JSON, script, CDP, date, failure, and validation guidance | Project-wide contribution policy |
| `validator/` | Executable validation behavior and schema | Prose-only source of truth |
| `tools/` | Inspection, validation, documentation, and live-scrutiny utilities | Canonical schema definitions |

## Document identity and numbering

Every indexed document has a stable `doc_id`. The ID is independent of the filename and must not be reused after deprecation.

| Layer | Format | Example |
|---|---|---|
| Repository docs | `DOC-<DOMAIN>-<NN>` | `DOC-QG-21` |
| Skill references | `REF-<DOMAIN>-<NN>` | `REF-MODE-40` |
| Templates | `TPL-<DOMAIN>-<NN>` | `TPL-REPORT-71` |
| Status records | `STATUS-<DOMAIN>-<NN>` | `STATUS-LIVE-60` |
| Skill contract | `SKILL-<DOMAIN>-<NN>` | `SKILL-CORE-00` |

Use increments of 10 where practical. Do not renumber documents solely to close gaps. `DOC-TEST-51` is the rendered-DOM fixture document and does not replace `DOC-TEST-50`.

Current repository document IDs are registered in [`index.yml`](index.yml). Existing numbered filenames under `docs/` remain valid for compatibility.

## Naming rules

- New Markdown files use lowercase kebab-case, except fixed entry points such as `README.md` and the existing numbered `docs/` series.
- Scraper and template YAML files use CamelCase names with `.yml`.
- Python implementation files use CamelCase names with `.py` and match their paired YAML/dependency name where applicable.
- Root scraper YAML contains required `name:`; unsupported `documentHeader` and `$vars` are prohibited.
- Dates in metadata and `# Last Updated` markers use ISO `YYYY-MM-DD`.
- Use tables for inventories and ownership; use fenced code blocks for commands and examples.

## Metadata rules

New or materially updated Markdown documents use YAML front matter. Controlled values are `status` (`draft`, `active`, `deprecated`, `archived`), `layer` (`repository`, `skill`, `template`, `status`, `tool`), `authority` (`canonical`, `derived`, `informational`), and `audience` (`agent`, `maintainer`, `contributor`).

When front matter contains `doc_id`, CI requires it to match `docs/index.yml`.

## Indexing rules

- `docs/README.md` is the human-readable index.
- `docs/index.yml` is the machine-readable agent and CI registry.
- Every repository-level Markdown document under `docs/` and every Markdown reference under `skills/stash-scraper-builder/references/` must be indexed.
- Root routing documents, `templates/README.md`, and `validator/README.md` must also be indexed.
- Every indexed path must exist, every `doc_id` must be unique, and routing references must point to registered IDs.
- Run `python tools/check_docs_index.py` after changing documentation paths or metadata.

## Agent routing

1. Repository administration, CI, paths, or contribution: `README.md` → `AGENTS.md` → `docs/README.md` → `docs/index.yml` → the owning repository document.
2. Scraper authoring or debugging: `skills/stash-scraper-builder/SKILL.md` → `references/skill-read-order.md` → the selected specialized reference.
3. Schema or validation questions: official `validator/index.mjs` and official schema first, then repository policy.
4. Live verification: `docs/06_Testing_Guide.md` → `docs/07_Rendered_DOM_Fixture_Testing.md` → `docs/LIVE_TEST_STATUS.md`. `tools/scrutiny.js` is raw HTTP plus JSDOM, not rendered-DOM or live Stash/CDP verification.
5. Authentication, cookies, or private variants: the skill secrets reference, then `scrapers/private/`.

If documentation conflicts, resolve in this order: official CommunityScrapers schema/validator, executable repository tools, canonical repository docs, skill references, examples.

## Formatter policy

Prettier is the repository formatter for Markdown, YAML, JSON, and JavaScript. The executable rules live in `.prettierrc.yml` and `.prettierignore`; this document owns only the policy.

```bash
npm run format
npm run format:check
```

- Run formatting before validation, never as a replacement for validation.
- Preserve YAML comments such as `# UNVERIFIED`.
- Do not use formatting to reorder scraper keys or URL arrays.
- Continue enforcing URL ordering with `npm run validate-sort`.
- Do not auto-translate or normalize scraped-value examples.
- Upstream schema mirrors and historical evidence files are excluded from formatting.
- Formatter enforcement remains local until an initial repository-wide formatting migration is completed; CI does not currently fail on pre-existing formatting drift.

## Canonical command policy

- `npm run validate` — validate all scrapers.
- `npm run validate-sort` — check URL ordering.
- `python -m pytest tools/tests/` — run Python tests.
- `bash tools/scraper-quality-gate.sh <scraper.yml>` — run the quality gate on one scraper.
- `bash tools/validate-all.sh` — run the quality gate over all scrapers.
- `node tools/scrutiny.js scrapers/<Scraper>.yml --search` — raw HTTP plus JSDOM scrutiny only.
- `node tools/verify-scraper-fixtures.mjs --self-test` — fixture-runner self-test, not site evidence.
- `python tools/parse_committed_yaml.py` — parse committed scraper YAML.
- `python tools/scan_session_material.py` — scan for session-material assignments without printing values.
- `python tools/check_evidence_labels.py` — reject unsupported verification claims.
- `python tools/check_live_cdp_status.py` — fail closed; not a live Stash run.
- `python tools/self_evaluate.py` — run the safeguard controls and print their boundaries.
- `python tools/check_scraper_docs.py` — check documentation examples and contradictions.
- `python tools/check_docs_index.py` — check the documentation registry.
- `npm run format:check` — check formatting locally.

If a command differs between local tooling and documentation, inspect the executable file first and update the documentation rather than inventing an alias.

## Cross-level linking rules

- Link to the owning document instead of restating detailed rules.
- Repository-level docs may summarize a skill rule, but should link to the skill reference for implementation details.
- Skill-level docs may link to repository commands and paths, but should not redefine repository governance.
- Every new documentation file must be listed in `docs/README.md` and `docs/index.yml`.
- Before a release, run link checking, documentation-index checking, and a search for stale command/path names.

## Review checklist

- [ ] Every referenced path exists.
- [ ] Commands match executable files.
- [ ] Naming and date formats are consistent.
- [ ] `doc_id` values are unique and registered.
- [ ] Public/private credential boundaries are clear.
- [ ] Official schema/validator precedence is explicit.
- [ ] Skill references do not contradict repository rules.
- [ ] New docs are indexed and cross-linked.
- [ ] Formatter and validator checks have been run where applicable.
