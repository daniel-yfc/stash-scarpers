# Entity Field Reference

Complete field lists for the seven scraped object types, verified against
the official CommunityScrapers validator schema (**repo-only** local copy: `validator/scraper.schema.json`).
Field names are case-sensitive.

"Schema required" = enforced by the validator.
"Runtime required" = enforced by Stash at scrape time per the official
ScraperDevelopment docs (not in the schema).

Source: https://docs.stashapp.cc/in-app-manual/scraping/scraperdevelopment/

## Scene

| Field          | Notes                                    |
| -------------- | ---------------------------------------- |
| Code           |                                          |
| Date           | Use `parseDate` with Go reference layout |
| Details        |                                          |
| Director       |                                          |
| Duration       |                                          |
| Groups         | Relationship                             |
| Image          | Cover image URL                          |
| Movies         | Relationship                             |
| Performers     | Relationship                             |
| ProductionDate |                                          |
| Studio         | Relationship                             |
| Tags           | Relationship                             |
| Title          | Runtime required if fileless             |
| URL            | Singular                                 |
| URLs           | Plural                                   |

## Performer

| Field          | Notes                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| Aliases        |                                                                                                               |
| Birthdate      |                                                                                                               |
| CareerEnd      |                                                                                                               |
| CareerLength   |                                                                                                               |
| CareerStart    |                                                                                                               |
| Circumcised    |                                                                                                               |
| Country        |                                                                                                               |
| DeathDate      |                                                                                                               |
| Details        |                                                                                                               |
| Disambiguation |                                                                                                               |
| Ethnicity      |                                                                                                               |
| EyeColor       |                                                                                                               |
| FakeTits       |                                                                                                               |
| Gender         | Enum: `male`, `female`, `transgender_male`, `transgender_female`, `intersex`, `non_binary` (case-insensitive) |
| HairColor      |                                                                                                               |
| Height         |                                                                                                               |
| Image          |                                                                                                               |
| Images         |                                                                                                               |
| Measurements   |                                                                                                               |
| Name           | **Schema required**                                                                                           |
| PenisLength    |                                                                                                               |
| Piercings      |                                                                                                               |
| Tags           | Relationship                                                                                                  |
| Tattoos        |                                                                                                               |
| Twitter        |                                                                                                               |
| URL            | Singular                                                                                                      |
| URLs           | Plural                                                                                                        |
| Weight         |                                                                                                               |

## Group

Replaces the deprecated `movieByURL` action.

| Field      | Notes            |
| ---------- | ---------------- |
| Aliases    |                  |
| BackImage  |                  |
| Date       |                  |
| Director   |                  |
| Duration   |                  |
| FrontImage |                  |
| Name       | Runtime required |
| Studio     | Relationship     |
| Synopsis   |                  |
| Tags       | Relationship     |
| URL        | Singular         |
| URLs       | Plural           |

## Gallery

| Field        | Notes               |
| ------------ | ------------------- |
| Code         |                     |
| Date         |                     |
| Details      |                     |
| Performers   | Relationship        |
| Photographer |                     |
| Studio       | Relationship        |
| Tags         | Relationship        |
| Title        | **Schema required** |
| URL          | Singular            |
| URLs         | Plural              |

## Image

| Field        | Notes        |
| ------------ | ------------ |
| Code         |              |
| Date         |              |
| Details      |              |
| Performers   | Relationship |
| Photographer |              |
| Studio       | Relationship |
| Tags         | Relationship |
| Title        |              |
| URLs         | Plural       |

## Studio

| Field   | Notes               |
| ------- | ------------------- |
| Aliases |                     |
| Details |                     |
| Image   |                     |
| Name    | **Schema required** |
| URL     | Singular            |
| URLs    | Plural              |

## Tag

The schema defines no properties for tags; only `Name` is used at runtime.

| Field | Notes                             |
| ----- | --------------------------------- |
| Name  | Runtime required (sole tag field) |

## Relationships vs plain fields

Fields marked "Relationship" (Performers, Tags, Studio, Groups, Movies) are
processed by `processSceneRelationships` and related functions, not by the
plain field-mapping path. See `references/debugging.md` for the nil-pointer
incident when a scrape returns zero plain fields but defines relationships.
