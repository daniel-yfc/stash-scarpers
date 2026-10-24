---
doc_id: DOC-E2E-83
title: Stash E2E Evidence Validation and Pilot Gate
status: active
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - testing
last_verified: "2026-10-24"
authority: informational
routing:
  intents:
    - stash-e2e
    - evidence-validation
    - release-readiness
---

# Stash E2E Evidence Contract and Pilot Gate

This document implements the evidence acceptance layer for **[Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) WS7**.
Its companion runtime runner is introduced in **[PR #84](https://github.com/daniel-yfc/stash-scarpers/pull/84)**.
The evidence checker is independent from the Stash server and may run offline.

## What this does (and does not) prove

A GitHub CI pass confirms only that the **checker and its mock tests** pass.
It does *not* execute Stash, connect to Tailscale, validate a real login, save any
media record, or verify that the deployed scraper YAML matches the checkout.

| Stage | Required proof | Automated by this checker |
| --- | --- | --- |
| Loader (L1) | Stash version and installed scraper inventory | Validates submitted Agent report shape only |
| Extraction (L2) | Actual GraphQL/API or UI post-processing assertions | Validates per-field status and evidence digest only |
| Persistence (L3) | Isolated **Test Stash** write → read-back → repeat/rollback | Requires supervised UI evidence with digest and PASS |
| Production readiness | Release-wide coverage, authorization, risk review | **Never automatically asserted** |

All reports must declare `production_ready: false`. `pilot_gate: PASS`
means that the **two-case Trance pilot** is sufficiently documented for
maintainer review, not that all sites are production-certified.

## Report types

- `AGENT_API`: output of `tools/stash-e2e.mjs` from PR #84.
  Fixed `mode: inventory|golden|search`; `persistence: UNVERIFIED`.
  A `PASS` on the inventory report is **loader only**.
- `HUMAN_UI` / `AGENT_UI`: supervised Stash UI test result, with
  `mode: manual` and `proof_scope: HUMAN_VERIFIED`.
  Each case has six explicit checks:
  `loader`, `extraction`, `postprocess`, `source_truth`,
  `identity` and `persistence`.

A manual case marked `PASS` must have:

1. Loader, extraction, postprocess and source truth **PASS**.
2. Identity check PASS or `NOT_APPLICABLE` (for Trance 40625, identity
   is mandatory for the pilot).
3. A real `evidence_sha256` of a sanitized, privately retained artifact.
4. Explicit disposition of persistence (PASS or NOT_APPLICABLE).
5. An exact 40-character repository commit and Stash version in the report.

The checker deliberately **does not trust or independently reconstruct**
the source truth from boolean attestations. Reviewers must inspect the
private redacted evidence artifact and confirm that the Stash installation
uses the matching YAML. Never put full HTML, cookies, private account
names, API keys, unsanitized screenshots or LAN addresses into Git.

## Validating a report

```bash
# A future authorized Agent/API run, kept in a private directory:
node tools/check_stash_e2e_evidence.mjs \
  --report=/private/reports/e2e-results.json

# Human can copy this incomplete template, then replace every field
# using actual observed values and private evidence:
cp tests/e2e/manual-evidence.example.json /private/reports/manual-e2e.json
node tools/check_stash_e2e_evidence.mjs \
  --report=/private/reports/manual-e2e.json

# Two Trance cases + manual Test Stash persistence evidence are required.
node tools/check_stash_e2e_evidence.mjs --pilot-gate \
  --report=/private/reports/e2e-results.json \
  --report=/private/reports/manual-e2e.json
```

An incomplete template can pass **schema validation** while the pilot
gate returns `NOT_READY`. The checker uses these outcomes:

- Exit **0**: syntactically valid reports, or `--pilot-gate` passed.
- Exit **1**: reports structurally valid, but the Trance pilot remains NOT_READY.
- Exit **2**: invalid schema, unsupported fields, bad statuses, unsafe
  claims, or unreadable report.

For the pilot, both `E2E-TRANCE-40625` and `E2E-TRANCE-40641` must be
confirmed by supervised UI reports. The first additionally requires a
PASS for Performer identity. At least one case must include authorized
Test Instance persistence verification. Every submitted report must
describe the **same** commit, Stash version, and Test environment and
must not have unaddressed FAIL/BLOCKED cases.

One manually performed end-to-end test is allowed, without an Agent report,
provided its actual UI values, deployed YAML and evidence have been reviewed.

## Privacy and evidence provenance

The validator rejects unknown object keys rather than persisting accidental
headers, cookies, raw GraphQL payloads, or local paths. Diagnostic errors
never print invalid report contents. Even valid SHA-256 values are
fingerprints of artifacts, **not** proof that an artifact is authentic.
Store original evidence privately and audit it in a separate reviewer step.

Use a separate Test Stash database and media library for writes. On
Production, persistence must always be `NOT_APPLICABLE`. A Production
report can be schema-validated but is never eligible for the Test pilot.

## Still unfinished after this PR

- Authorized Cloud Codex/other agent Tailscale onboarding and actual Stash instance access.
- Live Trance golden test run (version and installed YAML proven).
- Test Stash persistence/repeat/readback evidence.
- CDP/login tests and all-site runtime coverage.
- Separate release-wide gate; this is **pilot-level** only.
