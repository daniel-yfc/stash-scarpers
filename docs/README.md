---
doc_id: DOC-INDEX-00
title: Documentation Index
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
last_verified: "2026-10-06"
authority: canonical
routing:
  intents:
    - documentation-index
    - repository-workflow
---

# Documentation Index

This directory contains repository-level workflow, architecture, testing, and maintenance documentation. Start with the [English build guide](../README.md) or [Traditional Chinese build guide](../readme-zh-tw.md). The machine-readable registry is [`index.yml`](index.yml); [documentation architecture](repository-documentation-architecture.md) owns naming, metadata, routing, and formatter policy.

## Ownership

- Repository workflow and project operations: root README, this directory, and `CONTRIBUTING.md`.
- Agent boundaries: `AGENTS.md` and `CLAUDE.md`; scraper authoring: `skills/stash-scraper-builder/SKILL.md` and selected references.
- Schema and runtime behavior: executable validator/schema and verified runtime evidence, not an audit recommendation.

## Guides

| Document                                                                               | Purpose                                                   |
| -------------------------------------------------------------------------------------- | --------------------------------------------------------- |
| [`01_System_Architecture.md`](01_System_Architecture.md)                               | Repository architecture and verification layers           |
| [`02_Quality_Gate_Overview.md`](02_Quality_Gate_Overview.md)                           | Quality-gate overview                                     |
| [`03_Quality_Gate_Rules.md`](03_Quality_Gate_Rules.md)                                 | Canonical quality rules                                   |
| [`04_Production_Gate.md`](04_Production_Gate.md)                                       | Production readiness                                      |
| [`05_CI_Workflows.md`](05_CI_Workflows.md)                                             | CI workflow details                                       |
| [`06_Testing_Guide.md`](06_Testing_Guide.md)                                           | Testing and live-scrutiny guidance                        |
| [`07_Rendered_DOM_Fixture_Testing.md`](07_Rendered_DOM_Fixture_Testing.md)             | Rendered DOM fixture contract and authoring expectations  |
| [`LIVE_TEST_STATUS.md`](LIVE_TEST_STATUS.md)                                           | Live-site verification status                             |
| [`template-workflow.md`](template-workflow.md)                                         | Template-to-scraper workflow                              |
| [`test-report-template.md`](test-report-template.md)                                   | Full-suite test report format                             |
| [`verification-metadata.md`](verification-metadata.md)                                 | Verification metadata contract                            |
| [`repository-documentation-architecture.md`](repository-documentation-architecture.md) | Documentation naming, metadata, routing, formatter policy |
| [`../scrapers/README.md`](../scrapers/README.md)                                       | Public versus private scrapers and security               |
| [`../tools/README.md`](../tools/README.md)                                             | Tool commands, quality gate, and scrutiny                 |
| [`../tools/SRB-2.0-documentation.md`](../tools/SRB-2.0-documentation.md)               | Scraper Request Builder manual                            |

Use `templates/` to start a file, the skill to author it, `validator/` and `tools/` to verify it, and these guides to understand governance. Historical `evidence/` reviews are not canonical instructions.
