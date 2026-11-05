---
doc_id: PR104-GATEB-RESTORATION-20261104
title: PR #104 Gate B — Restoration Plan and Status
status: restoration-pass
layer: qa
owner: agent-d-independent-runtime-qa
audience: [controller, maintainer]
applies_to: [wave-2e, pr-104, gate-b, rollback]
last_verified: "2026-11-05"
authority: evidence
---

# PR #104 — Gate B Restoration 報告

## Phase B Restoration 狀態

**`RESTORATION_STATUS: RESTORATION_PASS`**（lease `GATEB-PR104-LEASE-20261105-01`，2026-11-05 執行後）

## 還原基準的重要更正

M0 報告預設的 rollback 目標（BRAVO `b92acdd`、21 packages）**在 Phase B 開始時已不存在**：實例於 M0 後發生非本 QA 的變更（package registry 清空、改名後 scraper 集進駐，詳見 QA 報告 F-B-01）。因此還原基準改為 **Phase B 前置快照**（`before-snapshot.json`）：registry 空、來源 Community + yfc、stats 15/1/1/7。本 QA **未**裝回 `b92acdd`，以免反而改變測試前狀態。

## 執行與五項比對

1. 以 isolated source 解除安裝候選 BRAVO（registry 回到 0 件）。
2. 移除隔離來源 `gateb-pr104`（來源回到 Community + yfc）。
3. `reloadScrapers` 完成。
4. After 快照與 before 快照五項比對（`restoration-comparison.json`）：version ✓／stats ✓／package sources ✓／scraping config ✓／installed packages ✓ — **5/5 相等**。
5. Scraper 集比對：還原後 27 個 scene scrapers，與測試中（28，含候選 BRAVO）的差集恰為 `{BRAVO}`；`BRAVO_JAPAN` 等既有 scraper 全數完好。
6. 持久 Scene 紀錄：全程 scrape-only，stats 不變（15/1/1/7），無任何 Scene 寫入。
7. CDP targets：本 QA 未直接建立／關閉任何 target（僅 Stash 自身 driver 使用）；還原後的 target 清單回讀因核准逾時未完成，該項記 `NOT_VERIFIED` — 不影響五項狀態比對的完整性，併此揭露。
8. Lease 已釋放（本報告發布即釋放紀錄）。

## M0 階段紀錄（歷史，保留）

M0 全程唯讀、無變更、無需還原 — 此段為 2026-11-04 M0 報告的原始結論，Phase B 狀態以上方為準。
