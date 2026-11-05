---
doc_id: PR93-LEASE03-PROXY-PUBLIC-EVIDENCE-RECHECK-20261105
title: PR #93 Lease-03 Proxy — independent verification after source branch publication
status: evidence_verified_with_binary_custody_and_publication_security_gaps
layer: qa
owner: controller
audience: [maintainer, agent, auditor]
last_verified: "2026-11-05"
authority: controller_historical_erratum
supersedes_custody_assertions_in:
  - PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105.md
  - PR93-LEASE03-PROXY-EVIDENCE-CUSTODY-20261105.md
  - PR93-LEASE03-PROXY-HISTORICAL-HANDOFF-20261105.yaml
---

# PR #93 Lease-03 Proxy — 公開證據重查與歷史歸檔更正

**Recheck ID:** `PR93-LEASE03-PROXY-PUBLIC-RECHECK-20261105`  
**Rechecked source:** `docs/qa-pr93-gateb-proxy-20261103@80f53073384214da2db902038b3e49c805a110bf`.  
**Old historical candidate:** `ce7ef6c8f5c5663f41295e92a0603bca486abe98`; **old contract:** Clips Duration = **1800**.  
**Verdict remains:** **`GATE_B_FAIL / BASELINE_BLOCKED_LIVE_QA`** for that *exact old candidate and contract*.  
**Current G0 remains:** **`ACCEPTED_CLOSED`** at `88d27a5` (Duration omission contract), merged as `ff236c9e91e27321e93f59d2bf12488db714dfc7`.

## 1. Correction of previous evidence-custody statement

