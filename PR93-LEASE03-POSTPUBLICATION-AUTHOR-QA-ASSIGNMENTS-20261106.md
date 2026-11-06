---
doc_id: PR93-LEASE03-POSTPUBLICATION-AUTHOR-QA-ASSIGNMENTS-20261106
date: "2026-11-06"
status: ASSIGNED_PENDING_EXECUTION
controller_decision: PR93-LEASE03-CONTROLLER-CONDITIONAL-PUBLICATION-20261106.md
approved_evidence_head: 855da215682fea92daf2daa2975fa28470cbbbf0
author_assignment: PR93-LEASE03-POSTPUBLICATION-AUTHOR-20261106
independent_qa_assignment: PR93-LEASE03-POSTPUBLICATION-INDEPENDENT-QA-20261106
merge_allowed: false
deploy_allowed: false
history_rewrite_allowed: false
---

# PR #93 Lease-03 — Post-publication author and independent QA assignments

## Scope and governing record
Repository: `daniel-yfc/stash-scarpers`.

**Source baseline**: public sanitized-evidence branch
`security/pr93-lease03-evidence-remediation-20261106@855da215682fea92daf2daa2975fa28470cbbbf0`.
Initial commit added exactly 81 files atop `main@2a00175ca77a010aeaa49dc3ef7e9572cd892559`.

Controller decision: `PR93-LEASE03-CONTROLLER-CONDITIONAL-PUBLICATION-20261106.md`.
Independent security verdict: `PR93-LEASE03-INDEPENDENT-SECURITY-QA.md`, **SECURITY_QA_PASS_WITH_NONBLOCKING_FINDINGS**, bound to the 62-item sanitized set and its `PUBLIC-SANITIZED-MANIFEST.sha256` digest `18364466539f207d597fecd86a2a29ffdc58e015b577bbd00318600809e414fd`.

**Scope fence:** This work is documentary closure of already-published sanitized evidence and independent review of the corrections. It does **not** re-open PR #93 implementation, infer a new live Gate B result, modify source scrapers, operate Stash, merge to `main`, deploy, force-push, or delete history.

### Protected evidence invariants
- Do **not** modify any of the 62 files under `sanitized/`; do **not** modify `PUBLIC-SANITIZED-MANIFEST.sha256`, reviewed mapping bytes, the two `page-html-*.html` files, or claim the original ZIP SHA for a new package.
- If any evidence bytes must change, **STOP**, report a blocker, produce a newly versioned manifest/package, and request a new independent QA assignment; old QA approval does not transfer.
- The private raw evidence branch `docs/qa-pr93-gateb-proxy-20261103@80f5307` is actually **publicly reachable**; do not assume it is confidential. Avoid amplifying raw IPs, private hostnames or share links. The file **named** `PRIVATE-RAW-MANIFEST.sha256` is already present on the public sanitized branch; the name alone does not confer privacy.

## Assignment A — Author / record implementer

**ID:** `PR93-LEASE03-POSTPUBLICATION-AUTHOR-20261106`
**Role:** documentation and evidence-custody author, not final security reviewer.
**Priority:** P0 documentation consistency; no urgent secret response currently evidenced.
**Allowed changes:** documentation-only follow-up commits on the dedicated `security/pr93-lease03-evidence-remediation-20261106` branch. A proposed follow-up to the separate archival branch must be staged for independent QA before it is published as canonical.

### A1. Fix QA-N1 (substantive record accuracy)
- Preserve the signed independent QA wording: `page-html-282.html` and `page-html-284.html` **each contain two quoted `sessionId` UUID occurrences**; QA classified these as Wix anonymous per-load viewerModel identifiers `PUBLIC_NONSECRET` after checking usage and access context.
- Create an explicit dated errata/supersession section for **every user-facing implementer document** that says “no session value exists,” especially `PR93-LEASE03-SANITIZATION-REPORT.md`, `PR93-LEASE03-SECURITY-REVIEW.md`, and `PR93-LEASE03-SECURITY-FINDINGS.yaml`. Never silently erase the original finding. Distinguish `sessionId` from svSession/member-auth cookie values. No need to reproduce either UUID.
- Make the PR #93 historical security comment's `no session value` assertion explicitly superseded by the Controller follow-up comment and link to the signed QA report.
- Do not claim that anonymous issuance alone proves universal non-authenticating behavior. If a new credible authentication-replay observation is found, escalate to Controller instead of preserving the current classification by assumption.

