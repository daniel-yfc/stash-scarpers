# Skill Read Order

**Repo-only**: when using this skill inside the `stash-scarpers` repo, read repository-level routing before skill-level guidance. Standalone, start at "Skill second".

## Repository first (repo-only)

1. `README.md` — project purpose, canonical commands, and directory map
2. `AGENTS.md` — repository-wide agent and safety rules
3. `docs/index.yml` — machine-readable document registry
4. `docs/repository-documentation-architecture.md` — ownership, numbering, naming, metadata, indexing, routing, and formatter policy
5. `templates/README.md` — when starting from a template
6. `CONTRIBUTING.md` — before committing or modifying shared repository files

## Skill second

7. `SKILL.md` — skill contract and authoring workflow
8. `references/out-of-scope.md` — confirm the task belongs to the skill
9. `SKILL.md` § Runtime selection — select XPath, JSON, script, or CDP
10. `references/phase0-secrets-policy.md` — when authentication or private paths are involved

## Specialized references

| Task                   | Read                                                                                   |
| ---------------------- | -------------------------------------------------------------------------------------- |
| New XPath scraper      | `xpath-patterns.md` → `schema-checklist.md` → `post-processing.md`                     |
| New JSON scraper       | `json-patterns.md` → `json-examples.md` → `schema-checklist.md` → `post-processing.md` |
| Script scraper         | `script-actions.md` → `authoring-checklist.md` → `schema-checklist.md`                 |
| CDP/login scraper      | `cdp-workflow.md` → `phase0-secrets-policy.md` → `schema-checklist.md`                 |
| Dates/post-processing  | `post-processing.md` (§ Date formats)                                                  |
| Field quality          | `field-quality.md` → `entity-fields.md` → `post-processing.md`                         |
| Examples               | `examples.md` → `json-examples.md`                                                     |
| Best practices         | `best-practices.md` → `multi-site-network-scrapers.md`                                 |
| Debugging failures     | `debugging.md` → `incident-reviews.md` (past incidents)                                |
| Regression/evaluation  | `eval-pack.md` → **repo-only**: repository `tools/tests/` and validation commands    |
| Verification metadata  | **Repo-only**: `docs/verification-metadata.md`                                         |
| Live-site verification | **Repo-only**: `docs/06_Testing_Guide.md` → `docs/LIVE_TEST_STATUS.md`                 |

## Before editing

- Check `UPSTREAM_SOURCES.md` for the owning source.
- Confirm every referenced path exists.
- **Repo-only**: use the canonical repository commands from `docs/repository-documentation-architecture.md`; register new or renamed Markdown documents in `docs/index.yml`; keep repository governance in repository-level docs and scraper semantics in skill-level docs.
