---
doc_id: TPL-REPORT-71
title: Full‑Suite Test Report Template (Markdown)
status: active
layer: template
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - testing
last_verified: "2026-10-15"
authority: informational
routing:
  intents:
    - testing
    - reporting
---

# Full‑Suite Test Report Template (Markdown)

## Purpose

A standardized Markdown report structure designed for human contributors, code reviewers, and release managers. It synthesizes static validation, policy enforcement, unit/regression suites, documentation checks, and live site scrutiny into a scannable, structured summary.

---

## 1. Quick Status Header

```markdown
# Full‑Suite Test Report

- **Date / Timestamp:** 2026-09-08 14:30:00 UTC
- **Commit / Ref:** `ab12cd3` (branch: `main`)
- **Environment:** Ubuntu 24.04 LTS / Node v20.x / Python 3.12.3
- **Executed By:** <Contributor Name / GitHub Actions Run #ID>
- **Verdict:** ✅ PASS (100% pass rate, 0 regressions)
```

---

## 2. Executive Test Matrix (Markdown Table)

| Test Suite / Layer          | Command / Tool                                          |  Total | Passed | Failed | Skipped |  Duration |  Status  | Notes / Key Findings                                        |
| :-------------------------- | :------------------------------------------------------ | -----: | -----: | -----: | ------: | --------: | :------: | :---------------------------------------------------------- |
| **Schema Validation**       | `npm run validate`                                      |     14 |     14 |      0 |       0 |      0.8s |   PASS   | All scrapers conform to `scraper.schema.json`               |
| **Repository Quality Gate** | `bash tools/validate-all.sh`                            |     14 |     14 |      0 |       0 |      1.2s |   PASS   | Strict syntax, naming, and policy rules satisfied           |
| **Python Test Suite**       | `python3 -m pytest tools/tests/ -v`                     |     13 |     13 |      0 |       0 |     1.67s |   PASS   | Tool scripts, validator wrappers, and skill references pass |
| **Documentation Check**     | `python3 tools/check_scraper_docs.py`                   |      9 |      9 |      0 |       0 |      0.4s |   PASS   | 9 embedded YAML blocks verified without contradiction       |
| **URL Sorting Check**       | `npm run validate-sort`                                 |     14 |     14 |      0 |       0 |      0.8s |   PASS   | URLs alphabetically ordered across all scrapers             |
| **Live Scrutiny (Smoke)**   | `node tools/scrutiny.js scrapers/<Target>.yml --search` |      8 |      8 |      0 |       0 |      4.5s |   PASS   | Target site live search and detail extraction verified      |
| **TOTAL / SUMMARY**         | _All Verification Layers_                               | **72** | **72** |  **0** |   **0** | **9.37s** | **PASS** | **Pass Rate: 100.0%**                                       |

---

## 3. Failure & Warning Breakdown

If any suite reports non-zero failures, detail each incident in this section:

| Issue ID | Suite | Target / Test Name | Root Cause / Error Message                | Action Taken / Owner |
| :------- | :---- | :----------------- | :---------------------------------------- | :------------------- |
| _None_   | —     | —                  | _No failures encountered during this run_ | —                    |

_If failures occur, use this format:_

```markdown
| BUG-01 | Quality Gate | scrapers/Sample.yml | Root `name:` declaration missing at col 0 | Fixed indentation in YAML |
| BUG-02 | Python Tests | test_tools.py::test_scrutiny_cli_help | Exit code 1: missing npm dependency | Added dependency to package.json |
```

---

## 4. Live Scrutiny Snapshot (Optional / Release Smoke)

When testing live upstream endpoints with `tools/scrutiny.js`:

| Scraper                 | Test Target / URL          |  Mode  | Fields Extracted | Coverage | Notes                                                   |
| :---------------------- | :------------------------- | :----: | ---------------: | :------: | :------------------------------------------------------ |
| `scrapers/Ko-Video.yml` | `product_code=KKE0149_DVD` | Detail |            8 / 8 |   100%   | Title, Code, Date, Image, Studio, Tags, Performers, URL |
| `scrapers/Ko-Video.yml` | `probe=雄穴`               | Search |            4 / 4 |   100%   | 20 candidates retrieved, pagination functional          |

---

## 5. Definition of Done & Sign-Off Checklist

Before merging a pull request or tagging a release, verify:

- [ ] All automated suites in Section 2 executed cleanly (0 failed).
- [ ] Any test failure in Section 3 is triaged, resolved, and documented.
- [ ] Modified scrapers have passed live verification via `tools/scrutiny.js`.
- [ ] No secrets, tokens, or personal session credentials committed to public files.
- [ ] Documentation check (`check_scraper_docs.py`) confirms no doc-code drift.

---

## Usage Instructions

1. **Copy Sections 1 through 5** above into your PR description, issue comment, or a release note artifact (e.g., `evidence/audit/report-YYYY-MM-DD.md`).
2. **Execute the standard commands** listed in column 2.
3. **Record actual counts and wall-clock times** emitted by the test runners.
4. **Calculate total pass rate:** `(Total Passed / Total Checked) × 100%`.
5. **Sign off** using Section 5.

---

_Template Version: 2.0 — Updated 2026-09-08_
