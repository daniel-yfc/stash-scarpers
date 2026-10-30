---
doc_id: DOC-E2E-82
title: Authorized Stash Runtime E2E Runbook
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
    - runtime-verification
    - graphql
---

# Authorized Stash Runtime E2E Runbook

This runbook implements **WS7 / [Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80)**.
It supports cloud agents that can actually reach an authorized Stash server across a
Tailscale tailnet, local agents, and humans using the Stash UI. It does **not**
assert that cloud-hosted CI has access to a LAN/Tailscale instance.

## Proof boundaries

| Proof | Method | Claim |
| --- | --- | --- |
| Schema/fixtures | Existing offline repository CI | **Not** a Stash runtime PASS |
| Loader | Read-only GraphQL `version` + `listScrapers` | Instance is reachable and scraper entries were loaded |
| Live extraction | Stash `scrapeSceneURL` or `scrapeSingleScene` | Actual Stash scraper and postProcess values verified |
| Persistence | Human or separately authorized test agent writes to **test-only** DB; read-back/rollback | Stash stores and re-reads results |
| Production | Read-only preview with approved network/API permissions | Never implies permission to save or mutate metadata |

The script in this change provides **loader, direct URL and name→selected-detail
extraction only**. Persistence, image content and authorized CDP/login tests
remain supervised/manual until separate signed-off executor support is built.
A loaded scraper does not prove that its external website is reachable.

## Preflight

1. Work from a pinned complete Git commit. Confirm that that exact YAML has
   been installed into Stash's active Scrapers folder; reload via
   Settings → Metadata Providers → Scrapers, then check `listScrapers`.
   **Do not trigger GraphQL `reloadScrapers` against Production**.
2. Record the installed Stash version. The current harness schema targets
   **v0.31.1**; other versions require explicit review and a pinned
   `--expected-version=` argument.
3. Select **test** or **production** explicitly. Use a separate Test Stash DB,
   media library, permissions and Tailscale identity for all write tests.
4. Connect the authorized agent to the Tailnet through its actual runtime
   (e.g. a permitted Tailscale client or approved gateway). GitHub access
   alone is not a LAN access entitlement. Configure tailnet ACLs so the
   agent reaches only the intended Stash endpoint.
5. Supply the credential via environment secret injection, **not** CLI flags,
   tracked `.env` files, issue comments, CI logs, shell history or PR text.
   Prefer HTTPS (e.g. Tailscale Serve) and a dedicated, limited Stash API key
   or server-side GraphQL operation allowlist when available. Tailnet ACLs
   alone do not prevent GraphQL mutations.
6. Never send credentials in any evidence. The harness only sends three
   hard-coded GraphQL **Query** operations. It cannot create, update or
   delete a Stash record.

### Run with an authorized agent

The following assumes the agent has the repo checkout, Node version from
`.nvmrc`, a reachable Stash instance and secret injection already configured:

```bash
export STASH_BASE_URL="https://your-stash-tailnet-endpoint"
# Set STASH_API_KEY securely in the agent's secret manager, not in this script.
export STASH_COMMIT_SHA="$(git rev-parse HEAD)"

# Safe first step: no third-party scrape is performed.
node tools/stash-e2e.mjs --env=test --mode=inventory \
  --report=/tmp/stash-e2e-inventory.json

# Real scraper runtime calls (explicit --live):
node tools/stash-e2e.mjs --env=test --mode=golden --live \
  --report=/tmp/stash-e2e-trance.json

# Optional search → choose exact URL → detail handoff.
node tools/stash-e2e.mjs --env=test --mode=search --live \
  --report=/tmp/stash-e2e-trance-search.json
```

The runner creates a report with permissions `0600`, refuses to overwrite
an existing report, outputs only aggregate status and case IDs, and never
prints raw GraphQL responses, image data or HTTP bodies. Report fields include
a SHA-256 digest of selected result data and individual expected-field
booleans; the digest is not independently a proof of source truth.

For a Tailscale IP / self-hosted HTTP endpoint, only if transport and ACLs
have been explicitly accepted by the operator, set
`STASH_ALLOW_PRIVATE_HTTP=1`. Default is HTTPS or local loopback HTTP.
Never use URL userinfo (`user:password@host`) or GraphQL API keys in URLs.

### Production: explicit read-only authorization

```bash
node tools/stash-e2e.mjs --env=production --mode=inventory \
  --allow-production-read --report=/tmp/stash-e2e-prod-inventory.json
```

Run live production previews only if approved and rate-limited. The flag is
an **operator acknowledgment**, not server-side enforcement. The harness
never sends mutations, but an authenticated GraphQL endpoint may allow them
to *other* clients. Restrict Production access using a gateway with a
GraphQL query-operation allowlist and segregated credentials.

### Golden Cases (actual Stash runtime required)

`tests/e2e/stash-golden.json` is the pinned **expected** value set derived
from committed HTML fixtures. These are *not* actual live outcomes:

