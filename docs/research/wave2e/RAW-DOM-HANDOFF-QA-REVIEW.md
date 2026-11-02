# Wave 2E — Independent Review of Raw-DOM Handoff (Agent A, WS-2E-10)

- Audit UTC: `2026-11-02T10:11:29.413Z`
- Assignment: `WAVE2E-A-DVD-DOM-20261102`
- Reviewed commit: `16224b4039e05b3acc675a219066cfd88172db80`
- Baseline main: `4bbafca9cf7b5d67117ac41136e74a303c28e4f4`
- Source: [RAW-DOM-VERIFICATION-ADDENDUM.md](RAW-DOM-VERIFICATION-ADDENDUM.md) (concurrent Agent A report)
- **Independent acceptance:** `CHANGES_REQUESTED` for independently reproducible *source evidence*. This is **not** a finding that the other Agent A fabricated data. It means the private captures and per-node evaluator outputs were not available to this reviewer. Author's `READY` claim is recorded, not silently overwritten.

## 1. New handoff received; reconcile with earlier BLOCKED review

A concurrent Agent A commit added an addendum reporting **11 CDP rendered-HTML captures** (nine real DVD pages 234,084,281,046,377,383,384,304,315 and two 404-like negatives 00/999999), timestamped 2026-11-02 09:57–10:03 UTC with distinct SHA-256 values. It reports lxml XPath cardinality=1 for Title/Code/URL/Details/Image/Date/Studio/Duration in all nine products and 22 h2 on each product page. This is materially stronger evidence than the earlier text-only report and resolves the old DVD 046 positional-selector disagreement **if its raw input and evaluator output can be checked**.

The historical 2026-10-14 complete DOM blobs independently inspected in [historical-dom-structural-audit.json](evidence/historical-dom-structural-audit.json) support the same 22-h2 layout and old `preceding::h2[2]` producing actual product titles on 281/046/173/215. They do **not** independently establish today's nine-page results or prove the raw SHA values.

**Direct independent website revisit here:** public URL fetch returned cache miss, and shell DNS could not resolve the BRAVO host. These failures are local inspection limitations, not BRAVO HTTP 404/challenge evidence. No access to the private raw-DOM workspace, archived CDP logs, or lxml JSON output was available in this session.

## 2. Evidence-contract items still necessary before an independent READY verdict

| Requirement | Available now | Acceptance item to provide |
| --- | --- | --- |
| 234 & 084 completed rendered DOM | Private captures claimed with timestamps & SHA-256; no sanitized DOM or node traces committed in research branch | Sanitized page DOM structural excerpts preserving exact XPath node ancestry/adjacency, canonical and title/Code, per-input SHA references, with privacy review; private source accessible to an authorized independent reviewer |
| HTTP / navigation evidence | Two pages called 404 by HTML `title` and `og:title`; no navigation HTTP code or redirected URL in addendum | HTTP status / final URL / redirect chain, CDP ready condition and timestamp for each capture; `404 page` versus `HTTP 404` explicitly distinguished |
| XPath cardinality and value | Per-field table says 9/9 =1 but no machine-readable per-page evaluator output or raw node evidence | Sanitized `xpath-evaluation-results.json`: XPath, node/value, n, page ID, source SHA; missing optional and 404 n=0/empty |
| Image | Per-page nonempty Wix image selector reported, including `BR-084soldout.jpg` | Media asset identity / alt / exact product container & negative case with **valid DVD but no cover** or unrelated logo; sold-out artwork decision by controller |
| Details 084 | `p.font_8` reportedly n=1 and content empty | Confirm empty value and behavior of scraper when empty (do not scrape price/status/nearby product as Details) |
| Studio | XPath retrieves `レーベル` values | Explicit semantic decision whether Stash Studio may be populated with DVD label; source extraction and target-field equivalence are distinct claims |
| Duration | DVD total minutes | Explicit decision: whole DVD becomes one Stash Scene or metadata is deliberately omitted for per-scene records; never silently claim single-scene duration |
| Tags/Performers | Site keywords common to all; cast unstructured | Omit both unless source-specific verified evidence exists |
| CDP requirement | Five pre-render SSR pages reportedly lack product data | SSR SHA list, before/after product-marker counts and CDP version, then verify effective Stash driver independently |
| Source integrity | 11 raw HTML SHA-256 listed in document | A manifest that links each digest to source filename, capture timestamps, navigation status, sanitizer version and lxml output; no credentials committed |

No file from the other Agent A was modified or overwritten by this independent audit. The sources with session material **must remain private**; it is acceptable to provide only privacy-reviewed structural excerpts publicly while allowing authorized Agent F access to originals.

## 3. Selector robustness and false-positive gates

