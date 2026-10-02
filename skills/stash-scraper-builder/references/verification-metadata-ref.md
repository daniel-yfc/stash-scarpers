# Verification Metadata Reference

This reference provides quick access to the verification metadata specification and related tooling.

## Core Specification

- [Verification Metadata Specification](../../docs/verification-metadata.md) — Complete definition of the four-axis verification framework (temporal, coverage, extraction, robustness)

## Related References

- [Testing Guide](../../docs/06_Testing_Guide.md) — How to run live tests and interpret results
- [LIVE_TEST_STATUS](../../docs/LIVE_TEST_STATUS.md) — Current status of all scrapers
- [Scraper Schema](scraper.schema.json) — Official Stash scraper schema

## Tooling

- [livetest.py](../../tools/livetest.py) — Python tool for parsing verification metadata and detecting stale scrapers
- [scraper-quality-gate.sh](../../tools/scraper-quality-gate.sh) — Shell script for running the full quality gate

## Quick Reference: Evidence Levels

| Level | Name | Description |
|:-----:|:-----|:------------|
| L1 | SCHEMA_VALID | Only schema validation passed |
| L2 | TESTED_STATIC | Static HTML reviewed |
| L3 | TESTED_RENDERED | Rendered DOM snapshot reviewed |
| L4 | VERIFIED_PUBLIC | Anonymous live fetch verified |
| L5 | VERIFIED_AUTH | Logged-in browser session verified |
| L6 | VERIFIED_BY_VALUE | Expected values matched actual values (strongest) |

## Quick Reference: Staleness Status

| Status | Age | Action |
|:------:|:---:|:-------|
| FRESH | ≤30 days | No action needed |
| AGING | 31–90 days | Schedule re-verification |
| STALE | >90 days | Re-verify immediately |
| UNKNOWN | No date | Add verification metadata |
