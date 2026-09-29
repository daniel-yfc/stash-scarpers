---
doc_id: DOC-INDEX-00
title: Documentation Index
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
last_verified: "2026-09-29"
authority: canonical
routing:
  intents:
    - documentation-index
    - repository-workflow
---

# Documentation Index

This directory contains repository-level workflow, architecture, testing, and maintenance documentation.

## Index layers

- [`index.yml`](index.yml) — machine-readable documentation registry for agents and CI.
- [`repository-documentation-architecture.md`](repository-documentation-architecture.md) — canonical numbering, naming, metadata, routing, and formatter policy.

## Ownership

- Repository workflow and project operations belong here and in the root `README.md`.
- Agent-wide constraints belong in `AGENTS.md` and `CLAUDE.md`.
- Scraper authoring rules belong in `skills/stash-scraper-builder/SKILL.md`.
- Specialized scraper behavior belongs in `skills/stash-scraper-builder/references/`.

## Guides

| Document | Purpose |
|---|---|
| [`01_System_Architecture.md`](01_System_Architecture.md) | Repository architecture and verification layers |
| [`02_Quality_Gate_Overview.md`](02_Quality_Gate_Overview.md) | Quality-gate overview |
| [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md) | Canonical quality rules |
| [`04_Production_Gate.md`](04_Production_Gate.md) | Production readiness |
| [`05_CI_Workflows.md`](05_CI_Workflows.md) | CI workflow details |
| [`06_Testing_Guide.md`](06_Testing_Guide.md) | Testing and raw-response scrutiny |
| [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md) | Rendered-DOM fixtures and failure-page classification |
| [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md) | Live-site verification status |
| [`template-workflow.md`](template-workflow.md) | Template-to-scraper workflow |
| [`test-report-template.md`](test-report-template.md) | Full-suite test report format |
| [`../scrapers/README.md`](../scrapers/README.md) | Public vs. private scrapers and security policy |
| [`../tools/README.md`](../tools/README.md) | Tool commands, quality gate, and scrutiny |
| [`../tools/SRB-2.0-documentation.md`](../tools/SRB-2.0-documentation.md) | Scraper Request Builder manual |

## Rule of thumb

Use `templates/` to start a file, `skills/stash-scraper-builder/` to decide how it should be authored, `validator/` and `tools/` to verify it, and `docs/` to understand repository workflow and maintenance.
