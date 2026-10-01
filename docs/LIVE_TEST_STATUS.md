# Live Test Status

This table separates schema validation from live-page verification. `Schema` means the official validator accepts the YAML; it does not mean the website selectors are currently working.

| Scraper       | Schema |       Live search | Live detail | Auth/CDP                               | Status                     |
| ------------- | -----: | ----------------: | ----------: | -------------------------------------- | -------------------------- |
| ACCEED        |   Pass |        Unverified |  Unverified | CDP enabled                            | Needs live test            |
| Bravo-Japan   |   Pass |    Not configured |  Unverified | CDP enabled                            | Needs live test            |
| CK-Download   |   Pass | Verified snapshot |  Unverified | CDP enabled/login-gated                | Needs live detail test     |
| Coat          |   Pass |        Unverified |  Unverified | CDP enabled/login-gated                | Needs live test            |
| fc2           |   Pass |    Not configured |  Unverified | Public                                 | Needs live test            |
| Games-Video   |   Pass |    Not configured |  Unverified | CDP enabled                            | Needs live test            |
| GV-Wiki       |   Pass |        Unverified |  Unverified | Private CDP; placeholder cookie fields | Configure session and test |
| Hunks-Ch      |   Pass | Verified snapshot |  Unverified | CDP enabled/login-gated                | Needs live detail test     |
| JGVData       |   Pass |        Unverified |  Unverified | Public                                 | Needs live test            |
| Justice01     |   Pass |    Not configured |  Unverified | CDP enabled                            | Needs live test            |
| KO-Shop       |   Pass | Verified snapshot |  Unverified | CDP enabled/login-gated                | Needs live detail test     |
| KO-Tube       |   Pass |        Unverified |  Unverified | CDP enabled                            | Needs live test            |
| Ko-Video      |   Pass | Verified snapshot |  Unverified | CDP enabled/login-gated                | Needs live detail test     |
| Men's Rush TV |   Pass | Verified snapshot |  Unverified | CDP enabled/login-gated                | Needs live detail test     |

## Test protocol

For each site, record:

1. One known detail URL.
2. One scene-name search URL, if supported.
3. Extracted title, code, date, image, studio, tags, performers, and URL.
4. Whether the page required CDP, login, age verification, or cookies.
5. The date and site response status.

Do not promote a scraper from `Unverified` based only on schema validation.