| Test ID | Source | Expected Code | Expected Date | Duration (seconds) |
| --- | --- | --- | --- | --- |
| E2E-TRANCE-40625 | /product/detail/40625 | TR-16-0028-01 | 2026-06-25 | 1545 |
| E2E-TRANCE-40641 | /product/detail/40641 | TC-05-0013-01 | 2026-10-08 | 1167 |

40625 additionally requires distinct performer URL identities
`model%5B%5D=210` and `model%5B%5D=212`.
40641 carries an optional source-language Name Search probe. The harness
performs **exact candidate URL selection**; a missing, ambiguous or changed
search result is FAIL rather than silently choosing the first result.

If the live source has changed since the snapshot, record the discrepancy
as FAIL/UNVERIFIED pending review. Do not rewrite expected values just to
make a failing test pass.

## Human-operated UI / CDP / Persistence test

The user can follow the *same* Golden Cases in the Stash UI and provide
a reviewed evidence record with `executor: HUMAN_UI`:

1. Open Stash Settings → Metadata Providers and confirm the installed scraper.
2. Preview each Golden URL in the scene scraping UI. Compare **source page**
   and final post-processed Title, Code, Date, Duration, Performer URLs.
3. Search by name if supported, select the candidate, inspect the selected
   detail. Verify selected and final works refer to the same product.
4. Inspect at least one **negative** case: no-result search, missing optional
   field, 404, bot/login gate, unrelated numeric fragment, or same-name
   performer identity. Distinguish `BLOCKED`, `FAIL`, `UNVERIFIED`.
5. If a site requires CDP, open a **visible, authorized** Chrome browser
   with a separate profile. Complete legitimate site login manually; never
   export browser cookies or bypass site access restrictions. Record whether
   the tested instance attached successfully.
6. Only on an **isolated Test Stash**, select a seeded/test-media scene and
   explicitly authorize a metadata save. Before and after the save, record
   its selected fields, re-read it, and repeat the test to detect unexpected
   duplicates. Keep rollback/restore available. Do **not** use Production
   for persistence or batch Identify tests.
7. Produce a sanitized record; a checked box or screenshot alone is not
   enough for a `PASS` claim.

Manual report skeleton (keep local/private until reviewed):

```json
{
  "schema_version": 1,
  "executor": "HUMAN_UI",
  "environment": "test",
  "scraper_commit": "<40-char Git SHA>",
  "stash_version": "v0.31.1",
  "executed_at": "<ISO timestamp>",
  "results": [
    {
      "id": "E2E-TRANCE-40625",
      "status": "UNVERIFIED",
      "checks": {
        "loader": "UNVERIFIED",
        "extraction": "UNVERIFIED",
        "identity": "UNVERIFIED",
        "persistence": "UNVERIFIED"
      },
      "evidence": "<sanitized private artifact reference>"
    }
  ]
}
```

For Production-only read access, mark persistence `NOT_APPLICABLE`; for
unreachable sources `BLOCKED`; never convert either to `PASS`.

## Failure classification / release control

- `PASS`: actual installed Stash executed the specific case and all
  asserted values match the source of record.
- `FAIL`: wrong or missing mappings, invalid response schema, identity
  collapse, date/duration mismatch, or wrong search-selected detail.
- `BLOCKED`: network timeout, unauthorized access or rate limits.
- `UNVERIFIED`: case not executed or supporting evidence unavailable.
- `NOT_APPLICABLE`: unsupported scraper entry point.

A `PASS` for extraction does not automatically pass persistence. The
release gate must independently require test-only read-back and
idempotency evidence for declared production workflows.

## Acceptance checklist

- [ ] Exact tested scraper commit, installed Stash version and executor recorded.
- [ ] Stash loader inventory confirms expected scraper IDs and entry points.
- [ ] Trance 40625 and 40641 live direct URL values verified.
- [ ] Performer query ID 210/212 distinction retained (40625).
- [ ] Name Search → selected detail and negative controls verified.
- [ ] Real Stash postProcess (not JSDOM-only) verified.
- [ ] Test Stash persistence, repeat-run, rollback tested separately.
- [ ] CDP/auth cases tested with consent, or clearly marked BLOCKED.
- [ ] Evidence is sanitized and cannot reveal LAN secrets, cookies or tokens.
- [ ] Live data quality and release readiness remain UNVERIFIED until evidence is reviewed.

## Official references

- [Stash GraphQL API](https://docs.stashapp.cc/api/)
- [v0.31.1 GraphQL scraper types](https://github.com/stashapp/stash/blob/v0.31.1/graphql/schema/types/scraper.graphql)
- [v0.31.1 Query operations](https://github.com/stashapp/stash/blob/v0.31.1/graphql/schema/schema.graphql)
- [Stash manual scraper installation](https://docs.stashapp.cc/metadata-sources/scrapers/)
