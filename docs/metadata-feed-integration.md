---
doc_id: DOC-INTEGRATION-80
title: Metadata Feed Integration
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
  - contributor
applies_to:
  - scrapers
  - metadata-quality
last_verified: "2026-10-10"
authority: derived
routing:
  intents:
    - identify
    - tagger
    - auto-tagging
    - graphql
---

# Metadata Feed Integration

These website scrapers supply metadata to Stash. They do not publish a stash-box
database, provide fingerprints, or synchronize local data to a remote service.
The scope here is compatibility and data quality; no bulk update or upload is
performed by the checks below.

## Integration boundaries

| Consumer      | Direct interface                                                 | What this repository contributes                                                                                                  |
| ------------- | ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| Identify      | A configured stash-box source or scraper with `sceneByFragment`  | Only a deterministic, verified single-scene match belongs here. A name search is not an Identify match.                           |
| Scene Tagger  | Stash-box fingerprint/keyword lookup                             | Indirect only: reviewed metadata may be submitted through a separate authorized stash-box workflow. Site codes are not stash IDs. |
| Auto Tagging  | Existing local entity names in file paths                        | Indirect: correctly saved performer, studio and tag names. It does not create entities and does not match performer aliases.      |
| Stash GraphQL | Scraping queries return candidates; separate mutations save data | Query using the actual installed scraper ID and retain source URLs. A GraphQL query does not populate stash-box.                  |

Sources: [Identify](https://github.com/stashapp/stash/blob/develop/ui/v2.5/src/docs/en/Manual/Identify.md),
[Scene Tagger](https://github.com/stashapp/stash/blob/develop/ui/v2.5/src/docs/en/Manual/Tagger.md),
[Auto Tagging](https://github.com/stashapp/stash/blob/develop/ui/v2.5/src/docs/en/Manual/AutoTagging.md),
[GraphQL scraper types](https://github.com/stashapp/stash/blob/develop/graphql/schema/types/scraper.graphql).

## Matching corrections

On 2026-10-10 the keyword-results `sceneByFragment` entries were removed from
CK-Download, ClubCK, GAMES, HunkCh, JGVData, Justice01, KOVideo, MensRushTV and
private/GV-Wiki. Their keyword search and selected-result detail paths remain.
Use those paths to select a real product before saving it. Reload installed
scrapers after deployment and review any Identify source lists referencing these
entries; they are no longer automatic Identify sources.

The XPath fragment path calls `scrapeScene`, which keeps the first mapped result.
Identify sees a single result, even if the HTML contains several candidates.
Consequently its multiple-match skip option cannot detect the discarded rows.
This can also mix a first title with several candidate URLs in a detail-shaped
result. Sources: [XPath runtime](https://github.com/stashapp/stash/blob/develop/pkg/scraper/xpath.go),
[mapped runtime](https://github.com/stashapp/stash/blob/develop/pkg/scraper/mapped.go),
[Identify matching](https://github.com/stashapp/stash/blob/develop/internal/identify/identify.go).

Private Gayerdar's scene and performer name entries used `{url}`. Stash's name
scraper substitutes only `{}`, so these entries and their unused search mappings
were removed. Restore name search only with a verified real keyword endpoint.

Remaining fragment declarations are **not certified for unattended Identify**:
ACCEED and private/Gayerdar depend on an existing scene URL; BRAVO derives a clip
path from title text; FC2 extracts digits from a filename. The latter two can
confuse unrelated numbers with a site identifier. Keep them out of bulk Identify
until positive, ambiguous, unrelated-number, missing-input and zero-result cases
have passed in the installed Stash version. Prefer explicit product URLs meanwhile.

## Executable checks

```bash
python tools/check_metadata_feed.py
python tools/check_metadata_feed.py --inventory
python -m pytest tools/tests/test_metadata_feed.py -v
```

The definition check fails on mapped name searches without `{}`, missing scene
search title/URL or detail handoff, and reuse of a name-search mapper or search
endpoint as a single-scene fragment lookup. These are repository integration
policies in addition to the official schema. The inventory reports declarations,
CDP requirements and field coverage; it labels live Stash behavior `UNVERIFIED`.
It is not a semantic or runtime certification of remaining entry points.

For captured website-scraper results:

```bash
python tools/check_metadata_feed.py --payload captured-results.json
python tools/check_metadata_feed.py --payload negative-control.json --allow-empty
```

Input is a JSON array of GraphQL-shaped `ScrapedScene` objects, or a complete
`data.scrapeSingleScene` response. Select `title`, `urls`, `date`,
`production_date`, `duration`, `code`, `remote_site_id`, and relationship
`name`, `urls`, `remote_site_id` fields when capturing results. Include tags'
names/remote IDs; tags do not expose URLs. Do not include authentication headers,
cookies, browser storage, or private file paths.

The checker enforces a nonempty plain title and source URL, absolute HTTP(S)
URLs, valid ISO calendar dates, integer seconds, plain relationship names,
duplicate review, and no fabricated stash-box IDs/fingerprints in a website feed.
Unknown optional fields may be null/absent. It never edits source-language values.
An empty response is a failure unless explicitly requested as a negative control;
GraphQL errors remain failures even when partial data exists. This tool is for
website feeds, not legitimate stash-box responses with remote IDs.

Image output is deliberately not inferred from these checks: Stash GraphQL may
return a base64 data URL after fetching a scraper's image URL. Verify the actual
cover separately. No offline check proves a title identifies the correct scene,
a code is correct, or a name refers to the intended person.

## Read-only GraphQL verification

Use the installed Stash GraphQL explorer and discover IDs with `listScrapers`;
do not assume the YAML display name is the ID. `scrapeSingleScene` accepts either
`scraper_id` or `stash_box_endpoint`, not both. With a website scraper, `query`
uses name search, `scene_input` uses selected-result query-fragment scraping,
and `scene_id` uses the stored scene/fragment path. Supply one input route at a
time. `scrapeMultiScenes` is not implemented for website scraper sources in the
reviewed upstream resolver. Check the installed version before relying on it.
Source: [scraper resolver](https://github.com/stashapp/stash/blob/develop/internal/api/resolver_query_scraper.go).

Before saving or publishing, compare the selected result with the source page:
title/code, canonical product URL, release date (not upload date), seconds,
studio versus label, individual performer names/profile URLs, and tag taxonomy.
Review same-name people and aliases rather than merging on a name alone. Leave
missing values absent; do not synthesize dates, genders, identities or fingerprints.

Run a small reviewed set first. For Identify, use Merge for existing metadata and
skip ambiguous matches; review entity creation and single-name performers. For
Tagger, review performer-gender filters and tag merging. For Auto Tagging, save
reviewed local entities first, then test file-name word boundaries and organized
flags. These are operator checks, not changes made by this repository.

## Evidence required for promotion

Retain the exact scraper revision and Stash version; one successful and one
negative case per enabled mode; search-to-selected-detail consistency; missing
optional values; duplicate and ambiguous identity cases; and fresh actual field
values compared with the source. Record schema, static contracts, synthetic
tests, browser DOM, Stash loading, live extraction and database saving separately.
The synthetic tests added here verify rejection behavior only. All-site live
Stash extraction, stash-box publishing and Auto Tagging remain unverified until
those separate checks are run.
