# Wave 2E Agent A — Independent Evidence Audit Addendum

- Assignment: `WAVE2E-A-DVD-DOM-20261102` / WS-2E-10
- Audit UTC: `2026-11-02T10:03:01.877Z`
- Baseline main: `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`
- Original research branch HEAD inspected: `075006e7685375d4a8b3e2ef94d57d1eed49ddca`
- Current report: [WAVE2E-A-DVD-DOM-REPORT.md](WAVE2E-A-DVD-DOM-REPORT.md)
- Pinned historical-HTML audit: [historical-dom-structural-audit.json](evidence/historical-dom-structural-audit.json)
- **Release/handoff gate: `HANDOFF_STATUS=BLOCKED` for final XPath.** This does not invalidate the previously captured text research.

## 1. Classification and reproducibility review

The existing evidence contains six committed *sanitized text* files, not rendered HTML. All six exact UTF-8 SHA-256 digests in the original `manifest.json` are **correct (6/6)**. The fact that files match their SHA does not independently establish their claimed capture origin or prove the website HTTP response, canonical attribute, active CDP, XPath cardinalities, or current full rendered DOM.

DVD 084 recapture: `dvd-084.sanitized.txt` and `dvd-084-recapture.sanitized.txt` **are not byte-identical files**. The `# role:` header differs. The product-content portion starting at `\ntop of page` **is byte-identical**, SHA-256 `b4d300cc885172324f3cf76963f654727f6eeb461aed66770e0b6a5eccf32eca`. Amend the earlier report's unqualified "byte-identical" language accordingly.

This audit attempted publicly readable primary URLs 234 and 084. Direct public web retrieval returned **cache miss**; isolated shell HTTP access failed at DNS resolution. These are **inspection-channel failures, not evidence that the BRAVO server returned 404, challenge, or blocked access**. The earlier text captures remain source-reported evidence, not independently reverified live HTML.

## 2. Corrections supported by four complete historical DOM blobs

| Item | New verified historical observation | Correction to earlier interpretation |
| --- | --- | --- |
| HTML heading | `h1=0`, `h2=22` in 281/046/173/215 | The fixture's union (`h1 \| og:title`) can succeed through **numeric `og:title`** alone. Do not say its presence proves an h1 DVD title. |
| Product Title | Product `h2` is separate from numeric document `<title>` / `og:title` | `og:title=281/046/173/215` is **not** the product title. |
| `preceding::h2[2]` on DVD 046 | The 2026-10-14 DOM contains an **empty subtitle h2** between title and 品番, so the 2nd preceding h2 is in fact the **product title**, not `GO to BRAVO-CLIPS`. All four pinned historical pages share that result in a static h2 scan. | The previous "046 necessarily selects navigation" claim is **not supported by the historical DOM**. It remains a fragile positional selector: if the empty h2 disappears it could select unrelated navigation. Current 046 not verified at DOM level. |
| Code | `品番` followed by `281/046/173/215`, including literal `046` | Treat as historical source text, preserve leading zero; no URL-derived value. |
| Image | Each historic DOM contains a per-page `og:image` plus **one corresponding `img`** with the same media asset ID | Prior claim "DVD source image absent" overstates the evidence. Historical **product hero image exists**, but whether it is a true DVD cover and whether present on 234/084 require separate proof. A missing image in one old Wix component fixture is not proof of no image anywhere on page. |
| Tags | All four historical `meta keywords` are identical | Not demonstrated product-specific. Do not map directly to per-scene tags. |
| Studio | `レーベル` label values exist, differ by product | **Label** is source-verified historically. Stash **Studio** equivalence is semantically `AMBIGUOUS_SOURCE`, not field-level `VERIFIED`. |
| Details on 084 | Earlier capture lacks detail text, but has no HTML DOM or attributes | Classify as `UNVERIFIED`, not `SOURCE_FIELD_ABSENT` for site source, until rendered DOM is inspected. |
| Duration | Source `収録時間` is entire DVD duration | Do not equate to one Stash Scene's duration unless mapping policy is explicitly approved. |

Historical observed values (full markup scanned; no long descriptions republished):

| DVD | Real Title h2 | Code h2 | DVD minutes | Release Date | Source Label | per-page og:image/hero linkage |
| --- | --- | --- | --- | --- | --- | --- |
| 281 | 熊ケツ4 | `281` | 120 | 2020年7月31日 | ooooPS!! | 1 matching img |
| 046 | ゆるゆる雄太のデブ竿ぽちゃ穴食べ放題! | `046` | 260 | 2010年09月30日 | ooooPS!! | 1 matching img |
| 173 | 筋肉BANANA | `173` | 110 | 2016年7月13日 | BRAVO! | 1 matching img |
| 215 | 種竿狂 | `215` | 125 | 2017年12月22日 | BRAVO! | 1 matching img |

**Method limitation:** Counts and relative values above are obtained by reading the full pinned HTML source and scanning complete h2/tag sequences. They are **not full XPath engine evaluations**; the Python replay helper below evaluates actual XPath using `lxml` when run from a checkout with those files.

## 3. A-02/A-03 acceptance gaps — DO NOT equate text capture to completed DOM

