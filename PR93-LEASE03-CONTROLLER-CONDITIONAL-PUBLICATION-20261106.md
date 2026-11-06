---
doc_id: PR93-LEASE03-CONTROLLER-CONDITIONAL-PUBLICATION-20261106
date: "2026-11-06"
status: CONDITIONAL_PUBLICATION_APPROVED_POSTPUBLICATION_CORRECTIONS_PENDING
assignment: PR93-LEASE03-CONTROLLER-PUBLICATION-DECISION-20261106
approved_evidence_commit: 855da215682fea92daf2daa2975fa28470cbbbf0
approved_public_branch: security/pr93-lease03-evidence-remediation-20261106
independent_qa_verdict: SECURITY_QA_PASS_WITH_NONBLOCKING_FINDINGS
merge_authorized: false
deploy_authorized: false
history_rewrite_authorized: false
---

# PR #93 Lease-03 — Controller limited publication decision (2026-11-06)

## Authority and scope
The user acting as Controller expressly authorized this evidence-publication review and permitted **conditional approval when residual risk is acceptable** on 2026-11-06. This document records the resulting Controller decision; it does not claim a cryptographic signature or approval by the independent QA reviewer. Approval is **only** for retaining the already-pushed sanitized historical-evidence branch at pinned commit `855da215682fea92daf2daa2975fa28470cbbbf0` and for making documentation-only corrections under controlled follow-up. It is not approval to merge into `main`, deploy, change Stash, alter PR #93 implementation, force-push, delete Git history, or close unrelated gates.

**Decision: `CONDITIONAL_PUBLICATION_APPROVED` / `POSTPUBLICATION_CORRECTIONS_PENDING`.**
Option A applies: keep existing Git history and publish/retain only the sanitized public evidence. The original raw historical commit remains accessible and cannot be recalled from existing clones. No confirmed credential leak was identified by the independent security review; the conclusion is based on the reviewed scope, not a guarantee that scanners find all secret material.

## Independent controller cross-check
- Repository: `daniel-yfc/stash-scarpers`. GitHub branch HEAD read back at `855da215682fea92daf2daa2975fa28470cbbbf0`. Parent: `2a00175ca77a010aeaa49dc3ef7e9572cd892559`; exactly one commit ahead; **81 added files, zero existing-file modifications or deletions** in that initial publication commit.
- Independently read back and recomputed SHA-256 for six UTF-8 files from the public commit; each matched the independent QA binding:
  - `PUBLIC-SANITIZED-MANIFEST.sha256`: `18364466539f207d597fecd86a2a29ffdc58e015b577bbd00318600809e414fd`.
  - `PRIVATE-RAW-MANIFEST.sha256`: `335a6e0aece0b3344679fdbd8bae3d68924a529346cdb2d951cefe50abbd30a5`.
  - `ORIGINAL-TO-SANITIZED-MAPPING.csv`: `aa48aa5c390f74adfe70b3faeb3c7c57e968ac5420fccfb86d454fff7b019ba5`.
  - `sanitized/docs/qa/evidence/pr93-gateb-proxy-20261103/MANIFEST-LIVE.sha256`: `d792b5f4a93782e9d4342e19ee17e9a1ed561170cecd7c130bcee71415175960`.
  - `sanitized/docs/qa/evidence/pr93-gateb-proxy-20261103/B3/page-html-282.html`: `95582b3040fc0ac43853c7c07866d212c3fd66aeb23de16a11b0c8928e664491`.
  - `sanitized/docs/qa/evidence/pr93-gateb-proxy-20261103/B3/page-html-284.html`: `02f6c134020fdaf8597efc58f869a9fd7633581a25647706028684ab6fbdfd3a`.
- This cross-check is **not** a fresh download and rehash of the QA-reviewed package ZIP (`b0fd7731…6414dc`), the original sealed evidence ZIP, or `pkgbuild/BRAVO.zip`. Independent QA's 62/62 raw + sanitized and 56/56 live-manifest checks remain the signed review result rather than being represented as a new Controller rerun.