The original Controller historical archive was created before discovering the dedicated, now-public [Proxy QA source branch](https://github.com/daniel-yfc/stash-scarpers/tree/docs/qa-pr93-gateb-proxy-20261103). Accordingly, its statements that the Proxy-specific `MANIFEST-LIVE` and original 56 files were *not in public GitHub* **are outdated**.

The dedicated branch contains:

- [Proxy execution report](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-proxy-20261103/docs/qa/PR93-GATEB-PROXY-REPORT-20261103.md).
- [Agent D's independent verdict](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-proxy-20261103/docs/qa/PR93-GATEB-PROXY-VERDICT-20261105.md).
- [Proxy handoff](https://github.com/daniel-yfc/stash-scarpers/blob/docs/qa-pr93-gateb-proxy-20261103/docs/qa/PR93-GATEB-PROXY-HANDOFF-20261104.yaml) and lease-03 record.
- `docs/qa/evidence/pr93-gateb-proxy-20261103/MANIFEST-LIVE.sha256` and **all 56 manifest-referenced files**, including B0–B6, ROLLBACK, four scripts and **two complete page-HTML files**.

### Exact re-verification performed by Controller

The Controller fetched the committed `MANIFEST-LIVE.sha256` and **all 56 GitHub-hosted UTF-8 source files**, independently re-encoded the fetched contents as UTF-8, computed SHA-256 and compared each digest with the original manifest entry.

| Scope | Observed result |
| --- | --- |
| Manifest paths | **56 entries** |
| Independently fetched paths | **56/56 present** |
| Independently recalculated SHA-256 | **56/56 MATCH**; **0 mismatch** |
| Full page HTML 282 | **881,400 bytes**, SHA-256 MATCH |
| Full page HTML 284 | **880,884 bytes**, SHA-256 MATCH |
| Proxy original *sealed evidence ZIP* | **NOT AVAILABLE IN THE CHECKED PUBLIC BRANCH**; 836,389 bytes / 67 ZIP entries are **Agent D reported**, **not** re-counted from the ZIP by Controller |
| `pkgbuild/BRAVO.zip` binary | **NOT AVAILABLE IN THE CHECKED PUBLIC BRANCH**; hash `cdb9d2c57ea549c9167e683f1f56dcfadcd8ad4fb672d8c496f48c5fb938de78` is recorded in public B0 text and matches the independent historical v3 report, but **no direct rehash of the binary** |

**Do not conflate** the now-verified **56 public source files** with the absent **sealed evidence ZIP** or absent **BRAVO.zip** binary. This recheck verifies the contents currently committed in GitHub against the committed manifest; it does not independently prove original archive bytes, original ZIP entry count or prior custody history.

## 2. Independent cross-check of original GraphQL evidence

The Controller separately fetched **six B1/B2 original GraphQL responses** (282/284 × 3), B5 QueryFragment 284, the B4 invalid 999999 response, B0 installed-package record and B6 control summary.

| Observation | Controller check |
| --- | --- |
| Clips 284 ×3, Clips 282 ×3 | Code, non-empty Title, matching canonical and non-empty product-specific Details all present |
| Details character count | **61** for 284, **65** for 282 in every trial |
| U+200B in Details | **ABSENT** in all six raw responses |
| Duration | **null 6/6**; B5 QF path also **null** |
| Image | null in all six positive response cases |
| 999999 invalid case | Title/Code/Details/Duration/Image null, but **one canonical URL and nine site-generic Tags** are returned; **not an all-fields-empty response** |
| B0 installed packages | **21** entries; installed candidate revision `ce7ef6c` present in record |
| QueryFragment 284 | Correct core Code/Title/Details but Duration null |
| B6 control | Published control summary and the **original raw GraphQL response** contain the reported KOShop Title and Code; independently checked |
| B3 page-HTML no-poster branch | Both full page HTML documents contain **2 video elements each and neither has a poster attribute**; **poster-present remains UNVERIFIED_BRANCH** and no CDP-rendered DOM equivalence is claimed |
| Rollback | `restoration-comparison.json` independently read; **all five equality flags true**. The stored before/after Scene-stats JSON have the same Git blob SHA. Historical log verification only, not a new Stash environment check |

The original Proxy Agent D verdict therefore now has independent, direct published-file corroboration rather than relying solely on the author's summary.

## 3. Public-repository sensitivity concern — separate from Gate B

**Security/privacy review required before promoting or reusing the Proxy evidence branch.** The source branch currently includes two **complete page HTML** files (direct page-HTML fallback, **not** a verified CDP-rendered DOM capture) (around 881 KB each), rather than only digests. In a targeted scan of 15 likely-sensitive files, the Controller also located a **plain internal tailnet/CDP endpoint** in the Proxy handoff, run log and rollback log, and session/cookie-related *terms* within the HTML.

- This **does not prove an exposed live credential**; the scan found **no clear populated bearer/api-key credential in the selected files**. A keyword scan is **not** a complete secret/sanitization audit.
- Raw HTML may embed visitor/session identifiers or sensitive runtime state; inspect with an authorized security reviewer. **Do not copy full HTML, credentials, internal addresses or session-bearing logs into this correction document or comments.**
- If actual sensitive values are confirmed in the public branch, merely deleting files in a later commit does **not erase them from public Git history**; remediation requires repository/host-specific history and exposure handling, coordinated with the maintainer.
- Until security review completes, **do not merge or re-publish the raw evidence wholesale**. The independently verified public-file SHA values may remain useful without copying original contents.

This disclosure concern is **not** a new functional Gate B failure for the historical candidate. It is a separate evidence-publication governance risk.

## 4. Version and decision boundary unchanged

1. **`ce7ef6c` / pre-defer Duration = 1800:** **`GATE_B_FAIL`** because live Duration was null. DEF-02 Details CLOSED.
2. **Poster-present path:** **`UNVERIFIED_BRANCH`**; no-poster observations do not demonstrate poster-present success.
3. **B4 invalid page:** Core identity fields absent, but URLs and Tags nonempty — do not call this a fully empty result or use it to claim universal fail-closed.
4. **`88d27a5` / revised omission contract:** **`GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`**. Original DEF-01 technology defect is deferred, not repaired.
5. **PR #93 G0:** **`ACCEPTED_CLOSED`**, ordinary merge `ff236c9`. The old FAIL cannot override the later acceptance.
6. **PR #104 DVD runtime:** This Lease-03 audit is *not* its Gate B result. No merge, deployment or environment action is authorized by this archival recheck.

**Corrected archival status:**  
`PUBLIC_PROXY_MANIFEST_56_OF_56_INDEPENDENTLY_REHASHED / ORIGINAL_ZIP_BINARY_NOT_REVERIFIED / PUBLICATION_SECURITY_REVIEW_REQUIRED / HISTORICAL_GATE_B_FAIL_OLD_CONTRACT_UNCHANGED / G0_ACCEPTED_UNAFFECTED`.

**Audit precedence:** This file supersedes *only the outdated evidence availability/custody statements* in the earlier historical archive; all earlier dated records and QA verdicts remain preserved.