| Target | Current inspected evidence | Required to close gate |
| --- | --- | --- |
| DVD 234 | Sanitized title/field text from previous session; no raw/complete DOM | Anonymous browser navigation response, final URL, HTTP status, CDP/JS readiness, sanitized **rendered HTML**, title & product Code/URL attribution, SHA-256 |
| DVD 084 | Repeated sanitized product text (body identical); no raw/complete DOM | Same, plus explicit test for missing Details vs hidden/late-loaded DOM and heading-less variant |
| DVD 281, 046 | Complete pinned 2026-10-14 rendered HTML; **not current website** | Evaluate exact XPath on historical pinned DOM and newly captured DOM; preserve literal `046` |
| Not-found / challenge | Earlier failed fetch attempts and historical Cloudflare test fixture only | Live HTTP/navigation result or `NOT_OBSERVED`; do not invent site 404 or Cloudflare |
| Missing optional image/Studio/performers | Historical source has some product hero images; no verified cast structure | Fail-closed; distinguish actual absent vs extraction tool omission |
| Product vs Scene | DVD descriptions mention multiple Parts / 2 discs | Explicit controller decision on single Scene accepting DVD-level fields; no `groupByURL` added here |

## 4. Next independent capture & research-only XPath replay

The independent, read-only helper `tools/evaluate_dvd_dom.py` evaluates actual XPath and outputs sanitized cardinality and values from given **local HTML snapshots**. It does not access Stash or initiate network traffic.

Run from repo root (on a machine with `lxml`, and **after obtaining the public pages lawfully in an isolated browser without user accounts/cookies**):

```bash
python -m pip install lxml
python docs/research/wave2e/tools/evaluate_dvd_dom.py \
  tests/fixtures/bravo/dvd-281.html \
  tests/fixtures/bravo/dvd-046.html \
  tests/fixtures/bravo/dvd-173.html \
  tests/fixtures/bravo/dvd-215.html \
  tests/fixtures/bravo/failure-cloudflare.html \
  --output /tmp/bravo-dvd-historical-xpath.json

# Separately capture complete anonymous rendered DOM using an authorized local
# browser/CDP environment. Keep raw material private. Inspect & sanitize first.
python docs/research/wave2e/tools/evaluate_dvd_dom.py \
  /private/bravo-dvd-234.sanitized-rendered.html \
  /private/bravo-dvd-084.sanitized-rendered.html \
  --output /tmp/bravo-dvd-primary-xpath.json
```

The replay tool is not evidence of a live capture, and its synthetic smoke test is not site evidence. Explicitly record `NOT_RUN` for XPath until actual pinned HTML is loaded under the script. Before publishing evidence, independently check that page/source and resulting JSON contain no session material, auth URLs, browser storage, credentials, private IDs, or token values. Do not copy unreviewed raw HTML into GitHub.

**Hard stop for Agent F:** Require completed current 234 and 084 DOM, HTTP/navigation & canonical proof, verified XPath values/cardinality including negative cases, and clear product-vs-scene semantics. `HANDOFF_STATUS=BLOCKED` until those conditions are met. Existing Draft PR #93 remains unmerged and no production scraper file is changed by Agent A.

## 5. Structured handoff override

```yaml
ASSIGNMENT_ID: WAVE2E-A-DVD-DOM-20261102
WORKSTREAM_ID: WS-2E-10
AGENT_ROLE: Agent A
ASSIGNMENT_STATUS: IN_PROGRESS_BLOCKED
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: research/e2e-bravo-dvd-dom
HEAD_SHA: "RESOLVE_GITHUB_REF_AFTER_COMMIT"
CHANGED_FILES:
  - docs/research/wave2e/WAVE2E-A-DVD-DOM-REPORT.md
  - docs/research/wave2e/WAVE2E-A-DVD-DOM-AUDIT-ADDENDUM.md
  - docs/research/wave2e/evidence/historical-dom-structural-audit.json
  - docs/research/wave2e/tools/evaluate_dvd_dom.py
DELIVERABLES:
  - "Audited six original sanitized SHA-256 evidence records: 6/6 match"
  - "Independent historical DOM field/heading comparison: four pinned pages"
  - "Explicit evidence corrections and research-only offline XPath replay script"
EVIDENCE:
  - "Pinned historical full rendered HTML: 281,046,173,215 (2026-10-14 only)"
  - "Previously committed 234/084 text captures (NOT complete rendered DOM)"
  - "DVD 084 two file hashes differ but product-text body bytes match"
TEST_RESULTS:
  - "Existing evidence SHA-256: PASS 6/6"
  - "Historical DOM static structural inspection: PASS 4/4"
  - "Research XPath replay helper: SYNTHETIC_SMOKE_ONLY; live/pinned full XPath NOT_RUN in this session"
  - "Primary rendered DOM/CDP HTTP capture: NOT_RUN (network/cache/DNS unavailable)"
KNOWN_LIMITATIONS:
  - "234/084 live complete rendered DOM and HTTP/CDP data not accessible"
  - "Current primary XPath cardinality unresolved"
  - "Studio vs Label and DVD vs Stash Scene semantics unresolved"
DEPENDENCIES:
  - "Agent F: DVD implementation and integration"
  - "Independent public-only DOM capture & XPath review"
RISKS_AND_DECISIONS:
  - "Do not infer source fields from URL or common site keywords"
  - "Do not accept unverified cover, studio, performer, or single-scene duration"
  - "No BRAVO.yml, Clips tests, historical fixtures, archived digest, stash-test, or production edits"
HANDOFF_STATUS: BLOCKED
```