## Authoritative corrections (supersede older implementer wording)
- **QA-N1:** Both B3 Page HTMLs contain quoted `sessionId` UUID *values* (two occurrences per page), contrary to previous `no session value` assertions. Independent QA classified these anonymous Wix viewerModel IDs as `PUBLIC_NONSECRET`, not member authentication cookies or a confirmed secret. Preserve both HTML files as reviewed and record this correction prominently; the absence of demonstrated authentication use does not by itself prove every possible use of the ID.
- **QA-N2:** `instanceId` distinct count **19**, not 21.
- **QA-N3:** long-hex hits **216**, not 224.
- **QA-N4:** original-tree custom scan **399** hits, sanitized-tree **398**; the public `custom-scan-findings.json` is for the sanitized tree. The original raw scan output is not yet part of the public evidence package; **do not upload raw findings containing unredacted infrastructure addresses or sharing URLs**. Provide a value-redacted count/provenance summary publicly and retain the immutable raw output in restricted custody.
- **QA-N5:** The historical-review addendum falsely states a status transition from X to the same X; use accurate status evolution and retain the original historical record through a clearly dated correction/addendum.
- **Additional transparency issue:** The file named `PRIVATE-RAW-MANIFEST.sha256` has **already been publicly committed**. It contains original-file digests, not original raw evidence bytes; no secret is identified in those digests. Nevertheless, no document should describe this manifest as solely private or absent from the public branch.
- Implementer reports still contain old states such as `PENDING_INDEPENDENT_REVIEW` or `PREPARED_LOCALLY_NOT_PUBLISHED`. Treat these as versioned *pre-QA snapshots*; make the independent QA report and this Controller decision the effective status, and add a visible supersession notice or errata. Do not silently rewrite the QA-reviewed package version.

## Release conditions and open gaps
1. The 62 files under `sanitized/` and the bound `PUBLIC-SANITIZED-MANIFEST.sha256` remain **byte-for-byte frozen** at the approved publication commit. A change to any bound byte requires a new manifest, a new binding, and a fresh independent security review; the original ZIP digest must never be claimed for a modified package.
2. Complete QA-N1–N5 documentation corrections, safe scan provenance, and independently verified custody status. The original `PR93-LEASE03-INDEPENDENT-SECURITY-QA.md` must remain publicly linked to the evidence and supersede outdated implementer-only findings.
3. Amend the canonical archive branch `docs/pr93-lease03-proxy-historical-review-20261105` by explicit dated, append-only addenda (and minimally necessary status fields), not by erasing previous historical decisions; maintain cross-links to the sanitized evidence and this decision.
4. The original sealed ZIP (67 entries, 836,389 bytes per prior report) and original `pkgbuild/BRAVO.zip` are **NOT_REACQUIRED / NOT_DIRECTLY_REHASHED**. Poster-present behavior remains **UNVERIFIED_BRANCH**. These are not released or closed by this security decision.
5. Historical Gate B FAIL at `ce7ef6c` under the old Duration=1800 contract, PASS at `88d27a5` under revised Duration-omission scope, and subsequent `G0_ACCEPTED_CLOSED` remain separate, version-bounded decisions.
6. No Incident Response, secret rotation, or Git history rewrite is presently authorized or required **on the reviewed evidence**. Reopen classification and approval if credible new evidence shows a replayable authentication token, protected content, or previously missed secret.

## Execution responsibility
- Author: `PR93-LEASE03-POSTPUBLICATION-AUTHOR-20261106` — document errata, custody addenda, safe scan-output provenance, stable links, no evidence-byte change.
- Independent Security QA (not the author): `PR93-LEASE03-POSTPUBLICATION-INDEPENDENT-QA-20261106` — independently review author's delta and either close corrections or retain blockers.
- The workflow contract is recorded in `PR93-LEASE03-POSTPUBLICATION-AUTHOR-QA-ASSIGNMENTS-20261106.md`. **No push of changed evidence, merge, or deploy follows automatically from either assignment.**

## Audit note
At the time of this decision there were no commit-status checks or check runs reported on the pinned publication HEAD; this is a documentation/evidence-only release, not an assertion of passing CI. The earlier PR #93 historical comments include the incorrect `no session values` statement; the PR's new Controller comment and this decision supersede that narrow claim without rewriting it.