### A2. Fix QA-N2/N3/N4/N5 and preserve provenance
- N2: F-04 `instanceId` **19 distinct**, not 21.
- N3: F-09 long hex **216**, not 224.
- N4: state scan counts with tree labels: **raw = 399**, **sanitized = 398**; `custom-scan-findings.json` is **sanitized**. Preserve the original QA's test record; provide a *safe* count-only/provenance result for raw. The raw-tree scan output itself may contain the 6 tailnet IPs/10 share-link locations: keep its unredacted JSON in private custody and link by digest/provenance only; **never publish raw JSON without independent redaction clearance**.
- N5: fix the `custody-docs-updated/PR93-LEASE03-PROXY-HISTORICAL-REVIEW-20261105.md` X→X false transition via an explicit dated correction; no silent alteration of prior decision text. If its YAML frontmatter status never changed, say so.
- Clarify the publicly committed `PRIVATE-RAW-MANIFEST.sha256` exposure. It contains SHA-256 digests, not evidence contents, and was shipped in the public 81-file commit. Remove false claims that it was not published; any mitigation requiring removal or history edits is out of scope.

### A3. Resolve current-vs-historical status without falsifying prior records
- Add a dated “effective-state ledger” summarizing: initial implementer self-check; independent QA verdict; Controller's conditional publication; remaining fixes. Explicitly label former `PENDING_INDEPENDENT_REVIEW` / `PREPARED_LOCALLY_NOT_PUBLISHED` statements as historical at their document revision, not current.
- Maintain links to the original branch `docs/qa-pr93-gateb-proxy-20261103@80f5307`, the sanitized publication HEAD, independent QA report, Controller decision, and resulting errata commit.
- Keep historical `ce7ef6c` old-scope `GATE_B_FAIL`, `88d27a5` revised-duration-scope `GATE_B_PASS_UNDER_REVISED_DURATION_SCOPE`, and `G0_ACCEPTED_CLOSED` simultaneously and explicitly version-scoped; do not claim a re-run.

### A4. Prepare canonical archive synchronization (requires review)
- Read the existing canonical archival branch `docs/pr93-lease03-proxy-historical-review-20261105@96f71948726246f006255e4448a34da96c300ab0` and separately diff each of the three `custody-docs-updated` copies against its exact files.
- Prepare **minimal, date-stamped append-only** additions and necessary status-field changes; do not rewrite historical claims/decision lines. Cross-reference the Controller decision and independent QA.
- Show the proposed canonical archive delta to independent QA before pushing any new archival-branch commit. Do not merge or deploy.

### A5. Deliverables
1. `PR93-LEASE03-POSTPUBLICATION-ERRATA-20261106.md` — public, date-scoped corrections for N1–N5, raw-manifest naming and historical-status drift.
2. `PR93-LEASE03-POSTPUBLICATION-AUTHOR-HANDOFF.yaml` — machine-readable exact HEAD, modified files, invariant checks, remaining exceptions.
3. `PR93-LEASE03-RAW-SCAN-PROVENANCE-REDACTED-20261106.json` — counts, scanner version, source pin, hashes of private outputs as available; **no actual raw secret/IP/link values**.
4. `custody-docs-updated/` corrected, with explicit archive-diff summary and a proposed archival addendum.
5. A documented test transcript with original-bound manifest digests and a changed-file list showing **zero changes to `sanitized/**` and the public manifest**.

**A acceptance**: all QA-N1–N5 wording corrected or appended as errata; no new sensitive public bytes; no old approval bound to changed evidence; only safe metadata and records changed.

