# Upstream Sources and Document Inventory

## Skill entry point

- `SKILL.md` — primary instructions and output contract.

## Reference documents

| Document                         | Role                                                                     | Status                              |
| -------------------------------- | ------------------------------------------------------------------------ | ----------------------------------- |
| `UPSTREAM_SOURCES.md`            | Source registry and maintenance notes                                    | Current                             |
| `best-practices.md`              | General authoring guidance (incl. anchors, studio maps, legacy patterns) | Audit with #21                      |
| `cdp-workflow.md`                | Login and CDP workflows                                                  | Audit with #21/#26                  |
| `eval-pack.md`                   | Five-task validation and regression pack                                 | Run under #26                       |
| `authoring-checklist.md`         | Template-to-scraper checklist                                            | Current                             |
| `debugging.md`                   | Failure catalog and incident reviews                                     | Current                             |
| `field-quality.md`               | Title and performer cleaning                                             | Current                             |
| `examples.md`                    | Minimal scraper examples and fixtures                                    | Audit with #21/#22/#24              |
| `json-examples.md`               | JSON scraper examples                                                    | Audit with #21/#26                  |
| `json-patterns.md`               | JSON selectors, entry points, and placeholders                           | Audit with #21/#22/#24              |
| `multi-site-network-scrapers.md` | Multi-site and network-source guidance                                   | Audit with #21                      |
| `out-of-scope.md`                | Explicit skill boundary                                                  | Phase 0 complete                    |
| `phase0-secrets-policy.md`       | Cookies, tokens, CDP, and private paths                                  | Phase 0 complete                    |
| `post-processing.md`             | Field transformation order (incl. Go date layouts)                       | Audit with #21/#26                  |
| `schema-checklist.md`            | Root keys and schema checklist                                           | Audit with #21/#22/#24              |
| `scraper.schema.json`            | Local schema reference                                                   | Compare with upstream under #21/#26 |
| `script-actions.md`              | Script action patterns and I/O                                           | Audit with #21/#22                  |
| `skill-read-order.md`            | Recommended reading sequence                                             | Phase 0 complete                    |
| `xpath-patterns.md`              | XPath scraper patterns                                                   | Audit with #21/#26                  |

## External source registry

| Source                                 | URL                                                                      | Use                                      |
| -------------------------------------- | ------------------------------------------------------------------------ | ---------------------------------------- |
| Stash scraping overview                | https://docs.stashapp.cc/in-app-manual/scraping/                         | Entry points and scraper categories      |
| Stash scraper development              | https://docs.stashapp.cc/in-app-manual/scraping/scraperdevelopment/      | Actions and post-processing              |
| Stash metadata sources                 | https://docs.stashapp.cc/metadata-sources/                               | Scraper and stash-box taxonomy           |
| Stash API                              | https://docs.stashapp.cc/api/                                            | Background only; GraphQL is out of scope |
| Stash login scraping guide             | https://docs.stashapp.cc/guides/scraping-metadata-behind-login/          | CDP/login baseline                       |
| CommunityScrapers architecture         | https://deepwiki.com/stashapp/CommunityScrapers/1.1-system-architecture  | Design context                           |
| CommunityScrapers driver configuration | https://deepwiki.com/stashapp/CommunityScrapers/8.4-driver-configuration | CDP, cookies, and browser automation     |

## Maintenance

- Verify material claims against an authoritative upstream source before rewriting a rule.
- Treat the official schema and current upstream documentation as authoritative over local stubs.
- Keep issue references current when the audit sequence changes.
- Re-run the evaluation pack after schema or entry-point guidance changes.
- Do not mark the skill complete while tracked P0/P1 corrections remain open in #21, #22, #24, #25, or #26.
