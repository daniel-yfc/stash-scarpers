---
doc_id: DOC-E2E-90
title: "Stash Live E2E Fix Workbench Index"
status: draft
layer: repository
owner: maintainer
audience:
  - agent
  - maintainer
applies_to:
  - scrapers
  - live-e2e
last_verified: "2026-10-31"
authority: derived
routing:
  intents:
    - stash-e2e
    - implementation-workbench
---

# Stash Live E2E 修復工作包（暫存）

> **狀態：WORKBENCH / DRAFT — 尚未開始實作；不代表修復完成。**  
> **Base:** `daniel-yfc/stash-scarpers@4bbafca9cf7b5d67117ac41136e74a303c28e4f4`  
> **Stash test build (reported):** `v0.31.1-182-g9e9ad972`  
> **決策依據:** 2026-10-31 的使用者提供 `QA-STASH-LIVE-E2E-20261031 v2`、`FIX-PLAN-STASH-E2E-20261031-v2`、交叉審查裁定，及 Perplexity draft 的批判性對照。

本目錄保存**時點性實測摘要、修復工作規格、技術設計參考、獨立驗收條件、完成後歸檔程序**。它不是取代 [品質規則](../../21-quality-gate-rules.md)、[測試指南](../../50-testing-guide.md)、[正式上線閘門](../../30-production-gate.md) 或 Stash 上游程式碼的規範。

## 文件地圖

| 文件 | 用途與權限界線 |
| --- | --- |
| [91-live-e2e-evidence.md](91-live-e2e-evidence.md) | Muse 提報的 Stash 實測 v2 事實摘要、21 個 Scraper 覆蓋表、12 項 finding、私有原始證據索引；**不冒稱本提交獨立重跑** |
| [92-fix-implementation-spec.md](92-fix-implementation-spec.md) | M0–M6、檔案 Owner、修復 PR、依賴、停損與安全邊界 |
| [93-design-decisions-and-references.md](93-design-decisions-and-references.md) | 已驗證程式碼事實、需要 A/B 實驗的假設、Perplexity 方案取捨、官方／repo 參照 |
| [94-delta-acceptance.md](94-delta-acceptance.md) | Gate A/B/C、候選套件來源鏈、逐項驗收案例與紀錄範本 |
| [95-archive-handoff.md](95-archive-handoff.md) | 完工判定、例外轉交、改存 `docs/archive/stash-e2e-20261031/` 的審核與索引更新程序 |
| [96-agent-prompt-metadata-integrity.md](96-agent-prompt-metadata-integrity.md) | English Wave 1A: Justice01/KOShop/CK-Download |
| [97-agent-prompt-bravo-clips.md](97-agent-prompt-bravo-clips.md) | English Wave 1B: BRAVO Clips and Fragment |
| [98-agent-prompt-acceed-guard.md](98-agent-prompt-acceed-guard.md) | English Wave 1C: ACCEED authentication guard |

## 平行開發（已規劃、未啟動）

第一波三個互不重疊的程式碼分支：`fix/e2e-metadata-integrity`、`fix/e2e-bravo-clips`、`fix/e2e-acceed-auth-guard`。第二波最多三分支，依賴前置 PR 合併與必要根因證據。三個英文 Prompt 如上；檔案所有權、單一 `stash-test` QA Lease、候選 ZIP SHA 驗證與 Gate A/B/C 詳見 [實施規格](92-fix-implementation-spec.md)。本文件 PR 不授權 Agent 自行建立修復分支、操作測試實例或合併。

## 當前控制狀態（不是新測試結論）

- `STACK_MERGED / REPOSITORY_MAIN_VERIFIED`：原 #87–#90 已合併；基準 commit 及 tree 由 GitHub 回讀。
- `SOURCE_INSTALL_REPORTED_PASS`：Muse 的 stash-test 實測報告稱公開 21/21 套件已安裝；原始 API JSON 未置入此公開 repo。
- `LIVE_STASH_E2E_CHANGES_REQUESTED`：包含 BRAVO、metadata 污染與搜尋精確度缺陷。
- `CDP_FIXED_ENDPOINT_REPORTED_PASS`：v2 修訂補測 `http://<internal-host>:9222/json/version`，GVWiki、BRAVO、KOShop 通過；**重啟驗證仍 NOT_RUN**。
- `PRODUCTION_NOT_READY`：包含登入態/正式環境、QA-06 歷史憑證事件未結案。

## 工作授權與公開資料保護

本工作包僅為文件提交。**不授權**修正 Scraper YAML、操作 stash-test/production、發送第三方網站大量請求、建立更多修復 PR、合併任何 PR 或變更部署。後續執行依 Controller 授權；合併保留給使用者。

不提交憑證、Cookie、完整 HAR、Browser Profile、私網位址、未去敏 GraphQL response 或原始 Host Trace。已知私有證據存放位置僅記述為 `qa-stash-live-e2e-20261031/evidence/`（**不位於公開 repo**）。有證據索引不等於證據檔已公開、重演或經第二方簽章。

## 生命週期

工作期間更新此目錄內的 finding/verdict 與驗收結果；當已核准的修復工作完成、Independent Live Delta QA 交付、剩餘阻擋事項明確移交，**另提 Archive-only PR**，使用 repo 既有的 `docs/archive/`（其用途即「archived」）而非新增重複的 `docs/archived/`。歸檔前不得標示本目錄 `archived`，亦不得從 QA 類別自動提升 `PRODUCTION_READY`。

## 主要參照

- [Epic #80](https://github.com/daniel-yfc/stash-scarpers/issues/80) — 舊狀態需於後續工作流更新；本文件 PR 不改 Issue。
- [PR #84](https://github.com/daniel-yfc/stash-scarpers/pull/84)、[PR #85](https://github.com/daniel-yfc/stash-scarpers/pull/85) — Draft E2E harness / evidence validator，**不可直接以本文件批准合併**。
- [GitHub 已合併基準](https://github.com/daniel-yfc/stash-scarpers/commit/4bbafca9cf7b5d67117ac41136e74a303c28e4f4)。
