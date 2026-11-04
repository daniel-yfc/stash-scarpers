# BRAVO Clips Duration — Deferred Source Specification

- Status: **DEFERRED** (not active, not a scraper, not a feature flag)
- Controller decision: `WS-2E-DEF01-DEFER-20261104` (2026-11-04)
- Source HEAD: `d6d6fbf44a4d6ecbd9f9368a07af19c41194c2d6` (PR #93)
- Reference: R3 root-cause report `PR93-DEF01-R3-TYPE-ISOLATION-REPORT.md`
  (hypothesis `GATEB-DEF01-H4-TYPE-MISMATCH`, END_TO_END_REPRODUCED)
- This file is documentation under `docs/qa/`. Stash never loads it;
  there is no active YAML field and no feature flag anywhere in this
  specification. Do not move it under `scrapers/`.

## 1. Why deferred

Source extraction is correct, but the Stash mapped runtime cannot
return a typed int for scene Duration: every mapped value is a Go
string, while `scrapedScene()` reads Duration through `IntPtr`, which
only accepts a Go `int` (string `"1800"` fails the assertion and
becomes `nil`, hence GraphQL `duration: null`). No YAML mapping can
fix that; the production `Scene.Duration` mapping was therefore
removed from `scrapers/BRAVO.yml` until the runtime capability in
section 6 is deployed. The extraction below is preserved verbatim so
restoration is a copy, not a redesign.

## 2. Original mapping (verbatim from d6d6fbf)

Selector (`clipSceneScraper.scene.Duration.selector`):

```xpath
//h2[normalize-space()='Clip']/following::h2[normalize-space(translate(., '​', '')) != '' and translate(substring(normalize-space(translate(., '​', '')), 1, 1), '0123456789', '') = ''][1]
```

Post-processing (`postProcess`, first digit group x 60, fail-closed
to empty):

```javascript
var v = value || "";
var m = v.match(/(\d+)/);
if (!m) return "";
return String(parseInt(m[1], 10) * 60);
```

## 3. U+200B handling

The `translate()` second argument in the selector is a literal single
U+200B character (UTF-8 E2 80 8B), occurring twice in the selector
(once per `translate()` call). It is invisible in a diff: do not
"clean" it away. Guards, each mandated by a regression case:

- Non-empty after translate-strip: a U+200B-only spacer heading after
  `Clip` is skipped instead of being taken as an empty value.
- Digit-start: a non-digit heading after `Clip` (for example a price
  heading) is skipped instead of being taken as minutes.

Live heading order (Gate B v3 L9): Code, `Clip`, minutes, clean
`作品TIME`, `min`. The selector anchors on the ASCII `Clip` label
and uses a forward axis only; it never references the `作品TIME`
label and never uses `preceding::`.

## 4. Expected source values and confidence

| Fixture         | Source minutes             | Future Duration seconds | Confidence                                             |
| --------------- | -------------------------- | ----------------------- | ------------------------------------------------------ |
| Clips 284       | 30                         | 1800                    | High: live L9 DOM + fixture                            |
| Clips 282       | 30                         | 1800                    | High: live L9 DOM + fixture                            |
| Clips 283       | 30                         | 1800                    | High: live spot-check + fixture                        |
| Synthetic 285   | 45                         | 2700                    | Medium: fixture-only (proves non-hardcoded conversion) |
| Price trap 287  | 30 (price heading skipped) | 1800                    | Medium: fixture-only                                   |
| Spacer trap 288 | 30 (spacer skipped)        | 1800                    | Medium: fixture-only                                   |
| Missing 289     | Absent                     | Absent                  | High: fail-closed, no guessing                         |

## 5. Known false-positive conditions

- A plain-digit price heading directly after `Clip` and before the
  minutes heading would still be ambiguous for this selector; no
  such heading exists on any live page checked.
- What is NOT a risk: falling back to the Code number. Code
  precedes `Clip`, so a forward-axis selector cannot reach it;
  only a reverse-axis selector from `min` had that failure mode.
- Reverse-axis selectors (simple v2, composite v3) are NOT
  alternatives: both passed offline yet returned null live, and
  the H4 finding makes the axis question moot for production
  until the runtime is fixed.

## 6. Required Stash runtime capability

Restoration requires a Stash build in which mapped scene Duration
accepts string numerics through a strict, validated conversion
(only all-digit strings; empty, whitespace, non-numeric, decimal,
negative and overflowing inputs rejected as absent; `"0"` yields a
present zero, not absent), or an equivalent typed-int path. The
fixed build must be newer than the tested commit `9e9ad972` and
must be actually deployed on the test instance — a merged but
undeployed upstream fix does not satisfy this section.

## 7. Restoration steps

1. Confirm the section 6 capability is deployed on stash-test and
   record the exact Stash build.
2. Restore the section 2 selector and post-processing verbatim
   into `clipSceneScraper.scene.Duration` in `scrapers/BRAVO.yml`.
   Do not invent a new selector: no new XPath iteration without
   fresh evidence.
3. Restore `mappedExpect.Duration` assertions in
   `tests/fixtures/bravo/bravo-clips-fixtures.yml` from the
   section 4 table (284/282/283: `1800`; 285: `2700`; 287/288:
   `1800`; 289: absent).
4. Re-run Gate A (validator, pytest, fixture manifests, evidence,
   formatting, security) and exact-head CI on the new HEAD.
5. Independent revised-scope Gate B re-run: Clips 284/282/283 and
   QueryFragment Duration, plus Details, Title, Code, URLs, Image
   and invalid-input regressions.
6. Only after the live re-run passes may this deferral be closed;
   a waiver does not retroactively pass the earlier failed Gate B.

## 8. Version

- v1, 2026-11-04: initial deferred specification, copied verbatim
  from PR #93 HEAD `d6d6fbf`. Any change to the selector or the
  conversion requires a new version entry here and a matching
  update to the source-only tests in `tools/tests/test_bravo_clips.py`.
