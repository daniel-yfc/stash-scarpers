---
doc_id: REF-CORE-00
title: Skill Read Order
status: active
layer: skill
owner: maintainer
audience:
  - agent
last_verified: "2026-10-02"
authority: canonical
routing:
  intents:
    - agent-routing
    - read-order
---

# Skill Read Order

Read repository-level routing before skill-level guidance.

## Repository first

1. `README.md` — project purpose, canonical commands, and directory map
2. `AGENTS.md` — repository-wide agent and safety rules
3. `docs/index.yml` — machine-readable document registry
4. `docs/repository-documentation-architecture.md` — ownership, numbering, naming, metadata, indexing, routing, and formatter policy
5. `templates/README.md` — when starting from a template
6. `CONTRIBUTING.md` — before committing or modifying shared repository files

## Skill second

7. `SKILL.md` — skill contract and authoring workflow
8. `references/out-of-scope.md` — confirm the task belongs to the skill
9. `references/source-selection.md` — select XPath, JSON, script, or CDP
10. `references/phase0-secrets-policy.md` — when authentication or private paths are involved

## Specialized references

| Task                   | Read                                                                   |
| ---------------------- | ---------------------------------------------------------------------- |
| New XPath scraper      | `xpath-patterns.md` → `schema-checklist.md` → `post-processing.md`     |
| New JSON scraper       | `json-patterns.md` → `schema-checklist.md` → `post-processing.md`      |
| Script scraper         | `script-actions.md` → `template-workflow.md` → `schema-checklist.md`   |
| CDP/login scraper      | `cdp-workflow.md` → `phase0-secrets-policy.md` → `schema-checklist.md` |
| Dates/post-processing  | `date-formats.md` → `post-processing.md`                               |
| Advanced patterns      | `advanced-patterns.md`                                                 |
| Regression/evaluation  | `eval-pack.md` → repository `tools/tests/` and validation commands     |
| Verification metadata  | `verification-metadata-ref.md` → `docs/verification-metadata.md`       |
| Live-site verification | repository `docs/06_Testing_Guide.md` → `docs/LIVE_TEST_STATUS.md`     |

## Before editing

- Check `UPSTREAM_SOURCES.md` for the owning source.
- Confirm every referenced path exists.
- Use the canonical repository commands from `docs/repository-documentation-architecture.md`.
- Register new or renamed Markdown documents in `docs/index.yml`.
- Keep repository governance in repository-level docs and scraper semantics in skill-level docs.
