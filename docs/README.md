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

This directory contains repository-level workflow, architecture, testing, and maintenance documentation. Start with the [English build guide](../README.md) or [Traditional Chinese build guide](../readme-zh-tw.md). The machine-readable registry is [`index.yml`](index.yml); [documentation architecture](00-documentation-architecture.md) owns naming, metadata, routing, and formatter policy.

## Ownership

- Repository workflow and project operations: root README, this directory, and `CONTRIBUTING.md`.
- Agent boundaries: `AGENTS.md` and `CLAUDE.md`; scraper authoring: `skills/stash-scraper-builder/SKILL.md` and selected references.
- Schema and runtime behavior: executable validator/schema and verified runtime evidence, not an audit recommendation.

## Guides

- [Metadata feed integration](80-metadata-feed-integration.md): consumer boundaries,
  matching corrections, executable data-quality checks and runtime verification.

| Document                                                                   | Purpose                                                   |
| -------------------------------------------------------------------------- | --------------------------------------------------------- |
| [`10-system-architecture.md`](10-system-architecture.md)                   | Repository architecture and verification layers           |
| [`20-quality-gate-overview.md`](20-quality-gate-overview.md)               | Quality-gate overview                                     |
| [`21-quality-gate-rules.md`](21-quality-gate-rules.md)                     | Canonical quality rules                                   |
| [`30-production-gate.md`](30-production-gate.md)                           | Production readiness                                      |
| [`40-ci-workflows.md`](40-ci-workflows.md)                                 | CI workflow details                                       |
| [`50-testing-guide.md`](50-testing-guide.md)                               | Testing and live-scrutiny guidance                        |
| [`51-rendered-dom-fixture-testing.md`](51-rendered-dom-fixture-testing.md) | Rendered DOM fixture contract and authoring expectations  |
| [`81-graphql-api-reference.md`](81-graphql-api-reference.md)               | Stash GraphQL API reference (endpoint, schema, mutations) |
| [`60-live-test-status.md`](60-live-test-status.md)                         | Live-site verification status                             |
| [`70-template-workflow.md`](70-template-workflow.md)                       | Template-to-scraper workflow                              |
| [`71-test-report-template.md`](71-test-report-template.md)                 | Full-suite test report format                             |
| [`72-evaluation-report-template.md`](72-evaluation-report-template.md)     | Local evaluation report format (standalone)               |
| [`52-verification-metadata.md`](52-verification-metadata.md)               | Verification metadata contract                            |
| [`00-documentation-architecture.md`](00-documentation-architecture.md)     | Documentation naming, metadata, routing, formatter policy |
| [`../scrapers/README.md`](../scrapers/README.md)                           | Public versus private scrapers and security               |
| [`../tools/README.md`](../tools/README.md)                                 | Tool commands, quality gate, and scrutiny                 |
| [`../tools/SRB-2.0-documentation.md`](../tools/SRB-2.0-documentation.md)   | Scraper Request Builder manual                            |

Use `templates/` to start a file, the skill to author it, `validator/` and `tools/` to verify it, and these guides to understand governance. Historical `evidence/` reviews are not canonical instructions.
