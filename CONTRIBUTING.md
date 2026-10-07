# Contributing

Thanks for contributing to Stash Scraper Builder!

## Quick Start

1. Fork and clone the repository
2. Install dependencies:

   ```bash
   npm ci
   python -m pip install -r requirements.txt
   ```

3. Create a branch: `git checkout -b feat/my-scraper`

## Making Changes

### Adding a Scraper

1. Create `scrapers/MyScraper.yml` with the required root `name:`.
2. Validate locally: `npm run validate`.
3. Check URL sorting: `npm run validate-sort`.
4. Run the repository policy gate and tests, then test applicable search and detail pages when site access permits. Record what remains unverified.

### Modifying the Skill

1. Edit files in `skills/stash-scraper-builder/`.
2. Ensure references and runnable examples remain valid.
3. Update `AGENTS.md` only if repository-wide rules change.

## Before You Push

- [ ] Run `npm run validate` — no schema errors.
- [ ] Run `npm run validate-sort` — URLs sorted A–Z.
- [ ] Run `bash tools/validate-all.sh` — repository policy gate.
- [ ] Run `python -m pytest tools/tests/ -v` — covered regression tests.
- [ ] Run `python tools/check_scraper_docs.py` and `python tools/check_docs_index.py` for documentation changes.
- [ ] Run `npm run format:check` for formatting; inspect the separate advisory link report when relevant.
- [ ] Record fixture, raw-response, rendered-DOM, live-search, live-detail, and Stash/CDP results separately; never replace missing evidence with a checklist pass.

## Pull Requests

- PRs to `scrapers/`, `skills/`, or `validator/` require maintainer review (see `.github/CODEOWNERS`).
- `validate.yml` runs the path-filtered repository validation layers, including pytest; `pr-check.yml` gives changed-scraper feedback.
- `fixture-manifests.yml`, `evidence-contract.yml`, and `cdp-evidence-gate.yml` check distinct evidence contracts on their configured triggers.
- `link-check.yml` runs on Markdown PRs, weekly, and manually, but broken external links are advisory (`fail: false`).
- `scrutiny.yml` is a deliberate manual raw-response check, not browser-rendered or live Stash/CDP verification.
- Read the exact trigger, scope, and proof boundary for all eight current workflows in [`docs/05_CI_Workflows.md`](docs/05_CI_Workflows.md). Only actually executed required checks can pass; an advisory green job is not a guarantee that every link resolved.

## Code Style

- YAML: 2-space indentation, sorted URL arrays.
- Python: follow `pytest` conventions in `tools/tests/`.
- Markdown: use relative paths for internal links and run the formatter; inspect link-check results separately.

## Evidence and source policy

Use this source hierarchy when authoring or changing scraper guidance:

1. Official CommunityScrapers schema and validator, from which this repository's validator expectations derive.
2. Official Stash scraper-development documentation for upstream application behavior.
3. Upstream Stash issues or source for runtime behavior.
4. Project references and examples.
5. Heuristics, explicitly labeled `Heuristic`.

- Normative schema/runtime rules must include a nearby source citation or point to `skills/stash-scraper-builder/references/UPSTREAM_SOURCES.md`.
- Experience-based recommendations must be labeled `Heuristic`; do not present them as schema behavior or runtime causality.
- Search the full `skills/stash-scraper-builder/` tree for duplicated wording before changing a rule.
- Keep complete YAML examples copy-paste-valid and include the required root `name:` field.
- If project guidance conflicts with an authoritative source, correct the project guidance first.

## Runtime claims

Do not claim a configuration prevents a runtime crash without a reproducible test or authoritative upstream evidence. For upstream bugs, cite the issue and document the trigger and mitigation separately.

## Pull-request evidence

Describe the authoritative source for behavior changes, list validation commands run, and note any remaining unverified live-page selectors.

## Questions?

Open an issue or reach out to `@daniel-yfc`.