## Assignment S — Independent post-publication Security QA

**ID:** `PR93-LEASE03-POSTPUBLICATION-INDEPENDENT-QA-20261106`
**Role:** reviewer independent of Assignment A.
**Start condition:** author submits exact commit SHA and A1–A5 handoff.
**Priority:** P0, blocker to “publication closed”; cannot be self-signed by the author.

### S1. Re-establish provenance and test evidence freeze
- Fetch the original publication commit `855da215682fea92daf2daa2975fa28470cbbbf0` and the author's new exact HEAD; check every change via Git diff.
- **Pass only if** all 62 `sanitized/` bytes, `PUBLIC-SANITIZED-MANIFEST.sha256`, and original published mapping are unchanged; verify all 62 sanitized manifest entries against the release as necessary. Recompute at least key file hashes, including both Page HTMLs.
- Do not assert verification of the signed reviewed ZIP `b0fd77315a8a2921b349abb8448a413b1f8a4a5ebc6d0de8131cab28246414dc` unless its actual binary bytes have been independently obtained.

### S2. Red-team the documentation and leak surface
- Verify N1 classification and wording against the two Page HTMLs: real UUID *values* exist; inspect whether the available source shows cookie/bearer use, without attempting active replay against a real service. Absence of observed auth use is a scoped conclusion, not a guarantee.
- Independently recalculate N2=19 distinct, N3=216, and N4=399 raw / 398 sanitized or explicitly mark any tool/path differences. Confirm no unredacted raw-scan JSON or infrastructure endpoint/share URL was accidentally published.
- Check N5 as a strict three-way review: original archival record, revised copy, new dated addendum. No false X→X transition and no erasure of old version-bound verdicts.
- Confirm explicitly that `PRIVATE-RAW-MANIFEST.sha256` is public, and assess whether metadata-only release causes any new sensitive exposure. Escalate if new facts warrant reclassification.

### S3. Result and decision
- Sign one of: `POSTPUBLICATION_QA_PASS_CORRECTIONS_CLOSED`, `POSTPUBLICATION_QA_PASS_WITH_FINDINGS`, or `POSTPUBLICATION_QA_FAIL`.
- Include exact author HEAD, test commands and independently computed hashes, a N1–N5 closure matrix, a full public-changed-files inventory, and a separate list of open binary-custody and poster-present gaps.
- Recommend whether the canonical archival update can be applied; if yes, bind that recommendation to the exact reviewed archive patch/commit and require subsequent readback. **QA approval alone does not permit merge, deploy, history rewrite, or modify evidence bytes.**
- Deliver: `PR93-LEASE03-POSTPUBLICATION-INDEPENDENT-QA.md`, `PR93-LEASE03-POSTPUBLICATION-QA-HANDOFF.yaml`, `PR93-LEASE03-POSTPUBLICATION-QA-TEST-RECORD.md`.

**S acceptance**: no new secret leak; no evidence-byte drift; QA-N1–N5 closed with supported sources; existing evidence custody gaps correctly remain open; exact-commit binding.

## Execution and stop conditions
**Sequence:** author documentation delta → independent QA pinned-head review → Controller closure decision and optional canonical archival application. Author may create the allowed documentation commit; pushing/merging any canonical archival branch update requires an explicit Controller closure step after the independent reviewer signs.

**STOP / escalate** on any newly confirmed credential, a `sessionId` that demonstrates access beyond anonymous permissions, unredacted raw evidence publication, any unexpected change to the 62 sanitized bytes, or an inability to establish exact source lineage. Record incident-response reconsideration only on new actionable evidence, not because a detector flags public JavaScript strings.

## Unrelated open gaps (do not auto-close)
Original sealed evidence ZIP (67 entries / 836,389 bytes), `pkgbuild/BRAVO.zip` binary and poster-present behavior remain outside this documentation QA. Their absence is a custody/functional coverage limitation, **not** a reason to rewrite historical Gate B PASS/FAIL decisions.
