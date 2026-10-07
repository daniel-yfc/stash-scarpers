# Template Workflow

## Purpose

Use the templates in `templates/` as scaffolding, then move the working scraper into `scrapers/`. The templates do not replace the skill instructions or the official CommunityScrapers validator.

## Which files belong together

For a declarative scraper, copy one YAML template. For a script scraper, copy both files:

- `templates/ScriptScraper/ScriptScraperTemplate.yml` — Stash-facing entry-point wrapper.
- `templates/ScriptScraper/ScriptScraperTemplate.py` — Python implementation scaffold invoked by the wrapper.
- Upstream source: [`stashapp/CommunityScrapers` › `templates/ScriptScraper/`](https://github.com/stashapp/CommunityScrapers/tree/master/templates/ScriptScraper).

The YAML operation arguments and the Python operation dispatcher must remain synchronized. The Python process must emit only scraper JSON on stdout; diagnostics belong on stderr.

## Workflow

1. Select the smallest template that matches the object type and runtime path.
2. Copy it into `scrapers/` and rename it using the target site's CamelCase name.
3. Keep or add the required root `name` key in the YAML.
4. For script scrapers, copy the Python file into the matching `scrapers/` dependency directory and update every YAML script path.
5. Remove modes the site does not support. Do not invent search endpoints.
6. Implement real extraction functions, dependency imports, and operation dispatch.
7. Verify the input/output contract in [`../skills/stash-scraper-builder/references/script-actions.md`](../skills/stash-scraper-builder/references/script-actions.md).
8. Run the schema checklist and official validator.
9. Run the repository tests and quality gate.
10. Mark untested selectors or site assumptions explicitly; do not present placeholder metadata as verified.

## Documentation relationships

| Layer                  | Responsibility                                    | Canonical location                          |
| ---------------------- | ------------------------------------------------- | ------------------------------------------- |
| Templates              | Starting YAML/Python scaffolds                    | `templates/`                                |
| Repository workflow    | Copying, pairing, and validation sequence         | `docs/`                                     |
| Agent behavior         | Scope, output contract, and global rules          | `AGENTS.md`                                 |
| Skill behavior         | Scraper design and authoring contract             | `skills/stash-scraper-builder/SKILL.md`     |
| Specialized operations | Script I/O, dates, XPath, JSON, CDP, and failures | `skills/stash-scraper-builder/references/`  |
| Runtime validation     | Official schema and validator                     | `validator/` and upstream CommunityScrapers |

## Script-specific checks

- YAML root `name` is present.
- Every script path resolves from the scraper location.
- Operation names match between YAML and Python.
- `*ByName` returns a JSON list, including one result.
- Other operations return the expected object shape.
- Errors and diagnostics do not pollute stdout.
- Dependencies and installation prerequisites are documented.
- Placeholder URLs and metadata are replaced before deployment.