- The 9-page result reportedly supports `//h2[contains(.,'品番')]/preceding::h2[2]` and `following::h2[1]`, including `046`. This supports a **provisional** selector proposal, not guaranteed resilience to a deleted empty subtitle node, inserted unrelated heading, wrong product container, duplicate `品番`, or future redesign. Include synthetic negative regression on each.
- `//img[@alt!='' and contains(@src,'wixstatic')]/@src` may be n=1 on nine current products and n=0 on two 404 pages yet still mis-select when a **valid product's** image is absent while a branded/logo image remains. It must not automatically accept sold-out artwork as an actual cover.
- `//link[@rel='canonical']/@href` is reportedly populated even on the 404 page. Product validity cannot rely on canonical alone. `品番` present is a necessary but not always sufficient signal; Gate B should also reject challenge/404 title, require nonempty Title and Code, and verify Code/canonical identity **without inventing values**.
- `Studio` and `Duration` require *semantic* acceptance, not just XPath count. `Tags` from site-generic meta keywords should remain absent, and unstructured description names must not automatically become Performers.
- No `groupByURL`, no production BRAVO YAML change, and no Stash environment access from this workstream.

## 4. Reproduction tools

- `tools/evaluate_dvd_dom.py` — offline XPath evaluator for historical or privately sanitized DOM; it does not capture web content.
- `tools/capture_public_dvd_dom.py` — isolated, **public BRAVO-only**, anonymous Playwright capture; records status/redirect/canonical, creates privacy-review-required structural HTML, SHA-256, and a private manifest. Each URL receives a fresh isolated browser context. Source HTML is processed in memory; source capture files are never automatically published. Script's sanitizer/identity and Python syntax tests passed only on **synthetic** HTML, and **no live capture** was performed in this audit.

Run only in authorized independent environment (not `stash-test`):

```bash
python -m pip install playwright lxml
python -m playwright install chromium
python docs/research/wave2e/tools/capture_public_dvd_dom.py \
  --private-output /private/bravo-wave2e-a \
  https://www.bravo-japan.com/dvds/234 \
  https://www.bravo-japan.com/dvds/084
python docs/research/wave2e/tools/evaluate_dvd_dom.py \
  /private/bravo-wave2e-a/dvd-234.sanitized-rendered.html \
  /private/bravo-wave2e-a/dvd-084.sanitized-rendered.html \
  --output /private/bravo-wave2e-a/xpath-evaluation-results.private.json
```

Inspect outputs for session material and accidental third-party data before any GitHub upload. The capture tool is independent from Stash's effective CDP driver; its success alone does not certify Gate B. Full raw DOM remains restricted, per assignment.

## 5. Gate verdict / Agent F handoff

- **Source Agent A addendum verdict:** `READY` (author's assertion, new 11-capture research).
- **Independent evidence-verifiability verdict:** `CHANGES_REQUESTED` (sanitized DOM traces, real evaluator outputs and HTTP/CDP provenance not independently accessible).
- **Agent F immediate permitted use:** review provisional candidate selectors, design test fixtures and decide DVD product-vs-Scene mapping; **do not treat the private capture summary as an independently signed release gate**.
- **Release gate:** still requires accepted Clips baseline (PR #93 remains Draft), exact-head offline checks, and independent authorized `stash-test` QA with exclusive lease. This audit does not authorize merging or environment modification.

```yaml
ASSIGNMENT_ID: WAVE2E-A-DVD-DOM-20261102
WORKSTREAM_ID: WS-2E-10
AGENT_ROLE: Agent A
ASSIGNMENT_STATUS: EVIDENCE_RECONCILIATION_PENDING
BASE_SHA: "4bbafca9cf7b5d67117ac41136e74a303c28e4f4"
BRANCH: research/e2e-bravo-dvd-dom
HEAD_SHA: "RESOLVE_BRANCH_REF_AFTER_COMMIT"
CHANGED_FILES:
  - docs/research/wave2e/RAW-DOM-HANDOFF-QA-REVIEW.md
  - docs/research/wave2e/tools/capture_public_dvd_dom.py
DELIVERABLES:
  - "Independent review of concurrent raw DOM verification claims"
  - "Public-only isolated DOM capture and private manifest script"
EVIDENCE:
  - "11 CDP source capture SHA-256 values claimed in existing RAW-DOM-VERIFICATION-ADDENDUM.md, not independently checked here"
  - "Historical four full rendered DOM source blobs independently inspected (2026-10-14)"
TEST_RESULTS:
  - "Public capture script: PY_COMPILE + SYNTHETIC_SANITIZER_IDENTITY_PASS"
  - "This audit's live URL fetch: CACHE_MISS; shell DNS: RESOLUTION_FAILED"
  - "Raw DOM hash verification + exact XPath 9-page run: NOT_INDEPENDENTLY_RUN"
KNOWN_LIMITATIONS:
  - "Source CDP capture files and per-page XPath evaluation outputs remain private/unavailable for independent QA"
  - "084 sold-out image, label to Studio, and DVD total duration to Scene semantics need decisions"
DEPENDENCIES:
  - "Agent F: DVD implementation and integration"
  - "Independent authorized raw-DOM evidence reviewer / controller"
RISKS_AND_DECISIONS:
  - "Do not overwrite concurrent Agent A report or raw source files"
  - "Require negative test with valid DVD lacking product image"
HANDOFF_STATUS: CHANGES_REQUESTED
```
