---
doc_id: REF-VERIFY-62
title: Verification Metadata Reference
status: active
layer: skill
owner: maintainer
audience:
  - agent
last_verified: "2026-10-06"
authority: derived
routing:
  intents:
    - verification
    - staleness
---

# Verification Metadata Reference

Quick access to the verification metadata specification and related tooling.

## Core Specification

- [Verification Metadata Specification](../../../docs/verification-metadata.md) — four-axis framework (temporal, coverage, extraction, robustness)

## Related References

- [Testing Guide](../../../docs/06_Testing_Guide.md) — how to run live tests and interpret results
- [LIVE_TEST_STATUS](../../../docs/LIVE_TEST_STATUS.md) — current status of all scrapers
- [Scraper Schema](scraper.schema.json) — official Stash scraper schema

## Tooling

- [staleness_check.py](../../../tools/staleness_check.py) — staleness detector; parses metadata blocks and reports STALE / AGING / FRESH / NO_META
- [scraper-quality-gate.sh](../../../tools/scraper-quality-gate.sh) — full quality gate runner

## Quick Reference: Evidence Levels

| Level | Name              | Description                                       |
| :---: | :---------------- | :------------------------------------------------ |
|  L1   | SCHEMA_VALID      | Only schema validation passed                     |
|  L2   | TESTED_STATIC     | Static HTML reviewed                              |
|  L3   | TESTED_RENDERED   | Rendered DOM snapshot reviewed                    |
|  L4   | VERIFIED_PUBLIC   | Anonymous live fetch verified                     |
|  L5   | VERIFIED_AUTH     | Logged-in browser session verified                |
|  L6   | VERIFIED_BY_VALUE | Expected values matched actual values (strongest) |

## Quick Reference: Staleness Status

| Status  | Definition               | Action                    |
| :-----: | :----------------------- | :------------------------ |
|  FRESH  | age ≤ ttl_days           | No action                 |
|  AGING  | age ≥ ttl_days / 2       | Schedule re-verification  |
|  STALE  | age > ttl_days           | Re-verify immediately     |
| UNKNOWN | Missing/unparseable date | Fix the metadata block    |
| NO_META | No metadata block        | Add verification metadata |
