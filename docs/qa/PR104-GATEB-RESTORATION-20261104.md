---
doc_id: PR104-GATEB-RESTORATION-20261104
title: PR #104 Gate B — Restoration Plan and Status
status: m0-no-change-phase-b-not-run
layer: qa
owner: agent-d-independent-runtime-qa
audience: [controller, maintainer]
applies_to: [wave-2e, pr-104, gate-b, rollback]
last_verified: "2026-11-04"
authority: evidence
---

# PR #104 — Gate B Restoration 報告

## M0 階段（本報告覆蓋範圍）

- M0 全程唯讀：未安裝套件、未 reload scrapers、未建立／關閉 CDP targets、未觸發 scrape、未寫入任何 Scene 或設定。
- 因此 M0 **無需還原**；結束核對：stash-test stats（15／1／1／7）與已安裝 packages（21 件、BRAVO `b92acdd`）與盤點值一致，候選 checkout 工作樹乾淨。
- M0 restoration 結論：`NO_CHANGE_MADE`（不等於 Phase B 的 `RESTORATION_PASS`）。

## Phase B Restoration 狀態

**`RESTORATION_STATUS: NOT_RUN`**（Phase B 未執行）

## Phase B 執行時之 Rollback 清單（lease 核發後逐項執行並留證）

1. 還原先前安裝的 scraper 套件：BRAVO 回到 `b92acdd`（來源 yfc main index），移除 isolated candidate source。
2. 還原 scraper 來源與 runtime 設定；確認 `scraperCDPPath` 維持固定 `/json/version` 形式、`scraperCertCheck` 不變。
3. 還原其他受測試影響的 runtime configuration（以 B-00 前 baseline 快照為準）。
4. 移除本 lease 建立的暫時測試產物（evidence 匯出除外，依 lease 之證據保留要求處理）。
5. 只關閉本 lease 建立的 CDP targets；M0 盤點時既有 targets（page 1 + worker 1）必須完好，比對數量與類型。
6. 確認持久 Scene 紀錄是否變更（scrape-only 原則下應為零變更；任何變更逐筆記錄）。
7. Before/after 五項比對：version／stats／package sources／scraping config／installed packages — 全數一致才可記 `RESTORATION_PASS`；部份完成記 `RESTORATION_PARTIAL`，失敗記 `RESTORATION_FAIL` 並列出未解差異。
8. 釋放獨占 lease 並記錄釋放時間。

註：資料庫備份可還原性仍為 `UNVERIFIED`（ standing M0 未決項）；本 rollback 設計比照 PR #93 Gate B 已驗證作法，不依賴 DB 備份還原，其足夠性由 Controller 於 lease 中明示裁示。
