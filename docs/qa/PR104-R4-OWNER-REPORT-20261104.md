# PR #104 R4 Hardening — Owner Report（歸檔）

> **歸檔說明（由 Muse Account ① 依 Controller 補正指示建立）**
> 本文為 PR #104 作者（Muse Account ②）R4 Hardening 報告的**逐字歸檔**。
> 原始出處：PR #104 留言 [6627506925](https://github.com/daniel-yfc/stash-scarpers/pull/104#issuecomment-6627506925)（2026-11-04T09:32:53Z）。
> 歸檔前，owner 報告僅存在於該留言與本地路徑，候選分支上無正式報告檔；本檔建立永久連結，不更動受測 HEAD `3f3b455`，不新增或修改 owner 的任何宣稱。
> 機器可讀版：`docs/qa/PR104-R4-OWNER-HANDOFF.yaml`（欄位值均取自本報告原文）。

---

## R4 Hardening pushed — HEAD 3f3b455 (WAVE2E-F-PR104-HARDENING-20261104-R4)

Owner status: HARDENING_COMPLETE_READY_FOR_DELTA_QA

Base 86ce058 → new HEAD 3f3b4559349e501fdb57bc053f1efb90400540a4 (single commit, 2 files: scrapers/BRAVO.yml, tools/tests/test_bravo_dvd_integration.py).

**A-01 Date calendar validation (Cross-QA A P1-3 → FIXED):** production Date JS now validates real calendar dates (month 1–12, day within month, leap-year February) via manual table lookup — no Date object, no overflow normalization, no timezone dependence. Impossible dates (month 13, day 32, Feb 30, Feb 29 on non-leap years) map to empty. All 10 mandatory cases pass, executed from the committed YAML; valid G1 dates unchanged.

**A-02 Identity gate (Cross-QA A P1-1 → PARTIALLY_FIXED):** URLs selector now additionally requires non-blank marker-anchored Title (preceding h2[2]) and Code (following h2[1]). This closes missing-Title, missing-Code, and marker-without-structure shapes; known 404 protection unchanged; all valid fixtures unchanged. Residual risk submitted to Controller as PRODUCT_IDENTITY_RESIDUAL_RISK and pinned in tests (not hidden): Code misaligned as a label h2, Code ≠ canonical segment, stray marker between unrelated h2s, canonical vs requested URL (not expressible in YAML). antchfx equivalence is a Gate B item (DVD-XPATH).

**Policies unchanged:** no Duration/Studio/Tags/Performers restored, Clips selectors untouched, QueryFragment stays removed.

**Gate A (working tree at new HEAD):** pytest 462 passed / 2 skipped / 3 xfailed, validate-all 24/24, fixture manifests 20/20, evidence contract 17/0, session scan 370 files, docs index 51 OK, format warnings only on 24 pre-existing files.

**Package:** BRAVO.zip version 3f3b455, SHA-256 5bc3b2b7656d9c988f3552aaae271883e9a0e303f2c5a9e4c46494b232670ddb (supersedes 10fa6183…32fa).

**Exact-head CI (checked 2026-11-04 17:31 CST):** 9 success, 1 skipped (Deploy to Pages, expected for Draft), 0 failed.

Gate B NOT_RUN. Merge and deployment NOT authorized. Delta QA by Account ① pending on this exact HEAD.
