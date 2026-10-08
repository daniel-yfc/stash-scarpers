# Skill Read Order

**Load when:** you need the repository reading sequence (repo-only).

**Repo-only**: when using this skill inside the `stash-scarpers` repo, read repository-level routing before skill-level guidance. Standalone, start at "Skill second".

## Repository first (repo-only)

1. `README.md` — project purpose, canonical commands, and directory map
2. `AGENTS.md` — repository-wide agent and safety rules
3. `docs/index.yml` — machine-readable document registry
4. `docs/repository-documentation-architecture.md` — ownership, numbering, naming, metadata, indexing, routing, and formatter policy
5. `templates/README.md` — when starting from a template
6. `CONTRIBUTING.md` — before committing or modifying shared repository files

## Skill second

`SKILL.md` is the primary router — its Reference map lists every reference with an explicit read trigger. The short path:

1. `SKILL.md` — skill contract and authoring workflow
2. `references/out-of-scope.md` — confirm the task belongs to the skill
3. `SKILL.md` § Runtime selection — select XPath, JSON, script, or CDP
4. `SKILL.md` § Security — before any authentication, cookie, or CDP work

## Before editing

- Check `UPSTREAM_SOURCES.md` for the owning source.
- Confirm every referenced path exists.
- **Repo-only**: use the canonical repository commands from `docs/repository-documentation-architecture.md`; register new or renamed Markdown documents in `docs/index.yml`; keep repository governance in repository-level docs and scraper semantics in skill-level docs.
