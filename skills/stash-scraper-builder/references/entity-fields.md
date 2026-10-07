# Entity Field Reference

Complete field lists for the seven scraped object types, per the official
Stash ScraperDevelopment documentation. Field names are case-sensitive and
must match the Go struct fields.

Source: https://docs.stashapp.cc/in-app-manual/scraping/scraperdevelopment/
(Official docs are ground truth; this file is a convenient index.)

## Scene

`Title` is required only when scraping fileless (no file attached).
Otherwise all fields are optional.

| Field      | Notes                                    |
| ---------- | ---------------------------------------- |
| Code       |                                          |
| Date       | Use `parseDate` with Go reference layout |
| Details    |                                          |
| Director   |                                          |
| Groups     | Relationship                             |
| Image      | Cover image URL                          |
| Performers | Relationship                             |
| Studio     | Relationship                             |
| Tags       | Relationship                             |
| Title      | Required if fileless                     |
| URLs       |                                          |

## Performer

`Name` is required.

| Field          | Notes                                                                                                         |
| -------------- | ------------------------------------------------------------------------------------------------------------- |
| Aliases        |                                                                                                               |
| Birthdate      |                                                                                                               |
| CareerLength   |                                                                                                               |
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
| Measurements   |                                                                                                               |
| Name           | **Required**                                                                                                  |
| PenisLength    |                                                                                                               |
| Piercings      |                                                                                                               |
| Tags           | Relationship                                                                                                  |
| Tattoos        |                                                                                                               |
| URLs           |                                                                                                               |
| Weight         |                                                                                                               |

## Group

`Name` is required. Replaces the deprecated `movieByURL` action.

| Field      | Notes        |
| ---------- | ------------ |
| Aliases    |              |
| BackImage  |              |
| Date       |              |
| Director   |              |
| Duration   |              |
| FrontImage |              |
| Name       | **Required** |
| Rating     |              |
| Studio     | Relationship |
| Synopsis   |              |
| Tags       | Relationship |
| URLs       |              |

## Gallery

`Title` is required.

| Field        | Notes        |
| ------------ | ------------ |
| Code         |              |
| Date         |              |
| Details      |              |
| Performers   | Relationship |
| Photographer |              |
| Rating       |              |
| Studio       | Relationship |
| Tags         | Relationship |
| Title        | **Required** |
| URLs         |              |

## Image

No required fields.

| Field        | Notes        |
| ------------ | ------------ |
| Code         |              |
| Date         |              |
| Details      |              |
| Performers   | Relationship |
| Photographer |              |
| Rating       |              |
| Studio       | Relationship |
| Tags         | Relationship |
| Title        |              |
| URLs         |              |

## Studio

`Name` is required.

| Field   | Notes                 |
| ------- | --------------------- |
| Aliases |                       |
| Details |                       |
| Name    | **Required**          |
| Tags    | Relationship          |
| URL     | Singular (not `URLs`) |

## Tag

`Name` is required.

| Field | Notes        |
| ----- | ------------ |
| Name  | **Required** |

## Relationships vs plain fields

Fields marked "Relationship" (Performers, Tags, Studio, Groups) are processed
by `processSceneRelationships` and related functions, not by the plain
field-mapping path. See `references/debugging.md` for the nil-pointer
incident when a scrape returns zero plain fields but defines relationships.
